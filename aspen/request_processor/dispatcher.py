"""
This module implements finding the file that matches a request path.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from functools import reduce
from inspect import isclass
from operator import attrgetter
import os
import posixpath

try:
    from os import scandir
except ImportError:
    from scandir import scandir

from ..exceptions import SlugCollision, WildcardCollision

from ..utils import auto_repr, Constant


def debug_noop(msg, *args):
    pass


def debug_stdout(msg, *args):
    r = msg(*args) if callable(msg) else msg % args
    try:
        print("DEBUG: " + r)
    except Exception:
        print("DEBUG: " + repr(r))

ASPEN_DEBUG = 'ASPEN_DEBUG' in os.environ
debug = debug_stdout if ASPEN_DEBUG else debug_noop


def get_mtime_ns(fspath):
    # For compatibility with Python < 3.3
    st = os.stat(fspath)
    return getattr(st, 'st_mtime_ns', int(st.st_mtime * 1000000000))


def splitext(name):
    return name.rsplit('.', 1) if '.' in name else [name, None]


def strip_matching_ext(a, b):
    """Given two names, strip a trailing extension iff they both have them.
    """
    aparts = splitext(a)
    bparts = splitext(b)

    def debug_ext():
        return "exts: %r( %r ) and %r( %r )" % (a, aparts[1], b, bparts[1])

    if aparts[1] == bparts[1]:
        debug(lambda: debug_ext() + " matches")
        return aparts[0], bparts[0]
    debug(lambda: debug_ext() + " don't match")
    return a, b


class DispatchStatus(object):
    """The attributes of this class are constants that represent dispatch statuses."""

    okay = Constant('okay')
    "Found a matching file."

    missing = Constant('missing')
    "No match found."

    unindexed = Constant('unindexed')
    "Found a matching node, but it's a directory without an index."


@auto_repr
class DispatchResult(object):
    """The result of a dispatch operation."""

    __slots__ = ('status', 'match', 'wildcards', 'extension', 'canonical')

    def __init__(self, status, match, wildcards, extension, canonical):
        self.status = status
        "A :class:`DispatchStatus` constant encoding the overall result."

        self.match = match
        "The matching filesystem path (if status != 'missing')."

        self.wildcards = wildcards or None
        "A dict whose keys are wildcard names, and values are as supplied by the path."

        self.extension = extension
        "A file extension, e.g. ``json`` when ``foo.spt`` is matched to ``foo.json``."

        self.canonical = canonical
        "The canonical path of the resource, e.g. ``/`` for ``/index.html``."

    def __eq__(self, other):
        return (
            isinstance(other, DispatchResult) and
            self.status == other.status and
            self.match == other.match and
            self.wildcards == other.wildcards and
            self.extension == other.extension and
            self.canonical == other.canonical
        )

    def __ne__(self, other):
        return not (self == other)

    def _as_tuple(self):
        # We can't give this class a proper `__hash__` method because
        # `DispatchResult` objects aren't immutable, so we use this method
        # instead to get a hashable tuple.
        return (
            self.status,
            self.match,
            frozenset(self.wildcards.items()) if self.wildcards else self.wildcards,
            self.extension,
            self.canonical
        )


MISSING = DispatchResult(DispatchStatus.missing, None, None, None, None)


@auto_repr
class FileNode(object):
    """Represents a file in a dispatch tree."""

    __slots__ = ('fspath', 'type', 'wildcard', 'extension')

    def __init__(self, fspath, type, wildcard, extension):
        self.fspath = fspath
        "The absolute filesystem path of this node."

        self.type = type
        "The node's type: 'dynamic' or 'static'."

        self.wildcard = wildcard
        "The name of the path variable if the node is a wildcard."

        self.extension = extension
        "The sub-extension of a dynamic file, e.g. ``json`` for ``foo.json.spt``."


@auto_repr
class DirectoryNode(object):
    """Represents a directory in a dispatch tree."""

    __slots__ = ('fspath', 'wildcard', 'children')

    type = 'directory'

    def __init__(self, fspath, wildcard, children):
        self.fspath = fspath
        "The absolute filesystem path of this node."

        self.wildcard = wildcard
        "The name of the path variable if the node is a wildcard."

        self.children = children
        "The node's children, a 2-tuple of dicts: ``(files, dirs)``."


@auto_repr
class LiveDirectoryNode(object):
    """Dynamically represents a directory in a dispatch tree."""

    __slots__ = ('fspath', 'wildcard', '_children', 'mtime', 'dispatcher')

    type = 'directory'

    def __init__(self, fspath, wildcard, children, mtime, dispatcher):
        self.fspath = fspath
        "The absolute filesystem path of this node."

        self.wildcard = wildcard
        "The name of the path variable if the node is a wildcard."

        self._children = children
        "The node's children, a 2-tuple of dicts: ``(files, dirs)``."

        self.mtime = mtime
        "The last modification time of the directory, in nanoseconds."

        self.dispatcher = dispatcher
        "Points to the :class:`Dispatcher` object that created this node."

    @property
    def children(self):
        mtime = get_mtime_ns(self.fspath)
        if mtime != self.mtime:
            dirnames = self.fspath[len(self.dispatcher.www_root)+1:].split(os.path.sep)
            varnames = {
                dirname[1:]: os.path.sep.join([self.dispatcher.www_root] + dirnames[:i+1])
                for i, dirname in enumerate(dirnames)
                if dirname.startswith('%')
            }
            self._children, self.mtime = self.dispatcher._build_subtree(self.fspath, varnames)
        return self._children


# Collision handlers
# ==================

def legacy_collision_handler(slug, node1, node2):
    """Ignores all collisions, like :class:`SystemDispatcher` does.
    """
    return 'ignore_second_node'


def strict_collision_handler(*args):
    """A sane collision handler, it doesn't allow any.
    """
    return 'raise'


def hybrid_collision_handler(slug, node1, node2):
    """This collision handler allows a static file to shadow a dynamic resource.

    Example: ``/file.js`` will be preferred over ``/file.js.spt``.
    """
    if node2.type == 'dynamic' and node2.fspath.startswith(node1.fspath + '.'):
        return 'ignore_second_node'
    return 'raise'


# File skippers
# =============

def skip_hidden_files(name, dirpath):
    """Skip all names starting with a dot, except ``.well-known``.
    """
    return name[0] == '.' and name != '.well-known'


def skip_nothing(name, dirpath):
    """Always returns :obj:`False`.
    """
    return False


# Dispatcher classes
# ==================

class Dispatcher(object):
    """The abstract base class of dispatchers.

    Args
    ----
    www_root
        the path to a filesystem directory
    is_dynamic
        a function that takes a file name and returns a boolean
    indices
        a list of filenames that should be treated as directory indexes
    typecasters
        a dict of typecasters, keys are strings and values are functions
    file_skipper
        a function that takes a file name and a directory path and returns a boolean
    collision_handler
        a function that takes 3 arguments (`slug, node1, node2`) and returns a string
    """

    def __init__(
        self, www_root, is_dynamic, indices, typecasters,
        file_skipper=skip_hidden_files, collision_handler=legacy_collision_handler
    ):
        self.www_root = os.path.realpath(www_root)
        self.is_dynamic = is_dynamic
        self.indices = indices
        self.typecasters = typecasters
        self.file_skipper = file_skipper
        self.collision_handler = collision_handler
        self.build_dispatch_tree()

    def build_dispatch_tree(self):
        """Called by :meth:`.__init__` to build the dispatch tree.

        Subclasses **must** implement this method.
        """
        raise NotImplementedError('abstract method')

    def dispatch(self, path, path_segments):
        """Dispatch a request.

        Args:
            path (str): the request path, e.g. ``'/'``
            path_segments (list): the path split into segments, e.g. ``['']``

        Subclasses **must** implement this method.
        """
        raise NotImplementedError('abstract method')

    def find_index(self, dirpath):
        """Looks for an index file in a directory.

        Returns:
            the full path of the first index file, or :obj:`None` if no index was found
        """
        for filename in self.indices:
            index = os.path.join(dirpath, filename)
            if os.path.isfile(index):
                return index
        return None

    def split_wildcard(self, wildcard, is_dir):
        """Splits a wildcard into its components.

        Args:
            wildcard (str): the string to split, e.g. :obj:`'year:int'`
            is_dir (bool): :obj:`True` if the wildcard is from a directory name

        Returns:
            a 3-tuple ``(varname, vartype, extension)``
        """
        if is_dir or '.' not in wildcard:
            extension = None
        else:
            wildcard, extension = wildcard.split('.', 1)
        if ':' in wildcard:
            varname, vartype = wildcard.rsplit(':', 1)
            if vartype not in self.typecasters:
                varname, vartype = wildcard, None
        else:
            varname, vartype = wildcard, None
        return varname, vartype, extension


class SystemDispatcher(Dispatcher):
    """Aspen's original dispatcher, it's very inefficient.
    """

    def build_dispatch_tree(self):
        """"""
        pass

    def dispatch(self, path, path_segments):
        """"""
        listnodes = os.listdir
        is_leaf = os.path.isfile
        traverse = os.path.join
        result = _dispatch_abstract(
            self, listnodes, self.is_dynamic, is_leaf, traverse, self.find_index,
            self.www_root, path_segments
        )
        debug(lambda: "dispatch_abstract returned: " + repr(result))

        # Protect against escaping the www_root.
        if result.match and not result.match.startswith(self.www_root):
            # Attempted breakout, e.g. a request for `/../secrets`
            return MISSING

        return result


def _dispatch_abstract(dispatcher, listnodes, is_dynamic, is_leaf, traverse, find_index, startnode, nodepath):
    """Given a list of nodenames (in 'nodepath'), return a DispatchResult.

    We try to traverse the directed graph rooted at 'startnode' using the
    functions:

       listnodes(joinedpath) - lists the nodes in the specified joined path

       is_dynamic(node) - returns true iff the specified node is dynamic

       is_leaf(node) - returns true iff the specified node is a leaf node

       traverse(joinedpath, newnode) - returns a new joined path by traversing
        into newnode from the current joinedpath

       find_index(joinedpath) - returns the index file in the specified path if
        it exists, or None if not

    Wildcards nodenames start with %. Non-leaf wildcards are used as keys in
    wildvals and their actual path names are used as their values. In general,
    the rule for matching is 'most specific wins': $foo looks for isfile($foo)
    then isfile($foo-minus-extension) then isfile(virtual-with-extension) then
    isfile(virtual-no-extension) then isdir(virtual)

    """
    file_skipper = dispatcher.file_skipper

    nodepath = nodepath[:]  # copy it so we can mutate it if necessary
    wildvals, wildleafs = {}, {}
    curnode = startnode
    extension, canonical = None, None
    is_dynamic_node = lambda n: is_dynamic(traverse(curnode, n))
    is_leaf_node = lambda n: is_leaf(traverse(curnode, n))

    def get_wildleaf_fallback():
        lastnode_ext = splitext(nodepath[-1])[1]
        wildleaf_fallback = lastnode_ext in wildleafs or None in wildleafs
        if wildleaf_fallback:
            ext = lastnode_ext if lastnode_ext in wildleafs else None
            curnode, wildvals = wildleafs[ext]
            debug(lambda: "Wildcard leaf match %r and ext %r" % (curnode, ext))
            return DispatchResult(DispatchStatus.okay, curnode, wildvals, None, None)
        return None

    for depth, node in enumerate(nodepath):

        # check all the possibilities:
        # node.html, node.html.spt, node.spt, node.html/, %node.html/ %*.html.spt, %*.spt

        # don't serve hidden files
        subnodes = set([ n for n in listnodes(curnode) if not file_skipper(n, curnode) ])

        node_noext, node_ext = splitext(node)

        # only maybe because non-spt files aren't wild
        maybe_wild_nodes = [ n for n in sorted(subnodes) if n.startswith("%") ]

        wild_leaf_ns = [ n for n in maybe_wild_nodes if is_leaf_node(n) and is_dynamic_node(n) ]
        wild_nonleaf_ns = [ n for n in maybe_wild_nodes if not is_leaf_node(n) ]

        # store all the fallback possibilities
        remaining = reduce(posixpath.join, nodepath[depth:])
        for n in wild_leaf_ns:
            wildwildvals = wildvals.copy()
            varname, vartype, leaf_ext = dispatcher.split_wildcard(splitext(n[1:])[0], False)
            wildcard = ':'.join((varname, vartype)) if vartype else varname
            if leaf_ext and remaining.endswith(leaf_ext):
                wildwildvals[wildcard] = remaining[:-len(leaf_ext)-1]
            else:
                wildwildvals[wildcard] = remaining
            wildleafs[leaf_ext] = (traverse(curnode, n), wildwildvals)

        debug(lambda: "wildleafs is %r" % wildleafs)

        found_n = None
        last_node = (depth + 1) == len(nodepath)
        if last_node:
            debug(lambda: "on last node %r" % node)
            if node == '':  # dir request
                debug(lambda: "...last node is empty")
                path_so_far = traverse(curnode, node)
                index = find_index(path_so_far)
                if index:
                    debug(lambda: "found index: %r" % index)
                    return DispatchResult(DispatchStatus.okay, index, wildvals, None, canonical)
                if wild_leaf_ns:
                    found_n = wild_leaf_ns[0]
                    debug(lambda: "found wild leaf: %r" % found_n)
                    curnode = traverse(curnode, found_n)
                    varname, vartype, _ = dispatcher.split_wildcard(splitext(found_n[1:])[0], False)
                    wildcard = ':'.join((varname, vartype)) if vartype else varname
                    wildvals[wildcard] = node
                    return DispatchResult(DispatchStatus.okay, curnode, wildvals, None, canonical)
                debug(lambda: "no match")
                return DispatchResult(
                    DispatchStatus.unindexed, curnode + os.path.sep, wildvals, None, canonical
                )
            elif node in subnodes and is_leaf_node(node):
                debug(lambda: "...found exact file, must be static")
                if is_dynamic_node(node):
                    return MISSING
                else:
                    found_n = node
                    if find_index(curnode) == traverse(curnode, node):
                        # The canonical path of `/index.html` is `/`
                        canonical = '/' + '/'.join(nodepath)[:-len(node)]
            elif node + ".spt" in subnodes and is_leaf_node(node + ".spt"):
                debug(lambda: "...found exact spt")
                found_n = node + ".spt"
            elif node_noext + ".spt" in subnodes and is_leaf_node(node_noext + ".spt") \
                    and node_ext:
                # node has an extension
                debug(lambda: "...found indirect spt, extension is `%s`" % node_ext)
                # indirect match - foo.spt is answering to foo.html
                extension = node_ext
                found_n = node_noext + ".spt"

            if found_n is not None:
                debug(lambda: "found_n: %r" % found_n)
                curnode = traverse(curnode, found_n)
            elif wild_nonleaf_ns:
                debug(lambda: "wild_nonleaf_ns")
                result = get_wildleaf_fallback()
                if result:
                    return result
                found_n = wild_nonleaf_ns[0]
                wildvals[found_n[1:]] = node
                curnode = traverse(curnode, found_n)
                nodepath.append('')
                canonical = '/' + '/'.join(nodepath)
            elif node in subnodes:
                debug(lambda: "exact dirmatch")
                curnode = traverse(curnode, node)
                nodepath.append('')
                canonical = '/' + '/'.join(nodepath)
            else:
                debug(lambda: "fallthrough")
                result = get_wildleaf_fallback()
                if not result:
                    return MISSING
                return result

        if not last_node:  # not at last path seg in request
            debug(lambda: "on node %r" % node)
            if node in subnodes and not is_leaf_node(node):
                found_n = node
                debug(lambda: "Exact match " + repr(node))
                curnode = traverse(curnode, found_n)
            elif wild_nonleaf_ns:
                # need to match a wildnode, and we're not the last node, so we should match
                # non-leaf first, then leaf
                found_n = wild_nonleaf_ns[0]
                wildvals[found_n[1:]] = node
                debug(lambda: "Wildcard match %r = %r " % (found_n, node))
                curnode = traverse(curnode, found_n)
            else:
                debug(lambda: "No exact match for " + repr(node))
                result = get_wildleaf_fallback()
                if not result:
                    return MISSING
                return result

    return DispatchResult(DispatchStatus.okay, curnode, wildvals, extension, canonical)


class UserlandDispatcher(Dispatcher):
    """A dispatcher optimized for production use.

    This dispatcher builds a complete and static tree when it is first created.
    It then uses this dispatch tree to route requests without making any system
    call, thus avoiding FFI and context switching costs.

    This is the default dispatcher (when the ``changes_reload`` configuration
    option is ``False``).
    """

    DIR_WILDCARD = Constant('DIR_WILDCARD')
    LEAF_WILDCARDS = Constant('LEAF_WILDCARDS')

    def make_dir_node(self, fspath, wildcard, children, mtime):
        return DirectoryNode(fspath, wildcard, children)

    def build_dispatch_tree(self):
        """"""
        children, mtime = self._build_subtree(self.www_root, {})
        self.tree = self.make_dir_node(self.www_root, None, children, mtime)

    def _build_subtree(self, dirpath, varnames):
        """This method recursively builds a dispacth subtree.
        """
        files, dirs = {}, {}
        mtime = get_mtime_ns(dirpath)
        index = self.find_index(dirpath)
        for entry in sorted(scandir(dirpath), key=attrgetter('name')):
            name = entry.name
            if self.file_skipper(name, dirpath):
                continue
            fspath = entry.path
            if entry.is_symlink():
                fspath = os.path.realpath(fspath)
                if not fspath.startswith(self.www_root):
                    # Prevent escaping the www_root
                    continue
            is_dir = entry.is_dir()
            if is_dir:
                node_type = 'directory'
                slug = name
            elif self.is_dynamic(name):
                node_type = 'dynamic'
                slug = name.rsplit('.', 1)[0]
            else:
                node_type = 'static'
                slug = name
            if slug.startswith('%') and node_type != 'static':
                varname, vartype, extension = self.split_wildcard(slug[1:], is_dir)
                if varname in varnames and varnames[varname] != dirpath:
                    raise WildcardCollision(varname)
                varnames[varname] = dirpath
                wildcard = ':'.join((varname, vartype)) if vartype else varname
                del varname, vartype
                if is_dir:
                    slug = self.DIR_WILDCARD
                else:
                    node = FileNode(fspath, node_type, wildcard, extension)
                    wildleafs = files.setdefault(self.LEAF_WILDCARDS, {})
                    wildleafs[extension] = node
                    continue
            else:
                wildcard, extension = None, None
            if is_dir:
                subtree, mtime = self._build_subtree(fspath, varnames.copy())
                node = self.make_dir_node(fspath, wildcard, subtree, mtime)
            else:
                node = FileNode(fspath, node_type, wildcard, extension)
            goes_into = dirs if is_dir else files
            if slug in goes_into:
                action = self.collision_handler(slug, goes_into[slug], node)
                debug("collision: %r is claimed by both %r and %r | action: %r"
                     , slug, goes_into[slug].fspath, node.fspath, action)
                if action == 'raise':
                    raise SlugCollision(slug, goes_into[slug], node)
                if action == 'ignore_second_node':
                    continue
                if action != 'replace_first_node':
                    raise ValueError("%r is not a valid collision action" % action)
            goes_into[slug] = node
            if fspath == index:
                files[''] = slug
        return (files, dirs), mtime

    def dispatch(self, path, path_segments):
        """"""
        DIR_WILDCARD = self.DIR_WILDCARD
        LEAF_WILDCARDS = self.LEAF_WILDCARDS

        extension, canonical = None, None
        fallback_wildleafs = None

        def fallback():
            if fallback_wildleafs:
                f_wildleafs, f_depth = fallback_wildleafs
                requested_extension = splitext(path_segments[-1])[1]
                if requested_extension in f_wildleafs:
                    node = f_wildleafs[requested_extension]
                elif None in f_wildleafs:
                    node = f_wildleafs[None]
                else:
                    debug("no suitable wildleaf fallback")
                    return MISSING
                debug("falling back to wild leaf: %r", node)
                if wildcards and f_depth < depth:
                    # We need to recreate the wildcards dict from scratch.
                    wildcards.clear()
                    fspath_segments = node.fspath[len(self.www_root)+1:].split(os.path.sep)
                    for i in range(f_depth):
                        fspath_segment = fspath_segments[i]
                        if fspath_segment.startswith('%'):
                            wildcards[fspath_segment[1:]] = path_segments[i]
                tail = '/'.join(path_segments[f_depth:])
                if node.extension:
                    wildcards[node.wildcard] = tail[:-len(node.extension)-1]
                else:
                    wildcards[node.wildcard] = tail
                return DispatchResult(DispatchStatus.okay, node.fspath, wildcards, None, None)
            debug("no wildleaf fallback")
            return MISSING

        def success():
            return DispatchResult(
                DispatchStatus.okay, node.fspath, wildcards, extension, canonical
            )

        wildcards = {}
        node = self.tree
        max_depth = len(path_segments) - 1
        for depth, segment in enumerate(path_segments):
            files, dirs = node.children

            if segment:
                # The segment isn't empty. Look for a match in files and dirs.
                if segment in files:
                    debug("exact file match: %r", segment)
                    node = files[segment]
                    if depth == max_depth:
                        if segment == files.get(''):
                            # The canonical path of `/index.html` is `/`
                            canonical = path[:-len(segment)]
                        return success()
                if depth == max_depth and '.' in segment:
                    base, extension = segment.rsplit('.', 1)
                    if base in files and files[base].type == 'dynamic':
                        # Base match (e.g. `foo.spt` for `/foo.json`)
                        debug("base match: %r", base)
                        node = files[base]
                        if segment == node.fspath.rsplit(os.path.sep, 1)[-1]:
                            # Don't route a request for `/bar.html.spt` to `bar.html.spt`
                            return MISSING
                        return success()
                    extension = None
                if segment in dirs:
                    debug("exact directory match: %r", segment)
                    node = dirs[segment]
                    continue
            elif depth == max_depth:
                # The segment is empty and it's the last one.
                break

            # This segment hasn't matched anything so far, look for wildcards.
            if LEAF_WILDCARDS in files:
                fallback_wildleafs = (files[LEAF_WILDCARDS], depth)
                debug("found fallback wildleafs: %r", fallback_wildleafs)
            if DIR_WILDCARD in dirs:
                # Try to find a wildleaf match first, so that `/foo.txt` matches
                # `/%bar.txt.spt` instead of `/%dir/`.
                if fallback_wildleafs and depth == max_depth:
                    result = fallback()
                    if result.status == DispatchStatus.okay:
                        return result
                # No suitable wildleaf was found, match the virtual directory.
                # Note: empty segments are allowed on purpose.
                node = dirs[DIR_WILDCARD]
                debug("virtual directory match: %r", node.wildcard)
                wildcards[node.wildcard] = segment
                continue

            return fallback()

        if node.type == 'directory':
            debug("final node is a directory")
            files, dirs = node.children
            canonical = path + '/' if path_segments[-1] != '' else None
            # Look for an index file
            if '' in files:
                debug("index match")
                node = files[files['']]
            elif LEAF_WILDCARDS in files:
                debug("wildleaf match")
                wildleafs = files[LEAF_WILDCARDS]
                # Legacy behavior: dispatch to the "first" wildleaf
                node = wildleafs[min(wildleafs)]
                wildcards[node.wildcard] = ''
            else:
                # e.g. request for `/bar` is matched to empty wildcard directory `%foo/`
                result = fallback()
                if result.status == DispatchStatus.okay:
                    return result
                fspath = node.fspath + os.path.sep
                return DispatchResult(
                    DispatchStatus.unindexed, fspath, wildcards, extension, canonical
                )

        return success()


class HybridDispatcher(UserlandDispatcher):
    """A dispatcher optimized for development environments.

    This dispatcher is almost identical to :class:`UserlandDispatcher`, except
    that it does make some system calls to check that the matched filesystem
    directories haven't been modified. If changes are detected, then the
    dispacth tree is updated accordingly.

    This is the default dispatcher when the ``changes_reload`` configuration
    option is set to ``True``.
    """

    def make_dir_node(self, fspath, wildcard, children, mtime):
        return LiveDirectoryNode(fspath, wildcard, children, mtime, self)


class TestDispatcher(object):
    """
    This pseudo-dispatcher calls all the other dispatchers and checks that their
    results are identical. It's only meant to be used in Aspen's own tests.
    """

    def __init__(self, *args, **kw):
        self.dispatchers = [cls(*args, **kw) for cls in DISPATCHER_CLASSES]

    def build_dispatch_tree(self):
        for dispatcher in self.dispatchers:
            dispatcher.build_dispatch_tree()

    def dispatch(self, path, path_segments):
        results = [
            (dispatcher, dispatcher.dispatch(path, path_segments))
            for dispatcher in self.dispatchers
        ]
        if len(set(t[1]._as_tuple() for t in results)) != 1:
            raise AssertionError(
                "the dispatchers disagree:\n    " +
                "\n    ".join(
                    "%s returned %r" % (dispatcher.__class__.__name__, result)
                    for dispatcher, result in results
                )
            )
        return results[0][1]


DISPATCHER_CLASSES = [
    o for o in globals().values() if isclass(o) and issubclass(o, Dispatcher) and o != Dispatcher
]
DISPATCHER_CLASSES.sort(key=lambda c: c.__name__)

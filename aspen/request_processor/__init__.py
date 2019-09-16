"""
The request processor dispatches requests to the filesystem, typecasts URL
path variables, loads the resource from the filesystem, and then renders and
encodes the resource (if it's dynamic).
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from copy import copy
import errno
import mimetypes
import os
import sys
from collections import defaultdict

from . import typecasting
from .dispatcher import DispatchStatus, HybridDispatcher, UserlandDispatcher
from .typecasting import defaults as default_typecasters
from ..resources import Resources
from ..http.resource import Static
from ..exceptions import ConfigurationError


default_indices = [
    'index.html', 'index.json', 'index',
    'index.html.spt', 'index.json.spt', 'index.spt',
]


class RequestProcessor(object):
    """A core request processor designed for integration into a host framework.

    The ``kwargs`` are for configuration, see :class:`DefaultConfiguration`
    for valid keys and default values.
    """

    def __init__(self, **kwargs):
        # Do some base-line configuration.
        # ================================
        # We want to do the following configuration of our Python environment
        # regardless of the user's configuration preferences

        # mimetypes
        aspens_mimetypes = os.path.join(os.path.dirname(__file__), 'mime.types')
        mimetypes.knownfiles += [aspens_mimetypes]
        # mimetypes.init is called below after the user has a turn.

        # XXX register codecs here


        # Configure from defaults and kwargs.
        # ===================================

        defaults = [(k, v) for k, v in DefaultConfiguration.__dict__.items() if k[0] != '_']
        for name, default in sorted(defaults):
            if name in kwargs:
                self.__dict__[name] = kwargs[name]
            else:
                self.__dict__[name] = copy(default)


        # Set some attributes.
        # ====================

        def safe_getcwd(errorstr):
            try:
                # If the working directory no longer exists, then the following
                # will raise OSError: [Errno 2] No such file or directory. I
                # swear I've seen this under supervisor, though I don't have
                # steps to reproduce. :-(  To get around this you specify a
                # www_root explicitly, or you can use supervisor's cwd
                # facility.

                return os.getcwd()
            except OSError as err:
                if err.errno != errno.ENOENT:
                    raise
                raise ConfigurationError(errorstr)

        # project root
        if self.project_root is not None:
            # canonicalize it
            if not os.path.isabs(self.project_root):
                cwd = safe_getcwd(
                    "Could not get a current working directory. You can specify "
                    "project_root in kwargs."
                )
                self.project_root = os.path.join(cwd, self.project_root)

            self.project_root = os.path.realpath(self.project_root)
            self.resource_directories.insert(0, self.project_root)

            # mime.types
            users_mimetypes = os.path.join(self.project_root, 'mime.types')
            mimetypes.knownfiles += [users_mimetypes]

            # PYTHONPATH
            sys.path.insert(0, self.project_root)

        # www_root
        if self.www_root is None:
            self.www_root = safe_getcwd(
                "Could not get a current working directory. You can specify "
                "www_root in kwargs."
            )

        self.www_root = os.path.realpath(self.www_root)
        self.resource_directories.insert(0, self.www_root)

        # kludge simplates -- should move out into a simplate plugin
        from ..simplates.renderers import factories
        from ..simplates.simplate import Simplate, SimplateDefaults
        Simplate.renderer_factories = factories(self)
        Simplate.default_renderers_by_media_type = defaultdict(lambda: self.renderer_default)
        Simplate.default_renderers_by_media_type[self.media_type_json] = 'json_dump'

        initial_context = { 'request_processor': self }
        Simplate.defaults = SimplateDefaults(
            Simplate.default_renderers_by_media_type,
            Simplate.renderer_factories,
            initial_context
        )

        # set up dynamic class mapping
        self.dynamic_classes_by_file_extension = dict(spt=Simplate)

        # create the dispatcher
        if self.dispatcher_class is None:
            self.dispatcher_class = (
                HybridDispatcher if self.changes_reload else UserlandDispatcher
            )
        self.dispatcher = self.dispatcher_class(
            self.www_root, self.is_dynamic, self.indices, self.typecasters,
            **kwargs.get('dispatcher_options', {})
        )
        self.dispatcher.build_dispatch_tree()

        # mime.types
        # ==========
        # It turns out that init'ing mimetypes is somewhat expensive. This is
        # significant in testing, though in dev/production you wouldn't notice.
        # In any case this means that if a devuser inits mimetypes themselves
        # then we won't do so again here, which is fine. Right?

        if not mimetypes.inited:
            mimetypes.init()

        # create the resources cache
        self.resources = Resources(self)


    def dispatch(self, path):
        """Call the dispatcher and inject the path variables into the given path object.

        Args:
            path (Path): the requested path, e.g. :obj:`'/foo'`

        Returns:
            A :class:`DispatchResult` object.
        """
        dispatch_result = self.dispatcher.dispatch(path.decoded, path.parts)
        if dispatch_result.wildcards:
            for k, v in dispatch_result.wildcards.items():
                path[k] = v
        return dispatch_result


    def process(self, path, querystring, accept_header, context):
        """Process a request.

        Args:
            path (Path): the requested path, e.g. :obj:`Path('/foo')`
            querystring (Querystring): the query parameters, e.g. :obj:`Querystring('?bar=baz')`
            accept_header (str): the value of the HTTP header ``Accept``
            context (dict): the context variables passed to dynamic resources

        Returns:
            A 3-tuple ``(dispatch_result, resource, output)``. The latter two are
            set to :obj:`None` if dispatching failed.

        """

        dispatch_result = self.dispatch(path)

        typecasting.apply_typecasters(self.typecasters, path, context)

        if dispatch_result.match and dispatch_result.status == DispatchStatus.okay:
            resource = self.resources.get(dispatch_result.match)
            context['querystring'] = querystring
            output = resource.render(context, dispatch_result, accept_header)
            if not isinstance(output.body, bytes):
                output.charset = self.encode_output_as
                output.body = output.body.encode(output.charset)
            return dispatch_result, resource, output

        return dispatch_result, None, None


    def is_dynamic(self, fspath):
        """Given a filesystem path, return a boolean.
        """
        return self.get_resource_class(fspath) is not Static


    def get_resource_class(self, fspath):
        """Given a filesystem path, return a resource class.
        """
        parts = fspath.split('.')
        extension = parts[-1] if len(parts) > 1 else None
        return self.dynamic_classes_by_file_extension.get(extension, Static)


    def guess_media_type(self, filename):
        """Guess the media type of a file by looking at its extension.

        This method is a small wrapper around :func:`mimetypes.guess_type`. It
        returns :attr:`~DefaultConfiguration.media_type_default` if the guessing
        fails.
        """
        media_type = mimetypes.guess_type(filename, strict=False)[0]
        if not media_type:
            media_type = self.media_type_default
        elif media_type == 'application/json':
            media_type = self.media_type_json
        return media_type


class DefaultConfiguration(object):
    """Default configuration values.
    """

    changes_reload = False
    """
    Reload files on every request if they've been modified. This can be costly,
    so it should be turned off in production.
    """

    charset_static = None
    """
    The charset of your static files. It ends up as a ``charset=`` parameter in
    ``Content-Type`` HTTP headers (if the framework on top of Aspen supports that).
    """

    dispatcher_class = None
    """
    The kind of dispatcher that will be used to route requests to files. By
    default :class:`UserlandDispatcher` is used, unless ``changes_reload`` is
    set to ``True``, then :class:`HybridDispatcher` is used.
    """

    encode_output_as = 'UTF-8'
    "The encoding to use for dynamically-generated output."

    indices = default_indices
    "List of file names that will be treated as directory indexes. The order matters."

    media_type_default = 'text/plain'
    "If the ``Content-Type`` of a response can't be determined, then this one is used."

    media_type_json = 'application/json'
    "The media type to use for the JSON format."

    project_root = None
    "The root directory of your project."

    renderer_default = 'stdlib_percent'
    "The default renderer for simplates."

    resource_directories = []
    """
    The list of directories containing resource files. Aspen will refuse to load
    any resource located outside these directories. The `www_root` directory is
    automatically added to this list. The `project_root` directory is added as
    well if it exists.
    """

    store_static_files_in_ram = False
    "If set to ``True``, store the contents of static files in RAM."

    typecasters = default_typecasters
    "See :mod:`aspen.request_processor.typecasting`."

    www_root = None
    """
    The root directory of your web app, containing the files it will serve.
    Defaults to the current directory.
    """

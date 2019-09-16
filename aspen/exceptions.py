"""
This module defines all of the custom exceptions used across the Aspen library.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class ConfigurationError(Exception):
    """This is an error in any part of our configuration.
    """

    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


class NegotiationFailure(Exception):
    """The requested media type isn't available (HTTP status code 406).
    """

    def __init__(self, accept, available_types):
        self.accept = accept
        self.available_types = available_types
        message = "Couldn't satisfy %s. The following media types are available: %s."
        self.message = message % (self.accept, ', '.join(self.available_types))

    def __str__(self):
        return self.message


class TypecastError(Exception):
    """Parsing a segment of the request path failed (HTTP status code 404).
    """

    def __init__(self, extension):
        self.msg = "Failure to typecast extension '{0}'".format(extension)
        Exception.__init__(self)


class NotFound(Exception):
    """The requested resource isn't available (HTTP status code 404).
    """

    def __init__(self, message=''):
        self.message = message or "not found"


class AttemptedBreakout(Exception):
    """Raised when a request is dispatched to a symlinked file which is outside
    :attr:`~aspen.request_processor.DefaultConfiguration.www_root`.
    """

    def __init__(self, sym_path, real_path):
        self.sym_path = sym_path
        self.real_path = real_path

    def __str__(self):
        if self.real_path == self.sym_path:
            return "%r isn't inside a known resource directory" % self.sym_path
        return "%r is a symlink to %r" % (self.sym_path, self.real_path)


class PossibleBreakout(AttemptedBreakout, Warning):
    """A warning emitted when a symlink that points outside
    :attr:`~aspen.request_processor.DefaultConfiguration.www_root` is detected.
    """


class SlugCollision(Exception):
    """Raised if two files claim the same URL path.

    Example: ``foo.html`` and ``foo.html.spt`` both claim ``/foo.html``.
    """

    def __init__(self, slug, node1, node2):
        self.slug = slug
        self.node1 = node1
        self.node2 = node2

    def __str__(self):
        return (
            "The URL segment %r is claimed by two different nodes:\n"
            "%s(fspath=%r, type=%r, ...) and\n"
            "%s(fspath=%r, type=%r, ...)"
        ) % (
            self.slug,
            self.node1.__class__.__name__, self.node1.fspath, self.node1.type,
            self.node2.__class__.__name__, self.node2.fspath, self.node2.type,
        )

class WildcardCollision(Exception):
    """Raised if a filesystem path contains multiple wildcards with the same name.

    Examples: ``www/%foo/%foo/index.spt``, ``www/%foo/bar/%foo.spt``.
    """

    def __init__(self, varname, fspath):
        self.varname = varname
        self.fspath = fspath

    def __str__(self):
        return "%r appears twice in the filesystem path %r" % ('%' + self.varname, self.fspath)

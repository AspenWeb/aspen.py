import os.path

import mimeparse
import mimetypes

from ..exceptions import AttemptedBreakout, NegotiationFailure, NotFound
from ..output import Output


def _is_subpath(path, root):
    return path.startswith(root) and path[len(root)] == os.path.sep


def open_resource(request_processor, resource_path):
    """Open a resource in read-only binary mode, after checking for symlinks.

    :raises AttemptedBreakout:
        if the :obj:`resource_path` points to a file that isn't inside any of
        the known
        :attr:`~aspen.request_processor.DefaultConfiguration.resource_directories`

    This function doesn't fully protect against attackers who have the ability
    to create and delete symlinks inside the resource directories whenever they
    want, but it makes the attack more difficult and detectable.
    """
    real_path = os.path.realpath(resource_path)
    is_outside = all(
        not _is_subpath(real_path, resource_dir)
        for resource_dir in request_processor.resource_directories
    )
    if is_outside:
        raise AttemptedBreakout(resource_path, real_path)
    return open(real_path, 'rb')


class Static(object):
    """Model a static HTTP resource.
    """

    __slots__ = ('request_processor', 'fspath', 'raw', 'media_type', 'charset')

    def __init__(self, request_processor, fspath):
        raw = None
        read_file = (
            request_processor.store_static_files_in_ram or
            request_processor.charset_static
        )
        if read_file:
            with open_resource(request_processor, fspath) as f:
                raw = f.read()
        self.request_processor = request_processor
        self.fspath = fspath
        self.raw = raw if request_processor.store_static_files_in_ram else None
        self.media_type = request_processor.guess_media_type(fspath)
        self.charset = None
        if request_processor.charset_static:
            try:
                raw.decode(request_processor.charset_static)
                self.charset = request_processor.charset_static
            except UnicodeDecodeError:
                pass

    def render(self, *ignored):
        """Returns the file's content as :class:`bytes`.

        If the ``store_static_files_in_ram`` configuration option was set to
        :obj:`False` (the default), then the file is read from the filesystem,
        otherwise its content is returned directly.
        """
        output = Output(media_type=self.media_type, charset=self.charset)
        if self.raw is None:
            with open_resource(self.request_processor, self.fspath) as f:
                output.body = f.read()
        else:
            output.body = self.raw
        return output


class Dynamic(object):
    """Model a dynamic HTTP resource.
    """

    __slots__ = ('request_processor', 'available_types')

    def render(self, context, dispatch_result, accept_header):
        """Render the resource.

        Before rendering we need to determine what type of content we're going
        to send back, by trying to find a match between the media types the
        client wants and the ones provided by the resource.

        The two sources for what the client wants are the extension in the
        request URL (:obj:`dispatch_result.extension`), and the ``Accept``
        header (:obj:`accept_header`). If the former fails to match we raise
        :class:`NotFound` (404), if the latter fails we raise
        :class:`NegotiationFailure` (406).

        Note that we don't always respect the ``Accept`` header (the spec says
        we can ignore it: <https://tools.ietf.org/html/rfc7231#section-5.3.2>).

        Args:
            context (dict): the variables you want to pass to the resource
            dispatch_result (DispatchResult): the object returned by the dispatcher
            accept_header (str): the requested media types

        Returns: an :class:`Output` object.

        """
        available = self.available_types

        dispatch_extension = dispatch_result.extension
        if dispatch_extension:
            # There's an extension in the URI path, guess the media type from it
            dispatch_accept = mimetypes.guess_type('a.' + dispatch_extension, strict=False)[0]
            if dispatch_accept is None:
                # The extension is unknown, raise NotFound
                raise NotFound()
            accept = dispatch_accept
            # Accept `media/type` for `media/x-type`
            i = accept.find('/x-')
            if i > 0:
                accept += ',' + accept[:i+1] + accept[i+3:]
            # Accept custom JSON media type
            if accept == 'application/json':
                accept += ',' + self.request_processor.media_type_json
        elif len(available) == 1:
            # If there's only one available type and no extension in the path,
            # then we ignore the Accept header
            return self.render_for_type(available[0], context)
        else:
            dispatch_accept = None
            accept = accept_header

        if accept:
            try:
                best_match = mimeparse.best_match(available, accept)
            except ValueError:
                # Unparseable accept header
                best_match = None
            if best_match:
                return self.render_for_type(best_match, context)
            elif best_match == '':
                if dispatch_accept is not None:
                    # e.g. client requested `/foo.json` but `/foo.spt` has no JSON page
                    raise NotFound()
                raise NegotiationFailure(accept, available)

        # Fall back to the first available type
        return self.render_for_type(available[0], context)

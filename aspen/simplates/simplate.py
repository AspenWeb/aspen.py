import re
import tokenize
from typing import Any, Callable, Dict

from ..http.resource import Dynamic, check_resource_path
from ..output import Output
from .pagination import split_and_escape, parse_specline, Page


renderer_re = re.compile(r'[a-z0-9.-_]+$')
media_type_re = re.compile(r'[A-Za-z0-9.+*-]+/[A-Za-z0-9.+*-]+$')


class SimplateDefaults:

    def __init__(
        self,
        renderers_by_media_type: Dict[str, str],
        renderer_factories: Dict[str, Callable],
        initial_context: Dict[str, Any],
    ):
        """
        Things that are usually the same across all simplates:

        renderers_by_media_type - dict[media_type_name] -> renderer_name
        renderer_factories - dict[renderer_name] -> renderer_factory
        initial_context - initial context passed into the 'run-once' page
        """
        self.renderers_by_media_type = renderers_by_media_type
        self.renderer_factories = renderer_factories
        self.initial_context = initial_context


class Simplate(Dynamic):
    """A simplate is a dynamic resource with multiple syntaxes in one file.

    Args:
        fspath (str): the absolute filesystem path of this simplate

    """

    __slots__ = (
        'fspath', 'default_media_type', 'renderers', 'page_one', 'page_two',
    )

    defaults: SimplateDefaults

    def __init__(self, request_processor, fspath):
        self.request_processor = request_processor
        self.fspath = fspath
        self.default_media_type = request_processor.guess_media_type(fspath.rsplit('.', 1)[0])

        self.renderers = {}         # mapping of media type to Renderer objects
        self.available_types = []   # ordered sequence of media types
        with tokenize.open(check_resource_path(request_processor, fspath)) as fh:
            pages = self.parse_into_pages(fh.read())
        self.compile_pages(pages)
        self.page_one, self.page_two = pages[0], pages[1]
        for renderer, media_type in pages[2:]:
            if media_type in self.renderers:
                raise SyntaxError("Two content pages defined for %s." % media_type)
            self.available_types.append(media_type)
            self.renderers[media_type] = renderer

    def render_for_type(self, media_type, context):
        """Render the simplate.

        Args:
            media_type (str): the media type of the page to render
            context (dict): execution context values you wish to supply

        .. warning: The ``context`` dict is updated with values from the first
                    and second pages of the simplate.

        Returns: an :class:`Output` object.
        """

        # create Output object and put it in the context
        output = context['output'] = Output(media_type=media_type)
        # update the context with values from the first page
        context.update(self.page_one)
        # use this as the context to execute the second page in
        exec(self.page_two, context)
        # skip rendering if the second page has already filled output.body
        if output.body is not None:
            return output

        if '__all__' in context:
            # templates will only see variables named in __all__
            context = dict((k, context[k]) for k in context['__all__'])

        # load the renderer
        render = self.renderers[media_type]
        # render
        output.body = render(context)

        return output

    def parse_into_pages(self, decoded):
        """Given a bytestring that is the entire simplate, return a list of pages.

        If there's one page, it's a template.

        If there's more than one page, the first page is always python and the
        last is always a template.

        If there's more than two pages, the second page is python *unless it has
        a specline*, which makes it a template.

        """
        pages = list(split_and_escape(decoded))
        npages = len(pages)
        blank = [Page('')]

        if npages == 1:
            pages = blank + blank + pages
        elif npages == 2:
            pages = blank + pages
        elif pages[1].header:  # it's got a header, so it's a template
            pages = blank + pages

        return pages

    def compile_pages(self, pages):
        """Given a list of pages, replace the pages with objects.

        Page 0 is the 'run once' page - it is executed and the resulting
        context stored in :obj:`self.pages[0]`.

        Page 1 is the 'run every' page - it is compiled for easier execution
        later, and stored in :obj:`self.pages[1]`.

        Subsequent pages are templates, so each one's content type and
        respective renderer are stored as a tuple in :obj:`self.pages[n]`.
        """

        # Exec the first page and compile the second.
        # ===========================================

        one, two = pages[:2]

        context = dict()
        context['__file__'] = self.fspath
        context.update(self.defaults.initial_context)

        one = compile(one.padded_content, self.fspath, 'exec')
        exec(one, context)     # mutate context
        one = context          # store it

        two = compile(two.padded_content, self.fspath, 'exec')

        pages[:2] = (one, two)
        pages[2:] = [self.compile_page(page) for page in pages[2:]]

    def compile_page(self, page):
        """Given a :class:`Page`, return a :obj:`(renderer, media_type)` pair.
        """
        make_renderer, media_type = self._parse_specline(page.header)
        renderer = make_renderer(self.fspath, page.content, media_type, page.offset)
        return (renderer, media_type)

    def _parse_specline(self, specline):
        """Given a bytestring, return a two-tuple.

        The incoming string is expected to be of the form:

            media_type via renderer

        Both are optional.

        The media_type will default to the default_media_type supplied to
        this simplate at instantiation time.  (Possibly determined by a
        file extension or other metadata)

        The renderer will be computed based on media type if absent.

        The return two-tuple contains a render function and a media
        type (as unicode). SyntaxError is raised if there aren't one or two
        parts or if either of the parts is malformed. If only one part is
        passed in it's interpreted as a media type.

        """
        # Parse into parts
        media_type, renderer = parse_specline(specline)

        if media_type == '':
            # no media type specified, use the default
            media_type = self.default_media_type
        if renderer == '':
            # no renderer specified, use the default
            renderer = self.defaults.renderers_by_media_type[media_type]

        # Validate media type.
        if media_type_re.match(media_type) is None:
            msg = ("Malformed media type '%s' in specline '%s'. It must match "
                   "%s.")
            msg %= (media_type, specline, media_type_re.pattern)
            raise SyntaxError(msg)

        # Hydrate and validate renderer.
        make_renderer = self._get_renderer_factory(media_type, renderer)

        # Return.
        return (make_renderer, media_type)

    def _get_renderer_factory(self, media_type, renderer):
        """Given two bytestrings, return a renderer factory or None.
        """
        factories = self.defaults.renderer_factories
        if renderer_re.match(renderer) is None:
            possible = ', '.join(sorted(factories.keys()))
            msg = ("Malformed renderer %s. It must match %s. Possible "
                   "renderers (might need third-party libs): %s.")
            raise SyntaxError(msg % (renderer, renderer_re.pattern, possible))

        make_renderer = factories.get(renderer, None)
        if isinstance(make_renderer, ImportError):
            raise make_renderer
        elif make_renderer is None:
            possible = []
            legend = ''
            for k, v in sorted(factories.items()):
                if isinstance(v, ImportError):
                    k = '*' + k
                    legend = " (starred are missing third-party libraries)"
                possible.append(k)
            possible = ', '.join(possible)
            raise ValueError("Unknown renderer for %s: %s. Possible "
                             "renderers%s: %s."
                             % (media_type, renderer, legend, possible))
        return make_renderer

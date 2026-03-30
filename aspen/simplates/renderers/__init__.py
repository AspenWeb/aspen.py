import sys
from importlib.metadata import entry_points


# Built-in renderers
BUILTIN_RENDERERS = [
    'stdlib_format', 'stdlib_percent', 'stdlib_template', 'json_dump', 'jsonp_dump',
]

RENDERERS = BUILTIN_RENDERERS[:]


for entrypoint in entry_points().select(group='aspen.renderers'):
    RENDERERS.append(entrypoint.name)

RENDERERS.sort()


def factories(configuration):
    """return a dict of render factory names to the factories themselves"""
    renderer_factories = {}
    # import the built-in renderers
    for name in BUILTIN_RENDERERS:
        # Pre-populate renderers so we can report on ImportErrors early
        try:
            capture = {}
            python_syntax = 'from aspen.simplates.renderers.%s import Factory'
            exec(python_syntax % name, capture)
            make_renderer = capture['Factory'](configuration)
        except ImportError as err:
            make_renderer = err
            err.info = sys.exc_info()
        renderer_factories[name] = make_renderer

    # import renderers provided by other packages
    for entrypoint in entry_points().select(group='aspen.renderers'):
        render_module = entrypoint.load()
        renderer_factories[entrypoint.name] = render_module.Factory(configuration)
    return renderer_factories


# abstract bases
# ==============
# The base is actually functional. It's a pass-through.

class Renderer:
    """The base class of renderers.
    """

    def __init__(self, factory, filepath, raw, media_type, offset):
        """Takes a Factory, three bytestrings, and an int.
        """
        self._filepath = filepath
        self._factory = factory
        self._changes_reload = factory._changes_reload
        self.meta = self._factory.meta
        self.raw = raw
        self.media_type = media_type
        self.offset = offset
        self.padded = ('\n' * offset) + self.raw
        self.compiled = self.compile(self._filepath, self.padded)

    def __call__(self, context):
        if self._changes_reload:
            self.meta = self._factory._update_meta()
            self.compiled = self.compile(self._filepath, self.padded)
        r = self.render_content(context)
        if r[:self.offset] == self.padded[:self.offset]:
            # The padding is still there, strip it
            return r[self.offset:]
        return r

    def compile(self, filepath, padded):
        """Override.

        Whatever you return from this will be set on self.compiled the first
        time the renderer is called. If changes_reload is True then this will
        be called every time the renderer is called. You can then use
        self.compiled in your render_content method as needed.

        """
        return padded

    def render_content(self, context):
        """Override. Context is a dict.

        You can use these attributes::

            self.raw        the raw bytes of the content page
            self.compiled   the result of self.compile (generally a template in
                             compiled object form)
            self.meta       the result of Factory.compile_meta
            self.media_type the media type of the page
            self.offset     the line number at which the page starts

        """
        return self.raw  # pass-through


class Factory:
    """The base class of renderer factories.
    """

    Renderer = Renderer

    def __init__(self, configuration):
        self._configuration = configuration
        self._changes_reload = configuration.changes_reload
        self.meta = self.compile_meta(configuration)

    def __call__(self, filepath, raw, media_type, offset):
        """Given three bytestrings and an int, return a callable.
        """
        self._update_meta()
        return self.Renderer(self, filepath, raw, media_type, offset)

    def _update_meta(self):
        if self._changes_reload:
            self.meta = self.compile_meta(self._configuration)
        return self.meta  # used in our child, Renderer

    def compile_meta(self, configuration):
        """Takes a configuration object. Override as needed.

        Whatever you return from this will be set on self.meta the first time
        the factory is called, or every time if changes_reload is True. You can
        then use self.meta in your Renderer class as needed.

        """
        return None

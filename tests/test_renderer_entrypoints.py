import importlib
import importlib.metadata as importlib_metadata
import sys


MODULE_NAME = 'aspen.simplates.renderers'


def import_renderers_module(monkeypatch, entry_points_func=None):
    monkeypatch.delitem(sys.modules, MODULE_NAME, raising=False)
    if entry_points_func is not None:
        monkeypatch.setattr(importlib_metadata, 'entry_points', entry_points_func)
    return importlib.import_module(MODULE_NAME)


def test_renderers_module_imports(monkeypatch):
    module = import_renderers_module(monkeypatch)
    assert module.RENDERERS == sorted(module.RENDERERS)
    assert module.BUILTIN_RENDERERS == [
        'stdlib_format',
        'stdlib_percent',
        'stdlib_template',
        'json_dump',
        'jsonp_dump',
    ]


def test_renderers_module_reads_selectable_entry_points(monkeypatch):
    class EntryPoint:
        def __init__(self, name):
            self.name = name

    module = import_renderers_module(
        monkeypatch,
        entry_points_func=lambda **kw: [EntryPoint('selectable-renderer')],
    )
    assert 'selectable-renderer' in module.RENDERERS

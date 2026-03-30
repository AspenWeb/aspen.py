import importlib
import importlib.metadata as importlib_metadata
import sys

import pytest


MODULE_NAME = 'aspen.simplates.renderers'


def import_renderers_module(monkeypatch, entry_points_func=None):
    monkeypatch.setitem(sys.modules, 'pkg_resources', None)
    monkeypatch.delitem(sys.modules, MODULE_NAME, raising=False)
    if entry_points_func is not None:
        monkeypatch.setattr(importlib_metadata, 'entry_points', entry_points_func)
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(str(exc))


def test_renderers_module_imports_without_pkg_resources(monkeypatch):
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

    class EntryPoints:
        def select(self, **kwargs):
            assert kwargs == {'group': 'aspen.renderers'}
            return [EntryPoint('selectable-renderer')]

    module = import_renderers_module(monkeypatch, entry_points_func=lambda: EntryPoints())

    assert 'selectable-renderer' in module.RENDERERS

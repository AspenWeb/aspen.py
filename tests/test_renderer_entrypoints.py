import importlib
import sys

import pytest


MODULE_NAME = 'aspen.simplates.renderers'


def import_renderers_module(monkeypatch):
    monkeypatch.setitem(sys.modules, 'pkg_resources', None)
    monkeypatch.delitem(sys.modules, MODULE_NAME, raising=False)
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


def test_iter_entry_points_supports_legacy_mapping_results(monkeypatch):
    module = import_renderers_module(monkeypatch)

    class EntryPoint:
        def __init__(self, name):
            self.name = name

    monkeypatch.setattr(module, 'entry_points', lambda: {
        'aspen.renderers': [EntryPoint('legacy-renderer')],
    })

    assert [ep.name for ep in module._iter_entry_points('aspen.renderers')] == ['legacy-renderer']


def test_iter_entry_points_supports_selectable_results(monkeypatch):
    module = import_renderers_module(monkeypatch)

    class EntryPoint:
        def __init__(self, name):
            self.name = name

    class EntryPoints:
        def select(self, **kwargs):
            assert kwargs == {'group': 'aspen.renderers'}
            return [EntryPoint('selectable-renderer')]

    monkeypatch.setattr(module, 'entry_points', lambda: EntryPoints())

    assert [ep.name for ep in module._iter_entry_points('aspen.renderers')] == [
        'selectable-renderer',
    ]

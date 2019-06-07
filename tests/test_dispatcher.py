from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import pytest

from filesystem_tree import FilesystemTree

from aspen.exceptions import SlugCollision, WildcardCollision
from aspen.http.request import Path
from aspen.request_processor.dispatcher import (
    DISPATCHER_CLASSES, DispatchStatus, legacy_collision_handler
)


# Helpers
# =======

def assert_match(
    harness, request_path, expected_match,
    status=DispatchStatus.okay, wildcards=None, extension=None, canonical=None
):
    result = harness.request_processor.dispatch(Path(request_path))
    assert result.status == status
    assert result.match == harness.fs.www.resolve(expected_match)
    assert result.wildcards == wildcards
    assert result.extension == extension
    assert result.canonical == canonical

def assert_missing(harness, request_path):
    result = harness.request_processor.dispatch(Path(request_path))
    assert result.status == DispatchStatus.missing
    assert result.match is None

def assert_unindexed(harness, request_path, wildcards=None, extension=None, canonical=None):
    result = harness.request_processor.dispatch(Path(request_path))
    assert result.status == DispatchStatus.unindexed
    assert result.match == harness.fs.www.resolve(request_path) + os.path.sep
    assert result.wildcards == wildcards
    assert result.extension == extension
    assert result.canonical == canonical

def assert_wildcards(harness, request_path, expected_vals):
    result = harness.request_processor.dispatch(Path(request_path))
    assert result.wildcards == expected_vals

def dispatch(harness, request_path):
    return harness.request_processor.dispatch(Path(request_path))

NEGOTIATED_SIMPLATE="""[-----]
[-----] text/plain
Greetings, program!
[-----] text/html
<h1>Greetings, Program!</h1>"""


# dispatcher.dispatch
# ===================

@pytest.mark.parametrize('dispatcher_class', DISPATCHER_CLASSES)
def test_dispatcher_returns_a_result(dispatcher_class):
    www = FilesystemTree()
    www.mk(('index.html', 'Greetings, program!'),)
    dispatcher = dispatcher_class(
        www_root    = www.root,
        is_dynamic  = lambda n: n.endswith('.spt'),
        indices     = ['index.html'],
        typecasters = {},
    )
    dispatcher.build_dispatch_tree()
    result = dispatcher.dispatch('/', [''])
    assert result.status == DispatchStatus.okay
    assert result.match == os.path.join(www.root, 'index.html')
    assert result.wildcards == None

@pytest.mark.parametrize('dispatcher_class', DISPATCHER_CLASSES)
def test_dispatcher_returns_unindexed_for_unindexed_directory(dispatcher_class):
    www = FilesystemTree()
    dispatcher = dispatcher_class(
        www_root    = www.root,
        is_dynamic  = lambda n: n.endswith('.spt'),
        indices     = [],
        typecasters = {},
    )
    dispatcher.build_dispatch_tree()
    r = dispatcher.dispatch('/', [''])
    assert r.status == DispatchStatus.unindexed
    assert r.match == www.root + os.path.sep

def test_dispatch_when_filesystem_has_been_modified():
    # Create an empty www_root
    www = FilesystemTree()
    # Help the dispatchers that rely on `mtime`
    st = os.stat(www.root)
    os.utime(www.root, (st.st_atime - 10, st.st_mtime - 10))
    # Initialize the dispatchers
    dispatchers = []
    for dispatcher_class in DISPATCHER_CLASSES:
        dispatchers.append(dispatcher_class(
            www_root    = www.root,
            is_dynamic  = lambda n: n.endswith('.spt'),
            indices     = ['index.html'],
            typecasters = {},
        ))
        dispatchers[-1].build_dispatch_tree()
    # Now add an index file and try to dispatch
    www.mk(('index.html', 'Greetings, program!'))
    for dispatcher in dispatchers:
        print("Attempting dispatch with", dispatcher.__class__.__name__)
        result = dispatcher.dispatch('/', [''])
        if dispatcher.__class__.__name__ == 'UserlandDispatcher':
            assert result.status == DispatchStatus.unindexed
            assert result.match == www.root + os.path.sep
        else:
            assert result.status == DispatchStatus.okay
            assert result.match == www.resolve('index.html')
        assert result.wildcards is None
        assert result.extension is None
        assert result.canonical is None


# Indices
# =======

def test_static_index(harness):
    harness.fs.www.mk(('index.html', 'Greetings, program!'))
    assert_match(harness, '/', 'index.html')

def test_index_without_extention(harness):
    harness.fs.www.mk(('index', 'Greetings, program!'))
    assert_match(harness, '/', 'index')

def test_dynamic_index(harness):
    harness.fs.www.mk(('index.spt', NEGOTIATED_SIMPLATE))
    assert_match(harness, '/', 'index.spt')

def test_empty_root(harness):
    assert_unindexed(harness, '/')

def test_unrecognized_index(harness):
    harness.fs.www.mk(('index.html', "Greetings, program!"),)
    harness.hydrate_request_processor(indices=["default.html"])
    assert_unindexed(harness, '/')

def test_dispatcher_matches_second_index_if_first_is_missing(harness):
    harness.fs.www.mk(('default.html', "Greetings, program!"),)
    harness.hydrate_request_processor(indices=["index.html", "default.html"])
    assert_match(harness, '/', 'default.html')

def test_dispatcher_matches_explicit_index(harness):
    harness.fs.www.mk(('index.html', "Greetings, program!"),)
    harness.hydrate_request_processor(indices=["index.html", "default.html"])
    assert_match(harness, '/index.html', 'index.html', canonical='/')

def test_dispatcher_matches_explicit_second_index(harness):
    harness.fs.www.mk(('default.html', "Greetings, program!"),)
    harness.hydrate_request_processor(indices=["index.html", "default.html"])
    assert_match(harness, '/default.html', 'default.html', canonical='/')

def test_dispatch_with_two_indexes(harness):
    harness.fs.www.mk(
        ('default.html', "Greetings, program!"),
        ('index.html', "Greetings, program!")
    )
    harness.hydrate_request_processor(indices=["index.html", "default.html"])
    assert_match(harness, '/', 'index.html')
    assert_match(harness, '/index.html', 'index.html', canonical='/')
    assert_match(harness, '/default.html', 'default.html')


# Negotiated Fall-through
# =======================

def test_indirect_negotiation_can_passthrough_static(harness):
    harness.fs.www.mk(('foo.html', "Greetings, program!"),)
    assert_match(harness, 'foo.html', 'foo.html')

def test_indirect_negotiation_can_passthrough_renderered(harness):
    harness.fs.www.mk(('foo.html.spt', NEGOTIATED_SIMPLATE),)
    assert_match(harness, 'foo.html', 'foo.html.spt')

def test_indirect_negotiation_can_passthrough_negotiated(harness):
    harness.fs.www.mk(('foo', "Greetings, program!"),)
    assert_match(harness, 'foo', 'foo')

def test_indirect_negotiation_modifies_one_dot(harness):
    harness.fs.www.mk(('foo.spt', NEGOTIATED_SIMPLATE),)
    assert_match(harness, 'foo.html', 'foo.spt', extension='html')

def test_indirect_negotiation_skips_two_dots(harness):
    harness.fs.www.mk(('foo.bar.spt', NEGOTIATED_SIMPLATE),)
    assert_match(harness, 'foo.bar.html', 'foo.bar.spt', extension='html')

def test_indirect_negotiation_prefers_rendered(harness):
    harness.fs.www.mk( ('foo.html', "Greetings, program!")
          , ('foo', "blah blah blah")
           )
    assert_match(harness, 'foo.html', 'foo.html')

def test_indirect_negotiation_really_prefers_rendered(harness):
    harness.fs.www.mk( ('foo.html', "Greetings, program!")
          , ('foo.', "blah blah blah")
           )
    assert_match(harness, 'foo.html', 'foo.html')

def test_indirect_negotiation_really_prefers_rendered_2(harness):
    harness.fs.www.mk( ('foo.html', "Greetings, program!")
          , ('foo', "blah blah blah")
           )
    assert_match(harness, 'foo.html', 'foo.html')

def test_indirect_negotation_doesnt_do_dirs(harness):
    assert_missing(harness, 'foo.html')


# Virtual Paths
# =============

def test_virtual_path_can_passthrough(harness):
    harness.fs.www.mk(('foo.html', "Greetings, program!"),)
    assert_match(harness, 'foo.html', 'foo.html')

def test_unfound_virtual_path_passes_through(harness):
    harness.fs.www.mk(('%bar/foo.html', "Greetings, program!"),)
    assert_missing(harness, '/blah/flah.html')

def test_virtual_path_is_virtual(harness):
    harness.fs.www.mk(('%bar/foo.html', "Greetings, program!"),)
    assert_match(harness, '/blah/foo.html', '%bar/foo.html', wildcards={'bar': 'blah'})

def test_virtual_path_sets_path(harness):
    harness.fs.www.mk(('%bar/foo.spt', NEGOTIATED_SIMPLATE),)
    assert_wildcards(harness, '/blah/foo.html', {'bar': 'blah'} )

def test_virtual_path_sets_unicode_path(harness):
    harness.fs.www.mk(('%bar/foo.html', "Greetings, program!"),)
    assert_wildcards(harness, '/%E2%98%83/foo.html', {'bar': '\u2603'})

def test_virtual_path_with_typecast(harness):
    harness.fs.www.mk(('%year.int/foo.html', "Greetings, program!"),)
    assert_wildcards(harness, '/1999/foo.html', {'year.int': '1999'})

def test_virtual_path_raises_on_direct_access(harness):
    assert_missing(harness, '/%name/foo.html')

def test_virtual_path_raises_404_on_direct_access(harness):
    assert_missing(harness, '/%name/foo.html')

def test_virtual_path_directory(harness):
    harness.fs.www.mk(('%first/index.html', "Greetings, program!"),)
    assert_match(harness, '/foo/', '%first/index.html', wildcards={'first': 'foo'})

def test_virtual_path_file(harness):
    harness.fs.www.mk(('foo/%bar.html.spt', NEGOTIATED_SIMPLATE),)
    assert_match(harness, '/foo/blah.html', 'foo/%bar.html.spt', wildcards={'bar': 'blah'})

def test_virtual_path_file_only_last_part(harness):
    harness.fs.www.mk(('foo/%bar.html.spt', NEGOTIATED_SIMPLATE),)
    assert_match(harness, '/foo/blah/baz.html', 'foo/%bar.html.spt', wildcards={'bar': 'blah/baz'})

def test_virtual_path_file_only_last_part____no_really(harness):
    harness.fs.www.mk(('foo/%bar.html.spt', "Greetings, program!"),)
    assert_missing(harness, '/foo/blah.html/')

def test_virtual_path_file_key_val_set(harness):
    harness.fs.www.mk(('foo/%bar.html.spt', NEGOTIATED_SIMPLATE),)
    assert_wildcards(harness, '/foo/blah.html', {'bar': 'blah'})

def test_virtual_path_file_key_val_without_cast(harness):
    harness.fs.www.mk(('foo/%bar.html.spt', NEGOTIATED_SIMPLATE),)
    assert_wildcards(harness, '/foo/537.html', {'bar': '537'})

def test_virtual_path_file_key_val_with_cast(harness):
    harness.fs.www.mk(('foo/%bar.int.html.spt', NEGOTIATED_SIMPLATE),)
    assert_wildcards(harness, '/foo/537.html', {'bar.int': '537'})

def test_virtual_path_file_key_val_percent(harness):
    harness.fs.www.mk(('foo/%bar.spt', NEGOTIATED_SIMPLATE),)
    assert_wildcards(harness, '/foo/%25blah', {'bar': '%blah'})

def test_virtual_path_file_not_dir(harness):
    harness.fs.www.mk( ('%foo/bar.html', "Greetings from bar!")
          , ('%baz.html.spt', NEGOTIATED_SIMPLATE)
           )
    assert_match(harness, '/bal.html', '%baz.html.spt', wildcards={'baz': 'bal'})

def test_virtual_path_when_dir_is_more_specific(harness):
    harness.fs.www.mk(
        ('%foo/%bar/file.html.spt', "Hello world!"),
        ('%foo.html.spt', "Hello world!")
    )
    assert_wildcards(harness, '/~/x/file.html', {'foo': '~', 'bar': 'x'})

def test_static_files_are_not_wild(harness):
    harness.fs.www.mk(('foo/%bar.html', "Greetings, program!"),)
    assert_missing(harness, '/foo/blah.html')
    assert_match(harness, '/foo/%25bar.html', 'foo/%bar.html')

def test_fallback_to_wildleaf_in_parent_directory(harness):
    harness.fs.www.mk(
        ('%foo/%bar/file.html', "Hello world!"),
        ('%foo/%bar.html', "Hello world!"),
        ('%foo.spt', NEGOTIATED_SIMPLATE)
    )
    assert_match(harness, '/~/x/file.txt', '%foo.spt', wildcards={'foo': '~/x/file.txt'})


# negotiated *and* virtual paths
# ==============================

def test_virtual_path__and_indirect_neg_file_not_dir(harness):
    harness.fs.www.mk( ('%foo/bar.html', "Greetings from bar!")
          , ('%baz.spt', NEGOTIATED_SIMPLATE)
           )
    assert_match(harness, '/bal.html', '%baz.spt', wildcards={'baz': 'bal.html'})

def test_virtual_path_and_indirect_neg_noext(harness):
    harness.fs.www.mk(('%foo/bar', "Greetings program!"),)
    assert_match(harness, '/greet/bar', '%foo/bar', wildcards={'foo': 'greet'})

def test_virtual_path_and_indirect_neg_ext(harness):
    harness.fs.www.mk(('%foo/bar.spt', NEGOTIATED_SIMPLATE),)
    assert_match(harness, '/greet/bar.html', '%foo/bar.spt',
                 wildcards={'foo': 'greet'}, extension='html')


# Collisions
# ==========

def test_variable_name_used_twice_in_path_results_in_WildcardCollision(harness):
    harness.fs.www.mk(('%foo/bar/%foo.spt', "Hello world!"))
    with pytest.raises(WildcardCollision):
        harness.hydrate_request_processor()

def test_same_name_used_in_different_dirs_is_okay(harness):
    harness.fs.www.mk(
        ('foo/%bar.spt', "Hello world!"),
        ('foo/z/%bar.spt', "Hello world!"),
    )
    assert_match(harness, '/foo/y/bar', 'foo/%bar.spt', wildcards={'bar': 'y/bar'})
    assert_match(harness, '/foo/z/bar', 'foo/z/%bar.spt', wildcards={'bar': 'bar'})

def test_same_dir_name_used_in_different_paths_is_okay(harness):
    harness.fs.www.mk(
        ('%foo/bar.spt', "Hello world!"),
        ('x/%foo/bar.spt', "Hello world!"),
    )
    assert_match(harness, '/foo/bar', '%foo/bar.spt', wildcards={'foo': 'foo'})
    assert_match(harness, '/x/foo/bar', 'x/%foo/bar.spt', wildcards={'foo': 'foo'})

def test_collision_between_file_and_directory(harness):
    harness.fs.www.mk(
        ('foo/bar.spt', ''),
        ('foo/bar/index.spt', ''),
    )
    with pytest.raises(SlugCollision):
        harness.hydrate_request_processor()

def test_collision_between_two_dir_wildcards(harness):
    harness.fs.www.mk(
        ('%first/foo.html', "Greetings, program!"),
        ('%second/foo.html', "WWAAAAAAAAAAAA!!!!!!!!"),
    )
    # Test with default collision handler, should raise an exception.
    with pytest.raises(SlugCollision):
        harness.hydrate_request_processor()
    # Test with legacy collision handler, should favor the first node.
    harness.hydrate_request_processor(
        dispatcher_options=dict(collision_handler=legacy_collision_handler),
    )
    assert_match(harness, '/1999/foo.html', '%first/foo.html', wildcards={'first': '1999'})


# trailing slash
# ==============

def test_dispatcher_passes_through_files(harness):
    harness.fs.www.mk(('foo/index.html', "Greetings, program!"),)
    assert_missing(harness, '/foo/537.html')

def test_trailing_slash_passes_dirs_with_slash_through(harness):
    harness.fs.www.mk(('foo/index.html', "Greetings, program!"),)
    assert_match(harness, '/foo/', '/foo/index.html')

def test_dispatcher_passes_through_virtual_dir_with_trailing_slash(harness):
    harness.fs.www.mk(('%foo/index.html', "Greetings, program!"),)
    assert_match(harness, '/foo/', '/%foo/index.html', wildcards={'foo': 'foo'})

def test_dispatcher_matches_dir_even_without_trailing_slash(harness):
    harness.fs.www.mk('foo',)
    assert_unindexed(harness, '/foo', canonical='/foo/')

def test_dispatcher_matches_virtual_dir_even_without_trailing_slash(harness):
    harness.fs.www.mk('%foo',)
    result = dispatch(harness, '/foo')
    assert result.status == DispatchStatus.unindexed
    assert result.match == harness.fs.www.resolve('%foo') + os.path.sep
    assert result.wildcards == {'foo': 'foo'}
    assert result.canonical == '/foo/'

def test_trailing_on_virtual_paths_missing(harness):
    harness.fs.www.mk('%foo/%bar/%baz/',)
    result = dispatch(harness, '/foo/bar/baz')
    assert result.status == DispatchStatus.unindexed
    assert result.match == harness.fs.www.resolve('%foo/%bar/%baz') + os.path.sep
    assert result.wildcards == {'foo': 'foo', 'bar': 'bar', 'baz': 'baz'}
    assert result.canonical == '/foo/bar/baz/'

def test_trailing_on_virtual_paths(harness):
    harness.fs.www.mk(('%foo/%bar/%baz/index.html', "Greetings program!"),)
    assert_match(harness, '/foo/bar/baz/', '/%foo/%bar/%baz/index.html',
                 wildcards={'foo': 'foo', 'bar': 'bar', 'baz': 'baz'})

def test_trailing_slash_matches_wild_leaf(harness):
    harness.fs.www.mk(('foo/%bar.html.spt', "Greetings program!"),)
    assert_match(harness, '/foo/', 'foo/%bar.html.spt', wildcards={'bar': ''})

def test_missing_trailing_slash_matches_wild_leaf(harness):
    harness.fs.www.mk(('foo/%bar.html.spt', "Greetings program!"),)
    assert_match(harness, '/foo', 'foo/%bar.html.spt',
                 wildcards={'bar': ''}, canonical='/foo/')

def test_dont_confuse_files_for_dirs(harness):
    harness.fs.www.mk(('foo.html', 'Greetings, Program!'),)
    assert_missing(harness, '/foo.html/')
    assert_missing(harness, '/foo.html/bar')

def test_wildleaf_with_extention_doesnt_match_trailing_slash(harness):
    harness.fs.www.mk(
        ('%name/index.html.spt', ''),
        ('%name/%cheese.txt.spt', ''),
    )
    assert_missing(harness, '/chad/cheddar.txt/')

def test_wildleaf_without_extention_matches_trailing_slash(harness):
    harness.fs.www.mk(
        ('%name/index.html.spt', ''),
        ('%name/%cheese.spt', ''),
    )
    assert_match(harness, '/chad/cheddar.txt/', '%name/%cheese.spt',
                 wildcards={'name': 'chad', 'cheese': 'cheddar.txt/'})

def test_extra_slash_matches(harness):
    harness.fs.www.mk(('foo/bar.spt', ''))
    assert_match(harness, '/foo/bar/', 'foo/bar.spt', canonical='/foo/bar')

def test_resource_in_parent_directory_is_used_as_index(harness):
    harness.fs.www.mk(('foo/bar.spt', ''))
    harness.fs.www.mk(('foo/bar/baz.spt', ''))
    assert_match(harness, '/foo/bar/', 'foo/bar.spt')


# path part params
# ================

def test_path_part_with_params_works(harness):
    harness.fs.www.mk(('foo/index.html', "Greetings program!"),)
    assert_match(harness, '/foo;a=1/', '/foo/index.html')

def test_path_part_params_vpath(harness):
    harness.fs.www.mk(('%bar/index.html', "Greetings program!"),)
    assert_match(harness, '/foo;a=1;b=;a=2;b=3/', '/%bar/index.html', wildcards={'bar': 'foo'})

def test_path_part_params_static_file(harness):
    harness.fs.www.mk(('/foo/bar.html', "Greetings program!"),)
    assert_match(harness, '/foo/bar.html;a=1;b=;a=2;b=3', '/foo/bar.html')

def test_path_part_params_simplate(harness):
    harness.fs.www.mk(('/foo/bar.html.spt', NEGOTIATED_SIMPLATE),)
    assert_match(harness, '/foo/bar.html;a=1;b=;a=2;b=3', '/foo/bar.html.spt')

def test_path_part_params_negotiated_simplate(harness):
    harness.fs.www.mk(('/foo/bar.spt', NEGOTIATED_SIMPLATE),)
    assert_match(harness, '/foo/bar.txt;a=1;b=;a=2;b=3', '/foo/bar.spt', extension='txt')

def test_path_part_params_greedy_simplate(harness):
    harness.fs.www.mk(('/foo/%bar.spt', NEGOTIATED_SIMPLATE),)
    assert_match(harness, '/foo/baz/buz;a=1;b=;a=2;b=3/blam.html', '/foo/%bar.spt',
                 wildcards={'bar': 'baz/buz/blam.html'})


# mongs
# =====
# These surfaced when porting mongs from Aspen 0.8.

def test_virtual_path_parts_can_be_empty(harness):
    harness.fs.www.mk(('foo/%bar/index.html.spt', NEGOTIATED_SIMPLATE),)
    assert_wildcards(harness, '/foo//' , {'bar': ''})

def test_file_matches_in_face_of_dir(harness):
    harness.fs.www.mk( ('%page/index.html.spt', NEGOTIATED_SIMPLATE)
          , ('%value.txt.spt', NEGOTIATED_SIMPLATE)
           )
    assert_wildcards(harness, '/baz.txt', {'value': 'baz'})

def test_file_doesnt_match_if_extensions_dont_match(harness):
    harness.fs.www.mk(
        ('%page/index.html.spt', NEGOTIATED_SIMPLATE),
        ('%value.txt.spt', NEGOTIATED_SIMPLATE)
    )
    assert_wildcards(harness, '/baz.html', {'page': 'baz.html'})

def test_file_matches_extension(harness):
    harness.fs.www.mk( ('%value.json.spt', '[-----]\n[-----]\n{"Greetings,": "program!"}')
          , ('%value.txt.spt', NEGOTIATED_SIMPLATE)
           )
    assert_match(harness, '/baz.json', "%value.json.spt", wildcards={'value': 'baz'})

def test_file_matches_other_extension(harness):
    harness.fs.www.mk( ('%value.json.spt', '[-----]\n[-----]\n{"Greetings,": "program!"}')
          , ('%value.txt.spt', NEGOTIATED_SIMPLATE)
           )
    assert_match(harness, '/baz.txt', "%value.txt.spt", wildcards={'value': 'baz'})


def test_virtual_file_with_no_extension_works(harness):
    harness.fs.www.mk(('%value.spt', NEGOTIATED_SIMPLATE),)
    assert_match(harness, '/baz.txt', '%value.spt', wildcards={'value': 'baz.txt'})

def test_normal_file_with_no_extension_works(harness):
    harness.fs.www.mk(
        ('%value.spt', NEGOTIATED_SIMPLATE),
        ('value', '{"Greetings,": "program!"}')
    )
    assert_match(harness, '/baz.txt', '%value.spt', wildcards={'value': 'baz.txt'})

def test_file_with_no_extension_matches(harness):
    harness.fs.www.mk( ('%value.spt', NEGOTIATED_SIMPLATE)
          , ('value', '{"Greetings,": "program!"}')
           )
    assert_match(harness, '/baz', '%value.spt', wildcards={'value': 'baz'})

def test_dont_serve_hidden_files(harness):
    harness.fs.www.mk(('.secret_data', ''),)
    assert_missing(harness, '/.secret_data')

def test_do_serve_files_under_well_known_directory(harness):
    harness.fs.www.mk(('.well-known/security.txt', 'Lorem ipsum'),)
    assert_match(harness, '/.well-known/security.txt', '.well-known/security.txt')

def test_dont_serve_spt_file_source(harness):
    harness.fs.www.mk(('foo.html.spt', "Greetings, program!"),)
    assert_missing(harness, '/foo.html.spt')


# dispatch_result.extension
# =========================

def test_dispatcher_sets_extension(harness):
    harness.fs.www.mk(('foo.spt', "Greetings, program!"))
    assert_match(harness, '/foo.css', 'foo.spt', extension='css')

def test_extension_is_set_even_when_unknown(harness):
    harness.fs.www.mk(('foo.spt', "Greetings, program!"))
    assert_match(harness, '/foo.unknown-extension', 'foo.spt', extension='unknown-extension')

def test_extension_is_None_when_url_doesnt_contain_any(harness):
    harness.fs.www.mk(('foo.spt', "Greetings, program!"))
    assert_match(harness, '/foo', 'foo.spt', extension=None)

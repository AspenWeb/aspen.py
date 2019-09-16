from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
from warnings import catch_warnings

from aspen.exceptions import AttemptedBreakout, PossibleBreakout
from aspen.http.resource import open_resource
from aspen.simplates.pagination import split
import pytest
from pytest import raises


# Test outputs

def test_barely_working(harness):
    output = harness.simple('Greetings, program!', 'index.html')
    assert output.media_type == 'text/html'

def test_charset_static_barely_working(harness):
    output = harness.simple( ('Greetings, program!', 'utf16')
                           , 'index.html'
                           , request_processor_configuration={'charset_static': 'utf16'}
                            )
    assert output.media_type == 'text/html'
    assert output.charset == 'utf16'

def test_charset_static_checks_encoding(harness):
    output = harness.simple( ('Greetings, program!', 'utf16')
                           , 'index.html'
                           , request_processor_configuration={'charset_static': 'utf8'}
                            )
    assert output.media_type == 'text/html'
    assert output.charset is None

def test_charset_static_None(harness):
    output = harness.simple( 'Greetings, program!'
                           , 'index.html'
                           , request_processor_configuration={'charset_static': None}
                            )
    assert output.media_type == 'text/html'
    assert output.charset is None

def test_encode_output_as_barely_working(harness):
    output = harness.simple( '[---]\n[---]\nGreetings, program!'
                           , 'index.html.spt'
                           , request_processor_configuration={'encode_output_as': 'ascii'}
                            )
    assert output.media_type == 'text/html'
    assert output.charset == 'ascii'

def test_resource_pages_work(harness):
    actual = harness.simple("[---]\nfoo = 'bar'\n[--------]\nGreetings, %(foo)s!").text
    assert actual == "Greetings, bar!"

def test_resource_dunder_all_limits_vars(harness):
    actual = raises( KeyError
                   , harness.simple
                   , "[---]\nfoo = 'bar'\n"
                     "__all__ = []\n"
                     "[---------]\n"
                     "Greetings, %(foo)s!"
                    ).value
    # in production, KeyError is turned into a 500 by an outer wrapper
    assert type(actual) == KeyError

def test_path_part_params_are_available(harness):
    output = harness.simple("""
        [---]
        if 'b' in path.parts[0].params:
            a = path.parts[0].params['a']
        [---]
        %(a)s
    """, '/foo/index.html.spt', '/foo;a=1;b;a=3/')
    assert output.text == "3\n"

def test_resources_dont_leak_whitespace(harness):
    """This aims to resolve https://github.com/whit537/aspen/issues/8.
    """
    actual = harness.simple("""
        [--------------]
        foo = [1,2,3,4]
        [--------------]
        %(foo)r""").text
    assert actual == "[1, 2, 3, 4]"

def test_negotiated_resource_doesnt_break(harness):
    expected = "Greetings, bar!\n"
    actual = harness.simple("""
        [-----------]
        foo = 'bar'
        [-----------] text/plain
        Greetings, %(foo)s!
        [-----------] text/html
        <h1>Greetings, %(foo)s!</h1>
        """
        , filepath='index.spt').text
    assert actual == expected

def test_request_processor_is_in_context(harness):
    output = harness.simple("""
        assert request_processor.__class__.__name__ == 'RequestProcessor', request_processor
        [--------]
        [--------]
        It worked.""")
    assert output.text == 'It worked.'

def test_unknown_mimetype_yields_default_mimetype(harness):
    output = harness.simple( 'Greetings, program!'
                             , filepath='foo.flugbaggity'
                              )
    assert output.media_type == 'text/plain'

def test_templating_without_script_works(harness):
    output = harness.simple('[-----]\n[-----] via stdlib_format\n{path.raw}')
    assert output.text == '/'


# Test offset calculation

def check_offsets(raw, offsets):
    actual = [page.offset for page in split(raw)]
    assert actual == offsets

def test_offset_calculation_basic(harness):
    check_offsets('\n\n\n[---]\n\n', [0, 4])

def test_offset_calculation_for_empty_file(harness):
    check_offsets('', [0])

def test_offset_calculation_advanced(harness):
    raw = (
        '\n\n\n[---]\n'
        'cheese\n[---]\n'
        '\n\n\n\n\n\n[---]\n'
        'Monkey\nHead\n') #Be careful: this is implicit concation, not a tuple
    check_offsets(raw, [0, 4, 6, 13])


# Test the `open_resource` function

def test_open_resource_opens_file_inside_www_root(harness):
    harness.fs.www.mk(('index.html', 'foo'))
    fspath = harness.fs.www.resolve('index.html')
    with open_resource(harness.request_processor, fspath) as f:
        actual = f.read()
        assert actual == b'foo'

def test_open_resource_opens_file_inside_project_root(harness):
    harness.fs.project.mk(('error.spt', 'bar'))
    spt_path = harness.fs.project.resolve('error.spt')
    with open_resource(harness.request_processor, spt_path) as f:
        actual = f.read()
        assert actual == b'bar'

# `realpath` doesn't work on Windows in Python < 3.8: https://bugs.python.org/issue9949
@pytest.mark.xfail('os.path.realpath is os.path.abspath')
def test_open_resource_raises_exception_when_file_is_outside(harness):
    # Create a symlink, if possible.
    executable = os.path.realpath(sys.executable)
    fspath = harness.fs.www.resolve('python')
    try:
        os.symlink(executable, fspath)
    except NotImplementedError:
        return
    # Initialize the request processor and check the warnings.
    with catch_warnings(record=True) as messages:
        harness.hydrate_request_processor()
        assert messages
        for m in messages:
            warning = m.message
            assert isinstance(warning, PossibleBreakout)
            assert warning.sym_path == fspath
            assert warning.real_path == executable
    # Attempt to open the resource.
    with raises(AttemptedBreakout):
        open_resource(harness.request_processor, fspath)

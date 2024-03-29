import io

from pytest import raises

from aspen.simplates import json_


def test_json_basically_works(harness):
    expected = '''{
    "Greetings": "program!"
}'''
    actual = harness.simple(
        "[---]\n[---] application/json\n{'Greetings': 'program!'}",
        filepath="foo.json.spt",
    ).text
    assert actual == expected

def test_json_defaults_to_application_json_for_static_json(harness):
    actual = harness.simple(
        '{"Greetings": "program!"}',
        filepath="foo.json",
    ).media_type
    assert actual == 'application/json'

def test_json_content_type_is_configurable_for_static_json(harness):
    harness.request_processor.media_type_json = "floober/blah"
    expected = 'floober/blah'
    actual = harness.simple(
        '{"Greetings": "program!"}',
        filepath="foo.json",
    ).media_type
    assert actual == expected

def test_json_content_type_is_configurable_from_kwargs(harness):
    actual = harness.simple(
        '{"Greetings": "program!"}',
        filepath="foo.json",
        request_processor_configuration={'media_type_json': 'floober/blah'},
    ).media_type
    assert actual == 'floober/blah'

def test_json_content_type_is_configurable_for_dynamic_json(harness):
    harness.request_processor.media_type_json = "floober/blah"
    actual = harness.simple(
        "[---]\n[---] floober/blah\n{'Greetings': 'program!'}",
        filepath="foo.json.spt",
    ).media_type
    assert actual == 'floober/blah'

def test_json_content_type_is_per_file_configurable(harness):
    expected = 'floober/blah'
    SPT = """
        [---]
        [---] floober/blah
        {'Greetings': 'program!'}
    """
    actual = harness.simple(SPT, filepath="foo.json.spt").media_type
    assert actual == expected

def test_json_handles_unicode(harness):
    expected = b'''{\n    "Greetings": "\\u00b5"\n}'''
    actual = harness.simple('''
        [---]
        [---] application/json
        {'Greetings': chr(181)}
    ''', filepath="foo.json.spt").body
    assert actual == expected

def test_json_doesnt_handle_non_ascii_bytestrings(harness):
    with raises(TypeError):
        harness.simple(
            "[---]\n[---] application/json\n{'Greetings': chr(181).encode('utf8')}",
            filepath="foo.json.spt",
        )

def test_json_handles_time(harness):
    expected = '''{\n    "seen": "19:30:00"\n}'''
    actual = harness.simple('''
        [---]
        import datetime
        [---------------] application/json
        {'seen': datetime.time(19, 30)}
    ''', filepath="foo.json.spt").text
    assert actual == expected

def test_json_handles_date(harness):
    expected = '''{\n    "created": "2011-05-09"\n}'''
    actual = harness.simple('''
        [---]
        import datetime
        [---------------] application/json
        {'created': datetime.date(2011, 5, 9)}
    ''', filepath='foo.json.spt').text
    assert actual == expected

def test_json_handles_datetime(harness):
    expected = '''{\n    "timestamp": "2011-05-09T00:00:00"\n}'''
    actual = harness.simple("""
        [---]
        import datetime
        [---------------] application/json
        {'timestamp': datetime.datetime(2011, 5, 9, 0, 0)}
    """, filepath="foo.json.spt").text
    assert actual == expected

def test_json_handles_complex(harness):
    expected = '''{
    "complex": [
        1.0,
        2.0
    ]
}'''
    actual = harness.simple("""
        [---]
        [---] application/json
        {'complex': complex(1,2)}
    """, filepath="foo.json.spt").text
    # The json module puts trailing spaces after commas, but simplejson
    # does not. Normalize the actual input to work around that.
    actual = '\n'.join([line.rstrip() for line in actual.split('\n')])
    assert actual == expected

def test_json_raises_TypeError_on_unknown_types(harness):
    with raises(TypeError):
        harness.simple("""
            [---]
            class Foo: pass
            [---] application/json
            Foo()
        """, filepath='foo.json.spt')

def test_aspen_json_load_loads():
    fp = io.StringIO()
    fp.write('{"cheese": "puffs"}')
    fp.seek(0)
    actual = json_.load(fp)
    assert actual == {'cheese': 'puffs'}

def test_aspen_json_dump_dumps():
    fp = io.BytesIO() if str is bytes else io.StringIO()
    json_.dump({"cheese": "puffs"}, fp)
    fp.seek(0)
    actual = fp.read()
    assert actual == '''{\n    "cheese": "puffs"\n}'''

def test_aspen_json_loads_loads():
    actual = json_.loads('{"cheese": "puffs"}')
    assert actual == {'cheese': 'puffs'}

def test_aspen_json_dumps_dumps():
    actual = json_.dumps({'cheese': 'puffs'})
    assert actual == '''{\n    "cheese": "puffs"\n}'''

# jsonp

JSONP_SIMPLATE = """
[---]
[---] application/json via jsonp_dump
{'Greetings': 'program!'}
"""

JSONP_RESULT = '''/**/ foo({
    "Greetings": "program!"
});'''

def _jsonp_query(harness, querystring):
    return harness.simple(JSONP_SIMPLATE, filepath='index.json.spt', querystring=querystring).text

def test_jsonp_basically_works(harness):
    actual = _jsonp_query(harness, "jsonp=foo")
    assert actual == JSONP_RESULT, "wanted %r got %r " % (JSONP_RESULT, actual)

def test_jsonp_basically_works_with_callback(harness):
    actual = _jsonp_query(harness, "callback=foo")
    assert actual == JSONP_RESULT, "wanted %r got %r " % (JSONP_RESULT, actual)

def test_jsonp_defaults_to_json_with_no_callback(harness):
    expected = '''{\n    "Greetings": "program!"\n}'''
    actual = harness.simple(JSONP_SIMPLATE, filepath='index.spt').text
    assert actual == expected, "wanted %r got %r " % (expected, actual)

def test_jsonp_filters_disallowed_chars(harness):
    actual = _jsonp_query(harness, "callback=f+o+o")
    assert actual == JSONP_RESULT, "wanted %r got %r " % (JSONP_RESULT, actual)

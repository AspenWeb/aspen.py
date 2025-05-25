from pytest import raises

from aspen.http.mapping import Mapping


def test_mapping_subscript_assignment_clobbers():
    m = Mapping()
    m['foo'] = 'bar'
    m['foo'] = 'baz'
    m['foo'] = 'buz'
    expected = ['buz']
    actual = dict.__getitem__(m, 'foo')
    assert actual == expected

def test_mapping_subscript_access_returns_last():
    m = Mapping()
    m['foo'] = 'bar'
    m['foo'] = 'baz'
    m['foo'] = 'buz'
    expected = 'buz'
    actual = m['foo']
    assert actual == expected

def test_mapping_get_returns_last():
    m = Mapping()
    m['foo'] = 'bar'
    m['foo'] = 'baz'
    m['foo'] = 'buz'
    expected = 'buz'
    actual = m.get('foo')
    assert actual == expected

def test_mapping_get_returns_default():
    m = Mapping()
    expected = 'cheese'
    actual = m.get('foo', 'cheese')
    assert actual == expected

def test_mapping_get_default_default_is_None():
    m = Mapping()
    expected = None
    actual = m.get('foo')
    assert actual is expected

def test_mapping_all_returns_list_of_all_values():
    m = Mapping()
    m['foo'] = 'bar'
    m.add('foo', 'baz')
    m.add('foo', 'buz')
    expected = ['bar', 'baz', 'buz']
    actual = m.all('foo')
    assert actual == expected

def test_mapping_all_returns_empty_list_when_key_is_missing():
    m = Mapping()
    expected = []
    actual = m.all('foo')
    assert actual == expected

def test_mapping_deleting_a_key_removes_it_entirely():
    m = Mapping()
    m['foo'] = 1
    m['foo'] = 2
    m['foo'] = 3
    del m['foo']
    assert 'foo' not in m

def test_accessing_missing_key():
    class Foobar(Exception):
        pass

    class FoobarMapping(Mapping):
        def __missing__(self, name):
            raise Foobar

    m = FoobarMapping()
    raises(Foobar, lambda k: m[k], 'foo')
    assert m.get('foo') is None

def test_mapping_pop_raises_KeyError_by_default():
    m = Mapping()
    with raises(KeyError):
        m.pop('foo')

def test_mapping_pop_removes_the_list_and_returns_its_last_item():
    m = Mapping()
    m['foo'] = 1
    m.add('foo', 2)
    m.add('foo', 3)
    popped = m.pop('foo')
    assert popped == 3
    assert 'foo' not in m

def test_mapping_popall_raises_KeyError_by_default():
    m = Mapping()
    with raises(KeyError):
        m.popall('foo')

def test_mapping_popall_removes_the_list_and_returns_it():
    m = Mapping()
    m['foo'] = 1
    m.add('foo', 1)
    m.add('foo', 3)
    expected = [1, 1, 3]
    actual = m.popall('foo')
    assert actual == expected
    assert 'foo' not in m

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

def test_accessing_missing_key_calls_keyerror():
    m = Mapping()

    class Foobar(Exception):
        pass

    def raise_foobar(self):
        raise Foobar

    m.keyerror = raise_foobar
    raises(Foobar, lambda k: m[k], 'foo')
    raises(Foobar, m.pop, 'foo')

def test_mapping_pop_returns_the_last_item():
    m = Mapping()
    m['foo'] = 1
    m.add('foo', 1)
    m.add('foo', 3)
    expected = 3
    actual = m.pop('foo')
    assert actual == expected

def test_mapping_pop_leaves_the_rest():
    m = Mapping()
    m['foo'] = 1
    m.add('foo', 1)
    m.add('foo', 3)
    m.pop('foo')
    expected = [1, 1]
    actual = m.all('foo')
    assert actual == expected

def test_mapping_pop_removes_the_item_if_that_was_the_last_value():
    m = Mapping()
    m['foo'] = 1
    m.pop('foo')
    expected = []
    actual = list(m.keys())
    assert actual == expected

def test_mapping_pop_raises_KeyError_by_default():
    m = Mapping()
    with raises(KeyError):
        m.pop('foo')

def test_mapping_popall_returns_a_list():
    m = Mapping()
    m['foo'] = 1
    m.add('foo', 1)
    m.add('foo', 3)
    expected = [1, 1, 3]
    actual = m.popall('foo')
    assert actual == expected

def test_mapping_popall_removes_the_item():
    m = Mapping()
    m['foo'] = 1
    m['foo'] = 1
    m['foo'] = 3
    m.popall('foo')
    assert 'foo' not in m

from operator import itemgetter

from ..utils import Constant


NO_DEFAULT = Constant('NO_DEFAULT')


class Mapping(dict):
    """Base class for HTTP mappings.

    This dictionary subclass maintains a list of values for each key. However,
    since most of the time only one value is expected and wanted for each key,
    the standard `dict` methods reimplemented by this class act as if there was
    only one value per key.

    Example:

    >>> m = Mapping([('a', '1')])
    >>> m
    Mapping({'a': ['1']})
    >>> m['a']
    '1'
    >>> m.append('a', '2')
    >>> m['a']
    '2'
    >>> m.all('a')
    ['1', '2']
    >>> m.pop('a')
    '2'
    >>> m['a']
    Traceback (most recent call last):
      ...
    KeyError: 'a'

    .. warning:: This isn't thread-safe.

    """

    def __init__(self, *a, **kw):
        self.update(*a, **kw)

    def __eq__(self, other):
        keys = self.keys()
        if keys != other.keys():
            return False
        for k in keys:
            theirs = other[k]
            ours = self.all(k) if isinstance(theirs, (list, tuple)) else self[k]
            if ours != theirs:
                return False
        return True

    def __ne__(self, other):
        return not (self == other)

    def __getitem__(self, name):
        return super().__getitem__(name)[-1]

    def __missing__(self, name):
        raise KeyError(name) from None

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __setitem__(self, name, value):
        super().__setitem__(name, [value])

    def copy(self):
        return self.__class__(self)

    copy.__doc__ = dict.copy.__doc__

    def pop(self, name, default=NO_DEFAULT):
        """Remove the `name` key from the mapping and return its associated value.

        If `name` is not present and `default` is given, that is returned instead.
        Otherwise, `self.__missing__(name)` is called, to make it easier for
        subclasses to raise custom exceptions.
        """
        values = super().pop(name, default)
        if values and values is not default:
            return values[-1]
        elif default is not NO_DEFAULT:
            return default
        else:
            return self.__missing__(name)

    popall = dict.pop

    def all(self, name):
        """Return the list of values for the `name` key, possibly an empty one.
        """
        return super().get(name, [])

    def get(self, name, default=None):
        """Return the last value of the list for the `name` key.
        """
        return super().get(name, (default,))[-1]

    last = get

    def add(self, name, value):
        """Append `value` to the list for the `name` key.
        """
        try:
            super().__getitem__(name).append(value)
        except KeyError:
            super().__setitem__(name, [value])

    append = add

    def extend(self, name, values):
        """Append `values` to the list for the `name` key.
        """
        try:
            super().__getitem__(name).extend(values)
        except KeyError:
            super().__setitem__(name, values)

    def setdefault(self, name, value):
        """Set the value for the `name` key if there is none.
        """
        if name not in self:
            self[name] = value

    def items(self):
        """Returns an iterator of `(name, last_value)` tuples.
        """
        return ((name, values[-1]) for name, values in super().items())

    def popitem(self):
        name, values = super().popitem()
        return (name, values[-1])

    popitem.__doc__ = dict.popitem.__doc__

    def update(self, *a, **kw):
        """Updates `self` with items from the iterables `*a` and the dict `**kw`.
        """
        for it in a:
            if not it:
                continue
            items = it.items() if hasattr(it, 'items') else it
            for k, v in items:
                if isinstance(v, str):
                    self.add(k, v)
                else:
                    self.extend(k, v)
        for k, v in kw.items():
            self[k] = v

    def values(self):
        """Returns an iterator yielding the last value for each key.
        """
        return map(itemgetter(-1), super().values())

    @classmethod
    def fromkeys(cls, iterable, value):
        """Create a new mapping with keys from `iterable` and values set to `value`.
        """
        return cls((name, value) for name in iterable)

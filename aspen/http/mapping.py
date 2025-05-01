NO_DEFAULT = object()


class Mapping(dict):
    """Base class for HTTP mappings.

    Mappings in HTTP differ from Python dictionaries in that they may have one
    or more values. This dictionary subclass maintains a list of values for
    each key. However, access semantics are asymmetric: subscript assignment
    clobbers to list, while subscript access returns the last item. Think
    about it.

    .. warning:: This isn't thread-safe.

    """

    def __init__(self, *a, **kw):
        super().__init__(*a)
        for k, v in self.items():
            dict.__setitem__(self, k, v.copy())
        for k, v in kw.items():
            self[k] = v

    def __getitem__(self, name):
        """Given a name, return the last value or call self.keyerror.
        """
        try:
            return dict.__getitem__(self, name)[-1]
        except KeyError:
            self.keyerror(name)

    def __setitem__(self, name, value):
        """Given a name and value, clobber any existing values.
        """
        dict.__setitem__(self, name, [value])

    def copy(self):
        return self.__class__(self)

    copy.__doc__ = dict.copy.__doc__

    def keyerror(self, key):
        """Called when a key is missing. Default implementation simply reraises.
        """
        raise

    def poplast(self, name, default=NO_DEFAULT):
        """Remove and return the last value of the list for the `name` key.

        If there is only one value in the list, then the key is removed from the
        mapping. If name is not present and default is given, that is returned
        instead. Otherwise, self.keyerror is called.

        """
        try:
            values = dict.__getitem__(self, name)
        except KeyError:
            if default is not NO_DEFAULT:
                return default
            self.keyerror(name)
        value = values.pop()
        if not values:
            del self[name]
        return value

    def all(self, name):
        """Given a name, return a list of values, possibly empty.
        """
        return dict.get(self, name, [])

    def get(self, name, default=None):
        """Override to only return the last value.
        """
        return dict.get(self, name, [default])[-1]

    def add(self, name, value):
        """Given a name and value, clobber any existing values with the new one.
        """
        if name in self:
            self.all(name).append(value)
        else:
            dict.__setitem__(self, name, [value])

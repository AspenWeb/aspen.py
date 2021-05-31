from urllib.parse import parse_qs, unquote, unquote_plus

from .mapping import Mapping


class PathPart(str):
    """Represents a segment of a URL path.

    Attributes:
        params (Mapping): extra data attached to this segment
    """

    __slots__ = ['params']

    def __new__(cls, value, params=None):
        obj = super(PathPart, cls).__new__(cls, value)
        obj.params = params
        return obj

    def __repr__(self):
        return '%s(%r, params=%r)' % (self.__class__.__name__, str(self), self.params)


def extract_rfc2396_params(path):
    """This function implements parsing URL path parameters, per `section 3.3 of RFC2396`_.

    * path should be raw so we don't split or operate on a decoded character
    * output is decoded

    Example:

    >>> path = '/frisbee;color=red;size=small/logo;sponsor=w3c;color=black/image.jpg'
    >>> extract_rfc2396_params(path) == [
    ...     PathPart('frisbee', params={'color': ['red'], 'size': ['small']}),
    ...     PathPart('logo', params={'sponsor': ['w3c'], 'color': ['black']}),
    ...     PathPart('image.jpg', params={})
    ... ]
    True

    .. _Section 3.3 of RFC2396: https://tools.ietf.org/html/rfc3986#section-3.3
    """
    pathsegs = path.lstrip('/').split('/')
    segments_with_params = []
    for component in pathsegs:
        parts = component.split(';')
        params = Mapping()
        segment = unquote(parts[0])
        for p in parts[1:]:
            if '=' in p:
                k, v = p.split('=', 1)
            else:
                k, v = p, ''
            params.add(unquote(k), unquote(v))
        segments_with_params.append(PathPart(segment, params))
    return segments_with_params


def split_path_no_params(path):
    """This splits a path into parts on "/" only (no split on ";" or ",").
    """
    return [PathPart(unquote(s)) for s in path.lstrip('/').split('/')]


class Path(Mapping):
    """Represent the path of a resource.

    Attributes:
        raw: the unparsed form of the path - :class:`str`
        decoded: the decoded form of the path - :class:`str`
        parts: the segments of the path - :class:`list` of :class:`PathPart` objects
    """

    def __init__(self, raw, split_path=extract_rfc2396_params):
        self.raw = raw
        self.decoded = unquote(raw)
        self.parts = split_path(raw)


class Querystring(Mapping):
    """Represent an HTTP querystring.

    Attributes:
        raw: the unparsed form of the querystring - :class:`str`
        decoded: the decoded form of the querystring - :class:`str`
    """

    def __init__(self, raw, errors='replace'):
        """Takes a string of type application/x-www-form-urlencoded.
        """
        self.decoded = unquote_plus(raw)
        self.raw = raw
        Mapping.__init__(self, parse_qs(
            raw, errors=errors, keep_blank_values=True, strict_parsing=False
        ))

import datetime

# Find a json module.
# ===================
# The standard library includes simplejson as json since 2.6, but without the
# C speedups. So we prefer simplejson if it is available.

try:
    import simplejson as _json
except ImportError:
    import json as _json


# Allow arbitrary encoders to be registered.
# ==========================================
# One of the difficulties with JSON in Python is that pretty quickly one hits a
# class or type that needs extra work to decode to JSON. Since Aspen takes on
# ownership of JSON encoding, we need to give Aspen users a way to register (and
# unregister, I guess) new encoders. You can do this by calling dumps with the
# cls keyword, but we call dumps for you for JSON resources, so we want a way to
# influence decoding that doesn't depend on dumps. And this is that way:

encoders = {}


def register_encoder(cls, encode):
    """Register the encode function for cls.

    An encoder should take an instance of cls and return something basically
    serializable (strings, lists, dictionaries).

    """
    encoders[cls] = encode


def unregister_encoder(cls):
    """Given a class, remove any encoder that has been registered for it.
    """
    if cls in encoders:
        del encoders[cls]


# http://docs.python.org/library/json.html
register_encoder(complex, lambda obj: [obj.real, obj.imag])

# http://stackoverflow.com/questions/455580/
register_encoder(datetime.datetime, lambda obj: obj.isoformat())
register_encoder(datetime.date, lambda obj: obj.isoformat())
register_encoder(datetime.time, lambda obj: obj.isoformat())


class FriendlyEncoder(_json.JSONEncoder):
    """Add support for additional types to the default JSON encoder.
    """
    def default(self, obj):
        cls = obj.__class__
        encode = encoders.get(cls, super(FriendlyEncoder, self).default)
        return encode(obj)


# Main public API.
# ================

def load(*a, **kw):
    return _json.load(*a, **kw)


def dump(*a, **kw):
    if 'cls' not in kw:
        kw['cls'] = FriendlyEncoder
    # Beautify json by default.
    if 'sort_keys' not in kw:
        kw['sort_keys'] = True
    if 'indent' not in kw:
        kw['indent'] = 4
    return _json.dump(*a, **kw)


def loads(*a, **kw):
    return _json.loads(*a, **kw)


def dumps(*a, **kw):
    if 'cls' not in kw:
        kw['cls'] = FriendlyEncoder
    # Beautify json by default.
    if 'sort_keys' not in kw:
        kw['sort_keys'] = True
    if 'indent' not in kw:
        kw['indent'] = 4
    return _json.dumps(*a, **kw)

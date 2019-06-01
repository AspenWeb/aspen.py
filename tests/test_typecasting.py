from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pytest

import aspen


def test_virtual_path_with_typecast(harness):
    harness.fs.www.mk(('%year:int/foo.html', "Greetings, program!"),)
    path = harness.hit('/1999/foo.html', want='path')
    assert path == {'year': [1999]}

def test_virtual_path_raises_on_bad_typecast(harness):
    harness.fs.www.mk(('%year:int/foo.html', "Greetings, program!"),)
    with pytest.raises(aspen.exceptions.TypecastError):
        harness.hit('/I am not a year./foo.html')

class User:

    def __init__(self, name):
        self.username = name

    @classmethod
    def toUser(cls, name, context):
        return cls(name)

def test_virtual_path_file_key_val_cast_custom(harness):
    harness.fs.www.mk(('user/%user:user.html.spt', "Greetings, user!"))
    harness.hydrate_request_processor(typecasters={'user': User.toUser})
    actual = harness.hit('/user/chad.html', want='path')
    assert actual['user'].username == 'chad'

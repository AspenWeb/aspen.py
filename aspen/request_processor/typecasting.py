"""
This module handles the parsing of path variables.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ..exceptions import TypecastError


#: Aspen's default typecasters.
defaults = { 'int': lambda pathpart, context: int(pathpart)
           , 'float': lambda pathpart, context: float(pathpart)
            }


def apply_typecasters(typecasters, path_vars, context):
    """Perform typecasting (in-place!).

    Args:
        typecasters: a :class:`dict` of type names to typecast functions
        path_vars: a :class:`~aspen.http.mapping.Mapping` of path variables
        context: a :class:`dict` passed to typecast functions as second argument

    Raises:
        TypecastError: if a typecast function raises an exception
    """
    for part in list(path_vars.keys()):
        if ':' in part:
            var, ext = part.rsplit(':', 1)
            if ext in typecasters:
                try:
                    # path_vars is a Mapping not a dict, so:
                    for v in path_vars.all(part):
                        path_vars.add(var, typecasters[ext](v, context))
                    path_vars.popall(part)
                except:
                    raise TypecastError(ext)


#########
  Aspen
#########

Aspen is a filesystem dispatch library for Python web frameworks. Instead of
using regular expressions, decorators, or object traversal, Aspen dispatches
HTTP requests based on the natural symmetry of URL paths and filesystem paths.
In the `immortal words`_ of Jeff Lindsay, "so like. a web server." Yes! ;-)

.. _immortal words: https://twitter.com/progrium/status/773694289033383937

This is the documentation for the development version of the core Aspen
library, describing its filesystem dispatch behavior regardless of the web
framework you're using it with. For instructions on configuring Aspen with a
specific web framework, see the docs for `django-aspen`_, `Flask-Aspen`_, or
`Pando`_. See the `project homepage`_ for an overview.

.. _django-aspen: http://django.aspen.io/
.. _Flask-aspen: http://flask.aspen.io/
.. _Pando: http://pando.aspen.io/
.. _project homepage: http://aspen.io/

This version of Aspen has been tested with Python 3.10, 3.11, 3.12, 3.13, and
3.14, on both Ubuntu and Windows.

Aspen's source code is on `GitHub`_, and is `MIT-licensed`_.

.. _GitHub: https://github.com/AspenWeb/aspen.py
.. _MIT-licensed: https://github.com/AspenWeb/aspen.py/blob/master/COPYRIGHT


**************
 Installation
**************

Aspen is available on `PyPI`_::

    $ pip install aspen

.. _PyPI: https://pypi.python.org/pypi/aspen


**********
 Contents
**********

.. toctree::
    :maxdepth: 2

    dispatch
    simplates
    plugins
    wrappers
    reference/index


**********
 See Also
**********

The `Keystone`_ web framework was inspired by Aspen.

.. _Keystone: http://keystone.readthedocs.org/

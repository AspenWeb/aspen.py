"""
:mod:`simplates`
================

The simplates module implements Aspen's file format, simplates (\*.spt).
Simplates combine request processing logic (think: Rails controller, or Django
view) with template code in one file. Here's an example::

    # Python syntax. Runs once on startup.
    import random

    [----]
    # Python syntax. Runs once per request..
    program = request.qs['program']
    excitement = '!' * random.randint(1, 10)

    # One of the following is used on each request, based on content type
    # negotiation. The syntax depends on the renderer.

    [----] text/html via jinja2
    <h1>Greetings, {{ program }}{{ excitement }}</h1>

    [----] text/plain via stdlib_format
    Greetings, {program}{excitement}

    [----] application/json via json_dump
    { "program": program
    , "excitement": excitement
     }


.. automodule:: aspen.simplates.renderers
.. automodule:: aspen.simplates.pagination
.. automodule:: aspen.simplates.json_

"""

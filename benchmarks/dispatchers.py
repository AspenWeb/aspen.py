import gc
import json
from timeit import timeit

from filesystem_tree import FilesystemTree

import aspen.request_processor


def is_dynamic(fspath):
    return fspath.endswith('.spt')


FILE_CONTENT = "The content doesn't matter, we're only testing dispatching."

FILES = [
    ('index.html.spt', FILE_CONTENT),
    ('style.css', FILE_CONTENT),
    ('%username/index.spt', FILE_CONTENT),
    ('foo/%catchall.spt', FILE_CONTENT),
]

URLS = [
    '/',
    '/style.css',
    '/username',
    '/username/',
    '/nonexistent/file.php',
    '/foo/',
    '/foo/bar',
    '/foo/bar.txt',
    '/foo/bar/',
    '/foo/bar/baz',
]


times = {}
for dispatcher_class in aspen.request_processor.dispatcher.DISPATCHER_CLASSES:
    print("Timing", dispatcher_class.__name__)
    total_time = 0
    with FilesystemTree() as ft:
        ft.mk(*FILES)
        dispatcher = dispatcher_class(
            ft.root,
            is_dynamic,
            aspen.request_processor.default_indices,
            aspen.request_processor.typecasting.defaults
        )
        dispatcher.build_dispatch_tree()
        for url in URLS:
            dispatch = lambda: dispatcher.dispatch(url, url.split('/'))
            time = timeit(dispatch, number=1000)
            print(url, time)
            total_time += time
    times[dispatcher_class.__name__] = total_time
    print()

print("Totals:", json.dumps(times, indent=4, sort_keys=True), end='\n\n')

ordered = sorted(times.items(), key=lambda t: t[1])
if len(ordered) > 2:
    print(
        "The winner is %s: it's %.2f times faster than the second best %s, and %.2f times faster than the slowest %s." %
        ( ordered[0][0], ordered[1][1] / ordered[0][1], ordered[1][0]
        , ordered[-1][1] / ordered[0][1], ordered[-1][0])
    )
else:
    print("The winner is %s: it's %.2f times faster than %s." %
          (ordered[0][0], ordered[1][1] / ordered[0][1], ordered[1][0]))

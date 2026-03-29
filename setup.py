from os.path import dirname, join

from setuptools import find_packages, setup

version = open('version.txt').read()


classifiers = [ 'Development Status :: 4 - Beta'
              , 'Environment :: Console'
              , 'Intended Audience :: Developers'
              , 'License :: OSI Approved :: MIT License'
              , 'Natural Language :: English'
              , 'Operating System :: OS Independent'
              , 'Programming Language :: Python :: 3.9'
              , 'Programming Language :: Python :: 3.10'
              , 'Programming Language :: Python :: 3.11'
              , 'Programming Language :: Python :: 3.12'
              , 'Programming Language :: Python :: 3.13'
              , 'Programming Language :: Python :: 3.14'
              , 'Programming Language :: Python :: Implementation :: CPython'
              , 'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
               ]

setup( author = 'Chad Whitacre et al.'
     , author_email = 'team@aspen.io'
     , classifiers = classifiers
     , description = 'A filesystem router for Python web frameworks'
     , long_description=open(join(dirname(__file__), 'README.rst')).read()
     , name = 'aspen'
     , packages = find_packages()
     , url = 'https://github.com/AspenWeb/aspen.py'
     , version = version
     , python_requires = '>=3.9,<3.15'
     , zip_safe = False
     , package_data = {'aspen': ['request_processor/mime.types']}
     , install_requires = open('requirements.txt').read()
     , tests_require = open('requirements_tests.txt').read()
      )

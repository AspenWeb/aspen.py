from os.path import dirname, join

from setuptools import find_packages, setup

root = dirname(__file__)

setup(
    author = 'Chad Whitacre et al.',
    author_email = 'team@aspen.io',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description = 'A filesystem router for Python web frameworks',
    long_description=open(join(dirname(__file__), 'README.rst')).read(),
    long_description_content_type='text/x-rst',
    name = 'aspen',
    url = 'https://github.com/AspenWeb/aspen.py',
    version = open(join(root, 'version.txt')).read().strip(),
    zip_safe = False,
    packages = find_packages(),
    package_data = {'aspen': ['request_processor/mime.types']},
    install_requires = open(join(root, 'requirements.txt')).read(),
    tests_require = open(join(root, 'requirements_tests.txt')).read(),
)

#!/usr/bin/env python

from distutils.core import setup
from os.path import abspath, dirname, join
import re

NAME = 'dbbot'
CLASSIFIERS = """
Development Status :: 4 - Beta 
License :: OSI Approved :: Apache Software License
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development :: Testing
""".strip().splitlines()
CURDIR = dirname(abspath(__file__))
with open(join(CURDIR, NAME, '__init__.py')) as f:
    VERSION = re.search("\n__version__ = '(.*)'\n", f.read()).group(1)
with open(join(CURDIR, 'README.rst')) as f:
    README = f.read()

setup(
    name             = NAME,
    version          = VERSION,
    author           = 'Robot Framework Developers',
    author_email     = 'robotframework@gmail.com',
    url              = 'https://github.com/robotframework/DbBot',
    download_url     = 'https://pypi.python.org/pypi/dbbot',
    license          = 'Apache License 2.0',
    description      = 'A tool for serializing Robot Framework test run '
                       'results into an sqlite3 database.',
    long_description = README,
    keywords         = 'robotframework testing testautomation atdd',
    platforms        = 'any',
    classifiers      = CLASSIFIERS,
    packages         = ['dbbot', 'dbbot.reader'],
    install_requires = ['robotframework']
)

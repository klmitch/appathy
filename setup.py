#!/usr/bin/env python

import re

from setuptools import setup


def readreq(filename, raw=False):
    namepat = re.compile(r'([a-zA-Z0-9_]+)(.*)')
    result = []
    with open(filename) as f:
        for req in f:
            req = req.partition('#')[0].strip()
            if not req:
                continue
            if raw:
                result.append(req)
            else:
                name, ver_req = namepat.match(req).groups()
                if ver_req:
                    result.append('%s(%s)' % (name, ver_req))
                else:
                    result.append(name)
    return result


def readfile(filename):
    with open(filename) as f:
        return f.read()


setup(
    name='Appathy',
    version='0.1.0',
    author='Kevin L. Mitchell',
    author_email='klmitch@mit.edu',
    url='http://github.com/klmitch/appathy',
    description='REST Application Framework',
    long_description=readfile('README.rst'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    packages=['appathy'],
    requires=readreq('install-requires'),
    tests_require=readreq('test-requires', True),
    entry_points={
        'appathy.loader': [
            'call = appathy.utils:import_call',
            'egg = appathy.utils:import_egg',
            ],
        'paste.app_factory': [
            'appathy = appathy.application:Application',
            ],
        },
    )

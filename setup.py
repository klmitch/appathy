#!/usr/bin/env python

from setuptools import setup


def readreq(filename):
    with open(filename) as f:
        reqs = [r.partition('#')[0].strip() for r in f]
        return [r for r in reqs if r]


def readfile(filename):
    with open(filename) as f:
        return f.read()


setup(
    name='Appathy',
    version='0.1',
    author='Kevin L. Mitchell',
    author_email='klmitch@mit.edu',
    url='http://github.com/klmitch/appathy',
    description='REST Application Framework',
    long_description=readfile('README.rst'),
    classifiers=[
        'Development Status :: 3 - Alpha',
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
    tests_require=readreq('test-requires'),
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

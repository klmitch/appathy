#!/usr/bin/env python

from setuptools import setup

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
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    packages=['appathy'],
    requires=[
        "metatools",
        "routes (>=1.12)",
        "webob (>=1.1)",
        "paste.deploy (>=1.5)",
        "pkg_resources",
        ],
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

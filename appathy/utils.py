# Copyright (C) 2012 by Kevin L. Mitchell <klmitch@mit.edu>
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see
# <http://www.gnu.org/licenses/>.

import re
import sys

import pkg_resources


# Regular expression to identify repeated slashes
_path_re = re.compile(r'/{2,}')


def norm_path(path, allow_trailing=True):
    """
    Normalize a route path.  Ensures that the path begins with a '/'.
    If `allow_trailing` is False, strips off any trailing '/'.  Any
    repeated '/' characters in the path will be collapsed into a
    single one.
    """

    # Collapse slashes
    path = _path_re.sub('/', path)

    # Force a leading slash
    if path[0] != '/':
        path = '/' + path

    # Trim a trailing slash
    if not allow_trailing and path[-1] == '/':
        path = path[:-1]

    return path


def import_call(string):
    """
    Import a controller class directly from the Python path.
    """

    return pkg_resources.EntryPoint.parse("x=" + string).load(False)


def import_egg(string):
    """
    Import a controller class from an egg.  Uses the entry point group
    "appathy.controller".
    """

    # Split the string into a distribution and a name
    dist, _sep, name = string.partition('#')

    return pkg_resources.load_entry_point(dist, 'appathy.controller', name)


def import_controller(string):
    """
    Imports the requested controller.  Controllers are specified in a
    URI-like manner; the scheme is looked up using the entry point
    group "appathy.loader".  Appathy supports the "call:" and "egg:"
    schemes by default.
    """

    # Split out the scheme and the controller descriptor
    scheme, _sep, controller = string.partition(':')

    # Look up a loader for that scheme
    for ep in pkg_resources.iter_entry_points('appathy.loader', scheme):
        try:
            loader = ep.load()
            break
        except (ImportError, pkg_resources.UnknownExtra):
            continue
    else:
        raise ImportError("Unable to find loader for scheme %r" % scheme)

    # Load the controller
    return loader(controller)

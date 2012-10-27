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


class AppathyResponse(Exception):
    """
    Special exception used by appathy.actions.ActionDescriptor.wrap()
    for passing webob.Response upstream to the application, for
    immediate return to the caller.
    """

    def __init__(self, response):
        """
        Initialize the exception by storing the response.
        """

        super(AppathyResponse, self).__init__('Response bail-out')
        self.response = response


class AppathyException(Exception):
    """Base class for all Appathy exceptions."""

    # A list of argument names for positional arguments to the
    # constructor.  If not provided, the first positional argument
    # (which will be optional) will be the message.
    base_args = None

    def __init__(self, *args, **kwargs):
        """
        Initialize an AppathyException.
        """

        if self.base_args:
            # If base_args is set, interpolate positional arguments
            # into keyword arguments and get the message from the
            # docstring
            message = self.__doc__
            targs = dict(zip(self.base_args, args))
            targs.update(kwargs)
            kwargs = targs
        elif args:
            # Get the message from the first positional argument
            message = args[0]
        else:
            # Get the message from the docstring
            message = self.__doc__

        super(AppathyException, self).__init__(message % kwargs)


class IncompleteController(AppathyException):
    """Cannot instantiate an incomplete controller"""


class NoSuchResource(AppathyException):
    """No such resource %(name)r"""

    base_args = ['name']


class UnboundResponse(AppathyException):
    """Response object must be bound before it can be serialized"""

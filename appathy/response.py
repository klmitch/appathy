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

import collections

import webob


class ResponseObject(collections.MutableMapping):
    """
    Represent a response object.
    """

    def __init__(self, req, result=None, code=None, headers=None, **kwargs):
        """
        Initialize a ResponseObject.

        :param req: The request associated with the response.
        :param result: The optional result.
        :param code: The HTTP response code.  If not specified, the
                     default set by the @action() decorator will be
                     used.  If no default was specified by @action(),
                     then the default will be 200.
        :param headers: A dictionary of headers for the response.
                        Note that keys will be handled in a
                        case-insensitive manner.
        """

        # Store the request, result, code, and headers
        self.req = req
        self.result = result
        self._code = code
        self._headers = {}
        if headers:
            self.update(headers)

        # Set up various defaults
        self._defcode = None
        self.content_type = None
        self.type_name = None
        self.serializer = None

        # If a method was specified, bind it; this prepares for
        # serialization and updates the default code
        if '_descriptor' in kwargs:
            self._bind(**kwargs)

    def __getitem__(self, key):
        """
        Retrieve the named header.
        """

        return self._headers[key.lower()]

    def __setitem__(self, key, value):
        """
        Change the value of the named header.
        """

        self._headers[key.lower()] = value

    def __delitem__(self, key):
        """
        Delete the named header.
        """

        del self._headers[key.lower()]

    def __contains__(self, key):
        """
        Determine if a named header exists.
        """

        return key.lower() in self._headers

    def __iter__(self):
        """
        Iterate over the defined headers, returning the header names.
        """

        return iter(self._headers)

    def iteritems(self):
        """
        Iterate over the defined headers, returning the header names
        and values.
        """

        return self._headers.iteritems()

    def keys(self):
        """
        Return a list of the defined header names.
        """

        return self._headers.keys()

    def _bind(self, _descriptor):
        """
        Bind a ResponseObject to a given action descriptor.  This
        updates the default HTTP response code and selects the
        appropriate content type and serializer for the response.
        """

        # If the method has a default code, use it
        self._defcode = getattr(_descriptor.method, '_wsgi_code', 200)

        # Set up content type and serializer
        self.content_type, self.serializer = _descriptor.serializer(self.req)

    def serialize(self):
        """
        Serialize the ResponseObject.  Returns a webob `Response`
        object.
        """

        # Build the response
        resp = webob.Response(request=self.req, status=self.code,
                              headerlist=self._headers.items())

        # Do we have a body?
        if self.result:
            resp.content_type = self.content_type
            resp.body = self.serializer(self.result)

        # Return the response
        return resp

    @property
    def code(self):
        """
        The HTTP response code associated with this ResponseObject.
        If instantiated directly without overriding the code, returns
        200 even if the default for the method is some other value.
        Can be set or deleted; in the latter case, the default will be
        restored.
        """

        if self._code is not None:
            return self._code
        elif self._defcode is not None:
            return self._defcode
        return 200

    @code.setter
    def code(self, value):
        """
        Set the response code value.
        """

        self._code = value

    @code.deleter
    def code(self):
        """
        Restore the default response code value.
        """

        self._code = None

    @property
    def headers(self):
        """
        Return a copy of the headers as a dictionary.
        """

        return self._headers.copy()

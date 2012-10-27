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

import inspect

import webob
import webob.exc

from appathy import response
from appathy import types


class ActionMethod(object):
    """
    Tracking for single action or extension methods.  Provides
    straight-forward access to serializers and deserializers, along
    with a safe replacement for calling which omits parameters not
    needed by the target method.
    """

    def __init__(self, method):
        """
        Initializes an ActionMethod object for the given method.  The
        lists of serializers and deserializers are converted into
        Translators for ease of use later.  Also caches some useful
        information, such as the isgenerator attribute.
        """

        self.method = method
        self.serializers = types.Translators(method, '_wsgi_serializers')
        self.deserializers = types.Translators(method, '_wsgi_deserializers')
        self.isgenerator = inspect.isgeneratorfunction(method)
        self.argspec = inspect.getargspec(method)
        self.argidx = int(inspect.ismethod(method))

    def __getattr__(self, attr):
        """
        Allow access to the attributes of the method by accessing the
        attributes of the ActionMethod object.
        """

        return getattr(self.method, attr)

    def __call__(self, *args, **kwargs):
        """
        Safely call the method.  Unneeded keyword arguments are
        omitted from the call.
        """

        # Trim kwargs down if we need to...
        if not self.argspec.keywords:
            argnames = self.argspec.args[self.argidx + len(args):]
            kwargs = dict((arg, kwargs[arg]) for arg in argnames
                          if arg in kwargs)

        # Call the method
        return self.method(*args, **kwargs)


class ActionDescriptor(object):
    """
    Describes an action on a controller.  Binds together the method
    which performs the action, along with all the registered
    extensions and the desired ResponseObject type.
    """

    def __init__(self, method, extensions, resp_type):
        """
        Initialize an ActionDescriptor from the method, extensions,
        and ResponseObject subclass specified by `resp_type`.
        """

        self.method = ActionMethod(method)
        self.extensions = [ActionMethod(ext) for ext in extensions]
        self.resp_type = resp_type

    def __call__(self, req, params):
        """
        Call the actual action method.  Wraps the return value in a
        ResponseObject, if necessary.
        """

        return self.wrap(req, self.method(req, **params))

    def deserialize_request(self, req):
        """
        Uses the deserializers declared on the action method and its
        extensions to deserialize the request.  Returns the result of
        the deserialization.  Raises `webob.HTTPUnsupportedMediaType`
        if the media type of the request is unsupported.
        """

        # See if we have a body
        if req.content_length == 0:
            return None

        # Get the primary deserializer
        try:
            deserializer = self.method.deserializers(req.content_type)
        except KeyError:
            raise webob.exc.HTTPUnsupportedMediaType()

        # If it has an attacher, attach all the deserializers for the
        # extensions
        if hasattr(deserializer, 'attach'):
            for ext in self.extensions:
                try:
                    deserializer.attach(ext.deserializers(req.content_type))
                except KeyError:
                    pass

        # A deserializer is simply a callable, so call it
        return deserializer(req.body)

    def serializer(self, req):
        """
        Selects and returns the serializer to use, based on the
        serializers declared on the action method and its extensions.
        The returned content type is selected based on the types
        available and the best match generated from the HTTP `Accept`
        header.  Raises `HTTPNotAcceptable` if the request cannot be
        serialized to an acceptable media type.  Returns a tuple of
        the content type and the serializer.
        """

        # Select the best match serializer
        content_types = self.method.serializers.get_types()
        content_type = req.accept.best_match(content_types)
        if content_type is None:
            raise webob.exc.HTTPNotAcceptable()

        # Select the serializer to use
        try:
            serializer = self.method.serializers(content_type)
        except KeyError:
            raise webob.exc.HTTPNotAcceptable()

        # If it has an attacher, attach all the serializers for the
        # extensions
        if hasattr(serializer, 'attach'):
            for ext in reversed(self.extensions):
                try:
                    serializer.attach(ext.serializers(content_type))
                except KeyError:
                    pass

        # Return content type and serializer
        return content_type, serializer

    def pre_process(self, req, params):
        """
        Pre-process the extensions for the action.  If any
        pre-processing extension yields a value which tests as True,
        extension pre-processing aborts and that value is returned;
        otherwise, None is returned.  Return value is always a tuple,
        with the second element of the tuple being a list to feed to
        post_process().
        """

        post_list = []

        # Walk through the list of extensions
        for ext in self.extensions:
            if ext.isgenerator:
                gen = ext(req, **params)
                try:
                    # Perform the preprocessing stage
                    result = gen.next()
                    if result:
                        return self.wrap(req, result), post_list
                except StopIteration:
                    # Only want to pre-process, I guess
                    continue

                # Save generator for post-processing
                post_list.insert(0, gen)
            else:
                # Save extension for post-processing
                post_list.insert(0, ext)

        # Return the post-processing list
        return None, post_list

    def post_process(self, post_list, req, resp, params):
        """
        Post-process the extensions for the action.  If any
        post-processing extension (specified by `post_list`, which
        should be generated by the pre_process() method) yields a
        value which tests as True, the response being considered by
        post-processing extensions is updated to be that value.
        Returns the final response.
        """

        # Walk through the post-processing extensions
        for ext in post_list:
            if inspect.isgenerator(ext):
                try:
                    result = ext.send(resp)
                except StopIteration:
                    # Expected, but not required
                    result = None

                # If it returned a response, use that for subsequent
                # processing
                if result:
                    resp = self.wrap(req, result)
            else:
                result = ext(req, resp, **params)

                # If it returned a response, use that for subsequent
                # processing
                if result:
                    resp = self.wrap(req, result)

        return resp

    def wrap(self, req, result):
        """
        Wrap method return results.  The return value of the action
        method and of the action extensions is passed through this
        method before being returned to the caller.  Instances of
        `webob.Response` are thrown, to abort the rest of action and
        extension processing; otherwise, objects which are not
        instances of ResponseObject will be wrapped in one.
        """

        if isinstance(result, webob.Response):
            # Straight-up webob Response object; we use raise to bail
            # out immediately and pass it upstream
            raise result
        elif isinstance(result, response.ResponseObject):
            # Already a ResponseObject; bind it to this descriptor
            result._bind(self)
            return result
        else:
            # Create a new, bound, ResponseObject
            return self.resp_type(req, result, _descriptor=self)

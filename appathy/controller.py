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

import functools

import metatools
import webob
import webob.exc

from appathy import exceptions
from appathy import response
from appathy import utils


class ControllerMeta(metatools.MetaClass):
    """
    Metaclass for class Controller.  Methods decorated with the
    @action() and @extends decorators are registered, and the default
    serializers and deserializers are set up.  Uses the metatools
    package to ensure inheritance of the path prefix, actions,
    extensions, serializers, and deserializers.
    """

    def __new__(mcs, name, bases, namespace):
        """
        Create a new Controller subclass.
        """

        # Normalize any specified path prefix
        if 'wsgi_path_prefix' in namespace:
            prefix = utils.norm_path(namespace['wsgi_path_prefix'], False)

            # If one of our bases has wsgi_path_prefix, prepend the
            # first one
            base_pfxs = [getattr(b, 'wsgi_path_prefix') for b in bases
                         if hasattr(b, 'wsgi_path_prefix')]
            if base_pfxs:
                prefix = base_pfxs[0] + prefix

            namespace['wsgi_path_prefix'] = prefix

        # Initialize the sets of actions and extensions
        actions = set()
        extensions = set()

        # Initialize serializers and deserializers
        serializers = {}
        deserializers = {}

        # Add the sets to the class dictionary
        namespace['_wsgi_actions'] = actions
        namespace['_wsgi_extensions'] = extensions

        # Add the serializers and deserializers to the class
        # dictionary
        namespace['_wsgi_serializers'] = serializers
        namespace['_wsgi_deserializers'] = deserializers

        # Find the action and extension methods
        for key, value in namespace.items():
            # Skip internal symbols and non-callables
            if key[0] == '_' or key.startswith('wsgi_') or not callable(value):
                continue

            # Is it an action or extension?
            if hasattr(value, '_wsgi_action'):
                actions.add(key)
            elif hasattr(value, '_wsgi_extension'):
                extensions.add(key)

        # Allow inheritance in our actions, extensions, serializers,
        # and deserializers
        for base in mcs.iter_bases(bases):
            mcs.inherit_set(base, namespace, '_wsgi_actions')
            mcs.inherit_set(base, namespace, '_wsgi_extensions')
            mcs.inherit_dict(base, namespace, '_wsgi_serializers')
            mcs.inherit_dict(base, namespace, '_wsgi_deserializers')

        return super(ControllerMeta, mcs).__new__(mcs, name, bases, namespace)


class Controller(object):
    """
    Identifies a resource.  All controllers must specify the attribute
    `wsgi_name`, which must be unique across all controllers; this
    name is used to formulate route names.  In addition, controllers
    may specify `wsgi_path_prefix`, which is used to prefix all action
    method paths, and `wsgi_resp_type`, to override the default
    ResponseObject class.  All other attributes beginning with `wsgi_`
    or `_wsgi_` are reserved.

    Note that the `wsgi_path_prefix` attribute is subject to
    inheritance; if a superclass defines `wsgi_path_prefix`, its value
    will be prepended to the one specified for this class.
    """

    __metaclass__ = ControllerMeta

    wsgi_resp_type = response.ResponseObject

    def __new__(cls, mapper=None):
        """
        Prefilter controller class instantiation.  Prohibits
        instantiation of a Controller subclass unless the class has
        the `wsgi_name` attribute set.
        """

        # Make sure we have a name; names are used for building routes
        if not hasattr(cls, 'wsgi_name'):
            raise exceptions.IncompleteController()

        return super(Controller, cls).__new__(cls, mapper)

    def __init__(self, mapper=None):
        """
        Initialize a Controller subclass.  The `mapper` argument is
        used by the Application class to specify the Routes mapper
        being constructed.
        """

        # Build up our mapping of action to method
        self.wsgi_actions = dict((k, getattr(self, k))
                                 for k in self._wsgi_actions)
        self.wsgi_extensions = dict((k, [getattr(self, k)])
                                    for k in self._wsgi_extensions)

        # Storage place for method descriptors
        self.wsgi_descriptors = {}

        # Save the mapper
        self.wsgi_mapper = mapper

        # Set up our routes
        if mapper:
            for action, route in self.wsgi_actions.items():
                self._route(action, route)

    def __call__(self, req, params):
        """
        Dispatch a request with the given parameters (developed from
        the path specified to the @action() decorator) to an
        appropriate action.  Deserializes any request body, processes
        extensions, calls the appropriate action method, and
        serializes the response, which is then returned.
        """

        # What action are we looking for?
        action = params.pop('action')

        # Look up the method in question
        descriptor = self._get_action(action)
        if not descriptor:
            raise webob.exc.HTTPNotFound()

        # Now we need to deserialize the body...
        body = descriptor.deserialize_request(req)
        if body is not None:
            params['body'] = body

        # Process the extensions...
        resp, post_list = descriptor.pre_process(req, params)

        # Call the actual action method...
        if not resp:
            resp = descriptor(req, params)

        # Perform post-processing...
        resp = descriptor.post_process(post_list, req, resp, params)

        # And finally, serialize and return the response
        return resp.serialize()

    def _get_action(self, action):
        """
        Retrieve a descriptor for the named action.  Caches
        descriptors for efficiency.
        """

        # If we don't have an action named that, bail out
        if action not in self.wsgi_actions:
            return None

        # Generate an ActionDescriptor if necessary
        if action not in self.wsgi_descriptors:
            self.wsgi_descriptors[action] = ActionDescriptor(
                self.wsgi_actions[action],
                self.wsgi_extensions.get(action, []),
                self.wsgi_resp_type)

        # OK, return the method descriptor
        return self.wsgi_descriptors[action]

    def _route(self, action, method):
        """
        Given an action method, generates a route for it.
        """

        # Compute route name
        name = '%s_%s' % (self.wsgi_name, action)

        # Set up path
        path = getattr(self, 'wsgi_path_prefix', '') + method._wsgi_path

        # Build up the conditions
        conditions = {}
        if hasattr(method, '_wsgi_methods'):
            conditions['method'] = method._wsgi_methods
        if hasattr(method, '_wsgi_condition'):
            conditions['function'] = method._wsgi_condition

        # Create the route
        self.wsgi_mapper.connect(name, path,
                                 controller=self,
                                 action=action,
                                 conditions=conditions,
                                 **getattr(method, '_wsgi_keywords', {}))

    def wsgi_extend(self, controller):
        """
        Extends a controller by registering another controller as an
        extension of it.  All actions defined on the extension
        controller have routes generated for them (only if none
        already exist) and are made actions of this controller; all
        extensions defined on the extension controller are added to
        the extensions registered on this controller.
        """

        # Add/override actions
        for key, action in controller.wsgi_actions.items():
            # If it's a new action, we'll need to route
            if self.mapper and key not in self.wsgi_actions:
                self._route(key, action)

            self.wsgi_actions[key] = action

            # Clear existing action descriptors
            if key in self.wsgi_descriptors:
                del self.wsgi_descriptors[key]

        # Register extensions
        for key, extensions in controller.wsgi_extensions.items():
            # Skip empty extension lists
            if not extensions:
                continue

            # Prime the pump...
            if key not in self.wsgi_extensions:
                self.wsgi_extensions[key] = []

            # Add the extensions
            self.wsgi_extensions[key].extend(extensions)

            # Clear existing action descriptors
            if key in self.wsgi_descriptors:
                del self.wsgi_descriptors[key]


def action(path, *methods, **kwargs):
    """
    Decorator which marks a method as an action.  The first positional
    argument identifies a Routes-compatible path for the action
    method.  If specified, remaining positional arguments identify
    permitted HTTP methods.  The following keyword arguments are also
    recognized:

    * conditions
        Identifies a single function which will be passed the request
        (an instance of `webob.Request` and the match dictionary.  It
        should return True if the route matches, and False otherwise.

    * code
        Specifies the default HTTP return code to use for the
        response.  If not specified, defaults to 200.  Note that the
        action method may always return a ResponseObject instance with
        an alternate code, if desired.

    All other keyword arguments will be statically passed to the
    action method when called.
    """

    # Build up the function attributes
    attrs = dict(_wsgi_action=True)

    # Normalize the path and set the attr
    attrs['_wsgi_path'] = utils.norm_path(path)

    # Are we restricting the methods?
    if methods:
        attrs['_wsgi_methods'] = [meth.upper() for meth in methods]

    # If we have a condition function, set it up
    if 'conditions' in kwargs:
        condition = kwargs.pop('conditions')
        @functools.wraps(condition)
        def wrapper(req, match_dict):
            if isinstance(req, dict):
                req = webob.Request(req)
            return condition(req, match_dict)
        attrs['_wsgi_condition'] = wrapper

    # If we have a default code, set it up
    if 'code' in kwargs:
        attrs['_wsgi_code'] = kwargs.pop('code')

    # Strip out action and controller arguments
    kwargs.pop('action', None)
    kwargs.pop('controller', None)

    # Save additional keyword arguments
    if kwargs:
        attrs['_wsgi_keywords'] = kwargs

    # Now, build the decorator we're going to return
    def decorator(func):
        # Save the attributes
        func.__dict__.update(attrs)
        return func

    return decorator


def extends(func):
    """
    Decorator which marks a method as an extension.  The method must
    have the same name as the method it is extending.  Extensions come
    in two flavors:

    * Generator extensions
        During request processing, generator extensions are called
        before calling the action method.  They may perform any
        desired preprocessing of the request, then they must yield.
        After the action method has been called, the final
        ResponseObject will be sent back to the generator (appearing
        as the return value of the "yield" statement), and the
        generator extension may perform any desired postprocessing of
        the response.  Note that if an actual value is yielded back to
        the caller, the postprocessing part of the generator will not
        be called, and normal request processing is aborted.  Also
        note that the postprocessing portions of all prior extensions
        *will* be called on the yielded response.

    * Regular extensions
        Regular extensions are simple methods, rather than generator
        methods.  They are only called during the postprocessing stage
        of request processing.

    During the postprocessing stage, if a generator extension yields
    another value or a regular extension returns a value, that value
    will be wrapped in a ResponseObject and will be used for
    subsequent postprocessing.
    """

    # Mark the function as an extension
    func._wsgi_extension = True
    return func

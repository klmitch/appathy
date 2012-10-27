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

import logging

import routes
from routes import middleware
import webob.dec
import webob.exc

from appathy import exceptions
from appathy import utils


LOG = logging.getLogger('appathy')


class Application(middleware.RoutesMiddleware):
    """
    Provides a PasteDeploy-compatible application class.  Resources
    and extensions are computed from the configuration; keys beginning
    with 'resource.' identify resources, and keys beginning with
    'extend.' identify space-separated lists of extensions to apply to
    the corresponding resource.  The part after the '.' names the
    resource being created or extended.  The values identify instances
    of class Controller, which define the actual resource or an
    extension.
    """

    def __init__(self, global_config, **local_conf):
        """
        Initialize the Application.
        """

        # Let's get a mapper
        mapper = routes.Mapper(register=False)

        # Now, set up our primary controllers
        self.resources = {}
        extensions = {}
        for key, value in local_conf.items():
            if '.' not in key:
                continue

            # OK, split up the key name
            item_type, item_name = key.split('.', 1)

            if item_type == 'extend':
                # Filter out extensions for later processing
                values = value.split()

                ext_list = []
                seen = set()
                for value in values:
                    # Filter out repeats
                    if value in seen:
                        continue
                    ext_list.append(value)
                    seen.add(value)

                extensions[item_name] = ext_list
            elif item_type == 'resource':
                # Set up resources
                controller = utils.import_controller(value)
                self.resources[item_name] = controller(mapper)

        # Now apply extensions
        for name, ext_list in extensions.items():
            if name not in self.resources:
                raise exceptions.NoSuchResource(name)
            res = self.resources[name]

            for ext_class in ext_list:
                # Get the class
                ext = utils.import_controller(ext_class)

                # Register the extension
                res.wsgi_extend(ext())

        # Now, with all routes set up, initialize the middleware
        super(Application, self).__init__(self.dispatch, mapper,
                                          singleton=False)

    @webob.dec.wsgify
    def dispatch(self, req):
        """
        Called by the Routes middleware to dispatch the request to the
        appropriate controller.  If a webob exception is raised, it is
        returned; if some other exception is raised, the webob
        `HTTPInternalServerError` exception is raised.  Otherwise, the
        return value of the controller is returned.
        """

        # Grab the request parameters
        params = req.environ['wsgiorg.routing_args'][1]

        # What controller is authoritative?
        controller = params.pop('controller')

        # Determine its name
        cont_class = controller.__class__
        cont_name = "%s:%s" % (cont_class.__module__, cont_class.__name__)

        # Determine the origin of the request
        origin = req.remote_addr if req.remote_addr else '[local]'
        if req.remote_user:
            origin = '%s (%s)' % (origin, req.remote_user)

        # Log that we're processing the request
        LOG.info("%s %s %s (controller %r)" %
                 (origin, req.method, req.url, cont_name))

        # Call into that controller
        try:
            return controller(req, params)
        except webob.exc.HTTPException as e:
            # Return the HTTP exception directly
            return e
        except exceptions.AppathyResponse as e:
            # Return the webob.Response directly
            return e.response
        except Exception as e:
            # Log the controller exception
            LOG.exception("Exception occurred in controller %r" % cont_name)

            # These exceptions result in a 500.  Note we're
            # intentionally not including the exception message, since
            # it could contain sensitive data.
            return webob.exc.HTTPInternalServerError()

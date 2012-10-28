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

import mock
import webob.exc

from appathy import application
from appathy import controller
from appathy import exceptions
from appathy import utils

import tests


class RequestTest(tests.TestCase):
    def test_context_unpopulated(self):
        req = application.Request.blank('/spam')

        self.assertEqual(req.context, None)

    def test_context_populated(self):
        req = application.Request.blank('/spam',
                                        environ={'appathy.context': 'context'})

        self.assertEqual(req.context, 'context')

    def test_context_setter(self):
        req = application.Request.blank('/spam')

        req.context = 'context'

        self.assertEqual(req.environ['appathy.context'], 'context')

    def test_context_deleter(self):
        req = application.Request.blank('/spam',
                                        environ={'appathy.context': 'context'})

        del req.context

        self.assertFalse('appathy.context' in req.environ)


class ApplicationTest(tests.TestCase):
    @mock.patch('routes.middleware.RoutesMiddleware.__init__')
    @mock.patch('routes.Mapper', return_value=mock.Mock())
    @mock.patch.object(utils, 'import_controller')
    def test_init_noconf(self, mock_import_controller, mock_Mapper,
                         mock_RoutesMiddleware):
        config = {
            'conf1': 1,
            'conf2': 2,
            'spam.conf3': 3,
            'spam.conf4': 4,
        }

        app = application.Application('global_conf', **config)

        mock_Mapper.assert_called_once_with(register=False)
        self.assertEqual(app.resources, {})
        self.assertFalse(mock_import_controller.called)
        mock_RoutesMiddleware.assert_called_once_with(
            mock.ANY, mock_Mapper.return_value, singleton=False)
        dispatch = mock_RoutesMiddleware.call_args[0][0]
        self.assertEqual(dispatch.func, app.dispatch.func)

    @mock.patch('routes.middleware.RoutesMiddleware.__init__')
    @mock.patch('routes.Mapper', return_value=mock.Mock())
    @mock.patch.object(utils, 'import_controller')
    def test_init_resources(self, mock_import_controller, mock_Mapper,
                            mock_RoutesMiddleware):
        controllers = dict(
            res1=mock.Mock(return_value='resource 1'),
            res2=mock.Mock(return_value='resource 2'),
            res3=mock.Mock(return_value='resource 3'),
        )
        mock_import_controller.side_effect = lambda x: controllers[x]
        config = {
            'resource.resource1': 'res1',
            'resource.resource2': 'res2',
            'resource.resource3': 'res3',
        }

        app = application.Application('global_conf', **config)

        mock_Mapper.assert_called_once_with(register=False)
        self.assertEqual(app.resources, dict(
            resource1='resource 1',
            resource2='resource 2',
            resource3='resource 3',
        ))
        mock_import_controller.assert_has_calls([
            mock.call('res1'),
            mock.call('res2'),
            mock.call('res3'),
        ], any_order=True)
        controllers['res1'].assert_called_once_with(mock_Mapper.return_value)
        controllers['res2'].assert_called_once_with(mock_Mapper.return_value)
        controllers['res3'].assert_called_once_with(mock_Mapper.return_value)
        mock_RoutesMiddleware.assert_called_once_with(
            mock.ANY, mock_Mapper.return_value, singleton=False)
        dispatch = mock_RoutesMiddleware.call_args[0][0]
        self.assertEqual(dispatch.func, app.dispatch.func)

    @mock.patch('routes.middleware.RoutesMiddleware.__init__')
    @mock.patch('routes.Mapper', return_value=mock.Mock())
    @mock.patch.object(utils, 'import_controller')
    def test_init_extensions(self, mock_import_controller, mock_Mapper,
                             mock_RoutesMiddleware):
        controllers = dict(
            res1=mock.Mock(return_value=mock.Mock()),
            res2=mock.Mock(return_value=mock.Mock()),
            res3=mock.Mock(return_value=mock.Mock()),
            ext11=mock.Mock(return_value='resource 1 extension 1'),
            ext12=mock.Mock(return_value='resource 1 extension 2'),
            ext13=mock.Mock(return_value='resource 1 extension 3'),
            ext21=mock.Mock(return_value='resource 2 extension 1'),
        )
        mock_import_controller.side_effect = lambda x: controllers[x]
        config = {
            'resource.resource1': 'res1',
            'resource.resource2': 'res2',
            'resource.resource3': 'res3',
            'extend.resource1': 'ext11 ext12 ext13',
            'extend.resource2': 'ext21 ext21',
        }

        app = application.Application('global_conf', **config)

        mock_Mapper.assert_called_once_with(register=False)
        self.assertEqual(app.resources, dict(
            resource1=controllers['res1'].return_value,
            resource2=controllers['res2'].return_value,
            resource3=controllers['res3'].return_value,
        ))
        mock_import_controller.assert_has_calls([
            mock.call('res1'),
            mock.call('res2'),
            mock.call('res3'),
            mock.call('ext11'),
            mock.call('ext12'),
            mock.call('ext13'),
            mock.call('ext21'),
        ], any_order=True)
        controllers['res1'].assert_called_once_with(mock_Mapper.return_value)
        controllers['res2'].assert_called_once_with(mock_Mapper.return_value)
        controllers['res3'].assert_called_once_with(mock_Mapper.return_value)
        controllers['ext11'].assert_called_once_with()
        controllers['ext12'].assert_called_once_with()
        controllers['ext13'].assert_called_once_with()
        controllers['ext21'].assert_called_once_with()
        controllers['res1'].return_value.assert_has_calls([
            mock.call.wsgi_extend('resource 1 extension 1'),
            mock.call.wsgi_extend('resource 1 extension 2'),
            mock.call.wsgi_extend('resource 1 extension 3'),
        ])
        controllers['res2'].return_value.assert_has_calls([
            mock.call.wsgi_extend('resource 2 extension 1'),
        ])
        self.assertFalse(controllers['res3'].return_value.wsgi_extend.called)
        mock_RoutesMiddleware.assert_called_once_with(
            mock.ANY, mock_Mapper.return_value, singleton=False)
        dispatch = mock_RoutesMiddleware.call_args[0][0]
        self.assertEqual(dispatch.func, app.dispatch.func)

    @mock.patch('routes.middleware.RoutesMiddleware.__init__')
    @mock.patch('routes.Mapper', return_value=mock.Mock())
    @mock.patch.object(utils, 'import_controller')
    def test_init_extensions_noresource(self, mock_import_controller,
                                        mock_Mapper, mock_RoutesMiddleware):
        controllers = dict(
            ext11=mock.Mock(return_value='resource 1 extension 1'),
        )
        mock_import_controller.side_effect = lambda x: controllers[x]
        config = {
            'extend.noresource': 'ext11',
        }

        with self.assertRaises(exceptions.NoSuchResource):
            app = application.Application('global_conf', **config)

        mock_Mapper.assert_called_once_with(register=False)
        self.assertFalse(mock_import_controller.called)
        self.assertFalse(mock_RoutesMiddleware.called)

    @staticmethod
    def make_request(method, url, controller, remote_addr=None,
                     remote_user=None, **kwargs):
        # Add controller to kwargs
        kwargs['controller'] = controller

        # Build our environment
        environ = {
            'wsgiorg.routing_args': ((), kwargs),
        }

        # Build and return the request
        return mock.NonCallableMock(method=method, url=url, environ=environ,
                                    remote_addr=remote_addr,
                                    remote_user=remote_user)

    @mock.patch.object(application.Application, '__init__', return_value=None)
    def test_dispatch_simple(self, _mock_Application):
        cont = mock.Mock(spec=controller.Controller, return_value='response')
        req = self.make_request('GET', '/spam', cont, a=1, b=2, c=3)
        app = application.Application()

        result = app.dispatch(req)

        self.assertEqual(self.log_messages, [
            "[local] GET /spam (controller 'appathy.controller:Controller')",
        ])
        cont.assert_called_once_with(req, dict(a=1, b=2, c=3))
        self.assertEqual(result, 'response')

    @mock.patch.object(application.Application, '__init__', return_value=None)
    def test_dispatch_withremote(self, _mock_Application):
        cont = mock.Mock(spec=controller.Controller, return_value='response')
        req = self.make_request('GET', '/spam', cont, a=1, b=2, c=3,
                                remote_addr='127.0.0.1:8080',
                                remote_user='user')
        app = application.Application()

        result = app.dispatch(req)

        self.assertEqual(self.log_messages, [
            "127.0.0.1:8080 (user) GET /spam (controller "
            "'appathy.controller:Controller')",
        ])
        cont.assert_called_once_with(req, dict(a=1, b=2, c=3))
        self.assertEqual(result, 'response')

    @mock.patch.object(application.Application, '__init__', return_value=None)
    def test_dispatch_httpexception(self, _mock_Application):
        response = webob.exc.HTTPNotFound()
        cont = mock.Mock(spec=controller.Controller, side_effect=response)
        req = self.make_request('GET', '/spam', cont)
        app = application.Application()

        result = app.dispatch(req)

        self.assertEqual(self.log_messages, [
            "[local] GET /spam (controller 'appathy.controller:Controller')",
        ])
        cont.assert_called_once_with(req, {})
        self.assertEqual(id(result), id(response))

    @mock.patch.object(application.Application, '__init__', return_value=None)
    def test_dispatch_appathyresponse(self, _mock_Application):
        response = exceptions.AppathyResponse('response')
        cont = mock.Mock(spec=controller.Controller, side_effect=response)
        req = self.make_request('GET', '/spam', cont)
        app = application.Application()

        result = app.dispatch(req)

        self.assertEqual(self.log_messages, [
            "[local] GET /spam (controller 'appathy.controller:Controller')",
        ])
        cont.assert_called_once_with(req, {})
        self.assertEqual(result, 'response')

    @mock.patch.object(application.Application, '__init__', return_value=None)
    def test_dispatch_exception(self, _mock_Application):
        response = tests.TestException('this is a test')
        cont = mock.Mock(spec=controller.Controller, side_effect=response)
        req = self.make_request('GET', '/spam', cont)
        app = application.Application()

        result = app.dispatch(req)

        self.assertEqual(self.log_messages[:1], [
            "[local] GET /spam (controller 'appathy.controller:Controller')",
        ])
        self.assertTrue(self.log_messages[1].startswith(
            "Exception occurred in controller "
            "'appathy.controller:Controller'"))
        cont.assert_called_once_with(req, {})
        self.assertIsInstance(result, webob.exc.HTTPInternalServerError)
        self.assertEqual(str(result), 'The server has either erred or is '
                         'incapable of performing the requested operation.')

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

from appathy import controller
from appathy import exceptions
from appathy import response

import tests


class ExtendsTest(tests.TestCase):
    def test_extends(self):
        @controller.extends
        def func():
            pass

        self.assertEqual(func._wsgi_extension, True)


class ActionTest(tests.TestCase):
    def test_basic(self):
        @controller.action()
        def func():
            pass

        self.assertEqual(func._wsgi_action, True)
        self.assertEqual(func._wsgi_path, None)
        self.assertEqual(func._wsgi_methods, None)
        self.assertFalse(hasattr(func, '_wsgi_condition'))
        self.assertFalse(hasattr(func, '_wsgi_code'))
        self.assertFalse(hasattr(func, '_wsgi_keywords'))

    def test_path(self):
        @controller.action('/path')
        def func():
            pass

        self.assertEqual(func._wsgi_action, True)
        self.assertEqual(func._wsgi_path, '/path')
        self.assertFalse(hasattr(func, '_wsgi_methods'))
        self.assertFalse(hasattr(func, '_wsgi_condition'))
        self.assertFalse(hasattr(func, '_wsgi_code'))
        self.assertFalse(hasattr(func, '_wsgi_keywords'))

    def test_methods(self):
        @controller.action('/path', 'MeThOd1', 'mEtHoD2')
        def func():
            pass

        self.assertEqual(func._wsgi_action, True)
        self.assertEqual(func._wsgi_path, '/path')
        self.assertEqual(func._wsgi_methods, ['METHOD1', 'METHOD2'])
        self.assertFalse(hasattr(func, '_wsgi_condition'))
        self.assertFalse(hasattr(func, '_wsgi_code'))
        self.assertFalse(hasattr(func, '_wsgi_keywords'))

    def test_code(self):
        @controller.action(code=404)
        def func():
            pass

        self.assertEqual(func._wsgi_action, True)
        self.assertEqual(func._wsgi_path, None)
        self.assertEqual(func._wsgi_methods, None)
        self.assertFalse(hasattr(func, '_wsgi_condition'))
        self.assertEqual(func._wsgi_code, 404)
        self.assertFalse(hasattr(func, '_wsgi_keywords'))

    def test_keywords(self):
        @controller.action(action='action', controller='controller',
                           kwarg1='kwarg1', kwarg2='kwarg2')
        def func():
            pass

        self.assertEqual(func._wsgi_action, True)
        self.assertEqual(func._wsgi_path, None)
        self.assertEqual(func._wsgi_methods, None)
        self.assertFalse(hasattr(func, '_wsgi_condition'))
        self.assertFalse(hasattr(func, '_wsgi_code'))
        self.assertEqual(func._wsgi_keywords,
                         dict(kwarg1='kwarg1', kwarg2='kwarg2'))

    @mock.patch('webob.Request', return_value='request')
    def test_condition(self, mock_Request):
        def condition(req, match_dict):
            self.assertEqual(req, 'req')
            self.assertEqual(match_dict, 'match_dict')
            return 'result'

        @controller.action(conditions=condition)
        def func():
            pass

        self.assertEqual(func._wsgi_action, True)
        self.assertEqual(func._wsgi_path, None)
        self.assertEqual(func._wsgi_methods, None)
        self.assertNotEqual(func._wsgi_condition, None)
        self.assertFalse(hasattr(func, '_wsgi_code'))
        self.assertFalse(hasattr(func, '_wsgi_keywords'))

        result = func._wsgi_condition('req', 'match_dict')

        self.assertFalse(mock_Request.called)
        self.assertEqual(result, 'result')

    @mock.patch('webob.Request', return_value='request')
    def test_condition_request(self, mock_Request):
        def condition(req, match_dict):
            self.assertEqual(req, 'request')
            self.assertEqual(match_dict, 'match_dict')
            return 'result'

        @controller.action(conditions=condition)
        def func():
            pass

        self.assertEqual(func._wsgi_action, True)
        self.assertEqual(func._wsgi_path, None)
        self.assertEqual(func._wsgi_methods, None)
        self.assertNotEqual(func._wsgi_condition, None)
        self.assertFalse(hasattr(func, '_wsgi_code'))
        self.assertFalse(hasattr(func, '_wsgi_keywords'))

        result = func._wsgi_condition(dict(request='request'), 'match_dict')

        mock_Request.assert_called_once_with(dict(request='request'))
        self.assertEqual(result, 'result')


def mock_action(func):
    func._wsgi_action = True
    return func


def mock_extends(func):
    func._wsgi_extension = True
    return func


class ControllerMetaTest(tests.TestCase):
    def test_basic(self):
        exemplar = dict(
            _wsgi_actions=set(),
            _wsgi_extensions=set(),
            _wsgi_serializers={},
            _wsgi_deserializers={},
            wsgi_method_map={},
        )

        class TestController(object):
            __metaclass__ = controller.ControllerMeta

        self.assertEqual(self.dict_select(TestController.__dict__, exemplar),
                         exemplar)
        self.assertFalse(hasattr(TestController, 'wsgi_path_prefix'))

    def test_collect_actions(self):
        exemplar = dict(
            _wsgi_actions=set(['action']),
            _wsgi_extensions=set(),
            _wsgi_serializers={},
            _wsgi_deserializers={},
            wsgi_method_map={},
        )

        class TestController(object):
            __metaclass__ = controller.ControllerMeta

            @mock_action
            def _int_action():
                pass

            @mock_action
            def wsgi_action():
                pass

            @mock_action
            def action():
                pass

            def nonaction():
                pass

            uncallable = mock.NonCallableMock(_wsgi_action=True)

        self.assertEqual(self.dict_select(TestController.__dict__, exemplar),
                         exemplar)

    def test_collect_extensions(self):
        exemplar = dict(
            _wsgi_actions=set(),
            _wsgi_extensions=set(['extension']),
            _wsgi_serializers={},
            _wsgi_deserializers={},
            wsgi_method_map={},
        )

        class TestController(object):
            __metaclass__ = controller.ControllerMeta

            @mock_extends
            def _int_extension():
                pass

            @mock_extends
            def wsgi_extension():
                pass

            @mock_extends
            def extension():
                pass

            def nonextension():
                pass

            uncallable = mock.NonCallableMock(_wsgi_extension=True)

        self.assertEqual(self.dict_select(TestController.__dict__, exemplar),
                         exemplar)

    def test_path_prefix(self):
        exemplar = dict(
            wsgi_path_prefix='/prefix',
            _wsgi_actions=set(),
            _wsgi_extensions=set(),
            _wsgi_serializers={},
            _wsgi_deserializers={},
            wsgi_method_map={},
        )

        class TestController(object):
            __metaclass__ = controller.ControllerMeta

            wsgi_path_prefix = '/prefix'

        self.assertEqual(self.dict_select(TestController.__dict__, exemplar),
                         exemplar)

    def test_path_prefix_inheritance(self):
        exemplar = dict(
            wsgi_path_prefix='/base1/prefix',
            _wsgi_actions=set(),
            _wsgi_extensions=set(),
            _wsgi_serializers={},
            _wsgi_deserializers={},
            wsgi_method_map={},
        )

        class Base1(object):
            wsgi_path_prefix = '/base1'

        class Base2(object):
            wsgi_path_prefix = '/base2'

        class TestController(Base1, Base2):
            __metaclass__ = controller.ControllerMeta

            wsgi_path_prefix = '/prefix'

        self.assertEqual(self.dict_select(TestController.__dict__, exemplar),
                         exemplar)


class ControllerTest(tests.TestCase):
    def test_init_unnamed(self):
        class TestController(controller.Controller):
            pass

        with self.assertRaises(exceptions.IncompleteController):
            cont = TestController()

    @mock.patch.object(controller.Controller, '_route')
    def test_init(self, mock_route):
        class TestController(controller.Controller):
            wsgi_name = 'name'

        cont = TestController()

        self.assertEqual(cont.wsgi_resp_type, response.ResponseObject)
        self.assertEqual(cont.wsgi_method_map, dict(
            create=("/%s", ["POST"]),
            index=("/%s", ["GET"]),
            show=("/%s/{id}", ["GET"]),
            update=("/%s/{id}", ["PUT"]),
            delete=("/%s/{id}", ["DELETE"]),
        ))
        self.assertEqual(cont.wsgi_actions, {})
        self.assertEqual(cont.wsgi_extensions, {})
        self.assertEqual(cont.wsgi_descriptors, {})
        self.assertEqual(cont.wsgi_mapper, None)
        self.assertFalse(mock_route.called)

    @mock.patch.object(controller.Controller, '_route')
    def test_init_actions_collector(self, mock_route):
        class TestController(controller.Controller):
            wsgi_name = 'name'

            @mock_action
            def action1():
                pass

            @mock_action
            def action2():
                pass

        cont = TestController()

        self.assertEqual(cont.wsgi_actions, dict(
            action1=cont.action1,
            action2=cont.action2,
        ))
        self.assertEqual(cont.wsgi_extensions, {})
        self.assertEqual(cont.wsgi_descriptors, {})
        self.assertEqual(cont.wsgi_mapper, None)
        self.assertFalse(mock_route.called)

    @mock.patch.object(controller.Controller, '_route')
    def test_init_extensions_collector(self, mock_route):
        class TestController(controller.Controller):
            wsgi_name = 'name'

            @mock_extends
            def action1():
                pass

            @mock_extends
            def action2():
                pass

        cont = TestController()

        self.assertEqual(cont.wsgi_actions, {})
        self.assertEqual(cont.wsgi_extensions, dict(
            action1=[cont.action1],
            action2=[cont.action2],
        ))
        self.assertEqual(cont.wsgi_descriptors, {})
        self.assertEqual(cont.wsgi_mapper, None)
        self.assertFalse(mock_route.called)

    @mock.patch.object(controller.Controller, '_route')
    def test_init_with_mapper(self, mock_route):
        class TestController(controller.Controller):
            wsgi_name = 'name'

            @mock_action
            def action1():
                pass

            @mock_action
            def action2():
                pass

        cont = TestController('mapper')

        self.assertEqual(cont.wsgi_actions, dict(
            action1=cont.action1,
            action2=cont.action2,
        ))
        self.assertEqual(cont.wsgi_extensions, {})
        self.assertEqual(cont.wsgi_descriptors, {})
        self.assertEqual(cont.wsgi_mapper, 'mapper')
        mock_route.assert_has_calls([
            mock.call('action1', cont.action1),
            mock.call('action2', cont.action2),
        ])

    def test_route(self):
        class TestController(controller.Controller):
            wsgi_name = 'name'

        def action():
            pass

        action._wsgi_path = '/path'

        cont = TestController(mock.Mock())

        cont._route('action', action)

        cont.wsgi_mapper.assert_has_calls([
            mock.call.connect('name_action', '/path', controller=cont,
                              action='action', conditions={}),
        ])

    def test_route_with_prefix(self):
        class TestController(controller.Controller):
            wsgi_name = 'name'
            wsgi_path_prefix = '/prefix'

        def action():
            pass

        action._wsgi_path = '/path'

        cont = TestController(mock.Mock())

        cont._route('action', action)

        cont.wsgi_mapper.assert_has_calls([
            mock.call.connect('name_action', '/prefix/path', controller=cont,
                              action='action', conditions={}),
        ])

    def test_route_methods(self):
        class TestController(controller.Controller):
            wsgi_name = 'name'

        def action():
            pass

        action._wsgi_path = '/path'
        action._wsgi_methods = ['GET', 'DELETE']

        cont = TestController(mock.Mock())

        cont._route('action', action)

        cont.wsgi_mapper.assert_has_calls([
            mock.call.connect('name_action', '/path', controller=cont,
                              action='action', conditions=dict(
                                  method=['GET', 'DELETE'],
                              )),
        ])

    def test_route_condition(self):
        class TestController(controller.Controller):
            wsgi_name = 'name'

        def action():
            pass

        action._wsgi_path = '/path'
        action._wsgi_condition = 'condition'

        cont = TestController(mock.Mock())

        cont._route('action', action)

        cont.wsgi_mapper.assert_has_calls([
            mock.call.connect('name_action', '/path', controller=cont,
                              action='action', conditions=dict(
                                  function='condition',
                              )),
        ])

    def test_route_missing_rule(self):
        class TestController(controller.Controller):
            wsgi_name = 'name'

        def action():
            pass

        action._wsgi_path = None
        action._wsgi_methods = None

        cont = TestController(mock.Mock())

        cont._route('action', action)

        self.assertFalse(cont.wsgi_mapper.called)
        self.assertEqual(self.log_messages, [
            'No path specified for action method action() of resource name',
        ])

    def test_route_with_rule(self):
        class TestController(controller.Controller):
            wsgi_name = 'name'
            wsgi_method_map = dict(
                action=("/%s", ["ACTION"]),
            )

        def action():
            pass

        action._wsgi_path = None
        action._wsgi_methods = None

        cont = TestController(mock.Mock())

        cont._route('action', action)

        cont.wsgi_mapper.assert_has_calls([
            mock.call.connect('name_action', '/name', controller=cont,
                              action='action', conditions=dict(
                                  method=['ACTION'],
                              )),
        ])

    def test_route_keywords(self):
        class TestController(controller.Controller):
            wsgi_name = 'name'

        def action():
            pass

        action._wsgi_path = '/path'
        action._wsgi_keywords = dict(a=1, b=2, c=3)

        cont = TestController(mock.Mock())

        cont._route('action', action)

        cont.wsgi_mapper.assert_has_calls([
            mock.call.connect('name_action', '/path', controller=cont,
                              action='action', conditions={}, a=1, b=2, c=3),
        ])

    @mock.patch.object(controller.Controller, '_route')
    def test_extend_actions(self, mock_route):
        class TestController(controller.Controller):
            wsgi_name = 'name'

            @mock_action
            def action2():
                pass

        extensions = mock.Mock(
            wsgi_actions=dict(
                action1='action 1',
                action2='action 2',
                action3='action 3',
            ),
            wsgi_extensions={},
        )

        cont = TestController()

        cont.wsgi_extend(extensions)

        self.assertEqual(cont.wsgi_actions, dict(
            action1='action 1',
            action2='action 2',
            action3='action 3',
        ))
        self.assertFalse(mock_route.called)

    @mock.patch.object(controller.Controller, '_route')
    def test_extend_actions_mapper(self, mock_route):
        class TestController(controller.Controller):
            wsgi_name = 'name'

            @mock_action
            def action2():
                pass

        extensions = mock.Mock(
            wsgi_actions=dict(
                action1='action 1',
                action2='action 2',
                action3='action 3',
            ),
            wsgi_extensions={},
        )

        cont = TestController(mock.Mock())

        cont.wsgi_extend(extensions)

        self.assertEqual(cont.wsgi_actions, dict(
            action1='action 1',
            action2='action 2',
            action3='action 3',
        ))
        mock_route.assert_has_calls([
            mock.call('action1', 'action 1'),
            mock.call('action3', 'action 3'),
        ], any_order=True)

    @mock.patch.object(controller.Controller, '_route')
    def test_extend_actions_descriptors(self, mock_route):
        class TestController(controller.Controller):
            wsgi_name = 'name'

            @mock_action
            def action2():
                pass

        extensions = mock.Mock(
            wsgi_actions=dict(
                action1='action 1',
                action2='action 2',
                action3='action 3',
            ),
            wsgi_extensions={},
        )

        cont = TestController()
        cont.wsgi_descriptors = dict(
            action1='descriptor 1',
            action4='descriptor 4',
        )

        cont.wsgi_extend(extensions)

        self.assertEqual(cont.wsgi_actions, dict(
            action1='action 1',
            action2='action 2',
            action3='action 3',
        ))
        self.assertEqual(cont.wsgi_descriptors, dict(
            action4='descriptor 4',
        ))
        self.assertFalse(mock_route.called)

    @mock.patch.object(controller.Controller, '_route')
    def test_extend_extensions(self, _mock_route):
        class TestController(controller.Controller):
            wsgi_name = 'name'

        extensions = mock.Mock(
            wsgi_actions={},
            wsgi_extensions=dict(
                action1=['action 1'],
                action2=['action 2', 'action 2a'],
                action3=[],
            ),
        )

        cont = TestController()
        cont.wsgi_extensions['action1'] = ['pre_ext 1']

        cont.wsgi_extend(extensions)

        self.assertEqual(cont.wsgi_extensions, dict(
            action1=['pre_ext 1', 'action 1'],
            action2=['action 2', 'action 2a'],
        ))

    @mock.patch.object(controller.Controller, '_route')
    def test_extend_extensions_descriptors(self, _mock_route):
        class TestController(controller.Controller):
            wsgi_name = 'name'

        extensions = mock.Mock(
            wsgi_actions={},
            wsgi_extensions=dict(
                action1=['action 1'],
                action2=['action 2', 'action 2a'],
                action3=[],
            ),
        )

        cont = TestController()
        cont.wsgi_extensions['action1'] = ['pre_ext 1']
        cont.wsgi_descriptors = dict(
            action1='descriptor 1',
            action4='descriptor 4',
        )

        cont.wsgi_extend(extensions)

        self.assertEqual(cont.wsgi_extensions, dict(
            action1=['pre_ext 1', 'action 1'],
            action2=['action 2', 'action 2a'],
        ))
        self.assertEqual(cont.wsgi_descriptors, dict(
            action4='descriptor 4',
        ))

    @mock.patch('appathy.actions.ActionDescriptor')
    def test_get_action_undeclared(self, mock_ActionDescriptor):
        class TestController(controller.Controller):
            wsgi_name = 'name'

        cont = TestController()

        result = cont._get_action('action1')

        self.assertEqual(result, None)
        self.assertFalse(mock_ActionDescriptor.called)

    @mock.patch('appathy.actions.ActionDescriptor')
    def test_get_action_cached(self, mock_ActionDescriptor):
        class TestController(controller.Controller):
            wsgi_name = 'name'

        cont = TestController()
        cont.wsgi_actions['action1'] = 'action 1'
        cont.wsgi_descriptors['action1'] = 'cached'

        result = cont._get_action('action1')

        self.assertEqual(result, 'cached')
        self.assertFalse(mock_ActionDescriptor.called)

    @mock.patch('appathy.actions.ActionDescriptor', return_value='descriptor')
    def test_get_action_generate(self, mock_ActionDescriptor):
        class TestController(controller.Controller):
            wsgi_name = 'name'

        cont = TestController()
        cont.wsgi_actions['action1'] = 'action 1'

        result = cont._get_action('action1')

        self.assertEqual(result, 'descriptor')
        mock_ActionDescriptor.assert_called_once_with('action 1', [],
                                                      response.ResponseObject)

    @mock.patch('appathy.actions.ActionDescriptor', return_value='descriptor')
    def test_get_action_generate_alt_resp_type(self, mock_ActionDescriptor):
        class TestController(controller.Controller):
            wsgi_name = 'name'
            wsgi_resp_type = 'response type'

        cont = TestController()
        cont.wsgi_actions['action1'] = 'action 1'

        result = cont._get_action('action1')

        self.assertEqual(result, 'descriptor')
        mock_ActionDescriptor.assert_called_once_with('action 1', [],
                                                      'response type')

    @mock.patch.object(controller.Controller, '_get_action')
    def test_call_noaction(self, mock_get_action):
        mock_get_action.return_value = None

        class TestController(controller.Controller):
            wsgi_name = 'name'

        cont = TestController()

        self.assertRaises(webob.exc.HTTPNotFound, cont, 'req',
                          dict(action='action'))
        mock_get_action.assert_called_once_with('action')

    @mock.patch.object(controller.Controller, '_get_action')
    def test_call_nobody_premature(self, mock_get_action):
        mock_response = mock.Mock(**{'_serialize.return_value': 'serialized'})
        mock_descriptor = mock.Mock(**{
            'deserialize_request.return_value': None,
            'pre_process.return_value': ('pre-response', 'post_list'),
            'post_process.return_value': mock_response,
        })
        mock_get_action.return_value = mock_descriptor

        class TestController(controller.Controller):
            wsgi_name = 'name'

        cont = TestController()

        result = cont('req', dict(action='action'))

        mock_get_action.assert_called_once_with('action')
        mock_descriptor.assert_has_calls([
            mock.call.deserialize_request('req'),
            mock.call.pre_process('req', {}),
            mock.call.post_process('post_list', 'req', 'pre-response', {}),
        ])
        mock_response._serialize.assert_called_once_with()
        self.assertEqual(result, 'serialized')

    @mock.patch.object(controller.Controller, '_get_action')
    def test_call_withbody_premature(self, mock_get_action):
        mock_response = mock.Mock(**{'_serialize.return_value': 'serialized'})
        mock_descriptor = mock.Mock(**{
            'deserialize_request.return_value': 'body',
            'pre_process.return_value': ('pre-response', 'post_list'),
            'post_process.return_value': mock_response,
        })
        mock_get_action.return_value = mock_descriptor

        class TestController(controller.Controller):
            wsgi_name = 'name'

        cont = TestController()

        result = cont('req', dict(action='action'))

        mock_get_action.assert_called_once_with('action')
        mock_descriptor.assert_has_calls([
            mock.call.deserialize_request('req'),
            mock.call.pre_process('req', dict(body='body')),
            mock.call.post_process('post_list', 'req', 'pre-response',
                                   dict(body='body')),
        ])
        mock_response._serialize.assert_called_once_with()
        self.assertEqual(result, 'serialized')

    @mock.patch.object(controller.Controller, '_get_action')
    def test_call_nobody(self, mock_get_action):
        mock_response = mock.Mock(**{'_serialize.return_value': 'serialized'})
        mock_descriptor = mock.Mock(**{
            'deserialize_request.return_value': None,
            'pre_process.return_value': (None, 'post_list'),
            'return_value': 'response',
            'post_process.return_value': mock_response,
        })
        mock_get_action.return_value = mock_descriptor

        class TestController(controller.Controller):
            wsgi_name = 'name'

        cont = TestController()

        result = cont('req', dict(action='action'))

        mock_get_action.assert_called_once_with('action')
        mock_descriptor.assert_has_calls([
            mock.call.deserialize_request('req'),
            mock.call.pre_process('req', {}),
            mock.call('req', {}),
            mock.call.post_process('post_list', 'req', 'response', {}),
        ])
        mock_response._serialize.assert_called_once_with()
        self.assertEqual(result, 'serialized')

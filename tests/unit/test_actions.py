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
import webob
import webob.exc

from appathy import actions
from appathy import exceptions
from appathy import response

import tests


class ActionMethodTest(tests.TestCase):
    @mock.patch('appathy.types.Translators',
                side_effect=['serializers', 'deserializers'])
    def test_init_function(self, mock_Translators):
        def function(a, b, c, d=4, e=5, f=6, *args, **kwargs):
            pass

        action = actions.ActionMethod(function)

        self.assertEqual(action.method, function)
        self.assertEqual(action.serializers, 'serializers')
        self.assertEqual(action.deserializers, 'deserializers')
        self.assertEqual(action.isgenerator, False)
        self.assertEqual(action.argspec,
                         (['a', 'b', 'c', 'd', 'e', 'f'], 'args', 'kwargs',
                          (4, 5, 6)))
        self.assertEqual(action.argidx, 0)
        mock_Translators.assert_has_calls([
            mock.call(function, '_wsgi_serializers'),
            mock.call(function, '_wsgi_deserializers'),
        ])

    @mock.patch('appathy.types.Translators',
                side_effect=['serializers', 'deserializers'])
    def test_init_generator(self, mock_Translators):
        def function(a, b, c, d=4, e=5, f=6, *args, **kwargs):
            yield

        action = actions.ActionMethod(function)

        self.assertEqual(action.method, function)
        self.assertEqual(action.serializers, 'serializers')
        self.assertEqual(action.deserializers, 'deserializers')
        self.assertEqual(action.isgenerator, True)
        self.assertEqual(action.argspec,
                         (['a', 'b', 'c', 'd', 'e', 'f'], 'args', 'kwargs',
                          (4, 5, 6)))
        self.assertEqual(action.argidx, 0)
        mock_Translators.assert_has_calls([
            mock.call(function, '_wsgi_serializers'),
            mock.call(function, '_wsgi_deserializers'),
        ])

    @mock.patch('appathy.types.Translators',
                side_effect=['serializers', 'deserializers'])
    def test_init_method(self, mock_Translators):
        class TestClass(object):
            def method(self, a, b, c, d=4, e=5, f=6, *args, **kwargs):
                pass

        test = TestClass()

        action = actions.ActionMethod(test.method)

        self.assertEqual(action.method, test.method)
        self.assertEqual(action.serializers, 'serializers')
        self.assertEqual(action.deserializers, 'deserializers')
        self.assertEqual(action.isgenerator, False)
        self.assertEqual(action.argspec,
                         (['self', 'a', 'b', 'c', 'd', 'e', 'f'], 'args',
                          'kwargs', (4, 5, 6)))
        self.assertEqual(action.argidx, 1)
        mock_Translators.assert_has_calls([
            mock.call(test.method, '_wsgi_serializers'),
            mock.call(test.method, '_wsgi_deserializers'),
        ])

    @mock.patch('appathy.types.Translators')
    def test_getattr(self, _mock_Translators):
        def function():
            pass

        function.test_attr = 'a test'

        action = actions.ActionMethod(function)

        self.assertEqual(action.test_attr, 'a test')
        with self.assertRaises(AttributeError):
            dummy = action.nonexistant

    @mock.patch('appathy.types.Translators')
    def test_call_function_nokwarg(self, _mock_Translators):
        check = dict(called=False)

        def function(a, b, c):
            self.assertEqual(a, 1)
            self.assertEqual(b, 2)
            self.assertEqual(c, 3)
            check['called'] = True

        action = actions.ActionMethod(function)

        # Verifying that this doesn't raise a TypeError, either...
        action(1, b=2, c=3, d=4, e=5, f=6)

        self.assertTrue(check['called'])

    @mock.patch('appathy.types.Translators')
    def test_call_function_withkwarg(self, _mock_Translators):
        check = dict(called=False)

        def function(a, b, c, **kwargs):
            self.assertEqual(a, 1)
            self.assertEqual(b, 2)
            self.assertEqual(c, 3)
            self.assertEqual(kwargs, dict(d=4, e=5, f=6))
            check['called'] = True

        action = actions.ActionMethod(function)

        # Verifying that this doesn't raise a TypeError, either...
        action(1, b=2, c=3, d=4, e=5, f=6)

        self.assertTrue(check['called'])

    @mock.patch('appathy.types.Translators')
    def test_call_method_nokwarg(self, _mock_Translators):
        check = dict(called=False)

        class Test(object):
            def method(inst, a, b, c):
                self.assertIsInstance(inst, Test)
                self.assertEqual(a, 1)
                self.assertEqual(b, 2)
                self.assertEqual(c, 3)
                check['called'] = True

        test = Test()

        action = actions.ActionMethod(test.method)

        # Verifying that this doesn't raise a TypeError, either...
        action(1, b=2, c=3, d=4, e=5, f=6)

        self.assertTrue(check['called'])

    @mock.patch('appathy.types.Translators')
    def test_call_function_withkwarg(self, _mock_Translators):
        check = dict(called=False)

        class Test(object):
            def method(inst, a, b, c, **kwargs):
                self.assertIsInstance(inst, Test)
                self.assertEqual(a, 1)
                self.assertEqual(b, 2)
                self.assertEqual(c, 3)
                self.assertEqual(kwargs, dict(d=4, e=5, f=6))
                check['called'] = True

        test = Test()

        action = actions.ActionMethod(test.method)

        # Verifying that this doesn't raise a TypeError, either...
        action(1, b=2, c=3, d=4, e=5, f=6)

        self.assertTrue(check['called'])


class ActionDescriptorTest(tests.TestCase):
    @mock.patch.object(actions, 'ActionMethod',
                       side_effect=['meth', 'ext1', 'ext2', 'ext3'])
    def test_init(self, mock_ActionMethod):
        desc = actions.ActionDescriptor('method', ['extension1', 'extension2',
                                                   'extension3'],
                                        'response_type')

        self.assertEqual(desc.method, 'meth')
        self.assertEqual(desc.extensions, ['ext1', 'ext2', 'ext3'])
        self.assertEqual(desc.resp_type, 'response_type')
        mock_ActionMethod.assert_has_calls([
            mock.call('method'),
            mock.call('extension1'),
            mock.call('extension2'),
            mock.call('extension3'),
        ])

    @mock.patch.object(actions, 'ActionMethod',
                       return_value=mock.Mock(return_value='response'))
    @mock.patch.object(actions.ActionDescriptor, 'wrap', return_value='resp')
    def test_call(self, mock_wrap, mock_ActionMethod):
        desc = actions.ActionDescriptor('method', [], 'resp_type')

        result = desc('req', dict(a=1, b=2, c=3))

        mock_ActionMethod.return_value.assert_called_once_with('req', a=1,
                                                               b=2, c=3)
        mock_wrap.assert_called_once_with('req', 'response')
        self.assertEqual(result, 'resp')

    @mock.patch.object(actions, 'ActionMethod')
    def test_deserialize_request_nobody(self, mock_ActionMethod,
                                        return_value=mock.Mock()):
        desc = actions.ActionDescriptor('method', [], 'resp_type')

        result = desc.deserialize_request(mock.Mock(content_length=0))

        self.assertEqual(result, None)
        self.assertFalse(mock_ActionMethod.return_value.deserializers.called)

    @mock.patch.object(actions, 'ActionMethod', return_value=mock.Mock(**{
        'deserializers.side_effect': KeyError,
    }))
    def test_deserialize_request_nodeserializer(self, mock_ActionMethod):
        request = mock.Mock(content_length=50, content_type='text/plain')

        desc = actions.ActionDescriptor('method', [], 'resp_type')

        with self.assertRaises(webob.exc.HTTPUnsupportedMediaType):
            result = desc.deserialize_request(request)

        mock_ActionMethod.return_value.deserializers.assert_called_once_with(
            'text/plain')

    @mock.patch.object(actions, 'ActionMethod')
    def test_deserialize_request_noattacher(self, mock_ActionMethod):
        deserializer = mock.Mock(spec=[], return_value='body')
        method = mock.Mock(**{'deserializers.return_value': deserializer})
        extensions = [mock.Mock(), mock.Mock()]
        mock_ActionMethod.side_effect = [method] + extensions
        request = mock.Mock(content_length=50,
                            content_type='text/plain',
                            body='this is the body')

        desc = actions.ActionDescriptor('method', ['ext1', 'ext2'], 'resp')

        result = desc.deserialize_request(request)

        self.assertFalse(hasattr(deserializer, 'attach'))
        method.deserializers.assert_called_once_with('text/plain')
        self.assertFalse(extensions[0].deserializers.called)
        self.assertFalse(extensions[1].deserializers.called)
        deserializer.assert_called_once_with('this is the body')
        self.assertEqual(result, 'body')

    @mock.patch.object(actions, 'ActionMethod')
    def test_deserialize_request_withattacher(self, mock_ActionMethod):
        deserializer = mock.Mock(return_value='body')
        method = mock.Mock(**{'deserializers.return_value': deserializer})
        extensions = [
            mock.Mock(**{'deserializers.return_value': 'extension1'}),
            mock.Mock(**{'deserializers.side_effect': KeyError}),
            mock.Mock(**{'deserializers.return_value': 'extension3'}),
        ]
        mock_ActionMethod.side_effect = [method] + extensions
        request = mock.Mock(content_length=50,
                            content_type='text/plain',
                            body='this is the body')

        desc = actions.ActionDescriptor('method', ['ext1', 'ext2', 'ext3'],
                                        'resp')

        result = desc.deserialize_request(request)

        method.deserializers.assert_called_once_with('text/plain')
        extensions[0].deserializers.assert_called_once_with('text/plain')
        extensions[1].deserializers.assert_called_once_with('text/plain')
        extensions[2].deserializers.assert_called_once_with('text/plain')
        deserializer.assert_has_calls([
            mock.call.attach('extension1'),
            mock.call.attach('extension3'),
            mock.call('this is the body'),
        ])
        self.assertEqual(result, 'body')

    @mock.patch.object(actions, 'ActionMethod')
    def test_serializer_nomatch(self, mock_ActionMethod):
        serializers = mock.Mock(**{
            'get_types.return_value': ['type1', 'type2'],
        })
        method = mock.Mock(serializers=serializers)
        mock_ActionMethod.side_effect = [method]
        request = mock.Mock(**{'accept.best_match.return_value': None})

        desc = actions.ActionDescriptor('method', [], 'resp_type')

        with self.assertRaises(webob.exc.HTTPNotAcceptable):
            dummy = desc.serializer(request)

        serializers.get_types.assert_called_once_with()
        request.accept.best_match.assert_called_once_with(['type1', 'type2'])
        self.assertFalse(serializers.called)

    @mock.patch.object(actions, 'ActionMethod')
    def test_serializer_noserializer(self, mock_ActionMethod):
        serializers = mock.Mock(**{
            'get_types.return_value': ['type1', 'type2'],
            'side_effect': KeyError,
        })
        method = mock.Mock(serializers=serializers)
        mock_ActionMethod.side_effect = [method]
        request = mock.Mock(**{'accept.best_match.return_value': 'text/plain'})

        desc = actions.ActionDescriptor('method', [], 'resp_type')

        with self.assertRaises(webob.exc.HTTPNotAcceptable):
            dummy = desc.serializer(request)

        serializers.get_types.assert_called_once_with()
        request.accept.best_match.assert_called_once_with(['type1', 'type2'])
        serializers.assert_called_once_with('text/plain')

    @mock.patch.object(actions, 'ActionMethod')
    def test_serializer_noattacher(self, mock_ActionMethod):
        serializer = mock.Mock(spec=[])
        serializers = mock.Mock(**{
            'get_types.return_value': ['type1', 'type2'],
            'return_value': serializer,
        })
        method = mock.Mock(serializers=serializers)
        extensions = [mock.Mock(), mock.Mock()]
        mock_ActionMethod.side_effect = [method] + extensions
        request = mock.Mock(**{'accept.best_match.return_value': 'text/plain'})

        desc = actions.ActionDescriptor('method', ['ext1', 'ext2'], 'resp')

        result = desc.serializer(request)

        serializers.get_types.assert_called_once_with()
        request.accept.best_match.assert_called_once_with(['type1', 'type2'])
        serializers.assert_called_once_with('text/plain')
        self.assertFalse(extensions[0].serializers.called)
        self.assertFalse(extensions[1].serializers.called)
        self.assertFalse(serializer.called)
        self.assertEqual(result[0], 'text/plain')
        self.assertEqual(id(result[1]), id(serializer))

    @mock.patch.object(actions, 'ActionMethod')
    def test_serializer_withattacher(self, mock_ActionMethod):
        serializer = mock.Mock()
        serializers = mock.Mock(**{
            'get_types.return_value': ['type1', 'type2'],
            'return_value': serializer,
        })
        method = mock.Mock(serializers=serializers)
        extensions = [
            mock.Mock(**{'serializers.return_value': 'extension1'}),
            mock.Mock(**{'serializers.side_effect': KeyError}),
            mock.Mock(**{'serializers.return_value': 'extension3'}),
        ]
        mock_ActionMethod.side_effect = [method] + extensions
        request = mock.Mock(**{'accept.best_match.return_value': 'text/plain'})

        desc = actions.ActionDescriptor('method', ['ext1', 'ext2', 'ext3'],
                                        'resp')

        result = desc.serializer(request)

        serializers.get_types.assert_called_once_with()
        request.accept.best_match.assert_called_once_with(['type1', 'type2'])
        serializers.assert_called_once_with('text/plain')
        extensions[0].serializers.assert_called_once_with('text/plain')
        extensions[1].serializers.assert_called_once_with('text/plain')
        extensions[2].serializers.assert_called_once_with('text/plain')
        serializer.assert_has_calls([
            mock.call.attach('extension3'),
            mock.call.attach('extension1'),
        ])
        self.assertFalse(serializer.called)
        self.assertEqual(result[0], 'text/plain')
        self.assertEqual(id(result[1]), id(serializer))

    @mock.patch.object(actions, 'ActionMethod')
    @mock.patch.object(actions.ActionDescriptor, 'wrap', return_value='resp')
    def test_pre_process_functions(self, mock_wrap, mock_ActionMethod):
        meth = mock.Mock()
        exts = [
            mock.Mock(isgenerator=False),
            mock.Mock(isgenerator=False),
            mock.Mock(isgenerator=False),
        ]
        mock_ActionMethod.side_effect = [meth] + exts

        desc = actions.ActionDescriptor('method', ['ext1', 'ext2', 'ext3'],
                                        'resp')

        result = desc.pre_process('req', 'params')

        self.assertEqual(result, (None, list(reversed(exts))))
        self.assertFalse(mock_wrap.called)

    @mock.patch.object(actions, 'ActionMethod')
    @mock.patch.object(actions.ActionDescriptor, 'wrap', return_value='resp')
    def test_pre_process_generators_noyield(self, mock_wrap,
                                            mock_ActionMethod):
        meth = mock.Mock()
        ext_gens = [
            mock.Mock(**{'next.return_value': None}),
            mock.Mock(**{'next.return_value': None}),
            mock.Mock(**{'next.return_value': None}),
        ]
        exts = [
            mock.Mock(isgenerator=True, return_value=ext_gens[0]),
            mock.Mock(isgenerator=True, return_value=ext_gens[1]),
            mock.Mock(isgenerator=True, return_value=ext_gens[2]),
        ]
        mock_ActionMethod.side_effect = [meth] + exts

        desc = actions.ActionDescriptor('method', ['ext1', 'ext2', 'ext3'],
                                        'resp')

        result = desc.pre_process('req', dict(a=1, b=2, c=3))

        exts[0].assert_called_once_with('req', a=1, b=2, c=3)
        exts[1].assert_called_once_with('req', a=1, b=2, c=3)
        exts[2].assert_called_once_with('req', a=1, b=2, c=3)
        ext_gens[0].next.assert_called_once_with()
        ext_gens[1].next.assert_called_once_with()
        ext_gens[2].next.assert_called_once_with()
        self.assertEqual(result, (None, list(reversed(ext_gens))))
        self.assertFalse(mock_wrap.called)

    @mock.patch.object(actions, 'ActionMethod')
    @mock.patch.object(actions.ActionDescriptor, 'wrap', return_value='resp')
    def test_pre_process_generators_noyield_stop(self, mock_wrap,
                                                 mock_ActionMethod):
        meth = mock.Mock()
        ext_gens = [
            mock.Mock(**{'next.side_effect': StopIteration}),
            mock.Mock(**{'next.return_value': None}),
            mock.Mock(**{'next.side_effect': StopIteration}),
        ]
        exts = [
            mock.Mock(isgenerator=True, return_value=ext_gens[0]),
            mock.Mock(isgenerator=True, return_value=ext_gens[1]),
            mock.Mock(isgenerator=True, return_value=ext_gens[2]),
        ]
        mock_ActionMethod.side_effect = [meth] + exts

        desc = actions.ActionDescriptor('method', ['ext1', 'ext2', 'ext3'],
                                        'resp')

        result = desc.pre_process('req', dict(a=1, b=2, c=3))

        exts[0].assert_called_once_with('req', a=1, b=2, c=3)
        exts[1].assert_called_once_with('req', a=1, b=2, c=3)
        exts[2].assert_called_once_with('req', a=1, b=2, c=3)
        ext_gens[0].next.assert_called_once_with()
        ext_gens[1].next.assert_called_once_with()
        ext_gens[2].next.assert_called_once_with()
        self.assertEqual(result, (None, [ext_gens[1]]))
        self.assertFalse(mock_wrap.called)

    @mock.patch.object(actions, 'ActionMethod')
    @mock.patch.object(actions.ActionDescriptor, 'wrap', return_value='resp')
    def test_pre_process_generators_yield(self, mock_wrap, mock_ActionMethod):
        meth = mock.Mock()
        ext_gens = [
            mock.Mock(**{'next.return_value': None}),
            mock.Mock(**{'next.return_value': 'generated'}),
            mock.Mock(**{'next.return_value': None}),
        ]
        exts = [
            mock.Mock(isgenerator=True, return_value=ext_gens[0]),
            mock.Mock(isgenerator=True, return_value=ext_gens[1]),
            mock.Mock(isgenerator=True, return_value=ext_gens[2]),
        ]
        mock_ActionMethod.side_effect = [meth] + exts

        desc = actions.ActionDescriptor('method', ['ext1', 'ext2', 'ext3'],
                                        'resp')

        result = desc.pre_process('req', dict(a=1, b=2, c=3))

        exts[0].assert_called_once_with('req', a=1, b=2, c=3)
        exts[1].assert_called_once_with('req', a=1, b=2, c=3)
        self.assertFalse(exts[2].called)
        ext_gens[0].next.assert_called_once_with()
        ext_gens[1].next.assert_called_once_with()
        self.assertFalse(ext_gens[2].next.called)
        self.assertEqual(result, ('resp', [ext_gens[0]]))
        mock_wrap.assert_called_once_with('req', 'generated')

    @mock.patch('inspect.isgenerator', return_value=False)
    @mock.patch.object(actions, 'ActionMethod')
    @mock.patch.object(actions.ActionDescriptor, 'wrap', return_value='resp')
    def test_post_process_functions_noreplace(self, mock_wrap,
                                              _mock_ActionMethod,
                                              _mock_is_generator):
        ext_list = [
            mock.Mock(return_value=None),
            mock.Mock(return_value=None),
            mock.Mock(return_value=None),
        ]

        desc = actions.ActionDescriptor('method', [], 'resp_type')

        result = desc.post_process(ext_list, 'req', 'in response',
                                   dict(a=1, b=2, c=3))

        ext_list[0].assert_called_once_with('req', 'in response',
                                            a=1, b=2, c=3)
        ext_list[1].assert_called_once_with('req', 'in response',
                                            a=1, b=2, c=3)
        ext_list[2].assert_called_once_with('req', 'in response',
                                            a=1, b=2, c=3)
        self.assertEqual(result, 'in response')
        self.assertFalse(mock_wrap.called)

    @mock.patch('inspect.isgenerator', return_value=False)
    @mock.patch.object(actions, 'ActionMethod')
    @mock.patch.object(actions.ActionDescriptor, 'wrap', return_value='resp')
    def test_post_process_functions_withreplace(self, mock_wrap,
                                                _mock_ActionMethod,
                                                _mock_is_generator):
        ext_list = [
            mock.Mock(return_value=None),
            mock.Mock(return_value='replacement'),
            mock.Mock(return_value=None),
        ]

        desc = actions.ActionDescriptor('method', [], 'resp_type')

        result = desc.post_process(ext_list, 'req', 'in response',
                                   dict(a=1, b=2, c=3))

        ext_list[0].assert_called_once_with('req', 'in response',
                                            a=1, b=2, c=3)
        ext_list[1].assert_called_once_with('req', 'in response',
                                            a=1, b=2, c=3)
        ext_list[2].assert_called_once_with('req', 'resp',
                                            a=1, b=2, c=3)
        self.assertEqual(result, 'resp')
        mock_wrap.assert_called_once_with('req', 'replacement')

    @mock.patch('inspect.isgenerator', return_value=True)
    @mock.patch.object(actions, 'ActionMethod')
    @mock.patch.object(actions.ActionDescriptor, 'wrap', return_value='resp')
    def test_post_process_generators_noreplace(self, mock_wrap,
                                               _mock_ActionMethod,
                                               _mock_is_generator):
        ext_list = [
            mock.Mock(**{'send.return_value': None}),
            mock.Mock(**{'send.side_effect': StopIteration}),
            mock.Mock(**{'send.return_value': None}),
        ]

        desc = actions.ActionDescriptor('method', [], 'resp_type')

        result = desc.post_process(ext_list, 'req', 'in response',
                                   dict(a=1, b=2, c=3))

        ext_list[0].send.assert_called_once_with('in response')
        ext_list[1].send.assert_called_once_with('in response')
        ext_list[2].send.assert_called_once_with('in response')
        self.assertEqual(result, 'in response')
        self.assertFalse(mock_wrap.called)

    @mock.patch('inspect.isgenerator', return_value=True)
    @mock.patch.object(actions, 'ActionMethod')
    @mock.patch.object(actions.ActionDescriptor, 'wrap', return_value='resp')
    def test_post_process_generators_withreplace(self, mock_wrap,
                                                 _mock_ActionMethod,
                                                 _mock_is_generator):
        ext_list = [
            mock.Mock(**{'send.return_value': None}),
            mock.Mock(**{'send.return_value': 'replacement'}),
            mock.Mock(**{'send.return_value': None}),
        ]

        desc = actions.ActionDescriptor('method', [], 'resp_type')

        result = desc.post_process(ext_list, 'req', 'in response',
                                   dict(a=1, b=2, c=3))

        ext_list[0].send.assert_called_once_with('in response')
        ext_list[1].send.assert_called_once_with('in response')
        ext_list[2].send.assert_called_once_with('resp')
        self.assertEqual(result, 'resp')
        mock_wrap.assert_called_once_with('req', 'replacement')

    @mock.patch.object(actions, 'ActionMethod')
    def test_wrap_httpexception(self, _mock_ActionMethod):
        response = webob.exc.HTTPNotFound()

        desc = actions.ActionDescriptor('method', [], 'resp_type')

        with self.assertRaises(webob.exc.HTTPException) as ctx:
            result = desc.wrap('req', response)

        self.assertEqual(id(ctx.exception), id(response))

    @mock.patch.object(actions, 'ActionMethod')
    def test_wrap_webob(self, _mock_ActionMethod):
        response = webob.Response()

        desc = actions.ActionDescriptor('method', [], 'resp_type')

        with self.assertRaises(exceptions.AppathyResponse) as ctx:
            result = desc.wrap('req', response)

        self.assertEqual(id(ctx.exception.response), id(response))

    @mock.patch.object(actions, 'ActionMethod')
    def test_wrap_responseobject(self, _mock_ActionMethod):
        resp = mock.Mock(spec=response.ResponseObject)

        desc = actions.ActionDescriptor('method', [], 'resp_type')

        result = desc.wrap('req', resp)

        self.assertEqual(id(result), id(resp))
        resp._bind.assert_called_once_with(desc)

    @mock.patch.object(actions, 'ActionMethod')
    def test_wrap_other(self, _mock_ActionMethod):
        resp_type = mock.Mock(return_value='wrapped')

        desc = actions.ActionDescriptor('method', [], resp_type)

        result = desc.wrap('req', 'response')

        self.assertEqual(result, 'wrapped')
        resp_type.assert_called_once_with('req', 'response', _descriptor=desc)

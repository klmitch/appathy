from appathy import exceptions
from appathy import response

import tests


class TestMethod(object):
    def __init__(self, code=None):
        if code:
            self._wsgi_code = code


class TestDescriptor(object):
    def __init__(self, content_type, code=None):
        self.method = TestMethod(code)
        self.content_type = content_type

    def serializer(self, request):
        # Return the request so it's easy to see
        return self.content_type, request


class TestResponse(object):
    def __init__(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)


class ResponseObject(tests.TestCase):
    def test_empty_init(self):
        robj = response.ResponseObject('request')

        self.assertEqual(robj.req, 'request')
        self.assertEqual(robj.result, None)
        self.assertEqual(robj._code, None)
        self.assertEqual(robj._headers, {})
        self.assertEqual(robj._defcode, None)
        self.assertEqual(robj.content_type, None)
        self.assertEqual(robj.type_name, None)
        self.assertEqual(robj.serializer, None)
        self.assertEqual(robj.code, 200)
        self.assertEqual(robj.headers, robj._headers)
        self.assertNotEqual(id(robj.headers), id(robj._headers))

    def test_result_init(self):
        robj = response.ResponseObject('request', result='result')

        self.assertEqual(robj.req, 'request')
        self.assertEqual(robj.result, 'result')
        self.assertEqual(robj._code, None)
        self.assertEqual(robj._headers, {})
        self.assertEqual(robj._defcode, None)
        self.assertEqual(robj.content_type, None)
        self.assertEqual(robj.type_name, None)
        self.assertEqual(robj.serializer, None)
        self.assertEqual(robj.code, 200)
        self.assertEqual(robj.headers, robj._headers)
        self.assertNotEqual(id(robj.headers), id(robj._headers))

    def test_code_init(self):
        robj = response.ResponseObject('request', code=204)

        self.assertEqual(robj.req, 'request')
        self.assertEqual(robj.result, None)
        self.assertEqual(robj._code, 204)
        self.assertEqual(robj._headers, {})
        self.assertEqual(robj._defcode, None)
        self.assertEqual(robj.content_type, None)
        self.assertEqual(robj.type_name, None)
        self.assertEqual(robj.serializer, None)
        self.assertEqual(robj.code, 204)
        self.assertEqual(robj.headers, robj._headers)
        self.assertNotEqual(id(robj.headers), id(robj._headers))

    def test_headers_init(self):
        robj = response.ResponseObject('request', headers={
                'X-Header-1': 'value1',
                'X-Header-2': 'value2',
                })

        self.assertEqual(robj.req, 'request')
        self.assertEqual(robj.result, None)
        self.assertEqual(robj._code, None)
        self.assertEqual(robj._headers, {
                'x-header-1': 'value1',
                'x-header-2': 'value2',
                })
        self.assertEqual(robj._defcode, None)
        self.assertEqual(robj.content_type, None)
        self.assertEqual(robj.type_name, None)
        self.assertEqual(robj.serializer, None)
        self.assertEqual(robj.code, 200)
        self.assertEqual(robj.headers, robj._headers)
        self.assertNotEqual(id(robj.headers), id(robj._headers))

    def test_descriptor_init(self):
        def fake_bind(robj, **kwargs):
            self.assertEqual(kwargs, dict(_descriptor='descriptor'))

        self.stubs.Set(response.ResponseObject, '_bind', fake_bind)

        robj = response.ResponseObject('request', _descriptor='descriptor')

        self.assertEqual(robj.req, 'request')
        self.assertEqual(robj.result, None)
        self.assertEqual(robj._code, None)
        self.assertEqual(robj._headers, {})
        self.assertEqual(robj._defcode, None)
        self.assertEqual(robj.content_type, None)
        self.assertEqual(robj.type_name, None)
        self.assertEqual(robj.serializer, None)
        self.assertEqual(robj.code, 200)
        self.assertEqual(robj.headers, robj._headers)
        self.assertNotEqual(id(robj.headers), id(robj._headers))

    def test_getitem(self):
        robj = response.ResponseObject('request', headers={
                'X-Header-1': 'value1',
                'x-header-2': 'value2',
                })

        self.assertEqual(robj['x-header-1'], 'value1')
        self.assertEqual(robj['X-Header-2'], 'value2')
        with self.assertRaises(KeyError):
            _dummy = robj['x-header-3']

    def test_setitem(self):
        robj = response.ResponseObject('request')

        robj['X-Header-1'] = 'value1'
        robj['x-header-2'] = 'value2'

        self.assertEqual(robj._headers, {
                'x-header-1': 'value1',
                'x-header-2': 'value2',
                })

    def test_delitem(self):
        robj = response.ResponseObject('request', headers={
                'X-Header-1': 'value1',
                'x-header-2': 'value2',
                })

        del robj['x-header-1']
        del robj['X-Header-2']

        self.assertEqual(robj._headers, {})

    def test_contains(self):
        robj = response.ResponseObject('request', headers={
                'X-Header-1': 'value1',
                'x-header-2': 'value2',
                })

        self.assertTrue('x-header-1' in robj)
        self.assertTrue('X-Header-2' in robj)
        self.assertFalse('x-header-3' in robj)

    def test_len(self):
        robj = response.ResponseObject('request', headers={
                'X-Header-1': 'value1',
                'x-header-2': 'value2',
                })

        self.assertEqual(len(robj), 2)

    def test_iter(self):
        robj = response.ResponseObject('request', headers={
                'X-Header-1': 'value1',
                'x-header-2': 'value2',
                })

        self.assertEqual(set(iter(robj)), set(['x-header-1', 'x-header-2']))

    def test_iteritems(self):
        robj = response.ResponseObject('request', headers={
                'X-Header-1': 'value1',
                'x-header-2': 'value2',
                })

        self.assertEqual(set(robj.iteritems()), set([
                    ('x-header-1', 'value1'),
                    ('x-header-2', 'value2'),
                    ]))

    def test_keys(self):
        robj = response.ResponseObject('request', headers={
                'X-Header-1': 'value1',
                'x-header-2': 'value2',
                })

        self.assertEqual(set(robj.keys()), set(['x-header-1', 'x-header-2']))

    def test_bind_nocode(self):
        desc = TestDescriptor('text/xml')
        robj = response.ResponseObject('request')
        robj._bind(desc)

        self.assertEqual(robj._defcode, 200)
        self.assertEqual(robj.code, 200)
        self.assertEqual(robj.content_type, 'text/xml')
        self.assertEqual(robj.serializer, 'request')

    def test_bind_withcode(self):
        desc = TestDescriptor('text/xml', 204)
        robj = response.ResponseObject('request')
        robj._bind(desc)

        self.assertEqual(robj._defcode, 204)
        self.assertEqual(robj.code, 204)
        self.assertEqual(robj.content_type, 'text/xml')
        self.assertEqual(robj.serializer, 'request')

    def test_bind_withcode_override(self):
        desc = TestDescriptor('text/xml', 204)
        robj = response.ResponseObject('request', code=202)
        robj._bind(desc)

        self.assertEqual(robj._defcode, 204)
        self.assertEqual(robj._code, 202)
        self.assertEqual(robj.code, 202)
        self.assertEqual(robj.content_type, 'text/xml')
        self.assertEqual(robj.serializer, 'request')

    def test_serialize_unbound(self):
        robj = response.ResponseObject('request')
        with self.assertRaises(exceptions.UnboundResponse):
            resp = robj._serialize()

    def test_serialize_bound(self):
        desc = TestDescriptor('text/xml')
        robj = response.ResponseObject('request', _descriptor=desc)
        robj.response_class = TestResponse
        resp = robj._serialize()

        self.assertIsInstance(resp, TestResponse)
        self.assertEqual(resp.request, 'request')
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.headerlist, [])
        self.assertFalse(hasattr(resp, 'content_type'))
        self.assertFalse(hasattr(resp, 'body'))

    def test_serialize_methcode(self):
        desc = TestDescriptor('text/xml', 204)
        robj = response.ResponseObject('request', _descriptor=desc)
        robj.response_class = TestResponse
        resp = robj._serialize()

        self.assertIsInstance(resp, TestResponse)
        self.assertEqual(resp.request, 'request')
        self.assertEqual(resp.status, 204)
        self.assertEqual(resp.headerlist, [])
        self.assertFalse(hasattr(resp, 'content_type'))
        self.assertFalse(hasattr(resp, 'body'))

    def test_serialize_withcode(self):
        desc = TestDescriptor('text/xml', 204)
        robj = response.ResponseObject('request', code=202, _descriptor=desc)
        robj.response_class = TestResponse
        resp = robj._serialize()

        self.assertIsInstance(resp, TestResponse)
        self.assertEqual(resp.request, 'request')
        self.assertEqual(resp.status, 202)
        self.assertEqual(resp.headerlist, [])
        self.assertFalse(hasattr(resp, 'content_type'))
        self.assertFalse(hasattr(resp, 'body'))

    def test_serialize_withheaders(self):
        desc = TestDescriptor('text/xml')
        robj = response.ResponseObject('request', _descriptor=desc, headers={
                'X-Header-1': 'value1',
                'x-header-2': 'value2',
                })
        robj.response_class = TestResponse
        resp = robj._serialize()

        self.assertIsInstance(resp, TestResponse)
        self.assertEqual(resp.request, 'request')
        self.assertEqual(resp.status, 200)
        self.assertEqual(set(resp.headerlist), set([
                ('x-header-1', 'value1'),
                ('x-header-2', 'value2'),
                ]))
        self.assertFalse(hasattr(resp, 'content_type'))
        self.assertFalse(hasattr(resp, 'body'))

    def test_serialize_withbody(self):
        def serializer(body):
            return 'serialized(%s)' % body

        desc = TestDescriptor('text/xml')
        robj = response.ResponseObject('request', result='result',
                                       _descriptor=desc)
        robj.response_class = TestResponse
        robj.serializer = serializer
        resp = robj._serialize()

        self.assertIsInstance(resp, TestResponse)
        self.assertEqual(resp.request, 'request')
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.headerlist, [])
        self.assertEqual(resp.content_type, 'text/xml')
        self.assertEqual(resp.body, 'serialized(result)')

    def test_code_set(self):
        desc = TestDescriptor('text/xml', 204)
        robj = response.ResponseObject('request', _descriptor=desc)
        robj.code = 202

        self.assertEqual(robj._defcode, 204)
        self.assertEqual(robj._code, 202)
        self.assertEqual(robj.code, 202)

    def test_code_del(self):
        desc = TestDescriptor('text/xml', 204)
        robj = response.ResponseObject('request', code=202, _descriptor=desc)
        del robj.code

        self.assertEqual(robj._defcode, 204)
        self.assertEqual(robj._code, None)
        self.assertEqual(robj.code, 204)

    def test_code_del_unset(self):
        desc = TestDescriptor('text/xml', 204)
        robj = response.ResponseObject('request', _descriptor=desc)
        del robj.code

        self.assertEqual(robj._defcode, 204)
        self.assertEqual(robj._code, None)
        self.assertEqual(robj.code, 204)

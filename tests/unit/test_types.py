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

import mock

from appathy import types

import tests


class RegisterTypes(tests.TestCase):
    @mock.patch.object(types, 'media_types', {})
    @mock.patch.object(types, 'type_names', {})
    def test_register_types(self):
        types.register_types("foo", "foo/bar", "application/x-foo-bar")

        self.assertEqual(types.media_types, {
            "foo/bar": "foo",
            "application/x-foo-bar": "foo",
        })
        self.assertEqual(types.type_names, dict(
            foo=set(["foo/bar", "application/x-foo-bar"]),
        ))

    @mock.patch.object(types, 'media_types', {})
    @mock.patch.object(types, 'type_names', {})
    def test_register_duplicates(self):
        types.register_types("foo", "foo/bar", "application/x-foo-bar")
        types.register_types("bar", "foo/bar")

        self.assertEqual(types.media_types, {
            "foo/bar": "bar",
            "application/x-foo-bar": "foo",
        })
        self.assertEqual(types.type_names, dict(
            foo=set(["application/x-foo-bar"]),
            bar=set(["foo/bar"]),
        ))


class TranslatorsDecorator(tests.TestCase):
    def test__translators_methods(self):
        @types._translators('_translators', dict(xml="xml"))
        @types._translators('_translators', dict(json="json"))
        def foobar():
            pass

        self.assertTrue(hasattr(foobar, '_translators'))
        self.assertEqual(foobar._translators, dict(xml="xml", json="json"))

    def test_serializers_methods(self):
        @types.serializers(xml="xml")
        @types.serializers(json="json")
        def foobar():
            pass

        self.assertTrue(hasattr(foobar, '_wsgi_serializers'))
        self.assertEqual(foobar._wsgi_serializers,
                         dict(xml="xml", json="json"))

    def test_deserializers_methods(self):
        @types.deserializers(xml="xml")
        @types.deserializers(json="json")
        def foobar():
            pass

        self.assertTrue(hasattr(foobar, '_wsgi_deserializers'))
        self.assertEqual(foobar._wsgi_deserializers,
                         dict(xml="xml", json="json"))

    def test__translators_classes(self):
        @types._translators('_translators', dict(xml="xml"))
        @types._translators('_translators', dict(json="json"))
        class Foobar(object):
            pass

        self.assertTrue(hasattr(Foobar, '_translators'))
        self.assertEqual(Foobar._translators, dict(xml="xml", json="json"))

    def test_serializers_classes(self):
        @types.serializers(xml="xml")
        @types.serializers(json="json")
        class Foobar(object):
            pass

        self.assertTrue(hasattr(Foobar, '_wsgi_serializers'))
        self.assertEqual(Foobar._wsgi_serializers,
                         dict(xml="xml", json="json"))

    def test_deserializers_classes(self):
        @types.deserializers(xml="xml")
        @types.deserializers(json="json")
        class Foobar(object):
            pass

        self.assertTrue(hasattr(Foobar, '_wsgi_deserializers'))
        self.assertEqual(Foobar._wsgi_deserializers,
                         dict(xml="xml", json="json"))


@mock.patch.object(types, 'media_types', {
    'text/xml': 'xml',
    'application/x-test-xml': 'xml',
    'text/json': 'json',
    'application/x-test-json': 'json',
})
@mock.patch.object(types, 'type_names', dict(
    xml=set(['text/xml', 'application/x-test-xml']),
    json=set(['text/json', 'application/x-test-json']),
))
class TranslatorsClass(tests.TestCase):
    def test_init_method_only(self):
        class TestClass(object):
            @types._translators('_translators', dict(xml="xlator"))
            def foobar(self):
                pass

        obj = TestClass()
        xlator = types.Translators(obj.foobar, '_translators')

        self.assertEqual(xlator.translators, dict(xml="xlator"))

    def test_init_class_only(self):
        @types._translators('_translators', dict(xml="xlator"))
        class TestClass(object):
            def foobar(self):
                pass

        obj = TestClass()
        xlator = types.Translators(obj.foobar, '_translators')

        self.assertEqual(xlator.translators, dict(xml="xlator"))

    def test_init_method_override(self):
        @types._translators('_translators', dict(xml="xlator"))
        class TestClass(object):
            @types._translators('_translators', dict(xml="override"))
            def foobar(self):
                pass

        obj = TestClass()
        xlator = types.Translators(obj.foobar, '_translators')

        self.assertEqual(xlator.translators, dict(xml="override"))

    def test_init_no_xlators(self):
        class TestClass(object):
            def foobar(self):
                pass

        obj = TestClass()
        xlator = types.Translators(obj.foobar, '_translators')

        self.assertEqual(xlator.translators, {})

    def test_get_types_no_xlators(self):
        class TestClass(object):
            def foobar(self):
                pass

        obj = TestClass()
        xlator = types.Translators(obj.foobar, '_translators')
        avail_types = xlator.get_types()

        self.assertEqual(avail_types, set())

    def test_get_types_one(self):
        class TestClass(object):
            @types._translators('_translators', dict(xml='xml'))
            def foobar(self):
                pass

        obj = TestClass()
        xlator = types.Translators(obj.foobar, '_translators')
        avail_types = xlator.get_types()

        self.assertEqual(avail_types,
                         set(['text/xml', 'application/x-test-xml']))

    def test_get_types_multiple(self):
        class TestClass(object):
            @types._translators('_translators',
                                dict(xml='xml', json='json'))
            def foobar(self):
                pass

        obj = TestClass()
        xlator = types.Translators(obj.foobar, '_translators')
        avail_types = xlator.get_types()

        self.assertEqual(avail_types,
                         set(['text/xml', 'application/x-test-xml',
                              'text/json', 'application/x-test-json']))

    def test_call_class(self):
        class Xlator(object):
            def __init__(self, type_name, content_type):
                self.type_name = type_name
                self.content_type = content_type

        class TestClass(object):
            @types._translators('_translators', dict(xml=Xlator))
            def foobar(self):
                pass

        obj = TestClass()
        xlator = types.Translators(obj.foobar, '_translators')
        converter = xlator('text/xml')

        self.assertIsInstance(converter, Xlator)
        self.assertEqual(converter.type_name, 'xml')
        self.assertEqual(converter.content_type, 'text/xml')

    def test_call_function(self):
        def translator(type_name, content_type, body):
            return body

        class TestClass(object):
            @types._translators('_translators', dict(xml=translator))
            def foobar(self):
                pass

        obj = TestClass()
        xlator = types.Translators(obj.foobar, '_translators')
        converter = xlator('text/xml')

        self.assertIsInstance(converter, functools.partial)
        self.assertEqual(converter.func, translator)
        self.assertEqual(converter.args, ('xml', 'text/xml'))
        self.assertEqual(converter.keywords, None)

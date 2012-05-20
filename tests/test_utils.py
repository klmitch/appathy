import pkg_resources

from appathy import utils

import tests


class NormPath(tests.TestCase):
    def test_leading(self):
        result = utils.norm_path('foobar')

        self.assertEqual(result, '/foobar')

    def test_collapse(self):
        result = utils.norm_path('///foo/////bar')

        self.assertEqual(result, '/foo/bar')

    def test_trailing_allowed(self):
        result = utils.norm_path('/foo/')

        self.assertEqual(result, '/foo/')

    def test_trailing_prohibited(self):
        result = utils.norm_path('/foo/', False)

        self.assertEqual(result, '/foo')


class ImportCall(tests.TestCase):
    def setUp(self):
        super(ImportCall, self).setUp()

        class FakeEP(object):
            # Using "inst" to avoid shadowing "self"
            def load(inst, require=True, env=None, installer=None):
                self.assertEqual(require, False)
                return "fake_obj"

            @classmethod
            def parse(cls, src, dist=None):
                self.assertEqual(src, 'x=foobar:Foobar')
                return cls()

        self.stubs.Set(pkg_resources, 'EntryPoint', FakeEP)

    def test_import_call(self):
        result = utils.import_call('foobar:Foobar')

        self.assertEqual(result, 'fake_obj')


class ImportEgg(tests.TestCase):
    def setUp(self):
        super(ImportEgg, self).setUp()

        def fake_load_entry_point(dist, group, name):
            self.assertEqual(dist, 'Foo')
            self.assertEqual(group, 'appathy.controller')
            self.assertEqual(name, 'bar')
            return "fake_obj"

        self.stubs.Set(pkg_resources, 'load_entry_point',
                       fake_load_entry_point)

    def test_import_egg(self):
        result = utils.import_egg('Foo#bar')

        self.assertEqual(result, 'fake_obj')


class ImportController(tests.TestCase):
    def setUp(self):
        super(ImportController, self).setUp()

        self.entry_points = None
        self.continued = False

        def fake_iter_entry_points(group, name):
            self.assertEqual(group, 'appathy.loader')
            self.assertEqual(name, 'foo')

            yield self.entry_points

            self.continued = True

        self.stubs.Set(pkg_resources, 'iter_entry_points',
                       fake_iter_entry_points)

    def test_import_error(self):
        class EPImportError(object):
            def load(self):
                raise ImportError

        self.entry_points = EPImportError()

        with self.assertRaisesRegexp(
            ImportError, "Unable to find loader for scheme 'foo'"):
            utils.import_controller('foo:bar')

        self.assertEqual(self.continued, True)

    def test_unknown_extra(self):
        class EPUnknownExtra(object):
            def load(self):
                raise pkg_resources.UnknownExtra

        self.entry_points = EPUnknownExtra()

        with self.assertRaisesRegexp(
            ImportError, "Unable to find loader for scheme 'foo'"):
            utils.import_controller('foo:bar')

        self.assertEqual(self.continued, True)

    def test_loader(self):
        def loader(controller):
            self.assertEqual(controller, 'bar')
            return "fake_obj"

        class EPLoader(object):
            def load(self):
                return loader

        self.entry_points = EPLoader()

        result = utils.import_controller('foo:bar')

        self.assertEqual(result, "fake_obj")
        self.assertEqual(self.continued, False)

    def test_bad_controller(self):
        with self.assertRaisesRegexp(
            ImportError, "No loader scheme specified by 'foobar'"):
            utils.import_controller('foobar')

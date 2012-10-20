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
    @mock.patch('pkg_resources.EntryPoint', **{
        'parse.return_value': mock.Mock(**{
            'load.return_value': 'fake_obj',
        }),
    })
    def test_import_call(self, mock_EntryPoint):
        result = utils.import_call('foobar:Foobar')

        self.assertEqual(result, 'fake_obj')
        mock_EntryPoint.parse.assert_called_once_with('x=foobar:Foobar')
        mock_EntryPoint.parse.return_value.load.assert_called_once_with(False)


class ImportEgg(tests.TestCase):
    @mock.patch('pkg_resources.load_entry_point', return_value='fake_obj')
    def test_import_egg(self, mock_load_entry_point):
        result = utils.import_egg('Foo#bar')

        self.assertEqual(result, 'fake_obj')
        mock_load_entry_point.assert_called_once_with('Foo',
                                                      'appathy.controller',
                                                      'bar')


class ImportController(tests.TestCase):
    @mock.patch('pkg_resources.iter_entry_points',
                return_value=[
                    mock.Mock(**{'load.side_effect': ImportError}),
                    mock.Mock(**{'load.side_effect': ImportError}),
                ])
    def test_import_error(self, mock_iter_entry_points):
        with self.assertRaisesRegexp(
                ImportError, "Unable to find loader for scheme 'foo'"):
            utils.import_controller('foo:bar')

        mock_iter_entry_points.assert_called_once_with('appathy.loader', 'foo')
        mock_iter_entry_points.return_value[0].load.assert_called_once_with()
        mock_iter_entry_points.return_value[1].load.assert_called_once_with()

    @mock.patch('pkg_resources.iter_entry_points',
                return_value=[
                    mock.Mock(**{
                        'load.side_effect': pkg_resources.UnknownExtra,
                    }),
                    mock.Mock(**{
                        'load.side_effect': pkg_resources.UnknownExtra,
                    }),
                ])
    def test_unknown_extra(self, mock_iter_entry_points):
        with self.assertRaisesRegexp(
                ImportError, "Unable to find loader for scheme 'foo'"):
            utils.import_controller('foo:bar')

        mock_iter_entry_points.assert_called_once_with('appathy.loader', 'foo')
        mock_iter_entry_points.return_value[0].load.assert_called_once_with()
        mock_iter_entry_points.return_value[1].load.assert_called_once_with()

    @mock.patch('pkg_resources.iter_entry_points',
                return_value=[
                    mock.Mock(**{'load.side_effect': tests.TestException}),
                    mock.Mock(**{'load.side_effect': tests.TestException}),
                ])
    def test_other_exception(self, mock_iter_entry_points):
        with self.assertRaises(tests.TestException):
            utils.import_controller('foo:bar')

        mock_iter_entry_points.assert_called_once_with('appathy.loader', 'foo')
        mock_iter_entry_points.return_value[0].load.assert_called_once_with()
        self.assertFalse(mock_iter_entry_points.return_value[1].load.called)

    @mock.patch('pkg_resources.iter_entry_points',
                return_value=[mock.Mock(**{
                    'load.return_value': mock.Mock(return_value='fake_obj'),
                })])
    def test_loader(self, mock_iter_entry_points):
        result = utils.import_controller('foo:bar')

        self.assertEqual(result, "fake_obj")
        mock_iter_entry_points.assert_called_once_with('appathy.loader', 'foo')
        mock_iter_entry_points.return_value[0].load.assert_called_once_with()
        mock_iter_entry_points.return_value[0].load.return_value\
            .assert_called_once_with('bar')

    @mock.patch('pkg_resources.iter_entry_points', side_effect=Exception)
    def test_bad_controller(self, mock_iter_entry_points):
        with self.assertRaisesRegexp(
                ImportError, "No loader scheme specified by 'foobar'"):
            utils.import_controller('foobar')

        self.assertFalse(mock_iter_entry_points.called)

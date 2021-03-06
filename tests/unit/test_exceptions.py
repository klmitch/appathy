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

from appathy import exceptions

import tests


class TestException(exceptions.AppathyException):
    """this is a test"""


class TestExceptionBaseArgs(exceptions.AppathyException):
    """this is a test: %(foo)s"""
    base_args = ['foo']


class AppathyExceptionTest(tests.TestCase):
    def test_no_args(self):
        exc = TestException()
        self.assertEqual(str(exc), "this is a test")
        with self.assertRaises(KeyError):
            exc = TestExceptionBaseArgs()

    def test_with_args(self):
        exc = TestException("testing")
        self.assertEqual(str(exc), "testing")

        exc = TestExceptionBaseArgs("testing")
        self.assertEqual(str(exc), "this is a test: testing")

    def test_with_kwargs(self):
        exc = TestException(foo="testing")
        self.assertEqual(str(exc), "this is a test")

        exc = TestExceptionBaseArgs(foo="testing")
        self.assertEqual(str(exc), "this is a test: testing")


class AppathyResponseTest(tests.TestCase):
    def test_init(self):
        exc = exceptions.AppathyResponse('response')

        self.assertEqual(exc.response, 'response')

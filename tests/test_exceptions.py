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

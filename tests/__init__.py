import logging
import unittest

import stubout


LOG = logging.getLogger('appathy')


class TestLogHandler(logging.Handler, object):
    def __init__(self):
        super(TestLogHandler, self).__init__(logging.DEBUG)

        self.messages = []

    def emit(self, record):
        try:
            self.messages.append(self.format(record))
        except Exception:
            pass

    def get_messages(self, clear=False):
        # Get the list of messages and clear it
        messages = self.messages
        if clear:
            self.messages = []
        return messages


# Set up basic logging for tests
test_handler = TestLogHandler()
LOG.addHandler(test_handler)
LOG.setLevel(logging.DEBUG)
LOG.propagate = False


class TestCase(unittest.TestCase):
    def setUp(self):
        self.stubs = stubout.StubOutForTesting()

        # Clear the log messages
        test_handler.get_messages(True)

    def tearDown(self):
        self.stubs.UnsetAll()

        # Clear the log messages
        test_handler.get_messages(True)

    @property
    def log_messages(self):
        # Retrieve and clear test log messages
        return test_handler.get_messages()

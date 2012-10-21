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

import logging

import unittest2


LOG = logging.getLogger('appathy')


class TestException(Exception):
    pass


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


class TestCase(unittest2.TestCase):
    def setUp(self):
        # Clear the log messages
        test_handler.get_messages(True)

    def tearDown(self):
        # Clear the log messages
        test_handler.get_messages(True)

    def dict_select(self, full_dict, exemplar):
        return dict((k, full_dict[k]) for k in exemplar)

    @property
    def log_messages(self):
        # Retrieve and clear test log messages
        return test_handler.get_messages()

# -*- coding: utf-8 -*-
#
import types
import unittest

from couchdb.server import state
from couchdb.server.mock import MockQueryServer


class StateTestCase(unittest.TestCase):

    def setUp(self):
        self.server = MockQueryServer()

    def test_add_lib(self):
        """should cache view lib to module attribute"""
        server = self.server
        self.assertEqual(server.state['view_lib'], None)
        self.assertTrue(state.add_lib(server, {'foo': 'bar'}))
        self.assertEqual(server.state['view_lib'], {'foo': 'bar'})


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StateTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

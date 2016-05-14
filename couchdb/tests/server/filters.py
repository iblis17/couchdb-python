# -*- coding: utf-8 -*-
#
import unittest

from couchdb.server import filters
from couchdb.server import state
from couchdb.server.mock import MockQueryServer


class FiltersTestCase(unittest.TestCase):

    def setUp(self):
        self.server = MockQueryServer()

    def test_filter(self):
        """should filter documents, returning True for good and False for bad"""
        state.add_fun(
            self.server,
            'def filterfun(doc, req, userctx):\n'
            '  return doc["good"]'
        )
        res = filters.filter(
            self.server,
            [{'foo': 'bar', 'good': True}, {'bar': 'baz', 'good': False}],
            {}, {}
        )
        self.assertEqual(res, [True, [True, False]])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FiltersTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

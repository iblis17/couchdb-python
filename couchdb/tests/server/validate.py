# -*- coding: utf-8 -*-
#
import unittest

from textwrap import dedent
from inspect import getsource

from couchdb.server import compiler
from couchdb.server import exceptions
from couchdb.server import validate
from couchdb.server.mock import MockQueryServer


class ValidateTestCase(unittest.TestCase):

    def setUp(self):
        def validatefun(newdoc, olddoc, userctx):
            if newdoc.get('try_assert'):
                assert newdoc['is_good']
            if newdoc.get('is_good'):
                return True
            else:
                raise Forbidden('bad doc')

        self.funsrc = dedent(getsource(validatefun))
        self.server = MockQueryServer()

    def test_validate(self):
        """should return 1 (int) on successful validation"""
        result = validate.validate(
            self.server, self.funsrc, {'is_good': True}, {}, {})
        self.assertEqual(result, 1)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ValidateTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

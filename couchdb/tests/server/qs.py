# -*- coding: utf-8 -*-
#
import unittest

from functools import partial

from couchdb import json
from couchdb.server import BaseQueryServer, SimpleQueryServer
from couchdb.server import exceptions
from couchdb.util import StringIO


class BaseQueryServerTestCase(unittest.TestCase):

    def test_set_version(self):
        server = BaseQueryServer((1, 2, 3))
        self.assertEqual(server.version, (1, 2, 3))

    def test_set_latest_version_by_default(self):
        server = BaseQueryServer()
        self.assertEqual(server.version, (999, 999, 999))

    def test_set_config_option(self):
        server = BaseQueryServer(foo='bar')
        self.assertTrue('foo' in server.config)
        self.assertEqual(server.config['foo'], 'bar')

    def test_config_option_handler(self):
        class CustomServer(BaseQueryServer):
            def config_foo(self, value):
                self.config['baz'] = value
        server = CustomServer(foo='bar')
        self.assertTrue('foo' not in server.config)
        self.assertTrue('baz' in server.config)
        self.assertEqual(server.config['baz'], 'bar')

    def test_process_request(self):
        server = BaseQueryServer()
        server.commands['foo'] = lambda s, x: x == 42
        self.assertTrue(server.process_request(['foo', 42]))

    def test_process_request_ddoc(self):
        server = BaseQueryServer()
        server.commands['foo'] = lambda s, x: x == 42
        self.assertTrue(server.process_request(['foo', 42]))

    def test_receive(self):
        server = BaseQueryServer(input=StringIO(b'["foo"]\n{"bar": "baz"}\n'))
        self.assertEqual(list(server.receive()), [['foo'], {'bar': 'baz'}])

    def test_response(self):
        output = StringIO()
        server = BaseQueryServer(output=output)
        server.respond(['foo'])
        server.respond({'bar': 'baz'})
        self.assertEqual(output.getvalue(), b'["foo"]\n{"bar": "baz"}\n')


class SimpleQueryServerTestCase(unittest.TestCase):

    def setUp(self):
        self.output = StringIO()
        self.server = partial(SimpleQueryServer, output=self.output)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BaseQueryServerTestCase, 'test'))
    suite.addTest(unittest.makeSuite(SimpleQueryServerTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

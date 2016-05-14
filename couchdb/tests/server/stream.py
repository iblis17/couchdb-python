# -*- coding: utf-8 -*-
#
import unittest

from couchdb.server import exceptions
from couchdb.server import stream
from couchdb.util import StringIO


class StreamTestCase(unittest.TestCase):

    def test_receive(self):
        """should decode json data from input stream"""
        input = StringIO(b'["foo", "bar"]\n["bar", {"foo": "baz"}]')
        reader = stream.receive(input)
        self.assertEqual(next(reader), ['foo', 'bar'])
        self.assertEqual(next(reader), ['bar', {'foo': 'baz'}])
        self.assertRaises(StopIteration, next, reader)

    def test_fail_on_receive_invalid_json_data(self):
        """should raise FatalError if json decode fails"""
        input = StringIO(b'["foo", "bar" "bar", {"foo": "baz"}]')
        try:
            next(stream.receive(input))
        except Exception as err:
            self.assertTrue(isinstance(err, exceptions.FatalError))
            self.assertEqual(err.args[0], 'json_decode')

    def test_respond(self):
        """should encode object to json and write it to output stream"""
        output = StringIO()
        stream.respond(['foo', {'bar': ['baz']}], output)
        self.assertEqual(output.getvalue(), b'["foo", {"bar": ["baz"]}]\n')

    def test_fail_on_respond_unserializable_to_json_object(self):
        """should raise FatalError if json encode fails"""
        output = StringIO()
        try:
            stream.respond(['error', 'foo', IOError('bar')], output)
        except Exception as err:
            self.assertTrue(isinstance(err, exceptions.FatalError))
            self.assertEqual(err.args[0], 'json_encode')

    def test_respond_none(self):
        """should not send any data if None passed"""
        output = StringIO()
        stream.respond(None, output)
        self.assertEqual(output.getvalue(), b'')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StreamTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

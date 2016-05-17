# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Christopher Lenz
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

from io import StringIO

import couchdb.server.__main__ as cli

from couchdb.tests import testutil


class ViewServerTestCase(unittest.TestCase):

    def test_reset(self):
        input = StringIO(u'["reset"]\n')
        output = StringIO()
        cli.run(input=input, output=output)
        self.assertEqual(output.getvalue(), 'true\n')

    def test_add_fun(self):
        input = StringIO(u'["add_fun", "def fun(doc): yield None, doc"]\n')
        output = StringIO()
        cli.run(input=input, output=output)
        self.assertEqual(output.getvalue(), 'true\n')

    def test_map_doc(self):
        input = StringIO(u'["add_fun", "def fun(doc): yield None, doc"]\n'
                         u'["map_doc", {"foo": "bar"}]\n')
        output = StringIO()
        cli.run(input=input, output=output)
        self.assertEqual(output.getvalue(),
                         u'true\n'
                         u'[[[null, {"foo": "bar"}]]]\n')

    def test_i18n(self):
        input = StringIO(u'["add_fun", "def fun(doc): yield doc[\\"test\\"], doc"]\n'
                         u'["map_doc", {"test": "b\xc3\xa5r"}]\n')
        output = StringIO()
        cli.run(input=input, output=output)
        self.assertEqual(output.getvalue(),
                         u'true\n'
                         u'[[["b\xc3\xa5r", {"test": "b\xc3\xa5r"}]]]\n')

    def test_map_doc_with_logging(self):
        fun = 'def fun(doc): log(\'running\'); yield None, doc'
        input = StringIO(u'["add_fun", "' + fun + u'"]\n'
                         u'["map_doc", {"foo": "bar"}]\n')
        output = StringIO()
        cli.run(input=input, output=output)
        self.assertEqual(output.getvalue(),
                         u'true\n'
                         u'["log", "running"]\n'
                         u'[[[null, {"foo": "bar"}]]]\n')

    def test_map_doc_with_legacy_logging(self):
        fun = 'def fun(doc): log(\'running\'); yield None, doc'
        input = StringIO(u'["add_fun", "' + fun + u'"]\n'
                         u'["map_doc", {"foo": "bar"}]\n')
        output = StringIO()
        cli.run(input=input, output=output, version=(0, 10, 0))
        self.assertEqual(output.getvalue(),
                         u'true\n'
                         u'{"log": "running"}\n'
                         u'[[[null, {"foo": "bar"}]]]\n')

    def test_map_doc_with_logging_json(self):
        fun = 'def fun(doc): log([1, 2, 3]); yield None, doc'
        input = StringIO(u'["add_fun", "' + fun + '"]\n'
                         u'["map_doc", {"foo": "bar"}]\n')
        output = StringIO()
        cli.run(input=input, output=output)
        self.assertEqual(output.getvalue(),
                         u'true\n'
                         u'["log", "[1, 2, 3]"]\n'
                         u'[[[null, {"foo": "bar"}]]]\n')

    def test_map_doc_with_legacy_logging_json(self):
        fun = 'def fun(doc): log([1, 2, 3]); yield None, doc'
        input = StringIO(u'["add_fun", "' + fun + u'"]\n'
                         u'["map_doc", {"foo": "bar"}]\n')
        output = StringIO()
        cli.run(input=input, output=output, version=(0, 10, 0))
        self.assertEqual(output.getvalue(),
                         u'true\n'
                         u'{"log": "[1, 2, 3]"}\n'
                         u'[[[null, {"foo": "bar"}]]]\n')

    def test_reduce(self):
        input = StringIO(
            u'["reduce", '
            u'["def fun(keys, values): return sum(values)"], '
            u'[[null, 1], [null, 2], [null, 3]]]\n')
        output = StringIO()
        cli.run(input=input, output=output)
        self.assertEqual(output.getvalue(), '[true, [6]]\n')

    def test_reduce_with_logging(self):
        input = StringIO(
            u'["reduce", '
            u'["def fun(keys, values): log(\'Summing %r\' % (values,)); return sum(values)"], '
            u'[[null, 1], [null, 2], [null, 3]]]\n')
        output = StringIO()
        cli.run(input=input, output=output)
        self.assertEqual(output.getvalue(),
                         u'["log", "Summing (1, 2, 3)"]\n'
                         u'[true, [6]]\n')

    def test_reduce_legacy_with_logging(self):
        input = StringIO(
            u'["reduce", '
            u'["def fun(keys, values): log(\'Summing %r\' % (values,)); return sum(values)"], '
            u'[[null, 1], [null, 2], [null, 3]]]\n')
        output = StringIO()
        cli.run(input=input, output=output, version=(0, 10, 0))
        self.assertEqual(output.getvalue(),
                         u'{"log": "Summing (1, 2, 3)"}\n'
                         u'[true, [6]]\n')

    def test_rereduce(self):
        input = StringIO(
            u'["rereduce", '
            u'["def fun(keys, values, rereduce): return sum(values)"], '
            u'[1, 2, 3]]\n')
        output = StringIO()
        cli.run(input=input, output=output)
        self.assertEqual(output.getvalue(), '[true, [6]]\n')

    def test_reduce_empty(self):
        input = StringIO(
            u'["reduce", '
            u'["def fun(keys, values): return sum(values)"], '
            u'[]]\n')
        output = StringIO()
        cli.run(input=input, output=output)
        self.assertEqual(
            output.getvalue(),
            u'[true, [0]]\n')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(testutil.doctest_suite(cli))
    suite.addTest(unittest.makeSuite(ViewServerTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

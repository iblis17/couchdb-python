# -*- coding: utf-8 -*-
#
import binascii
import types
import unittest

from couchdb import util
from couchdb.server import compiler
from couchdb.server import exceptions

# universe.question.get_answer() => 42 (int)
DUMMY_EGG = (''
'UEsDBBQAAAAIAKx1qD6TBtcyAwAAAAEAAAAdAAAARUdHLUlORk8vZGVwZW5kZW5jeV9saW5rcy50'
'eHTjAgBQSwMEFAAAAAgArHWoPrbiy8BxAAAAuQAAABEAAABFR0ctSU5GTy9QS0ctSU5GT/NNLUlM'
'SSxJ1A1LLSrOzM+zUjDUM+Dl8kvMTbVSSE1P5+VClQguzc1NLKq0Ugj18/bzD/fj5fLIz03VLUhM'
'T0UScywtycgvwhDQTc1NzMxBEvbJTE7NK0bW6ZJanFyUWVACthEuGpCTWJKWX5SLJAQAUEsDBBQA'
'AAAIAKx1qD7n9n20agAAAKYAAAAUAAAARUdHLUlORk8vU09VUkNFUy50eHQrTi0pLdArqOTlSk1P'
'1wNi3cy8tHz9AG93XU8/N3804WD/0CBn12C9kooSNJmU1ILUvJTUvOTK+JzMvOxiLEpK8gvic1LL'
'UnMgcqV5mWWpRcWp+vHxmXmZJfHxYFfARQtLU4tLMvPzwKIAUEsDBBQAAAAIAKx1qD6I9wVkCwAA'
'AAkAAAAWAAAARUdHLUlORk8vdG9wX2xldmVsLnR4dCvNyyxLLSpO5QIAUEsDBBQAAAAIAKx1qD6T'
'BtcyAwAAAAEAAAARAAAARUdHLUlORk8vemlwLXNhZmXjAgBQSwMEFAAAAAgAunSoPiupvPYyAAAA'
'OgAAABQAAAB1bml2ZXJzZS9xdWVzdGlvbi5weeOKj0/MyYmPV7BViFZPTy2JT8wrLk8tUo/l4kpJ'
'TVNAiGhoWnEpAEFRaklpUZ6CiREAUEsDBBQAAAAIAKx1qD71mOyCrAAAAAYBAAAVAAAAdW5pdmVy'
'c2UvcXVlc3Rpb24ucHljy/3Ey9VQdMw3mQEKGIHYAYiLxYBECgNDOiNDFJDByNDCwBDFyJDCxBCs'
'wQyUKuECEumpJfGJecXlqUUo+p1B+lkYwNqCNZiADL9MLSCpwYBJlIAkkkozc1JiklIyi0v0yjPz'
'jI1iUtPTY0rzMstSi4pTYwpLU4tLMvPz9Aoqg0B6QEYXM4Ft8wMbX8IOJOLjE3Ny4uPBKsCiYFYQ'
'E4p1QSD3lYAIeyaYKZxMAFBLAwQUAAAACADJdKg+38+n3x8AAAAdAAAAFAAAAHVuaXZlcnNlL19f'
'aW5pdF9fLnB5SyvKz1UozcssSy0qTlXIzC3ILypRKCxNLS7JzM8DAFBLAwQUAAAACACsdag+VUoJ'
'NoEAAAC4AAAAFQAAAHVuaXZlcnNlL19faW5pdF9fLnB5Y8v9xMs1q+iYbzIDFDABsQMQFwsCiRQG'
'hmwGhhxGhihGBsYURoZgDZC0BiNIngNIFJamFpdk5uf5gcVLQEKleZllqUXFqSXI8mAdQSBCgwFG'
'lGgBiaTSzJyUmKSUzOISvfLMPGOjmNT09BiYGTHx8Zl5mSXx8XoFlSUg3fZgm0G6AVBLAQIUABQA'
'AAAIAKx1qD6TBtcyAwAAAAEAAAAdAAAAAAAAAAAAAAC2gQAAAABFR0ctSU5GTy9kZXBlbmRlbmN5'
'X2xpbmtzLnR4dFBLAQIUABQAAAAIAKx1qD624svAcQAAALkAAAARAAAAAAAAAAAAAAC2gT4AAABF'
'R0ctSU5GTy9QS0ctSU5GT1BLAQIUABQAAAAIAKx1qD7n9n20agAAAKYAAAAUAAAAAAAAAAAAAAC2'
'gd4AAABFR0ctSU5GTy9TT1VSQ0VTLnR4dFBLAQIUABQAAAAIAKx1qD6I9wVkCwAAAAkAAAAWAAAA'
'AAAAAAAAAAC2gXoBAABFR0ctSU5GTy90b3BfbGV2ZWwudHh0UEsBAhQAFAAAAAgArHWoPpMG1zID'
'AAAAAQAAABEAAAAAAAAAAAAAALaBuQEAAEVHRy1JTkZPL3ppcC1zYWZlUEsBAhQAFAAAAAgAunSo'
'PiupvPYyAAAAOgAAABQAAAAAAAAAAAAAALaB6wEAAHVuaXZlcnNlL3F1ZXN0aW9uLnB5UEsBAhQA'
'FAAAAAgArHWoPvWY7IKsAAAABgEAABUAAAAAAAAAAAAAALaBTwIAAHVuaXZlcnNlL3F1ZXN0aW9u'
'LnB5Y1BLAQIUABQAAAAIAMl0qD7fz6ffHwAAAB0AAAAUAAAAAAAAAAAAAAC2gS4DAAB1bml2ZXJz'
'ZS9fX2luaXRfXy5weVBLAQIUABQAAAAIAKx1qD5VSgk2gQAAALgAAAAVAAAAAAAAAAAAAAC2gX8D'
'AAB1bml2ZXJzZS9fX2luaXRfXy5weWNQSwUGAAAAAAkACQBZAgAAMwQAAAAA')


class DDocModulesTestCase(unittest.TestCase):

    def test_resolve_module(self):
        module = {'foo': {'bar': {'baz': '42'}}}
        mod_info = compiler.resolve_module('foo/bar/baz'.split('/'), {}, module)
        self.assertEqual(
            mod_info,
            {
                'current': '42',
                'parent': {
                    'current': module['foo']['bar'],
                    'id': 'foo/bar',
                    'parent': {
                        'id': 'foo',
                        'current': module['foo'],
                        'parent': {'current': module}
                    },
                },
                'id': 'foo/bar/baz',
                'exports': {},
            }
        )

    def test_relative_path(self):
        module = {'foo': {'bar': {'baz': '42'}}}
        mod_info = compiler.resolve_module(
            'foo/./bar/../bar/././././baz/../../bar/baz'.split('/'), {}, module)
        self.assertTrue(mod_info['id'], 'foo/bar/baz')

    def test_relative_path_from_other_point(self):
        module = {'foo': {'bar': {'baz': '42', 'boo': '100500'}}}
        mod_info = compiler.resolve_module('foo/bar/baz'.split('/'), {}, module)
        mod_info = compiler.resolve_module('../boo'.split('/'), mod_info, module)
        self.assertEqual(mod_info['id'], 'foo/bar/boo')

    def test_invalid_require_path_error_type(self):
        try:
            compiler.resolve_module('/'.split('/'), {}, {})
        except Exception as err:
            self.assertTrue(isinstance(err, exceptions.Error))
            self.assertEqual(err.args[0], 'invalid_require_path')

    def test_fail_on_slash_started_path(self):
        module = {'foo': {'bar': {'baz': '42'}}}
        self.assertRaises(exceptions.Error,
                          compiler.resolve_module,
                          '/foo/bar/baz'.split('/'), {}, module)

    def test_fail_on_sequence_of_slashes_in_path(self):
        module = {'foo': {'bar': {'baz': '42'}}}
        self.assertRaises(exceptions.Error,
                          compiler.resolve_module,
                          'foo/bar//baz'.split('/'), {}, module)

    def test_fail_on_trailing_slash(self):
        module = {'foo': {'bar': {'baz': '42'}}}
        self.assertRaises(exceptions.Error,
                          compiler.resolve_module,
                          'foo/bar/baz/'.split('/'), {}, module)

    def test_fail_if_path_item_missed(self):
        module = {'foo': {'bar': {'baz': '42'}}}
        self.assertRaises(exceptions.Error,
                          compiler.resolve_module,
                          'foo/baz'.split('/'), {}, module)

    def test_fail_if_leaf_not_a_source_string(self):
        module = {'foo': {'bar': {'baz': 42}}}
        self.assertRaises(exceptions.Error,
                          compiler.resolve_module,
                          'foo/bar/baz'.split('/'), {}, module)

    def test_fail_path_too_long(self):
        module = {'foo': {'bar': {'baz': '42'}}}
        self.assertRaises(exceptions.Error,
                          compiler.resolve_module,
                          'foo/bar/baz/boo'.split('/'), {}, module)

    def test_fail_no_path_item_parent(self):
        module = {'foo': {'bar': {'baz': '42'}}}
        self.assertRaises(exceptions.Error,
                          compiler.resolve_module,
                          '../foo/bar/baz'.split('/'), {}, module)

    def test_fail_for_relative_path_against_root_module(self):
        module = {'foo': {'bar': {'baz': '42'}}}
        self.assertRaises(exceptions.Error,
                          compiler.resolve_module,
                          './foo/bar/baz'.split('/'), {}, module)

    def test_cache_bytecode_for_future_usage(self):
        ddoc = {'foo': {'bar': {'baz': 'exports["answer"] = 42'}}}
        require = compiler.require(ddoc)
        exports = require('foo/bar/baz')
        self.assertEqual(exports['answer'], 42)
        self.assertTrue(isinstance(ddoc['foo']['bar']['baz'], types.CodeType))
        exports = require('foo/bar/baz')
        self.assertEqual(exports['answer'], 42)

    def test_cache_egg_exports(self):
        ddoc = {
            'lib': {
                'universe': DUMMY_EGG
            }
        }
        require = compiler.require(ddoc, enable_eggs=True)
        exports = require('lib/universe')
        self.assertEqual(exports['universe'].question.get_answer(), 42)
        self.assertTrue(isinstance(ddoc['lib']['universe'], dict))
        exports = require('lib/universe')
        self.assertEqual(exports['universe'].question.get_answer(), 42)

    def test_reqire_egg_from_module(self):
        ddoc = {
            '_id': 'foo',
            'lib': {
                'egg': DUMMY_EGG,
                'utils.py': (
                    "universe = require('lib/egg')['universe'] \n"
                    "exports['title'] = 'The Answer' \n"
                    "exports['body'] = str(universe.question.get_answer())")
            }
        }
        require = compiler.require(ddoc, enable_eggs=True)
        exports = require('lib/utils.py')
        result = ' - '.join([exports['title'], exports['body']])
        self.assertEqual(result, 'The Answer - 42')

    def test_required_modules_has_global_namespace_access(self):
        ddoc = {
            '_id': 'foo',
            'lib': {
                'egg': DUMMY_EGG,
                'utils.py': (
                    "import math\n"
                    "def foo():\n"
                    "  return math.cos(0)\n"
                    "exports['foo'] = foo")
            }
        }
        require = compiler.require(ddoc, enable_eggs=True)
        exports = require('lib/utils.py')
        self.assertEqual(exports['foo'](), 1)

    def test_fail_on_resolving_deadlock(self):
        ddoc = {
            'lib': {
                'stuff': (
                    "exports['utils'] = require('./utils') \n"
                    "exports['body'] = 'doc forever!'"),
                'helper': (
                    "exports['title'] = 'best ever' \n"
                    "exports['body'] = require('./stuff')"),
                'utils': (
                    "def help():\n"
                    "  return require('./helper') \n"
                    "stuff = help()\n"
                    "exports['title'] = stuff['title'] \n"
                    "exports['body'] = stuff['body']")
            }
        }
        require = compiler.require(ddoc)
        self.assertRaises(exceptions.Error, require, 'lib/utils')


class EggModulesTestCase(unittest.TestCase):

    def test_require_egg(self):
        exports = compiler.import_b64egg(DUMMY_EGG)
        self.assertEqual(exports['universe'].question.get_answer(), 42)

    def test_fail_for_invalid_egg(self):
        egg = 'UEsDBBQAAAAIAKx1qD6TBtcyAwAAAAEAAAAdAAAARUdHLUlORk8vZGVwZW5kZW=='
        self.assertRaises(exceptions.Error, compiler.import_b64egg, egg)

    def test_fail_for_invalid_b64egg_string(self):
        egg = 'UEsDBBQAAAAIAKx1qD6TBtcyAwAAAAEAAAAdAAAARUdHLUlORk8vZGVwZW5kZW'
        # python3 will raise ``binascii.Error``
        # https://docs.python.org/3/library/base64.html#base64.b64decode
        self.assertRaises((TypeError, binascii.Error),
                          compiler.import_b64egg, egg)

    def test_fail_for_no_setuptools_or_pkgutils(self):
        egg = 'UEsDBBQAAAAIAKx1qD6TBtcyAwAAAAEAAAAdAAAARUdHLUlORk8vZGVwZW5kZW=='
        func = compiler.iter_modules
        compiler.iter_modules = None
        self.assertRaises(ImportError, compiler.import_b64egg, egg)
        compiler.iter_modules = func


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DDocModulesTestCase, 'test'))
    suite.addTest(unittest.makeSuite(EggModulesTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

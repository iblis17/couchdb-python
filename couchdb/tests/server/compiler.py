# -*- coding: utf-8 -*-
#
import binascii
import types
import unittest

from couchdb import util
from couchdb.server import compiler
from couchdb.server import exceptions


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

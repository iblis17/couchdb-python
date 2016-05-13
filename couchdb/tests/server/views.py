# -*- coding: utf-8 -*-
#
import unittest

from couchdb.server import exceptions
from couchdb.server import state
from couchdb.server import views
from couchdb.server.mock import MockQueryServer


class MapTestCase(unittest.TestCase):

    def setUp(self):
        self.server = MockQueryServer()

    def test_map_doc(self):
        """should apply map function to document"""
        state.add_fun(
            self.server,
            'def mapfun(doc):\n'
            '  yield doc["_id"], "bar"'
        )
        result = views.map_doc(self.server, {'_id': 'foo'})
        self.assertEqual(result, [[['foo', 'bar']]])

    def test_map_doc_by_many_functions(self):
        """should apply multiple map functions to single document"""
        state.add_fun(
            self.server,
            'def mapfun(doc):\n'
            '  yield doc["_id"], "foo"\n'
            '  yield doc["_id"], "bar"'
        )
        state.add_fun(
            self.server,
            'def mapfun(doc):\n'
            '  yield doc["_id"], "baz"'
        )
        state.add_fun(
            self.server,
            'def mapfun(doc):\n'
            '  return [[doc["_id"], "boo"]]'
        )
        result = views.map_doc(self.server, {'_id': 'foo'})
        self.assertEqual(result, [[['foo', 'foo'], ['foo', 'bar']],
                                  [['foo', 'baz']], [['foo', 'boo']]])

    def test_rethrow_viewserver_exception_as_is(self):
        """should rethrow any QS exception as is"""
        state.add_fun(
            self.server,
            'def mapfun(doc):\n'
            '  raise FatalError("test", "let it crush!")'
        )
        try:
            views.map_doc(self.server, {'_id': 'foo'})
        except Exception as err:
            self.assertTrue(err, exceptions.FatalError)
            self.assertEqual(err.args[0], 'test')
            self.assertEqual(err.args[1], 'let it crush!')

    def test_raise_error_exception_on_any_python_one(self):
        """should raise QS Error exception on any Python one"""
        state.add_fun(
            self.server,
            'def mapfun(doc):\n'
            '  1/0'
        )
        try:
            views.map_doc(self.server, {'_id': 'foo'})
        except Exception as err:
            self.assertTrue(err, exceptions.Error)
            self.assertEqual(err.args[0], ZeroDivisionError.__name__)

    def test_map_function_shouldnt_change_document(self):
        """should prevent document changing within map function"""
        state.add_fun(
            self.server,
            'def mapfun(doc):\n'
            '  assert "bar" not in doc\n'
            '  doc["bar"] = "baz"\n'
            '  yield doc["bar"], 1'
        )
        state.add_fun(
            self.server,
            'def mapfun(doc):\n'
            '  assert "bar" not in doc\n'
            '  yield doc["_id"], 0'
        )
        doc = {'_id': 'foo'}
        views.map_doc(self.server, doc)

    def test_prevent_changes_of_nested_mutable_values(self):
        state.add_fun(
            self.server,
            'def mapfun(doc):\n'
            '  assert not doc["bar"]["baz"]\n'
            '  doc["bar"]["baz"].append(42)\n'
            '  yield doc["bar"], 1'
        )
        state.add_fun(
            self.server,
            'def mapfun(doc):\n'
            '  assert not doc["bar"]["baz"]\n'
            '  yield doc["_id"], 0'
        )
        doc = {'_id': 'foo', 'bar': {'baz': []}}
        views.map_doc(self.server, doc)

    def test_return_nothing(self):
        """shouldn't crush if map function returns nothing"""
        state.add_fun(
            self.server,
            'def mapfun(doc):\n'
            '  pass'
        )
        doc = {'_id': 'foo'}
        views.map_doc(self.server, doc)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MapTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

# -*- coding: utf-8 -*-
#
import unittest

from inspect import getsource
from textwrap import dedent

from couchdb.server import exceptions
from couchdb.server import render
from couchdb.server.mock import MockQueryServer


class ShowTestCase(unittest.TestCase):

    def setUp(self):
        self.server = MockQueryServer()
        self.doc = {'title': 'best ever', 'body': 'doc body', '_id': 'couch'}

    def test_show_simple(self):
        def func(doc, req):
            return ' - '.join([doc['title'], doc['body']])
        resp = render.run_show(self.server, func, self.doc, {})
        self.assertEqual(resp, ['resp', {'body': 'best ever - doc body'}])

    def test_show_with_headers_old(self):
        def func(doc, req):
            resp = {
                'code': 200,
                'headers': {'X-Couchdb-Python': 'Hello, world!'}
            }
            resp['body'] = ' - '.join([doc['title'], doc['body']])
            return resp
        funsrc = dedent(getsource(func))
        resp = render.show_doc(self.server, funsrc, self.doc, {})
        valid_resp = {
            'headers': {'X-Couchdb-Python': 'Hello, world!'},
            'code': 200,
            'body': 'best ever - doc body'
        }
        self.assertEqual(resp, valid_resp)

    def test_show_with_headers(self):
        def func(doc, req):
            resp = {
                'code': 200,
                'headers': {'X-Couchdb-Python': 'Hello, world!'}
            }
            resp['body'] = ' - '.join([doc['title'], doc['body']])
            return resp
        resp = render.run_show(self.server, func, self.doc, {})
        valid_resp = ['resp', {
            'headers': {'X-Couchdb-Python': 'Hello, world!'},
            'code': 200,
            'body': 'best ever - doc body'
        }]
        self.assertEqual(resp, valid_resp)

    def test_show_provides_old(self):
        def func(doc, req):
            def html():
                return '<html><body>%s</body></html>' % doc['_id']

            def xml():
                return '<root><doc id="%s" /></root>' % doc['_id']

            def foo():
                return 'foo? bar! bar!'

            register_type('foo', 'application/foo', 'application/x-foo')
            return response_with(req, {
                'html': html,
                'xml': xml,
                'foo': foo,
                'fallback': 'html'
            })

        req = {'headers': {'Accept': 'text/html,application/atom+xml; q=0.9'}}
        funsrc = dedent(getsource(func))
        resp = render.show_doc(self.server, funsrc, self.doc, req)
        self.assertTrue('text/html' in resp['headers']['Content-Type'])
        self.assertEqual(resp['body'], '<html><body>couch</body></html>')

    def test_show_provides_old_fallback(self):
        def func(doc, req):
            def foo():
                return 'foo? bar! bar!'
            register_type('foo', 'application/foo', 'application/x-foo')
            return response_with(req, {
                'foo': foo,
                'fallback': 'foo'
            })

        req = {'headers': {'Accept': 'text/html,application/atom+xml; q=0.9'}}
        funsrc = dedent(getsource(func))
        resp = render.show_doc(self.server, funsrc, self.doc, req)
        self.assertTrue('application/foo' in resp['headers']['Content-Type'])
        self.assertEqual(resp['body'], 'foo? bar! bar!')

    def test_not_acceptable_old(self):
        def func(doc, req):
            def foo():
                return 'foo? bar! bar!'
            register_type('foo', 'application/foo', 'application/x-foo')
            return response_with(req, {
                'foo': foo,
            })

        req = {'headers': {'Accept': 'text/html,application/atom+xml; q=0.9'}}
        funsrc = dedent(getsource(func))
        resp = render.show_doc(self.server, funsrc, self.doc, req)
        self.assertTrue('code' in resp)
        self.assertEqual(resp['code'], 406)

    def test_nowhere_to_fallback(self):
        def func(doc, req):
            def foo():
                return 'foo? bar! bar!'
            register_type('foo', 'application/foo', 'application/x-foo')
            return response_with(req, {
                'foo': foo,
                'fallback': 'htnl'
            })

        req = {'headers': {'Accept': 'text/html,application/atom+xml; q=0.9'}}
        funsrc = dedent(getsource(func))
        resp = render.show_doc(self.server, funsrc, self.doc, req)
        self.assertTrue('code' in resp)
        self.assertEqual(resp['code'], 406)

    def test_error_in_resonse_with_handler_function(self):
        def func(doc, req):
            def foo():
                raise Error('foo', 'bar')
            register_type('foo', 'application/foo', 'application/x-foo')
            return response_with(req, {
                'foo': foo,
            })

        req = {'headers': {'Accept': 'application/foo'}}
        funsrc = dedent(getsource(func))
        self.assertRaises(exceptions.Error, render.show_doc,
                          self.server, funsrc, self.doc, req)

    def test_python_exception_in_show_doc(self):
        def func(doc, req):
            1/0
        funsrc = dedent(getsource(func))
        try:
            render.show_doc(self.server, funsrc, self.doc, {})
        except Exception as err:
            self.assertTrue(isinstance(err, exceptions.Error))
            self.assertEqual(err.args[0], 'render_error')
        else:
            self.fail('render_error expected')

    def test_invalid_show_doc_response(self):
        def func(doc, req):
            return object()
        funsrc = dedent(getsource(func))
        try:
            render.show_doc(self.server, funsrc, self.doc, {})
        except Exception as err:
            self.assertTrue(isinstance(err, exceptions.Error))
            self.assertEqual(err.args[0], 'render_error')
        else:
            self.fail('render_error expected')

    def test_show_provides(self):
        def func(doc, req):
            def html():
                return '<html><body>%s</body></html>' % doc['_id']

            def xml():
                return '<root><doc id="%s" /></root>' % doc['_id']

            def foo():
                return 'foo? bar! bar!'

            register_type('foo', 'application/foo', 'application/x-foo')
            provides('html', html)
            provides('xml', xml)
            provides('foo', foo)
        req = {'headers': {'Accept': 'text/html,application/atom+xml; q=0.9'}}
        token, resp = render.run_show(self.server, func, self.doc, req)
        self.assertEqual(token, 'resp')
        self.assertTrue('text/html' in resp['headers']['Content-Type'])
        self.assertEqual(resp['body'], '<html><body>couch</body></html>')

    def test_show_list_api(self):
        def func(doc, req):
            start({
                'X-Couchdb-Python': 'Relax!'
            })
            send('foo, ')
            send('bar, ')
            return 'baz'
        token, resp = render.run_show(self.server, func, self.doc, {})
        self.assertEqual(token, 'resp')
        self.assertEqual(resp['headers']['X-Couchdb-Python'], 'Relax!')
        self.assertEqual(resp['body'], 'foo, bar, baz')

    def test_show_list_api_and_provides(self):
        # https://issues.apache.org/jira/browse/COUCHDB-1272
        def func(doc, req):
            def text():
                send('4, ')
                send('5, ')
                send('6, ')
                return '7!'
            provides('text', text)
            send('1, ')
            send('2, ')
            return '3, '
        token, resp = render.run_show(self.server, func, self.doc, {})
        self.assertEqual(token, 'resp')
        self.assertEqual(resp['body'], '1, 2, 3, 4, 5, 6, 7!')

    def test_show_provides_return_status_code_or_headers(self):
        # https://issues.apache.org/jira/browse/COUCHDB-1330
        def func(doc, req):
            def text():
                return {
                    'headers': {
                        'Location': 'http://www.iriscouch.com'
                    },
                    'code': 302,
                    'body': 'Redirecting to IrisCouch website...'
                }
            provides('text', text)
        token, resp = render.run_show(self.server, func, self.doc, {})
        self.assertEqual(token, 'resp')
        self.assertTrue('headers' in resp)
        self.assertTrue('Location' in resp['headers'])
        self.assertEqual(resp['headers']['Location'], 'http://www.iriscouch.com')
        self.assertTrue('code' in resp)
        self.assertEqual(resp['code'], 302)

    def test_show_provides_return_json_or_base64_body(self):
        # https://issues.apache.org/jira/browse/COUCHDB-1330
        def func(doc, req):
            def text():
                return {
                    'code': 419,
                    'json': {'foo': 'bar'}
                }
            provides('text', text)

        token, resp = render.run_show(self.server, func, self.doc, {})
        self.assertEqual(token, 'resp')
        self.assertTrue('code' in resp)
        self.assertTrue(resp['code'], 419)
        self.assertEqual(resp['json'], {'foo': 'bar'})

    def test_show_provided_resp_overrides_original_resp_data(self):
        # https://issues.apache.org/jira/browse/COUCHDB-1330
        def func(doc, req):
            def text():
                return {
                    'code': 419,
                    'headers': {
                        'X-Couchdb-Python': 'Relax!'
                    },
                    'json': {'foo': 'bar'}
                }
            provides('text', text)
            return {
                'code': 200,
                'headers': {
                    'Content-Type': 'text/plain'
                },
                'json': {'boo': 'bar!'}
            }
        token, resp = render.run_show(self.server, func, self.doc, {})
        self.assertEqual(token, 'resp')
        self.assertTrue('code' in resp)
        self.assertTrue(resp['code'], 419)
        self.assertEqual(resp['headers'], {'X-Couchdb-Python': 'Relax!'})
        self.assertEqual(resp['json'], {'foo': 'bar'})

    def test_show_invalid_start_func_headers(self):
        def func(doc, req):
            start({
                'code': 200,
                'headers': {
                    'X-Couchdb-Python': 'Relax!'
                }
            })
            send('let it crush!')
        try:
            token, resp = render.run_show(self.server, func, self.doc, {})
        except Exception as err:
            self.assertTrue(isinstance(err, exceptions.Error))
            self.assertEqual(err.args[0], 'render_error')
        else:
            self.fail('Render error excepted due to invalid headers passed to'
                      ' start function')

    def test_invalid_response_type(self):
        def func(doc, req):
            return object()
        try:
            token, resp = render.run_show(self.server, func, self.doc, {})
        except Exception as err:
            self.assertTrue(isinstance(err, exceptions.Error))
            self.assertEqual(err.args[0], 'render_error')
        else:
            self.fail('Show function should return dict or string value')

    def test_show_function_has_no_access_to_get_row(self):
        def func(doc, req):
            for row in get_row():
                pass

        try:
            token, resp = render.run_show(self.server, func, self.doc, {})
        except Exception as err:
            self.assertTrue(isinstance(err, exceptions.Error))
            self.assertEqual(err.args[0], 'render_error')
        else:
            self.fail('Show function should not has get_row() method in scope.')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ShowTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

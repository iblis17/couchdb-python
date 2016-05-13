# -*- coding: utf-8 -*-
#
import unittest

from couchdb.tests.server import compiler, mime, qs, render, stream


def suite():
    suite = unittest.TestSuite()
    suite.addTest(compiler.suite())
    suite.addTest(mime.suite())
    suite.addTest(qs.suite())
    suite.addTest(render.suite())
    suite.addTest(stream.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

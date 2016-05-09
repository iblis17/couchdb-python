# -*- coding: utf-8 -*-
#
import unittest

from couchdb.tests.server import qs, stream


def suite():
    suite = unittest.TestSuite()
    suite.addTest(qs.suite())
    suite.addTest(stream.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
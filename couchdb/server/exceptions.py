# -*- coding: utf-8 -*-
#


class QueryServerException(Exception):
    """Base query server exception"""


class Error(QueryServerException):
    """Non fatal error which should not terminate query serve"""


class FatalError(QueryServerException):
    """Fatal error which should terminates query server"""


class Forbidden(QueryServerException):
    """Non fatal error which signs access deny for processed operation"""

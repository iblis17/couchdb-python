# -*- coding: utf-8 -*-
#
import logging
import sys

from functools import partial

from couchdb import json, util
from couchdb.server import (compiler, ddoc, exceptions, filters, render,
                            state, stream, validate, views)
from couchdb.server.helpers import maybe_extract_source

__all__ = ('BaseQueryServer', 'SimpleQueryServer')


class NullHandler(logging.Handler):
    """NullHandler backport for python26"""
    def emit(self, *args, **kwargs):
        pass


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(NullHandler())


class BaseQueryServer(object):
    """Implements Python CouchDB query server.

    :param version: CouchDB server version as three int elements tuple.
                    By default tries to work against highest implemented one.
    :type version: tuple
    :param input: Input stream with ``.readline()`` support.
    :param output: Output stream with ``.readline()`` support.

    :param options: Custom keyword arguments.
    """
    def __init__(self, version=None, input=sys.stdin, output=sys.stdout,
                 **options):
        """Initialize query server instance."""

        self._receive = partial(stream.receive, input=input)
        self._respond = partial(stream.respond, output=output)

        self._version = version or (999, 999, 999)

        self._commands = {}
        self._commands_ddoc = {}
        self._ddoc_cache = {}

        self._config = {}
        self._state = {
            'view_lib': None,
            'line_length': 0,
            'query_config': {},
            'functions': [],
            'functions_src': [],
            'row_line': {}
        }

        for key, value in options.items():
            self.handle_config(key, value)


class SimpleQueryServer(BaseQueryServer):
    """Implements Python query server with high level API."""

    def __init__(self, *args, **kwargs):
        super(SimpleQueryServer, self).__init__(*args, **kwargs)

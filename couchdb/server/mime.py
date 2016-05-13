# -*- coding: utf-8 -*-
#
import logging

from pprint import pformat

from couchdb.server.exceptions import Error
from couchdb.util import OrderedDict

log = logging.getLogger(__name__)

__all__ = ('best_match', 'MimeProvider', 'DEFAULT_TYPES')


# Some default types.
# Build list of `MIME types
# <http://www.iana.org/assignments/media-types/>`_ for HTTP responses.
# Ported from `Ruby on Rails
# <https://github.com/rails/rails/blob/v3.1.0/actionpack/lib/action_dispatch/http/mime_types.rb>`_
DEFAULT_TYPES = {
    'all': ['*/*'],
    'text': ['text/plain; charset=utf-8', 'txt'],
    'html': ['text/html; charset=utf-8'],
    'xhtml': ['application/xhtml+xml', 'xhtml'],
    'xml': ['application/xml', 'text/xml', 'application/x-xml'],
    'js': ['text/javascript', 'application/javascript',
           'application/x-javascript'],
    'css': ['text/css'],
    'ics': ['text/calendar'],
    'csv': ['text/csv'],
    'rss': ['application/rss+xml'],
    'atom': ['application/atom+xml'],
    'yaml': ['application/x-yaml', 'text/yaml'],
    # just like Rails
    'multipart_form': ['multipart/form-data'],
    'url_encoded_form': ['application/x-www-form-urlencoded'],
    # http://www.ietf.org/rfc/rfc4627.txt
    'json': ['application/json', 'text/x-json']
    # TODO: https://issues.apache.org/jira/browse/COUCHDB-1261
    # 'kml', 'application/vnd.google-earth.kml+xml',
    # 'kmz', 'application/vnd.google-earth.kmz'
}


class MimeProvider(object):
    """Provides custom function depending on requested MIME type."""

    def __init__(self):
        self.mimes_by_key = {}
        self.keys_by_mime = {}
        self.funcs_by_key = OrderedDict()
        self._resp_content_type = None

        for k, v in DEFAULT_TYPES.items():
            self.register_type(k, *v)

    def is_provides_used(self):
        """Checks if any provides function is registered."""
        return bool(self.funcs_by_key)

    @property
    def resp_content_type(self):
        """Returns actual response content type."""
        return self._resp_content_type

    def register_type(self, key, *args):
        """Register MIME types.

        :param key: Shorthand key for list of MIME types.
        :type key: str

        :param args: List of full quality names of MIME types.

        Predefined types:
            - all: ``*/*``
            - text: ``text/plain; charset=utf-8``, ``txt``
            - html: ``text/html; charset=utf-8``
            - xhtml: ``application/xhtml+xml``, ``xhtml``
            - xml: ``application/xml``, ``text/xml``, ``application/x-xml``
            - js: ``text/javascript``, ``application/javascript``,
              ``application/x-javascript``
            - css: ``text/css``
            - ics: ``text/calendar``
            - csv: ``text/csv``
            - rss: ``application/rss+xml``
            - atom: ``application/atom+xml``
            - yaml: ``application/x-yaml``, ``text/yaml``
            - multipart_form: ``multipart/form-data``
            - url_encoded_form: ``application/x-www-form-urlencoded``
            - json: ``application/json``, ``text/x-json``

        Example:
            >>> register_type('png', 'image/png')
        """
        self.mimes_by_key[key] = args
        for item in args:
            self.keys_by_mime[item] = key

    def provides(self, key, func):
        """Register MIME type handler which will be called when design function
        would be requested with matched `Content-Type` value.

        :param key: MIME type.
        :type key: str

        :param func: Function object or any callable.
        :type func: function or callable
        """
        # TODO: https://issues.apache.org/jira/browse/COUCHDB-898
        self.funcs_by_key[key] = func

    def run_provides(self, req, default=None):
        bestfun = None
        bestkey = None
        accept = None
        if 'headers' in req:
            accept = req['headers'].get('Accept')
        if 'query' in req and 'format' in req['query']:
            bestkey = req['query']['format']
            if bestkey in self.mimes_by_key:
                self._resp_content_type = self.mimes_by_key[bestkey][0]
        elif accept:
            supported_mimes = (
                mime
                for key in self.funcs_by_key
                for mime in self.mimes_by_key[key]
                if key in self.mimes_by_key)
            self._resp_content_type = best_match(supported_mimes, accept)
            bestkey = self.keys_by_mime.get(self._resp_content_type)
        else:
            bestkey = self.funcs_by_key and list(self.funcs_by_key.keys())[0] or None
        log.debug('Provides\nBest key: %s\nBest mime: %s\nRequest: %s',
                  bestkey, self.resp_content_type, req)
        if bestkey is not None:
            bestfun = self.funcs_by_key.get(bestkey)
        if bestfun is not None:
            return bestfun()
        if default is not None and default in self.funcs_by_key:
            bestkey = default
            bestfun = self.funcs_by_key[default]
            self._resp_content_type = self.mimes_by_key[default][0]
            log.debug('Provides fallback\n'
                      'Best key: %s\nBest mime: %s\nRequest: %s',
                      bestkey, self.resp_content_type, req)
            return bestfun()
        supported_types = ', '.join(
            ', '.join(value) or key for key, value in self.mimes_by_key.items())
        content_type = accept or self.resp_content_type or bestkey
        msg = 'Content-Type %s not supported, try one of:\n%s'
        log.error(msg, content_type, supported_types)
        raise Error('not_acceptable', msg % (content_type, supported_types))

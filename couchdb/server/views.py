# -*- coding: utf-8 -*-
#
import copy
import logging

from couchdb import json
from couchdb.server.exceptions import QueryServerException, Error

__all__ = ('map_doc',)

log = logging.getLogger(__name__)


def map_doc(server, doc):
    """Applies available map functions to document.

    :command: map_doc

    :param server: Query server instance.
    :type server: :class:`~couchdb.server.BaseQueryServer`

    :param doc: Document object.
    :type doc: dict

    :return: List of key-value results for each applied map function.

    :raises:
        - :exc:`~couchdb.server.exceptions.Error`
          If any Python exception occurs due mapping.
    """
    docid = doc.get('_id')
    log.debug('Apply map functions to document `%s`:\n%s', docid, doc)
    orig_doc = copy.deepcopy(doc)
    map_results = []
    _append = map_results.append
    try:
        for idx, func in enumerate(server.state['functions']):
            # TODO: https://issues.apache.org/jira/browse/COUCHDB-729
            # Apply copy.deepcopy for `key` and `value` to fix this issue
            _append([[key, value] for key, value in func(doc) or []])
            if doc != orig_doc:
                log.warning('Document `%s` had been changed by map function'
                            ' `%s`, but was restored to original state',
                            docid, func.__name__)
                doc = copy.deepcopy(orig_doc)
    except Exception as err:
        msg = 'Exception raised for document `%s`:\n%s\n\n%s\n\n'
        funsrc = server.state['functions_src'][idx]
        log.exception(msg, docid, doc, funsrc)
        if isinstance(err, QueryServerException):
            raise
        # TODO: https://issues.apache.org/jira/browse/COUCHDB-282
        # Raise FatalError to fix this issue
        raise Error(err.__class__.__name__, str(err))
    else:
        return map_results

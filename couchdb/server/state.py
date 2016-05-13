# -*- coding: utf-8 -*-
#
import logging

__all__ = ('add_fun', 'add_lib')

log = logging.getLogger(__name__)


def add_fun(server, funsrc):
    """Compiles and adds function to state cache.

    :command: add_fun

    :param server: Query server instance.
    :type server: :class:`~couchdb.server.BaseQueryServer`

    :param funsrc: Python function as source string.
    :type funsrc: basestring

    :return: True
    :rtype: bool
    """
    log.debug('Add new function to server state:\n%s', funsrc)
    if server.version >= (1, 1, 0):
        ddoc = {'views': {'lib': server.state.get('view_lib', '')}}
    else:
        ddoc = None
    server.state['functions'].append(server.compile(funsrc, ddoc))
    server.state['functions_src'].append(funsrc)
    return True


def add_lib(server, lib):
    """Add lib to state which could be used within views that allows usage
    require function within maps one to import shared objects.

    :command: add_lib

    :param server: Query server instance.
    :type server: :class:`~couchdb.server.BaseQueryServer`

    :param lib: Python source code which used require function protocol.
    :type lib: basestring

    :return: True
    :rtype: bool

    .. versionadded:: 1.1.0
    """
    log.debug('Set view_lib:\n%s', lib)
    server.state['view_lib'] = lib
    return True

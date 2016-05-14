# -*- coding: utf-8 -*-
#
import logging

from functools import partial
from types import FunctionType

from couchdb import util
from couchdb.server import mime
from couchdb.server.exceptions import Error, FatalError, QueryServerException

__all__ = ('show', 'list', 'update',
           'show_doc', 'list_begin', 'list_row', 'list_tail',
           'ChunkedResponder')

log = logging.getLogger(__name__)


def apply_context(func, **context):
    globals_ = func.__globals__.copy()
    globals_.update(context)
    func = FunctionType(func.__code__, globals_)
    return func


def maybe_wrap_response(resp):
    if isinstance(resp, util.strbase):
        return {'body': resp}
    else:
        return resp


################################################################################
# Old render used only for 0.9.x
#

def render_function(func, args):
    try:
        resp = maybe_wrap_response(func(*args))
        if isinstance(resp, (dict,) + util.strbase):
            return resp
        else:
            msg = 'Invalid response object %r ; type: %r' % (resp, type(resp))
            log.error(msg)
            raise Error('render_error', msg)
    except QueryServerException:
        raise
    except Exception as err:
        log.exception('Unexpected exception occurred in %s', func)
        raise Error('render_error', str(err))


def response_with(req, responders, mime_provider):
    """Context dispatcher method.

    :param req: Request info.
    :type req: dict

    :param responders: Handlers mapping to mime format.
    :type responders: dict

    :param mime_provider: Mime provider instance.
    :type mime_provider: :class:`~couchdb.server.mime.MimeProvider`

    :return: Response object.
    :rtype: dict
    """
    fallback = responders.pop('fallback', None)
    for key, func in responders.items():
        mime_provider.provides(key, func)
    try:
        resp = maybe_wrap_response(mime_provider.run_provides(req, fallback))
    except Error as err:
        if err.args[0] != 'not_acceptable':
            log.exception('Unexpected error raised:\n'
                          'req: %s\nresponders: %s', req, responders)
            raise
        mimetype = req.get('headers', {}).get('Accept')
        mimetype = req.get('query', {}).get('format', mimetype)
        log.warning('Not acceptable content-type: %s', mimetype)
        return {'code': 406, 'body': 'Not acceptable: {0}'.format(mimetype)}
    else:
        if 'headers' not in resp:
            resp['headers'] = {}
        resp['headers']['Content-Type'] = mime_provider.resp_content_type
        return resp


def show_doc(server, funsrc, doc, req):
    """Implementation of `show_doc` command.

    :command: show_doc

    :param server: Query server instance.
    :type server: :class:`~couchdb.server.BaseQueryServer`

    :param funsrc: Python function source code.
    :type funsrc: basestring

    :param doc: Document object.
    :type doc: dict

    :param req: Request info.
    :type req: dict

    .. versionadded:: 0.9.0
    .. deprecated:: 0.10.0 Use :func:`show` instead.
    """
    mime_provider = mime.MimeProvider()
    context = {
        'response_with': partial(response_with, mime_provider=mime_provider),
        'register_type': mime_provider.register_type
    }
    func = server.compile(funsrc, context=context)
    log.debug('Run show %s\ndoc: %s\nreq: %s\nfunsrc:\n%s',
              func, doc, req, funsrc)
    return render_function(func, [doc, req])


def list_begin(server, head, req):
    """Initiates list rows generation.

    :command: list_begin

    :param server: Query server instance.
    :type server: :class:`~couchdb.server.BaseQueryServer`

    :param head: Headers information.
    :type head: dict

    :param req: Request information.
    :type req: dict

    :return: Response object.
    :rtype: dict

    .. versionadded:: 0.9.0
    .. deprecated:: 0.10.0 Use :func:`list` instead.
    """
    func = server.state['functions'][0]
    server.state['row_line'][func] = {
        'first_key': None,
        'row_number': 0,
        'prev_key': None
    }
    log.debug('Run list begin %s\nhead: %s\nreq: %s', func, head, req)
    func = apply_context(func, response_with=response_with)
    return render_function(func, [head, None, req, None])


def list_row(server, row, req):
    """Generates single list row.

    :command: list_row

    :param server: Query server instance.
    :type server: :class:`~couchdb.server.BaseQueryServer`

    :param row: View result information.
    :type row: dict

    :param req: Request information.
    :type req: dict

    :return: Response object.
    :rtype: dict

    .. versionadded:: 0.9.0
    .. deprecated:: 0.10.0 Use :func:`list` instead.
    """
    func = server.state['functions'][0]
    row_info = server.state['row_line'].get(func, None)
    log.debug('Run list row %s\nrow: %s\nreq: %s', func, row, req)
    func = apply_context(func, response_with=response_with)
    assert row_info is not None
    resp = render_function(func, [None, row, req, row_info])
    if row_info['first_key'] is None:
        row_info['first_key'] = row.get('key')
    row_info['prev_key'] = row.get('key')
    row_info['row_number'] += 1
    server.state['row_line'][func] = row_info
    return resp


def list_tail(server, req):
    """Finishes list result output.

    :command: list_tail

    :param server: Query server instance.
    :type server: :class:`~couchdb.server.BaseQueryServer`

    :param req: Request information.
    :type req: dict

    :return: Response object.
    :rtype: dict

    .. versionadded:: 0.9.0
    .. deprecated:: 0.10.0 Use :func:`list` instead.
    """
    func = server.state['functions'][0]
    row_info = server.state['row_line'].pop(func, None)
    log.debug('Run list row %s\nrow_info: %s\nreq: %s', func, row_info, req)
    func = apply_context(func, response_with=response_with)
    return render_function(func, [None, None, req, row_info])

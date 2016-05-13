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
    except ViewServerException:
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

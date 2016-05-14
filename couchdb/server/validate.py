# -*- coding: utf-8 -*-
#
import logging

from couchdb.server.exceptions import Forbidden, Error, QueryServerException

__all__ = ('validate',)

log = logging.getLogger(__name__)


def handle_error(func, err, userctx):
    if isinstance(err, Forbidden):
        reason = err.args[0]
        log.warning('Access deny: %s\nuserctx: %s\nfunc: %s',
                 reason, userctx, func)
        raise
    elif isinstance(err, AssertionError):
        # This is custom behavior that allows to use assert statement
        # for field validation. It's just quite handy.
        log.warning('Access deny: %s\nuserctx: %s\nfunc: %s',
                 err, userctx, func)
        raise Forbidden(str(err))
    elif isinstance(err, QueryServerException):
        log.exception('%s exception raised by %s',
                      err.__class__.__name__, func)
        raise
    else:
        log.exception('Something went wrong in %s', func)
        raise Error(err.__class__.__name__, str(err))


def run_validate(func, *args):
    log.debug('Run %s for userctx:\n%s', func, args[2])
    try:
        func(*args)
    except Exception as err:
        handle_error(func, err, args[2])
    return 1


def validate(server, funsrc, newdoc, olddoc, userctx):
    """Implementation of `validate` command.

    :command: validate

    :param server: Query server instance.
    :type server: :class:`~couchdb.server.BaseQueryServer`

    :param funsrc: validate_doc_update function source.
    :type funsrc: unicode

    :param newdoc: New document version.
    :type newdoc: dict

    :param olddoc: Stored document version.
    :type olddoc: dict

    :param userctx: User info.
    :type userctx: dict

    :return: 1 (number one)
    :rtype: int

    .. versionadded:: 0.9.0
    .. deprecated:: 0.11.0
        Now is a subcommand of :ref:`ddoc`.
        Use :func:`~couchdb.server.validate.ddoc_validate` instead.
    """
    return run_validate(server.compile(funsrc), newdoc, olddoc, userctx)

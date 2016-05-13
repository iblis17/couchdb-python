# -*- coding: utf-8 -*-
#
import logging

from types import FunctionType

from couchdb.server.exceptions import FatalError, Error

__all__ = ('DDoc',)

log = logging.getLogger(__name__)


class DDoc(object):
    """Design document operation class.

    :param commands: Mapping of commands to their callable handlers. Each
                     command actually is the first item in design function path.
                     See :meth:`run_ddoc_func` for more information.
    :type commands: dict

    :param others: Commands defined in keyword style. Have higher priority above
                   `commands` variable.
    """
    def __init__(self, commands=None, **others):
        if commands is None:
            commands = {}
        assert isinstance(commands, dict)
        commands.update(others)
        self.commands = commands
        self.cache = {}

    def __call__(self, *args, **kwargs):
        return self.process_request(*args, **kwargs)

    def process_request(self, server, cmd, *args):
        """Processes design functions stored within design documents."""
        if cmd == 'new':
            return self.add_ddoc(server, *args)
        else:
            return self.run_ddoc_func(server, cmd, *args)

    def add_ddoc(self, server, ddoc_id, ddoc):
        """
        :param server: Query server instance.
        :type server: :class:`~couchdb.server.BaseQueryServer`

        :param ddoc_id: Design document id.
        :type ddoc_id: unicode

        :param ddoc: Design document itself.
        :type ddoc: dict

        :return: True

        .. versionadded:: 0.11.0
        """
        log.debug('Cache design document `%s`', ddoc_id)
        self.cache[ddoc_id] = ddoc
        return True

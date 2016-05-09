#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Christopher Lenz
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

"""Implementation of a view server for functions written in Python."""
import getopt
import logging
import os
import sys

from couchdb import json
from couchdb.server import SimpleQueryServer

__all__ = ['main', 'run']
__docformat__ = 'restructuredtext en'

log = logging.getLogger('couchdb.server')

_VERSION = """%(name)s - CouchDB Python %(version)s

Copyright (C) 2007 Christopher Lenz <cmlenz@gmx.de>.
"""

_HELP = """Usage: %(name)s [OPTION]

The %(name)s command runs the CouchDB Python query server.

The exit status is 0 for success or 1 for failure.

Options:

  --version               display version information and exit
  -h, --help              display a short help message and exit
  --json-module=<name>    set the JSON module to use ('simplejson', 'cjson',
                          or 'json' are supported)
  --log-file=<file>       name of the file to write log messages to, or '-' to
                          enable logging to the standard error stream
  --log-level=<level>     specify logging level (debug, info, warn, error).
                          Used info level if omitted.
  --allow-get-update      allows GET requests to call update functions.
  --enable-eggs           enables support of eggs as modules.
  --egg-cache=<path>      specifies egg cache dir. If omitted, PYTHON_EGG_CACHE
                          environment variable value would be used or system
                          temporary directory if variable not setted.
  --debug                 enable debug logging; requires --log-file to be
                          specified

Report bugs via the web at <https://github.com/djc/couchdb-python/issues>.
"""


def run(input=sys.stdin, output=sys.stdout, version=None, **config):
    qs = SimpleQueryServer(version, input=input, output=output, **config)
    return qs.serve_forever()


def main():
    """Command-line entry point for running the query server."""
    from couchdb import __version__ as VERSION

    qs_config = {}

    try:
        option_list, argument_list = getopt.gnu_getopt(
            sys.argv[1:], 'h',
            ['version', 'help', 'json-module=', 'debug', 'log-file=',
             'log-level=', 'allow-get-update', 'enable-eggs',
             'egg-cache']
        )

        db_version = None
        message = None

        for option, value in option_list:
            if option in ('--version',):
                message = _VERSION % dict(name=os.path.basename(sys.argv[0]),
                                          version=VERSION)
            elif option in ('-h', '--help'):
                message = _HELP % dict(name=os.path.basename(sys.argv[0]))
            elif option in ('--json-module',):
                json.use(module=value)
            elif option in ('--debug',):
                qs_config['log_level'] = 'DEBUG'
            elif option in ('--log-level',):
                qs_config['log_level'] = value.upper()
            elif option in ('--log-file',):
                qs_config['log_file'] = value
            elif option in ('--allow-get-update',):
                qs_config['allow_get_update'] = True
            elif option in ('--enable-eggs',):
                qs_config['enable_eggs'] = True
            elif option in ('--egg-cache',):
                qs_config['egg_cache'] = value

        if message:
            sys.stdout.write(message)
            sys.stdout.flush()
            sys.exit(0)

    except getopt.GetoptError as error:
        message = '{0}\n\nTry `{1} --help` for more information.\n'.format(
                  str(error), os.path.basename(sys.argv[0]))
        sys.stderr.write(message)
        sys.stderr.flush()
        sys.exit(1)

    sys.exit(run(version=db_version, **qs_config))


if __name__ == '__main__':
    main()

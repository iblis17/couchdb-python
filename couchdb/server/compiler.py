# -*- coding: utf-8 -*-
#
"""Proceeds query server function compilation within special context."""
import base64
import os
import logging
import tempfile

from codecs import BOM_UTF8
from pkgutil import iter_modules
from types import CodeType, FunctionType
from types import ModuleType

from couchdb import json, util
from couchdb.server.exceptions import Error, FatalError, Forbidden

log = logging.getLogger(__name__)


def resolve_module(names, mod, root=None):
    def helper():
        return ('\n    id: %r'
                '\n    names: %r'
                '\n    parent: %r'
                '\n    current: %r'
                '\n    root: %r') % (idx, names, parent, current, root)
    idx = mod.get('id')
    parent = mod.get('parent')
    current = mod.get('current')
    if not names:
        if not isinstance(current, util.strbase + (CodeType, EggExports)):
            raise Error('invalid_require_path',
                        'Must require Python string, code object or egg cache,'
                        ' not %r (at %s)' % (type(current), idx))
        log.debug('Found object by id %s', idx)
        return {
            'current': current,
            'parent': parent,
            'id': idx,
            'exports': {}
        }
    log.debug('Resolving module at %s, remain path: %s', (idx, names))
    name = names.pop(0)
    if not name:
        raise Error('invalid_require_path',
                    'Required path shouldn\'t starts with slash character'
                    ' or contains sequence of slashes.' + helper())
    if name == '..':
        if parent is None or parent.get('parent') is None:
            raise Error('invalid_require_path',
                        'Object %r has no parent.' % idx + helper())
        return resolve_module(names, {
            'id': idx[:idx.rfind('/')],
            'parent': parent.get('parent'),
            'current': parent.get('current'),
        })
    elif name == '.':
        if parent is None:
            raise Error('invalid_require_path',
                        'Object %r has no parent.' % idx + helper())
        return resolve_module(names, {
            'id': idx,
            'parent': parent,
            'current': current,
        })
    elif root:
        idx = None
        mod = {'current': root}
        current = root
    if current is None:
        raise Error('invalid_require_path',
                    'Required module missing.' + helper())
    if name not in current:
        raise Error('invalid_require_path',
                    'Object %r has no property %r' % (idx, name) + helper())
    return resolve_module(names, {
        'current': current[name],
        'parent': mod,
        'id': (idx is not None) and (idx + '/' + name) or name
    })

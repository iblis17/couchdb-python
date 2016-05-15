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


class EggExports(dict):
    """Sentinel for egg export statements."""


def maybe_b64egg(b64str):
    """Checks if passed string is base64 encoded egg file"""
    # Quick and dirty check for base64 encoded zipfile.
    # Saves time and IO operations in most cases.
    return isinstance(b64str, util.strbase) and b64str.startswith('UEsDBBQAAAAIA')


def maybe_export_egg(source, allow_eggs=False, egg_cache=None):
    """Tries to extract export statements from encoded egg"""
    if allow_eggs and maybe_b64egg(source):
        return import_b64egg(source, egg_cache)
    return None


def maybe_compile_function(source):
    """Tries to compile Python source code to bytecode"""
    if isinstance(source, util.strbase):
        return compile_to_bytecode(source)
    return None


def maybe_export_bytecode(source, context):
    """Tries to extract export statements from executed bytecode source"""
    if isinstance(source, CodeType):
        exec(source, context)
        return context.get('exports', {})
    return None


def maybe_export_cached_egg(source):
    """Tries to extract export statements from cached egg namespace"""
    if isinstance(source, EggExports):
        return source
    return None


def cache_to_ddoc(ddoc, path, obj):
    """Cache object to ddoc by specified path"""
    assert path, 'Path should not be empty'
    point = ddoc
    for item in path:
        prev, point = point, point.get(item)
    prev[item] = obj


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


def import_b64egg(b64str, egg_cache=None):
    """Imports top level namespace from base64 encoded egg file.

    For Python 2.4 `setuptools <http://pypi.python.org/pypi/setuptools>`_
    package required.

    :param b64str: Base64 encoded egg file.
    :type b64str: str

    :return: Egg top level namespace or None if egg import disabled.
    :rtype: dict
    """
    if iter_modules is None:
        raise ImportError('No tools available to work with eggs.'
                          ' Probably, setuptools package could solve'
                          ' this problem.')
    egg = None
    egg_path = None
    egg_cache = (egg_cache or
                 os.environ.get('PYTHON_EGG_CACHE') or
                 os.path.join(tempfile.gettempdir(), '.python-eggs'))
    try:
        try:
            if not os.path.exists(egg_cache):
                os.mkdir(egg_cache)
            hegg, egg_path = tempfile.mkstemp(dir=egg_cache)
            egg = os.fdopen(hegg, 'wb')
            egg.write(base64.b64decode(b64str))
            egg.close()
            exports = EggExports(
                [(name, loader.load_module(name))
                 for loader, name, ispkg in iter_modules([egg_path])]
            )
        except:
            log.exception('Egg import failed')
            raise
        else:
            if not exports:
                raise Error('egg_error', 'Nothing to export')
            return exports
    finally:
        if egg_path is not None and os.path.exists(egg_path):
            os.unlink(egg_path)

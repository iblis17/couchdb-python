# -*- coding: utf-8 -*-
#
from inspect import getsource
from textwrap import dedent
from types import FunctionType

from couchdb import util


def maybe_extract_source(fun):
    if isinstance(fun, FunctionType):
        return dedent(getsource(fun))
    elif isinstance(fun, util.strbase):
        return fun
    raise TypeError('Function object or source string expected, got %r' % fun)

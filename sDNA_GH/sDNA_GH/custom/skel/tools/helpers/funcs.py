#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'


import sys
from inspect import getargspec
if sys.version < '3.3':
    from collections import Callable
else:
    from collections.abc import Callable

from sDNA_GH.sDNA_GH.custom.skel.tools.helpers.quacks_like import (quacks_like
                                                                  ,basic_function
                                                                  )
            

def tool_name(tool):
    #type(type[any] / function) -> str
    if hasattr(tool, 'tool_name'):
        return tool.tool_name
    elif hasattr(tool, 'name'):
        return tool.name
    elif hasattr(tool,'__name__'):
        return tool.__name__  
    elif hasattr(tool,'func_name'):
        return tool.func_name
    elif hasattr(tool,'__qualname__'):
        return tool.__qualname__  
    else:
        return tool.__class__.__name__

def get_args(callable):
    if not isinstance(callable, Callable):
        return None
    # assert hasattr(callable, '__call__')
    if (type(f).__name__ == 'function' or
        f.__class__.__name__ == 'function' or
        quacks_like(basic_function)):
        return getargspec(f)
    elif hasattr(f, '__call__'):
        return getargspec(f.__call__)
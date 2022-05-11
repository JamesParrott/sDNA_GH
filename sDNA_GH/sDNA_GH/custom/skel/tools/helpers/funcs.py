#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import inspect
import itertools
from uuid import UUID # Only used for checking str format. 
                      # Haven't tried Iron Python / .Net System.Guid
           

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
        c = inspect.currentframe().f_back.f_locals.items()
        names = [name.strip("'") for name, val in c if val is tool]  
        return names[0]



def is_uuid(val):
    try:
        UUID(str(val))
        return True
    except ValueError:
        return False
#https://stackoverflow.com/questions/19989481/how-to-determine-if-a-string-is-a-valid-v4-uuid

if hasattr(itertools, 'pairwise'):
    pairwise = itertools.pairwise
else:
    #https://docs.python.org/2.7/library/itertools.html
    def pairwise(iterable):
        "s -> (s0,s1), (s1,s2), (s2, s3), ..."
        a, b = itertools.tee(iterable)
        next(b, None)
        return itertools.izip(a, b)

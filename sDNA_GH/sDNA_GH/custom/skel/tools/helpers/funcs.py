#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'


from uuid import UUID
           

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


def is_uuid(val):
    try:
        UUID(str(val))
        return True
    except ValueError:
        return False
#https://stackoverflow.com/questions/19989481/how-to-determine-if-a-string-is-a-valid-v4-uuid

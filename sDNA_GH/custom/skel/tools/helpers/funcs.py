#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import os
import inspect
from uuid import UUID # Only used for checking str format. 
                      # Iron Python/GhPython System.Guid is an option in .Net
    

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


def windows_installation_paths(names):
    #type(str/Sequence(str)) -> list(str)
    """ Constructs a list of possible installation paths on Windows for an 
        unlocated app named name.

        e.g. returns [r'C:\' + name
                     ,r'C:\Program Files\' + name
                     ,r'C:\Program Files (x86)\' + name
                     ,r'C:\Users\James\AppData\Roaming\' + name
                     ] 
        and any paths on the system path with name as a substring. 
    """
    if isinstance(names, str):
        names = [names]
    paths = []
    for name in names:
        paths += [os.path.join(os.getenv('SYSTEMDRIVE'), os.sep, name)]# r'C:\' + name
        paths += [os.path.join(os.getenv('PROGRAMFILES'), name)]
        paths += [os.path.join(os.getenv('PROGRAMFILES(X86)'), name)]
        paths += [os.path.join(os.getenv('APPDATA'),name)]
        paths += list(path 
                    for path in os.getenv('PATH').split(';')
                    if name in path 
                    )   
    return paths         
# https://docs.microsoft.com/en-us/windows/deployment/usmt/usmt-recognized-environment-variables

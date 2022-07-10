#! /usr/bin/python
# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) [2021] [Cardiff University, a body incorporated
# by Royal Charter and a registered charity (number:
# 1136855) whose administrative offices are at 7th floor 30-
# 36 Newport Road, University CF24 0DE, Wales, UK]

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__author__ = 'James Parrott'
__version__ = '0.06'

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
    """ Yields possible installation paths on Windows for an 
        un-located app named name.

        for each name in names, yields:
            all paths on the system path with name as a substring
            'C:\' + name
            r'C:\Program Files\' + name
            r'C:\Program Files (x86)\' + name
            e.g. r'C:\Users\USER_NAME\AppData\Roaming\' + name

    """
    if isinstance(names, str):
        names = [names]
    for name in names:
        for path in os.getenv('PATH').split(';'):
            if name in path:
                yield path 
        yield os.path.join(os.getenv('SYSTEMDRIVE'), os.sep, name)# r'C:\' + name
        # os.sep is needed.  os.getenv('SYSTEMDRIVE') returns c: on Windows.
        #                    assert os.path.join('c:', 'foo') == 'c:foo'
        yield os.path.join(os.getenv('PROGRAMFILES'), name)
        yield os.path.join(os.getenv('PROGRAMFILES(X86)'), name)
        yield os.path.join(os.getenv('APPDATA'), name)
# https://docs.microsoft.com/en-us/windows/deployment/usmt/usmt-recognized-environment-variables

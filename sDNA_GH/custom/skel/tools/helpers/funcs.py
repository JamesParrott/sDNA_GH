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
__version__ = '0.12'

import os
import logging
import itertools
import functools
import collections
from collections import OrderedDict
if hasattr(collections, 'Callable'):
    Callable = collections.Callable
else:
    import collections.abc  
    Callable = collections.abc.Callable
import inspect
from uuid import UUID # Only used for checking str format. 
                      # Iron Python/GhPython System.Guid is an option in .Net

try:
    basestring #type: ignore
except NameError:
    basestring = str
    
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


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

hexit = r'[0-9A-Fa-f]'
uuid_pattern = r'%s{8}-%s{4}-%s{4}-%s{4}-%s{12}' % ((hexit,)*5)

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
    if isinstance(names, basestring):
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
        yield os.path.join(os.getenv('LOCALAPPDATA'), name)
        yield os.path.join(os.getenv('LOCALAPPDATA'), 'Programs', name)
        # e.g. for one user: C:\Users\James\AppData\Local\Programs\sDNA\
# https://docs.microsoft.com/en-us/windows/deployment/usmt/usmt-recognized-environment-variables


def make_regex(pattern):
    # type (str) -> str
    """ Makes a regex from its 'opposite'/'inverse': a format string.  
        Escapes special characters.
        Turns format string fields: {name} 
        into regex named capturing groups: (?P<name>.*) 
    """
    
    the_specials = '.^$*+?[]|():!#<='
    #escape special characters
    for c in the_specials:
        pattern = pattern.replace(c,'\\' + c)

    # turn all named fields '{name}' in the format string 
    # into named capturing groups r'(?P<name>.*)' in a regex
    pattern = pattern.replace( '{', r'(?P<' ).replace( '}', r'>.*)' )

    # Anchor to beginning and end.
    return r'\A' + pattern + r'\Z'
    

def list_of_lists(iterable):
    #type(Iterable[Iterable]) -> list[list]
    return [list(item) for item in iterable]

if not hasattr(itertools, 'zip_longest'):
   itertools.zip_longest = itertools.izip_longest

if hasattr(itertools, 'pairwise'):
   pairwise = itertools.pairwise
else:
    #https://docs.python.org/2.7/library/itertools.html
    def pairwise(iterable):
        "s -> (s0,s1), (s1,s2), (s2, s3), ..."
        a, b = itertools.tee(iterable)
        next(b, None)
        return itertools.izip(a, b)
    itertools.pairwise = pairwise


def classes_from_grouped_keyed_items(
                     items
                    ,key_func = lambda x : isinstance(x, tuple) and len(x) == 2
                    ,manglers = {True : lambda x: [OrderedDict(x)]
                                ,False: lambda x: [OrderedDict(y) for y in x]
                                }
                    ):
    #type(Iterable, type[any] | function, function, dict) -> list
    """ Manglers needs a function for each value of key_func takes for each of items. """
    keys_and_groups = itertools.groupby(items, key_func)
    for key, group in keys_and_groups:
        yield manglers[key](group)


def compose(*funcs):
    #type(*functions) -> function
    if len(funcs) <= 1:
        msg = 'Need two or more functions to compose.'
        logger.error(msg)
        raise ValueError(msg)
    bad_funcs = [func for func in funcs 
                      if not isinstance(func, Callable)] 
    if bad_funcs:
        msg = 'Can only compose callables, e.g. functions.  Not callable: %s'
        msg %= bad_funcs
        logger.error(msg)
        raise TypeError(msg)
    return functools.reduce(lambda f, g: lambda x: f(g(x)), funcs)

# already_warned = False

# if not already_warned:
#     already_warned = True
#     msg = ('Entry with multiple shapes found. '
#         +'Geom will be a DataTree, not a list.'
#         )
#     logger.warning(msg)
#     warnings.warn(msg)
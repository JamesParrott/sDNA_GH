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
__version__ = '3.0.0.alpha_1'

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
    #type(str/Sequence(str)) -> Iterator(str)
    r""" Yields possible installation paths on Windows for an 
        un-located app named name.

        for each name in names, yields:
            all paths on the system path with name as a substring
            r'C:' + '\\' name
            r'C:\Program Files' + '\\'name
            r'C:\Program Files (x86)' + '\\'name
            e.g. r'C:\Users\USER_NAME\AppData\Roaming' + '\\'name

    """
    if isinstance(names, basestring):
        names = [names]
    for name in names:
        for path in os.getenv('PATH').split(';'):
            if name in path:
                yield path 
        yield os.path.join(os.getenv('LOCALAPPDATA'), 'Programs', name)
        yield os.path.join(os.getenv('LOCALAPPDATA'), name)
        yield os.path.join(os.getenv('APPDATA'), name)
        yield os.path.join(os.getenv('PROGRAMFILES(X86)'), name)
        yield os.path.join(os.getenv('PROGRAMFILES'), name)
        yield os.path.join(os.getenv('SYSTEMDRIVE'), os.sep, name)# r'C:\' + name
        # os.sep is needed.  os.getenv('SYSTEMDRIVE') returns c: on Windows.
        #                    assert os.path.join('c:', 'foo') == 'c:foo'
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


def ensure_3D(lists):
    #type(List[List[Number]]) -> List[List[Number]]
    """ Appends 0 to lists of two numbers in a list of list of numbers. 
    
        Mutates: lists 
        Returns: lists
    """
    for list_ in lists:
        if len(list_) == 2:
            list_.append(0)
    return lists


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


def multi_item_unpacking_iterator(
                     items
                    ,is_single_item
                    ,manglers
                    ):
    #type(Iterable, Callable, dict) -> list
    keys_and_groups = itertools.groupby(items, key = is_single_item)
    for key, group in keys_and_groups:
        if key: #assert all(is_single_item(x) for x in group)
            yield manglers[key](group) # group of single items
        else: #assert all(not is_single_item(x) for x in group)
            for sub_group in group:
                yield manglers[key](sub_group)


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


def first_of_each(seqs):
    #type(Iterable) -> Iterable
    """ Returns the first item of each tuple from an iterable of Sequences. """
    return (seq[0] for seq in seqs)


def get_main_else_get_aliases(dict_, main, aliases, fallback_value = None, mangler = None):
    #type(dict, Hashable, *Hashable, type[any]) -> type[any]
    """ Returns mangler(value) in dict_ for a key's main name, if in dict_.  
        Otherwise returns mangler(value) for any alias key in aliases in dict_.  
        Otherwise returns fallback_value.  
        
        Mutates: dict_"""
    import itertools
    for key in itertools.chain([main], aliases):
        if key in dict_ and dict_[key] is not None:
            retval = dict_.pop(key) # intentional pop - f_name back in dict
            if mangler is not None:
                retval = mangler(retval)
            return retval 
    return fallback_value # intentionally un-mangled.

#! /usr/bin/awk NR==3
# -*- coding: utf-8 -*-
# This module requires Grasshopper Python (Rhino3D)

# MIT License

# Copyright (c) [2021] [Cardiff University, a body incorporated
# by Royal Charter and a registered charity (number:
# 1136855) whose administrative offices are at 7th floor 30-
# 36 Newport Road, UniversityCF24 0DE, Wales, UK]

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
__version__ = '0.02'

import os
import logging
import collections
if hasattr(collections, 'Iterable'):
    Iterable = collections.Iterable 
else:
    import collections.abc
    Iterable = collections.abc.Iterable
import re

import GhPython
import System.Drawing  # .Net / C# Classes.
                       # System is in Iron Python.  But System.Drawing is not.

from .basic.ghdoc import ghdoc
from .tools import runner
from . import add_params


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def make_component(name
                  ,category
                  ,subcategory
                  ,launcher_code
                  ,position
                  ,SDK_not_script = True
                  ,locked = True
                  ):
    # type(str, str, str, str, list) -> None
    new_comp = GhPython.Component.ZuiPythonComponent()

    #new_comp.CopyFrom(this_comp)
    sizeF = System.Drawing.SizeF(*position)

    new_comp.Attributes.Pivot = System.Drawing.PointF.Add(new_comp.Attributes.Pivot, sizeF)
    

    new_comp.Code = launcher_code
    new_comp.NickName = name
    new_comp.Name = name
    new_comp.Params.Clear()
    new_comp.IsAdvancedMode = SDK_not_script
    new_comp.Category = category 
 
    new_comp.SubCategory = subcategory 
    new_comp.Locked = locked


    GH_doc = ghdoc.Component.Attributes.Owner.OnPingDocument()
    success = GH_doc.AddObject(docObject = new_comp, update = False)
    return success

class ComponentsBuilder(add_params.ToolWithParams, runner.RunnableTool): 
    component_inputs = ('code','plug_in', 'component_names', 'name_map', 'categories', 'd_h', 'w')

    def __call__(self
                ,code
                ,plug_in_name
                ,names
                ,name_map
                ,categories
                ,readme_file = None
                ,d_h = None
                ,w = None
                ):
        #type(str, dict) -> None
        # = (kwargs[k] for k in self.args)
        d_h = 175 if d_h is None else d_h
        w = 800 if w is None else w
        
        while (isinstance(code, Iterable) 
               and not isinstance(code, str)):
            code = code[0]

        if (readme_file is None or 
            not isinstance(readme_file, str) or 
            not os.path.isfile(readme_file)):
            #
            readme = ''
        else:
            with open(readme_file, 'r') as f:
                readme = ''.join(f.readlines())

        logger.debug('readme[:20] == %s' % readme[:20])


        names_built = []
        tool_code = code
        doc_string_summary_line_pattern = re.compile(r'"""(.*?)\r?\n"""'
                                                    ,flags = re.DOTALL
                                                    )
        # code comes from a Grasshopper file reader component, so in windows
        # line endings include '\r\n' - '\r' is not removed, unlike open(..., 'r')

        doc_string_start_match = doc_string_summary_line_pattern.search( code )
        if doc_string_start_match:
            old_doc_string_start = doc_string_start_match.groups()[0]
            logger.debug('old_doc_string_start == %s' % old_doc_string_start)
            doc_string_start = doc_string_start_match.group()
            logger.debug('doc_string_match == %s' % doc_string_start)
        else:
            logger.debug('No regex match found for docstring in launcher code.')
        #raise Exception('Break point')


        for i, name in enumerate(names):
            if name_map.get(name, name) not in categories:
                msg =  'No category for ' + name
                logging.error(msg)
                raise ValueError(msg)
            else:

                i *= d_h
                position = [200 + (i % w), 550 + 220*(i // w)]
                subcategory = categories.get(name_map.get(name, name), '')
                logger.debug('Building tool with (nick)name = %s' % name)
                if readme:
                    tool_name = name_map.get(name, name)
                    logger.debug('Looking in readme for tool with name = %s' % tool_name)

                    tool_summary_pattern = re.compile(r'\(%s\)\r?\n(.*?)(\r?\n){3}' % tool_name
                                                     ,flags = re.DOTALL
                                                     )
                    logger.debug('tool_summary_pattern == %s' % tool_summary_pattern.pattern)

                    summary_match = tool_summary_pattern.search( readme )
                    if summary_match:
                        summary = summary_match.groups()[0]
                        logger.debug('summary == %s' % summary)
                        tool_code = code.replace(old_doc_string_start, summary)
                        logger.debug('tool_code[:2400] == %s' % tool_code[:2400])
                    else:
                        tool_code = code
                        logger.debug('tool_code unchanged.')
                success = make_component(name
                                        ,category = plug_in_name
                                        ,subcategory = subcategory
                                        ,launcher_code = tool_code
                                        ,position = position
                                        )
                if success:
                    names_built += [name]

        retcode = 0
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)
    
    retvals = ('retcode', 'names_built')



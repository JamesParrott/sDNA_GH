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


import logging
import collections
if hasattr(collections, 'Iterable'):
    Iterable = collections.Iterable 
else:
    import collections.abc
    Iterable = collections.abc.Iterable

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





        names_built = []
        for i, name in enumerate(names):
            #if name_map.get(name, name) not in categories:
            #   msg =  'No category for ' + name
            #   logging.error(msg)
            #   raise ValueError(msg)
            #else:
                i *= d_h
                position = [200 + (i % w), 550 + 220*(i // w)]
                subcategory = categories.get(name_map.get(name, name), '')
                success = make_component(name
                                        ,category = plug_in_name
                                        ,subcategory = subcategory
                                        ,launcher_code = code
                                        ,position = position
                                        )
                if success:
                    names_built += [name]

        retcode = 0
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)
    
    retvals = ('retcode', 'names_built')



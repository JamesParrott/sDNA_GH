#! /usr/bin/ipy
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys, logging
if sys.version < '3.3':
    from collections import Iterable
else:
    from collections.abc import Iterable

import GhPython
from System.Drawing import SizeF, PointF   # .Net Classes, e.g. via Iron Python.

from .tools.helpers.classes import Tool
from .basic.ghdoc import ghdoc


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def make_new_component(name
                      ,category
                      ,subcategory
                      ,launcher_code
                      ,position
                      ):
    # type(str, str, str, str, list) -> None
    new_comp = GhPython.Component.ZuiPythonComponent()

    #new_comp.CopyFrom(this_comp)
    sizeF = SizeF(*position)

    new_comp.Attributes.Pivot = PointF.Add(new_comp.Attributes.Pivot, sizeF)
    

    new_comp.Code = launcher_code
    new_comp.NickName = name
    new_comp.Name = name
    new_comp.Params.Clear()
    new_comp.IsAdvancedMode = True
    new_comp.Category = category 
 
    new_comp.SubCategory = subcategory 

    GH_doc = ghdoc.Component.Attributes.Owner.OnPingDocument()
    GH_doc.AddObject(new_comp, False)

class BuildComponents(Tool): 
    args = ('launcher_code', 'plug_in', 'component_names', 'd_h', 'w')
    component_inputs = ('go',) + args[1:-2] + ('name_map', 'categories')

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

 
        #retcode, names  = return_component_names(opts_at_call)
        #names now from param input

        nicknameless_names = [name for name in names 
                                   if all(name != var and name not in var 
                                                  for var in name_map.values()
                                         )
                             ]

        for i, name in enumerate(set(list(name_map.keys()) + nicknameless_names)):
            #if name_map.get(name, name) not in categories:
            #   msg =  'No category for ' + name
            #   logging.error(msg)
            #   raise ValueError(msg)
            #else:
                i *= d_h
                position = [200 + (i % w), 550 + 220*(i // w)]
                subcategory = categories.get(name_map.get(name, name), '')
                make_new_component(name
                                  ,category = plug_in_name
                                  ,subcategory = subcategory
                                  ,launcher_code = code
                                  ,position = position
                                  )

        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    retvals = ('retcode',)



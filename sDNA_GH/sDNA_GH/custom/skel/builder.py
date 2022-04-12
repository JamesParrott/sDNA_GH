#! /usr/bin/ipy
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys, logging
if sys.version < '3.3':
    from collections import Hashable, Iterable, MutableMapping
else:
    from collections.abc import Hashable, Iterable, MutableMapping

import GhPython
from System import SizeF, PointF   # .Net Classes, e.g. via Iron Python.

from .tools.helpers.classes import Tool
from ..skel.basic.GH_env import ghdoc


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def make_new_component(name
                      ,category
                      ,subcategory
                      ,launcher_code
                      ,this_comp
                      ,position
                      ):
    comp = GhPython.Component.ZuiPythonComponent()
    
    #comp.CopyFrom(this_comp)
    sizeF = SizeF(*position)

    comp.Attributes.Pivot = PointF.Add(comp.Attributes.Pivot, sizeF)
    

    comp.Code = launcher_code
    #comp.NickName = name
    comp.Params.Clear()
    comp.IsAdvancedMode = True
    comp.Category = category
    comp.SubCategory = subcategory

    GH_doc = this_comp.OnPingDocument()
    GH_doc.AddObject(comp, False)

class BuildComponents(Tool): 
    args = ('launcher_code', 'plug_in', 'component_names', 'opts', 'd_h', 'w')
    component_inputs = ('go',) + args[1:-2] + ('name_map', 'categories')

    def __call__(self, code, plug_in_name, names, opts_at_call, d_h = None, w = None):
        #type(str, dict) -> None
        # = (kwargs[k] for k in self.args)
        d_h = 175 if d_h is None else d_h
        w = 800 if w is None else w
        
        while (isinstance(code, Iterable) 
               and not isinstance(code, str)):
            code = code[0]

        global module_opts
        module_opts['options']._replace(auto_get_Geom = False
                                ,auto_read_Usertext = False
                                ,auto_write_new_Shp_file = False
                                ,auto_read_Shp = False
                                ,auto_plot_data = False
                                )

        metas = opts_at_call['metas']

        sDNAUISpec = opts_at_call['options'].sDNAUISpec
        categories = {Tool.__name__ : Tool.category for Tool in sDNAUISpec.get_tools()}
        categories.update(metas.categories._asdict())

        name_map = metas.name_map._asdict()

        #retcode, names  = return_component_names(opts_at_call)
        #names now from param input

        nicknameless_names = [name for name in names 
                                   if all(name != var and name not in var 
                                                  for var in name_map.values
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
                new_comp = GhPython.Component.ZuiPythonComponent()
    
                #new_comp.CopyFrom(this_comp)
                sizeF = SizeF(*position)

                new_comp.Attributes.Pivot = PointF.Add(new_comp.Attributes.Pivot, sizeF)
                

                new_comp.Code = code
                new_comp.NickName = name
                new_comp.Name = name
                new_comp.Params.Clear()
                new_comp.IsAdvancedMode = True
                new_comp.Category = plug_in_name #'sDNA'
                if name_map.get(name, name) in categories:
                    new_comp.SubCategory = categories[name_map.get(name, name)]

                GH_doc = ghdoc.Component.Attributes.Owner.OnPingDocument()
                GH_doc.AddObject(new_comp, False)

        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    retvals = ('retcode',)


    show = dict(Input = component_inputs
               ,Output = ('OK',) + retvals[1:]    
               )
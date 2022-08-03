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
__version__ = '0.08'


import os
import logging
from collections import OrderedDict
import System  #.Net from IronPython

import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

from ...basic.ghdoc import ghdoc

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class NullPathError(Exception):
    pass


def get_path(fallback = None, inst = None):
    #type(dict, type[any]) -> str
    #refers to `magic' global ghdoc so needs to 
    # be in module scope (imported above)
    
    path_getters = [lambda : Rhino.RhinoDoc.ActiveDoc.Path
                   ,lambda : ghdoc.Path
                   ,lambda : inst.ghdoc.Path  #e.g. via old Component decorator
                   ,lambda : sc.doc.Path
                   ,lambda : fallback
                   ]
    path = None
    for path_getter in path_getters:
        try:
            path = path_getter()
        except AttributeError:
            continue
        if isinstance(path, str) and (os.path.isfile(path) or os.path.isdir(path)):
            return path 
    return None 


def toggle_sc_doc():
    #type() -> None
    if sc.doc not in (Rhino.RhinoDoc.ActiveDoc, ghdoc): 
        # ActiveDoc may change on Macs 
        msg = 'sc.doc == %s , type == %s ' % (sc.doc, type(sc.doc))
        logger.error(msg)
        raise NameError(msg)
    sc.doc = Rhino.RhinoDoc.ActiveDoc if sc.doc == ghdoc else ghdoc # type: ignore


def change_line_thickness(obj, width, rel_or_abs = False):  
    #type(str, Number, bool) -> None
    #
    # The default value in Rhino for wireframes is zero so rel_or_abs==True 
    # will not be effective if the width has not already been increased.
    #
    # To make changes resulting from the function visible, it is necessary
    # to change the view mode into PrintDisplay, e.g. by calling
    # rs.Command('_PrintDisplay _State=_On Color=Display Thickness='
    #                +str(options.line_width)
    #                +' _enter')
    
    x = rs.coercerhinoobject(obj, True, True)
    x.Attributes.PlotWeightSource = Rhino.DocObjects.ObjectPlotWeightSource.PlotWeightFromObject
    if rel_or_abs:
        width = width * x.Attributes.PlotWeight
    x.Attributes.PlotWeight = width
    x.CommitChanges()


def multi_context_checker(is_thing):
    #type(function, function) -> function
    def get_sc_doc_of_thing(x):
        #type(str)-> bool  
        if x:
            if is_thing(x):
                return sc.doc
            else:
                toggle_sc_doc()
                if is_thing(x):
                    return sc.doc
            return False
    return get_sc_doc_of_thing


@multi_context_checker
def get_sc_doc_of_obj(x):
    #type(str) -> bool
    return bool(sc.doc.Objects.FindGeometry(System.Guid(str(x)))) if x else False 


@multi_context_checker
def get_sc_doc_of_curve(x):
    #type(str) -> bool
    return rs.IsCurve(x) if x else False
 

def get_obj_keys(obj):
    # type(str) -> list
    return rs.GetUserText(obj)


def get_obj_val(obj, key):
    # type(str, str) -> str
    return rs.GetUserText(obj, key)


def write_obj_val(obj, key, val):
    # type(str, str) -> str
    return rs.SetUserText(obj, key, val, False)


def get_val_list(val_getter = get_obj_val):
    # type(function) -> function
    def f(obj, keys):
        # type(str, list) -> list

        return [val_getter(obj, key) for key in keys]
    return f


def get_OrderedDict( keys_getter = get_obj_keys
                    ,val_getter = get_obj_val):
    # type(function) -> function
    def g(z):
        if hasattr(Rhino.Geometry, type(z).__name__):
            z_geom = z
        else:
            z = System.Guid(str(z))
            z_geom = Rhino.RhinoDoc.ActiveDoc.Objects.FindGeometry(z)
            if not z_geom:
                z_geom = ghdoc.Objects.FindGeometry(z)
        # if hasattr(z_geom,'TryGetPolyline'):
        #     z_geom = z_geom.TryGetPolyline()[1]
        name_val_map = z_geom.GetUserStrings() #.Net str only dict
        # assert isinstance(name_val_map, System.Collections.Specialized.NameValueCollection)
        return OrderedDict( [  (key, name_val_map.Get(key)) 
                                    for key in name_val_map.AllKeys  ] )
    return g



@multi_context_checker
def get_sc_doc_of_group(x):
    #type( str ) -> boolean
    return rs.IsGroup(x) if x else False


def get_all_groups():
    #type( None ) -> list
    return rs.GroupNames()


def get_members_of_a_group(group):
    #type(str) -> list
    return rs.ObjectsByGroup(group)



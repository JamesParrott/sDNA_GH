#! Grasshopper Python
# -*- coding: utf-8 -*-

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
            pass
        if isinstance(path, str) and os.path.isfile(path):
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
    # to change the view mode into PrintDistplat, e.g. by calling
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

    #return rs.IsObject(x) if x else False
    #return bool(sc.doc.Objects.FindGeometry(x)) if x else False 
    #return bool(sc.doc.Objects.FindGeometry(System.Guid(x))) if x else False 
    #logger.debug(str(x))
    # logger.debug('str(x): %s ' % x))
    # logger.debug('System.Guid(x): ')
    # logger.debug(System.Guid(x))
    # logger.debug('x.ToString(): ')
    # logger.debug(x.ToString())
    # logger.debug('To Guid')
    # logger.debug(System.Guid(x.ToString()))
    # logger.debug('Check: ')
    # return bool(sc.doc.Objects.FindGeometry(System.Guid(x.ToString()))) if x else False 

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
    def f(obj):
        # type(str, list) -> list
        #if is_a_curve_in_GH_or_Rhino(obj):
        target_doc = get_sc_doc_of_obj(obj)    
        if target_doc:
            sc.doc = target_doc        
            keys = keys_getter(obj)
            return OrderedDict( (key, val_getter(obj, key)) for key in keys)
        else:
            return OrderedDict()
    return f

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



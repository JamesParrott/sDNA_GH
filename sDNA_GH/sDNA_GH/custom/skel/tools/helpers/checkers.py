#! Grasshopper Python
# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict
import System  #.Net from IronPython

import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

from ...basic.ghdoc import ghdoc

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def toggle_sc_doc():
    #type() -> None
    if sc.doc not in (Rhino.RhinoDoc.ActiveDoc, ghdoc): 
        # ActiveDoc may change on Macs 
        msg = 'sc.doc == ' + str(sc.doc) + ' type == ' + str(type(sc.doc))
        logger.error(msg)
        raise NameError(msg)
    sc.doc = Rhino.RhinoDoc.ActiveDoc if sc.doc == ghdoc else ghdoc # type: ignore

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
    #return rs.IsObject(x)
    return bool(sc.doc.Objects.FindGeometry(System.Guid(str(x)))) if x else False
    #return bool(sc.doc.Objects.FindGeometry(x)) if x else False 

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




import logging
from collections import OrderedDict

import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

from ...basic.ghdoc import ghdoc

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def multi_context_checker(is_thing, toggle_context):
    #type(function, function) -> function
    def context_toggling_is_thing_checker(x):
        #type(str)-> bool  
        if x:
            if is_thing(x):
                return sc.doc
            else:
                toggle_context()
                if is_thing(x):
                    return sc.doc
            return False
    return context_toggling_is_thing_checker

def toggle_Rhino_GH_file_target():
    #type() -> None
    if sc.doc not in (Rhino.RhinoDoc.ActiveDoc, ghdoc): 
        # ActiveDoc may change on Macs 
        msg = 'sc.doc == ' + str(sc.doc) + ' type == ' + str(type(sc.doc))
        logger.error(msg)
        raise NameError(msg)
    sc.doc = Rhino.RhinoDoc.ActiveDoc if sc.doc == ghdoc else ghdoc # type: ignore

def is_obj(x):
    #type(str) -> bool
    #return rs.IsObject(x)
    return bool(sc.doc.Objects.FindGeometry(x)) if x else False

    
is_an_obj_in_GH_or_Rhino = multi_context_checker(is_obj, toggle_Rhino_GH_file_target)

def is_curve(x):
    #type(str) -> bool
    return rs.IsCurve(x) if x else False

is_a_curve_in_GH_or_Rhino = multi_context_checker(is_curve, toggle_Rhino_GH_file_target)



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
        target_doc = is_an_obj_in_GH_or_Rhino(obj)    
        if target_doc:
            sc.doc = target_doc        
            keys = keys_getter(obj)
            return OrderedDict( (key, val_getter(obj, key)) for key in keys)
        else:
            return OrderedDict()
    return f

def is_group(x):
    #type( str ) -> boolean
    return rs.IsGroup(x) if x else False

is_a_group_in_GH_or_Rhino = multi_context_checker(is_group, toggle_Rhino_GH_file_target)

def get_all_groups():
    #type( None ) -> list
    return rs.GroupNames()

def get_members_of_a_group(group):
    #type(str) -> list
    return rs.ObjectsByGroup(group)



#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys, logging
from collections import OrderedDict
from itertools import chain, repeat, izip
if sys.version < '3.3':
    from collections import Iterable 
else:
    from collections.abc import Iterable

import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
from ghpythonlib import treehelpers as th
from Grasshopper import DataTree

from ..launcher import Output, Debugger
from .skel.tools.helpers.funcs import is_uuid
from .skel.basic.ghdoc import ghdoc
from .pyshp_wrapper import (create_new_groups_layer_from_points_list
                           ,get_all_shp_type_Rhino_objects
                           ,check_is_specified_obj_type
                           )

#import logging
logger = logging.getLogger(__name__).addHandler(logging.NullHandler())
#logger = logging.getLogger(__name__)

output = Output(tmp_logs = [], logger = logger)
debug = Debugger(output)

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
        raise NameError(output('sc.doc == ' 
                            + str(sc.doc) 
                            + ' type == ' 
                            + str(type(sc.doc)) 
                            +' ','ERROR'))
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


def make_obj_key(x, *args):
    # type(str) -> str
    return x  #.ToString()  # Group names do also 
                         # have a ToString() method, even 
                         # though they're already strings

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






def make_gdm(main_iterable
            ,object_hasher = make_obj_key
            ): 
    #type(namedtuple, function, function)-> dict   

    gdm = OrderedDict( (object_hasher(obj, d), d)  
                       for obj, d in main_iterable
                     )


    return gdm
    
def try_to_make_dict_else_leave_alone(list_of_key_list_and_val_list):
    if len(list_of_key_list_and_val_list)>=2:
        if len(list_of_key_list_and_val_list) > 2:
            output( 'More than 2 items in list of keys and values. '
                   +'  Assuming'
                   +'first two are keys and vals.  '
                   +'Discarding subsequent items in list (this item).  '
                   ,'WARNING')
        return OrderedDict(zip(list_of_key_list_and_val_list[:2]))
    else:
        return list_of_key_list_and_val_list







def convert_dictionary_to_data_tree_or_lists(nested_dict):
    # type(dict) -> DataTree
    if all(isinstance(val, dict) for val in nested_dict.values()):    
        User_Text_Keys = [ list(group_dict.keys()) # list() for Python 3
                        for group_dict in nested_dict.values()
                        ]
        #In the current source ghpythonlib.treehelpers.list_to_tree only uses len()
        # and loops over the list.  Tested: Calling with a tuple returns a Datatree.
        #It does not check it really is a list - any iterable with len should be fine.
        #TODO!!!!!   Keys and Values???!!!  Just want the val from Data
        User_Text_Values = [ list(group_dict.values()) # list() for Python 3
                            for group_dict in nested_dict.values()
                            ]
        
        Data =  th.list_to_tree([[User_Text_Keys, User_Text_Values]])
    else:
        Data = nested_dict.values()
    Geometry = nested_dict.keys()  # Multi-polyline-groups aren't unpacked.
    return Data, Geometry
    #layerTree = []


def override_gdm_with_gdm(lesser, override, opts):  
    #type(dict, dict, dict) -> dict
    # overwrite ?
    # call update on the sub dicts?:
    #debug(lesser)
    #debug(override)

    if not lesser:
        lesser = OrderedDict()
    #debug(lesser)
    if opts['options'].merge_Usertext_subdicts_instead_of_overwriting:
        debug('Merging gdms.  ')
        for key in override:
            if   key in lesser and all(
                 isinstance(override[key], dict)
                ,isinstance(lesser[key], dict)   ):
                lesser[key].update(override[key])
            else:
                lesser[key] = override[key]
    else:
        lesser.update(**override)
    #debug(lesser)
    return lesser







def get_shape_file_rec_ID(options): 
    #type(namedtuple) -> function
    def f(obj, rec):
        #debug(obj)
        #debug(type(obj).__name__)
        if is_uuid(obj):
            target_doc = is_an_obj_in_GH_or_Rhino(obj)    
            if target_doc:
                sc.doc = target_doc
                # and is_an_obj_in_GH_or_Rhino(obj):
                return make_obj_key(obj)
        if hasattr(rec, 'as_dict'):
            d = rec.as_dict()
            if options.uuid_shp_file_field_name in d:
                obj_ID = d[options.uuid_shp_file_field_name]     
                #debug(obj_ID)
                # For future use.  Not possible until sDNA round trips through
                # Userdata into the output .shp file, including our uuid
                target_doc = is_an_obj_in_GH_or_Rhino(obj_ID)    
                if target_doc:
                    sc.doc = target_doc
                    return obj_ID
                #if (is_an_obj_in_GH_or_Rhino(obj_ID) or 
                #    is_a_group_in_GH_or_Rhino(obj_ID) ):
                #    return obj_ID
        g = create_new_groups_layer_from_points_list(options)
        return g(obj, rec)
    return f    


def get_objs_and_OrderedDicts(options #= module_opts['options']
                             ,all_objs_getter = get_all_shp_type_Rhino_objects
                             ,group_getter = get_all_groups
                             ,group_objs_getter = get_members_of_a_group
                             ,OrderedDict_getter = get_OrderedDict()
                             ,obj_type_checker = check_is_specified_obj_type
                             ):
    #type(function, function, function) -> function
    shp_type = options.shp_file_shape_type            
    def generator():
        #type( type[any]) -> list, list
        #
        # Groups first search.  If a special Usertext key on member objects 
        # is used to indicate groups, then an objects first search 
        # is necessary instead, to test every object for membership
        # and track the groups yielded to date, in place of group_getter
        objs_in_any_group = []

        if options.include_groups_in_gdms:
            groups = group_getter()
            for group in groups:
                objs = group_objs_getter(group)
                if ( objs and
                    any(obj_type_checker(x, shp_type) 
                                                for x in objs) ):                                                 
                    objs_in_any_group += objs
                    d = {}
                    for obj in objs:
                        d.update(OrderedDict_getter(obj))
                    yield group, d

        objs = all_objs_getter(shp_type)
        for obj in objs:
            if ((not options.include_groups_in_gdms) or 
                 obj not in objs_in_any_group):
                d = OrderedDict_getter(obj)
                yield obj, d
        return  # For the avoidance of doubt

    return generator()

##########################################################################################################

def convert_Data_tree_and_Geom_list_to_gdm(Geom, Data, options):
    # type (type[any], list, dict)-> dict
    
    #debug(Geom)
    if Geom in [None, [None]]:
        debug(' No Geom. Processing Data only ')
        Geom = []


    #debug(Geom)
    #debug(sc.doc)

    if isinstance(Geom, str) or not isinstance(Geom, Iterable):
        debug('Listifying Geom.  ')
        Geom = [Geom]
    elif (isinstance(Geom, list) 
          and len(Geom) >= 1 and
          isinstance(Geom[0], list)):
        if len(Geom) > 1:
            output('List found in element 1 of Geom.  '
                   +'Discarding Elements 2 onwards.'
                   ,'WARNING')
        Geom = Geom[0]

    # This check won't allow legend tags through so is too strong for
    # this stage.  Let later functions and checks handle invalid geometry
    #if  any( not is_an_obj_in_GH_or_Rhino(x) 
    #         and not is_a_group_in_GH_or_Rhino(x) 
    #                                for x in Geom ):
    #    debug('Is an obj[0] doc == ' + str(is_an_obj_in_GH_or_Rhino(Geom[0])))
    #   #debug(sc.doc)
    #
    #    debug('Is a group[0] doc == ' + str(is_a_group_in_GH_or_Rhino(Geom[0])))
    #    #debug(sc.doc)
    #    raise ValueError(output( 'Invalid obj in Geom:  ' 
    #           +' '.join([str(x) for x in Geom if not is_an_obj_in_GH_or_Rhino(x)
    #                                          and not is_a_group_in_GH_or_Rhino(x)]) 
    #           ,'ERROR'))

    # 
    debug(Data)
    if (Data in [[], None, [None]] or
        getattr(Data,'BranchCount',999)==0):
        Data = OrderedDict()
    elif (isinstance(Data, DataTree[object]) 
          and getattr(Data, 'BranchCount', 0) > 0):
        debug('Datatree inputted to Data.  Converting....  ')
        Data = th.tree_to_list(Data)
    elif not isinstance(Data, list):
        debug('Listifying Data.  ')
        Data = [Data]
        # Tuples don't get split over multiple geometric objects

    while len(Data)==1 and isinstance(Data[0], list):
        Data=Data[0]
    
    if  ( len(Data) >= 2 and
          isinstance(Data[0], list) and
          isinstance(Data[1], list) and  # constructing keys and vals is possible
          ( len(Data[0]) == len(Data[1]) == len(Geom) or  #clear obj-> (key, val) correspondence
            len(Geom) != len(Data) ) # No possible 1-1 correspondence on all of Data
        ):
        if len(Data) > 2:
            output(  'Data tree has more than two branches.  '
                    +'Using first two for keys and vals.  '
                    ,'WARNING'
                  )
        key_lists = Data[0]
        val_lists = Data[1]
        Data = [  OrderedDict(zip(key_list, val_list)) for key_list, val_list in 
                                            izip(key_lists, val_lists)  
               ]

        # Else treat as a list of values
        # with no keys, the
        # same as any other list below:


    #debug('Data == ' + str(Data))
    debug('len(Geom) == ' + str(len(Geom)))
    debug('len(Data) == ' + str(len(Data)))

    #print Geom
    #print Data

    if len(Geom) < len(Data):
        #print('More values in Data list than Geometry. Storing excess '
        #       +'values from Data with key tuple(). '
        #       )#,'INFO')
        component_inputs_gen_exp =  chain( izip(Geom, Data[:len(Geom)])
                                          ,[(tuple(), Data[len(Geom):])]
                                          )
        #print('Chaining worked')
    else:
        if len(Geom) > len(Data):
            debug('repeating OrderedDict() after Data... ')
            Data = chain( Data,  repeat(OrderedDict()) )
        else:
            debug( "Data and Geom equal length.  " )
        component_inputs_gen_exp =  izip(Geom, Data)





    #component_inputs_gen_exp =  izip(Geom, Data)



    geom_data_map = make_gdm(component_inputs_gen_exp  
                            ,make_obj_key
                            )

    #geom_data_map = make_gdm( izip(Geom, imap( izip, key_lists, val_lists)), make_obj_key)

    #debug(geom_data_map)

    return geom_data_map
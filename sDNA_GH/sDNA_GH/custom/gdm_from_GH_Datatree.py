#! Grasshopper Python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys
import logging
from collections import OrderedDict
import itertools
if sys.version < '3.3':
    from collections import Iterable 
else:
    from collections.abc import Iterable

import rhinoscriptsyntax as rs
from ghpythonlib import treehelpers as th
from Grasshopper import DataTree



logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())





def make_gdm(main_iterable): 
    #type(namedtuple)-> dict   

    gdm = OrderedDict( (obj, d)  
                       for obj, d in main_iterable
                     )


    return gdm
    
def dict_from_key_val_lists(key_val_lists):
    #type(list(list(keys), list(values))) -> dict / list
    if len(key_val_lists)>=2:
        if len(key_val_lists) > 2:
            logger.warning('More than 2 items in list of keys and values. '
                           +'  Assuming'
                           +'first two are keys and vals.  '
                           +'Discarding subsequent items in list (this item).  '
                           )
        return OrderedDict(zip(key_val_lists[:2]))
    else:
        return key_val_lists







def dict_from_DataTree_and_lists(nested_dict):
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


def override_gdm(lesser, override, merge_subdicts = True):  
    #type(dict, dict, dict) -> dict
    # overwrite ?
    # call update on the sub dicts?:


    if not lesser:
        lesser = OrderedDict()
    if merge_subdicts:# :
        logger.debug('Merging gdms.  ')
        for key in override:
            if (key in lesser
                and isinstance(override[key], dict)
                and isinstance(lesser[key], dict)   ):
                lesser[key].update(override[key])
            else:
                lesser[key] = override[key]
    else:
        lesser.update(**override)
    return lesser











##########################################################################################################

def gdm_from_DataTree_and_list(Geom, Data):
    # type (type[any], list, dict)-> dict
    
    if Geom in [None, [None]]:
        logger.debug(' No Geom. Processing Data only ')
        Geom = []



    if isinstance(Geom, str) or not isinstance(Geom, Iterable):
        logger.debug('Listifying Geom.  ')
        Geom = [Geom]
    elif (isinstance(Geom, list) 
          and len(Geom) >= 1 and
          isinstance(Geom[0], list)):
        if len(Geom) > 1:
            logger.warning('List found in element 1 of Geom.  '
                           +'Discarding Elements 2 onwards.'
                           )
        Geom = Geom[0]

    # This check won't allow legend tags through so is too strong for
    # this stage.  Let later functions and checks handle invalid geometry
    #if  any( not is_an_obj_in_GH_or_Rhino(x) 
    #         and not is_a_group_in_GH_or_Rhino(x) 
    #                                for x in Geom ):
    #    raise ValueError(logger.exception( 'Invalid obj in Geom:  ' 
    #           +' '.join([str(x) for x in Geom if not is_an_obj_in_GH_or_Rhino(x)
    #                                          and not is_a_group_in_GH_or_Rhino(x)]) 
    #           ,'ERROR'))

    # 
    logger.debug(str(Data))
    if (Data in [[], None, [None]] or
        getattr(Data,'BranchCount',999)==0):
        Data = OrderedDict()
    elif (isinstance(Data, DataTree[object]) 
          and getattr(Data, 'BranchCount', 0) > 0):
        logger.debug('Datatree inputted to Data.  Converting....  ')
        Data = th.tree_to_list(Data)
    elif not isinstance(Data, list):
        logger.debug('Listifying Data.  ')
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
            logger.warning('Data tree has more than two branches.  '
                          +'Using first two for keys and vals.  '
                          )
        key_lists = Data[0]
        val_lists = Data[1]
        Data = [  OrderedDict(zip(key_list, val_list)) for key_list, val_list in 
                                            itertools.izip(key_lists, val_lists)  
               ]

        # Else treat as a list of values
        # with no keys, the
        # same as any other list below:


    logger.debug('len(Geom) == ' + str(len(Geom)))
    logger.debug('len(Data) == ' + str(len(Data)))


    if len(Geom) < len(Data):

        component_inputs_gen_exp =  itertools.chain( itertools.izip(Geom
                                                                   ,Data[:len(Geom)]
                                                                   )
                                                   ,[ (tuple(), Data[len(Geom):]) ]
                                                   )
    else:
        if len(Geom) > len(Data):
            logger.debug('repeating OrderedDict() after Data... ')
            Data = itertools.chain( Data,  itertools.repeat(OrderedDict()) )
        else:
            logger.debug( "Data and Geom equal length.  " )
        component_inputs_gen_exp =  itertools.izip(Geom, Data)





    #component_inputs_gen_exp =  izip(Geom, Data)



    geom_data_map = make_gdm(component_inputs_gen_exp  
                            )

    #geom_data_map = make_gdm( izip(Geom, imap( izip, key_lists, val_lists)), make_obj_key)


    return geom_data_map

def is_selected(obj):
    return rs.IsObjectSelected(obj)

def obj_layer(obj):
    return rs.ObjectLayer(obj)
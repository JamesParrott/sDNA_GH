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
__version__ = '2.6.0'


import logging
import itertools
import collections
if hasattr(collections, 'Iterable'):
    Iterable = collections.Iterable 
else:
    import collections.abc
    Iterable = collections.abc.Iterable
import warnings

import Rhino
import Grasshopper
import rhinoscriptsyntax as rs
from ghpythonlib import treehelpers as tree_helpers

from .skel.tools.helpers import rhino_gh_geom


try:
    basestring #type: ignore
except NameError:
    basestring = str
    
OrderedDict = collections.OrderedDict

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def remove_outer_length_one_lists(obj):
    #type( type[any] -> type[any])
    if not isinstance(obj, list):
        return obj
    while len(obj)==1 and isinstance(obj[0], list):
        obj=obj[0]
    return obj


def str_Rhino_objs(Geom):
    #type(Iterable -> Iterator)
    for obj in Geom:
        if isinstance(obj, basestring):
            yield obj
            continue

        __, source = rhino_gh_geom.get_geom_and_source_else_leave(obj)
        if source is Rhino.RhinoDoc.ActiveDoc:
            yield str(obj)
            continue

        yield obj



class GeomDataMapping(OrderedDict):
    """ Primary intermediate data structure of sDNA_GH, mapping 
        strings of references to Rhino geometric objects, or 
        actual Grasshopper geometric objects (uuids) to string 
        keyed sub-dictionaries of data suitable for User Text.  
    """

    def __init__(self, keys_and_vals=()): 
        #type(*Iterable)-> dict   
        """ The keys should be Rhino or Grasshopper geometric objects,
            or strings matching the uuid pattern.  The values should 
            also be a dictionary, string keyed, containing associated 
            data usable as for User Text.

            If keys_and_vals is a generator expression it should be 
            exhausted (if creation of the actual Rhino/Grasshopper 
            objects referred to by the keys is a desired side effect).
        """
        super(GeomDataMapping, self).__init__(keys_and_vals)


    @staticmethod
    def from_DataTree_and_list(Geom, Data):
        # type (type[any], list, dict)-> dict
        
        if Geom in [None, [None]]:
            logger.debug(' No Geom. Processing Data only ')
            Geom = []



        if isinstance(Geom, basestring) or not isinstance(Geom, Iterable):
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

        # This check won't allow legend tags through. Later functions 
        # must handle invalid geometry
        # 
        logger.debug(str(Data))
        if (Data in [[], None, [None]] or
            getattr(Data,'BranchCount',999)==0):
            Data = OrderedDict()
        elif (isinstance(Data, Grasshopper.DataTree[object]) 
            and getattr(Data, 'BranchCount', 0) > 0):
            logger.debug('Datatree inputted to Data.  Converting....  ')
            Data = tree_helpers.tree_to_list(Data)
        elif not isinstance(Data, list):
            logger.debug('Listifying Data.  ')
            Data = [Data]
            # Tuples don't get split over multiple geometric objects

        Data = remove_outer_length_one_lists(Data)
        
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
            Data = [OrderedDict(zip(key_list, val_list)) 
                    for key_list, val_list in itertools.izip(key_lists, val_lists)  
                   ]

            # Else treat as a list of values
            # with no keys, the
            # same as any other list below:


        logger.debug('len(Geom) == %s' % len(Geom))
        logger.debug('len(Data) == %s' % len(Data))



        if len(Geom) < len(Data):

            component_inputs_gen_exp =  itertools.chain( 
                                                itertools.izip(str_Rhino_objs(Geom)
                                                              ,Data[:len(Geom)]
                                                              )
                                               ,[(tuple(), Data[len(Geom):])]
                                               )
            logger.warning('More Data than Geom.  Assigning list of '
                          +'surplus Data items to the empty tuple key. ')
        else:
            if len(Geom) > len(Data):
                logger.debug('repeating OrderedDict() after Data... ')
            else:
                logger.debug( "Data and Geom equal length.  " )
            component_inputs_gen_exp =  itertools.zip_longest(
                                                     str_Rhino_objs(Geom)
                                                    ,Data
                                                    ,fillvalue = OrderedDict()
                                                    )



        return GeomDataMapping(component_inputs_gen_exp) 



def is_gdm(x):
    return isinstance(x, GeomDataMapping)

def make_list_of_gdms(items
                     ,is_multiple_shapes = is_gdm
                     ,prepare_object_and_data = lambda x : x
                     ):
    #type(Iterable, function, function) -> list
    retval = []
    keys_and_groups = itertools.groupby(items, is_multiple_shapes)
    already_warned = False
    for key, group in keys_and_groups:
        if key: 
            # assert all(is_multiple_shapes(x) for x in group)
            if not already_warned:
                already_warned = True
                msg = ('Entry with multiple shapes found. '
                    +'Geom will be a DataTree, not a list.'
                    )
                logger.warning(msg)
                warnings.warn(msg)
            retval.extend(group) # group is iterable of gdms
        else:
            retval.append(GeomDataMapping(group))
    return retval


    

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


def nested_lists_of_keys_and_values_or_values(dict_):
    #type(dict) -> list
    User_Text_Keys = [list(group_dict.keys()) # list() for Python 3
                        for group_dict in dict_.values()
                        ]
    User_Text_Values = [list(group_dict.values()) # list() for Python 3
                        for group_dict in dict_.values()
                        ]
    return [User_Text_Keys, User_Text_Values]



def DataTree_and_list_from_dict(nested_dict):
    # type(dict) -> Grasshopper.DataTree[object], list
    if all(isinstance(val, dict) for val in nested_dict.values()):    
        # User_Text_Keys = [list(group_dict.keys()) # list() for Python 3
        #                   for group_dict in nested_dict.values()
        #                  ]
        # #In the current source ghpythonlib.treehelpers.list_to_tree only uses len()
        # # and loops over the list.  Tested: Calling with a tuple returns a Datatree.
        # #It does not check it really is a list - any iterable with len should be fine.
        # User_Text_Values = [list(group_dict.values()) # list() for Python 3
        #                     for group_dict in nested_dict.values()
        #                    ]
        
        Data =  tree_helpers.list_to_tree([nested_lists_of_keys_and_values_or_values(nested_dict)])
    else:
        Data = list(nested_dict.values())
    Geometry = nested_dict.keys()  # Multi-polyline-groups aren't unpacked.
    return Data, Geometry
    #layerTree = []

def keys_and_values_lists_if_nested_dict_else_values(dict_):
    if all(isinstance(val, dict) for val in dict_.values()):
        return nested_lists_of_keys_and_values_or_values(dict_) 
    return list(dict_.values())

def shallowest_data_tree(list_):
    #type(list) -> Grasshopper.DataTree[object]
    list_ = remove_outer_length_one_lists(list_)
    return tree_helpers.list_to_tree(list_)

def Data_Tree_and_Data_Tree_from_dicts(dicts):
    #type(Iterable[dict])-> Grasshopper.DataTree[object], Grasshopper.DataTree[object]
    if isinstance(dicts, dict):
        dicts = [dicts]
    # if all(all(isinstance(val, dict) for val in dict_.values())
    #        for dict_ in dicts):
    #     #
    #     Data = tree_helpers.list_to_tree(
    #         [nested_lists_of_keys_and_values_or_values(dict_) 
    #          for dict_ in dicts_1
    #         ]
    #     )
    # else:
    #     Data = [list(dict_.values()) for dict_ in dicts]
    
    Data = [keys_and_values_lists_if_nested_dict_else_values(dict_)
            for dict_ in dicts
           ]
    Geometry = [list(dict_.keys()) for dict_ in dicts]
    ret = shallowest_data_tree(Data)

    return ret, shallowest_data_tree(Geometry)
        




def override_gdm(lesser, override, merge_subdicts = True):  
    #type(dict, dict, dict) -> dict
    # overwrite ?
    # call update on the sub dicts?:


    if not lesser:
        lesser = GeomDataMapping()
    logger.debug('Overriding gdm with gdms.  ')
    for key, val in override.items():
        if (merge_subdicts and
            key in lesser and
            isinstance(val, dict) and
            isinstance(lesser[key], dict)):
            #
            lesser[key].update(val)
        else:
            lesser[key] = val.copy() if isinstance(val, dict) else val
    return lesser




def is_selected(obj):
    return rs.IsObjectSelected(obj)

def obj_layer(obj):
    return rs.ObjectLayer(obj)

def doc_layers(sort = False):
    return rs.LayerNames(sort)
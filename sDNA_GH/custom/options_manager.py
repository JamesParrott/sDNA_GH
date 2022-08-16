#! /usr/bin/python
# -*- coding: utf-8 -*-

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
__version__ = '0.09'
"""
Functions to override namedtuples, from dicts, toml files 
and other named tuples e.g. for options data structures.

There is no module logger, as other loggers themselves may be 
configured from options calculated from this module.  Logs go to 
the root logger with the default settings
from logging (i.e. to stderr for >= warning, into the void otherwise).
"""

import sys
import os
import logging
import collections
if hasattr(collections, 'Sequence'):
    Sequence = collections.Sequence 
else:
    import collections.abc
    Sequence = collections.abc.Sequence
if hasattr(collections, 'Set'):
    Set = collections.Set 
else:
    import collections.abc
    Set = collections.abc.Set
from numbers import Number

from ..third_party import toml


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

try:
    basestring #type: ignore
except NameError:
    basestring = str

OrderedDict = collections.OrderedDict

def isnamedtuple(obj):
    #type(type[any]) -> bool
    return isinstance(obj, tuple) and hasattr(obj, '_fields')

def attrs(X):
    return [attr for attr in dir(X) if not attr.startswith('_')]

def any_clashes(X,Y):
    return any(attr in attrs(X) for attr in attrs(Y))


def get_BaseOptsClass(**kwargs):
    #type(dict) -> type[any]
    class BaseOptsClass(object):
        pass
    for k, v in kwargs.items():
        setattr(BaseOptsClass, k, v)
    return BaseOptsClass

def get_dict_of_Classes(**kwargs):
    #type( dict(str: dict) ) -> dict(str : type[any])
    return OrderedDict( (key, get_BaseOptsClass(**val)) 
                        for (key, val) in kwargs.items() 
                      )

def namedtuple_from_class(Class, name = None):
    # type: ( type[any], str) -> collections.namedtuple
    #https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code
    if name is None:
        name = 'NT_' + Class.__name__
    fields_dict = OrderedDict(  (attr, getattr(Class, attr) )
                                for attr in dir(Class) 
                                if not attr.startswith('_')
                             )  
    factory = collections.namedtuple(name, fields_dict.keys(), rename = True)   
    return factory(**fields_dict)



def list_contains(check_list, name, name_map):
    # type( MyComponent, list(str), str, dict(str, str) ) -> bool
    #name_map
    return name in check_list or (name in name_map._fields and 
                                  getattr(name_map, name) in check_list
                                  )
    #return name in check_list or (name in name_map and name_map[name] in check_list)


def no_name_clashes(name_map, list_of_names_lists):
    #type( MyComponent, dict(str, str), list(str) ) -> bool

    num_names = sum(len(names_list) for names_list in list_of_names_lists)

    super_set = set(name for names_list in list_of_names_lists 
                         for name in names_list
                   )
    # Check no duplicated name entries in list_of_names_lists.
    if set(['options', 'metas']) & super_set:
        return False  # Clashes with internal reserved names.  Still best avoided even though tool options
                      # are now a level below (under the sDNA version key)
    return num_names == len(super_set) and not any([x == getattr(name_map, x) 
                                                   for x in name_map._fields])  
                                                   # No trivial cycles


def namedtuple_from_dict(d
                        ,NT_name
                        ,strict = True
                        ,class_prefix = 'NT_'
                        ,convert_subdicts = False
                        ,**kwargs
                        ):
    #type (dict, str, str) -> namedtuple(d), tree (Class)
    #
    if strict and not isinstance(d, dict):
        return None
    d = d.copy() 
    for key, val in d.items():
        if isinstance(val, dict) and convert_subdicts:
            d[key] = namedtuple_from_dict(val
                                         ,key
                                         ,False # strict. already checked 
                                         ,class_prefix
                                         ,**kwargs
                                         )  

    return collections.namedtuple(class_prefix + NT_name
                                 ,d.keys()
                                 ,rename=False 
                                 )(**d)  # Don't return nt class

def delistify_vals_if_not_list_in(d_lesser, d_greater): 
    #type(dict, dict) -> None   
    """ Changes d_greater's values that are lists to their first element,
        unless the corresponding value with the same key in d_lesser is
        already a list.
        Mutates d_greater.  d_lesser unaltered. 
    """
    for key, val in d_greater.items():
        if isinstance(val, list) and (  key not in d_lesser 
            or not isinstance(d_lesser[key], list)  ):
            d_greater[key]=val[0]


def is_instance_of_Class_of(x, y):
    #type: (type[any], type[any]) -> bool
    return isinstance(x, y.__class__)


def is_instance_of_Class_of_item_of(x, y):
    #type: (type[any], type[any]) -> bool
    return isinstance(y, (Sequence, Set)) and any(is_instance_of_Class_of(x, z) 
                                                  for z in y
                                                 )


def override_dict_key_val_generator(d_lesser
                                   ,od_greater
                                   ,check_types = False
                                   ,delistify = True
                                   ,add_new_opts = False
                                   ,allow_containers = True
                                   ,hush_type_error = False
                                   ,**kwargs
                                   ):
    #type: (dict, OrderedDict, bool, bool, bool, bool, bool, dict) -> tuple

    for key in od_greater:
        val = od_greater[key]  #we may change val, so don't loop over .items()

        if key not in d_lesser:
            if add_new_opts:
                yield key, val
            continue
        assert key in d_lesser, ("key: %s not in d_lesser.keys(): %s" 
                                 % (key, d_lesser.keys()))

        if (delistify and 
            isinstance(val, list) and 
            not isinstance(d_lesser[key], list)):
            #
            val = val[0]
        
        print('isinstance(d_lesser[key], Sentinel) == %s' % isinstance(d_lesser[key], Sentinel))

        if (check_types and 
            d_lesser[key] is not None and 
            not isinstance(d_lesser[key], Sentinel) and
            # set default to None to allow override to be of any type
            not is_instance_of_Class_of(val, d_lesser[key]) and 
            (not allow_containers or
            not is_instance_of_Class_of_item_of(val, d_lesser[key]))):
            #val is mistyped

            if hush_type_error:
                msg = 'Skipping key: %s from override as val == %s is not an instance of: %s, '
                msg = msg % (key, val, d_lesser[key])
                msg += 'and is not an instance of the Class of any of its elements (if any)'
                logger.warning(msg)
                continue
            
            msg = 'Option: %s needs to be instance of type: %s, '
            msg += 'or an instance of the Class of one of its elements (if any).'
            msg += ' Type supplied: %s (val == %s)' 
            msg = msg % (key, d_lesser[key].__class__, val.__class__, val)
            logger.error(msg)
            raise TypeError(msg)
        
        yield key, val


def override_OrderedDict_with_dict(d_lesser
                                  ,od_greater
                                  ,strict = True
                                  ,check_types = False
                                  ,delistify = True
                                  ,add_new_opts = False
                                  ,allow_containers = True
                                  ,hush_type_error = False
                                  ,**kwargs
                                  ):
    #type: (dict, OrderedDict, bool, bool, bool, bool, bool, bool, dict) -> OrderedDict
    #
    d_lesser = d_lesser.copy()


    if strict and not isinstance(od_greater, dict):  # also true for OrderedDict
        return d_lesser


    d_lesser.update( override_dict_key_val_generator(d_lesser
                                                    ,od_greater
                                                    ,check_types
                                                    ,delistify
                                                    ,add_new_opts
                                                    ,allow_containers
                                                    ,hush_type_error
                                                    ,**kwargs)
                   )

    return d_lesser



def override_namedtuple_with_dict(nt_lesser
                                 ,d_greater
                                 ,strict = True
                                 ,check_types = True  #types of dict values
                                 ,delistify = True
                                 ,**kwargs
                                 ):  
    #type (namedtuple, dict, Boolean, Boolean, Boolean) -> namedtuple
    #

    if strict and not isinstance(d_greater, dict):
        return nt_lesser
    elif set(d_greater.keys()).issubset(nt_lesser._fields) and not check_types:  
        #.viewkeys doesn't have .issubset method ipy 2.7
        if delistify:
            delistify_vals_if_not_list_in(nt_lesser._asdict(), d_greater)
        return nt_lesser._replace(**d_greater)
    else:
        newDict = override_OrderedDict_with_dict(nt_lesser._asdict()
                                                ,d_greater
                                                ,strict
                                                ,check_types
                                                ,delistify
                                                ,**kwargs
                                                )

        return namedtuple_from_dict(newDict
                                   ,nt_lesser.__class__.__name__
                                   ,strict
                                   ,''   # NT Class name prefix
                                   ,**kwargs
                                   ) 


def override_namedtuple_with_namedtuple(nt_lesser
                                       ,nt_greater
                                       ,strict = True        # strictly enforce (opts) 
                                       ,**kwargs
                                       ):  
    #type (namedtuple, namedtuple, Boolean, Boolean, Boolean, function) -> namedtuple
    if strict and not isinstance(nt_greater, nt_lesser.__class__):
        return nt_lesser
    else:
        return override_namedtuple_with_dict(nt_lesser
                                            ,nt_greater._asdict()
                                            ,strict = False
                                            ,**kwargs
                                            )



toml_types = [bool, basestring, Number, tuple, list, dict]


def save_toml_file(file_name, d):
    #type(str, dict) -> None
    """ Saves a dictionary to a toml file.  Toml specifies the utf-8 encoding."""
    with open(file_name, 'w') as f:
        toml.dump(d, f)


def load_toml_file(config_path = os.path.join(sys.path[0], 'config.toml')
                  ,**kwargs
                  ):
    #type (namedtuple, str) -> namedtuple

    """ Loads a toml file as a dictionary.  Trivial wrapper, to accept kwargs.
    
    https://github.com/uiri/toml/blob/master/toml/decoder.py

    Please note, .toml tables are mapped correctly to OrderedDictionaries
    by the line below.  But if convert_subdicts is False, then this dict is
    passed into override_namedtuple, and will pass up through the normal 
    hierarchy of functions in this options_manager module, finally having 
    make_nested_namedtuple called on it, turning the .toml table
    into a namedtuple."""
    return toml.load(config_path, _dict = OrderedDict)


override_funcs_dict = {  dict : override_namedtuple_with_dict  }


def override_namedtuple(nt_lesser
                       ,overrides_list
                       ,override_funcs_dict = override_funcs_dict
                       ,**kwargs
                       ):                        
    # type(namedtuple, list(object), dict, dict) -> namedtuple
    """ Override an nt, from a list of dicts, toml and nt.
    
    Full function hierarchy kwargs
    kwargs: {make_nested_namedtuple : {strict = True, class_prefix = 'C_', convert_subdicts is False}
             override_ordereddict_with_dict : {strict = True, check_types = False, delistify = True, add_new_opts = True}
             override_namedtuple_with_dict {strict = True, check_types = False, delistify = True}
             override_namedtuple_with_namedtuple{strict = True}
             override_namedtuple : {override_funcs_dict : None => { dict : override_namedtuple_with_dict 
                                                                   ,None : lambda greater, lesser, *args : lesser
                                                                   ,nt_lesser.__class__ : override_namedtuple_with_namedtuple}
              }
    """

    if not isinstance(overrides_list, list):
        overrides_list=[overrides_list]
    
    if not isinstance(override_funcs_dict, dict):
        msg =  'override_funcs_dict is a ' + type(override_funcs_dict).__name__
        msg += ', not a dictionary.  '
        if hasattr(override_funcs_dict, 'items'):
            msg += 'Relying on duck-typing.  '
            logging.warning(msg)
        else:
            msg += '.items() method required.  '
            logging.error(msg)
            raise TypeError(msg)
    
    
    def get_nt_overrider_func(override, nt_lesser):
        #type(type[any], namedtuple) -> function
        if isinstance(override, basestring):
            if override.endswith('.toml'):
                msg = 'Call load_toml_file first and add dict to overrides'
                logging.error(msg)
                raise NotImplementedError(msg)

        if isinstance(override, nt_lesser.__class__):
            return override_namedtuple_with_namedtuple  

        for key, val in override_funcs_dict.items():
            if isinstance(override, key):
                #print('returning val == %s' % val)
                return val 
        
        if hasattr(override, '_asdict'):
            logging.warning('Duck-typing override as namedtuple.  Calling' 
                           +type(override).__name__ + '._asdict' 
                           +' to coerce to ordered dict.' 
                           )
            return override_namedtuple_with_namedtuple  

        msg = 'Overrider func not found for override type: '
        msg += type(override).__name__
        logging.error(msg)
        raise NotImplementedError(msg)


    for override in overrides_list:
        if override: # != None:
            overrider_func = get_nt_overrider_func(override, nt_lesser)
            nt_lesser = overrider_func( nt_lesser, override, **kwargs ) 


    return nt_lesser

class Sentinel(object):
    def __init__(self, message):
        self.message = message
    def __repr__(self):
        return 'Sentinel("' + self.message + '")'

#TODO:  Make bool(Sentinel) False optionally, and fail louder on iteration.

def error_raising_sentinel_factory(warning
                                  ,message
                                  ,extra_dunders = ('call','getitem','setitem'
                                                   , 'hash','len','iter'
                                                   ,'delattr','delete'
                                                   #,'get', 'set', 'setattr'
                                                   )
                                  ,leave_alone = ('init','repr','message'
                                                 # leaving repr the same as 
                                                 # Sentinel makes it
                                                 # printable.
                                                 ,'weakref','module','class'
                                                 ,'dict' ,'new','metaclass'
                                                 ,'subclasshook','mro','bases'
                                                 ,'getattr','getattribute'
                                                 ,'dir'
                                                 )
                                  ):
    #type(str, str, tuple, tuple) -> type[any]
    def raise_error(*args):
        raise ValueError(warning) 
    class NewSentinel(Sentinel):
        def __getattribute__(self, name):
            if name.strip('_') not in leave_alone:
                return raise_error()
            return object.__getattribute__(self, name)
    for name in list(extra_dunders):
        if name not in leave_alone:
            setattr(NewSentinel, '__' + name + '__', raise_error)
        
    return NewSentinel(message)
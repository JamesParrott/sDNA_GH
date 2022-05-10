#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'
"""
Functions to override namedtuples, from dicts, ini files, toml files 
and other named tuples e.g. for options data structures.

There is no logger in this module, as loggers themselves may be 
configured from options calculated from this module.  Logs go to the default
from logging (i.e. to stderr for >= warning, into the void otherwise).
"""

import sys
import os
import logging
from collections import namedtuple, OrderedDict
# https://docs.python.org/2.7/library/collections.html#collections.namedtuple
if sys.version_info.major >= 3: 
    import configparser as ConfigParser # Python 3
else:   
    import ConfigParser # Python 2

from ..third_party.toml import decoder


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
    # type: ( type[any], str) -> namedtuple
    #https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code
    if name is None:
        name = 'NT_' + Class.__name__
    fields = [attr for attr in dir(Class) if not attr.startswith('_')]
    factory = namedtuple(name, fields, rename=True)   
    return factory(**{x : getattr(Class, x) for x in fields})



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
                        ,d_namedtuple_class_name
                        ,strict = True
                        ,class_prefix = 'NamedTuple_'
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

    return namedtuple(class_prefix + d_namedtuple_class_name
                     ,d.keys()
                     ,rename=False 
                     )(**d)  # Don't return nt class

def delistify_vals_if_not_list_in(d_lesser, d_greater): 
    #type(dict, dict) -> None   # Mutates d_greater.  d_lesser unaltered.
        for key, val in d_greater.items():
            if isinstance(val, list) and (  key not in d_lesser 
                or not isinstance(d_lesser[key], list)  ):
               d_greater[key]=val[0]


def override_OrderedDict_with_dict( d_lesser
                                  ,od_greater
                                  ,strict = True
                                  ,check_types = False
                                  ,delistify = True
                                  ,add_new_opts = False
                                  ,**kwargs
                                  ):
    #type: (dict, OrderedDict, bool, bool, bool, bool, dict) -> OrderedDict
    #
    if strict and not isinstance(od_greater, dict):  # also true for OrderedDict
        return d_lesser

    if not add_new_opts:
        new_od = OrderedDict( (key, val) 
                   for key, val in od_greater.items() 
                   if key in d_lesser )
    else: 
        new_od = od_greater.copy() 
    
    if delistify:
        delistify_vals_if_not_list_in(d_lesser, new_od)

    if check_types:
        for key in d_lesser.viewkeys() & new_od:  #.keys():
            if (         d_lesser[key]  is not None       
                and type(d_lesser[key]) != type(new_od[key])   ):
                del new_od[key]

    if sys.version_info.major > 3 or (    sys.version_info.major == 3 
                                  and sys.version_info.minor >= 9 ):
        return d_lesser | new_od    # I like this! :)  There's otherwise no 
                                    # need to check >= Python 3.9
                                    # n.b. dict key insertion order guaranteed
                                    # to be preserved >= Python 3.7
    else:
        return OrderedDict(d_lesser, **new_od)      
            # Arguments must be string-keyed PEP 0584
            # The values of od_greater take priority if the keys clash
            # But the order of the keys is as for d_lesser (Iron Python 2.7.11)
            #
            # Extra keys in new_od are added to d_lesser

    # PEP 0584
    # PEP 468
    # https://docs.python.org/3/library/collections.html#collections.OrderedDict

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

def readline_generator(fp):
    yield '[DEFAULT]'
    from re import match
    line = fp.readline()             # Snippet modified to skip .ini file section headers.  
    while line:                      # https://docs.python.org/3.10/library/configparser.html#configparser.ConfigParser.readfp
        if not match(r'\[.*', line):  # we could -only ignore- '[...]' instead of anything that starts with '[.....' but 
                                        # best not to have to worry about how ConfigParser will deal with '[.....' & no ']'
                                        # re.match only matches from the beginning, so we don't need \A as with re.search
            yield line
        line = fp.readline()
    fp.close()
    yield ''

def load_ini_file( file_path
                 ,dump_all_in_default_section = False
                 ,empty_lines_in_values = False
                 ,interpolation = None
                 ,**kwargs
                 ):
    if not os.path.isfile(file_path):
        return None
    else:
        if sys.version_info.major >= 3 : # version > '3':   # if Python 3
            config = ConfigParser.ConfigParser(empty_lines_in_values, interpolation)
        else:   # e.g.  Python 2
            config = ConfigParser.RawConfigParser()   # to turn off interpolation.  Python 3 documentation implies RawConfigParser is 
                                                    # unsafe, so 
                                                    # we have wrapped it in this function to limit its scope 
    
    if dump_all_in_default_section:
        f = open(file_path,'rU')
        f_gen = readline_generator(f)

        if sys.version_info.major < 3 or (sys.version_info.major ==3 and sys.version_info.minor < 2) :  
            class G(object):
                pass
            G.readline = f_gen.next
            config.readfp(G)
        #  ConfigParser.readfp deprecated in Python 3.2 but read_file not available before then
        else:
            config.read_file(f_gen)

    else:
        result = config.read(file_path)
        if not result:
            return None

    return config

def get_coercer(old_val
               ,config
               ,d = None
               ,**kwargs
               ):
    # type (any, Class, dict) -> function
    if ( d is None or not isinstance(d, dict) 
         or any(not isinstance(k, type) for k in d) 
         or any(not hasattr(config, v) for v in ['get'] + d.values()) ):
        #
        d = OrderedDict( [(bool,  config.getboolean)
                         ,(int,   config.getint)
                         ,(float, config.getfloat)
                         ] 
                       ) 
    for k, v in d.items():
        if type(old_val) is k: # isinstance is quirky: isinstance(True, int)
            return v           # and these getters perhaps shouldn't read 
                               # unsual derived classes from a config.ini file
    return config.get     

def override_namedtuple_with_config(nt_lesser
                                   ,config 
                                   ,section_name = 'DEFAULT'
                                   ,leave_as_strings = False
                                   ,**kwargs
                                   ):
    #type ([str,RawConfigParser], namedtuple,Boolean, Boolean, Boolean, Boolean) -> namedtuple
    
    #assert isinstance(ConfigParser.ConfigParser()
    #                 ,ConfigParser.RawConfigParser)
    if  not isinstance(config, ConfigParser.RawConfigParser) : 
        return nt_lesser

    old_dict = nt_lesser._asdict()
    new_dict = {}
    for key, value in config.items(section_name):
        message = key + ' : ' + value
        if not leave_as_strings and key in old_dict:   
            try:
                getter = get_coercer( old_dict[key],  config )
                new_dict[key] = getter( section_name,  key )
            except:
                message +=  (".  failed to parse value in field "
                            + key
                            +'  old_dict[key]) == ' 
                            + str(old_dict[key]) 
                            +'   type(old_dict[key]) == ' 
                            + type(old_dict[key]).__name__ 
                            + 'getter = ' + getter.__name__
                            ) 
                raise TypeError(message)

        else:
            new_dict[key] = value    
            # Let override_namedtuple_with_dict decide 
            # whether to exclude new keys or not



    return override_namedtuple_with_dict(nt_lesser
                                        ,new_dict
                                        ,strict = False
                                        ,**kwargs
                                        )      

        # We know new_dict is a dict so strict == False.
        # We may have already done some type checking
        # using config's methods, so setting 
        # check_types = True on top of this
        # means the user cannot override e.g. lists or dicts
        # until we make type_coercer_factory support them

def override_namedtuple_with_ini_file(nt_lesser
                                     ,config_path = os.path.join(sys.path[0]
                                                                ,'config.ini'
                                                                )
                                     ,**kwargs
                                     ):
    #type (namedtuple, [str,RawConfigParser]) -> namedtuple
    if not isinstance(config_path, str) and not os.path.isfile(config_path):
        return nt_lesser
    config = load_ini_file(config_path, **kwargs)
    return override_namedtuple_with_config(nt_lesser
                                          ,config 
                                          ,**kwargs 
                                          )

def load_toml_file(config_path = os.path.join(sys.path[0], 'config.toml')
                  ,**kwargs
                  ):
    #type (namedtuple, str) -> namedtuple

    """ Loads a toml file as a dictionary.  Trivial wrapper, to accept kwargs.
    
    https://github.com/uiri/toml/blob/master/toml/decoder.py

    Please note, .toml tables are mapped correctly to OrderedDictionaries
    by the line below.  But if convert_subdicts == False, then this dict is
    passed into override_namedtuple, and will pass up through the normal 
    heirarchy of functions in this options_manager module, finally having 
    make_nested_namedtuple called on it, turning the .toml table
    into a namedtuple."""
    return decoder.load(config_path, _dict = OrderedDict)


override_funcs_dict = {  
             dict : override_namedtuple_with_dict 
            ,str : override_namedtuple_with_ini_file # TODO: Write switcher function that also does .toml
            ,ConfigParser.RawConfigParser : override_namedtuple_with_config
            ,ConfigParser.ConfigParser : override_namedtuple_with_config
                        }


def override_namedtuple(nt_lesser
                       ,overrides_list
                       ,override_funcs_dict = override_funcs_dict
                       ,**kwargs
                       ):                        
    # type(list(object), namedtuple, Boolean, Boolean, Boolean, Class -> namedtuple
    """ Override an nt, from a list of dicts, configs, ini, toml and nt.
    
    Full function heirarchy kwargs
    kwargs: {make_nested_namedtuple : {strict = True, class_prefix = 'C_', convert_subdicts == False}
             override_ordereddict_with_dict : {strict = True, check_types = False, delistify = True, add_new_opts = True}
             override_namedtuple_with_dict {strict = True, check_types = False, delistify = True}
             override_namedtuple_with_namedtuple{strict = True}
             load_ini_file : {dump_all_in_default_section = True, empty_lines_in_values = False, interpolation = None}
             type_coercer_factory : {d : None => {bool : config.getboolean, int : config.getint, float : config.getfloat}
             override_namedtuple_with_config : {section_name = 'DEFAULT', leave_as_strings = False}
             override_namedtuple_with_ini_file : {}
             override_namedtuple : {override_funcs_dict : None => { dict : config.getboolean 
                                                                   ,str : override_namedtuple_with_ini_file
                                                                   ,ConfigParser.RawConfigParser : override_namedtuple_with_config
                                                                   ,ConfigParser.ConfigParser : override_namedtuple_with_config
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
            msg += 'Relying on ducktyping.  '
            logging.warning(msg)
        else:
            msg += '.items() method required.  '
            logging.error(msg)
            raise TypeError(msg)
    
    
    def get_nt_overrider_func(override, nt_lesser):
        #type(type[any], namedtuple) -> function
        if isinstance(override, str):
            if override.endswith('.ini'):
                return override_namedtuple_with_ini_file
            if override.endswith('.toml'):
                msg = 'Call load_toml_file first and add dict to overrides'
                logging.error(msg)
                raise NotImplementedError(msg)

        if isinstance(override, nt_lesser.__class__):
            return override_namedtuple_with_namedtuple  

        for key, val in override_funcs_dict.items():
            if isinstance(override, key):
                return val 
        
        if hasattr(override, 'asdict'):
            logging.warning('Ducktyping override as namedtuple.  Calling' 
                           +type(override).__name__ + '.asdict' 
                           +' to coerce to dict.' 
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

#TODO:  Make bool(Sentinel)== False optionally, and fail louder on iteration.

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
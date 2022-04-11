#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Functions to manage options data structures, e.g. fix dictionaries into named tuples
#
__author__ = 'James Parrott'
__version__ = '0.01'
#
# No logging here so that we can use wrapper_logger before the options object is fixed
#

from sys import path as sys_path, argv as sys_argv, version_info
from os.path import normpath, join, isfile
from collections import namedtuple, OrderedDict
# https://docs.python.org/2.7/library/collections.html#collections.namedtuple
if version_info.major >= 3 : # version > '3':   # if Python 3
    import configparser as ConfigParser
else:   # e.g.  Python 2
    import ConfigParser    

from ..third_party.toml.decoder import load


if __name__=='__main__':
    sys_path += [join(sys_path[0], '..')]

#FixedOptions = namedtuple('FixedOptions', config.options.keys(), rename = True)
# TODO: Check for renamed reserved or duplicated field names due to see if 'rename = True' above changed anything
# defaults = FixedOptions(**defaults)



def get_namedtuple_etc_from_class(Class, name):
    # type: ( type[any], str) -> namedtuple
    #https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code

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


def make_nested_namedtuple(d
                          ,d_namedtuple_class_name
                          ,strict = True
                          ,class_prefix = 'NamedTuple_'
                          ,**kwargs
                          ):
    #type (dict, str, str) -> namedtuple(d), tree (Class)
    #
    if strict and not isinstance(d, dict):
        return None

    d = d.copy() 
    for key, val in d.items():
        if isinstance(val, dict):
            d[key] = make_nested_namedtuple(val
                                           ,key
                                           ,False # strict. already checked 
                                           ,class_prefix
                                           ,**kwargs
                                           )  

    return namedtuple(class_prefix + d_namedtuple_class_name
                     ,d.keys()
                     ,rename=False 
                     )(**d)  # Don't return nt class

def delistify_dicts(d_lesser, d_greater): # Mutates d_greater.  d_lesser unaltered.
    #type(dict, dict) -> None
        for key, val in d_greater.items():
            if isinstance(val, list) and (  key not in d_lesser 
                or not isinstance(d_lesser[key], list)  ):
               d_greater[key]=val[0]


def override_ordereddict_with_dict( d_lesser
                                   ,od_greater
                                   ,strict = True
                                   ,check_types = False
                                   ,delistify = True
                                   ,add_in_new_options_keys = False
                                   ,**kwargs):
    #type: (dict, OrderedDict, bool, bool, bool, bool, dict) -> OrderedDict
    #
    if strict and not isinstance(od_greater, dict):  # also true for OrderedDict
        return d_lesser

    if not add_in_new_options_keys:
        new_od = OrderedDict( (key, val) 
                   for key, val in od_greater.items() 
                   if key in d_lesser )
    else: 
        new_od = od_greater.copy() 
    
    if delistify:
        delistify_dicts(d_lesser, new_od)

    if check_types:
        for key in d_lesser.viewkeys() & new_od:  #.keys():
            if (         d_lesser[key]  != None       
                and type(d_lesser[key]) != type(new_od[key])   ):
                del new_od[key]
    
    if version_info.major > 3 or (    version_info.major == 3 
                                  and version_info.minor >= 9 ):
        return d_lesser | new_od    # I like this! :)  There's otherwise no 
                                    # need to check >= Python 3.9
                                    # n.b. dict key insertion order guaranteed 
                                    # to be preserved >= Python 3.7
    else:
        return OrderedDict(d_lesser, **new_od)      # Arguments must be string-keyed PEP 0584
                                                    # The values of od_greater take priority if the keys clash
                                                    # But the order of the keys is as for d_lesser (Iron Python 2.7.11)
                                                    #
                                                    # Extra keys in new_od are added to d_lesser

    # PEP 0584
    # PEP 468
    # https://docs.python.org/3/library/collections.html#collections.OrderedDict

def override_namedtuple_with_dict( nt_lesser
                                  ,d_greater
                                  ,strict = True
                                  ,check_types = True  #types of dict values
                                  ,delistify = True
                                  ,**kwargs):  
    #type (namedtuple, dict, Boolean, Boolean, Boolean) -> namedtuple
    #
    if strict and not isinstance(d_greater, dict):
        return nt_lesser
    elif set(d_greater.keys()).issubset(nt_lesser._fields) and not check_types:  #.viewkeys doesn't have .issubset method ipy 2.7
        if delistify:
            delistify_dicts(nt_lesser._asdict(), d_greater)
        
        return nt_lesser._replace(**d_greater)
    else:
        newDict = override_ordereddict_with_dict(nt_lesser._asdict()
                                                ,d_greater
                                                ,strict
                                                ,check_types
                                                ,delistify
                                                ,**kwargs
                                                )
        return make_nested_namedtuple(newDict
                                     ,nt_lesser.__class__.__name__
                                     ,strict
                                     ,''   # NT Class name prefix
                                     ,**kwargs) 


# ftrick = namedtuple('Trick',trick.keys())(**trick)
# newtrick=ftrick._replace(**{k : asd[k] for k in asd.keys() if k in ftrick._fields})

def override_namedtuple_with_namedtuple( nt_lesser
                                        ,nt_greater
                                        ,strict = True        # strictly enforce (opts) 
                                        ,**kwargs):  
    #type (namedtuple, namedtuple, Boolean, Boolean, Boolean, function) -> namedtuple
    if strict and not isinstance(nt_greater, nt_lesser.__class__):
        return nt_lesser
    else:
        return override_namedtuple_with_dict(nt_lesser
                                            ,nt_greater._asdict()
                                            ,strict = False
                                            ,**kwargs)

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
                 ,**kwargs):
    if not isfile(file_path):
        return None
    else:
        if version_info.major >= 3 : # version > '3':   # if Python 3
            config = ConfigParser.ConfigParser(empty_lines_in_values, interpolation)
        else:   # e.g.  Python 2
            config = ConfigParser.RawConfigParser()   # to turn off interpolation.  Python 3 documentation implies RawConfigParser is 
                                                    # unsafe, so 
                                                    # we have wrapped it in this function to limit its scope 
    
    if dump_all_in_default_section:
        f = open(file_path,'rU')
        f_gen = readline_generator(f)

        if version_info.major < 3 or (version_info.major ==3 and version_info.minor < 2) :  
            class G():
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

def type_coercer_factory(old_val, config, d = None, **kwargs):
    # type (any, Class, dict) -> function
    if d is None or not isinstance(d,dict) or any(
        [not isinstance(k,type) for k in d] ) or any(
        [not hasattr(config,v) for v in ['get'] + d.values()] ):
            d = OrderedDict( [ (bool, config.getboolean)
                              ,(int, config.getint)
                              ,(float, config.getfloat)] ) 
    for k, v in d.items():
        if type(old_val) is k: # isinstance is quirky: isinstance(True, int)
            return v           # and these getters perhaps shouldn't read 
                               # unsual derived classes from a config.ini file
    return config.get     # TODO:  Fix: Trying to override a list or a dict 
                          # will replace it with a string.

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
    #print('Parsing config file...  '+'INFO')
    for key, value in config.items(section_name):
        message = key + ' : ' + value
        if not leave_as_strings and key in old_dict:   
            try:
                getter = type_coercer_factory( old_dict[key],  config )
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
            new_dict[key] = value    # Let override_namedtuple_with_dict decide whether to exclude new keys or not
        #if key=='message':
        #    print(message+'  '+'DEBUG')


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

def override_namedtuple_with_ini_file(   
                                   nt_lesser
                                  ,config_path = join(sys_path[0],'config.ini')
                                  ,**kwargs
                                     ):
    #type (namedtuple, [str,RawConfigParser]) -> namedtuple
    if not isinstance(config_path, str) and not isfile(config_path):
        return nt_lesser
    config = load_ini_file(config_path, **kwargs)
    return override_namedtuple_with_config(     nt_lesser
                                                ,config 
                                                ,**kwargs 
                                           )

def load_toml_file(  config_path = join(sys_path[0],'config.toml')
                    ,**kwargs
                   ):
    #type (namedtuple, str) -> namedtuple

    # Please note, .toml tables are mapped to correctly to OrderedDictionaries
    # by the line below.  But if this is then 
    # passed into override_namedtuple, it will pass up through the normal 
    # heirarchy of functions in this module, finally having 
    # make_nested_namedtuple called on it, turning the .toml table
    # into a namedtuple.
    
    return load(config_path, _dict = OrderedDict)      #toml.decoder





def override_namedtuple( nt_lesser
                        ,overrides_list
                        ,**kwargs
                        ):                        
    # type(list(object), namedtuple, Boolean, Boolean, Boolean, Class -> namedtuple
    # kwargs: {make_nested_namedtuple : {strict = True, class_prefix = 'C_'}
    #          override_ordereddict_with_dict : {strict = True, check_types = False, delistify = True, add_in_new_options_keys = True}
    #          override_namedtuple_with_dict {strict = True, check_types = False, delistify = True}
    #          override_namedtuple_with_namedtuple{strict = True}
    #          load_ini_file : {dump_all_in_default_section = True, empty_lines_in_values = False, interpolation = None}
    #          type_coercer_factory : {d : None => {bool : config.getboolean, int : config.getint, float : config.getfloat}
    #          override_namedtuple_with_config : {section_name = 'DEFAULT', leave_as_strings = False}
    #          override_namedtuple_with_ini_file : {}
    #          override_namedtuple : {override_funcs_dict : None => { dict : config.getboolean 
    #                                                                ,str : override_namedtuple_with_ini_file
    #                                                                ,ConfigParser.RawConfigParser : override_namedtuple_with_config
    #                                                                ,ConfigParser.ConfigParser : override_namedtuple_with_config
    #                                                                ,None : lambda greater, lesser, *args : lesser
    #                                                                ,nt_lesser.__class__ : override_namedtuple_with_namedtuple}
    #           }
    #

    if not isinstance(overrides_list,list):
        overrides_list=[overrides_list]
    
    #if not isinstance(override_funcs_dict,dict) or any(
    #    [not isinstance(k,type) for k in override_funcs_dict]) or any(
    #    [not v in globals() for v in override_funcs_dict.values()]):
    override_funcs_dict = {  
                 dict : override_namedtuple_with_dict 
                ,str : override_namedtuple_with_ini_file # TODO: Write switcher function that also does .toml
                ,ConfigParser.RawConfigParser : override_namedtuple_with_config
                ,ConfigParser.ConfigParser : override_namedtuple_with_config
                ,nt_lesser.__class__ : override_namedtuple_with_namedtuple  
                          }


    #print(str(overrides_list))
    #print('cls.name : ' + nt_lesser.__class__.__name__+' nt_lesser == ' + str(nt_lesser))
    for override in overrides_list:
        if override: # != None:
            for key, val in override_funcs_dict.items():
                #print('override == ' + str(override) + ' key == ' + str(key))
                if isinstance(override, key):
                    #print('  override = ' + str(override) + ' key == ' + str(key) + ' val == ' + str(val))
                    nt_lesser = val( nt_lesser, override, **kwargs ) 
                    break #inner loop only

            #print( ' nt_lesser : ' + str(nt_lesser) 
            #      +' nt_lesser.__class__.__name__ : ' + nt_lesser.__class__.__name__ 
            #      +' override = ' + str(override))

    return nt_lesser


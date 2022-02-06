#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Functions to manage options data structures, e.g. fix dictionaries into named tuples
#
__author__ = 'James Parrott'
__version__ = '0.00'
#
# No logging here so that we can use wrapper_logger before the options object is fixed
#

from sys import path as sys_path, argv as sys_argv, version_info
from os.path import normpath, join, isfile
if version_info.major >= 3 : # version > '3':   # if Python 3
    import configparser as ConfigParser
else:   # e.g.  Python 2
    import ConfigParser    



from collections import namedtuple, OrderedDict
# https://docs.python.org/2.7/library/collections.html#collections.namedtuple
if __name__=='__main__':
    sys_path += [join(sys_path[0], '..')]

#FixedOptions = namedtuple('FixedOptions', config.options.keys(), rename = True)
# TODO: Check for renamed reserved or duplicated field names due to see if 'rename = True' above changed anything
# defaults = FixedOptions(**defaults)

def make_nested_namedtuple(d, d_namedtuple_class_name, strict = True, class_prefix = 'C_', **kwargs):
    #type (dict, str, str) -> namedtuple(d), tree (Class)
    #
    if strict and not isinstance(d,dict):
        return None

    d = d.copy() 
    for key, val in d.items():
        if isinstance(val,dict):
            d[key] = make_nested_namedtuple(val, key, False, class_prefix, **kwargs)  # strict = False because we type-checked 
                                                                                      # val on the previous line

    return namedtuple(class_prefix + d_namedtuple_class_name, d.keys(), rename=False )(**d)  # Don't return nt class

def override_ordereddict_with_dict( d_lesser
                                   ,od_greater
                                   ,strict = True
                                   ,check_types = False
                                   ,add_in_new_options_keys = False
                                   ,**kwargs):
    #type: (dict, OrderedDict, bool, bool, bool, dict) -> OrderedDict
    #
    if strict and not isinstance(od_greater,dict):  # also true for OrderedDict
        return d_lesser

    if not add_in_new_options_keys:
        new_od = {key : val for key, val in od_greater.items() if key in d_lesser}
    else: 
        new_od = od_greater.copy() 
    
    if check_types:
        for key in d_lesser.viewkeys() & new_od:  #.keys():
            if type(d_lesser[key]) != type(new_od[key]):
                del new_od[key]
    
    if version_info.major > 3 or (version_info.major == 3 and version_info.minor >= 9) :
        return d_lesser | new_od    # I like this! :)  There's otherwise no good reason to check >= Python 3.9
                                    # n.b. dict order guaranteed preserved >= Python 3.7
    else:
        return OrderedDict(d_lesser, **new_od)      # Arguments must be string-keyed PEP 0584
                                                    # The values of od_greater take priority if the keys clash
                                                    # But the order of the keys is as for d_lesser (Iron Python 2.7.11)
                                                    #
                                                    # Extra keys in od_greater are added to od_lesser

    # PEP 0584
    # PEP 468
    # https://docs.python.org/3/library/collections.html#collections.OrderedDict

def override_namedtuple_with_dict( nt_lesser
                                  ,d_greater
                                  ,strict = True
                                  ,check_types = True  #types of dict values
                                  ,**kwargs):  
    #type (dict, namedtuple, Boolean, Boolean, Boolean) -> namedtuple
    #
    if strict and not isinstance(d_greater, dict):
        return nt_lesser
    elif set(d_greater.keys()).issubset(nt_lesser._fields) and not check_types:  #.viewkeys doesn't have .issubset method ipy 2.7
        return nt_lesser._replace(**d_greater)
    else:
        newDict = override_ordereddict_with_dict(nt_lesser._asdict(), d_greater, strict, check_types, **kwargs)
        return make_nested_namedtuple(newDict, nt_lesser.__class__.__name__, strict, '', **kwargs) 


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
        return override_namedtuple_with_dict(nt_lesser, nt_greater._asdict(), strict = False, **kwargs)

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

def setup_config( file_path
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
    if d == None or not isinstance(d,dict) or any(
        [not isinstance(k,type) for k in d]) or any(
        [not hasattr(config,v) for v in ['get'] + d.values()]):
            d = {bool : config.getboolean, int : config.getint, float : config.getfloat}
    for k, v in d.items():
        if isinstance(old_val, k):
            return v
    return config.get     # TODO:  Fix: Trying to override a list or a dict will replace it with a string.

def override_namedtuple_with_config(     nt_lesser
                                        ,config 
                                        ,section_name = 'DEFAULT'
                                        ,leave_as_strings = False
                                        ,**kwargs
                                      ):
    #type ([str,RawConfigParser], namedtuple,Boolean, Boolean, Boolean, Boolean) -> namedtuple
    if  not isinstance(config, ConfigParser.RawConfigParser) and not isinstance(config, ConfigParser.ConfigParser) :
        return nt_lesser

    old_dict = nt_lesser._asdict()
    new_dict = {}
    #print('Parsing config file...  '+'INFO')
    for key, value in config.items(section_name):
        message = key + ' : ' + value
        if key in old_dict:   
            new_dict[key] = value if leave_as_strings else type_coercer_factory(
                                                             old_dict[key]
                                                            ,config 
                                                           )(section_name
                                                            ,key
                                                            )
            message += '  old_dict[key]) == ' + str(old_dict[key]) + (
                  '   type(old_dict[key]) == ' + type(old_dict[key]).__name__ )
        else:
            new_dict[key] = value    # Let override_namedtuple_with_dict decide whether to exclude new keys or not
        #print(message+'  '+'DEBUG')


    return override_namedtuple_with_dict(nt_lesser, new_dict, strict = False, **kwargs)      
                                                                                 # We know new_dict is a dict so strict == False.
                                                                                 # We may have already done some type checking
                                                                                 # using config's methods, so setting 
                                                                                 # check_types = True on top of this
                                                                                 # means the user cannot override e.g. lists or dicts
                                                                                 # until we make type_coercer_factory support them

def override_namedtuple_with_ini_file(   nt_lesser
                                        ,config_path = join(sys_path[0],'config.ini')   
                                        ,**kwargs
                                      ):
    #type ([str,RawConfigParser], namedtuple,Boolean, Boolean, Boolean, Boolean) -> namedtuple
    if not isinstance(config_path, str) and not isfile(config_path):
        return nt_lesser
    config = setup_config(config_path, **kwargs)
    return override_namedtuple_with_config(     nt_lesser
                                                ,config 
                                                ,**kwargs 
                                           )

def override_namedtuple( nt_lesser
                        ,overrides_list
                        ,**kwargs
                        ):                        
    # type(list(object), namedtuple, Boolean, Boolean, Boolean, Class -> namedtuple
    # kwargs: {make_nested_namedtuple : {strict = True, class_prefix = 'C_'}
    #          override_ordereddict_with_dict : {strict = True, check_types = False, add_in_new_options_keys = True}
    #          override_namedtuple_with_dict {strict = True, check_types = False}
    #          override_namedtuple_with_namedtuple{strict = True}
    #          setup_config : {dump_all_in_default_section = True, empty_lines_in_values = False, interpolation = None}
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
    override_funcs_dict = {  dict : override_namedtuple_with_dict 
                            ,str : override_namedtuple_with_ini_file
                            ,ConfigParser.RawConfigParser : override_namedtuple_with_config
                            ,ConfigParser.ConfigParser : override_namedtuple_with_config
                            ,nt_lesser.__class__ : override_namedtuple_with_namedtuple  
                            }



    for override in overrides_list:
        if override != None and len(override) > 0:
            for key, val in override_funcs_dict.items():
                if isinstance(override, key):
                    nt_lesser = val( nt_lesser, override, **kwargs ) 
                    break #inner loop only

        #print('nt_lesser : ' + nt_lesser.__class__.__name__ + '  override = ' + str(override))

    return nt_lesser


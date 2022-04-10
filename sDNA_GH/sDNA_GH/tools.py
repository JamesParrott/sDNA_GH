#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.01'

import sys, os  
from os.path import (join, split, isfile, dirname, isdir, sep, normpath
                     ,basename as filename
                     )

from re import match
from subprocess import check_output, call
from time import asctime
from collections import namedtuple, OrderedDict
from itertools import chain, izip, repeat #, cycle
import inspect
from uuid import UUID
import csv
from numbers import Number
import locale
from math import log
from importlib import import_module
if sys.version < '3.3':
    from collections import Hashable, Iterable, MutableMapping
else:
    from collections.abc import Hashable, Iterable, MutableMapping
from abc import abstractmethod
if sys.version < '3.4':
    from abc import ABCMeta
    class ABC:
        __metaclass__ = ABCMeta
else:
    from abc import ABC

import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import ghpythonlib.treehelpers as th
from System.Drawing import Color as Colour
from System.Drawing import PointF, SizeF
import Grasshopper.Kernel 
from Grasshopper import DataTree
from Grasshopper.GUI.Gradient import GH_Gradient
import GhPython
from ghpythonlib.components import ( BoundingBox
                                    ,Rectangle
                                    ,Legend 
                                    ,XYPlane
                                    ,XZPlane
                                    ,YZPlane
                                    ,CustomPreview
                                    )

from .custom_python_modules.options_manager import (load_toml_file
                                                   ,make_nested_namedtuple     
                                                   ,load_ini_file                             
                                                   ,override_namedtuple        
                                                   )
from .custom_python_modules import wrapper_logging
from .custom_python_modules.wrapper_pyshp import (get_fields_recs_and_shapes_from_shapefile
                                                 ,get_unique_filename_if_not_overwrite
                                                 ,write_from_iterable_to_shapefile_writer
                                                 )
from .sDNA_GH_launcher import Output, load_modules


output = Output()


if 'ghdoc' not in globals():
    if sc.doc == Rhino.RhinoDoc.ActiveDoc:
        raise ValueError(output('sc.doc == Rhino.RhinoDoc.ActiveDoc. '
                               +'Switch sc.doc = ghdoc and re-import module. '
                               ,'ERROR'
                               )
                        )
    if isinstance(sc.doc, GhPython.DocReplacement.GrasshopperDocument):
        ghdoc = sc.doc  # Normally a terrible idea!  But the check conditions
                        # are strong, and we need to get ghdoc in this 
                        # namespace.
    else:
        raise TypeError(output('sc.doc is not of type: '
                              +'GhPython.DocReplacement.GrasshopperDocument '
                              +'Ensure sc.doc == ghdoc and re-import module.'
                              ,'ERROR'
                              )
                        )

class HardcodedMetas(): 
    config = join( dirname(dirname(__file__)), r'config.toml')
    add_in_new_options_keys = False
    allow_components_to_change_type = False
    typecheck_opts_namedtuples = True
    typecheck_opts_fields = True
    sDNAUISpec = 'sDNAUISpec'
    runsdnacommand = 'runsdnacommand' # only used for .map_to_string. 
                               # Kept in case we use work out how
                               # to run runsdnacommand.runsdnacommand in future 
                               # with an env, while being able to get the 
                               # sDNA stderr and stdout to the sDNA_GH logging
    sDNA = (sDNAUISpec, runsdnacommand)  # Read only.  Auto updates from above two.
    sDNA_path = ''  # Read only.  Determined after loading sDNAUISpec to which ever below
                    # it is found in.
                    # after loading, assert opts['metas'].sDNA_path == dirname(opts['options'].sDNAUISpec.__file__)
    #sDNA_UISpec_path = r'C:\Program Files (x86)\sDNA\sDNAUISpec.py'
    #sDNA_search_paths = [sDNA_UISpec_path, 
    sDNA_search_paths  = [r'C:\Program Files (x86)\sDNA']
    sDNA_search_paths += [join(os.getenv('APPDATA'),'sDNA')]
    sDNA_search_paths += [path for path in os.getenv('PATH').split(';') if 'sDNA' in path ]
    auto_update_Rhino_doc_path = True
                        #Abbreviation = Tool Name
#######################################################################################################################
    name_map = dict(    #sDNA_Demo = [ 'Read_From_Rhino'
                        #            ,'Read_Usertext'
                        #            ,'Write_Shp'
                        #            ,'sDNAIntegral'
                        #            ,'Read_Shp'
                        #            ,'Write_Usertext'
                        #            ,'Parse_Data'
                        #            ,'Recolour_objects'
                        #            ]
                         Read_From_Rhino = 'get_Geom'
                        ,Read_Usertext = 'read_Usertext'
                        ,Write_Shp = 'write_shapefile'
                        ,Read_Shp = 'read_shapefile'
                        ,Write_Usertext = 'write_Usertext'
                        ,Bake_UserText = 'bake_Usertext'
                        ,Parse_Data = 'parse_data'
                        ,Recolour_objects = 'recolour_objects'
                        ,Recolor_objects = 'recolour_objects'
                        #,'main_sequence'
                        #,'sDNAIntegral'
                        #,'sDNASkim'
                        ,sDNAIntFromOD = 'sDNAIntegralFromOD'
                        #,'sDNAGeodesics'
                        #,'sDNAHulls'
                        #,'sDNANetRadii'
                        ,sDNAAccessMap = 'sDNAAccessibilityMap'
                        #,'sDNAPrepare'
                        #,'sDNALineMeasures'
                        #,'sDNALearn'
                        #,'sDNAPredict'
                    )
    name_map = make_nested_namedtuple(name_map
                                     ,'NameMap'
                                     ,strict = True
                                     )
                          
    categories = {
                         'get_Geom'         : 'Support'
                        ,'read_Usertext'    : 'Usertext'
                        ,'write_shapefile'  : 'Support'
                        ,'read_shapefile'   : 'Support'
                        ,'write_Usertext'   : 'Usertext'
                        ,'bake_Usertext'    : 'Usertext'
                        ,'parse_data'       : 'Support'
                        ,'recolour_objects' : 'Support'
                        ,'sDNAIntegral'     : 'Analysis'
                        ,'sDNASkim'         : 'Analysis'
                        ,'sDNAIntFromOD'    : 'Analysis'
                        ,'sDNAGeodesics'    : 'Geometric analysis'
                        ,'sDNAHulls'        : 'Geometric analysis'
                        ,'sDNANetRadii'     : 'Geometric analysis'
                        ,'sDNAAccessMap'    : 'Analysis'
                        ,'sDNAPrepare'      : 'Preparation'
                        ,'sDNALineMeasures' : 'Preparation'
                        ,'sDNALearn'        : 'Calibration'
                        ,'sDNAPredict'      : 'Calibration'
                        ,'sDNA_general'     : 'Dev tools'
                        ,'Python'           : 'Dev tools'
                        ,'Self_test'        : 'Dev tools'
                        ,'Build_components' : 'Dev tools' 
                    }
    categories = make_nested_namedtuple(categories
                                       ,'Categories'
                                       ,strict = True
                                       )

#######################################################################################################################


valid_re_normalisers = ['linear', 'exponential', 'logarithmic']


class HardcodedOptions():            
    ####################################################################################
    #System
    platform = 'NT' # in {'NT','win32','win64'} only supported for now
    encoding = 'utf-8'
    rhino_executable = r'C:\Program Files\Rhino 7\System\Rhino.exe'
    sDNAUISpec = None
    run_sDNA = None
    Rhino_doc_path = ''  # tbc by auto update
    sDNA_prepare = r'C:\Program Files (x86)\sDNA\bin\sdnaprepare.py'
    sDNA_integral = r'C:\Program Files (x86)\sDNA\bin\sdnaintegral.py'
    python_exe = r'C:\Python27\python.exe' # Default installation path of Python 2.7.3 release (32 bit ?) http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi
                                            # grouped from sDNA manual https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/installation_usage.html    
    ####################################################################################
    #Logging    
    #os.getenv('APPDATA'),'Grasshopper','Libraries','sDNA_GH','sDNA_GH.log')
    logs_subdir_name = 'logs'
    log_file = 'sDNA_GH.log'

    tests_subdirectory = r'tests'
    logger_file_level = 'DEBUG'
    logger_console_level = 'INFO'
    logger_custom_level = 'INFO'

    ####################################################################################
    #GDM
    merge_Usertext_subdicts_instead_of_overwriting = True
    use_initial_groups_if_too_many_in_list = True
    use_initial_data_if_too_many_in_list = True
    include_groups_in_gdms = False
    ####################################################################################
    #Shapefiles
    shp_file_shape_type = 'POLYLINEZ'
    cache_iterable_when_writing_to_shp= False
    shp_file_extension = '.shp' # file extensions are actually optional in PyShp, but just to be safe and future proof
    supply_sDNA_file_names = True
    shape_file_to_write_Rhino_data_to_from_sDNA_GH = r'C:\Users\James\Documents\Rhino\Grasshopper\tmp.shp' # None means Rhino .3dm filename is used.
    overwrite_shp_file = True
    overwrite_UserText = True
    duplicate_UserText_key_suffix = r'_{}'
    prepped_shp_file_suffix = "_prepped"
    output_shp_file_suffix = "_output"
    duplicate_file_name_suffix = r'_({})' # Needs to contain a replacement field {} that .format can target.  No f strings in Python 2.7 :(
    max_new_files_to_make = 20
    suppress_overwrite_warning = True     
    uuid_shp_file_field_name = 'Rhino3D_' # 'object_identifier_UUID_'     
    uuid_length = 36 # 32 in 5 blocks (2 x 6 & 2 x 5) with 4 seperator characters.
    calculate_smallest_field_sizes = True
    delete_shapefile_after_reading = False
    global_shp_file_field_size = 30
    global_shp_number_of_decimal_places = 10
    shp_file_field_size_num_extra_chars = 2
    enforce_yyyy_mm_dd = False
    use_str_decimal = True
    do_not_convert_floats = True
    decimal_module_prec = 12
    shp_record_max_decimal = 4
    ####################################################################################
    #Writing and Reading Usertext to/from Rhino
    create_new_groups_layer_from_shapefile = False
    max_new_UserText_keys_to_make = 20
    #
    #
    rhino_user_text_key_format_str_to_read = 'sDNA input name={name} type={fieldtype} size={size}'  #30,000 characters tested!
    sDNA_output_user_text_key_format_str_to_read = 'sDNA output={name} run time={datetime}'  #30,000 characters tested!
    ####################################################################################
    #sDNA
    Default_sDNA_GH_file_path = __file__
    overwrite_input_shapefile = False
    auto_get_Geom = False
    auto_read_Usertext = False
    auto_write_new_Shp_file = False
    auto_read_Shp = False
    auto_parse_data = False
    auto_plot_data = False
    #Plotting results
    field = 'BtEn'
    plot_max = None
    plot_min = None
    sort_data = True
    base = 10 # base of log and exp spline, not of number representations
    re_normaliser = 'linear' 
    assert re_normaliser in valid_re_normalisers 
    classes = [None] #[2000000, 4000000, 6000000, 8000000, 10000000, 12000000]
    legend_extent = None  # [xmin, ymin, xmax, ymax]
    bbox = None  # [xmin, ymin, xmax, ymax]
    number_of_classes = 7
    class_spacing = 'equal number of members' 
    assert class_spacing in valid_re_normalisers + ['equal number of members']
    first_legend_tag_format_string = 'below {upper}'
    inner_tag_format_string = '{lower} - {upper}' # also supports {mid_pt}
    last_legend_tag_format_string = 'above {lower}'
    num_format = '{:.3n}'
    leg_frame = ''  # uuid of GH object
    locale = '' # ''=> auto .  Used for locale.setlocale(locale.LC_ALL,  options.locale)
    all_in_class_same_colour = False
    GH_Gradient = False
    GH_Gradient_preset = 5
    rgb_max = (155, 0, 0) #990000
    rgb_min = (0, 0, 125) #3333cc
    rgb_mid = (0, 155, 0) # guessed
    line_width = 4 # milimetres? 
    ####################################################################################
    #Test
    message = 'Hardcoded default options from tools.py'

GH_Gradient_preset_names = { 0 : 'EarthlyBrown'
                            ,1 : 'Forest'
                            ,2 : 'GreyScale'
                            ,3 : 'Heat'
                            ,4 : 'SoGay'
                            ,5 : 'Spectrum'
                            ,6 : 'Traffic'
                            ,7 : 'Zebra'
                            }

class HardcodedLocalMetas():
    sync_to_module_opts = True    
    read_from_shared_global_opts = True
    nick_name = ''


# Pre Python 3.6 the order of an OrderedDict isn't necessarily that of the 
# arguments in its constructor so we build our options and metas namedtuples
# from a class, to avoid re-stating the order of the keys.

class TestABC(ABC):
    @abstractmethod
    def f(self):
        '''Do nothing'''

class TestNormal():
    def f(self):
        '''Do nothing'''

abc_only_attrs = [x for x in dir(TestABC) if x not in dir(TestNormal)]
abc_only_attrs += [x for x in dir(TestABC.f) if x not in dir(TestNormal.f)]

#   to allow a non-abstract obj to quack like an abstract obj in a Structural
#   Typing test. 
#   e.g. abc_only_attrs += ['__isabstractmethod__'], but there are a lot more!
#   __isabstractmethod__ is set==True by @abstractmethod on attrs of 
#   ABC subclasses https://peps.python.org/pep-3119/


def quacks_like(Duck
               ,obj
               ,check_attr_types = True
               ,check_dunders = False
               ):
    #type(type[Any], type[Any], bool, bool) -> bool

    # A simple (naive) Structural Typing checker, to permit duck typing.  
    # Checks instances as well as classes.  Untested on waterfowl.  
    #
    # A template Tool is provided below to 
    # define the interface supported by run_tools,
    # but I don't want to force power 
    # users importing the package
    # to inherit from ABCs, as instances of 
    # Tool (with __call__) can equally well be 
    # replaced by normal Python functions 
    # with a few extra attributes.

    return (  isinstance(obj, Duck.__class__ )
              or all( hasattr(obj, attr) and 
                        (not check_attr_types or 
                         quacks_like(getattr(Duck, attr)
                                    ,getattr(obj, attr)
                                    ,check_attr_types
                                    ,check_dunders
                                    )
                         )
                      for attr in dir(Duck) if (check_dunders or 
                                                not attr.startswith('_') and
                                                attr not in abc_only_attrs 
                                                )
                    )
            )

def get_namedtuple_etc_from_class(Class, name):
    # type: ( type[any], str) -> namedtuple
    #https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code

    fields = [attr for attr in dir(Class) if not attr.startswith('_')]
    factory = namedtuple(name, fields, rename=True)   
    return factory(**{x : getattr(Class, x) for x in fields})

default_metas = get_namedtuple_etc_from_class(HardcodedMetas, 'Metas')
default_options = get_namedtuple_etc_from_class(HardcodedOptions, 'Options')
default_local_metas = get_namedtuple_etc_from_class(HardcodedLocalMetas, 'LocalMetas')

empty_NT = namedtuple('Empty','')(**{})

module_opts = OrderedDict( metas = default_metas
                         ,options = default_options
                         )                

opts = 6

# Initialise caches:
get_syntax_dict = {} 
input_spec_dict = {}                 

def get_path(inst = None, opts = module_opts):
    path = Rhino.RhinoDoc.ActiveDoc.Path
                    
    if not isinstance(path, str) or not isfile(path):
        try:
            path = ghdoc.Path
        except:
            try:
                path = inst.ghdoc.Path #type: ignore
            except:
                try:
                    path = sc.doc.Path
                except:
                    path = None
        finally:
            if not path:
                path = opts['options'].Default_sDNA_GH_file_path
    
    return path



# tmp_logs = []

# def output(s, logging_level = "INFO", logging_dict = {}, tmp_logs=tmp_logs ):
#     #type: (str, str, dict, list) -> str
    
#     #print(s)

#     if logging_dict == {} and 'logger' in globals(): 
#         logging_dict = dict( DEBUG = logger.debug
#                             ,INFO = logger.info
#                             ,WARNING = logger.warning
#                             ,ERROR = logger.error
#                             ,CRITICAL = logger.critical
#                             )

#     logging_dict.get( logging_level
#                      ,lambda x : tmp_logs.append( (x, logging_level) ) 
#                      )(s)

#     return logging_level + ' : ' + s + ' '

#
#
def func_name(f):
    #type(function)->str
    if hasattr(f,'__qualname__'):
        return f.__qualname__  
    elif hasattr(f,'__name__'):
        return f.__name__  
    else:
        return f.func_name
#
#

class Debugger:
    def __init__(self, output = None):
        #type(type[any], function) -> None  # callable object
        if output is None:
            output = Output()
        self.output = output # want to call an instance that we also use for
                             # higher logging level messages so 
                             # composition instead of inheritance is used
    def __call__(self, x):
        c = inspect.currentframe().f_back.f_locals.items()

        names = [name.strip("'") for name, val in c if val is x]
        # https://stackoverflow.com/questions/18425225/getting-the-name-of-a-variable-as-a-string
        # https://stackoverflow.com/a/40536047

        if names:
            return self.output(str(names) + ' == ' + str(x)+' ','DEBUG')
        else:
            return self.output(str(x)+' ','DEBUG')

debug = Debugger(output)

# def debug(x):
#     # type(type[any]) -> str

#     c = inspect.currentframe().f_back.f_locals.items()

#     names = [name.strip("'") for name, val in c if val is x]
#     # https://stackoverflow.com/questions/18425225/getting-the-name-of-a-variable-as-a-string

#     if names:
#         return output(str(names) + ' == ' + str(x)+' ','DEBUG')
#     else:
#         return output(str(x)+' ','DEBUG')

#debug(component)
#
####################################################################################################################
#
# 





def unpack_first_item_from_list(l, null_container = {}):
    #type(type[any])-> dict
    #hopefully!
    if l:
        if isinstance(l, Iterable) and not isinstance(l, str):
            return l[0]
        else:
            return l
    else:
        return null_container

    





#if 'logger' not in globals():

debug(module_opts['options'].message)


####################################################################################################################
#
#
def override_all_opts( args_dict
                      ,local_opts # mutated
                      ,external_opts
                      ,local_metas = default_local_metas
                      ,external_local_metas = empty_NT
                      ,name = ''):
    #type(dict, dict, dict, namedtuple, namedtuple, str) -> namedtuple
    #
    # 1) We assume opts has been built from a previous GHPython launcher component and call to this very function.  This
    # trusts the user and our components somewhat, in so far as we assume metas and options in opts have not been crafted to have
    # be of a class named 'Metas', 'Options', yet contain missing options.  
    #
    # 2) A primary meta in opts refers to an old primary meta (albeit the most recent one) and will not be used
    # in the options_manager.override order as we assume that file has already been read into a previous opts in the chain.  If the user wishes 
    # to apply a new project config.ini file, they need to instead specify it in args (by adding a variable called config to 
    # the GHPython sDNA_GH launcher component.
    metas = local_opts['metas']
    options = local_opts['options']
    def sDNA():
        return local_opts['metas'].sDNA


        # Unlike in all the other functions, sDNA might change in this one, (in metas in the 
        # main options update loop).  So we store 
        # tool args ready under this new sDNA version, in advance of the component
        # importing the new sDNA module, and we just have to then perform an update in
        # cache_syntax_and_UISpec instead of an overwrite

    args_metas = {}
    args_options = {}
    args_tool_options = {}
    args_local_metas = {}

    for (arg_name, arg_val) in args_dict.items():  # local_metass() will be full of all our other variables.
        if arg_val: # Unconnected input variables in a Grasshopper component are None.  
                    # No sDNA tool inputspec default, no metas and no options default is None.
                    #If None values are needed as specifiable inputs, we would 
                    # need to e.g. test ghenv for an input variable's connectedness
                    # so we don't support this
            if arg_name in metas._fields:      
                args_metas[arg_name] = arg_val
            elif arg_name in options._fields:   
                args_options[arg_name] = arg_val
            elif arg_name in getattr(  local_opts.get( name,{}).get(sDNA(),{} ), '_fields' ,{} ): 
                args_tool_options[arg_name] = arg_val
            elif arg_name in local_metas._fields:
                args_local_metas[arg_name] = arg_val



    def kwargs(key, local_opts):
        d = dict( 
          dump_all_in_default_section = False
         ,empty_lines_in_values = False
         ,interpolation = None # For load_ini_file above
         ,section_name = key # For override_namedtuple below
         ,leave_as_strings = False 
         ,strict = local_opts['metas'].typecheck_opts_namedtuples
         ,check_types = local_opts['metas'].typecheck_opts_fields
         ,add_in_new_options_keys = local_opts['metas'].add_in_new_options_keys
                )
        return d

    ###########################################################################
    #Primary meta:
    #
    config_file_override = {}

    if 'config' in args_metas and isfile(args_metas['config']): 
        path = args_metas['config']
        file_ext = path.rpartition('.')[2]
        if file_ext == 'ini':
            debug('Loading options from .ini file: ' + path)
            config_file_override =  load_ini_file( path, **kwargs('', local_opts) )
        elif file_ext == 'toml':
            debug('Loading options from .toml file: ' + path)
            config_file_override =  load_toml_file( path )
        else:
            debug('config_file_override = ' + str(config_file_override))
    else:
        debug('No valid config file in args.  ')
        file_ext = ''


    def config_file_reader(key):
        #type(str)->[dict/file object]
        if isinstance(config_file_override, dict) and key in config_file_override:
            return config_file_override[key] 
        else:
            return config_file_override


    ###########################################################################
    # Update syncing / desyncing controls in local_metas
    #
    ext_local_metas_dict = external_local_metas._asdict()
    if 'nick_name' in ext_local_metas_dict:
        ext_local_metas_dict.pop('nick_name')

    if file_ext:
        if file_ext == 'ini':
            for section in ('DEFAULT', 'local_metas'):
                if config_file_override.has_section(section):
                    config_file_override.remove_option(section, 'nick_name')
        elif file_ext == 'toml' or isinstance(config_file_override, dict):
            if ( 'local_metas' in config_file_override and
                 'nick_name' in config_file_override['local_metas'] ):
                config_file_override['local_metas'].pop('nick_name')

    if 'nick_name' in args_local_metas:
        args_local_metas.pop('nick_name')

    local_metas_overrides_list = [ext_local_metas_dict
                                 ,config_file_reader('local_metas') # 'nick_name' removed above.
                                 ,args_local_metas
                                 ]
    local_metas = override_namedtuple(local_metas
                                     ,local_metas_overrides_list
                                     ,**kwargs('DEFAULT', local_opts) 
                                     ) 
    ###########################################################################


    sub_args_dict = {     'metas' : args_metas
                          ,'options' : args_options
                          ,name : args_tool_options
                    }

    def overrides_list(key):
        # type (str) -> list
        if (local_metas.sync_to_module_opts or 
            not local_metas.read_from_shared_global_opts):
            retval = []  
        else: 
            #if not synced but still reading from module opts, 
            # then add module opts to overrides
            retval = [    module_opts.get( key,  {} ).get( sDNA(),  {} )    ]

        
        ext_opts = external_opts.get( key,  {} )
        if key not in ('options','metas') :
            ext_opts = ext_opts.get( sDNA(),  {} )
        
        retval += [ext_opts, config_file_reader(key), sub_args_dict.get(key,{})]



        return retval

        

    #overrides_list = lambda key : [ external_opts.get(key,{}).get(sDNA(), {})
    #                              ,config_file_reader, sub_args_dict.get(key, {})]
    if local_metas.sync_to_module_opts:
        dict_to_update = module_opts # the opts in module's global scope, outside this function
    else:
        dict_to_update = local_opts
        #if local_metas.read_from_shared_global_opts:
          #  overrides = lambda key : [opts.get(key,{}).get(sDNA(), {})] + overrides(key)

    for key in dict_to_update:
        if key in ('options','metas'):
            dict_to_update[key] = override_namedtuple( dict_to_update[key]
                                                      ,overrides_list(key)
                                                      ,**kwargs(key, local_opts) 
                                                      ) 
            #if key=='options':
            #    print('dict_to_update message == '+dict_to_update['options'].message+' '+'DEBUG')
        else:
            if sDNA() in dict_to_update[key]:
                dict_to_update[key][sDNA()] = override_namedtuple(   dict_to_update[key][sDNA()]
                                                                    ,overrides_list(key)
                                                                    ,**kwargs(key, local_opts) 
                                                                    )
            else:
                for tool in dict_to_update[key]:
                    dict_to_update[key][tool][sDNA()] = override_namedtuple( dict_to_update[key][tool][sDNA()]
                                                                            ,overrides_list(key) # + '_tool'
                                                                            ,**kwargs(key, local_opts) # + '_tool'
                                                                            ) # TODO: add in tool name to key
    return local_metas


# First options options_manager.override (3), user's installation specific options over (4), hardcoded defaults above
#
# Use the above function to load the user's installation wide defaults by using
#  the primary meta from the hardcoded defaults.

if isfile(default_metas.config):
    #print('Before override: message == '+opts['options'].message)
    override_all_opts(args_dict = default_metas._asdict() # to get installation config.toml
                     ,local_opts = module_opts #  mutates opts
                     ,external_opts = {}  
                     ) 

    debug("After override: opts['options'].message == " + module_opts['options'].message)
else:
    output('Config file: ' + default_metas.config + ' not found. ','WARNING')    
#
####################################################################################################################

folders = [r'C:\Program Files\Python27'
          ,r'%appdata%\Python27'
          ,r'C:\Program Files (x86)\Python27'
          ]
pythons = ['python.exe'
          ,'py27.exe'
          ]

possible_pythons = (join(folder, python) for folder in folders for python in pythons)

while not isfile(module_opts['options'].python_exe):
    module_opts['options']._replace(python_exe = next(possible_pythons))

assert isfile(module_opts['options'].python_exe)

if not hasattr(sys.modules['sDNA_GH.tools'], 'logger'):
    
    logs_directory = join(dirname(get_path()),module_opts['options'].logs_subdir_name)

    if not isdir(logs_directory):
        os.mkdir(logs_directory)

    # wrapper_logging.logging.shutdown() # Ineffective in GH :(


    logger = wrapper_logging.new_Logger( 'sDNA_GH'
                                        ,join(logs_directory, module_opts['options'].log_file)
                                        ,module_opts['options'].logger_file_level
                                        ,module_opts['options'].logger_console_level
                                        ,None # custom_file_object 
                                        ,module_opts['options'].logger_custom_level
                                        )

    sDNA_tool_logger = wrapper_logging.logging.getLogger('sDNA')

    output.set_logger(logger)

    debug('Logging set up in sDNA_GH.tools ')



####################################################################################################################
# Auxillary functions
#
def make_regex(pattern):
    # type (str) -> str
    the_specials = '.^$*+?[]|():!#<='
    for c in the_specials:
        pattern = pattern.replace(c,'\\' + c)
    pattern = pattern.replace( '{', r'(?P<' ).replace( '}', r'>.*)' )
    return r'\A' + pattern + r'\Z'



def is_uuid(val):
    try:
        UUID(str(val))
        return True
    except ValueError:
        return False
#https://stackoverflow.com/questions/19989481/how-to-determine-if-a-string-is-a-valid-v4-uuid



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

def old_multi_context_checker(is_thing, toggle_context):
    #type(function, function) -> function
    def context_toggling_is_thing_checker(x):
        #type(str)-> bool  
        if x:
            if is_thing(x):
                return True  
            else:
                toggle_context()
                return is_thing(x)
        else:
            return False
    return context_toggling_is_thing_checker    

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

def make_new_group(group_name = None):
    #type(str) -> str
    return rs.AddGroup(group_name)

def add_objects_to_group(objs, group_name):
    #type(list, str) -> int
    return rs.AddObjectsToGroup(objs, group_name)    

Rhino_obj_converter_Shp_file_shape_map = dict( NULL = None
                                            ,POINT = 'PointCoordinates'
                                            ,MULTIPATCH = 'MeshVertices'  # Unsupported.  Complicated.  TODO!  
                                            ,POLYLINE = 'PolylineVertices'  # Works on Line too, unlike the checker.
                                            ,POLYGON = 'PolylineVertices'   
                                            ,MULTIPOINT = 'PointCloudPoints'  # Unsupported.  Needs chaining to list or POINT
                                            ,POINTZ = 'PointCoordinates'
                                            ,POLYLINEZ = 'PolylineVertices'
                                            ,POLYGONZ = 'PolylineVertices'  
                                            ,MULTIPOINTZ = 'PointCloudPoints'  #see MULTIPOINT
                                            ,POINTM = 'PointCoordinates'
                                            ,POLYLINEM = 'PolylineVertices'
                                            ,POLYGONM = 'PolylineVertices'    
                                            ,MULTIPOINTM = 'PointCloudPoints'  #see MULTIPOINT
                                            )  

def get_points_list_from_geom_obj(x, shp_type='POLYLINEZ'):
    #type(str, dict) -> list
    f = getattr(rs, Rhino_obj_converter_Shp_file_shape_map[shp_type])
    return [list(y) for y in f(x)]

Rhino_obj_checker_Shp_file_shape_map = dict( 
     NULL = [None]
    ,POINT = ['IsPoint']
    ,MULTIPATCH = ['IsMesh']    # Unsupported.  Complicated.  TODO!
    ,POLYLINE = ['IsLine','IsPolyline']  #IsPolyline ==False for lines, 
#                                        # on which PolylineVertices works fine
    ,POLYGON = ['IsPolyline'] #2 pt Line not a Polygon.Doesn't check closed
    ,MULTIPOINT = ['IsPoint']   # Need to define lambda l : any(IsPoint(x) for x in l)
    ,POINTZ = ['IsPoint']
    ,POLYLINEZ = ['IsLine','IsPolyline']
    ,POLYGONZ = ['IsPolyline']   #Doesn't check closed
    ,MULTIPOINTZ = ['IsPoints']  # see MULTIPOINT
    ,POINTM = ['IsPoint']
    ,POLYLINEM = ['IsLine','IsPolyline']
    ,POLYGONM = ['IsPolyline']   #Doesn't check closed 
    ,MULTIPOINTM = ['IsPoints']  # see MULTIPOINT
                                            )  

def check_is_specified_obj_type(obj, shp_type):   #e.g. polyline
    # type(str) -> bool

    allowers = Rhino_obj_checker_Shp_file_shape_map[ shp_type]
    return any( getattr(rs, allower )( obj ) for allower in allowers)

Rhino_obj_getter_code_Shp_file_shape_map = dict( NULL = None
                                            ,POINT = 1          # Untested.  TODO
                                            ,MULTIPATCH = 32    # Unsupported.  Complicated.  TODO!
                                            ,POLYLINE = 4
                                            ,POLYGON = 4  
                                            ,MULTIPOINT = 2     # Untested.  TODO
                                            ,POINTZ = 1         
                                            ,POLYLINEZ = 4
                                            ,POLYGONZ = 4   
                                            ,MULTIPOINTZ = 2 
                                            ,POINTM = 1
                                            ,POLYLINEM = 4
                                            ,POLYGONM = 4  
                                            ,MULTIPOINTM = 2                                              )  

def get_all_shp_type_Rhino_objects(shp_type='POLYLINEZ'):
    #type (None) -> list
    return rs.ObjectsByType( Rhino_obj_getter_code_Shp_file_shape_map[shp_type]
                            ,select=False
                            ,state=0)

Rhino_obj_adder_Shp_file_shape_map = dict( NULL = None
                                ,POINT = 'AddPoint'
                                ,MULTIPATCH = 'AddMesh'    # Unsupported.  Complicated.  TODO!
                                ,POLYLINE = 'AddPolyline'
                                ,POLYGON = 'AddPolyline'   # check Pyshp closes them
                                ,MULTIPOINT = 'AddPoints'
                                ,POINTZ = 'AddPoint'
                                ,POLYLINEZ = 'AddPolyline'
                                ,POLYGONZ = 'AddPolyline'   # check Pyshp closes them
                                ,MULTIPOINTZ = 'AddPoints'
                                ,POINTM = 'AddPoint'
                                ,POLYLINEM = 'AddPolyline'
                                ,POLYGONM = 'AddPolyline'    # check Pyshp closes them
                                ,MULTIPOINTM = 'AddPoints'
                                )  

def get_objs_and_OrderedDicts( 
                              options = module_opts['options']
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
#
# 
def nick_names_that_map_to(names, name_map):
    #type(list, namedtuple) -> list
    if isinstance(names, str):
        names = [names]
    #nick_names = [nick_name for nick_name, mapped_names in name_map._asdict().items()
    #              if (nick_name not in names and 
    #                  any((name == mapped_names or name in mapped_names) for name in names))]
    #nick_names += nick_names_that_map_to(nick_names, name_map)
    #nick_names += names

    nick_names = [nick_name for nick_name in name_map._fields if getattr(name_map, nick_name) in names
                                                                and nick_name not in names] 
    if nick_names == []:
        return names
    else:
        return nick_names_that_map_to(nick_names + names, name_map)


def are_GhPython_components_in_GH(compnt, names):
    #type(str)->bool
    doc = compnt.Attributes.Owner.OnPingDocument() #type: ignore
    return any( type(GH_component) is GhPython.Component.ZuiPythonComponent 
                and GH_component.NickName in names
                for GH_component in doc.Objects
              )
#
#
class Connected_Components():
    IO = {'upstream':'Input', 'downstream':'Output'}
    connected = {'upstream':'Sources', 'downstream':'Recipients'}
                    
    def __call__(self, up_or_downstream, Params):
        #type(str, type[any]) -> bool
        assert up_or_downstream in self.keys
        return [comp.Attributes.GetTopLevel.DocObject
                for param in getattr(Params
                                    ,self.IO[up_or_downstream]
                                    ) 
                for comp in getattr(param
                                   ,self.connected[up_or_downstream]
                                   )
                ]
connected_components = Connected_Components()

def downstream_components(Params):
    return [recipient.Attributes.GetTopLevel.DocObject
            for param in Params.Output 
            for recipient in param.Recipients
            ]

def are_any_GhPython_comps(up_or_downstream, names, Params):
    #type(str, list, type[any])-> bool
    comps = connected_components(up_or_downstream, Params) #compnt, Params)
    GhPython_compnt_NickNames = [ comp.NickName for comp in comps
                                if type( comp.Attributes.GetTopLevel.DocObject ) 
                                   is GhPython.Component.ZuiPythonComponent
                                ]
    return ( any(name in GhPython_compnt_NickNames 
                for name in names
                )
            or
            any(are_any_GhPython_comps(up_or_downstream, names, comp.Params) 
                for comp in comps
                if hasattr(comp, 'Params') 
                ) 
            )
            
def are_GhPython_downstream(names, Params):
    comps = downstream_components(Params) #compnt, Params)
    GhPython_compnt_NickNames = [ comp.NickName for comp in comps
                                  if type( comp.Attributes.GetTopLevel.DocObject ) 
                                     is GhPython.Component.ZuiPythonComponent
                                ]
    return ( any(name in GhPython_compnt_NickNames 
                 for name in names
                 )
             or
             any(are_GhPython_downstream(names, comp.Params) 
                 for comp in comps
                 if hasattr(comp, 'Params') 
                 ) 
            )

up_or_downstream_dict = dict(before = 'upstream'
                            ,after =  'downstream'
                            )

def insert_tool(compnt
               ,before_or_after
               ,tools
               ,Params
               ,tool_to_insert
               ,is_target
               ,not_target
               ):
    #type(type[any], str, list, type[any], class, function, list) -> list
    assert before_or_after in ('before', 'after')
    up_or_downstream = up_or_downstream_dict[before_or_after]
    offset = 1 if before_or_after == 'after' else 0
    if any(func_name(tool) not in not_target for tool in tools):  
                    # Not just last tool.  Else no point checking more
                    # than one downstream component?  The user may 
                    # wish to do other stuff after the tool
                    # and name_map is now a meta option too.
        already_have_tool = [name for name, tool_list in tools_dict.items() 
                            if tool_to_insert in tool_list]
                        # tools_dict is keyed on all present nick names 
                        # as well as names of tools defined in this module
        debug(already_have_tool)
        debug(tools_dict)
        #if (  not are_GhPython_components_in_GH(compnt, already_have_tool) and

        name_map = compnt.opts['metas'].name_map
        debug(name_map)

        nick_names = nick_names_that_map_to(func_name(tool_to_insert), name_map)
        nick_names += already_have_tool
        debug(nick_names)

        tool_in_other_components = are_any_GhPython_comps(up_or_downstream
                                                         ,nick_names
                                                         ,Params
                                                         )

        debug('tool_in_other_components == ' 
              + str(not tool_in_other_components) 
             )
        if  not tool_in_other_components:
                             # check tool not already there in another 
                             # component that will be executed next.
                             # TODO: None in entire canvas is too strict?
            for i, tool in enumerate(tools):
                debug('is_target(tool) : ' + str(is_target(tool)))
                debug('tool : ' + str(tool))
                if before_or_after == 'after':
                    tools_run_anyway = tools[i:] 
                else:
                    tools_run_anyway = tools[:i] 

                if is_target(tool) and tool_to_insert not in tools_run_anyway:
                         # check tool not already inserted 
                         # in tools after specials
                    output('Inserting tool : ' + str(tool_to_insert), 'INFO')
                    tools.insert(i + offset, tool_to_insert)
    return tools

# def insert_tool_after_targets(   compnt
#                                 ,tools
#                                 ,Params
#                                 ,tool_to_insert
#                                 ,is_target
#                                 ,not_target
#                                 ):
#     if any(func_name(tool) not in not_target for tool in tools):  
#                     # Not just last tool.  Else no point checking more
#                     # than one downstream component?  The user may 
#                     # wish to do other stuff after the tool
#                     # and name_map is now a meta option too.
#         already_have_tool = [name for name, tool_list in tools_dict.items() 
#                             if tool_to_insert in tool_list]
#                         # tools_dict is keyed on all present nick names 
#                         # as well as names of tools defined in this module
#         debug(already_have_tool)
#         debug(tools_dict)
#         #if (  not are_GhPython_components_in_GH(compnt, already_have_tool) and

#         name_map = compnt.opts['metas'].name_map
#         debug(name_map)

#         nick_names = nick_names_that_map_to(func_name(tool_to_insert), name_map)
#         nick_names += already_have_tool
#         debug(nick_names)


#         debug('not are_GhPython_downstream(nick_names, Params) == ' 
#                + str(not are_GhPython_downstream(nick_names, Params)) )
#         if  ( not are_GhPython_downstream(nick_names, Params)     ):
#                              # check tool not already there in another 
#                              # component that will be executed next.
#                              # TODO: None in entire canvas is too strict?
#             for i, tool in enumerate(tools):
#                 debug('is_target(tool) : ' + str(is_target(tool)))
#                 debug('tool : ' + str(tool))
#                 if is_target(tool) and tool_to_insert not in tools[i:]:
#                          # check tool not already inserted 
#                          # in tools after specials
#                     output('Inserting tool : ' + str(tool_to_insert), 'INFO')
#                     tools.insert(i + 1, tool_to_insert)
#     return tools


#        print [x.Name for x in [r.Attributes.GetTopLevel.DocObject for x in self.Params.Output for r in x.Recipients][0].Params.Output]
#
#
class Tool(ABC):    #Template for tools that can be run by run_tools()
                    # Subclass of this is not enforced, to permit tools from
                    # functions with attributes via ducktyping
    @abstractmethod
    def args(self):
        return ()   # Only the order need correspond to 
                # __call__'s args. The names can be 
                # different.  The ones in the args tuple
                # are used as keys in vals_dict.  
                # show['Inputs'] defines the
                # input Param names of the component 

    @abstractmethod
    def __call__(self, *args):
        assert len(args) == len(self.args)
        '''  Main tool function'''
        retcode=0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    @abstractmethod
    def retvals(self): 
        return ('retcode',) # strings of variable names inside __call__, to be used 
                 # keys in vals_dict.  show['Outputs'] defines the required 
                 # output Param names on the 
                 # GH component

    @abstractmethod
    def show(self):
        return dict(Inputs = ()
                   ,Outputs = ()
                   )


def run_tools(tools
             ,args_dict
             ):  #f_name, gdm, opts):
    #type(list[Tool], dict)-> dict

    if not isinstance(tools, list):
        tools = list(tools)
    invalid_tools = [tool for tool in tools if not (isinstance(tool, Tool) or quacks_like(Tool, tool))]
    if invalid_tools:
        raise ValueError(output('Invalid tool(s) == ' + str(invalid_tools),'ERROR'))
    
    opts = args_dict['opts']
    metas = opts['metas']
    name_map = metas.name_map._asdict()

    #tool_names = []
    #assert not any(key == name_map[key] for key in name_map)
    # return_component_names checked for clashes and cycles etc.

    # def get_tools(name):
    #     for tool_name in name_map[name]:
    #         if tool_name in name_map:
    #             tool_names += get_tools(tool_name)  
    #         else:
    #             tool_names += [tool_name]

    # assert len(tool_names) == len(tools)

    vals_dict = args_dict 
                #OrderedDict( [   ('f_name', f_name)
                #                ,('gdm', gdm)
                #                ,('opts', opts)
                #             ]
                #            )

    debug(tools)                            
    for tool in tools:
        debug(tool)


        inputs = [vals_dict.get(input, None) for input in tool.args]
        retvals = tool( *inputs)
                        #  if input not in (('Data','Geom','go')
                        #  +opt)] 
                        # vals_dict['f_name']
                        #,vals_dict['gdm']
                        #,vals_dict['opts'] 
                        #)
        vals_dict.update( OrderedDict(zip(tool.retvals, retvals)) )
        vals_dict.setdefault( 'file'
                            , vals_dict.get('f_name')
                            )
        vals_dict['OK'] = (vals_dict['retcode'] == 0)

        retcode = vals_dict['retcode']
        debug(' return code == ' + str(retcode))
        if retcode != 0:
            raise Exception(output(  'Tool ' + func_name(tool) + ' exited '
                                    +'with status code ' 
                                    + str(retcode)
                                    ,'ERROR'
                                    )
                            )

    return vals_dict        
#
#
#############################################################################################################################


#############################################################################################################################
# Main component tool functions
#
#
class GetObjectsFromRhino(Tool):
    args = ('gdm', 'opts') # Only the order need correspond to the 
                           # function's args. The names can be 
                           # different.  The ones in the args tuple
                           # are used as keys in vals_dict and for 
                           # input Param names on the component
    component_inputs = ('go', args[1]) # 'Geom', 'Data') + args
    
    def __call__(self, geom_data_map, opts):
        #type(str, dict, dict) -> int, str, dict, list

        options = opts['options']
        #if 'ghdoc' not in globals():
        #    global ghdoc
        #    ghdoc = sc.doc  

        sc.doc = Rhino.RhinoDoc.ActiveDoc 
        
        #rhino_groups_and_objects = make_gdm(get_objs_and_OrderedDicts(options))
        gdm = make_gdm(get_objs_and_OrderedDicts(
                                                options
                                                ,get_all_shp_type_Rhino_objects
                                                ,get_all_groups
                                                ,get_members_of_a_group
                                                ,lambda *args, **kwargs : {} 
                                                ,check_is_specified_obj_type
                                                            ) 
                                )
        # lambda : {}, as Usertext is read elsewhere, in read_Usertext




        debug('First objects read: \n' + '\n'.join(str(x) for x in gdm.keys()[:3]))
        if len(gdm) > 0:
            debug('type(gdm[0]) == ' + type(gdm.keys()[0]).__name__ )
        debug('....Last objects read: \n' + '\n'.join(str(x) for x in gdm.keys()[-3:]))

        gdm = override_gdm_with_gdm(gdm, geom_data_map, opts)
        sc.doc = ghdoc # type: ignore 

        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]

    retvals = 'retcode', 'gdm'
    show = dict(Input = component_inputs
               ,Output = ('OK', 'Geom') + retvals[1:]
               )


get_Geom = GetObjectsFromRhino()




class ReadUsertext(Tool):
    args = ('gdm', 'opts')
    component_inputs = ('go', 'Data', args[0])

    def __call__(self, gdm, opts):
        #type(str, dict, dict) -> int, str, dict, list

        debug('Starting read_Usertext... ')
        options = opts['options']

        # if (options.auto_get_Geom and
        #    (not geom_data_map or not hasattr(geom_data_map, 'keys') or
        #    (len(geom_data_map.keys()) == 1 and geom_data_map.keys()[0] == tuple() ))):
        #     #
        #     retcode, gdm = get_Geom( geom_data_map
        #                             ,opts
        #                             )
        #     #
        # else:
        #     retcode = 0
        #     gdm = geom_data_map
        #if opts['options'].read_overides_Data_from_Usertext:

        read_Usertext_as_tuples = get_OrderedDict()
        for obj in gdm:
            gdm[obj].update(read_Usertext_as_tuples(obj))

        # get_OrderedDict() will get Usertext from both the GH and Rhino docs
        # switching the target to RhinoDoc if needed, hence the following line 
        # is important:
        sc.doc = ghdoc # type: ignore 
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]

    retvals = 'retcode', 'gdm'

    show = dict(Input = component_inputs
               ,Output = ('OK', 'Geom', 'Data') + retvals[1:]
               )

read_Usertext = ReadUsertext()


class WriteShapefile(Tool):
    args = ('file', 'gdm', 'opts')
    component_inputs = ('go', args[0], 'Geom', 'Data') + args[1:]

    def __call__(self, f_name, geom_data_map, opts):
        #type(str, dict, dict) -> int, str, dict, list
        
        options = opts['options']

        shp_type = options.shp_file_shape_type            
        #print geom_data_map
        # if (options.auto_read_Usertext and
        #         (not geom_data_map or not hasattr(geom_data_map, 'values')
        #         or all(len(v) ==0  for v in geom_data_map.values()))):
        #     retcode, f_name, geom_data_map = read_Usertext(  f_name
        #                                                     ,geom_data_map
        #                                                     ,opts
        #                                                     )

        format_string = options.rhino_user_text_key_format_str_to_read
        pattern = make_regex( format_string )

        def pattern_match_key_names(x):
            #type: (str)-> object #re.MatchObject

            return match(pattern, x) 
            #           if m else None #, m.group('fieldtype'), 
                                                # m.group('size') if m else None
                                                # can get 
                                                # (literal_text, field_name, 
                                                #                  f_spec, conv) 
                                                # from iterating over
                                                # string.Formatter.parse(
                                                #                 format_string)

        def get_list_of_lists_from_tuple(obj):
            #debug(obj)
            #if is_an_obj_in_GH_or_Rhino(obj):
            target_doc = is_an_obj_in_GH_or_Rhino(obj)    
            if target_doc:
                sc.doc = target_doc
                if check_is_specified_obj_type(obj, shp_type):
                    return [get_points_list_from_geom_obj(obj, shp_type)]
                else:
                    return []      
                #elif is_a_group_in_GH_or_Rhino(obj):
            else:
                target_doc = is_a_group_in_GH_or_Rhino(obj)    
                if target_doc:
                    sc.doc = target_doc                  
                    return [get_points_list_from_geom_obj(y, shp_type) 
                            for y in get_members_of_a_group(obj)
                            if check_is_specified_obj_type(y, shp_type)]
                else:
                    return []

        def shape_IDer(obj):
            return obj #tupl[0].ToString() # uuid

        def find_keys(obj):
            return geom_data_map[obj].keys() #tupl[1].keys() #rs.GetUserText(x,None)

        def get_data_item(obj, key):
            return geom_data_map[obj][key] #tupl[1][key]

        if not f_name:  
            if (   options.shape_file_to_write_Rhino_data_to_from_sDNA_GH
                and isdir(dirname( options.shape_file_to_write_Rhino_data_to_from_sDNA_GH ))   ):
                f_name = options.shape_file_to_write_Rhino_data_to_from_sDNA_GH
            else:
                f_name = options.Rhino_doc_path.rpartition('.')[0] + options.shp_file_extension
                            # file extensions are actually optional in PyShp, 
                            # but just to be safe and future proof we remove
                            # '.3dm'                                        

        #debug('Type of geom_data_map == '+ type(geom_data_map).__name__)                         
        #debug('Size of geom_data_map == ' + str(len(geom_data_map)))
        #debug('Gdm keys == ' + ' '.join( map(lambda x : x[:5],geom_data_map.keys() )) )
        #debug('Gdm.values == ' + ' '.join(map(str,geom_data_map.values())))
        sc.doc = Rhino.RhinoDoc.ActiveDoc 
        (retcode, f_name, fields, gdm) = ( 
                            write_from_iterable_to_shapefile_writer(
                                                geom_data_map
                                        #my_iter 
                                                ,f_name 
                                        #shp_file 
                                                ,get_list_of_lists_from_tuple 
                                        # shape_mangler, e.g. start_and_end_points
                                                ,shape_IDer
                                                ,find_keys 
                                        # key_finder
                                                ,pattern_match_key_names 
                                        #key_matcher
                                                ,get_data_item 
                                        #value_demangler e.g. rs.GetUserText
                                                ,shp_type 
                                        #"POLYLINEZ" #shape
                                                ,options 
                                                ,None 
                                        # field names
                            )
        ) 
        # get_list_of_lists_from_tuple() will 
        # switch the targeted file to RhinoDoc if needed, hence the following line 
        # is important:
        sc.doc = ghdoc # type: ignore 
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]

    retvals = 'retcode', 'f_name', 'gdm'

    show = dict(Input = component_inputs
               ,Output = ('OK', 'file') #+ write_shp.retvals[2:]
               )

write_shapefile = WriteShapefile()

def create_new_groups_layer_from_points_list(
     options = module_opts['options']
    ,make_new_group = make_new_group
    ,add_objects_to_group = add_objects_to_group
    ,Rhino_obj_adder_Shp_file_shape_map = Rhino_obj_adder_Shp_file_shape_map
                    ):
    #type(namedtuple, function, function, dict) -> function
    shp_type = options.shp_file_shape_type            
    rhino_obj_maker = getattr(rs, Rhino_obj_adder_Shp_file_shape_map[shp_type])

    def g(obj, rec):
        objs_list = []
        
        for points_list in obj:
            #debug(points_list)
            objs_list += [rhino_obj_maker(points_list) ] 
    # Creates not necessarily returned Rhino object as intentional side effect
        if len(objs_list) > 1:
            new_group_name = make_new_group()
            add_objects_to_group(objs_list, new_group_name)
            return new_group_name
        elif len(objs_list)==1:
            return objs_list[0]
        else: 
            return None
    return g

def get_shape_file_rec_ID(options = module_opts['options']): 
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

class ReadShapefile(Tool):
    #type() -> function
    args = ('file', 'gdm', 'opts')
    component_inputs = ('go', args[0], 'Geom') + args[1:]

    def __call__(self, f_name, geom_data_map, opts ):
        #type(str, dict, dict) -> int, str, dict, list
        options = opts['options']

        ( fields
        ,recs
        ,shapes
        ,bbox ) = get_fields_recs_and_shapes_from_shapefile( f_name )

        if not recs:
            output('No data read from Shapefile ' + f_name + ' ','WARNING')
            return 1, f_name, geom_data_map, None    
            
        if not shapes:
            output('No shapes in Shapefile ' + f_name + ' ','WARNING')
            return 1, f_name, geom_data_map, None

        if not bbox:
            output('No Bounding Box in Shapefile.  '
                   + f_name 
                   + ' '
                   +'Supply bbox manually or create rectangle to plot legend.  '
                   ,'WARNING')
            

        field_names = [ x[0] for x in fields ]

        debug('options.uuid_shp_file_field_name in field_names == ' + str(options.uuid_shp_file_field_name in field_names))
        debug(field_names)

        shapes_to_output = ([shp.points] for shp in shapes )
        
        obj_key_maker = create_new_groups_layer_from_points_list( options ) 



        if not options.create_new_groups_layer_from_shapefile:   #TODO: put new objs in a new layer or group
            obj_key_maker = get_shape_file_rec_ID(options) # key_val_tuples
            # i.e. if options.uuid_shp_file_field_name in field_names but also otherwise
        
            if isinstance(geom_data_map, dict) and len(geom_data_map) == len(recs):
                # figuring out an override for different number of overrided geom objects
                # to shapes/recs is to open a large a can of worms.  Unsupported.
                # If the override objects are in Rhino anyway then the uuid field in the shape
                # file will be picked up in any case in get_shape_file_rec_ID
                if sys.version_info.major < 3:
                    shape_keys = geom_data_map.viewkeys()  
                else: 
                    shape_keys = geom_data_map.keys()
                shapes_to_output = [shp_key for shp_key in shape_keys]
                    # These points shouldn't be used, as by definition they 
                    # come from objects that already
                    # exist in Rhino.  But if they are to be used, then use this!
                #debug(shapes_to_output)    


        shp_file_gen_exp  = izip( shapes_to_output
                                ,(rec.as_dict() for rec in recs)
                                )
        
        #(  (shape, rec) for (shape, rec) in 
        #                                       izip(shapes_to_output, recs)  )              
        sc.doc = Rhino.RhinoDoc.ActiveDoc
        gdm = make_gdm(shp_file_gen_exp, obj_key_maker)
        sc.doc = ghdoc # type: ignore
        
        dot_shp = options.shp_file_extension
        csv_f_name = f_name.rpartition('.')[0] + dot_shp + '.names.csv'
        sDNA_fields = {}
        if isfile(csv_f_name):
            f = open(csv_f_name, 'rb')
            f_csv = csv.reader(f)
            sDNA_fields = [OrderedDict( (line[0], line[1]) for line in f_csv )]
            abbrevs = [line[0] for line in f_csv ]


        debug(bbox)

        #override_gdm_with_gdm(gdm, gdm, opts)   # TODO:What for?

        if options.delete_shapefile_after_reading and isfile(f_name): 
            os.remove(f_name)  # TODO: Fix, currently Win32 error

        retcode = 0

        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]

    retvals = 'retcode', 'gdm', 'abbrevs', 'sDNA_fields', 'bbox', 'opts'
    show = dict(Input = component_inputs
               ,Output = ('OK', 'Geom', 'Data') + retvals[1:]
               ) 


read_shapefile = ReadShapefile()

    #keys=[]
    #if options.create_new_groups_layer_from_shapefile:
    #    Geometry =  [] # only overwrites local variable in this function
    #    rs.AddLayer(name = split(f_name)[1] ) #.rpartition('.')[0])
    #    for group in shapes:
    #        if len(group) > 1:   #multi-polyline group
    #            new_group = rs.AddGroup()
    #            polylines = []
    #            for list_of_points_lists in group:
    #                polylines += rs.AddPolyline( list_of_points_lists )
    #            rs.AddObjectsToGroup(polylines, new_group)
    #            Geometry += new_group
    #        else:          # single polyline group (pyshp returns nested)
    #            Geometry += rs.AddPolyline(group[0])
    #    keys = Geometry
    #elif options.uuid_shp_file_field_name in field_names:
    #    ID_index = field_names.index( options.uuid_shp_file_field_name )    
    #    keys = [rec[ID_index] for rec in recs]
    #if keys:
    #    Data = OrderedDict(   ( key, dict(zip(field_names, rec)) ) 
    #                                        for key, rec in zip(keys, recs)   )
    #else:
    #    Data = [ dict(zip(field_names, rec)) for rec in recs]
    #
    # return 0, f_name, gdm, opts



class WriteUsertext(Tool):
    args = ('gdm', 'opts')
    component_inputs = ('go', 'Geom', 'Data') + args


    def __call__(self, gdm, opts):
        #type(str, dict, dict) -> int, str, dict, list
        options = opts['options']

        date_time_of_run = asctime()

        def write_dict_to_UserText_on_obj(d, rhino_obj):
            #type(dict, str) -> None
            if not isinstance(d, dict):
                return
            
            #if is_an_obj_in_GH_or_Rhino(rhino_obj):
                # Checker switches GH/ Rhino context
            
            target_doc = is_an_obj_in_GH_or_Rhino(rhino_obj)    
            if target_doc:
                sc.doc = target_doc        
                existing_keys = get_obj_keys(rhino_obj)
                #TODO Move key pattern matching into ReadSHP
                if options.uuid_shp_file_field_name in d:
                    obj = d.pop( options.uuid_shp_file_field_name )
                
                for key in d:

                    s = options.sDNA_output_user_text_key_format_str_to_read
                    UserText_key_name = s.format(name = key
                                                ,datetime = date_time_of_run
                                                )
                    
                    if not options.overwrite_UserText:

                        for i in range(0, options.max_new_UserText_keys_to_make):
                            tmp = UserText_key_name 
                            tmp += options.duplicate_UserText_key_suffix.format(i)
                            if tmp not in existing_keys:
                                break
                        UserText_key_name = tmp
                    else:
                        if not options.suppress_overwrite_warning:
                            output( "UserText key == " 
                                    + UserText_key_name 
                                    +" overwritten on object with guid " 
                                    + str(rhino_obj)
                                    ,'WARNING'
                                    )
                    write_obj_val(rhino_obj, UserText_key_name, str( d[key] ))
            else:
                output('Object: ' 
                    + key[:10] 
                    + ' is neither a curve nor a group. '
                    ,'INFO'
                    )

        for key, val in gdm.items():
            #if is_a_curve_in_GH_or_Rhino(key):
            target_doc = is_an_obj_in_GH_or_Rhino(key)    
            if target_doc:
                sc.doc = target_doc          
                group_members = [key]
            else:
                target_doc = is_a_group_in_GH_or_Rhino(key)    
                if target_doc:
                    sc.doc = target_doc              
                    #elif is_a_group_in_GH_or_Rhino(key):
                    # Switches context, but will be switched again
                    # when members checked
                    group_members = get_members_of_a_group(key)
                    # Can't use rs.SetUserText on a group name.  Must be a uuid.
                else:
                    group_members = [key]

                
            for member in group_members:
                write_dict_to_UserText_on_obj(val, member)

        sc.doc = ghdoc # type: ignore 
        
        retcode = 0

        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    retvals = ('retcode', 'gdm')
    show = dict(Input = component_inputs
               ,Output = ('OK',) #[0] + ('Geom', 'Data') + write_Usertext.retvals[1:]
               )

write_Usertext = WriteUsertext()


class BakeUsertext(Tool):
    args = ('gdm', 'opts')
    component_inputs = ('go', 'Geom') + args


    def __call__(self, geom_data_map, opts):
        #type(str, dict, dict) -> int, str, dict, list  

        gdm = OrderedDict()
        for obj in geom_data_map:
            doc_obj = ghdoc.Objects.Find(obj)
            if doc_obj:
                geometry = doc_obj.Geometry
                attributes = doc_obj.Attributes
                if geometry:
                    add_to_Rhino = Rhino.RhinoDoc.ActiveDoc.Objects.Add 
                    # trying to avoid constantly switching sc.doc

                    gdm[add_to_Rhino(geometry, attributes)] = geom_data_map[obj] # The bake
        
        retcode, gdm = write_Usertext(gdm, opts)
        # write_data_to_USertext context switched when checking so will move
        #sc.doc = Rhino.RhinoDoc.ActiveDoc on finding Rhino objects.
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]

    retvals = ('retcode',) #'f_name', 'gdm'
    show = dict(Input = component_inputs
               ,Output = ('OK',) #bake_Usertext.retvals #[0] + ('Geom', 'Data') + bake_Usertext.retvals[1:]
               )

bake_Usertext = BakeUsertext()



def linearly_interpolate(x, x_min, x_mid, x_max, y_min, y_max):
    # type(Number, Number, Number, Number, Number, Number) -> Number
    assert x_min != x_max
    return y_min + ( (y_max - y_min) * (x - x_min) / (x_max - x_min) )


def quadratic_mid_spline(x, x_min, x_mid, x_max, y_min, y_max):
    # type(Number, Number, Number, Number, Number, Number) -> Number
    assert x_min != x_mid != x_max    
    retval = y_max*((x - x_max)*(x - x_min)/((x_mid - x_max)*(x_mid - x_min)))
    #retval == 0 at x == x_min and x == x_max 
    #retval == y_max at x == x_mid
    retval += y_min
    return retval


def log_spline(x, x_min, base, x_max, y_min, y_max):        
    # type(Number, Number, Number, Number, Number, Number) -> Number
    assert x_min != x_max
    log_2 = log(2, base)

    return y_min + (y_max / log_2) * log(  1 + ( (x-x_min)/(x_max-x_min) )
                                          ,base  )


def exp_spline(x, x_min, base, x_max, y_min, y_max):
    # type(Number, Number, Number, Number, Number, Number) -> Number
    assert y_min != 0 != x_max - x_min
    return y_min * pow(base, ((x - x_min)/(x_max - x_min))*log(y_max/ y_min
                                                              ,base 
                                                              )
                       )


#valid_renormalisers = ['linear', 'exponential', 'logarithmic']
splines = dict(zip(  valid_re_normalisers 
                    ,[   linearly_interpolate
                        ,exp_spline
                        ,log_spline
                        ]
                   )
               )


def three_point_quadratic_spline(x, x_min, x_mid, x_max, y_min, y_mid, y_max):
    #z = 2
    z =  quadratic_mid_spline(x, x_mid, x_min, x_max, 0, y_min) #y_min*((x - x_max)*(x - x_mid)/((x_min - x_max)*(x_min - x_mid)))
    z += quadratic_mid_spline(x, x_min, x_mid, x_max, 0, y_mid) #y_mid*((x - x_max)*(x - x_min)/((x_mid - x_max)*(x_mid - x_min)))
    z += quadratic_mid_spline(x, x_min, x_max, x_mid, 0, y_max) #y_max*((x - x_mid)*(x - x_min)/((x_max - x_mid)*(x_max - x_min)))
    return max(0, min( z, 255))        


def map_f_to_tuples(f, x, x_min, x_max, tuples_min, tuples_max): 
    # (x,x_min,x_max,triple_min = rgb_min, triple_max = rgb_max)
    return [f(x, x_min, x_max, a, b) for (a, b) in zip(tuples_min, tuples_max)]


def map_f_to_three_tuples(f
                         ,x
                         ,x_min
                         ,x_med
                         ,x_max
                         ,tuple_min
                         ,tuple_med
                         ,tuple_max
                         ): 
    #type(function, Number, Number, Number, Number, tuple, tuple, tuple)->list
    # (x,x_min,x_max,triple_min = rgb_min, triple_max = rgb_max)
    return [f(x, x_min, x_med, x_max, a, b, c) 
            for (a, b, c) in zip(tuple_min, tuple_med, tuple_max)]


def change_line_thickness(obj, width, rel_or_abs = False):  #The default value in Rhino for wireframes is zero so rel_or_abs==True will not be effective if the width has not already been increased.
    #type(str, Number, bool)
    x = rs.coercerhinoobject(obj, True, True)
    x.Attributes.PlotWeightSource = Rhino.DocObjects.ObjectPlotWeightSource.PlotWeightFromObject
    if rel_or_abs:
        width = width * x.Attributes.PlotWeight
    x.Attributes.PlotWeight = width
    x.CommitChanges()


class ParseData(Tool):
    args = ('gdm', 'opts')
    component_inputs = ('go', 'Geom', 'Data', args[0], 'field', 'plot_max', 'plot_min', 'classes') + args[1:]

    def __call__(self, geom_data_map, opts):
        #type(str, dict, dict) -> int, str, dict, list
        # Note!  opts can be mutated.
        options = opts['options']

        field = options.field

        data = [ val[field] for val in geom_data_map.values()]
        debug('data == ' + str(data[:3]) + ' ... ' + str(data[-3:]))
        x_max = max(data) if options.plot_max is None else options.plot_max
        x_min = min(data) if options.plot_min is None else options.plot_min
        # bool(0) == False so in case x_min==0 we can't use 
        # if options.plot_min if options.plot_min else min(data) 


        no_manual_classes = (not isinstance(options.classes, list)
                            or not all( isinstance(x, Number) 
                                            for x in options.classes
                                        )
                            )

        if options.sort_data or (no_manual_classes 
           and options.class_spacing == 'equal_spacing'  ):
            # 
            gdm = OrderedDict( sorted(geom_data_map.items()
                                    ,key = lambda tupl : tupl[1][field]
                                    ) 
                            )
        else:
            gdm = geom_data_map

        #valid_class_spacers = valid_renormalisers + ['equal number of members'] 

        param={}
        param['exponential'] = param['logarithmic'] = options.base

        if no_manual_classes:
            m = options.number_of_classes
            if options.class_spacing == 'equal number of members':
                n = len(gdm)
                objs_per_class, rem = divmod(n, m)
                # assert gdm is already sorted
                classes = [ val[field] for val in 
                                    gdm.values()[objs_per_class:m*objs_per_class:objs_per_class] 
                                ]  # classes include their lower bound
                debug('num class boundaries == ' + str(len(classes)))
                debug(options.number_of_classes)
                debug(n)
                assert len(classes) + 1 == options.number_of_classes
            else: 
                classes = [
                    splines[options.class_spacing](  
                                    i
                                    ,0
                                    ,param.get(options.class_spacing, 'Not used')
                                    ,m + 1
                                    ,x_min
                                    ,x_max
                                                )     for i in range(1, m + 1) 
                                    ]
        else:
            classes = options.classes
        
        # opts['options'] = opts['options']._replace(
        #                                     classes = classes
        #                                    ,plot_max = x_max
        #                                    ,plot_min = x_min
        #                                                         )


        def re_normaliser(x, p = param.get(options.re_normaliser, 'Not used')):
            return splines[options.re_normaliser](   x
                                                    ,x_min
                                                    ,p
                                                    ,x_max
                                                    ,x_min
                                                    ,x_max
                                                )
        
        if not options.all_in_class_same_colour:
            classifier = re_normaliser
        elif options.re_normaliser:
            #'linear' # exponential, logarithmic
            def classifier(x): 

                highest_lower_bound = x_min if x < classes[0] else max(y 
                                                for y in classes + [x_min] 
                                                if y <= x                       )
                #Classes include their lower bound
                least_upper_bound = x_max if x >= classes[-1] else min(y for y in classes + [x_max] 
                                        if y > x)

                return re_normaliser (0.5*(least_upper_bound + highest_lower_bound))

        #retvals = {}

        # todo:  '{n:}'.format() everything to apply localisation, 
        # e.g. thousand seperators


        mid_points = [0.5*(x_min + min(classes))]
        mid_points += [0.5*(x + y) for (x,y) in zip(  classes[0:-1]
                                                    ,classes[1:]  
                                                )
                    ]
        mid_points += [ 0.5*(x_max + max(classes))]
        debug(mid_points)

        locale.setlocale(locale.LC_ALL,  options.locale)

        x_min_s = options.num_format.format(x_min)
        upper_s = options.num_format.format(min( classes ))
        mid_pt_s = options.num_format.format( mid_points[0] )

        legend_tags = [options.first_legend_tag_format_string.format( 
                                                                lower = x_min_s
                                                                ,upper = upper_s
                                                                ,mid_pt = mid_pt_s
                                                                    )
                                                        ]
        for lower_bound, mid_point, upper_bound in zip( 
                                            classes[0:-1]
                                            ,mid_points[1:-1]
                                            ,classes[1:]  
                                                    ):
            
            lower_s = options.num_format.format(lower_bound)
            upper_s = options.num_format.format(upper_bound)
            mid_pt_s = options.num_format.format(mid_point)

            legend_tags += [options.inner_tag_format_string.format(
                                                    lower = lower_s
                                                    ,upper = upper_s
                                                    ,mid_pt = mid_pt_s 
                                                                )
                            ]

        lower_s = options.num_format.format(max( classes ))
        x_max_s = options.num_format.format(x_max)
        mid_pt_s = options.num_format.format(mid_points[-1])

        legend_tags += [options.last_legend_tag_format_string.format( 
                                                                lower = lower_s
                                                                ,upper = x_max_s 
                                                                ,mid_pt = mid_pt_s 
                                                                    )        
                        ]                                                       

        assert len(legend_tags) == options.number_of_classes == len(mid_points)

        debug(legend_tags)

        #first_legend_tag_format_string = 'below {upper}'
        #inner_tag_format_string = '{lower} - {upper}' # also supports {mid}
        #last_legend_tag_format_string = 'above {lower}'

        #retvals['max'] = x_max = max(data)
        #retvals['min'] = x_min = min(data)

        gdm = OrderedDict(zip( geom_data_map.keys() + legend_tags 
                            ,(classifier(x) for x in data + mid_points)
                            )
                        )
        plot_min, plot_max = x_min, x_max
        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    retvals = 'retcode', 'plot_min', 'plot_max', 'gdm', 'opts', 'classes'
    show = dict(Input = component_inputs
               ,Output = ('OK',) + retvals[1:3] + ('Data', 'Geom') + retvals[3:-1]
               )

parse_data = ParseData()


class RecolourObjects(Tool):
    args = ('gdm', 'opts')
    component_inputs = ('go', 'Data', 'Geom', 'bbox') + args


    def __call__(self, geom_data_map, opts):
        #type(str, dict, dict) -> int, str, dict, list
        # Note!  opts can be mutated.

        options = opts['options']
        
        field = options.field
        objs_to_parse = OrderedDict(  (k, v) for k, v in geom_data_map.items()
                                    if isinstance(v, dict) and field in v    
                                    )  # any geom with a normal gdm dict of keys / vals
        if objs_to_parse:
            ret_code, x_min, x_max, gdm_in, opts = parse_data(objs_to_parse, opts)
                                                                            
            debug(x_min)
            debug(x_max)
        else:
            gdm_in = {}
            x_min, x_max = options.plot_min, options.plot_max
            debug(options.plot_min)
            debug(options.plot_max)     

        debug(opts['options'].plot_min)
        debug(opts['options'].plot_max)

        objs_to_get_colour = OrderedDict( (k, v) for k, v in geom_data_map.items()
                                                if isinstance(v, Number) 
                                        )
        objs_to_get_colour.update(gdm_in)  # no key clashes possible unless some x
                                        # isinstance(x, dict) 
                                        # and isinstance(x, Number)
        if options.GH_Gradient:
            grad = getattr( GH_Gradient()
                        ,GH_Gradient_preset_names[options.GH_Gradient_preset])
            def get_colour(x):
                # Number-> Tuple(Number, Number, Number)
                # May need either rhinoscriptsyntax.CreateColor
                # or System.Drawing.Color.FromArgb and even 
                # Grasshopper.Kernel.Types.GH_Colour calling on the result to work
                # in Grasshopper
                return grad().ColourAt(linearly_interpolate( x
                                                            ,x_min
                                                            ,None
                                                            ,x_max
                                                            ,0 #0.18
                                                            ,1 #0.82
                                                            )
                                        )
        else:
            def get_colour(x):
                # Number-> Tuple(Number, Number, Number)
                # May need either rhinoscriptsyntax.CreateColor
                # or System.Drawing.Color.FromArgb and even 
                # Grasshopper.Kernel.Types.GH_Colour calling on the result to work
                # in Grasshopper
                rgb_col =  map_f_to_three_tuples( three_point_quadratic_spline
                                                ,x
                                                ,x_min
                                                ,0.5*(x_min + x_max)
                                                ,x_max
                                                ,tuple(options.rgb_min)
                                                ,tuple(options.rgb_mid)
                                                ,tuple(options.rgb_max)
                                                )
                bounded_colour = ()
                for channel in rgb_col:
                    bounded_colour += ( max(0, min(255, channel)), )
                return rs.CreateColor(bounded_colour)

        objs_to_recolour = OrderedDict( (k, v) for k, v in geom_data_map.items()
                                            if isinstance(v, Colour)  
                                    )
            
        objs_to_recolour.update( (key,  get_colour(val))
                                for key, val in objs_to_get_colour.items()
                                )


        legend_tags = OrderedDict()
        legend_first_pattern = make_regex(options.first_legend_tag_format_string)
        legend_inner_pattern = make_regex(options.inner_tag_format_string)
        legend_last_pattern = make_regex(options.last_legend_tag_format_string)

        legend_tag_patterns = (legend_first_pattern
                            ,legend_inner_pattern
                            ,legend_last_pattern
                            )


        GH_objs_to_recolour = OrderedDict()
        objects_to_widen_lines = []

        for obj, new_colour in objs_to_recolour.items():
            #debug(obj)
            if is_uuid(obj): # and is_an_obj_in_GH_or_Rhino(obj):
                target_doc = is_an_obj_in_GH_or_Rhino(obj)    
                if target_doc:
                    sc.doc = target_doc
                    if target_doc == ghdoc:
                        GH_objs_to_recolour[obj] = new_colour 
                    #elif target_doc == Rhino.RhinoDoc.ActiveDoc:
                    else:
                        rs.ObjectColor(obj, new_colour)
                        objects_to_widen_lines.append(obj)

                else:
                    raise ValueError(output( 'sc.doc == ' + str(sc.doc) 
                                            +' i.e. neither Rhinodoc.ActiveDoc '
                                            +'nor ghdoc'
                                            ,'ERROR'
                                            )
                                    )

            elif any(  bool(match(pattern, obj)) 
                        for pattern in legend_tag_patterns ):
                sc.doc = ghdoc
                legend_tags[obj] = rs.CreateColor(new_colour) # Could glitch if dupe
            else:
                raise NotImplementedError(output( 'Valid colour in Data but ' 
                                                    +'no geom obj or legend tag.'
                                                    ,'ERROR'
                                                )
                                        )

        sc.doc = ghdoc
        #[x.Geometry for x in list(GH_objs_to_recolour.keys())]
        #CustomPreview( list(GH_objs_to_recolour.keys())
        #              ,list(GH_objs_to_recolour.values())
        #              )


        keys = objects_to_widen_lines
        if keys:
            sc.doc = Rhino.RhinoDoc.ActiveDoc                             
            rs.ObjectColorSource(keys, 1)  # 1 => colour from object
            rs.ObjectPrintColorSource(keys, 2)  # 2 => colour from object
            rs.ObjectPrintWidthSource(keys, 1)  # 1 => print width from object
            rs.ObjectPrintWidth(keys, options.line_width) # width in mm
            rs.Command('_PrintDisplay _State=_On Color=Display Thickness='
                    +str(options.line_width)
                    +' _enter')
            #sc.doc.Views.Redraw()
            sc.doc = ghdoc


        # "Node in code"
        #pt = rs.CreatePoint(0, 0, 0)
        #bbox = BoundingBox(objs_to_recolour.keys, XYPlane(pt)) # BoundingBox(XYPlane

        #bbox_xmin = min(list(p)[0] for p in bbox.box.GetCorners()[:4] )
        #bbox_xmax = max(list(p)[0] for p in bbox.box.GetCorners()[:4] )
        #bbox_ymin = min(list(p)[1] for p in bbox.box.GetCorners()[:4] )
        #bbox_ymax = max(list(p)[1] for p in bbox.box.GetCorners()[:4] )

        debug(options)

        if options.legend_extent or options.bbox:
            if options.legend_extent:
                [legend_xmin
                ,legend_ymin
                ,legend_xmax
                ,legend_ymax] = options.legend_extent
                debug('legend extent == ' + str(options.legend_extent))
            elif options.bbox:
                bbox = [bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax] = options.bbox

                legend_xmin = bbox_xmin + (1 - 0.4)*(bbox_xmax - bbox_xmin)
                legend_ymin = bbox_ymin + (1 - 0.4)*(bbox_ymax - bbox_ymin)
                legend_xmax, legend_ymax = bbox_xmax, bbox_ymax
                
                debug('bbox == ' + str(bbox))


                #leg_frame = Rectangle( XYPlane(pt)
                #                      ,[legend_xmin, legend_xmax]
                #                      ,[legend_ymin, legend_ymax]
                #                      ,0
                #                      )

                plane = rs.WorldXYPlane()
                leg_frame = rs.AddRectangle( plane
                                            ,legend_xmax - legend_xmin
                                            ,legend_ymax - legend_ymin 
                                            )

                debug( 'Rectangle width * height == ' 
                       +str(legend_xmax - legend_xmin)
                       +' * '
                       +str(legend_ymax - legend_ymin)
                       )


                rs.MoveObject(leg_frame, [1.07*bbox_xmax, legend_ymin])
                #rs.MoveObject(leg_frame, [65,0]) #1.07*bbox_xmax, legend_ymin])

                # opts['options'] = opts['options']._replace(
                #                                     leg_frame = leg_frame 
                #                                                         )

                #debug(leg_frame)
                #leg_frame = sc.doc.Objects.FindGeometry(leg_frame)
                #leg_frame = sc.doc.Objects.Find(leg_frame)

        else:
            output('No legend rectangle dimensions.  ', 'INFO')
            leg_frame = None

    


        debug(leg_frame)

        #def c():
            #return GH_Colour(Color.FromArgb(r(0,255), r(0,255), r(0,255)))
            #return Color.FromArgb(r(0,255), r(0,255), r(0,255))
            #return rs.CreateColor(r(0,255), r(0,255), r(0,255))
        #tags=['Tag1', 'Tag2', 'Tag3', 'Tag4', 'Tag5']
        #colours = [c(), c(), c(), c(), c()]
        #rect = sc.doc.Objects.FindGeometry(leg_frame)
        #for k, v in legend_tags.items():
        #    Legend(Colour.FromArgb(*v), k, leg_frame)
        #Legend( [GH_Colour(Colour.FromArgb(*v)) for v in legend_tags.values()]
        #       ,list(legend_tags.keys()) 
        #       ,leg_frame
        #       )
        gdm = GH_objs_to_recolour
        leg_cols = list(legend_tags.values())
        leg_tags = list(legend_tags.keys())


        sc.doc =  ghdoc # type: ignore
        sc.doc.Views.Redraw()

        retcode = 0

        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    retvals = 'retcode', 'gdm', 'leg_cols', 'leg_tags', 'leg_frame', 'opts'
    show = dict(Input = component_inputs    
               ,Output = ('OK', 'Geom', 'Data') + retvals[1:]
               )
          # To recolour GH Geom with a native Preview component


#recolour_objects = recolour_objects_factory()
recolour_objects = RecolourObjects()


                  



#########################################################
#Grasshopper component auto add/remove output param rules
#
do_not_add = ['retcode'] # Won't be added automatically
#
do_not_remove = ('out'   # TODO: Removing Params has proved to be a 
                ,'OK'    #       glitch ridden hassle!  Why?
                ,'Data'
                ,'Geom'
                ,'file'
                ,'gdm'
                ,'a'
                ,'opts'
                ,'l_metas'
                ,'retcode' # But if user adds it, we won't remove it
                ,'classes'
                )
#
do_not_remove += default_metas._fields
do_not_remove += default_options._fields
do_not_remove += default_local_metas._fields
#########################################################





tools_dict = dict(get_Geom = get_Geom
                 ,read_Usertext = read_Usertext
                 ,write_shapefile = write_shapefile
                 ,read_shapefile = read_shapefile
                 ,write_Usertext = write_Usertext
                 ,bake_Usertext = bake_Usertext
                 ,parse_data = parse_data
                 ,recolour_objects = recolour_objects # Needed in iterable wrappers
                 )

support_component_names = list(tools_dict.keys())[:] # In Python 3, .keys() and 
                                                     # .values() are dict views
                                                     # not lists

special_names =           [  'sDNA_General'
                            ]

dev_tools = ['Python'
            ,'Self_test'
            ,'Build_components']

sDNA_GH_names = support_component_names + special_names + dev_tools




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

def make_new_component(name
                      ,category
                      ,subcategory
                      ,launcher_code
                      ,this_comp
                      ,position
                      ):
    comp = GhPython.Component.ZuiPythonComponent()
    
    #comp.CopyFrom(this_comp)
    sizeF = SizeF(*position)

    comp.Attributes.Pivot = PointF.Add(comp.Attributes.Pivot, sizeF)
    

    comp.Code = launcher_code
    #comp.NickName = name
    comp.Params.Clear()
    comp.IsAdvancedMode = True
    comp.Category = category
    comp.SubCategory = subcategory

    GH_doc = this_comp.OnPingDocument()
    GH_doc.AddObject(comp, False)
    

    

def dev_tools_factory(name, name_map, inst, retvals = None): 

    args = ('opts',)
    component_inputs = ('go',) + args

    def return_component_names(local_opts):
        sDNAUISpec = local_opts['options'].sDNAUISpec
        
        sDNA_tool_names = [Tool.__name__ for Tool in sDNAUISpec.get_tools()]
        names_lists = [support_component_names, special_names, sDNA_tool_names]
        names_list = [x for z in names_lists for x in z]
        clash_test_passed = no_name_clashes( name_map,  names_lists )


        if not clash_test_passed:
            output('Component name/abbrev clash.  Rename component or abbreviation. ','WARNING') 
            output('name_map == ' + str(name_map),'INFO') 
            output('names_lists == ' + str(names_lists),'INFO') 
            output('names_list == ' + str(names_list),'INFO') 
        else:
            output('Component name/abbrev test passed. ','INFO') 

        assert clash_test_passed
                                                                # No nick names allowed that are 
                                                                # a tool's full / real name.
        names_and_nicknames = names_list + list(name_map._fields) #name_map.keys()   
        def points_to_valid_tools(tool_names):
            if not isinstance(tool_names, list):
                tool_names = [tool_names]
            return all(name in names_and_nicknames for name in tool_names)
        invalid_name_map_vals = {key : val for key, val in name_map._asdict().items()
                                           if not points_to_valid_tools(val)}
        # TODO.  Lowest priority: Check there are no non-trivial cycles.  this is only devtool validation code - 
        #        not likely a user will expect
        #        correct results if they alter name_map to include a non-trivial cycle.
        if invalid_name_map_vals:
            output('Invalid name_map entries: ' 
                  +'\n'.join([k + (v if not isinstance(v, list) else
                                   ' '.join([n for n in v if not points_to_valid_tools(n)])
                                  )
                              for k, v in invalid_name_map_vals.items()])
                   ,'CRITICAL'
                   )
        else:
            output('Name_map validated successfully.  ','INFO')
        assert not invalid_name_map_vals
        #return special_names + support_component_names + sDNA_tool_names, None, None, None

        names = ([name for name in names_list 
                           if name not in name_map] #.values()] 
                     + list(name_map._fields) #keys())
                    )

        #return 0, None, {}, ret_names, #names_list
        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in return_component_names.retvals]

    if retvals is None:
        return_component_names.retvals = 'retcode', 'names'
    else:
        return_component_names.retvals = retvals
    return_component_names.show = {}
    return_component_names.args = args
    return_component_names.show['Input'] = component_inputs
    return_component_names.show['Output'] = ('OK',) + return_component_names.retvals[1:]
 


    builder_args = ('launcher_code', 'opts')
    builder_component_inputs = ('go',) + builder_args + ('name_map', 'categories')

    def build_components(code, opts_at_call):
        #type(str, dict) -> None

        while (isinstance(code, Iterable) 
               and not isinstance(code, str)):
            code = code[0]

        global module_opts
        module_opts['options']._replace( auto_get_Geom = False
                                 ,auto_read_Usertext = False
                                 ,auto_write_new_Shp_file = False
                                 ,auto_read_Shp = False
                                 ,auto_plot_data = False
                                 )

        metas = opts_at_call['metas']

        sDNAUISpec = opts_at_call['options'].sDNAUISpec
        categories = {Tool.__name__ : Tool.category for Tool in sDNAUISpec.get_tools()}
        categories.update(metas.categories._asdict())

        name_map = metas.name_map._asdict()

        retcode, names  = return_component_names(opts_at_call)

        nicknameless_names = [name for name in names if name not in name_map.values()]

        this_comp = inst.Attributes.Owner


        for i, name in enumerate(set(list(name_map.keys()) + nicknameless_names)):
            if name_map.get(name, name) not in categories:
                raise ValueError(output('No category for ' + name, 'ERROR'))
            else:
                i *= 175
                w = 800
                #make_new_component(  name
                #                    ,'sDNA'
                #                    ,categories[name_map.get(name, name)]
                #                    ,code
                #                    ,this_comp
                #                    [i % w, i // w]
                #                    )

                position = [200 + (i % w), 550 + 220*(i // w)]
                comp = GhPython.Component.ZuiPythonComponent()
    
                #comp.CopyFrom(this_comp)
                sizeF = SizeF(*position)

                comp.Attributes.Pivot = PointF.Add(comp.Attributes.Pivot, sizeF)
                

                comp.Code = code
                comp.NickName = name
                comp.Name = name
                comp.Params.Clear()
                comp.IsAdvancedMode = True
                comp.Category = 'sDNA'
                comp.SubCategory = categories[name_map.get(name, name)]

                GH_doc = this_comp.OnPingDocument()
                GH_doc = ghdoc.Component.Attributes.Owner.OnPingDocument()
                # No they're not the same!  ghdoc is for Geometry and 
                #                           baking to Rhino etc.
                #                           GH_Doc is the canvas for components
                GH_doc.AddObject(comp, False)

        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in build_components.retvals]

    if retvals is None:
        build_components.retvals = ('retcode',)
    else:
        build_components.retvals = retvals
    build_components.show = {}
    build_components.args = builder_args
    build_components.show['Input'] = builder_component_inputs
    build_components.show['Output'] = ('OK',) + build_components.retvals[1:]    



    dev_tools = dict( Python = return_component_names
                     ,Self_test = lambda *args : args  # TODO!  Make it do something!
                     ,Build_components = build_components
                     )

    return dev_tools[name]



class ReturnComponentNames(Tool): # (name, name_map, inst, retvals = None): 

    args = ('opts',)
    component_inputs = ('go',) + args

    def __call__(self, local_opts):
        
        sDNAUISpec = local_opts['options'].sDNAUISpec
        name_map = local_opts['metas'].name_map

        sDNA_tool_names = [Tool.__name__ for Tool in sDNAUISpec.get_tools()]
        names_lists = [support_component_names, special_names, sDNA_tool_names]
        names_list = [x for z in names_lists for x in z]
        clash_test_passed = no_name_clashes( name_map,  names_lists )


        if not clash_test_passed:
            output('Component name/abbrev clash.  Rename component or abbreviation. ','WARNING') 
            output('name_map == ' + str(name_map),'INFO') 
            output('names_lists == ' + str(names_lists),'INFO') 
            output('names_list == ' + str(names_list),'INFO') 
        else:
            output('Component name/abbrev test passed. ','INFO') 

        assert clash_test_passed
                                                                # No nick names allowed that are 
                                                                # a tool's full / real name.
        names_and_nicknames = names_list + list(name_map._fields) #name_map.keys()   
        def points_to_valid_tools(tool_names):
            if not isinstance(tool_names, list):
                tool_names = [tool_names]
            return all(name in names_and_nicknames for name in tool_names)
        invalid_name_map_vals = {key : val for key, val in name_map._asdict().items()
                                           if not points_to_valid_tools(val)}
        # TODO.  Lowest priority: Check there are no non-trivial cycles.  this is only devtool validation code - 
        #        not likely a user will expect
        #        correct results if they alter name_map to include a non-trivial cycle.
        if invalid_name_map_vals:
            output('Invalid name_map entries: ' 
                  +'\n'.join([k + (v if not isinstance(v, list) else
                                   ' '.join([n for n in v if not points_to_valid_tools(n)])
                                  )
                              for k, v in invalid_name_map_vals.items()])
                   ,'CRITICAL'
                   )
        else:
            output('Name_map validated successfully.  ','INFO')
        assert not invalid_name_map_vals
        #return special_names + support_component_names + sDNA_tool_names, None, None, None

        names = ([name for name in names_list 
                           if name not in name_map] #.values()] 
                     + list(name_map._fields) #keys())
                    )

        #return 0, None, {}, ret_names, #names_list
        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]

    retvals = 'retcode', 'names'
    
    show = dict(Input = component_inputs
               ,Output = ('OK',) + retvals[1:]
               )
  
return_component_names = ReturnComponentNames()
tools_dict['Python'] = return_component_names


class Buildcomponents(Tool): 
    args = ('launcher_code', 'opts')
    component_inputs = ('go',) + args[1:] + ('name_map', 'categories')

    def __call__(self, code, opts_at_call):
        #type(str, dict) -> None

        while (isinstance(code, Iterable) 
               and not isinstance(code, str)):
            code = code[0]

        global module_opts
        module_opts['options']._replace(auto_get_Geom = False
                                ,auto_read_Usertext = False
                                ,auto_write_new_Shp_file = False
                                ,auto_read_Shp = False
                                ,auto_plot_data = False
                                )

        metas = opts_at_call['metas']

        sDNAUISpec = opts_at_call['options'].sDNAUISpec
        categories = {Tool.__name__ : Tool.category for Tool in sDNAUISpec.get_tools()}
        categories.update(metas.categories._asdict())

        name_map = metas.name_map._asdict()

        retcode, names  = return_component_names(opts_at_call)

        nicknameless_names = [name for name in names if name not in name_map.values()]

        for i, name in enumerate(set(list(name_map.keys()) + nicknameless_names)):
            if name_map.get(name, name) not in categories:
                raise ValueError(output('No category for ' + name, 'ERROR'))
            else:
                i *= 175
                w = 800
                #make_new_component(  name
                #                    ,'sDNA'
                #                    ,categories[name_map.get(name, name)]
                #                    ,code
                #                    ,this_comp
                #                    [i % w, i // w]
                #                    )

                position = [200 + (i % w), 550 + 220*(i // w)]
                comp = GhPython.Component.ZuiPythonComponent()
    
                #comp.CopyFrom(this_comp)
                sizeF = SizeF(*position)

                comp.Attributes.Pivot = PointF.Add(comp.Attributes.Pivot, sizeF)
                

                comp.Code = code
                comp.NickName = name
                comp.Name = name
                comp.Params.Clear()
                comp.IsAdvancedMode = True
                comp.Category = 'sDNA'
                comp.SubCategory = categories[name_map.get(name, name)]

                GH_doc = ghdoc.Component.Attributes.Owner.OnPingDocument()
                GH_doc.AddObject(comp, False)

        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    retvals = ('retcode',)


    show = dict(Input = component_inputs
               ,Output = ('OK',) + retvals[1:]    
               )

build_components = Buildcomponents()
tools_dict['Build_components'] = build_components

tools_dict['Self_test'] = lambda *args : args  # TODO!  Make it do something!

# dict( Python = return_component_names
#                      ,Self_test = lambda *args : args  # TODO!  Make it do something!
#                      ,Build_components = build_components
#                      )

def dev_tools(name): 
    #type(str, named_tuple, type[any], tuple) -> type[any]
    return dev_tools[name]

#def sDNA_wrapper_factory

class sDNAWrapper(Tool):
    # This class is instantiated once per sDNA tool name.  In addition to the 
    # other necessary attributes of Tool, instances know their own name, in
    # self.tool_name.  Only when instances are called, are Nick_names and sDNA
    # are looked up in local_metas, and opts['metas'], in the args.
    # 
    def get_tool_opts_and_syntax(self
                                ,opts
                                ,local_metas
                                ):
        metas = opts['metas']
        nick_name = local_metas.nick_name
        sDNAUISpec = opts['options'].sDNAUISpec
        sDNA = opts['metas'].sDNA

        tool_opts = opts.setdefault(nick_name, {})
        debug(tool_opts)
        tool_opts = tool_opts.setdefault(self.tool_name, tool_opts)
        # Note, this is intended to do nothing if nick_name == self.tool_name
        try:
            sDNA_Tool = getattr(sDNAUISpec, self.tool_name)
        except:
            raise ValueError(output('No tool called '
                                   +self.tool_name
                                   +sDNAUISpec.__name__
                                   +'.  Rename tool_name or change sDNA version.  '
                                   )
                            )
        input_spec = sDNA_Tool.getInputSpec()
        get_syntax = sDNA_Tool.getSyntax     

        defaults_dict = { varname : default for (varname
                                                ,displayname
                                                ,datatype
                                                ,filtr
                                                ,default
                                                ,required
                                                ) in input_spec  
                        }            
        if sDNA in tool_opts:
            tool_opts_dict = defaults_dict.update( tool_opts[sDNA]._asdict() ) 
        else:
            tool_opts_dict = defaults_dict
        namedtuple_class_name = (nick_name 
                                +(self.tool_name if self.tool_name != nick_name else '') 
                                +sDNAUISpec.__file__
                                )
        tool_opts[sDNA] = make_nested_namedtuple(tool_opts_dict
                                                ,namedtuple_class_name
                                                ,strict = True
                                                ) 

        return tool_opts, get_syntax


    def __init__(self
                ,tool_name
                ,opts
                ,local_metas
                ):
        #if tool_name in support_component_names:
        #    def support_tool_wrapper(f_name, Geom, Data, opts):  
        #        return globals()[tool_name](f_name, Geom, Data)
        #    tools_dict[tool_name] = support_tool_wrapper   
            #
            #
        self.tool_name = tool_name
        tool_opts, _ = self.get_tool_opts_and_syntax(opts, local_metas)

        sDNA = opts['metas'].sDNA
        global do_not_remove
        do_not_remove += tuple(tool_opts[sDNA]._fields)


    args = ('file', 'opts', 'l_metas')
    component_inputs = ('go', ) + args[:2]


    def __call__(self # the callable instance / func, not the GH component.
                ,f_name
                ,opts
                ,local_metas
                ):
        #type(Class, dict(namedtuple), str, Class, DataTree)-> Boolean, str

        sDNA = opts['metas'].sDNA
        sDNAUISpec = opts['options'].sDNAUISpec
        run_sDNA = opts['options'].run_sDNA 



        if not hasattr(sDNAUISpec, self.tool_name): 
            raise ValueError(self.tool_name + 'not found in ' + sDNA[0])
        options = opts['options']

        tool_opts, get_syntax = self.get_tool_opts_and_syntax(opts, local_metas)


        dot_shp = options.shp_file_extension

        input_file = tool_opts[sDNA].input
        

        #if (not isinstance(input_file, str)) or not isfile(input_file): 
        if (isinstance(f_name, str) and isfile(f_name)
            and f_name.rpartition('.')[2] in [dot_shp[1:],'dbf','shx']):  
            input_file = f_name
    
            # if options.auto_write_new_Shp_file and (
            #     options.overwrite_input_shapefile 
            #     or not isfile(input_file)):
            #     retcode, input_file, gdm = write_shapefile( 
            #                                                  input_file
            #                                                 ,gdm
            #                                                 ,opts
            #                                                 )
            


        output_file = tool_opts[sDNA].output
        if output_file == '':
            output_suffix = options.output_shp_file_suffix
            if self.tool_name == 'sDNAPrepare':
                output_suffix = options.prepped_shp_file_suffix   
            output_file = input_file.rpartition('.')[0] + output_suffix + dot_shp

        output_file = get_unique_filename_if_not_overwrite(output_file, options)

            
        syntax = get_syntax(tool_opts[sDNA]._asdict().update(input = input_file))

        f_name = output_file

        command =   (options.python_exe 
                    + ' -u ' 
                    + '"' 
                    + join(  dirname(sDNAUISpec.__file__)
                            ,'bin'
                            ,syntax['command'] + '.py'  
                            ) 
                    + '"'
                    + ' --im ' + run_sDNA.map_to_string( syntax["inputs"] )
                    + ' --om ' + run_sDNA.map_to_string( syntax["outputs"] )
                    + ' ' + syntax["config"]
                    )
        
        sDNA_tool_logger.debug(command)

        try:
            output_lines = check_output(command)
            #print output_lines
            retcode = 0
        except:
            retcode = 1
        finally:
            try:
                line_end = '\r\n' if '\r\n' in output_lines else '\n'
                for line in output_lines.split(line_end):
                    sDNA_tool_logger.debug(line)
            except:
                pass
        #return_code = call(command)   
        
        #return_code = run_sDNA.runsdnacommand(    syntax
        #                                    ,sdnapath = dirname(sDNAUISpec.__file__)  #opts['options'].sDNA_UISpec_path
        #                                    ,progress = IllusionOfProgress()
        #                                    ,pythonexe = options.python_exe
        #                                    ,pythonpath = None)   # TODO:  Work out if this is important or not! 
                                                                # os.environ["PYTHONPATH"] not found in Iron Python

        #return return_code, tool_opts[sDNA].output, gdm, a
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    retvals = 'retcode', 'f_name', 'gdm', 'opts'
    show = dict(Input = component_inputs
                ,Output = ('OK', 'file', retvals[-1])
                )


def tool_factory(nick_name
                ,local_opts
                ):  
    #type( str, namedtuple, dict ) -> list

    #sDNA, sDNAUISpec, run_sDNA = local_opts['options'].sDNA, local_opts['options'].sDNAUISpec, local_opts['options'].run_sDNA

    #global tools_dict # mutable - access through normal parent module namespace

    sDNA = local_opts['metas'].sDNA
    name_map = local_opts['metas'].name_map
    global tools_dict
    # A special component that takes its nickname from the parameters provided,
    # only working out which tools to run at run time.  

    if not isinstance(nick_name, Hashable):
        raise TypeError(output('Non-hashable variable given for key' + str(nick_name),'ERROR'))

    if (   nick_name not in tools_dict ):  #or 
            #sDNA not in local_opts.get(nick_name, {})   ):
        map_result = getattr(name_map, nick_name, nick_name)  # in case nick_name == tool_name
        if not isinstance(map_result, str):
            debug('Processing list of tools found for ' + nick_name)
            tools =[]
            #nick_name_opts = {}
            for mapped_name in map_result:
                tools.append(tool_factory(mapped_name
                                         ,local_opts 
                                         )
                            )
                #cache_syntax_and_UISpec(nick_name, mapped_name, local_opts)                    
                # Not needed as no function closure will ever be 
                # created that refers to self.opts[nickname][not a tool_name]

                #nick_name_opts[mapped_name] = local_opts[mapped_name]
            if len(tools) == 1:
                tools = tools[0]
            tools_dict.setdefault(nick_name, tools )
        else:
            mapped_name = map_result
            debug(nick_name + ' maps to ' + mapped_name)
            #cache_syntax_and_UISpec(nick_name, mapped_name, local_opts)                    

            tools_dict.setdefault(mapped_name
                                 ,sDNAWrapper(mapped_name)
                                 )

            # if mapped_name in support_component_names:
            #     tools_dict[nick_name] = tools_dict[mapped_name]
            #     output(mapped_name + ' in support_component_names','DEBUG')
            # elif nick_name in dev_tools: #Dev tool for naming components
            #     tools_dict[nick_name] = [dev_tools(nick_name)] 
            #     output('nick_name' + ' in Dev tools','DEBUG')
            #     # Needs to be here to be passed name_map

            # elif nick_name in special_names: #["sDNA_general"]  
            #     output(nick_name + ' is in special_names','DEBUG')

            # # Not 'elif' to create opts for "Python"
            #     tools_dict[nick_name] = [tool_factory_wrapper] 
            # else:  # mapped_name is a tool_name, possibly named explicitly in nick_name
            #     # create entries for sDNA tools and non-special support tools & "Python"
            #     output(nick_name + ' needs new tool to be built, e.g. from sDNA. ','DEBUG')
            #     tools_dict[nick_name] = [sDNA_wrapper]
            #     #tools_dict[nick_name] = [sDNAWrapper(mapped_name, nick_name, local_opts)]  
            #     #tools_dict[nick_name] = [sDNA_wrapper_factory(mapped_name, nick_name, local_opts)]  
            #     # assert isinstance(sDNA_wrapper_factory(map_result, nick_name, name_map, local_opts), list)

    debug('tools_dict[' + nick_name + '] == ' + str(tools_dict[nick_name]) )
    return tools_dict[nick_name] 


class ToolFactoryWrapper(Tool):
    args = ('file', 'gdm', 'opts', 'tool')
    component_inputs = ('go', args[0], 'Geom', 'Data') + args[1:]
    def __init__(self): #, component):
        pass
        #self.component = component


    #def tool_factory_wrapper(f_name, gdm, opts, tool = None):
    def __call__(self, f_name, gdm, opts, tool, *args):

        name_map = opts['metas'].name_map
        if tool is None:
            tool_name = opts['options'].tool_name
        tools = tool_factory(tool_name 
                            ,opts 
                            )
            
        #tools = self.component.auto_insert_tools(tools
        #                                        ,self.component.Params
        #                                        )
        #inst.Params = 
        #self.component.update_Params(self.component.ghenv.Component.Params
        #                            ,tools
        #                            )

        # TODO:  How do component args work?!

        return run_tools(tools
                        ,dict(f_name = f_name
                             ,gdm = gdm
                             ,opts = opts
                             )
                        ) 
    # tool_factory_wrapper.show = {}
    # tool_factory_wrapper.args = args
    # tool_factory_wrapper.show['Input'] = component_inputs
    # tool_factory_wrapper.retvals = 'retcode', 'Geom', 'Data', 'f_name', 'gdm', 'opts'
    # tool_factory_wrapper.show['Output'] = ('OK', ) + tool_factory_wrapper.retvals[1:3] + ('file',) + tool_factory_wrapper.retvals[4:]
    retvals = 'retcode', 'Geom', 'Data', 'f_name', 'gdm', 'opts'

    show = dict(Input = component_inputs
               ,Output = ('OK', ) + retvals[1:3] + ('file',) + retvals[4:]
               )

tool_factory_wrapper = ToolFactoryWrapper()
tools_dict['sDNA_General'] = tool_factory_wrapper


def component_decorator( BaseClass
                        ,ghenv
                        ,nick_name = 'Self_test'
                        ):
    #type:(type[type], str, object) -> type[type]
    class sDNA_GH_Component(BaseClass):

        # Options from module, from defaults and installation config.toml
        opts = module_opts  
        local_metas = default_local_metas   # immutable.  controls syncing /
                                            # desyncing / read / write of the
                                            # above (opts).
                                            # Although local, it can be set on 
                                            # groups of components using the 
                                            # default section of a project 
                                            # config.ini, or passed as a
                                            # Grasshopper parameter between
                                            # components.

        #sDNA_GH_path = sDNA_GH_path
        #sDNA_GH_package = sDNA_GH_package

        def remove_component_output(self, name):
            for param in self.Params.Output:
                if param.NickName == name:
                    self.Params.UnregisterOutputParam(param)
        

        def auto_insert_tools(self, tools, Params):
            #type(type[any], list) -> None
            if tools is None:
                tools = self.my_tools
            tools = tools[:] if isinstance(tools, list) else [tools]

            options = self.opts['options']
            



            # if options.auto_write_new_Shp_file and (
            #     options.overwrite_input_shapefile 
            #     or not isfile(input_file))

            if options.auto_write_new_Shp_file:
                tools = insert_tool(self
                                   ,'before'
                                   ,tools
                                   ,Params
                                   ,write_shapefile
                                   ,lambda tool : tool.__class__ == sDNAWrapper
                                   ,sDNA_GH_names
                                   )
            if options.auto_read_Usertext:
                tools = insert_tool(self
                                   ,'before'
                                   ,tools
                                   ,Params
                                   ,read_Usertext
                                   ,lambda tool : tool == write_shapefile
                                   ,[]
                                   )   

            if options.auto_get_Geom:
                tools = insert_tool(self
                                   ,'before'
                                   ,tools
                                   ,Params
                                   ,get_Geom
                                   ,lambda tool : tool == read_Usertext
                                   ,[]
                                   )   

            if options.auto_read_Shp:
                tools = insert_tool(self
                                   ,'after'
                                   ,tools
                                   ,Params
                                   ,read_shapefile
                                   ,lambda tool : tool.__class__ == sDNAWrapper
                                   ,sDNA_GH_names
                                   )
            
            if options.auto_parse_data:
                tools = insert_tool(self
                                   ,'after'
                                   ,tools
                                   ,Params
                                   ,parse_data
                                   ,lambda tool : tool == read_shapefile
                                   ,[]
                                   )     
            
            
            if options.auto_plot_data:
                tools = insert_tool(self
                                   ,'after'                
                                   ,tools
                                   ,Params
                                   ,recolour_objects
                                   ,lambda tool : tool == parse_data
                                   ,[]
                                   )    
            return tools

        def update_Input_or_Output_Params(self
                                         ,Input_or_Output
                                         ,Params = None
                                         ,tools = None
                                         ,params_current = None
                                         ,params_needed = None
                                         ):
            #type(str, list, list) -> None   


            assert Input_or_Output in ['Input', 'Output']

            if Params is None:
                Params = self.Params

            if params_current is None:
                params_current = getattr(Params, Input_or_Output)[:]

            self.do_not_add = do_not_add[:]


            if tools is None:
                tools = self.tools

            if params_needed is None:
                tools = self.tools
                if Input_or_Output == 'Input':
                    params_needed = [ input for tool in tools 
                                            for input in tool.show['Input'] ]
                else:
                    tool = tools[-1]
                    params_needed = list(tool.show['Output'])


            debug(   'params_current NickNames =='
                    + ' '.join(str(param.NickName) for param in params_current)
                )

            for param in params_current:  
                if param.NickName in params_needed:
                    debug('Param already there, adding to self.do_not_add == '
                        + str(param.NickName))
                    self.do_not_add += [param.NickName]
                elif (param.NickName not in do_not_remove and
                    len(getattr(param, 'Recipients', [])) == 0 and  
                    len(getattr(param, 'Sources',    [])) == 0     ):
                    debug(    'Param ' 
                            + str(param.NickName) 
                            + ' not needed, and can be removed.  ')
                    #debug('Removing param ' + str(param.NickName))
                    #Params.UnregisterOutputParameter(param)
                    #Params.Output.Count -=1
                    #Params.Output.Remove(param) 
                    #Params.OnParametersChanged()
                else:
                    debug('Leaving param alone.  User added output? == ' 
                        + str(param.NickName))

                # else:  Leave alone.  The user added the param, 
                # or the component was supplied that way by ourselves.
                    self.do_not_add += [param.NickName]

            for param_name in params_needed:
                if param_name not in self.do_not_add: 
                    self.do_not_add += [param_name]
                    debug('Adding param == ' + param_name)

                    #var = Grasshopper.Kernel.Parameters.Param_String(NickName = param_name)
                    if param_name in ['leg_frame']:
                        new_param_type = Grasshopper.Kernel.Parameters.Param_Geometry
                    #elif param_name in ['leg_cols']:
                    else:
                        new_param_type = Grasshopper.Kernel.Parameters.Param_GenericObject
                    #else:
                    #    new_param_type = Grasshopper.Kernel.Parameters.Param_String

                    if param_name == 'Data':
                        Access = Grasshopper.Kernel.GH_ParamAccess.tree
                    else: 
                        Access = Grasshopper.Kernel.GH_ParamAccess.list

                    var = new_param_type(NickName = param_name
                                        ,Name = param_name
                                        ,Description = param_name
                                        ,Access = Access
                                        ,Optional = True
                                        )

                    #var.NickName = param_name
                    #var.Name = param_name
                    #var.Description = param_name
                    #if param_name == 'Data':
                    #    var.Access = Grasshopper.Kernel.GH_ParamAccess.tree
                    #else: 
                    #    var.Access = Grasshopper.Kernel.GH_ParamAccess.list

                    #var.Optional = True

                    #index = getattr(Params, Input_or_Output).Count

                    registers = dict(Input  = 'RegisterInputParam'
                                    ,Output = 'RegisterOutputParam'
                                    )
                    getattr(Params, registers[Input_or_Output])(var) #, index)
                    #Params.Output.Count +=1
                    Params.OnParametersChanged()

                else:
                    debug('Param in self.do_not_add == ' + param_name)

        def update_Params(   self
                            ,Params = None
                            ,tools = None
                         ):
            

            if Params is None:
                try:
                    Params = ghenv.Component.Params
                except:
                    Params = self.Params
                #Params = getattr(self, 'Params', ghenv.Component.Params) 

            if tools is None:
                tools = self.tools

            ParamsSyncObj = Params.EmitSyncObject()


            
            self.update_Input_or_Output_Params('Output', Params, tools)
            self.update_Input_or_Output_Params('Input', Params, tools)

            Params.Sync(ParamsSyncObj)
            Params.RepairParamAssociations()

            return Params
    

        def update_tools(self):
            #self.my_tools = []

            #for tool in tools:
            #    # some are unique closures so no #if not hasattr(self, tool.func_name):
            #    setattr(self, func_name(tool), tool)
            #    self.my_tools +=[getattr(self, func_name(tool))]
            
            #Avoid issues with calling tools stored as methods with self:
            tools = tool_factory(self.local_metas.nick_name
                                ,self.opts
                                )
            debug(tools)
                 

            #debug(self.opts)
            debug('Tool opts == ' + '\n'.join( str(k) + ' : ' + str(v) 
                                                for k,v in self.opts.items()
                                                if k not in ('options','metas')
                                              ) 
                 )

            return tools






        def update_name(self, new_name = None):
            if new_name is None:
                try:
                    new_name = self.Attributes.Owner.NickName 
                except:
                    try:
                        new_name = nick_name 
                    except:
                        try:
                            new_name = ghenv.Component.NickName
                        except:
                            new_name = "Self_test"     

            if not hasattr(self, 'nick_name') or (
               self.opts['metas'].allow_components_to_change_type
               and self.local_metas.nick_name != new_name    ):  
                #
                self.local_metas = self.local_metas._replace(nick_name = new_name)
                self.logger = logger.getChild(self.local_metas.nick_name)

                output( ' Component nick name changed to : ' 
                                + self.local_metas.nick_name, 'INFO' )
                return 'Name updated'
            return 'Name not updated'


  



            
        def update_sDNA(self):
            debug('Self has attr sDNA == ' 
                 +str(hasattr(self,'sDNA'))
                 )
            debug('self.opts[metas].sDNA == (' 
                 +str(self.opts['metas'].sDNAUISpec)
                 +', '
                 +self.opts['metas'].runsdnacommand 
                 +') '
                 )

            if hasattr(self,'sDNA'):
                debug('Self has attr sDNA == ' + str(hasattr(self,'sDNA')))
            
            sDNA = ( self.opts['metas'].sDNAUISpec  # Needs to be hashable to be
                    ,self.opts['metas'].runsdnacommand )   # a dict key => tuple not list
                     # these are both just module names.  
                     # Python can't import two files with the same name
                     # so changing these triggers the change to input the new one

            if not hasattr(self,'sDNA') or self.sDNA != sDNA:
                self.sDNAUISpec, self.run_sDNA, path = self.load_modules(
                                                          sDNA
                                                         ,self.opts['metas'].sDNA_search_paths
                                                         )
                #  self.sDNAUISpec, self.run_sDNA are the two Python modules
                #  to allow different components to run different sDNA versions
                #  these module references are instance variables

                assert self.sDNAUISpec.__name__ == self.opts['metas'].sDNAUISpec
                assert self.run_sDNA.__name__ == self.opts['metas'].runsdnacommand




                debug('Self has attr sDNAUISpec == ' + str(hasattr(self,'sDNAUISpec')))
                debug('Self has attr run_sDNA == ' + str(hasattr(self,'run_sDNA')))

                self.sDNA = sDNA
                self.sDNA_path = path
                self.opts['metas'] = self.opts['metas']._replace(    sDNA = self.sDNA
                                                                    ,sDNA_path = path 
                                                                )
                self.opts['options'] = self.opts['options']._replace(  sDNAUISpec = self.sDNAUISpec
                                                                      ,run_sDNA = self.run_sDNA 
                                                                    )  

                assert self.opts['metas'].sDNA_path == dirname(self.opts['options'].sDNAUISpec.__file__)                                                                  






        def __init__(self, *args, **kwargs):

            BaseClass.__init__(self, *args, **kwargs)
            
            self.load_modules = load_modules
            self.ghdoc = ghdoc
            self.ghenv = ghenv

            self.update_sDNA() 


            

            
            #self.update_name()  All runs anyway at start of RunScript even if
            #                    go == False
            #self.my_tools = self.update_tools() elsewhere requires name to 
            #                                    be updated
            #self.tools = self.auto_insert_tools(self.my_tools) 
            #self.update_Params(self.Params, self.tools)










        #sDNA_GH = strict_import('sDNA_GH', join(Grasshopper.Folders.DefaultAssemblyFolder,'sDNA_GH'), sub_folder = 'sDNA_GH')   
                                            # Grasshopper.Folders.AppDataFolder + r'\Libraries'
                                            # %appdata%  + r'\Grasshopper\Libraries'
                                            # os.getenv('APPDATA') + r'\Grasshopper\Libraries'
        def RunScript(self, *args): #go, Data, Geom, f_name, *args):
            # type (bool, str, Rhino Geometry, datatree, tuple(namedtuple,namedtuple), *dict)->bool, str, Rhino_Geom, datatree, str

            args_dict = {key.Name : val for key, val in zip(self.Params.Input, args) } # .Input[4:] type: ignore
            
            debug(args_dict)
            debug('self.Params.Input Names == ' + ' '.join(key.Name for key in self.Params.Input))
            debug(args)

            go = args_dict.get('go', False)
            Data = args_dict.get('Data', None)
            Geom = args_dict.get('Geom', None)
            f_name = args_dict.get('file', '')

            if f_name and not isinstance(f_name, str) and isinstance(f_name, list):
                    f_name=f_name[0] 

            external_opts = unpack_first_item_from_list(args_dict.get('opts', {}), {})
            debug(external_opts)

            

            external_local_metas = unpack_first_item_from_list(args_dict.get('local_metas', empty_NT), empty_NT)
            gdm = args_dict.get('gdm', {})

            debug('gdm from start of RunScript == ' + str(gdm)[:50])
            #print('#1 self.local_metas == ' + str(self.local_metas))
            
            if self.update_name() == 'Name updated':
                pass
                self.my_tools = self.update_tools()
            
            self.tools = self.auto_insert_tools(self.my_tools, self.Params)  
                    # Other components may mean self.tools needs extra tools adding or /removing
                    # but this could - annoy many users.  TODO!  Get early feedback!
            #self.Params = 
            self.update_Params()#self.Params, self.tools)

            
            synced = self.local_metas.sync_to_module_opts
            old_sDNA = self.opts['metas'].sDNA

            self.local_metas = override_all_opts(args_dict = args_dict
                                                ,local_opts = self.opts # mutated
                                                ,external_opts = external_opts 
                                                ,local_metas = self.local_metas 
                                                ,external_local_metas = external_local_metas
                                                )

            args_dict['opts'] = self.opts
            args_dict['l_metas'] = self.local_metas

            debug('Opts overridden....    ')
            debug(self.local_metas)
            debug('options after override in RunScript == ' + str(self.opts['options']))
            
            if (self.opts['metas'].auto_update_Rhino_doc_path 
                or not isfile(self.opts['options'].Rhino_doc_path)        ):

                path = get_path(self)

                self.opts['options'] = self.opts['options']._replace( Rhino_doc_path = path )

            if self.opts['metas'].allow_components_to_change_type: 
                
                if self.local_metas.sync_to_module_opts != synced:
                    if self.local_metas.sync_to_module_opts:
                        self.opts = module_opts #sync
                    else:
                        self.opts = self.opts.copy() #desync

                if self.opts['metas'].sDNA != old_sDNA:
                    self.update_sDNA()
                    #self.Params = 
                    self.update_Params()#self.Params, self.tools)
            


                    

            # Defined_tools = [y for z in tools_dict.values() for y in z]
            # debug(Defined_tools)
            # debug(type(Defined_tools))
            # Undefined_tools = [x for x in self.my_tools if x not in Defined_tools]

            if False:
                debug('Defined_tools == ' + str(Defined_tools))
                debug('Undefined tools == ' + str(Undefined_tools))
                raise ValueError(output('Tool function not in cache, possibly ' 
                                       + 'unsupported.  Check input tool_name '
                                       +'if sDNAGeneral, else tool_factory '
                                       ,'ERROR'
                                       )
                                )


            if go in [True, [True]]: # [True] in case go set to List Access in GH component 
                returncode = 999
                assert isinstance(self.tools, list)

                debug('my_tools == '
                     +str(self.tools)
                     )

                geom_data_map = convert_Data_tree_and_Geom_list_to_gdm(Geom
                                                                      ,Data
                                                                      ,self.opts
                                                                      )
                
                debug('type(geom_data_map) == '
                     +str(type(geom_data_map))
                     )
                

                geom_data_map = override_gdm_with_gdm(gdm
                                                     ,geom_data_map
                                                     ,self.opts
                                                     )

                debug('After merge type(geom_data_map) == ' 
                     +str(type(geom_data_map))
                     )                
                
                debug('After merge geom_data_map == ' 
                     +str(geom_data_map.items()[:3])
                     +' ...'
                     )


                ret_vals_dict = run_tools(self.tools, args_dict)

                gdm = ret_vals_dict.get('gdm', {})
                #print (str(gdm))
                if isinstance(gdm, dict):
                    debug('Converting gdm to Data and Geometry')
                    (NewData, NewGeometry) = (
                    convert_dictionary_to_data_tree_or_lists(gdm)
                                        )    
                    #debug(NewData)
                    #debug(NewGeometry)                    
                else:
                    NewData, NewGeometry = None, None

                ret_vals_dict['Data'] = NewData
                ret_vals_dict['Geom'] = NewGeometry
                #if 'leg_frame' in ret_vals_dict:
                #    ret_vals_dict['rect'] = ret_vals_dict['leg_frame']
                ret_vals_dict['opts'] = [self.opts.copy()]
                ret_vals_dict['l_metas'] = self.local_metas #immutable

                def get_val(key):
                    return ret_vals_dict.get(key
                                            ,getattr(self.opts['metas']
                                                    ,key
                                                    ,getattr(self.opts['options']
                                                            ,key
                                                            ,getattr(self.local_metas
                                                                    ,key
                                                                    ,getattr(self.opts.get(self.local_metas.nick_name
                                                                                          ,{}
                                                                                          ).get(self.opts['metas'].sDNA
                                                                                               ,{}
                                                                                               )
                                                                            ,key
                                                                            ,'No variable or field: ' + key + ' found. '
                                                                            )
                                                                    )
                                                            )
                                                    )                            
                                            )

                #if func_name(self.tools[-1]) == 'recolour_objects':
                #    debug('Making new rect.  ')
                #    rect = rs.AddRectangle(rs.WorldXYPlane(), 20, 60)
                    #rect = Grasshopper.Kernel.GH_Convert.ToGHCurve(rect)
                    #rs.MoveObject(rect, [60, 0])
                #    ret_vals_dict['leg_frame'] = rect
                    #debug('sc.doc == ' + str(sc.doc))


                ret_vals = tuple(get_val(param.NickName) for param in self.Params.Output)
                return ret_vals
            else:   
                return (False, ) + tuple(repeat(None, len(self.Params.Output) - 1))

#def deco(BaseClass):
    #class M(BaseClass):
    #    def RunScript(self, go, Data, Geom, f_name, *args):
    #        a = 'Running Runscript from class deco'
    #        print(a)
    #        return a
    #return M                    
    return sDNA_GH_Component

""" loc = tool_factory()
comp = sDNA_GH_component_deco(object) """



###############################################################################
#Main script only process
#
if      '__file__' in dir(__builtins__)  and  __name__ in __file__ and '__main__' not in __file__ and '<module>' not in __file__:                     
    # Assert:  We're in a module!
    pass
else:
    pass


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


import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import ghpythonlib.treehelpers as th
from System.Drawing import Color as Colour
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



if 'ghdoc' not in globals():
    try:
        ghdoc = sc.doc
    except:
        try:
            ghdoc = Rhino.RhinoDoc.ActiveDoc
        except:
            ghdoc = 'No Rhino Doc and no GH canvas found'
            print(ghdoc)



if sys.version < '3.3':
    from collections import Hashable, Iterable
else:
    from collections.abc import Hashable, Iterable

from .custom_python_modules.options_manager import (                     
                                     load_toml_file,
                                     make_nested_namedtuple     
                                    ,load_ini_file                             
                                    ,override_namedtuple        
)

from .custom_python_modules import wrapper_logging

from .custom_python_modules.wrapper_pyshp import (get_fields_recs_and_shapes_from_shapefile
                                                 ,get_unique_filename_if_not_overwrite
                                                 ,write_from_iterable_to_shapefile_writer)

def get_stem_and_folder(path):
    if isfile(path):
        path=dirname(path)
    return split(path)

class HardcodedMetas(): 
    config = join( dirname(dirname(__file__)), r'config.toml')
    add_in_new_options_keys = False
    allow_components_to_change_type = False
    typecheck_opts_namedtuples = True
    typecheck_opts_fields = True
    sDNAUISpec = 'sDNAUISpec'
    runsdna = 'runsdnacommand'
    sDNA = (sDNAUISpec, runsdna)  # Read only.  Auto updates from above two.
    sDNA_path = ''  # Read only.  Determined after loading sDNAUISpec to which ever below
                    # it is found in.
                    # after loading, assert opts['metas'].sDNA_path == dirname(opts['options'].UISpec.__file__)
    sDNA_UISpec_path = r'C:\Program Files (x86)\sDNA\sDNAUISpec.py'
    sDNA_search_paths = [sDNA_UISpec_path, join(os.getenv('APPDATA'),'sDNA')]
    sDNA_search_paths += [join(os.getenv('APPDATA'), get_stem_and_folder(sDNA_search_paths[0])[1]) ]
    auto_update_Rhino_doc_path = True
                        #Abbreviation = Tool Name
#######################################################################################################################
    name_map = dict(    sDNA_Demo = [ 'Read_From_Rhino'
                                    ,'Read_Usertext'
                                    ,'Write_Shp'
                                    ,'sDNAIntegral'
                                    ,'Read_Shp'
                                    ,'Write_Usertext'
                                    ,'Parse_Data'
                                    ,'Recolour_objects'
                                    ]
                        ,test_write_Usertext_req = [ 'Read_From_Rhino'
                                    ,'Read_Usertext'
                                    ,'Write_Shp'
                                    ,'sDNAIntegral'
                                    ,'Read_Shp'
                                    ,'Parse_Data'
                                    ,'Recolour_objects'
                                    ]
                        ,sDNA_Demo_old_plot = [
                                    'Read_From_Rhino'
                                    ,'Read_Usertext'
                                    ,'Write_Shp'
                                    ,'sDNAIntegral'
                                    ,'Read_Shp'
                                    ,'Write_Usertext'
                                    ,'Visualise_Data' #TODO: Delete.  Deprecated.
                                    ]
                        ,Read_From_Rhino = 'get_objects_from_Rhino'
                        ,Read_Usertext = 'read_Usertext'
                        ,Write_Shp = 'write_objects_and_data_to_shapefile'
                        ,Read_Shp = 'read_shapes_and_data_from_shapefile'
                        ,Write_Usertext = 'write_data_to_Usertext'
                        ,Bake_UserText = 'bake_and_write_data_as_Usertext_to_Rhino'
                        ,Visualise_Data = 'plot_data_on_Rhino_objects'  #TODO: Delete.  Deprecated.
                        ,Parse_Data = 'parse_data'
                        ,Recolour_objects='recolour_objects'
                        ,Recolor_objects ='recolour_objects'
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
    name_map = namedtuple('name_map',name_map.keys())(**name_map)
#######################################################################################################################
    #share_installation_defaults_key = "sDNA_GH_installation_default_options"
    #share_sDNA_tools_key = "sDNA_UI_Spec_tools"
    #if all(['ghdoc' in globals, hasattr(ghdoc,'Path'), isfile(ghdoc.Path)]):    
    #    join(Grasshopper.Folders.DefaultAssemblyFolder,'sDNA_GH')
    #    join(Grasshopper.Folders.AppDataFolder,'Libraries','sDNA_GH')
    #    join(os.getenv('APPDATA'),'Grasshopper','Libraries','sDNA_GH')
    #    __file__
    #else: 
    #    installation_log_file = r'C:\Users\James\AppData\Roaming\Grasshopper\Libraries\sDNA_GH'


#    append_iterable_values_do_not_overwrite = True # TODO: implement this!
#    allocate_misnamed_GH_component_input_names_in_order = False # TODO: implement this!
#    allocate_all_GH_component_input_names_in_order = False # TODO: implement this!
#    modules_subdirectories = [   r'third_party_python_modules'   
#                                ,r'custom_python_modules'
#                                ] 

valid_re_normalisers = ['linear', 'exponential', 'logarithmic']


class HardcodedOptions():            
    ####################################################################################
    #System
    platform = 'NT' # in {'NT','win32','win64'} only supported for now
    encoding = 'utf-8'
    rhino_executable = r'C:\Program Files\Rhino 7\System\Rhino.exe'
    UISpec = None
    run = None
    Rhino_doc_path = ''  # tbc by loader
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
    logger_console_level = 'DEBUG'
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
    auto_get_objects_from_Rhino = True
    auto_read_Usertext = True
    auto_write_new_Shp_file = False
    auto_read_Shp = False
    auto_plot_Shp_data = False
    #Plotting results
    sDNA_output_abbrev_to_graph = 'BtEn'
    plot_max = None
    plot_min = None
    sort_data = True
    base = 10 # base of log and exp spline, not of number representations
    re_normaliser = 'linear' 
    assert re_normaliser in valid_re_normalisers 
    class_boundaries = [None] #[2000000, 4000000, 6000000, 8000000, 10000000, 12000000]
    legend_extent = None  # [xmin, ymin, xmax, ymax]
    bbox = None  # [xmin, ymin, xmax, ymax]
    number_of_classes = 7
    class_spacing = 'equal number of members' 
    assert class_spacing in valid_re_normalisers + ['equal number of members']
    first_legend_tag_format_string = 'below {upper}'
    inner_tag_format_string = '{lower} - {upper}' # also supports {mid_pt}
    last_legend_tag_format_string = 'above {lower}'
    num_format = '{:.3n}'
    legend_rectangle = ''  # uuid of GH object
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
    sync_to_shared_global_opts = True    # Needs to be true to
    read_from_shared_global_opts = True
    write_to_shared_global_opts = False  

    # if we want to run two versions of sDNA in the same Python instance
    # there'll be a module name clash unless this tuple sDNA is changed in
    # components using a different version to the default.  Copies of
    # the corresponding sDNA version B files with these names will 
    # need to be created.  The shared global opts cannot be used to record
    # the sDNA version.    

# Pre Python 3.6 the order of an OrderedDict isn't necessarily that of the arguments in its constructor so we build
# our options and metas namedtuples from a class, to avoid re-stating the order of the keys.

def get_namedtuple_etc_from_class(Class, name):
    # type: ( type[any], str) -> namedtuple
    fields = [attr for attr in dir(Class) if not attr.startswith('_')]
    factory = namedtuple(name, fields, rename=True)   
    return factory(**{x : getattr(Class, x) for x in fields})

default_metas = get_namedtuple_etc_from_class(HardcodedMetas, 'Metas')
default_options = get_namedtuple_etc_from_class(HardcodedOptions, 'Options')
local_metas = get_namedtuple_etc_from_class(HardcodedLocalMetas, 'LocalMetas')

empty_NT = namedtuple('Empty','')(**{})

opts = OrderedDict( metas = default_metas
                   ,options = default_options
                   )                

get_syntax_dict = {} 
input_spec_dict = {}                 

def get_path():
    path = Rhino.RhinoDoc.ActiveDoc.Path
                    
    if not isinstance(path, str) or not isfile(path):
        try:
            path = self.ghdoc.Path #type: ignore
        except:
            path = None
        finally:
            if not path:
                path = opts['options'].Default_sDNA_GH_file_path
    
    return path


tmp_logs = []

def output(s, logging_level = "INFO", stream = None, logging_dict = {} ):
    #type: (str,...,str,dict) -> str
    #type: (stream) == anything with a write method. e.g. 'file-like object' supporting write() and flush() methods, e.g. WriteableFlushableList
    
    #print(s)


    #if stream == None and ('a' in locals or 'a' in globals()):   # a is attached to a logger StreamHandler now, so if that works 
    #                                                             # this code would double log to it
    #    global a
    #    stream = a

    if hasattr(stream, 'write'): #isinstance(stream, WriteableFlushableList):
        stream.write(s)

    if logging_dict == {} and 'logger' in globals(): 
        logging_dict = dict( DEBUG = logger.debug
                            ,INFO = logger.info
                            ,WARNING = logger.warning
                            ,ERROR = logger.error
                            ,CRITICAL = logger.critical
                            )

    logging_dict.get( logging_level
                     ,lambda x : tmp_logs.append( (x, logging_level) ) 
                     )(s)

    return logging_level + ' : ' + s + ' '

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

def report(s):
    #type(str)->str
    return output(str(s)+' ','DEBUG')

def report_value(x, x_val = None):
    # type(type[any]) -> str
    if x_val == None:
        if type(x).__name__ == 'generator':
            x_val = " Generator " # don't use up now just for reporting
        else:
            x_val = x

    c = inspect.currentframe().f_back.f_locals.items()
    names = [var_name.strip("'") for var_name, var_val in c if var_val is x]
    # https://stackoverflow.com/questions/18425225/getting-the-name-of-a-variable-as-a-string


    return report(str(names) + ' == ' + str(x_val)+' ')

#report_value(component)
#
####################################################################################################################
#
# 

class WriteableFlushableList(list):
    # a simple input for a StreamHandler https://docs.python.org/2.7/library/logging.handlers.html#logging.StreamHandler
    # that stacks logging messages in a list of strings.  Instances are lists wth two extra methods, not streams akin to 
    # generators - memory use is not optimised.
    #
    def write(self, s):
    #type: ( str) -> None
    # https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code
    #
        if s:
            if isinstance(s, str):
                self.append(s)
            else:
                self.extend(s)

    debug = write
    info = write
    warning = write
    error = write
    critical = write


    def flush(self):  
    #type: () -> None
        pass  # A flush method is needed by logging


# 'a' in Grasshopper to be added by Launcher 





#if 'logger' not in globals():

report(opts['options'].message)


####################################################################################################################
#
#
def override_all_opts( args_dict
                      ,local_opts
                      ,external_opts
                      ,local_metas
                      ,external_local_metas
                      ,name):
    #type (dict, dict(namedtuple), dict(namedtuple), namedtuple, namedtuple, dict, str) -> namedtuple
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
            config_file_override =  load_ini_file( path, **kwargs('', local_opts) )
        elif file_ext == 'toml':
            config_file_override =  load_toml_file( path )

    def config_file_reader(key):
        #type(str)->[dict/file object]
        if isinstance(config_file_override, dict) and key in config_file_override:
            return config_file_override[key] 
        else:
            return config_file_override


    ###########################################################################
    # Update syncing / desyncing
    #
    local_metas_overrides_list = [external_local_metas
                                 ,config_file_reader('local_metas')
                                 ,args_local_metas
                                 ]
    local_metas = override_namedtuple(  local_metas
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
        if any(( local_metas.sync_to_shared_global_opts,  
                 not local_metas.read_from_shared_global_opts )):
            retval = []  
        else: 
            retval = [    opts.get( key,  {} ).get( sDNA(),  {} )    ]

        
        ext_opts = external_opts.get( key,  {} )
        if key not in ('options','metas') :
            ext_opts = ext_opts.get( sDNA(),  {} )
        
        retval += [ext_opts, config_file_reader(key), sub_args_dict.get(key,{})]

        return retval

        

    #overrides_list = lambda key : [ external_opts.get(key,{}).get(sDNA(), {})
    #                              ,config_file_reader, sub_args_dict.get(key, {})]
    if local_metas.sync_to_shared_global_opts:
        dict_to_update = opts # the opts in module's global scope, outside this function
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

    override_all_opts(  default_metas._asdict()
    # just to retrieve hardcoded primary meta (installation config file location)
                        ,opts #  mutates opts
                        ,{}       #external_opts
                        ,local_metas 
                        ,empty_NT #external_local_metas
                        ,'')

    report("After override: opts['options'].message == " + opts['options'].message)
else:
    output('Config file: ' + default_metas.config + ' not found. ','WARNING')    
#
####################################################################################################################


if not hasattr(sys.modules['sDNA_GH.tools'], 'logger'):
    
    logs_directory = join(dirname(get_path()),opts['options'].logs_subdir_name)

    if not isdir(logs_directory):
        os.mkdir(logs_directory)

    # wrapper_logging.logging.shutdown() # Ineffective in GH :(


    logger = wrapper_logging.new_Logger( 'sDNA_GH'
                                        ,join(logs_directory, opts['options'].log_file)
                                        ,opts['options'].logger_file_level
                                        ,opts['options'].logger_console_level
                                        ,None # custom_file_object 
                                        ,opts['options'].logger_custom_level
                                        )

    sDNA_logger = wrapper_logging.logging.getLogger('sDNA')

    report('Logging set up in sDNA_GH.tools ')

    for tmp_log in tmp_logs:
        output(*tmp_log)




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
    # overwrite ?
    # call update on the sub dicts?:
    #report_value(lesser)
    #report_value(override)

    if not lesser:
        lesser = OrderedDict()
    #report_value(lesser)
    if opts['options'].merge_Usertext_subdicts_instead_of_overwriting:
        report('Merging gdms.  ')
        for key in override:
            if   key in lesser and all(
                 isinstance(override[key], dict)
                ,isinstance(lesser[key], dict)   ):
                lesser[key].update(override[key])
            else:
                lesser[key] = override[key]
    else:
        lesser.update(**override)
    #report_value(lesser)
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
                              options = opts['options']
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
    
    report_value(Geom)
    if Geom in [None, [None]]:
        report(' No Geom. Processing Data only ')
        Geom = []


    #report_value(Geom)
    #report_value(sc.doc)

    if isinstance(Geom, str) or not isinstance(Geom, Iterable):
        report('Listifying Geom.  ')
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
    #    report('Is an obj[0] doc == ' + str(is_an_obj_in_GH_or_Rhino(Geom[0])))
    #   #report_value(sc.doc)
    #
    #    report('Is a group[0] doc == ' + str(is_a_group_in_GH_or_Rhino(Geom[0])))
    #    #report_value(sc.doc)
    #    raise ValueError(output( 'Invalid obj in Geom:  ' 
    #           +' '.join([str(x) for x in Geom if not is_an_obj_in_GH_or_Rhino(x)
    #                                          and not is_a_group_in_GH_or_Rhino(x)]) 
    #           ,'ERROR'))

    # 
    report_value(Data)
    if (Data in [[], None, [None]] or
        getattr(Data,'BranchCount',999)==0):
        Data = OrderedDict()
    elif (isinstance(Data, DataTree[object]) 
          and getattr(Data, 'BranchCount', 0) > 0):
        report('Datatree inputted to Data.  Converting....  ')
        Data = th.tree_to_list(Data)
    elif not isinstance(Data, list):
        report('Listifying Data.  ')
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


    #report('Data == ' + str(Data))
    report('len(Geom) == ' + str(len(Geom)))
    report('len(Data) == ' + str(len(Data)))

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
            report(r'repeating OrderedDict() after Data... ')
            Data = chain( Data,  repeat(OrderedDict()) )
        else:
            report( "Ah yeah!  Equal length.  " )
        component_inputs_gen_exp =  izip(Geom, Data)





    #component_inputs_gen_exp =  izip(Geom, Data)



    geom_data_map = make_gdm(component_inputs_gen_exp  
                            ,make_obj_key
                            )

    #geom_data_map = make_gdm( izip(Geom, imap( izip, key_lists, val_lists)), make_obj_key)

    #report_value(geom_data_map)

    return geom_data_map
#
# 
def are_GhPython_components_in_GH(compnt, names):
    #type(str)->bool
    doc = compnt.Attributes.Owner.OnPingDocument() #type: ignore
    return any( type(GH_component) is GhPython.Component.ZuiPythonComponent 
                and GH_component.NickName in names
                for GH_component in doc.Objects
              )
#
#
def downstream_components(compnt):
    return [recipient.Attributes.GetTopLevel.DocObject
            for param in compnt.Params.Output 
            for recipient in param.Recipients
            ]


def are_GhPython_downstream(names, compnt):
    comps = downstream_components(compnt)
    GhPython_compnt_NickNames = [ comp.NickName for comp in comps
                                  if type( comp.Attributes.GetTopLevel.DocObject ) 
                                     is GhPython.Component.ZuiPythonComponent
                                ]
    return ( any(name in GhPython_compnt_NickNames for name in names) or
             any(are_GhPython_downstream(names, comp) for comp in comps) )

def insert_tool_after_specials(   compnt
                                 ,tools
                                 ,tool
                                 ,is_special
                                 ,not_special_names
                                 ):
        if any(func_name(tool) not in not_special_names for tool in tools):  
                            # Not just last tool.  Else no point checking more
                            # than one downstream component?  The user may 
                            # wish to do other stuff after the tool
                            # and name_map is now a meta option too.
            special_names = [name for name, tool_list in tools_dict.items() 
                             if tool in tool_list]
                            # tools_dict is keyed on all present nick names 
                            # as well as names of tools defined in this module

        if (  not are_GhPython_components_in_GH(compnt, special_names) and
              not are_GhPython_downstream(special_names, compnt)     ):
                             # check tool not already there in another 
                             # component that will be executed next.
                             # TODO: None in entire canvas is too strict?
            for i, tool in enumerate(tools):
                if (  is_special(tool)  
                      and tool not in tools[i:]  ):
                         # check tool not already inserted 
                         # in tools after specials
                    tools.insert(i+1, tool)


#        print [x.Name for x in [r.Attributes.GetTopLevel.DocObject for x in self.Params.Output for r in x.Recipients][0].Params.Output]
#
#
def run_tools(self, my_tools, f_name, gdm, opts_at_call):
    #type(type[any], list, str, dict, dict)-> int, str, dict, WriteableFlushableList
    a = WriteableFlushableList()

    tools = my_tools[:]
    options = opts_at_call['options']

    if options.auto_read_Shp:
        insert_tool_after_specials(   self
                                     ,tools
                                     ,tools_dict['read_shapes_and_data_from_shapefile']
                                     ,lambda tool : hasattr(self.opts['options'].UISpec, func_name(tool))
                                     ,sDNA_GH_names
                                     )
    if options.auto_plot_Shp_data:
        insert_tool_after_specials(   self
                                     ,tools
                                     ,tools_dict['recolour_objects']
                                     ,lambda tool : tool == tools_dict['read_shapes_and_data_from_shapefile']
                                     ,[]
                                     )        

    report_value(f_name)
    report_value(gdm)
    report_value(opts_at_call)

    vals_dict = OrderedDict( [   ('f_name', f_name)
                                ,('gdm', gdm)
                                ,('opts_at_call', opts_at_call)
                             ]
                            )
    for tool in tools:
        if tool:
            report_value(tool)

            #returncode, f_name, gdm, tmp_a = 
            retvals = tool(  vals_dict['f_name']
                            ,vals_dict['gdm']
                            ,vals_dict['opts_at_call'] 
                            )
            vals_dict.update( OrderedDict(zip(tool.retvals, retvals)) )
            returncode = vals_dict['retcode']
            tmp_a = vals_dict['a']
            report('Tool name == ' + func_name(tool) + ' return code == ' + str(returncode))
            a.write(tmp_a)
            if returncode != 0:
                raise Exception(output(  'Tool ' + func_name(tool) + ' exited '
                                        +'with status code ' 
                                        + str(returncode),'ERROR'
                                        )
                                )
        else:
            raise TypeError(output('Bad tool == ' + str(tool), 'ERROR'))
    return vals_dict        
#
#
#############################################################################################################################


#############################################################################################################################
# Main component tool functions
#
#
def get_objects_from_Rhino(retvals = None, Required = None):
    #type() -> function
    def get_objs(f_name, geom_data_map, opts_at_call):
        #type(str, dict, dict) -> int, str, dict, list

        options = opts_at_call['options']
        a = WriteableFlushableList()
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




        report('First objects read: \n' + '\n'.join(str(x) for x in gdm.keys()[:3]))
        if len(gdm) > 0:
            report('type(gdm[0]) == ' + type(gdm.keys()[0]).__name__ )
        report('....Last objects read: \n' + '\n'.join(str(x) for x in gdm.keys()[-3:]))

        gdm = override_gdm_with_gdm(gdm, geom_data_map, opts_at_call)
        sc.doc = ghdoc # type: ignore 

        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in get_objs.retvals]
    if retvals == None:
        get_objs.retvals = 'retcode', 'f_name', 'gdm', 'a'
    else:
        get_objs.retvals = retvals
    if Required == None:
        get_objs.Required = (get_objs.retvals[0], 'Geom') + get_objs.retvals[1:]
    else:
        get_objs.Required = Required
    return get_objs


def read_Usertext_factory(retvals = None, Required = None):
    #type() -> function

    def read_Usertext(f_name, geom_data_map, opts_at_call):
        #type(str, dict, dict) -> int, str, dict, list

        report('Starting read_Usertext... ')
        options = opts_at_call['options']

        a = WriteableFlushableList()

        if (options.auto_get_objects_from_Rhino and
           (not geom_data_map or not hasattr(geom_data_map, 'keys') or
           (len(geom_data_map.keys()) == 1 and geom_data_map.keys()[0] == tuple() ))):
            #
            retcode, f_name, gdm, tmp_a = tools_dict['get_objects_from_Rhino'](  f_name
                                                                                ,geom_data_map
                                                                                ,opts_at_call
                                                                                )
            a.write(tmp_a)
            #
        else:
            retcode = 0
            gdm = geom_data_map
        #if opts_at_call['options'].read_overides_Data_from_Usertext:

        read_Usertext_as_tuples = get_OrderedDict()
        for obj in gdm:
            gdm[obj].update(read_Usertext_as_tuples(obj))

        # get_OrderedDict() will get Usertext from both the GH and Rhino docs
        # switching the target to RhinoDoc if needed, hence the following line 
        # is important:
        sc.doc = ghdoc # type: ignore 
        locs = locals().copy()
        return [locs[retval] for retval in read_Usertext.retvals]
    if retvals == None:
        read_Usertext.retvals = 'retcode', 'f_name', 'gdm', 'a'
    else:
        read_Usertext.retvals = retvals
    if Required == None:
        read_Usertext.Required = (read_Usertext.retvals[0], 'Geom', 'Data') + read_Usertext.retvals[1:]
    else:
        read_Usertext.Required = Required
    return read_Usertext


def write_objects_and_data_to_shapefile(retvals = None, Required = None):
    #type() -> function

    def write_shp(f_name, geom_data_mapping, opts_at_call):
        #type(str, dict, dict) -> int, str, dict, list
        
        options = opts_at_call['options']

        a = WriteableFlushableList()

        shp_type = options.shp_file_shape_type            
        #print geom_data_mapping
        if (options.auto_read_Usertext and
                (not geom_data_mapping or not hasattr(geom_data_mapping, 'values')
                or all(len(v) ==0  for v in geom_data_mapping.values()))):
            retcode, f_name, geom_data_mapping, tmp_a = tools_dict['read_Usertext'](   f_name
                                                                        ,geom_data_mapping
                                                                        ,opts_at_call
                                                                        )

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
            #report_value(obj)
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
            return geom_data_mapping[obj].keys() #tupl[1].keys() #rs.GetUserText(x,None)

        def get_data_item(obj, key):
            return geom_data_mapping[obj][key] #tupl[1][key]

        if not f_name:  
            if (   options.shape_file_to_write_Rhino_data_to_from_sDNA_GH
                and isdir(dirname( options.shape_file_to_write_Rhino_data_to_from_sDNA_GH ))   ):
                f_name = options.shape_file_to_write_Rhino_data_to_from_sDNA_GH
            else:
                f_name = options.Rhino_doc_path.rpartition('.')[0] + options.shp_file_extension
                            # file extensions are actually optional in PyShp, 
                            # but just to be safe and future proof we remove
                            # '.3dm'                                        

        #report('Type of geom_data_mapping == '+ type(geom_data_mapping).__name__)                         
        #report('Size of geom_data_mapping == ' + str(len(geom_data_mapping)))
        #report('Gdm keys == ' + ' '.join( map(lambda x : x[:5],geom_data_mapping.keys() )) )
        #report('Gdm.values == ' + ' '.join(map(str,geom_data_mapping.values())))
        sc.doc = Rhino.RhinoDoc.ActiveDoc 
        (retcode, f_name, fields, gdm) = ( 
                            write_from_iterable_to_shapefile_writer(
                                                geom_data_mapping
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
        return [locs[retval] for retval in write_shp.retvals]
    if retvals == None:    
        write_shp.retvals = 'retcode', 'f_name', 'gdm', 'a'
    else:
        write_shp.retvals = retvals
    if Required == None:
        write_shp.Required = write_shp.retvals
    else:
        write_shp.Required = Required
    return write_shp




def create_new_groups_layer_from_points_list(
     options = opts['options']
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
            report_value(points_list)
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

def get_shape_file_rec_ID(options = opts['options']): 
    #type(namedtuple) -> function
    def f(obj, rec):
        #report_value(obj)
        #report(type(obj).__name__)
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
                report_value(obj_ID)
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



def read_shapes_and_data_from_shapefile(retvals = None, Required = None):
    #type() -> function

    def read_shp( f_name, geom_data_mapping, opts_at_call ):
        #type(str, dict, dict) -> int, str, dict, list
        options = opts_at_call['options']

        a = WriteableFlushableList()

        ( fields
        ,recs
        ,shapes
        ,bbox ) = get_fields_recs_and_shapes_from_shapefile( f_name )

        if not recs:
            output('No data read from Shapefile ' + f_name + ' ','WARNING')
            return 1, f_name, geom_data_mapping, None    
            
        if not shapes:
            output('No shapes in Shapefile ' + f_name + ' ','WARNING')
            return 1, f_name, geom_data_mapping, None

            

        field_names = [ x[0] for x in fields ]

        report('options.uuid_shp_file_field_name in field_names == ' + str(options.uuid_shp_file_field_name in field_names))
        report_value(field_names)

        shapes_to_output = ([shp.points] for shp in shapes )
        
        obj_key_maker = create_new_groups_layer_from_points_list( options ) 



        if not options.create_new_groups_layer_from_shapefile:   #TODO: put new objs in a new layer or group
            obj_key_maker = get_shape_file_rec_ID(options) # key_val_tuples
            # i.e. if options.uuid_shp_file_field_name in field_names but also otherwise
        
            if isinstance(geom_data_mapping, dict) and len(geom_data_mapping) == len(recs):
                # figuring out an override for different number of overrided geom objects
                # to shapes/recs is to open a large a can of worms.  Unsupported.
                # If the override objects are in Rhino anyway then the uuid field in the shape
                # file will be picked up in any case in get_shape_file_rec_ID
                if sys.version_info.major < 3:
                    shape_keys = geom_data_mapping.viewkeys()  
                else: 
                    shape_keys = geom_data_mapping.keys()
                shapes_to_output = [shp_key for shp_key in shape_keys]
                    # These points shouldn't be used, as by definition they 
                    # come from objects that already
                    # exist in Rhino.  But if they are to be used, then use this!
                report_value(shapes_to_output)    


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

        if not options.bbox and not options.legend_extent:
            opts_at_call['options'] = opts_at_call['options']._replace(bbox = bbox)

        #override_gdm_with_gdm(gdm, gdm, opts_at_call)   # TODO:What for?

        if options.delete_shapefile_after_reading and isfile(f_name): 
            os.remove(f_name)  # TODO: Fix, currently Win32 error

        retcode = 0

        locs = locals().copy()
        return [locs[retval] for retval in read_shp.retvals]
    if retvals == None:
        read_shp.retvals = 'retcode', 'f_name', 'gdm', 'a', 'abbrevs', 'sDNA_fields'
    if Required == None:
        read_shp.Required = (read_shp.retvals[0], 'Geom', 'Data') + read_shp.retvals[1:]
    else:
        read_shp.Required = Required
    return read_shp



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
    # return 0, f_name, gdm, opts_at_call



def write_data_to_Usertext(retvals = None, Required = None):
    #type() -> function

    def write_Usertext(   f_name     #Bake_Geom_and_Data
                ,gdm  # nested dict
                ,opts_at_call
                ):
        #type(str, dict, dict) -> int, str, dict, list
        options = opts_at_call['options']

        a = WriteableFlushableList()

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
        return [locs[retval] for retval in write_Usertext.retvals]
    if retvals == None:
        write_Usertext.retvals = 'retcode', 'gdm', 'a'
    if Required == None:
        write_Usertext.Required = write_Usertext.retvals #[0] + ('Geom', 'Data') + write_Usertext.retvals[1:]
    else:
        write_Usertext.Required = Required
    return write_Usertext

def bake_and_write_data_as_Usertext_to_Rhino(retvals = None, Required = None):
    #type() -> function

    def bake_Usertext(f_name, geom_data_mapping, opts_at_call ):
        #type(str, dict, dict) -> int, str, dict, list  
        a = WriteableFlushableList()

        gdm = OrderedDict()
        for obj in geom_data_mapping:
            doc_obj = ghdoc.Objects.Find(obj)
            if doc_obj:
                geometry = doc_obj.Geometry
                attributes = doc_obj.Attributes
                if geometry:
                    add_to_Rhino = Rhino.RhinoDoc.ActiveDoc.Objects.Add 
                    # trying to avoid constantly switching sc.doc

                    gdm[add_to_Rhino(geometry, attributes)] = geom_data_mapping[obj] # The bake
        
        retcode, gdm, tmp_a = tools_dict['write_data_to_Usertext'](f_name, gdm, opts_at_call)
        a.write(tmp_a)
        # write_data_to_USertext context switched when checking so will move
        #sc.doc = Rhino.RhinoDoc.ActiveDoc on finding Rhino objects.
        locs = locals().copy()
        return [locs[retval] for retval in bake_Usertext.retvals]
    if retvals == None:
        bake_Usertext.retvals = 'retcode', 'a' #'f_name', 'gdm', 'a'
    if Required == None:
        bake_Usertext.Required = bake_Usertext.retvals #[0] + ('Geom', 'Data') + bake_Usertext.retvals[1:]
    else:
        bake_Usertext.Required = Required
    return bake_Usertext


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


def parse_data_factory(retvals = None, Required = None):
    #type() -> function

    def parse_data(f_name, geom_data_map, opts_at_call):
        #type(str, dict, dict) -> int, str, dict, list
        # Note!  opts_at_call can be mutated.
        options = opts_at_call['options']

        a = WriteableFlushableList()

        field = options.sDNA_output_abbrev_to_graph

        data = [ val[field] for val in geom_data_map.values()]
        report('data == ' + str(data[:3]) + ' ... ' + str(data[-3:]))
        x_max = max(data) if options.plot_max == None else options.plot_max
        x_min = min(data) if options.plot_min == None else options.plot_min
        # bool(0) == False so in case x_min==0 we can't use 
        # if options.plot_min if options.plot_min else min(data) 


        no_manual_classes = (not isinstance(options.class_boundaries, list)
                            or not all( isinstance(x, Number) 
                                            for x in options.class_boundaries
                                        )
                            )

        if options.sort_data or (no_manual_classes 
        and options.class_spacing == 'equal_spacing'): 
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
                class_boundaries = [ val[field] for val in 
                                    gdm.values()[objs_per_class:m*objs_per_class:objs_per_class] 
                                ]  # classes include their lower bound
                report('num class boundaries == ' + str(len(class_boundaries)))
                report_value(options.number_of_classes)
                report_value(n)
                assert len(class_boundaries) + 1 == options.number_of_classes
            else: 
                class_boundaries = [
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
            class_boundaries = options.class_boundaries
        
        opts_at_call['options'] = opts_at_call['options']._replace(
                                            class_boundaries = class_boundaries
                                           ,plot_max = x_max
                                           ,plot_min = x_min
                                                                )


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

                highest_lower_bound = x_min if x < class_boundaries[0] else max(y 
                                                for y in class_boundaries + [x_min] 
                                                if y <= x                       )
                #Classes include their lower bound
                least_upper_bound = x_max if x >= class_boundaries[-1] else min(y for y in class_boundaries + [x_max] 
                                        if y > x)

                return re_normaliser (0.5*(least_upper_bound + highest_lower_bound))

        #retvals = {}

        # todo:  '{n:}'.format() everything to apply localisation, 
        # e.g. thousand seperators


        mid_points = [0.5*(x_min + min(class_boundaries))]
        mid_points += [0.5*(x + y) for (x,y) in zip(  class_boundaries[0:-1]
                                                    ,class_boundaries[1:]  
                                                )
                    ]
        mid_points += [ 0.5*(x_max + max(class_boundaries))]
        report_value(mid_points)

        locale.setlocale(locale.LC_ALL,  options.locale)

        x_min_s = options.num_format.format(x_min)
        upper_s = options.num_format.format(min( class_boundaries ))
        mid_pt_s = options.num_format.format( mid_points[0] )

        legend_tags = [options.first_legend_tag_format_string.format( 
                                                                lower = x_min_s
                                                                ,upper = upper_s
                                                                ,mid_pt = mid_pt_s
                                                                    )
                                                        ]
        for lower_bound, mid_point, upper_bound in zip( 
                                            class_boundaries[0:-1]
                                            ,mid_points[1:-1]
                                            ,class_boundaries[1:]  
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

        lower_s = options.num_format.format(max( class_boundaries ))
        x_max_s = options.num_format.format(x_max)
        mid_pt_s = options.num_format.format(mid_points[-1])

        legend_tags += [options.last_legend_tag_format_string.format( 
                                                                lower = lower_s
                                                                ,upper = x_max_s 
                                                                ,mid_pt = mid_pt_s 
                                                                    )        
                        ]                                                       

        assert len(legend_tags) == options.number_of_classes == len(mid_points)

        report_value(legend_tags)

        #first_legend_tag_format_string = 'below {upper}'
        #inner_tag_format_string = '{lower} - {upper}' # also supports {mid}
        #last_legend_tag_format_string = 'above {lower}'

        #retvals['max'] = x_max = max(data)
        #retvals['min'] = x_min = min(data)

        gdm = OrderedDict(zip( geom_data_map.keys() + legend_tags 
                            ,(classifier(x) for x in data + mid_points)
                            )
                        )
        plot_min, plot_max = options.plot_min, options.plot_max
        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in parse_data.retvals]
    if retvals == None:
        parse_data.retvals = 'retcode', 'plot_min', 'plot_max', 'f_name', 'gdm', 'a'
    if Required == None:
        parse_data.Required = parse_data.retvals[:3] + ('Data', 'Geometry') + parse_data.retvals[3:]
    else:
        parse_data.Required = Required
    return parse_data      


def recolour_objects_factory(retvals = None, Required = None):
    #type() -> function

    def recolour_objects(f_name, geom_data_map, opts_at_call):
        #type(str, dict, dict) -> int, str, dict, list
        # Note!  opts_at_call can be mutated.

        options = opts_at_call['options']

        a = WriteableFlushableList()
        
        field = options.sDNA_output_abbrev_to_graph
        objs_to_parse = OrderedDict(  (k, v) for k, v in geom_data_map.items()
                                    if isinstance(v, dict) and field in v    
                                    )
        if objs_to_parse:
            ret_code, f_name, gdm, messages = tools_dict['parse_data'](  f_name
                                                                        ,objs_to_parse
                                                                        ,opts_at_call
                                                                        )
        else:
            gdm = {}

        x_min, x_max = options.plot_min, options.plot_max

        objs_to_get_colour = OrderedDict( (k, v) for k, v in geom_data_map.items()
                                                if isinstance(v, Number) 
                                        )
        objs_to_get_colour.update(gdm)  # no key clashes possible unless some x
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
            #report_value(obj)
            if is_uuid(obj): # and is_an_obj_in_GH_or_Rhino(obj):
                target_doc = is_an_obj_in_GH_or_Rhino(obj)    
                if target_doc:
                    sc.doc = target_doc
                    if False: #target_doc == ghdoc:
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
            sc.doc.Views.Redraw()
            sc.doc = ghdoc


        # "Node in code"
        #pt = rs.CreatePoint(0, 0, 0)
        #bbox = BoundingBox(objs_to_recolour.keys, XYPlane(pt)) # BoundingBox(XYPlane

        #bbox_xmin = min(list(p)[0] for p in bbox.box.GetCorners()[:4] )
        #bbox_xmax = max(list(p)[0] for p in bbox.box.GetCorners()[:4] )
        #bbox_ymin = min(list(p)[1] for p in bbox.box.GetCorners()[:4] )
        #bbox_ymax = max(list(p)[1] for p in bbox.box.GetCorners()[:4] )

        if options.bbox:
            bbox = [bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax] = options.bbox

            legend_xmin = bbox_xmin + (1 - 0.4)*(bbox_xmax - bbox_xmin)
            legend_ymin = bbox_ymin + (1 - 0.4)*(bbox_ymax - bbox_ymin)
            legend_xmax, legend_ymax = bbox_xmax, bbox_ymax
            
            report_value(bbox)

        elif options.legend_extent:
            [legend_xmin
            ,legend_ymin
            ,legend_xmax
            ,legend_ymax] = options.legend_extent

    

        #rectangle = Rectangle( XYPlane(pt)
        #                      ,[legend_xmin, legend_xmax]
        #                      ,[legend_ymin, legend_ymax]
        #                      ,0
        #                      )

        plane = rs.WorldXYPlane()
        rectangle = rs.AddRectangle(plane
                                ,legend_xmax - legend_xmin
                                ,legend_ymax - legend_ymin )

        rs.MoveObject(rectangle, [1.07*bbox_xmax, legend_ymin])

        opts_at_call['options'] = opts_at_call['options']._replace(
                                            legend_rectangle = rectangle 
                                                                )

        #def c():
            #return GH_Colour(Color.FromArgb(r(0,255), r(0,255), r(0,255)))
            #return Color.FromArgb(r(0,255), r(0,255), r(0,255))
            #return rs.CreateColor(r(0,255), r(0,255), r(0,255))
        #tags=['Tag1', 'Tag2', 'Tag3', 'Tag4', 'Tag5']
        #colours = [c(), c(), c(), c(), c()]
        #rect = sc.doc.Objects.FindGeometry(rectangle)
        #for k, v in legend_tags.items():
        #    Legend(Colour.FromArgb(*v), k, rectangle)
        #Legend( [GH_Colour(Colour.FromArgb(*v)) for v in legend_tags.values()]
        #       ,list(legend_tags.keys()) 
        #       ,rectangle
        #       )

        leg_tags = list(legend_tags.keys())
        leg_cols = list(legend_tags.values())


        sc.doc =  ghdoc # type: ignore
        retcode = 0

        locs = locals().copy()
        return [locs[retval] for retval in recolour_objects.retvals]
    if retvals == None:
        recolour_objects.retvals = 'retcode', 'leg_cols', 'leg_tags', 'rectangle', 'a'
    if Required == None:
        recolour_objects.Required = (recolour_objects.retvals[0], 'Geom', 'Data') + recolour_objects.retvals[1:]
          # To recolour GH Geom with a native Preview component
    else:
        recolour_objects.Required = Required
    return recolour_objects



                  



#########################################################
#Grasshopper component auto add/remove output param rules
#
do_not_add = ['retcode'] # Won't be added automatically
#
do_not_remove = ('out'
                ,'OK'
                ,'Data'
                ,'Geometry'
                ,'f_name'
                ,'gdm'
                ,'a'
                ,'opts'
                ,'l_metas'
                ,'retcode' # But if user adds it, we won't remove it
                )
#
do_not_remove += default_metas._fields
do_not_remove += default_options._fields
do_not_remove += local_metas._fields
#########################################################


def cache_syntax_and_UISpec(nick_name, tool_name, local_opts):    
    # type(str, dict) -> str, dict, function

    sDNA, UISpec = local_opts['metas'].sDNA, local_opts['options'].UISpec
    #
    global get_syntax_dict, do_not_remove
    # 
    #
    def update_or_init(cache, defaults, nick_name, tool_name):
        #type(dict, dict / function, str, str) -> None
        def getdefaults():
            if isinstance(defaults, dict):
                return make_nested_namedtuple( defaults,  nick_name ) #+ '_' + tool_name ) 
            else:
                return defaults

        cache.setdefault(nick_name, OrderedDict()) #OrderedDict([(1,2)])
        
        if nick_name != tool_name:
            cache.setdefault(tool_name, OrderedDict()) #OrderedDict([(3,4)])
            cache[nick_name].setdefault(tool_name, OrderedDict()) #OrderedDict([(2,3)])
            cache[nick_name][tool_name].setdefault( sDNA 
                                                   ,cache[tool_name].setdefault( sDNA
                                                                                ,getdefaults()
                                                                                )
                                                   )
        else:
            cache[tool_name].setdefault(sDNA, getdefaults() )
        #
        #
        #if nick_name not in cache:
        #    cache[nick_name] =  {}
        #if  (   nick_name != tool_name and
        #        tool_name not in cache[nick_name]   ):
        #    cache[nick_name][tool_name] = {}
        #if sDNA not in cache[nick_name][tool_name]: # and name is a tool name not a nick name
        #    cache[nick_name][tool_name][sDNA] = ( make_nested_namedtuple( defaults,  name ) 
        #                if isinstance(defaults, dict) else defaults  )
        #else:
        #    output('Name : ' + name + ' already in cache ', 'INFO')
            #if isinstance(defaults, dict) and hasattr(cache[name][sDNA]
            #                                            ,'_asdict'): #NT
            #    defaults.update(cache[name][sDNA]._asdict())


    if hasattr(UISpec, tool_name):
        sDNA_tool_instance = getattr( UISpec,  tool_name )()

        get_syntax = sDNA_tool_instance.getSyntax     
        # not called until component executes in RunScript
        update_or_init( get_syntax_dict,  get_syntax,  tool_name, tool_name )
        # Global get_syntax_dict intentional
        input_spec = sDNA_tool_instance.getInputSpec()
        defaults_dict = { varname : default for (    varname
                                                    ,displayname
                                                    ,datatype
                                                    ,filtr
                                                    ,default
                                                    ,required
                                                ) in input_spec  }
        update_or_init(  local_opts, defaults_dict, nick_name, tool_name )
        do_not_remove += tuple(defaults_dict.keys())
        # Tool options are stored per nick_name, which may equal tool_name
    else:
        update_or_init( local_opts,  OrderedDict(),  nick_name, tool_name )
        #update_or_init( get_syntax_dict,  OrderedDict(),  tool_name, tool_name )
    return #local_opts[nick_name], get_syntax_dict[tool_name]



tools_dict=dict( get_objects_from_Rhino = [get_objects_from_Rhino()]
                ,read_Usertext = [read_Usertext_factory()]
                ,write_objects_and_data_to_shapefile = [write_objects_and_data_to_shapefile()]
                ,read_shapes_and_data_from_shapefile = [read_shapes_and_data_from_shapefile()]
                ,write_data_to_Usertext = [write_data_to_Usertext()]
                ,bake_and_write_data_as_Usertext_to_Rhino = [bake_and_write_data_as_Usertext_to_Rhino()]
                ,parse_data = [parse_data_factory()]
                ,recolour_objects = [recolour_objects_factory()] # Needed in iterable wrappers
                )

support_component_names = list(tools_dict.keys())[:] # In Python 3, .keys() and 
                                                     # .values() are dict views
                                                     # not lists

special_names =           [  'sDNA_general'
                            ]

sDNA_GH_names = support_component_names + special_names + ['Python', 'selftest']


def list_contains(check_list, name, name_map):
    # type( MyComponent, list(str), str, dict(str, str) ) -> bool
    name_map
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


def return_component_names_factory(name_map, retvals = None, Required = None): 
                                       # name_map is unknown in this module so 
                                       # create closure. Call it from outside.
    def return_component_names(f_name, gdm, local_opts):
        UISpec = local_opts['options'].UISpec
        
        sDNA_tool_names = [Tool.__name__ for Tool in UISpec.get_tools()]
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
        #return special_names + support_component_names + sDNA_tool_names, None, None, None, self.a 

        ret_names = ([name for name in names_list 
                           if name not in name_map] #.values()] 
                     + list(name_map._fields) #keys())
                    )

        #return 0, None, {}, ret_names, #names_list
        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in return_component_names.retvals]
    if retvals == None:
        return_component_names.retvals = 'retcode', 'names'
    else:
        return_component_names.retvals = retvals
    if Required == None:
        return_component_names.Required = return_component_names.retvals
    else:
        return_component_names.Required = Required  


    return [return_component_names]


def get_specific_tool(tool_name
                     ,nick_name
                     ,local_opts
                     ,retvals = None
                     ,Required = None
                     ):
    # type(str) -> function

    UISpec = local_opts['options'].UISpec

    #if tool_name in support_component_names:
    #    def support_tool_wrapper(f_name, Geom, Data, opts):  
    #        return globals()[tool_name](f_name, Geom, Data)
    #    tools_dict[tool_name] = support_tool_wrapper   
        #
        #
    if hasattr(UISpec, tool_name): 
        def run_sDNA_wrapper(f_name, gdm, opts_at_call):
            #type(Class, dict(namedtuple), str, Class, DataTree)-> Boolean, str
            #global opts # - deliberate to access global 
            #
            # Closure due to dependence on nick_name and name
            #
            (sDNA, UISpec, run ) = ( opts_at_call['metas'].sDNA
                                    ,opts_at_call['options'].UISpec
                                    ,opts_at_call['options'].run )
            
            options = opts_at_call['options']
            tool_opts = opts_at_call[nick_name]
            report_value(tool_opts)

            tool_opts = tool_opts.get(tool_name, tool_opts)
            report_value(tool_opts)

            dot_shp = options.shp_file_extension

            a = WriteableFlushableList()

            input_file = tool_opts[sDNA].input
            

            if (not isinstance(input_file, str)) or not isfile(input_file): 
                if (isinstance(f_name, str) and isfile(f_name)
                    and f_name.rpartition('.')[2] in [dot_shp[1:],'dbf','shx']):  
                    input_file = f_name
                    
                if options.auto_write_new_Shp_file and (
                   options.overwrite_input_shapefile 
                   or not isfile(input_file)                  ):
                    retcode, input_file, gdm, tmp_a = tools_dict['write_objects_and_data_to_shapefile']( 
                                                                                             input_file
                                                                                            ,gdm
                                                                                            ,opts_at_call
                                                                                            )
                    a.write(tmp_a)
                
                tool_opts[sDNA] = tool_opts[sDNA]._replace(input = input_file)


            output_file = tool_opts[sDNA].output
            if output_file == '':
                output_suffix =  options.output_shp_file_suffix
                if tool_name == 'sDNAPrepare':
                    output_suffix = options.prepped_shp_file_suffix   
                output_file = input_file.rpartition('.')[0] + output_suffix + dot_shp

            output_file = get_unique_filename_if_not_overwrite(output_file, options)

            tool_opts[sDNA] = tool_opts[sDNA]._replace(output = output_file)
            f_name = output_file

            syntax = get_syntax_dict[tool_name][sDNA]( 
                                                    tool_opts[sDNA]._asdict() 
                                                     )   
                            #opts[nick_name] was initialised to defaults in 
                            # in cache_syntax_and_UISpec
            #        get_syntax_dict in module global name space                     

            command = (options.python_exe 
                       + ' -u ' 
                       + '"' 
                       + join(  dirname(UISpec.__file__)
                                ,'bin'
                                ,syntax['command'] + '.py'  
                              ) 
                       + '"'
                       + ' --im ' + run.map_to_string( syntax["inputs"] )
                       + ' --om ' + run.map_to_string( syntax["outputs"] )
                       + ' ' + syntax["config"]
                      )
            
            sDNA_logger.debug(command)

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
                        sDNA_logger.debug(line)
                except:
                    pass
            #return_code = call(command)   
            
            #return_code = run.runsdnacommand(    syntax
            #                                    ,sdnapath = dirname(UISpec.__file__)  #opts['options'].sDNA_UISpec_path
            #                                    ,progress = IllusionOfProgress()
            #                                    ,pythonexe = options.python_exe
            #                                    ,pythonpath = None)   # TODO:  Work out if this is important or not! 
                                                                    # os.environ["PYTHONPATH"] not found in Iron Python

            #return return_code, tool_opts[sDNA].output, gdm, a
            locs = locals().copy()
            return [locs[retval] for retval in run_sDNA_wrapper.retvals]
        if retvals == None:
            run_sDNA_wrapper.retvals = 'retcode', 'f_name', 'gdm', 'a'
        else:
            run_sDNA_wrapper.retvals = retvals
        if Required == None:
            run_sDNA_wrapper.Required = ('f_name',)
            run_sDNA_wrapper.Required = (run_sDNA_wrapper.retvals[0], 'Geom', 'Data') + run_sDNA_wrapper.retvals[1:]
        else:
            run_sDNA_wrapper.Required = Required    
        return [run_sDNA_wrapper]
    else:
        return [None]


def tool_factory(self, nick_name, name_map, local_opts):  
    #type( type[any], str, namedtuple, dict ) -> list

    #sDNA, UISpec, run = local_opts['options'].sDNA, local_opts['options'].UISpec, local_opts['options'].run

    #global tools_dict # mutable - access through normal parent module namespace

    sDNA = local_opts['metas'].sDNA
    global tools_dict
    # A special component that takes its nickname from the parameters provided,
    # only working out which tools to run at run time.  
    def tool_factory_wrapper(inst, f_name, gdm, opts_at_call):
        tools = tool_factory( inst 
                             ,opts_at_call['options'].tool_name
                             ,name_map  
                             ,opts_at_call 
                             )
        inst.update_component_outputs(tools)
        return run_tools(inst, tools, f_name, gdm, opts_at_call)

 
    if isinstance(nick_name, Hashable):
        if (   nick_name not in tools_dict or 
               sDNA not in local_opts.get(nick_name, {})   ):
            map_result = getattr(name_map, nick_name, nick_name)  # in case nick_name == tool_name
            if not isinstance(map_result, str):
                output('Processing list of tools found for '
                       + nick_name, 'DEBUG')
                tools =[]
                #nick_name_opts = {}
                for mapped_name in map_result:
                    tools += tool_factory( self
                                          ,mapped_name
                                          ,name_map
                                          ,local_opts 
                                          )
                    #cache_syntax_and_UISpec(nick_name, mapped_name, local_opts)                    
                    # Not needed as no function closure will ever be 
                    # created that refers to self.opts[nickname][not a tool_name]

                    #nick_name_opts[mapped_name] = local_opts[mapped_name]
                tools_dict[nick_name] = tools 
            else:
                mapped_name = map_result
                cache_syntax_and_UISpec(nick_name, mapped_name, local_opts) 
                output(nick_name + ' maps to ' + mapped_name,'DEBUG')

                if mapped_name in support_component_names:
                    tools_dict[nick_name] = tools_dict[mapped_name]
                    output(mapped_name + ' in support_component_names','DEBUG')
                elif nick_name == 'Python': #Dev tool for naming components
                    tools_dict[nick_name] = return_component_names_factory(name_map) 
                    output(nick_name + ' is "Python"','DEBUG')
                    # Needs to be here to be passed name_map

                elif nick_name in special_names: #["sDNA_general"]  
                    output(nick_name + ' is in special_names','DEBUG')

                # Not 'elif' to create opts for "Python"
                    tools_dict[nick_name] = tool_factory_wrapper 
                else:  # mapped_name is a tool_name, possibly named explicitly in nick_name
                    # create entries for sDNA tools and non-special support tools & "Python"
                    output(nick_name + ' needs new tool to be built, e.g. from sDNA. ','DEBUG')

                    tools_dict[nick_name] = get_specific_tool(mapped_name, nick_name, local_opts)  
                    # assert isinstance(get_specific_tool(map_result, nick_name, name_map, local_opts), list)

        report('tools_dict[' + nick_name + '] == ' + str(tools_dict[nick_name][0]) )
        return tools_dict[nick_name] 
    else:
        output('Non-hashable variable given for key' + str(nick_name),'ERROR')
        return [None]



def module_loader( self, m_names, path_lists ): #sDNA, self.opts['metas'].sDNA_search_paths):
    modules = ()
    try:
        tmp = sys.path
        for test_path in path_lists: 
            #TODO support nested lists
            sys.path = [test_path]
            if all(isfile(join(test_path, m_name) + '.py' )
                    for m_name in m_names):
                path = test_path
                break
        for m_name in m_names:
            modules += ( import_module(m_names[0],''), )
    finally:
        sys.path = tmp

    return modules + (path,)
    #return tuple(strict_import(name, path, '') for name in m_names) + (path,)
    #return self.UISpec, self.run, path




def component_decorator(BaseClass, loader = module_loader):
    #type:(type[type], function) -> type[type]
    class sDNA_GH_Component(BaseClass):
        
        #GH Environment `magic' global variables:
        ghdoc = ghdoc #type: ignore
        #Component = ghenv.Component #type: ignore
        RhinoDoc = Rhino.RhinoDoc

        # Options from defautls and installation config.toml
        opts = opts  
        local_metas = local_metas   # immutable.  controls syncing /
                                    # desyncing / read / write of the
                                    # above, opts.
                                    # Although local, can be set on 
                                    # groups of components using the 
                                    # default section of a project 
                                    # config.ini, or passed as a
                                    # Grasshopper parameter between
                                    # components

        #sDNA_GH_path = sDNA_GH_path
        #sDNA_GH_package = sDNA_GH_package

        def remove_component_output(self, name):
            for param in self.Params.Output:
                if param.NickName == name:
                    self.Params.Output.Remove(param)
        

        def update_component_outputs( self
                                     ,tools = None  
                                     ):
            global do_not_add
            
            if tools == None:
                tools = self.my_tools
            tool = tools[-1] 
            params_needed = tool.Required
            params_current = self.Params.Output[:]

            for param in params_current:  
                if param.NickName in params_needed:
                    do_not_add += [param.NickName]
                elif (     param.NickName not in do_not_remove
                           and len(param.Recipients) == 0        ):
                    self.Params.Output.Remove(param)
                # else:  Leave alone.  The user added the param, 
                # or the component was supplied that way by ourselves.
                    do_not_add += [param.NickName]
            for param_name in params_needed:
                if param_name not in do_not_add: 
                    var = Grasshopper.Kernel.Parameters.Param_String(NickName = param_name)

                    #var.NickName = param
                    #var.Name = param
                    #var.Description = "test var"
                    var.Access = Grasshopper.Kernel.GH_ParamAccess.list
                    self.Params.RegisterOutputParam(var)
            self.Params.OnParametersChanged()
    

        def update_tools(self):
            #self.my_tools = []

            #for tool in tools:
            #    # some are unique closures so no #if not hasattr(self, tool.func_name):
            #    setattr(self, func_name(tool), tool)
            #    self.my_tools +=[getattr(self, func_name(tool))]
            
            #Avoid issues with calling tools stored as methods with self:
            self.my_tools = tool_factory(self 
                                        ,self.nick_name
                                        ,self.opts['metas'].name_map
                                        ,self.opts)
            output('My_tools ==\n'
                    +'\n'.join([func_name(tool) for tool in self.my_tools])
                    ,'DEBUG')

            report_value('self.opts : '+ str(self.opts))
            output('\n'.join(str(k) + ' : ' + str(v) 
                             for k,v in self.opts.items()
                             if k not in ('options','metas')
                             )
                   ,'DEBUG')

            self.update_component_outputs()


        def update_name(self, new_name = 'selftest'):       
            self.nick_name = new_name 
            self.logger = logger.getChild(self.nick_name)
            self.update_tools()


            
        def update_sDNA(self):
            output('Self has attr sDNA == ' + str(hasattr(self,'sDNA'))+' ','DEBUG')
            output('self.opts[metas].sDNA == (' + str(self.opts['metas'].sDNAUISpec)
                    + ', ' + self.opts['metas'].runsdna + ') ','DEBUG')

            if hasattr(self,'sDNA'):
                output('Self has attr sDNA == ' + str(hasattr(self,'sDNA'))+' ','DEBUG')
            
            sDNA = ( self.opts['metas'].sDNAUISpec  # Needs to be hashable to be
                    ,self.opts['metas'].runsdna )   # a dict key => tuple not list

            if not hasattr(self,'sDNA') or self.sDNA != sDNA:
                self.UISpec, self.run, path = self.loader( self
                                                        ,sDNA
                                                        ,self.opts['metas'].sDNA_search_paths
                                                        ) 




                output('Self has attr UISpec == ' + str(hasattr(self,'UISpec'))+' ' , 'DEBUG')
                output('Self has attr run == ' + str(hasattr(self,'run'))+' ' ,'DEBUG')

                self.sDNA = sDNA
                self.sDNA_path = path
                self.opts['metas'] = self.opts['metas']._replace(    sDNA = self.sDNA
                                                                    ,sDNA_path = path 
                                                                )
                self.opts['options'] = self.opts['options']._replace(  UISpec = self.UISpec
                                                                      ,run = self.run 
                                                                    )  

                assert self.opts['metas'].sDNA_path == dirname(self.opts['options'].UISpec.__file__)                                                                  






        def __init__(self, *args, **kwargs):

            BaseClass.__init__(self, *args, **kwargs)
            self.loader = loader
            self.a = WriteableFlushableList()

            self.update_sDNA() 
            # update_name and update_tools within it will get called in RunScript

            add_file_to_logger = wrapper_logging.add_custom_file_to_logger
            add_file_to_logger(  logger
                                ,self.a
                                ,self.opts['options'].logger_custom_level)








        #sDNA_GH = strict_import('sDNA_GH', join(Grasshopper.Folders.DefaultAssemblyFolder,'sDNA_GH'), sub_folder = 'sDNA_GH')   
                                            # Grasshopper.Folders.AppDataFolder + r'\Libraries'
                                            # %appdata%  + r'\Grasshopper\Libraries'
                                            # os.getenv('APPDATA') + r'\Grasshopper\Libraries'
        def RunScript(self, go, Data, Geom, f_name, *args):
            # type (bool, str, Rhino Geometry, datatree, tuple(namedtuple,namedtuple), *dict)->bool, str, Rhino_Geom, datatree, str
            
            #if not 'opts' in globals():
            #    global opts
            if f_name and not isinstance(f_name, str) and isinstance(f_name, list):
                    f_name=f_name[0] 
            
            self.a = WriteableFlushableList() 
            #Output from previous calls to RunScript is already logged elsewhere.

            args_dict = {key.Name : val for key, val in zip(self.Params.Input[1:], args) } # type: ignore
            
            external_opts = args_dict.get('opts', {})
            external_local_metas = args_dict.get('local_metas', {})
            gdm = args_dict.get('gdm', {})

            #print('#1 self.local_metas == ' + str(self.local_metas))
            
    
            try:
                new_name = self.Attributes.Owner.NickName #type: ignore 
            except:
                new_name = "selftest"     

            if not hasattr(self, 'nick_name') or (
               self.opts['metas'].allow_components_to_change_type
               and self.nick_name != new_name    ):  
                #
                self.update_name(new_name)

                output( ' Component nick name changed to : ' 
                                + self.nick_name, 'INFO' )
                output( ' Tools in ' + self.nick_name + ' changed to : ' 
                                + str(self.my_tools), 'INFO' )
            
            
            synced = self.local_metas.sync_to_shared_global_opts
            old_sDNA = self.opts['metas'].sDNA

            #print('#1.05 self.local_metas == ' + str(self.local_metas))

            #if not self.local_metas.sync_to_shared_global_opts and self.local_metas.read_from_shared_global_opts:
            #    self.opts = opts.copy() 
            
            self.local_metas = override_all_opts( 
                                                 args_dict 
                                                ,self.opts # mutated
                                                ,external_opts 
                                                ,self.local_metas 
                                                ,external_local_metas
                                                ,self.nick_name
                                                )


            print()
            #output('#2 self.local_metas == ' + str(self.local_metas),'DEBUG')
            
            if (self.opts['metas'].auto_update_Rhino_doc_path 
                or not isfile(self.opts['options'].Rhino_doc_path)        ):

                path = get_path()

                self.opts['options'] = self.opts['options']._replace( Rhino_doc_path = path )

            if self.opts['metas'].allow_components_to_change_type: 
                
                if self.local_metas.sync_to_shared_global_opts != synced:
                    if self.local_metas.sync_to_shared_global_opts:
                        self.opts = opts 
                    else:
                        self.opts = self.opts.copy()

                if self.opts['metas'].sDNA != old_sDNA:
                    self.update_sDNA()
                    self.update_tools()   # Again, if name has also changed.  
                                          # But it was unavoidable (rare).
            


                    

            Defined_tools = [y for z in tools_dict.values() for y in z]
            print(Defined_tools)
            print(type(Defined_tools))
            Undefined_tools = [x for x in self.my_tools if x not in Defined_tools]

            if Undefined_tools:
                output('Defined_tools == ' + str(Defined_tools), 'DEBUG')
                output('Undefined tools == ' + str(Undefined_tools), 'DEBUG')
                raise ValueError(output('Tool function not in cache, possibly ' 
                                        + 'unsupported.  Check input tool_name '
                                        +'if sDNAGeneral, else tool_factory '
                                        ,'ERROR',self))


            if go in [True, [True]]: # [True] in case go set to List Access in GH component 
                returncode = 999
                assert isinstance(self.my_tools, list)

                output('my_tools == '+str(self.my_tools),'DEBUG')

                geom_data_map = convert_Data_tree_and_Geom_list_to_gdm(  Geom
                                                                        ,Data
                                                                        ,self.opts
                                                                        )
                
                output('type(geom_data_map) == ' + str(type(geom_data_map)), 'DEBUG')
                

                geom_data_map = override_gdm_with_gdm(   gdm
                                                        ,geom_data_map
                                                        ,self.opts
                                                        )

                output('After merge type(geom_data_map) == ' 
                        +str(type(geom_data_map))
                        ,'DEBUG'
                        )                
                
                output(   'After merge geom_data_map == ' 
                        +str(geom_data_map.items()[:3])
                        +' ...'
                        ,'DEBUG'
                        )


                ret_vals_dict = run_tools(   self
                                            ,self.my_tools
                                            ,f_name
                                            ,geom_data_map
                                            ,self.opts
                                            )
                gdm = ret_vals_dict['gdm']
                print (str(gdm))
                if isinstance(gdm, dict):
                    (NewData, Geometry) = (
                    convert_dictionary_to_data_tree_or_lists(gdm)
                                        )                
                else:
                    NewData, Geometry = None, None
                ret_vals_dict['Data'] = NewData
                ret_vals_dict['Geometry'] = Geometry
                #ret_vals_dict
                #ret_vals = ((returncode==0)
                #            ,NewData
                #            ,Geometry
                #            ,ret_f_name
                #            ,[gdm]
                #            ,a
                #            ,[self.opts.copy()]
                #            ,[self.local_metas]
                #            )
                #ret_vals = (returncode==0), NewData, Geometry, ret_f_name, a 

                #if self.my_tools[-1] == tools_dict['parse_data']:
                #    ret_vals = ( ret_vals[0]
                #                ,options.plot_min
                #                ,options.plot_max   ) + ret_vals[1:] #TODO!!!!!!!!!!!!!!
                ret_vals_dict['retcode'] = (ret_vals_dict['retcode'] == 0)

                def get_val(key):
                    return                    ret_vals_dict.get(key,
                                    getattr(self.opts['metas'], key,
                                    getattr(self.opts['metas'], key,
                                      getattr(self.local_metas, key,
                        self.opts.get(self.nick_name,{}).get(self.opts['metas'].sDNA,{}).get(key, None)))))


                ret_vals = tuple(get_val(param.NickName) for param in self.Params.Output)
                return ret_vals
                                            #In Python 3 .keys() returns a dictview not a list
            else:   
                return (False, ) + repeat(None, len(self.Params.Output) - 1)
                #return False, Data, Geom, f_name, self.a #, self.opts.copy(), self.local_metas
                return ( False
                        ,Data
                        ,Geom
                        ,f_name
                        ,[gdm]
                        ,self.a
                        ,[self.opts.copy()]
                        ,[self.local_metas]
                        )
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


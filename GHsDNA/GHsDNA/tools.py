#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.01'

import sys, os  
from os.path import join, split, isfile, dirname
from re import match
from subprocess import call
from time import asctime
from collections import namedtuple, OrderedDict
from itertools import chain, izip, cycle
import inspect
from uuid import UUID

if sys.version < '3.3':
    from collections import Hashable
else:
    from collections.abc import Hashable



def get_stem_and_folder(path):
    if isfile(path):
        path=dirname(path)
    return split(path)

class HardcodedMetas(): 
    config_file_path = join( dirname(dirname(__file__)), r'config.ini')
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
    #share_installation_defaults_key = "GHsDNA_installation_default_options"
    #share_sDNA_tools_key = "sDNA_UI_Spec_tools"
    #if all(['ghdoc' in globals, hasattr(ghdoc,'Path'), isfile(ghdoc.Path)]):    
    #    join(Grasshopper.Folders.DefaultAssemblyFolder,'GHsDNA')
    #    join(Grasshopper.Folders.AppDataFolder,'Libraries','GHsDNA')
    #    join(os.getenv('APPDATA'),'Grasshopper','Libraries','GHsDNA')
    #    __file__
    #else: 
    #    installation_log_file = r'C:\Users\James\AppData\Roaming\Grasshopper\Libraries\GHsDNA'


#    append_iterable_values_do_not_overwrite = True # TODO: implement this!
#    allocate_misnamed_GH_component_input_names_in_order = False # TODO: implement this!
#    allocate_all_GH_component_input_names_in_order = False # TODO: implement this!
#    modules_subdirectories = [   r'third_party_python_modules'   
#                                ,r'custom_python_modules'
#                                ] 

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
    log_file_suffix = '_GHsDNA'
    log_file = __file__.rpartition('.')[0] + log_file_suffix + '.log'
    #os.getenv('APPDATA'),'Grasshopper','Libraries','GHsDNA','GHsDNA.log')
    logs_subdirectory = r'logs'
    tests_subdirectory = r'tests'
    logger_file_level = 'DEBUG'
    logger_console_level = 'ERROR'
    logger_custom_level = 'ERROR'

    ####################################################################################
    #GDM
    read_overides_Data_from_Usertext = True
    merge_Usertext_subdicts_instead_of_overwriting = True
    use_initial_groups_if_too_many_in_list = True
    use_initial_data_if_too_many_in_list = True
    include_groups_in_gdms = False
    ####################################################################################
    #Shapefiles
    shp_file_shape_type = 'POLYLINEZ'
    read_from_Rhino_if_no_shp_data = False
    cache_iterable_when_writing_to_shp= False
    shp_file_extension = '.shp' # file extensions are actually optional in PyShp, but just to be safe and future proof
    supply_sDNA_file_names = True
    shape_file_to_write_Rhino_data_to_from_GHsDNA = r'C:\Users\James\Documents\Rhino\Grasshopper\GHsDNA_shapefiles\t6.shp' # None means Rhino .3dm filename is used.
    overwrite_shp_file = True
    overwrite_UserText = True
    duplicate_UserText_key_suffix = r'_{}'
    prepped_shp_file_suffix = "_prepped"
    output_shp_file_suffix = "_output"
    duplicate_file_name_suffix = r'_({})' # Needs to contain a replacement field {} that .format can target.  No f strings in Python 2.7 :(
    max_new_files_to_make = 20
    suppress_overwrite_warning = False     
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
    #Plotting results
    sDNA_output_abbrev_to_graph = 'BtEn'
    ####################################################################################
    #Test
    message = 'Solid.  Solid as a rock!'

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

def get_namedtuple_etc_from_class(C, name):
    # type: ( type[any], str) -> namedtuple
    fields = dir(C)
    fields.remove('__doc__')
    fields.remove('__module__')
    factory = namedtuple(name, fields, rename=True)   
    return factory(**{x : getattr(C,x) for x in fields})

default_metas = get_namedtuple_etc_from_class(HardcodedMetas, 'Metas')
default_options = get_namedtuple_etc_from_class(HardcodedOptions, 'Options')
local_metas = get_namedtuple_etc_from_class(HardcodedLocalMetas, 'LocalMetas')

empty_NT = namedtuple('Empty','')(**{})

opts = OrderedDict( metas = default_metas
                   ,options = default_options
                   )                

get_syntax_dict = {} 
input_spec_dict = {}                 

if 'ghdoc' not in globals():
    import scriptcontext as sc
    ghdoc = sc.doc



def output(s, logging_level = "INFO", stream = None, logging_dict = None ):
    #type: (str,...,str,dict) -> None
    #type: (stream) == anything with a write method. e.g. 'file-like object' supporting write() and flush() methods, e.g. WriteableFlushableList
    
    #print(s)


    #if stream == None and ('a' in locals or 'a' in globals()):   # a is attached to a logger StreamHandler now, so if that works 
    #                                                             # this code would double log to it
    #    global a
    #    stream = a

    if hasattr(stream,'write'): #isinstance(stream,WriteableFlushableList):
        stream.write(s)

    if logging_dict == None:
        #print 'logging in globals() == ' + str('logging' in globals())
        if 'logger' in globals():
            logging_dict = dict( DEBUG = logger.debug
                                ,INFO = logger.info
                                ,WARNING = logger.warning
                                ,ERROR = logger.error
                                ,CRITICAL = logger.critical
                                )
        else:
            logging_dict = {}
    if  logging_level in logging_dict:
        logging_dict[logging_level](s)
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

from .custom_python_modules.options_manager import (                     
                                     make_nested_namedtuple     
                                    ,setup_config                             
                                    ,override_namedtuple        
                                    ,override_namedtuple_with_ini_file
)




#
####################################################################################################################
#
#

#if 'logger' in globals() and isinstance(logger, wrapper_logging.logging.Logger): 
#    pass
#else:      

from .custom_python_modules import wrapper_logging

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

if 'logger' not in globals():
    logger = WriteableFlushableList()


from .custom_python_modules.wrapper_pyshp import (get_fields_recs_and_shapes_from_shapefile
                                                 ,get_unique_filename_if_not_overwrite
                                                 ,write_from_iterable_to_shapefile_writer)



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
    # to apply a new project config.ini file, they need to instead specify it in args (by adding a variable called config_file_path to 
    # the GHPython GHsDNA launcher component.
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
        return dict( dump_all_in_default_section = False
                    ,empty_lines_in_values = False
                    ,interpolation = None # For setup_config above
                    ,section_name = key # For override_namedtuple below
                    ,leave_as_strings = False 
                    ,strict = local_opts['metas'].typecheck_opts_namedtuples
                    ,check_types = local_opts['metas'].typecheck_opts_fields
                    ,add_in_new_options_keys = local_opts['metas'].add_in_new_options_keys
                    )

    ################################################################################
    #Primary meta:
    #

    if 'config_file_path' in args_metas: 
        config_file_reader = setup_config(   args_metas['config_file_path'], **kwargs('', local_opts))
    else:
        config_file_reader = None 
    #################################################################################

    local_metas_overrides_list = [external_local_metas, config_file_reader, args_local_metas]
    local_metas = override_namedtuple(  local_metas, local_metas_overrides_list, **kwargs('DEFAULT', local_opts) ) 
    #print('#1.1 local_metas == ' + str(local_metas))

    sub_args_dict = {     'metas' : args_metas
                          ,'options' : args_options
                          ,name : args_tool_options
                    }



    def overrides_list(key):
        # type (str) -> list
        
        retval = [] if local_metas.sync_to_shared_global_opts or not local_metas.read_from_shared_global_opts else [
                  opts.get( key,  {} ).get( sDNA(),  {} )  ] 

        
        ext_opts = external_opts.get( key,  {} )
        if key not in ('options','metas') :
            ext_opts = ext_opts.get( sDNA(),  {} )
        
        retval += [ext_opts, config_file_reader, sub_args_dict.get(key,{})]

        return retval

        

    #overrides_list = lambda key : [external_opts.get(key,{}).get(sDNA(), {}), config_file_reader, sub_args_dict.get(key, {})]
    if local_metas.sync_to_shared_global_opts:
        dict_to_update = opts # the opts in module's global scope, outside this function
        #print('Using global opts '+'DEBUG')
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
            dict_to_update[key][sDNA()] = override_namedtuple(dict_to_update[key][sDNA()]
                                                             ,overrides_list(key)
                                                             ,**kwargs(key, local_opts) 
                                                             )
    return local_metas

####################################################################################################################
# First options options_manager.override (3), user's installation specific options over (4), hardcoded defaults above
#
# Use the above function to load the user's installation wide defaults by using
#  the primary meta from the hardcoded defaults.

if isfile(default_metas.config_file_path):
    #print('Before override: message == '+opts['options'].message)

    override_all_opts(  default_metas._asdict()
    # just to retrieve hardcoded primary meta (installation config file location)
                        ,opts #  mutates opts
                        ,{}       #external_opts
                        ,local_metas 
                        ,empty_NT #external_local_metas
                        ,'')

    #print('After override: message == '+opts['options'].message)
else:
    print('Config.ini not found at '+default_metas.config_file_path)    
#
####################################################################################################################








def make_regex_inverse_of_format_string(pattern):
    # type (str) -> str
    the_specials = '.^$*+?[]|():!#<='
    for c in the_specials:
        pattern = pattern.replace(c,'\\' + c)
    pattern = pattern.replace( '{', r'(?P<' ).replace( '}', r'>.*)' )
    return r'\A' + pattern + r'\Z'



def is_uuid(val):
    try:
        UUID(val)
        return True
    except ValueError:
        return False
#https://stackoverflow.com/questions/19989481/how-to-determine-if-a-string-is-a-valid-v4-uuid



def convert_dictionary_to_data_tree(nested_dict):
    # type(dict) -> DataTree
    import ghpythonlib.treehelpers as th
        
    User_Text_Keys = [[key for key in group_dict] for group_dict in nested_dict]
    User_Text_Values = [[val for val in group_dict.values()] for group_dict in nested_dict]
    
    Data =  th.list_to_tree([[User_Text_Keys, User_Text_Values]])
    Geometry = nested_dict.keys()  # Multi-polyline-groups aren't unpacked.
    return Data, Geometry
    #layerTree = []


def override_gdm_with_gdm(lesser, override, opts):  
    # overwrite ?
    # call update on the sub dicts?:
    if opts['options'].merge_Usertext_subdicts_instead_of_overwriting:
        for key in override:
            if key in lesser:
                lesser[key].update(override[key])
            else:
                lesser[key] = override[key]
    else:
        lesser.update(**override)
    return lesser

def make_obj_key(x, *args):
    # type(str) -> str
    return x.ToString()  # Group names do also 
                         # have a ToString() method, even 
                         # though they're already strings

def get_obj_keys(obj):
    # type(str) -> list
    import rhinoscriptsyntax as rs
    return rs.GetUserText(obj)

def get_obj_val(obj, key):
    # type(str, str) -> str
    import rhinoscriptsyntax as rs
    return rs.GetUserText(obj, key)

def write_obj_val(obj, key, val):
    # type(str, str) -> str
    import rhinoscriptsyntax as rs
    return rs.SetUserText(obj, key, val, False)

def get_val_list(val_getter = get_obj_val):
    # type(function) -> function
    def f(obj, keys):
        # type(str, list) -> list

        return [val_getter(obj, key) for key in keys]
    return f

def get_key_val_tuples( keys_getter = get_obj_keys
                          ,val_getter = get_obj_val):
    # type(function) -> function
    def f(obj):
        # type(str, list) -> list
        keys = keys_getter(obj)
        return ( (key, val_getter(obj, key)) for key in keys)
    return f

def is_group(x):
    #type( str ) -> boolean
    import rhinoscriptsyntax as rs
    return rs.IsGroup(x)   

def get_all_groups():
    #type( None ) -> list
    import rhinoscriptsyntax as rs
    return rs.GroupNames()

def get_members_of_a_group(group):
    #type(str) -> list
    import rhinoscriptsyntax as rs
    return rs.ObjectsByGroup(group)

def make_new_group(group_name = None):
    #type(str) -> str
    import rhinoscriptsyntax as rs
    return rs.AddGroup(group_name)

def add_objects_to_group(objs, group_name):
    #type(list, str) -> int
    import rhinoscriptsyntax as rs
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

def get_points_list_from_Rhino_obj(x, shp_type='POLYLINEZ'):
    #type(str, dict) -> list
    import rhinoscriptsyntax as rs
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
    import rhinoscriptsyntax as rs
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
    import rhinoscriptsyntax as rs
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

def get_objs_and_key_val_tuples( 
                              options = opts['options']
                             ,all_objs_getter = get_all_shp_type_Rhino_objects
                             ,group_getter = get_all_groups
                             ,group_objs_getter = get_members_of_a_group
                             ,key_val_tuples_getter = get_key_val_tuples()
                             ,obj_type_checker = check_is_specified_obj_type
                             ,shp_type = 'POLYLINEZ'
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
                    groups_key_val_tuples = [key_val_tuples_getter(obj) 
                                                    for obj in objs]
                    yield group, groups_key_val_tuples

        objs = all_objs_getter(shp_type)
        for obj in objs:
            if ((not options.include_groups_in_gdms) or 
                 obj not in objs_in_any_group):
                key_val_tuples = key_val_tuples_getter(obj)
                yield obj, key_val_tuples
        return  # For the avoidance of doubt

    return generator()


def make_gdm(main_iterable
            ,object_hasher = make_obj_key ): 
    #type(namedtuple, function, function)-> dict   

    gdm = OrderedDict(  ( ( object_hasher(obj, key_val_tuples)
                            ,OrderedDict(  key_val_tuples) )   
                            for obj, key_val_tuples in main_iterable
                            ) 
                        )

    return gdm
    

def convert_Data_tree_and_Geom_list_to_dictionary(Data, Geom, options):
    # type (type[any], list, dict)-> dict
    import ghpythonlib.treehelpers as th
    import rhinoscriptsyntax as rs 

    if (not isinstance(Geom, list) or
       any( not rs.IsObject(x) and not is_group(x) for x in Geom) ):
        return {}
    elif not isinstance(Data, th.Tree): 
        return {obj : {} for obj in Geom}
    else:
        l = th.tree_to_list(Data)

        if len(l) == 2:
            [key_lists, val_lists] = l
        elif len(l) > 2:
            output('Data tree has more than two branches.  '
                    'Using first two for keys and vals.  ', 'WARNING')
            key_lists = l[0]
            val_lists = l[1]
        else:
            raise ValueError(output('Data tree has less than two branches '
                                    +' (e.g. no keys?).  ', 'ERROR'))
            # raise Error won't re-initialise the component.

        


        component_inputs_gen_exp = (  (obj, zip(key_list, val_list)) 
                                        for obj, key_list, val_list in 
                                        izip(Geom, key_lists, val_lists)  )

        geom_data_map = make_gdm(component_inputs_gen_exp  
                                ,make_obj_key
                                )

        #geom_data_map = make_gdm( izip(Geom, imap( izip, key_lists, val_lists)), make_obj_key)

        return geom_data_map


def read_objects_groups_and_Usertext_from_Rhino(f_name, gdm, opts_at_call):
    #type(type[any], str, dict, dict) -> int, str, dict, dict
    import Rhino
    import scriptcontext as sc
    import rhinoscriptsyntax as rs

    options = opts_at_call['options']

    #if 'ghdoc' not in globals():
    #    global ghdoc
    #    ghdoc = sc.doc  

    sc.doc = Rhino.RhinoDoc.ActiveDoc # type: ignore 
    # ActiveDoc may change on Macs - TODO: only call once or accept argument
    output('Starting read_objects_groups_and_Usertext_from_Rhino','DEBUG')
    
    sc.doc = Rhino.RhinoDoc.ActiveDoc
    rhino_groups_and_objects = make_gdm(get_objs_and_key_val_tuples(options))
    sc.doc = ghdoc

    report('First objects read: \n' + '\n'.join(rhino_groups_and_objects.keys()[:3]))
    report('....Last objects read: \n' + '\n'.join(rhino_groups_and_objects.keys()[-3:]))


    if opts_at_call['options'].read_overides_Data_from_Usertext:
        read_Usertext_as_tuples = get_key_val_tuples()
        for obj in gdm:
            gdm[obj].update(read_Usertext_as_tuples(obj))

    override_gdm_with_gdm(rhino_groups_and_objects, gdm, opts_at_call)

    return 0, f_name, rhino_groups_and_objects, None


def write_objects_and_data_to_shapefile(f_name, geom_data_map, opts_at_call):
    #type(type[any], str, dict, dict) -> int, str, dict, dict
    
    import rhinoscriptsyntax as rs
    import Rhino
    import scriptcontext as sc
    
    options = opts_at_call['options']

    shp_type = options.shp_file_shape_type            
    
    if geom_data_map == {} and options.read_from_Rhino_if_no_shp_data:
        output('No geometry to write to shapefile.  Reading geometry from Rhino...  ','WARNING')
        retcode, ret_f_name, geom_data_map = (
              read_objects_groups_and_Usertext_from_Rhino(   f_name
                                                            ,{}
                                                            ,opts_at_call
                                                          )
        )
        output('Read geometry from Rhino.  Writing to Shapefile... ','INFO')


    def pattern_match_key_names(x):
        #type: (str)-> str / None
        format_string = options.rhino_user_text_key_format_str_to_read
        pattern = make_regex_inverse_of_format_string( format_string )
        m = match(pattern, x) 
        return m   #           if m else None #, m.group('fieldtype'), 
                                              # m.group('size') if m else None
                                              # can get 
                                              # (literal_text, field_name, 
                                              #                  f_spec, conv) 
                                              # from iterating over
                                              # string.Formatter.parse(
                                              #                 format_string)

    def get_list_of_lists_from_tuple(tupl):
        obj = tupl[0]
        report_value(obj)

        if check_is_specified_obj_type(obj, shp_type):
            return [get_points_list_from_Rhino_obj(obj, shp_type)]
        elif is_group(obj):
            return [get_points_list_from_Rhino_obj(y, shp_type) 
                     for y in get_members_of_a_group(obj)
                     if check_is_specified_obj_type(y, shp_type)]
        else:
            return None

    def shape_IDer(tupl):
        return tupl[0].ToString() # uuid

    def find_keys(tupl):
        return tupl[1].keys() #rs.GetUserText(x,None)

    def get_data_item(tupl, key):
        return tupl[1][key]

    if f_name == None:  
        try:
            f_name = options.Rhino_doc_path.rpartition('.')[0] + options.shp_file_extension
                        # file extensions are actually optional in PyShp, 
                        # but just to be safe and future proof we remove
                        # '.3dm'                                        
        except:
            f_name = options.shape_file_to_write_Rhino_data_to_from_GHsDNA

    shp_type = options.shp_file_shape_type            
    #report('Type of gdm == '+ type(geom_data_map).__name__)                         
    #report('Size of gdm == ' + str(len(geom_data_map)))
    #report('Gdm keys == ' + ' '.join( map(lambda x : x[:5],geom_data_map.keys() )) )
    #report('Gdm.values == ' + ' '.join(map(str,geom_data_map.values())))
    sc.doc = Rhino.RhinoDoc.ActiveDoc
    (retcode, filename, fields, user_data, geometry_data_iterable) = ( 
                         write_from_iterable_to_shapefile_writer(
                                             geom_data_map.items() #my_iter 
                                            ,f_name #shp_file 
                                            ,get_list_of_lists_from_tuple # shape_mangler, e.g. start_and_end_points
                                            ,shape_IDer
                                            ,find_keys # key_finder
                                            ,pattern_match_key_names #key_matcher
                                            ,get_data_item #value_demangler e.g. rs.GetUserText
                                            ,shp_type #"POLYLINEZ" #shape
                                            ,options #options
                                            ,None # field names
                         )
    ) 
    sc.doc = ghdoc
    return retcode, filename, geom_data_map, None





def create_new_groups_layer_from_points_list(
                     options = opts['options']
                    ,make_new_group = make_new_group
                    ,add_objects_to_group = add_objects_to_group
                    ,Rhino_obj_adder_Shp_file_shape_map = Rhino_obj_adder_Shp_file_shape_map
                    ):
    import rhinoscriptsyntax as rs
    rhino_obj_maker = getattr(rs, Rhino_obj_adder_Shp_file_shape_map[options.shp_file_shape_type])

    def g(obj, rec):
        objs_list = []
        
        for points_list in obj:
            report_value(points_list)
            objs_list += [rhino_obj_maker(points_list).ToString() ] 
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
    import rhinoscriptsyntax as rs 

    def f(obj, rec):
        if is_uuid(obj) and rs.IsObject(obj):
            return make_obj_key(obj)
        if hasattr(rec, 'as_dict'):
            d = rec.as_dict()
            if options.uuid_shp_file_field_name in d:
                obj_ID = d[options.uuid_shp_file_field_name]     
                report_value(obj_ID)
                # For future use.  Not possible until sDNA round trips through
                # Userdata into the output .shp file, including our uuid
                if rs.IsObject(obj_ID) or is_group(obj_ID):
                    return obj_ID
        g = create_new_groups_layer_from_points_list(options)
        return g(obj, rec)
    return f



def read_shapes_and_data_from_shapefile( f_name
                                        ,geom_data_map 
                                        ,opts_at_call
                                        ):
    #type(type[any], str, dict, dict) -> int, str, dict, dict
    import rhinoscriptsyntax as rs
    import Rhino
    import scriptcontext as sc
    options = opts_at_call['options']

    ( fields
     ,recs
     ,shapes ) = get_fields_recs_and_shapes_from_shapefile( f_name )

    if not recs or len(recs)==0:
         output('No data read from Shapefile ' + f_name + ' ','ERROR')
         return 9, f_name, geom_data_map, None

    field_names = [ x[0] for x in fields ]

    report('options.uuid_shp_file_field_name in field_names == ' + str(options.uuid_shp_file_field_name in field_names))
    report_value(field_names)

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
            report_value(shapes_to_output)    


    shp_file_gen_exp  = izip(shapes_to_output, (rec.as_dict().items() for rec in recs))
    
    #(  (shape, rec) for (shape, rec) in 
    #                                       izip(shapes_to_output, recs)  )              
    sc.doc = Rhino.RhinoDoc.ActiveDoc
    gdm = make_gdm(shp_file_gen_exp, obj_key_maker)
    sc.doc = ghdoc

    override_gdm_with_gdm(gdm, geom_data_map, opts_at_call)   

    if options.delete_shapefile_after_reading and isfile(f_name): # TODO: Fix, currently Win32 error
        os.remove(f_name)


    return 0, f_name, gdm, None



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



def write_data_to_Usertext(  f_name     #Bake_Geom_and_Data
                            ,geom_data_map  # nested dict
                            ,opts_at_call
                            ):
    #type(type[any], str, dict, dict) -> int, str, dict, dict

    import Rhino
    import scriptcontext as sc
    import rhinoscriptsyntax as rs

    options = opts_at_call['options']
    date_time_of_run = asctime()

    def write_dict_to_UserText_on_obj(d, rhino_obj):
        if not rs.IsObject(rhino_obj) or not isinstance(d, dict):
            return

        existing_keys = get_obj_keys(rhino_obj)
        
        if options.uuid_shp_file_field_name in d:
            obj = d.pop( options.uuid_shp_file_field_name )
        
        for key in d:

            s = options.sDNA_output_user_text_key_format_str_to_read
            UserText_key_name = s.format(name = key, datetime = date_time_of_run)
            
            if not options.overwrite_UserText:

                for i in range(0, options.max_new_UserText_keys_to_make):
                    tmp = UserText_key_name + options.duplicate_UserText_key_suffix.format(i)
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

    sc.doc = Rhino.RhinoDoc.ActiveDoc
    for key, val in geom_data_map.items():
        if is_group(key):
            group_members = get_members_of_a_group(key)
        else:
            group_members = [key]
        for member in group_members:
            write_dict_to_UserText_on_obj(val, member)
    sc.doc = ghdoc


    return 0, f_name, geom_data_map, None
    

def plot_data_on_objects(f_name, geom_data_map, opts_at_call):
    #type(type[any], str, dict, dict) -> int, str, dict, dict

    import Rhino
    import scriptcontext as sc
    import rhinoscriptsyntax as rs

    options = opts_at_call['options']

    field = options.sDNA_output_abbrev_to_graph

    keys = (geom_data_map.viewkeys() 
                    if sys.version_info.major < 3 else geom_data_map.keys())

    vals = (geom_data_map.viewvalues() 
                    if sys.version_info.major < 3 else geom_data_map.values())

    output ("Plotting field == " + field,'INFO')
    data_points = [ d[field] for d in vals ]
    data_max = max(data_points)
    data_min = min(data_points)
    rgb_max = (155, 0, 0) #990000
    rgb_min = (0, 0, 125) #3333cc
    rgb_mid = (0, 155, 0) # guessed


    def map_f_to_tuples(f,x,x_min,x_max,tuples_min, tuples_max): # (x,x_min,x_max,triple_min = rgb_min, triple_max = rgb_max)
        return [f(x,x_min,x_max,a, b) for (a, b) in zip(tuples_min, tuples_max)]

    def interpolate(x, x_min, x_max, y_min, y_max):
        return y_min + ( (y_max - y_min) * (x - x_min) / (x_max - x_min) )

    def map_f_to_three_tuples(f,x,x_min,x_med,x_max,tuple_min, tuple_med, tuple_max): # (x,x_min,x_max,triple_min = rgb_min, triple_max = rgb_max)
        return [f(x, x_min, x_med, x_max, a, b, c) for (a, b, c) in zip(tuple_min, tuple_med, tuple_max)]

    def three_point_quadratic_spline(x, x_min, x_mid, x_max, y_min, y_mid, y_max):
        z = 2
        z =  y_min*((x - x_max)*(x - x_mid)/((x_min - x_max)*(x_min - x_mid)))
        z += y_mid*((x - x_max)*(x - x_min)/((x_mid - x_max)*(x_mid - x_min)))
        z += y_max*((x - x_mid)*(x - x_min)/((x_max - x_mid)*(x_max - x_min)))
        return max(0, min( z, 255))

    def change_line_thickness(obj, width, rel_or_abs = False):  #The default value in Rhino for wireframes is zero so rel_or_abs==True will not be effective if the width has not already been increased.
        x = rs.coercerhinoobject(obj, True, True)
        x.Attributes.PlotWeightSource = Rhino.DocObjects.ObjectPlotWeightSource.PlotWeightFromObject
        if rel_or_abs:
            width = width * x.Attributes.PlotWeight
        x.Attributes.PlotWeight = width
        x.CommitChanges()


    new_width = 4
    
    sc.doc = Rhino.RhinoDoc.ActiveDoc

    for rhino_obj, d in geom_data_map.items():
        #change_line_thickness(rhino_obj, new_width)
        #rs.ObjectColor(rhino_obj, map_f_to_tuples(interpolate, record[sDNA_output_to_plot_index], data_min, data_max, rgb_min, rgb_max))
        rs.ObjectColor(rhino_obj, map_f_to_three_tuples( three_point_quadratic_spline
                                                        ,d[field]
                                                        ,data_min
                                                        ,0.5*(data_min + data_max)
                                                        ,data_max
                                                        ,rgb_min
                                                        ,rgb_mid
                                                        ,rgb_max
                                                        )
                        )

    rs.ObjectColorSource(keys, 1)  # 1 => colour from object
    rs.ObjectPrintColorSource(keys, 2)  # 2 => colour from object
    rs.ObjectPrintWidthSource(keys, 1)  # 1 => print width from object
    rs.ObjectPrintWidth(keys, new_width) # width in mm
    #rs._commanPrint Display (Model Viewports) ( State=On  Color=Display  Thickness=15 ): Thickness=20
    rs.Command('_PrintDisplay _State=_On Color=Display Thickness=8 ')
    #rs.Command('Print Display (Model Viewports) ( State=On  Color=Display  Thickness=8 )')

    sc.doc.Views.Redraw()
    sc.doc = ghdoc# type: ignore

    return 0, f_name, geom_data_map, None
                  

def list_contains(check_list, name, name_map):
    # type( MyComponent, list(str), str, dict(str, str) ) -> bool

    return name in check_list or (name in name_map and name_map[name] in check_list)

def no_name_clashes(name_map, list_of_names_lists):
    #type( MyComponent, dict(str, str), list(str) ) -> bool

    num_names = sum(len(names_list) for names_list in list_of_names_lists)
    super_set = set(name for names_list in list_of_names_lists for name in names_list)
    # Check no duplicated name entries in list_of_names_lists.
    if set(['options', 'metas']) & super_set:
        return False  # Clashes with internal reserved names.  Still best avoided even though tool options
                      # are now a level below (under the sDNA version key)
    return num_names == len(super_set) and not any([x == name_map[x] for x in name_map])  # No trivial cycles




def cache_syntax_and_UISpec(nick_name, tool_name, local_opts):    
    # type(str, dict) -> str, dict, function

    sDNA, UISpec = local_opts['metas'].sDNA, local_opts['options'].UISpec
    #
    global get_syntax_dict
    # 
    #
    def update_or_init(cache, defaults, name):
        #type(dict, dict / function, str) -> None
        if name not in cache:
            cache[name] =  {}
        if sDNA not in cache[name]:
            cache[name][sDNA] = ( make_nested_namedtuple( defaults,  name ) 
                        if isinstance(defaults, dict) else defaults  )
        else:
            output('Name : ' + name + ' already in cache ', 'INFO')
            #if isinstance(defaults, dict) and hasattr(cache[name][sDNA]
            #                                            ,'_asdict'): #NT
            #    defaults.update(cache[name][sDNA]._asdict())


    if hasattr(UISpec, tool_name):
        sDNA_tool_instance = getattr( UISpec,  tool_name )()

        get_syntax = sDNA_tool_instance.getSyntax     
        # not called until component executes in RunScript
        update_or_init( get_syntax_dict,  get_syntax,  tool_name )
        # Global get_syntax_dict intentional
        input_spec = sDNA_tool_instance.getInputSpec()
        defaults_dict = { varname : default for (    varname
                                                    ,displayname
                                                    ,datatype
                                                    ,filtr
                                                    ,default
                                                    ,required
                                                ) in input_spec  }
        update_or_init( local_opts,  defaults_dict,  nick_name )
        # Tool options are stored per nick_name, which may equal tool_name
    else:
        update_or_init( local_opts,  {},  nick_name )
        update_or_init( get_syntax_dict,  {},  tool_name )
    return 

class FakeProgress():
    setInfo = output
    def setPercentage(self,*args):
        pass

tools_dict=dict( read_objects_groups_and_Usertext_from_Rhino = [read_objects_groups_and_Usertext_from_Rhino]
                ,write_objects_and_data_to_shapefile = [write_objects_and_data_to_shapefile]
                ,read_shapes_and_data_from_shapefile = [read_shapes_and_data_from_shapefile]
                ,write_data_to_Usertext = [write_data_to_Usertext]
                ,plot_data_on_objects = [plot_data_on_objects] # Needed in iterable wrappers
                )

support_component_names = list(tools_dict.keys()) # In Python 3, .keys() and 
                                                  # .values() are dict views
                                                  # not lists

special_names =           [  'sDNA_general'
                            ]
                            
def component_names_factory(name_map): # name_map is unknown in this module so 
                                       # create closure. Call it from outside.
    def return_component_names(f_name, gdm, local_opts):
        UISpec = local_opts['options'].UISpec
        
        sDNA_tool_names = [Tool.__name__ for Tool in UISpec.get_tools()]
        names_lists = [special_names, support_component_names, sDNA_tool_names]
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
    
       
        valid_name_map_vals = {key : val in names_list + name_map.keys() or (isinstance(val, list) 
                                and all(name in names_list + name_map.keys() for name in val)) for key, val in name_map.items()}
        # TODO.  Lowest priority: Check there are no non-trivial cycles.  this is only devtool validation code - 
        #        not likely a user will expect
        #        correct results if they alter name_map to include a non-trivial cycle.
        if not all(valid_name_map_vals.values()):
            vals_in_name_map_with_no_Tools = [key for (key, val) in valid_name_map_vals.items() if not val]
            output('Invalid name_map: ' + ' '.join(vals_in_name_map_with_no_Tools) + 
                    '.  Adjust name_map to point to known functions or lists thereof in tools_dict, or vice-versa.  ','CRITICAL')
        else:
            output('Name_map validated successfully.  ','INFO')
        assert all(valid_name_map_vals.values())
        #return special_names + support_component_names + sDNA_tool_names, None, None, None, self.a 
        return 0, None, {}, names_list


    return [return_component_names]


def get_specific_tool(tool_name, nick_name, local_opts):
    # type(str) -> function
    # global get_syntax_dict  # access shared global cache via parent module namespace.  Not mutated here (done already in cache_syntax_and_UISpec).
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

            dot_shp = options.shp_file_extension

            input_file = tool_opts[sDNA].input
            if (not isinstance(input_file, str)) or not isfile(input_file): 
                if (isinstance(f_name, str) and isfile(f_name)
                    and f_name.rpartition('.')[2]==dot_shp[1:]):
                    input_file = f_name
                else:
                    default_file_name = (options.Rhino_doc_path.rpartition('.')[0] 
                                                                    + dot_shp)
                    if (options.supply_sDNA_file_names and 
                                              isfile(default_file_name) ): 
                        input_file = default_file_name
                    else:
                        pass # e.g. could call write_from_iterable_to_shapefile_writer
                tool_opts[sDNA] = tool_opts[sDNA]._replace(input = input_file)


            output_file = tool_opts[sDNA].output
            if output_file == '':
                output_suffix =  options.output_shp_file_suffix
                if tool_name == 'sDNAPrepare':
                    output_suffix = options.prepped_shp_file_suffix   
                output_file = input_file.rpartition('.')[0] + output_suffix + dot_shp

            output_file = get_unique_filename_if_not_overwrite(output_file, options)
            tool_opts[sDNA] = tool_opts[sDNA]._replace(output = output_file)

            

            syntax = get_syntax_dict[tool_name][sDNA]( tool_opts[sDNA]._asdict() )   
                                                      #opts[nick_name] was initialised to defaults in 
                                                      # in cache_syntax_and_UISpec

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
            
            return_code = call(command)   
            
            



            #return_code = run.runsdnacommand(    syntax
            #                                    ,sdnapath = dirname(UISpec.__file__)  #opts['options'].sDNA_UISpec_path
            #                                    ,progress = FakeProgress()
            #                                    ,pythonexe = options.python_exe
            #                                    ,pythonpath = None)   # TODO:  Work out if this is important or not! 
                                                                    # os.environ["PYTHONPATH"] not found in Iron Python
            # To allow auto reading the shapefile afterwards, the returned Data == None == None to end
            # the input GDM's round trip, in favour of Data and Geometry read from the sDNA analysis just now completed.
            return return_code, tool_opts[sDNA].output, gdm, None
        return [run_sDNA_wrapper]
    else:
        return [None]

def run_tools(tools, f_name, gdm, opts_at_call):
    #type(list, str, dict, dict)-> int, str, dict, WriteableFlushableList
    a = WriteableFlushableList()
    for tool in tools:
        if tool:
            report_value(tool)
            report_value(f_name)
            report_value(gdm)

            returncode, f_name, gdm, tmp_a = tool( f_name 
                                                  ,gdm
                                                  ,opts_at_call 
                                                 )
            report('Tool name == ' + tool.func_name + ' return code == ' + str(returncode))
            a.write(tmp_a)
            #if returncode != 0:
            #    break
        else:
            raise TypeError(output('Bad tool == ' + str(tool), 'ERROR'))
    return returncode, f_name, gdm, a

def tool_factory(nick_name, name_map, local_opts):  
    #type( str, dict, dict ) -> list

    #sDNA, UISpec, run = local_opts['options'].sDNA, local_opts['options'].UISpec, local_opts['options'].run

    #global tools_dict # mutable - access through normal parent module namespace
    sDNA = local_opts['metas'].sDNA
    global tools_dict
    # A special component that takes its nickname from the parameters provided,
    # only working out which tools to run at run time.  
    def tool_factory_wrapper(f_name, gdm, opts_at_call):
        tools = tool_factory( opts_at_call['options'].tool_name
                             ,name_map  
                             ,opts_at_call )
        return run_tools(tools, f_name, gdm, opts_at_call)

 
    if isinstance(nick_name, Hashable):
        if nick_name not in tools_dict or sDNA not in opts.get(nick_name, {}):
            map_result = name_map.get(nick_name, nick_name)  # in case nick_name == tool_name
            if not isinstance(map_result, str):
                output('Processing list of tools found for '
                       + nick_name, 'DEBUG')
                tools =[]
                for mapped_name in map_result:
                    tools += tool_factory( mapped_name,  name_map,  local_opts ) 
                tools_dict[nick_name] = tools 
            else:
                mapped_name = map_result
                cache_syntax_and_UISpec(nick_name, mapped_name, local_opts) 
                output(nick_name + ' maps to ' + mapped_name,'DEBUG')
                if mapped_name in support_component_names:
                    tools_dict[nick_name] = tools_dict[mapped_name]
                    output(mapped_name + ' in support_component_names','DEBUG')
                elif nick_name == 'Python':   # Validates name_map and used in dev
                                            # tool to auto name components
                    tools_dict[nick_name] = component_names_factory(name_map) 
                    output(nick_name + ' is "Python"','DEBUG')

                    # Needs to be here because glbal scoep doens't know what name_map from
                    # the launcher is
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

loc = tool_factory # just to make the syntax highlighting above bright





###############################################################################
#Main script only process
#
from os.path import isdir, isfile, sep, normpath, join, split
if      '__file__' in dir(__builtins__)  and  __name__ in __file__ and '__main__' not in __file__ and '<module>' not in __file__:                     
    # Assert:  We're in a module!
    pass
else:
    pass


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

if sys.version < '3.3':
    from collections import Hashable
else:
    from collections.abc import Hashable



def get_stem_and_folder(path):
    if isfile(path):
        path=dirname(path)
    return split(path)

class HardcodedMetas(): 
    config_file_path = r'config.ini'
    add_in_new_options_keys = False
    allow_components_to_change_type = False
    typecheck_opts_namedtuples = True
    typecheck_opts_fields = True
    sDNA = ('sDNAUISpec','runsdnacommand')
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
                                            # linked from sDNA manual https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/installation_usage.html
    
    ####################################################################################
    #Logging    
    log_file_suffix = '_GHsDNA'
    log_file = __file__.rpartition('.')[0] + log_file_suffix + '.log'
    #os.getenv('APPDATA'),'Grasshopper','Libraries','GHsDNA','GHsDNA.log')
    logs_subdirectory = r'logs'
    tests_subdirectory = r'tests'
    logger_file_level = 'DEBUG'
    logger_console_level = 'DEBUG'
    logger_custom_level = 'WARNING'

    ####################################################################################
    #GDM
    read_overides_Data_from_Usertext = True
    merge_Usertext_subdicts_instead_of_overwriting = True
    use_initial_links_if_too_many_in_list = True
    use_initial_data_if_too_many_in_list = True
    ####################################################################################
    #Shapefiles
    shp_file_shape_type = 'POLYLINEZ'
    read_from_Rhino_if_no_shp_data = False
    cache_iterable_to_shp = False
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
    delete_shapefile_after_reading = True
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
    create_new_links_layer_from_shapefile = True
    max_new_UserText_keys_to_make = 20
    #
    #
    rhino_user_text_key_format_str_to_read = 'sDNA input name={name} type={fieldtype} size={size}'  #30,000 characters tested!
    sDNA_output_user_text_key_format_str_to_read = 'sDNA output={name} run time={datetime}'  #30,000 characters tested!
    ####################################################################################
    #Plotting results
    sDNA_output_abbrev_to_graph = 'BtE'
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

sDNA_output_abbrevs = ['AngD', 'BtA', 'BtC', 'BtE', 'BtH', 'Conn', 'DivA', 'DivC', 'DivE', 'DivH', 'HMb', 'HMf', 'HullA', 'HullB', 'HullP', 'HullR' 
                       ,'HullSI', 'Jnc', 'LAC', 'LBear', 'LConn', 'Len', 'Lfrac', 'LLen', 'Lnk', 'LSin', 'MAD', 'MCD', 'MCF', 'MED', 'MGLA', 'MGLC'
                       ,'MGLE', 'MGLH', 'MHD', 'NQPDA', 'NQPDC', 'NQPDE', 'NQPDH', 'SAD', 'SCD', 'SCF', 'SED', 'SGLA', 'SGLC', 'SGLE', 'SGLH', 'SHD' 
                       ,'TPBtA', 'TPBtC', 'TPBtE', 'TPBtH', 'TPDA', 'TPDC', 'TPDE', 'TPDH', 'Wl', 'Wp', 'Wt']

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

from .custom_python_modules.options_manager import (                     
                                     make_nested_namedtuple     
                                    ,setup_config                             
                                    ,override_namedtuple        
                                    ,override_namedtuple_with_ini_file
)



####################################################################################################################
# First options options_manager.override (3), user's installation specific options over (4), hardcoded defaults above
#
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

config_abs_path = join( dirname(__file__), default_metas.config_file_path)  
                      #abspath(metas.config_file_path)
if isfile( config_abs_path ):
    output('Loading config file from ' + config_abs_path, 'DEBUG')
    config = setup_config(   config_abs_path, **kwargs('', opts))

    opts['metas'] = override_namedtuple_with_ini_file( default_metas
                                                      ,config_abs_path
                                                      ,**kwargs('metas', opts)
    )
    opts['options'] = override_namedtuple_with_ini_file( 
                                                    default_options
                                                    ,config_abs_path
                                                    ,**kwargs('options', opts)
    )
else:    
    output('No Installation wide config file found at ' 
           + config_abs_path 
           + ' .  Using hardcoded default options.  ', 'WARNING'
           )
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
    def write(self,s):
    #type: ( str) -> None
    # https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code
    #
        if isinstance(s,str):
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

#def function_imported_by_GHsDNA_launcher(f_name, Geom, Data, opts):
    #type(bool, str, Rhino Geometry, datatree, tuple(namedtuple,namedtuple), *dict) -> bool, str, Rhino_Geom, datatree, str
# return ran_OK, output_file_path, Geometry, Data, a

#def override_namedtuple( user_args_dict
#                        ,project_ini_file_path
#                        ,old_nt_or_dict
#                        ,installation_nt
#                        ,add_in_new_options_keys=True
#                        ,check_types = True 
#                        ,strict = False
#                        ,NTClass = None
#                        ):
#type() -> namedtuple




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
        if arg_val != None:  # Unconnected input variables in a Grasshopper component are None.  
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




    #test_opts = opts
    #if opts != None and (len(opts)==1 and isinstance(opts,list)):    # Check for list input mode on the GHPython Component input variable
    #    test_opts = opts[0]

    #if isinstance(opts,tuple):
    #    if len(opts)==3:
    #        test_metas, test_options, test_tool_options = test_opts
    #    elif len(opts)==2:
    #        test_options, test_tool_options = test_opts        
    #    elif len(opts)==1:
    #        test_tool_options = test_opts
    #    
    #new_metas = metas           # From Global scope in this module. 
    #new_options = options       # Installation options and metas have already overridden the Hardcoded ones above.
    #if test_opts != None and len(test_opts) == 2 and isinstance(test_opts,tuple):
    #   test_metas, test_options = test_opts
    #elif test_opts != None and len(test_opts) == 1 and isinstance(test_opts,namedtuple)
    #
    #   if (test_metas.__class__.__name__ == 'Metas' and 
    #       test_options.__class__.__name__ == 'Options'):
    #
    #metas = override_namedtuple( args_metas 
    #                            ,args_metas.get(config_file_path,'')
    #                            ,test_metas 
    #                            ,metas
    #                            ,add_in_new_options_keys = False 
    #                            ,check_types = True 
    #                            ,strict = True
    #                            ,NTClass = metas_factory)
    #
    #options = override_namedtuple(   args_options 
    #                                ,args_metas.get(config_file_path,'') 
    #                                ,test_options 
    #                                ,options
    #                                ,add_in_new_options_keys = False 
    #                                ,check_types = True 
    #                                ,strict = True
    #                                ,NTClass = options_factory)
    #
    #tool_options = override_namedtuple(  args_tool_options 
    #                                    ,args_metas.get(config_file_path,'') 
    #                                    ,test_tool_options 
    #                                    ,tool_options
    #                                    ,add_in_new_options_keys = False 
    #                                    ,check_types = True 
    #                                    ,strict = True
    #                                    ,NTClass = options_factory)                                
    
    ############################################################
    #
    #Primary meta:
    #

    if 'config_file_path' in args_metas: 
        config_file_reader = setup_config(   args_metas['config_file_path'], **kwargs('', local_opts))
    else:
        config_file_reader = None 
    #print('1.09 ')

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
        
        retval += [ext_opts, config_file_reader, sub_args_dict[key]]

        return retval

        

    #overrides_list = lambda key : [external_opts.get(key,{}).get(sDNA(), {}), config_file_reader, sub_args_dict.get(key, {})]
    if local_metas.sync_to_shared_global_opts:
        dict_to_update = opts # the opts in module's global scope, outside this function
    else:
        dict_to_update = local_opts
        #if local_metas.read_from_shared_global_opts:
          #  overrides = lambda key : [opts.get(key,{}).get(sDNA(), {})] + overrides(key)

    def get_overidden_options_NT(lesser_NT, overrides, key, opts_NT):

        tmp_NT = override_namedtuple( lesser_NT,  overrides(key),  **kwargs(key, local_opts) )  
        tmp_opts_NT = opts_NT
        if local_metas.write_to_shared_global_opts and not local_metas.sync_to_shared_global_opts:
            tmp_opts_NT = override_namedtuple( opts_NT, tmp_NT,  **kwargs(key, local_opts) ) 

        return tmp_NT, tmp_opts_NT

    for key in dict_to_update:
        if key in ('options','metas'):
            dict_to_update[ key ],  opts[ key ] = (
                        get_overidden_options_NT( dict_to_update[ key ]
                                                 ,overrides_list
                                                 ,key
                                                 ,opts[ key ] 
                        )
            )            
        else:
            dict_to_update[ key ][ sDNA() ],  opts[ key ][ sDNA() ] = (
                        get_overidden_options_NT( dict_to_update[ key ][ sDNA() ]
                                                 ,overrides_list
                                                 ,key
                                                 ,opts[ key ][ sDNA() ] 
                        )
            )

        #if key not in ('options','metas') and sDNA in val:
        #   dict_to_update[ key ][ sDNA ] = get_overidden_options_NT(dict_to_update[ key ][ sDNA ], overrides_list(key))
        #else:
        #   dict_to_update[ key ] = get_overidden_options_NT(dict_to_update[ key ], overrides_list(key))
        #
        #if local_metas.write_to_shared_global_opts and not local_metas.sync_to_shared_global_opts:
        #    if key not in ('options','metas') and sDNA in val:
        #        opts[ key ][ sDNA ] = get_overidden_options_NT(opts[ key ][ sDNA ], dict_to_update[ key ][ sDNA ] )
        #    else:
        #        opts[ key ] = get_overidden_options_NT(opts[ key ], dict_to_update[ key ])
            #opts[key].get( sDNA,  opts[key] ) = override_namedtuple( opts[key].get( sDNA,  opts[key] )
            #                                                                         ,dict_to_update[key]
            #                                                                         ,**kwargs 
            #                                                                        )


                                                

    return local_metas

# Load primary meta.
override_all_opts(  dict(config_file_path = default_metas.config_file_path) 
# just to retrieve hardcoded primary meta (installation config file location)
                    ,opts #  mutates opts
                    ,{}       #external_opts
                    ,local_metas 
                    ,empty_NT #external_local_metas
                    ,'')







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
    names = [var_name for var_name, var_val in c if var_val is x]
    # https://stackoverflow.com/questions/18425225/getting-the-name-of-a-variable-as-a-string


    return report(str(names) + ' == ' + str(x_val)+' ')

def make_regex_inverse_of_format_string(pattern):
    # type (str) -> str
    the_specials = '.^$*+?[]|():!#<='
    for c in the_specials:
        pattern = pattern.replace(c,'\\' + c)
    pattern = pattern.replace( '{', r'(?P<' ).replace( '}', r'>.*)' )
    return r'\A' + pattern + r'\Z'


def convert_dictionary_to_data_tree(nested_dict):
    # type(dict) -> DataTree
    import ghpythonlib.treehelpers as th
        
    User_Text_Keys = [[key for key in link_dict] for link_dict in nested_dict]
    User_Text_Values = [[val for val in link_dict.values()] for link_dict in nested_dict]
    
    Data =  th.list_to_tree([[User_Text_Keys, User_Text_Values]])
    Geometry = nested_dict.keys()  # Multi-polyline-links aren't unpacked.
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
                                            ,POLYLINE = 'PolylineVertices'
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

def get_points_list_from_Rhino_obj(x, shp_type):
    #type(str, dict) -> list
    import rhinoscriptsyntax as rs
    f = getattr(rs, Rhino_obj_converter_Shp_file_shape_map[shp_type])
    return [list(y) for y in f(x)]

Rhino_obj_checker_Shp_file_shape_map = dict( NULL = None
                                            ,POINT = 'IsPoint'
                                            ,MULTIPATCH = 'IsMesh'    # Unsupported.  Complicated.  TODO!
                                            ,POLYLINE = 'IsPolyline'
                                            ,POLYGON = 'IsPolyline'   #Doesn't check closed
                                            ,MULTIPOINT = 'IsPoint'   # Need to define lambda l : any(IsPoint(x) for x in l)
                                            ,POINTZ = 'IsPoint'
                                            ,POLYLINEZ = 'IsPolyline'
                                            ,POLYGONZ = 'IsPolyline'   #Doesn't check closed
                                            ,MULTIPOINTZ = 'IsPoints'  # see MULTIPOINT
                                            ,POINTM = 'IsPoint'
                                            ,POLYLINEM = 'IsPolyline'
                                            ,POLYGONM = 'IsPolyline'   #Doesn't check closed 
                                            ,MULTIPOINTM = 'IsPoints'  # see MULTIPOINT
                                            )  

def check_is_specified_obj_type(obj, shp_type):   #e.g. polyline
    # type(str) -> bool
    import rhinoscriptsyntax as rs
    return getattr(rs, Rhino_obj_checker_Shp_file_shape_map[ shp_type] )( obj )

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

def get_all_shp_type_Rhino_objects(shp_type):
    #type (None) -> list
    import rhinoscriptsyntax as rs
    def f():
        return rs.ObjectsByType( Rhino_obj_getter_code_Shp_file_shape_map[shp_type]
                                ,select=False
                                ,state=0)
    return f

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

def get_groups_links_and_key_val_tuples( 
                              options = opts['options']
                             ,obj_getter = get_all_shp_type_Rhino_objects
                             ,group_getter = get_all_groups
                             ,group_member_getter = get_members_of_a_group
                             ,key_val_tuples_getter = get_key_val_tuples()
                             ,shp_type = 'POLYLINEZ'
                            ):
    #type(function, function, function) -> function
    shp_type = options.shp_file_shape_type            
    def generator(obj):
        #type( type[any]) -> list, list
        #
        # Groups first search.  If a special Usertext key on member objects 
        # is used to indicate links, then an objects first search 
        # is necessary instead.  This would be better for reading shapefiles.

        members_of_all_groups = []
        groups = group_getter()
        for group in groups:
            group_members = group_member_getter(group)
            if ( group_members and
                 any(check_is_specified_obj_type(x, shp_type) 
                                             for x in group_members) ):
                members_of_all_groups += group_members
                key_val_tuples = chain( *( key_val_tuples_getter(member)
                                                for member in group_members ) 
                                       )
                yield group, key_val_tuples

        objs = obj_getter(shp_type)
        for obj in objs:
            if obj not in members_of_all_groups:
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

    try:
        ghdoc     # type: ignore
    except:
        global ghdoc
        ghdoc = sc.doc  

    sc.doc = Rhino.RhinoDoc.ActiveDoc # type: ignore 
    # ActiveDoc may change on Macs - TODO: only call once or accept argument
    output('Starting Read_Network_Links','DEBUG')

    rhino_groups_and_objects = make_gdm(get_groups_links_and_key_val_tuples(options))

    if opts_at_call['options'].read_overides_Data_from_Usertext:
        read_Usertext_as_tuples = get_key_val_tuples()
        for obj in gdm:
            gdm[obj].update(read_Usertext_as_tuples(obj))

    override_gdm_with_gdm(rhino_groups_and_objects, gdm, opts_at_call)

    return 0, f_name, rhino_groups_and_objects, None


def write_objects_and_data_to_shapefile(f_name, geom_data_map, opts_at_call):
    #type(type[any], str, dict, dict) -> int, str, dict, dict
    
    import rhinoscriptsyntax as rs
    
    options = opts_at_call['options']


    shp_type = options.shp_file_shape_type            
    
    if geom_data_map == {} and options.read_from_Rhino_if_no_shp_data:
        retcode, ret_f_name, geom_data_map = (
              read_objects_groups_and_Usertext_from_Rhino(   f_name
                                                            ,{}
                                                            ,opts_at_call
                                                          )
        )

    def pattern_match_key_names(x):
        #type: (str)-> str / None
        format_string = options.rhino_user_text_key_format_str_to_read
        pattern = make_regex_inverse_of_format_string( format_string )
        m = match(pattern, x) 
        return m.group('name') if m else None #, m.group('fieldtype'), 
                                              # m.group('size') if m else None
                                              # can get 
                                              # (literal_text, field_name, 
                                              #                  f_spec, conv) 
                                              # from iterating over
                                              # string.Formatter.parse(
                                              #                 format_string)

    def get_list_of_lists_from_tuple(tupl):
        obj = tupl[0]
        if check_is_specified_obj_type(obj, shp_type):
            return [get_points_list_from_Rhino_obj(y, shp_type) for y in obj]
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
                         )
    ) 
    return retcode, filename, geom_data_map, None





def make_list_of_rhino_objs_from_shapefile_geometry_pts_lists(
                     options = opts['options']
                    ,make_new_group = make_new_group
                    ,add_objects_to_group = add_objects_to_group
                    ,Rhino_obj_adder_Shp_file_shape_map = Rhino_obj_adder_Shp_file_shape_map
                    ):
    import rhinoscriptsyntax as rs
    rhino_obj_maker = getattr(rs, Rhino_obj_adder_Shp_file_shape_map[options.shp_file_shape_type])
    def f(l, rec):
        objs_list = []
        for points_list in l:
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
    return f

def get_shape_file_rec_ID(options = opts['options']): 
    import rhinoscriptsyntax as rs 

    def f(l, rec):
        shp_file_obj_ID = rec._asdict().get(options.uuid_shp_file_field_name, '')
        if rs.IsObject(shp_file_obj_ID) or is_group(shp_file_obj_ID):
            return shp_file_obj_ID
        else:
            g = make_list_of_rhino_objs_from_shapefile_geometry_pts_lists(options)
            rhino_obj_or_group_name = g(l, rec)
            return rhino_obj_or_group_name
    return f



def Read_Links_Data_From_Shapefile( f_name
                                   ,geom_data_map 
                                   ,opts_at_call
                                   ):
    #type(type[any], str, dict, dict) -> int, str, dict, dict
    import rhinoscriptsyntax as rs
    options = opts_at_call['options']

    ( fields
     ,recs
     ,shapes ) = get_fields_recs_and_shapes_from_shapefile( f_name )

    field_names = [ x[0] for x in fields ]


    if options.create_new_links_layer_from_shapefile: 
        obj_key_maker = make_list_of_rhino_objs_from_shapefile_geometry_pts_lists( options ) 
        shapes_to_output = shapes
    else:          
        obj_key_maker = get_shape_file_rec_ID(options) # key_val_tuples
        # i.e. if options.uuid_shp_file_field_name in field_names but also otherwise
      
        if sys.version_info.major < 3:
            shapes_to_output = geom_data_map.viewkeys()  
        else: 
            shapes_to_output = geom_data_map.keys() 

    shp_file_gen_exp  = (  (shape, zip(field_names, rec)) for (shape, rec) in 
                                           izip(shapes_to_output, recs)  )              

    gdm = make_gdm( shp_file_gen_exp
                   ,obj_key_maker 
                   )

    override_gdm_with_gdm(gdm, geom_data_map, opts_at_call)

    if options.delete_shapefile_after_reading and isfile(f_name):
        os.remove(f_name)


    return 0, f_name, gdm, None



    #keys=[]
    #if options.create_new_links_layer_from_shapefile:
    #    Geometry =  [] # only overwrites local variable in this function
    #    rs.AddLayer(name = split(f_name)[1] ) #.rpartition('.')[0])
    #    for link in shapes:
    #        if len(link) > 1:   #multi-polyline link
    #            new_group = rs.AddGroup()
    #            polylines = []
    #            for list_of_points_lists in link:
    #                polylines += rs.AddPolyline( list_of_points_lists )
    #            rs.AddObjectsToGroup(polylines, new_group)
    #            Geometry += new_group
    #        else:          # single polyline link (pyshp returns nested)
    #            Geometry += rs.AddPolyline(link[0])
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



def Write_Links_Data_To_Rhino_File( f_name     #Bake_Geom_and_Data
                                   ,geom_data_map  # nested dict
                                   ,opts_at_call
                                   ):
    #type(type[any], str, dict, dict) -> int, str, dict, dict

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
        
        for key, val in d:

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
            write_obj_val(rhino_obj, UserText_key_name, str( val ))

    for key, val in geom_data_map.items():
        if is_group(key):
            group_members = get_members_of_a_group(key)
        else:
            group_members = [key]
        for member in group_members:
            write_dict_to_UserText_on_obj(val, member)


    return 0, f_name, geom_data_map, None
    
###################################################################################################
#                                                                           # TODO: Fix interface - fields
def Plot_Data_On_Links(f_name, geom_data_map, opts):
    #type(type[any], str, dict, dict) -> int, str, dict, dict

    import Rhino
    import scriptcontext as sc
    import rhinoscriptsyntax as rs

    options = opts['options']

    field = options.write_from_iterable_to_shapefile_writer

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
                  

###############################################################################
def main_sequence(ghenv, f_name, gdm, opts):
    #type(type[any], str, , type[any], type[any], dict) -> bool, str, type[any], type[any], WriteableFlushableList
    output('Starting main sequence... ','INFO')
    metas, options = opts['metas'], opts['options']
    #a = WriteableFlushableList()                                     

    ################################################################################
    # GHsDNA main sequence  
    # 
    ###############################################################################

    ###############################################################################
    #
    # This script can be imported as a module, e.g. to make import_module_or_search_for_it()
    # available as this is the primary definition for it.  But it is normally run as a 
    # straightforward script, either from Grasshopper or the command line, as a
    # once-through batch process
    # with no loops or branches or dynamic behaviour in the main function sequence.
    # Such more complicated control structures can easily be implemented in Grasshopper,
    # or forks of this project.
    #
    # Execution Order:
    # ### Standard library Imports => ### Meta Options => ### Module import/searcher => ### Options =>### Logging
    # ### Logging => 
    # ### Custom Imports =>
    # ### Read geometry, previous GHsDNA user text, from Rhino .3dm file and read user weights () => Create .shp file(s) with
    # sufficient number, type and size of  fields => Write to .shp input files =>
    # call sDNA => Read fron .shp output file => Write data to Grasshopper file (user can bake to Rhino .3dm using GH if desired)
    #
    # #### Options / Inputs:
    # 1) User inputs from GH component or command line switches       --options_manager.overrides--->
    # 2) options variable in user specified config.py file            --options_manager.overrides--->
    # 3) options variable in Main GHsDNA application config.py file   --options_manager.overrides--->
    # 4) hardcoded options in this file
    #
    # The metas control the details of the above process, especially where to find config.py:
    # 1) User inputs from GH component or command line switches define how to read in               --options_manager.overrides--->
    # 2) TODO: Other user inputs, e.g. if misspelt, in wrong order, of wrong type, missing or extra --options_manager.overrides--->
    # 3) metas variable in user specified config.py file                                            --options_manager.overrides--->
    # 4) metas variable in Main GHsDNA application config.py file                                   --options_manager.overrides--->
    # 5) hardcoded metas in this file
    #
    # So that the user may specify options that effect subsequent sections e.g. to log more or less verbosely, and to customise 
    # the module importer we parse the options first, at the cost of not being able to helpfully import config.py and 
    # options_manager.py, not being able to customise their locations beyond the default hardcoded subdir, main project dir,
    # and searching sys.path (sys.path here) the same as normal use of import
    #

    #
    # Named tuples are immutable and indexable without ['']
    # but require a little boilerplate code to set up.  They can easily be created from 
    # dictionaries and lists. They do still require e.g. ._fields to iterate over their 
    # field names or test keys/field names for membership
    # (although dir ( ) can be avoided along (with the special methods it outputs) ).  
    #
    # In GHsDNA we live in a GH component, in GH, in Rhino.  This component could be one of many in the grasshopper
    # definition (the .gh file).  Each component 
    # runs its own Python interpreter instance.  Therefore the author decrees the options should 
    # not change within each of the four or so function bodies of the main subprocesses below (only between them and between calls)
    # so they are fixed immediately after the function headers here.
    # See options_design_notes.txt
    #

    #
    #
    ################
    # Logging.  (Uses class above)
    #import wrapper_logging
    #wrapper_logging = import_module_or_search_for_it('wrapper_logging')


    #
    #gh_component_output=logging.StreamHandler(a)
    #gh_component_output.setLevel(logging.INFO)
    #
    ################
    #
    ###############################################################################


    ###############################################################################
    # Custom module imports
    #
    #from .third_party_python_modules import shapefile as shp
    #shp = import_module_or_search_for_it('shapefile')
    #output("options.uuid_length == " + str(options.uuid_length))
    #wrapper_pyshp = import_module_or_search_for_it('wrapper_pyshp')
    #from .custom_python_modules import wrapper_pyshp
    ###############################################################################




    ###############################################################################
    # Main Grasshopper imports
    #############################
    #
    # Core Python modules
    #
    # Pypi Python modules 
    #
    # Rhino/GH API modules 
    import Rhino
    import scriptcontext as sc
    import rhinoscriptsyntax as rs    
    #Rhino = import_module_or_search_for_it('Rhino')
    #sc = import_module_or_search_for_it('scriptcontext') # sc = for common import ... as sc pattern
    #rs = import_module_or_search_for_it('rhinoscriptsyntax') 
    #utility = import_module_or_search_for_it('utility') # Unused?
    #
    #############################################################################################################


    #############################################################################################################
    # Local functions for Grasshopper context
    #
    def start_and_end_points(curve): # curve : Rhino.Geometry.Curve https://developer.rhino3d.com/api/RhinoCommon/html/T_Rhino_Geometry_Curve.htm
        #type: (Rhino.Geometry.Curve)->list(list(float,3),list(float,3))
        return [[list(rs.CurveStartPoint(curve)),list(rs.CurveEndPoint(curve))]]
    #
    #
    #
    ############################################################################################################




    ############################################################################################################
    # GHsDNA GH component main process logic
    try:
        ghdoc  # type: ignore
    except:
        ghdoc = sc.doc
    sc.doc = Rhino.RhinoDoc.ActiveDoc # type: ignore # ActiveDoc may change on Macs - TODO: only call once or accept argument
    #
    #
    #############################################################################
    # Main import of rhino objects
    rhino_doc_curves = rs.ObjectsByType(4, select=False, state=0) # 4 => Curves, could use state=1 (Nomal) or state=3==1+2 (Normal + Locked, i.e. No hidden ones)
    #
    #############################################################################
    #
    #
    def pattern_match_key_names(x):
        #type: (str)-> str / None
        format_string = options.rhino_user_text_key_format_str_to_read
        pattern = make_regex_inverse_of_format_string( format_string )
        m = match(pattern, x)
        return m.group('name') if m else None

    def write_to_shapefile_with_rhino_doc_as_default( my_iter = rhino_doc_curves 
                                                    ,shp_file = options.shape_file_to_write_Rhino_data_to_from_GHsDNA # None is Hardcoded default val
                                                    ,shape_mangler = start_and_end_points
                                                    ,key_finder = lambda x : rs.GetUserText(x,None)
                                                    ,key_matcher = pattern_match_key_names
                                                    #,key_mangler = lambda x : options.rhino_user_text_key_format_str_to_read.format(name = x)
                                                    #,value_mangler = rs.SetUserText
                                                    ,value_demangler = rs.GetUserText
                                                    ,shape = 'POLYLINEZ'
                                                    ,options = options
                                                    ):

        if shp_file == None:
            shp_file = options.Rhino_doc_path[:-4] + options.shp_file_extension
                                # file extensions are actually optional in PyShp, but just to be safe and future proof we slice out '.3dm'
        return write_from_iterable_to_shapefile_writer(  my_iter 
                                                        ,shp_file 
                                                        ,shape_mangler
                                                        ,key_finder
                                                        ,key_matcher
                                                        #,key_mangler
                                                        #,value_mangler
                                                        ,value_demangler
                                                        ,shape
                                                        ,options
                                                        )

    #output(options.uuid_length)

    ret_code, shp_filename, cached_fields, cached_user_data, cached_geometry = write_to_shapefile_with_rhino_doc_as_default()
    default_sDNA_prepped_shp_file_name = shp_filename[:-4] + options.prepped_shp_file_suffix + options.shp_file_extension

    def call_sDNA_prepare (shp_input_file = shp_filename
                          ,shp_output_file = default_sDNA_prepped_shp_file_name
                          ,options = options 
                          ):
        shp_output_file = get_unique_filename_if_not_overwrite(shp_output_file,options)
        command = options.python_exe + " -u " + '"' + options.sDNA_prepare + '"' + " -i " + shp_input_file + " -o " + shp_output_file
        output(command)
        call( command )
        return shp_output_file

    shp_prepped_file = call_sDNA_prepare()

    default_sDNA_output_shp_file_name = shp_filename[:-4] + options.output_shp_file_suffix + options.shp_file_extension
    
    def call_sDNA_integral (shp_input_file = shp_filename
                           ,shp_output_file = default_sDNA_output_shp_file_name
                           ,options = options
                           ):
        shp_output_file = get_unique_filename_if_not_overwrite(shp_output_file,options)
        command =  options.python_exe + " -u " + '"' + options.sDNA_integral + '"' + " -i " + shp_input_file + " -o " + shp_output_file
        output(command)
        call( command)            
        return shp_output_file 

    sDNA_output_shp_file = call_sDNA_integral()

    #############################
    # TODO:  Write cached_fields, cached_user_data to the .3dm file as document user text, or even attribute_table_data in a local temp file containing a hash of the 
    # .3dm file, to speed up future calls of this function even from differetn python instances

    

    sDNA_fields, sDNA_recs, sDNA_shapes = get_fields_recs_and_shapes_from_shapefile( sDNA_output_shp_file )
    sDNA_field_names = [ x[0] for x in sDNA_fields ]

    #Rhino_object_uuid_index = sDNA_field_names.index(options.uuid_shp_file_field_name)
    date_time_of_run = asctime()

    for rhino_obj, record in zip(cached_geometry ,sDNA_recs):
        existing_keys = rs.GetUserText(rhino_obj)
        for (output_val, sDNA_output_field_info) in zip(record, sDNA_fields):
            output_abbrev, type_code, field_length, decimal_length = sDNA_output_field_info
            s = options.sDNA_output_user_text_key_format_str_to_read
            UserText_key_name = s.format(name = output_abbrev, datetime = date_time_of_run)
            if not options.overwrite_UserText:
                i = 2
                tmp = UserText_key_name + options.duplicate_UserText_key_suffix.format(i)
                while tmp in existing_keys:
                    i+=1
                    tmp = UserText_key_name + options.duplicate_UserText_key_suffix.format(i)
                UserText_key_name = tmp
            else:
                if not options.suppress_overwrite_warning:
                    output("UserText key == " + UserText_key_name + " overwritten on object with guid " + str(rhino_obj),'INFO')
            rs.SetUserText(rhino_obj, UserText_key_name, str(output_val))
    # 
    ############################################################################################################
    sDNA_output_to_plot_index = 10 #sDNA_output_abbrevs.index('TPBtE') #sDNA_field_names.index(options.sDNA_output_abbrev_to_graph )
    output ("Plotting field == " + str(sDNA_fields[sDNA_output_to_plot_index]))
    data_points = [x[sDNA_output_to_plot_index] for x in sDNA_recs]
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

    def change_line_thickness(obj,width,rel_or_abs = False):  #The default value in Rhino for wireframes is zero so rel_or_abs==True will not be effective if the width has not already been increased.
        x = rs.coercerhinoobject(obj, True, True)
        x.Attributes.PlotWeightSource = Rhino.DocObjects.ObjectPlotWeightSource.PlotWeightFromObject
        if rel_or_abs:
            width = width * x.Attributes.PlotWeight
        x.Attributes.PlotWeight = width
        x.CommitChanges()


    new_width = 4

    for rhino_obj, record in zip(cached_geometry ,sDNA_recs):
        #change_line_thickness(rhino_obj, new_width)
        #rs.ObjectColor(rhino_obj, map_f_to_tuples(interpolate, record[sDNA_output_to_plot_index], data_min, data_max, rgb_min, rgb_max))
        rs.ObjectColor(rhino_obj, map_f_to_three_tuples( three_point_quadratic_spline
                                                        ,record[sDNA_output_to_plot_index]
                                                        ,data_min
                                                        ,0.5*(data_min + data_max)
                                                        ,data_max
                                                        ,rgb_min
                                                        ,rgb_mid
                                                        ,rgb_max
                                                        )
                        )

    rs.ObjectColorSource(cached_geometry,1)  # 1 => colour from object
    rs.ObjectPrintColorSource(cached_geometry,2)  # 2 => colour from object
    rs.ObjectPrintWidthSource(cached_geometry,1)  # 1 => print width from object
    rs.ObjectPrintWidth(cached_geometry,new_width) # width in mm
    #rs._commanPrint Display (Model Viewports) ( State=On  Color=Display  Thickness=15 ): Thickness=20
    rs.Command('_PrintDisplay _State=_On Color=Display Thickness=8 ')
    #rs.Command('Print Display (Model Viewports) ( State=On  Color=Display  Thickness=8 )')

    sc.doc.Views.Redraw()
    sc.doc=ghdoc

    return 0, sDNA_output_shp_file, cached_geometry, None, #sDNA_recs, None
#
###############################################################################

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

    # global opts instead of local_opts is intentional 
    # for cacheing (like get_syntax_dict)
    sDNA, UISpec = local_opts['metas'].sDNA, local_opts['options'].UISpec
    # 
    #
    def update_or_init(cache, defaults, name):
        if name in cache and sDNA in cache[name]:
            if isinstance(defaults, dict):
                defaults.update(cache[name][sDNA]._asdict())
                cache[name][sDNA] = make_nested_namedtuple( defaults , name)
            #else:
            #    pass
                #assert cache[name][sDNA] = defaults # already
        else:
            cache.setdefault(name, {})
            cache[name][sDNA] = defaults


    if hasattr(UISpec, tool_name):
        get_syntax = getattr(UISpec, tool_name).getSyntax     
        # not called until component executes in RunScript
        update_or_init( get_syntax_dict,  get_syntax,  tool_name )

        input_spec = getattr( UISpec,  tool_name ).getInputSpec()
        defaults_dict = { varname : default for (    varname
                                                    ,displayname
                                                    ,datatype
                                                    ,filtr
                                                    ,default
                                                    ,required
                                                ) in input_spec  }
        update_or_init( opts,  defaults_dict,  nick_name )
        # Tool options are stored per nick_name, which may equal tool_name
    else:
        update_or_init( opts,  empty_NT,  nick_name )
        update_or_init( get_syntax_dict,  empty_NT,  tool_name )
    return 

class FakeProgress():
    setInfo = output
    def setPercentage(self,*args):
        pass

tools_dict=dict( read_objects_groups_and_Usertext_from_Rhino = [read_objects_groups_and_Usertext_from_Rhino]
                ,Write_Objects_and_Data_To_Shapefile = [write_objects_and_data_to_shapefile]
                ,Read_Links_Data_From_Shapefile = [Read_Links_Data_From_Shapefile]
                ,Plot_Data_On_Links = [Plot_Data_On_Links]
                ,main_sequence = [main_sequence]
                )

support_component_names = list(tools_dict.keys()) # In Python 3, .keys() and 
                                                  # .values() are dict views
                                                  # not lists

support_component_names = list(tools_dict.keys())

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
            output('Invalid name_map: ' + ' '.join(map(str,vals_in_name_map_with_no_Tools)) + 
                    '.  Adjust name_map to point to known functions or lists thereof.  ','CRITICAL')
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
                                    ,opts_at_call['run'].run )
            
            options = opts_at_call['options']

            dot_shp = options.shp_file_extension

            input_file = opts_at_call[nick_name][sDNA].input
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
                opts_at_call[nick_name][sDNA] = opts_at_call[nick_name][sDNA]._replace(input = input_file)


            output_file = opts_at_call[nick_name][sDNA].output
            if output_file == '':
                output_suffix =  options.output_shp_file_suffix
                if tool_name == 'sDNAPrepare':
                    output_suffix = options.prepped_shp_file_suffix   
                output_file = input_file.rpartition('.')[0] + output_suffix + dot_shp

            output_file = get_unique_filename_if_not_overwrite(output_file, opts_at_call)
            opts_at_call[nick_name][sDNA] = opts_at_call[nick_name][sDNA]._replace(output = output_file)

            

            syntax = get_syntax_dict[tool_name][sDNA]( opts_at_call[nick_name][sDNA]._asdict() )   
                                                      #opts[nick_name] was initialised to defaults in 
                                                      # in cache_syntax_and_UISpec

            return_code = run.runsdnacommand(    syntax
                                                ,sdnapath = dirname(UISpec.__file__)  #opts['options'].sDNA_UISpec_path
                                                ,progress = FakeProgress()
                                                ,pythonexe = options.python_exe
                                                ,pythonpath = None)   # TODO:  Work out if this is important or not! 
                                                                    # os.environ["PYTHONPATH"] not found in Iron Python
            # To allow auto reading the shapefile afterwards, the returned Data == None == None to end
            # the input GDM's round trip, in favour of Data and Geometry read from the sDNA analysis just now completed.
            return return_code==0, getattr( opts_at_call[nick_name],  'output' ), None, None
        return [run_sDNA_wrapper]
    else:
        return [None]

def tool_factory(nick_name, name_map, local_opts):  
    #type( list or str, dict ) -> 

    #sDNA, UISpec, run = local_opts['options'].sDNA, local_opts['options'].UISpec, local_opts['options'].run

    #global tools_dict # mutable - access through normal parent module namespace
    sDNA = local_opts['metas'].sDNA

                            
    def tool_factory_wrapper(f_name, gdm, opts_at_call):
        return tool_factory( opts_at_call['options'].tool_name
                            ,name_map # so technically a closure, but only to 
                            ,opts_at_call )(f_name # conform to tool interface
                                            ,gdm
                                            ,opts_at_call )
 
    if isinstance(nick_name, Hashable):
        if nick_name not in tools_dict or sDNA not in opts.get(nick_name, {}):
            map_result = name_map.get(nick_name, nick_name)
            if isinstance(map_result, list):
                tools =[]
                for mapped_name in map_result:
                    tools += tool_factory( mapped_name,  name_map,  local_opts ) 
                tools_dict.setdefault(  nick_name,  tools )
            else:
                mapped_name = map_result
            if nick_name == "Python":   # Validates name_map and used in dev
                                        # tool to auto name components
                tools_dict.setdefault(  nick_name,  component_names_factory(name_map) )
            if nick_name in special_names: #["sDNA_general"]
                tools_dict.setdefault(  nick_name,  tool_factory_wrapper )
            else:  # mapped_name is a tool_name, possibly named explicitly in nick_name
                cache_syntax_and_UISpec(nick_name, mapped_name, local_opts) # create entries for sDNA
                tools_dict.setdefault(  nick_name,  get_specific_tool(mapped_name, nick_name, local_opts)  )
                # assert isinstance(get_specific_tool(map_result, nick_name, name_map, local_opts), list)                    
        return tools_dict[nick_name] 
    else:
        return None

loc = tool_factory





###############################################################################
#Main root process
#
from os.path import isdir, isfile, sep, normpath, join, split
if      '__file__' in dir(__builtins__)  and  __name__ in __file__ and '__main__' not in __file__ and '<module>' not in __file__:                     
    # Assert:  We're in a module!
    pass
else:
    pass


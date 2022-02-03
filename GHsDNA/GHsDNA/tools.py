#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.01'
__copyright__ = 'Cardiff University'
__license__ = {  'Python standard library modules and ' : 'Python Software Foundation 2.7.18' # https://docs.python.org/2.7/license.html
                ,'wrapper_logging' : 'Python Software Foundation 2.7.18'
                ,'wrapper_pyshp' : 'MIT' # https://pypi.org/project/pyshp/ 
                ,'sDNAUISpec.py' : 'MIT' # https://github.com/fiftysevendegreesofrad/sdna_open/blob/master/LICENSE.md
                ,'everything else' : 'same as for sDNA ' # https://sdna.cardiff.ac.uk/sdna/legal-license/ 
              }



from collections import namedtuple, OrderedDict
from json import tool
import sys, os  
from os.path import join, split, isfile, dirname #, isdir
from re import match
#from subprocess import call
from time import asctime

import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs

from .third_party_python_modules import shapefile as shp
from .custom_python_modules import options_manager, wrapper_logging, wrapper_pyshp


def make_regex_inverse_of_format_string(pattern):
    # type (str) -> str
    the_specials = '.^$*+?[]|():!#<='
    for c in the_specials:
        pattern = pattern.replace(c,'\\' + c)
    pattern = pattern.replace( '{', r'(?P<' ).replace( '}', r'>.*)' )
    return r'\A' + pattern + r'\Z'

def get_stem_and_folder(path):
    if isfile(path):
        path=dirname(path)
    return split(path)

print("Hi everybody!")
class HardcodedMetas(): 
    #current_working_dir =  sys.path[0]  # where am I?
    config_file_path = 'config.ini'
    add_in_new_options_keys = False
    allow_components_to_change_type = False
    typecheck_opts_namedtuples = True
    typecheck_opts_fields = True
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
#    modules_subdirectories = [   r'third_party_python_modules'   # all pushed to sys.path
#                                ,r'custom_python_modules'
#                                ] 
#    custom_module_search_paths = [   r'C:\Users\James\AppData\Roaming\Grasshopper\Libraries'
#                                    ,r'C:\Users\James\AppData\Roaming\Grasshopper'
#                                    ,r'C:\Users\James\AppData\Roaming\Grasshopper\UserObjects'
#                                    ,r'C:\Users\James\AppData\Roaming\Grasshopper\AutoSave'
#                                    ,r'C:\Users\James\Downloads\GHsDNA'
#                                    ,r'C:\Users\James\Downloads'
#                                    ,r'C:\Users\James'
#                                    ,r'C:\Users\James\AppData\Roaming\GHsDNA'
#                                    ,r'C:\Program files\GHsDNA'
#                                    ,r'C:\Program Files (x86)\GHsDNA'
#                                    ,r'C:\GHsDNA'
#                                    ,r'C:\Users\James\AppData\Roaming\McNeel\Rhinoceros\7.0\scripts'
#                                    ,r'C:\Users\James\AppData\Roaming\McNeel\Rhinoceros\packages\7.0'
#                                ]        

class HardcodedOptions():            
    platform = 'NT' # in {'NT','win32','win64'} only supported for now
    encoding = 'utf-8'
    rhino_executable = r'C:\Program Files\Rhino 7\System\Rhino.exe'
    sDNA = ('sDNAUISpec','runsdnacommand')
    sDNA_path = ''
    UISpec = None
    run = None
    sDNA_UISpec_path = r'C:\Program Files (x86)\sDNA\sDNAUISpec.py'
    sDNA_search_paths = [sDNA_UISpec_path, join(os.getenv('APPDATA'),'sDNA')]
    sDNA_search_paths += [join(os.getenv('APPDATA'), get_stem_and_folder(sDNA_search_paths[0])[1]) ]
    sDNA_prepare = r'C:\Program Files (x86)\sDNA\bin\sdnaprepare.py'
    sDNA_integral = r'C:\Program Files (x86)\sDNA\bin\sdnaintegral.py'
    python_exe = r'C:\Python27\python.exe' # Default installation path of Python 2.7.3 release (32 bit ?) http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi
                                            # linked from sDNA manual https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/installation_usage.html
    tool_name="main_sequence"
    log_file_post_fix = '_GHsDNA'
    log_file = ghdoc.Path.rsplit('.')[0]+'.log' if 'ghdoc' in globals() else join(
               sys.path[0],sys.argv[0].rsplit('.')[0] + log_file_post_fix + '.log')
                              #os.getenv('APPDATA'),'Grasshopper','Libraries','GHsDNA','GHsDNA.log')
    logs_subdirectory = r'logs'
    tests_subdirectory = r'tests'
    logger_file_level = 'DEBUG'
    logger_console_level = 'INFO'
    logger_custom_level = 'INFO'
    shp_file_extension = '.shp' # file extensions are actually optional in PyShp, but just to be safe and future proof
    supply_sDNA_file_names = True
    shape_file_to_write_Rhino_data_to_from_GHsDNA = r'C:\Users\James\Documents\Rhino\Grasshopper\GHsDNA_shapefiles\t6.shp' # None means Rhino .3dm filename is used.
    overwrite_shp_file = True
    overwrite_UserText = True
    duplicate_UserText_key_suffix = r'_{}'
    prepped_shp_file_suffix = "_prepped"
    output_shp_file_suffix = "_output"
    duplicate_file_name_suffix = r'_({})' # Needs to contain a replacement field {} that .format can target.  No f strings in Python 2.7 :(
    suppress_overwrite_warning = False     
    uuid_shp_file_field_name = 'Rhino3D_' # 'object_identifier_UUID_'     
    uuid_length = 36 # 32 in 5 blocks with 4 seperators.
    calculate_smallest_field_sizes = True
    global_shp_file_field_size = 30
    global_shp_number_of_decimal_places = 10
    shp_file_field_size_num_extra_chars = 2
    use_memo = False
    enforce_yyyy_mm_dd = False
    use_str_decimal = True
    do_not_convert_floats = True
    decimal_module_prec = 12
    shp_record_max_decimal = 4
    #
    #
    rhino_user_text_key_format_str_to_read = 'sDNA_{name}_type={fieldtype}_size={size}'  #30,000 characters tested!
    sDNA_output_user_text_key_format_str_to_read = 'sDNA_output_{name}_run_time={datetime}'  #30,000 characters tested!
    #
    rhino_user_text_key_pattern = make_regex_inverse_of_format_string(rhino_user_text_key_format_str_to_read)
    sDNA_output_abbrev_to_graph = 'BtE'

class HardcodedLocalMetas():
    sync_to_shared_global_opts = True
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

metas= get_namedtuple_etc_from_class(HardcodedMetas, 'Metas')
options = get_namedtuple_etc_from_class(HardcodedOptions, 'Options')
local_metas = get_namedtuple_etc_from_class(HardcodedLocalMetas, 'LocalMetas')

empty_NT = namedtuple('Empty','')(**{})

opts = OrderedDict( metas=metas
                   ,options=options
                   )

get_syntax_dict = {} 
input_spec_dict = {}                 

def output(s, logging_level = "INFO", stream = None, logging_dict = None ):
    #type: (str,...,str,dict) -> None
    #type: (stream) == anything with a write method. e.g. 'file-like object' supporting write() and flush() methods, e.g. WriteableFlushableList
    
    print(s)


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
#import options_manager.override_namedtuple_with_ini_file, options_manager.override_namedtuple_with_namedtuple, options_manager.override_namedtuple_with_dict

####################################################################################################################
# First options options_manager.override (3), user's installation specific options over (4), hardcoded defaults above
if isfile(metas.config_file_path):
    metas = options_manager.override_namedtuple_with_ini_file(metas.config_file_path, metas, False)
    options = options_manager.override_namedtuple_with_ini_file(metas.config_file_path, options, metas.add_in_new_options_keys)
else:    
    output('No Installation wide config file found at ' + metas.config_file_path + ' .  Using hardcoded default options.  ','WARNING')
####################################################################################################################
#
#


#def function_imported_by_GHsDNA_launcher(ghenv, f_name, Geom, Data, opts, *args):
    #type(ghenv, bool, str, Rhino Geometry, datatree, tuple(namedtuple,namedtuple), *dict) -> bool, str, Rhino_Geom, datatree, str
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

    ###############################################################################################################
    # Override (3) user installation specific options with (2) previously updated options in Grasshopper definition 
    # from another GHsDNA component
    #new_nt = options_manager.override_namedtuple_with_namedtuple(installation_nt, old_nt_or_dict, add_in_new_options_keys=True, check_types = True, strict = False)
    #new_metas = options_manager.override_namedtuple_with_namedtuple(test_metas, new_metas, add_in_new_options_keys=True, check_types = True, strict = False)
    #new_options = options_manager.override_namedtuple_with_namedtuple(test_options, new_options, True, add_in_new_options_keys=True, check_types = True, strict = False)
                                                               # Both must have an _asdict() method.  See note 1) above.
                                                               # Assume both came from a previous call to this function
                                                               # and so already contain hardcoded and installation options
                                                               # i.e.  no fields are missing.

    #if 'config_file_path' in args_metas:
    #    ###########################################################################################################################
    #    # Override (2) previously updated options in Grasshopper definition with (1) latest (e.g. different) project file's options
    #    new_metas = options_manager.override_namedtuple_with_ini_file(  args_metas[config_file_path]
    #                                                                   ,new_metas
    #                                                                   ,metas.add_in_new_options_keys
    #                                                                   ,False
    #                                                                   ,'Metas'
    #                                                                   ,False
    #                                                                   ,None
    #                                                                   )
    #    new_options = options_manager.override_namedtuple_with_ini_file( args_metas[config_file_path]
    #                                                                    ,new_options
    #                                                                    ,metas.add_in_new_options_keys
    #                                                                    ,False
    #                                                                    ,'Metas'
    #                                                                    ,False
    #                                                                    ,None
    #                                                                    )
        # Note, the order of the processing of hardcoded and installation config.ini options is unlikely to matter but
        # the user may expect arg_metas (processed below) to occur before project config.ini options_manager.overrides new_options (processed above)
        # TODO: Nice to have.  Switch this order if a meta is changed (need to always check for this meta in higher priorities first, 
        # before overriding lower priority options).

    #######################################################################################################################
    # Override (1) latest project file's options with (0) options arguments directly supplied to the Grasshopper component
    #new_metas = options_manager.override_namedtuple_with_dict(args_metas, new_metas, True, 'Metas')
    #new_options = options_manager.override_namedtuple_with_dict(args_options, new_options, True, 'Options')
    #return new_nt

def override_all_opts( args_dict
                      ,local_opts
                      ,external_opts
                      ,local_metas
                      ,external_local_metas
                      ,name):
    #type (dict, dict(namedtuple), str) -> dict(namedtuple)
    #
    # 1) We assume opts has been built from a previous GHPython launcher component and call to this very function.  This
    # trusts the user and our components somewhat, in so far as we assume metas and options in opts have not been crafted to have
    # be of a class named 'Metas', 'Options', yet contain missing options.  
    #
    # 2) A primary meta in opts refers to an old primary meta (albeit the most recent one) and will not be used
    # in the options_manager.override order as we assume that file has already been read into a previous opts in the chain.  If the user wishes 
    # to apply a new project config.ini file, they need to instead specify it in args (by adding a variable called config_file_path to 
    # the GHPython GHsDNA launcher component.
    sDNA = local_opts['options'].sDNA

    args_metas = {}
    args_options = {}
    args_tool_options = {}
    args_local_metas = {}

    for (arg_name, arg_val) in args_dict.items():  # local_metass() will be full of all our other variables.
        if arg_val != None:  # Unconnected input variables in a Grasshopper component are None.  
                         # No sDNA tool inputspec default, no metas and no options default is None.
                         #If None values are needed as specifiable inputs, we need to e.g. test ghenv for an input variable's connectedness
            if arg_name in metas._fields:      
                args_metas[arg_name] = arg_val
            elif arg_name in options._fields:   
                args_options[arg_name] = arg_val
            elif arg_name in local_opts[sDNA].get(name,empty_NT)._fields: 
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

    kwargs = dict(   dump_all_in_default_section = True
                    ,empty_lines_in_values = False
                    ,interpolation = None # For setup_config above
                    ,section_name = name # For override_namedtuple below
                    ,leave_as_strings = False 
                    ,strict = local_opts['metas'].typecheck_opts_namedtuples
                    ,check_types = local_opts['metas'].typecheck_opts_fields
                    ,add_in_new_options_keys = local_opts['metas'].add_in_new_options_keys
                    )

    if 'config_file_path' in args_metas: 
        config_file_reader = options_manager.setup_config(   args_metas['config_file_path'], **kwargs)
    else:
        config_file_reader = None 
    print('1.09 ')

    local_metas_overrides_list = [external_local_metas, config_file_reader, args_local_metas]
    local_metas = options_manager.override_namedtuple(  local_metas, local_metas_overrides_list, **kwargs ) 
    print('#1.1 local_metas == ' + str(local_metas))

    sub_args_dict = dict( metas=args_metas
                         ,options = args_options
                         ,name = args_tool_options
                         )

    overrides = lambda key : [external_opts.get(key,{}), config_file_reader, sub_args_dict.get(key, {})]
    if local_metas.sync_to_shared_global_opts:
        dict_to_update = opts 
    else:
        dict_to_update = local_opts
        if local_metas.read_from_shared_global_opts:
            overrides = lambda key : [opts.get(key,{})] + overrides(key)



    for key, val in dict_to_update.items():
        dict_to_update[key] = options_manager.override_namedtuple( val, overrides(key), **kwargs )
        #
        if local_metas.write_to_shared_global_opts and not local_metas.sync_to_shared_global_opts:
            opts[key] = options_manager.override_namedtuple( opts[key], dict_to_update[key], **kwargs )


                                                

    return local_metas


if 'logger' in globals() and isinstance(logger, wrapper_logging.logging.Logger): 
    pass
else:      
    logger = wrapper_logging.new_Logger(  __name__
                                        ,options.log_file
                                        ,options.logger_file_level
                                        ,options.logger_console_level
                                        )   # 'a' in Grasshopper to be added by Launcher 



def start_and_end_points(curve, rs): # curve : Rhino.Geometry.Curve https://developer.rhino3d.com/api/RhinoCommon/html/T_Rhino_Geometry_Curve.htm
    #type: (...)->list(list(float,3),list(float,3))
    return [list(rs.CurveStartPoint(curve)),list(rs.CurveEndPoint(curve))]

def pattern_match_key_names(x):
    #type: (str)-> str / None
    return match(options.rhino_user_text_key_pattern,x)

def write_to_shapefile_with_rhino_doc_as_default( my_iter 
                                                ,shp_file = options.shape_file_to_write_Rhino_data_to_from_GHsDNA # None is Hardcoded default val
                                                ,shape_mangler = start_and_end_points
                                                ,key_finder = lambda x : rs.GetUserText(x,None)
                                                ,key_matcher = pattern_match_key_names
                                                #,key_mangler = lambda x : options.rhino_user_text_key_format_str_to_read.format(name = x)
                                                #,value_mangler = rs.SetUserText
                                                ,value_demangler = rs.GetUserText
                                                ,shape = "POLYLINEZ"
                                                ,options = options
                                                ):

    if shp_file == None:
        shp_file = Rhino.RhinoDoc.ActiveDoc.Path[:-4] + options.shp_file_extension
                            # file extensions are actually optional in PyShp, but just to be safe and future proof we slice out '.3dm'
    return wrapper_pyshp.write_from_iterable_to_shapefile_writer(    my_iter 
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

def Read_Network_Links():
    try:
        ghdoc
    except:
        ghdoc = sc.doc
    sc.doc = Rhino.RhinoDoc.ActiveDoc # ActiveDoc may change on Macs - TODO: only call once or accept argument
    #
    #
    #############################################################################
    # Main import of rhino objects
    rhino_doc_curves = rs.ObjectsByType(4, select=False, state=0)
    return rhino_doc_curves

def Write_Links_Data_To_Shapefile():




    #output(options.uuid_length)

    OK, shp_filename, cached_fields, cached_user_data, cached_geometry = write_to_shapefile_with_rhino_doc_as_default()
    return OK, shp_filename

def Read_Links_Data_From_Shapefile(sDNA_output_shp_file, cached_geometry):
    cached_sDNA_fields, cached_sDNA_outputs = wrapper_pyshp.get_fields_and_records_from_shapefile( sDNA_output_shp_file 
                                                                                                  ,Rhino.RhinoDoc.ActiveDoc
                                                                                                  ,options
                                                                                                  )
    sDNA_output_field_names = [ x[0] for x in cached_sDNA_fields ]

    #Rhino_object_uuid_index = sDNA_output_field_names.index(options.uuid_shp_file_field_name)
    date_time_of_run = asctime()

    for rhino_obj, record in zip(cached_geometry ,cached_sDNA_outputs):
        existing_keys = rs.GetUserText(rhino_obj)
        for (output_val, sDNA_output_field_info) in zip(record, cached_sDNA_fields):
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

def Plot_Data_On_Links(cached_sDNA_fields, cached_geometry, cached_sDNA_outputs):
    sDNA_output_to_plot_index = 10 #sDNA_output_abbrevs.index('TPBtE') #sDNA_output_field_names.index(options.sDNA_output_abbrev_to_graph )
    output ("Plotting field == " + str(cached_sDNA_fields[sDNA_output_to_plot_index]))
    data_points = [x[sDNA_output_to_plot_index] for x in cached_sDNA_outputs]
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

    for rhino_obj, record in zip(cached_geometry ,cached_sDNA_outputs):
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

def main_sequence(ghenv, f_name, Geom, Data, opts, args):
    #type(class,bool,tuple(str)) -> WriteableFlushableList
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
    ###############################################################################
    # Python standard library imports                   
    #  
    from os.path import isdir, isfile, sep, normpath, join, split
    from importlib import import_module
    from collections import namedtuple
    from re import match
    from subprocess import call
    from time import asctime
    #
    ###############################################################################



    #for sub_folder in metas.modules_subdirectories:
    #    test_path = join(metas.current_working_dir, sub_folder)
    #    if isdir(test_path):
    #        sys.path += [test_path]
    #

    #options_manager = import_module_or_search_for_it('options_manager')
    from .custom_python_modules import options_manager
    #import options_manager

    ############################################################################################################
    #  Parse args
    #
    # change args in method to (Go,*args)
    args_metas = {}
    args_options = {}
    args_extras = {}
    for (input,val) in zip(ghenv.Component.Params.Input[1:], args):  # locals() will be full of all our other variables.
        if input.Name in metas._fields:
            args_metas[input.Name] = val
        elif input.Name in options._fields:
            args_options[input.Name] = val
        else:
            args_extras[input.Name] = val
    #GH_component_class_method_args = {input.Name : arg for (input,arg) in zip(ghenv.Component.Params.Input,args)}
    ############################################################################################################

    ############################################################################################################
    # Meta options options_manager.override logic and config file loading
    #
    


    config_path = metas.config_file_path  # Hardcoded default
    if 'config_file_path' in args_metas:  # Possible new one from function arguments
        config_path = args_metas['config_file_path'] # Primary meta.  # Override metas 4) -> 3), and options 3)-> 2)
        sys.path = [config_path] + sys.path
    from . import config
    #config = import_module_or_search_for_it('config')


    metas = options_manager.options_manager.override_namedtuple_with_dict(config.metas, metas, False, 'Metas')  # Override metas 5) -> 3) or 4) 
    metas = options_manager.options_manager.override_namedtuple_with_dict(args_metas, metas, False, 'Metas') # metas 1st options_manager.override 3) or 4) -> 1)
    config.metas = metas                                      # Share with custom modules
    #
    ############################################################################################################

    ############################################################################################################
    # Main options options_manager.override logic
    #
    options = options_manager.options_manager.override_namedtuple_with_dict(config.options, options, False, 'Options')  # options_manager.override options 5) -> 3) or 2)
    options = options_manager.options_manager.override_namedtuple_with_dict(args_options, options, False, 'Options') # options_manager.override options  3) or 2) -> 1)
    config.options = options                                        # Share with custom modules
    #
    ############################################################################################################

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
    from .third_party_python_modules import shapefile as shp
    #shp = import_module_or_search_for_it('shapefile')
    #output("options.uuid_length == " + str(options.uuid_length))
    #wrapper_pyshp = import_module_or_search_for_it('wrapper_pyshp')
    from .custom_python_modules import wrapper_pyshp
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
        return [list(rs.CurveStartPoint(curve)),list(rs.CurveEndPoint(curve))]
    #
    #
    #
    ############################################################################################################




    ############################################################################################################
    # GHsDNA GH component main process logic
    try:
        ghdoc
    except:
        ghdoc = sc.doc
    sc.doc = Rhino.RhinoDoc.ActiveDoc # ActiveDoc may change on Macs - TODO: only call once or accept argument
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
        return match(options.rhino_user_text_key_pattern,x)

    def write_to_shapefile_with_rhino_doc_as_default( my_iter = rhino_doc_curves 
                                                    ,shp_file = options.shape_file_to_write_Rhino_data_to_from_GHsDNA # None is Hardcoded default val
                                                    ,shape_mangler = start_and_end_points
                                                    ,key_finder = lambda x : rs.GetUserText(x,None)
                                                    ,key_matcher = pattern_match_key_names
                                                    #,key_mangler = lambda x : options.rhino_user_text_key_format_str_to_read.format(name = x)
                                                    #,value_mangler = rs.SetUserText
                                                    ,value_demangler = rs.GetUserText
                                                    ,shape = "POLYLINEZ"
                                                    ,options = options
                                                    ):

        if shp_file == None:
            shp_file = Rhino.RhinoDoc.ActiveDoc.Path[:-4] + options.shp_file_extension
                                # file extensions are actually optional in PyShp, but just to be safe and future proof we slice out '.3dm'
        return wrapper_pyshp.write_from_iterable_to_shapefile_writer(    my_iter 
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

    shp_filename, cached_fields, cached_user_data, cached_geometry = write_to_shapefile_with_rhino_doc_as_default()
    default_sDNA_prepped_shp_file_name = shp_filename[:-4] + options.prepped_shp_file_suffix + options.shp_file_extension

    def call_sDNA_prepare (shp_input_file = shp_filename
                          ,shp_output_file = default_sDNA_prepped_shp_file_name
                          ,options = options 
                          ):
        shp_output_file = wrapper_pyshp.get_unique_filename_if_not_overwrite(shp_output_file,options)
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
        shp_output_file = wrapper_pyshp.get_unique_filename_if_not_overwrite(shp_output_file,options)
        command =  options.python_exe + " -u " + '"' + options.sDNA_integral + '"' + " -i " + shp_input_file + " -o " + shp_output_file
        output(command)
        call( command)            
        return shp_output_file 

    sDNA_output_shp_file = call_sDNA_integral()

    #############################
    # TODO:  Write cached_fields, cached_user_data to the .3dm file as document user text, or even attribute_table_data in a local temp file containing a hash of the 
    # .3dm file, to speed up future calls of this function even from differetn python instances

    

    cached_sDNA_fields, cached_sDNA_outputs = wrapper_pyshp.get_fields_and_records_from_shapefile( sDNA_output_shp_file 
                                                                                                  ,Rhino.RhinoDoc.ActiveDoc
                                                                                                  ,options
                                                                                                  )
    sDNA_output_field_names = [ x[0] for x in cached_sDNA_fields ]

    #Rhino_object_uuid_index = sDNA_output_field_names.index(options.uuid_shp_file_field_name)
    date_time_of_run = asctime()

    for rhino_obj, record in zip(cached_geometry ,cached_sDNA_outputs):
        existing_keys = rs.GetUserText(rhino_obj)
        for (output_val, sDNA_output_field_info) in zip(record, cached_sDNA_fields):
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
    sDNA_output_to_plot_index = 10 #sDNA_output_abbrevs.index('TPBtE') #sDNA_output_field_names.index(options.sDNA_output_abbrev_to_graph )
    output ("Plotting field == " + str(cached_sDNA_fields[sDNA_output_to_plot_index]))
    data_points = [x[sDNA_output_to_plot_index] for x in cached_sDNA_outputs]
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

    for rhino_obj, record in zip(cached_geometry ,cached_sDNA_outputs):
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

    return True, '', None, None
#
###############################################################################


def list_contains(check_list, name, name_map):
    # type( MyComponent, list(str), str, dict(str, str) ) -> bool

    return name in check_list or (name in name_map and name_map[name] in check_list)

def no_name_clashes(name_map, list_of_names_lists):
    #type( MyComponent, dict(str, str), list(str) ) -> bool

    num_names = sum(len(names_list) for names_list in list_of_names_lists)
    super_set = set(name for names_list in list_of_names_lists for name in names_list)
    if 'options' in super_set or 'metas' in super_set:
        return False
    return num_names == len(super_set) and all([x == name_map[x] for x in name_map if x in super_set])


tools_dict=dict( Read_Network_Links = Read_Network_Links
                ,Write_Links_Data_To_Shapefile = Write_Links_Data_To_Shapefile
                ,Read_Links_Data_From_Shapefile = Read_Links_Data_From_Shapefile
                ,Plot_Data_On_Links = Plot_Data_On_Links
                ,main_sequence = main_sequence
                )

support_component_names = tools_dict.keys()
#support_component_names = [  'Read_Network_Links'
#                            ,'Write_Links_Data_To_Shapefile'
#                            ,'Read_Links_Data_From_Shapefile'
#                            ,'Plot_Data_On_Links'
#                            ]
#
#                   
#
special_names =           [  'sDNA_general'
                            ]

def update_component_tool(nick_name, tool_name, local_opts):   
    # type(str, dict, dict) -> str, dict, function

    
     # Abbreviations take priority in name_map.get(n,n) if there is a clash.

    #if not isinstance(nick_names, list):
    #    nick_names = [nick_names] 
    #for nick_name in nick_names:
    #global opts, get_syntax_dict, input_spec_dict - access and mutate mutable shared globals via parent module namespace
    sDNA, UISpec = local_opts['options'].sDNA, local_opts['options'].UISpec
    # 
    if not (nick_name in opts[sDNA] and tool_name in get_syntax_dict[sDNA]):  
        # input_spec is only used to supply key/field names and 
        # initialise default values in opts[nick_name], i.e. never used
        # again outside this function.
        if hasattr(UISpec,tool_name):
            input_spec = getattr(UISpec,tool_name).getInputSpec()
            get_syntax = getattr(UISpec,tool_name).getSyntax
            #input_spec_dict[sDNA][tool_name] = input_spec    # Only ever referred to here.  
            get_syntax_dict[sDNA][tool_name] = get_syntax
            defaults_dict = {varname : default for (varname, 
                              displayname, datatype, filtr, default, required) in input_spec}
            opts[sDNA][nick_name] = options_manager.make_nested_namedtuple(defaults_dict,nick_name)
                                                            # Tool options are stored per nickname
                                                            # to allow components to be customised: 
                                                            # set multiple nicknames for the same one.
                                                            # Each one with the same nick name has its
                                                            # own options.
        else:
            opts[sDNA][nick_name] = empty_NT
    return #tool_name

#update_component_tool(nick_name, tool_name, opts)

class FakeProgress():
    setInfo = output
    def setPercentage(self,*args):
        pass

def fill_in_invalid_file_names(  args_dict
                                ,tool_name
                                ,opts_at_call
                                ,keys =['input','output']
                                ,is_invalid=lambda x : not isinstance(x,str) or x !='' and not x.isspace() # isfile
                                ,new_names = None
                                ,unique_file_name_func = None ):
    #type (dict, str, list, function, list, function) -> dict   
    if new_names == None:
        new_name = Rhino.RhinoDoc.ActiveDoc.Path.rpartition('.')[0] 
        output_suffix = opts_at_call['options'].prepped_shp_file_suffix if tool_name == 'sDNAPrepare' else opts_at_call['options'].output_shp_file_suffix
        new_names = {'input' : new_name + opts_at_call['options'].shp_file_extension,
                     'output' : new_name + output_suffix + opts_at_call['options'].shp_file_extension}
    if unique_file_name_func == None:
        unique_file_name_func = wrapper_pyshp.get_unique_filename_if_not_overwrite

    assert is_invalid('')
    for key in keys:
        if is_invalid(args_dict.get(key,'')):    # '' Needs to be invalid
            args_dict[key] = unique_file_name_func(new_names[key])
    return args_dict




def component_names_wrapper(name_map): 
    def return_GHsDNA_component_names_list(ghenv, f_name, Geom, Data, local_opts, args):
        UISpec = local_opts['options'].UISpec
        
        sDNA_tool_names = [Tool.__name__ for Tool in UISpec.get_tools()]
        names_list = special_names + support_component_names + sDNA_tool_names
        clash_test_passed = no_name_clashes( name_map,  [support_component_names, special_names, sDNA_tool_names] )


        if not clash_test_passed:
            output('Component name/abbrev clash.  Rename component or abbreviation. ','WARNING') 
        assert clash_test_passed
                                                                # No nick names allowed that are 
                                                                # a different tool's full name.
                                                                # The nicknamed one takes priority 
                                                                # in name_map.get(n,n)
        def is_tool(name):
            return name in support_component_names + special_names or hasattr(UISpec, name)

        tools_defined= {name : is_tool(name) for name in names_list}

    
        if not all(tools_defined.values()):
            undefined_names_with_no_Tools = [name for name in names_list if not tools_defined[name]]
            output('Invalid tool names: ' + ' '.join(str(undefined_names_with_no_Tools)) + 
                    '.  Adjust nick_names or name_map to point to known functions.  ','CRITICAL') 
        assert all(tools_defined.values())
        
        valid_name_map_vals = {key : is_tool(val) or (isinstance(val, list) 
                                and all([is_tool(name) for name in val])) for key, val in name_map.items()}

        if not all(valid_name_map_vals.values()):
            vals_in_name_map_with_no_Tools = [key for key, val in valid_name_map_vals if not val]
            output('Invalid name_map: ' + ' '.join(str(vals_in_name_map_with_no_Tools)) + 
                    '.  Adjust name_map to point to known functions or lists thereof.  ','CRITICAL')
        assert all(valid_name_map_vals.values())
        #return special_names + support_component_names + sDNA_tool_names, None, None, None, self.a 
        return True, None, None, names_list, ' Returned component names OK '
    return return_GHsDNA_component_names_list

def get_specific_tool(tool_name, nick_name, name_map, local_opts):
    # type(str) -> function
    # global get_syntax_dict  # access shared global cache via parent module namespace.  Not mutated here (done already in update_component_tool).
    UISpec = local_opts['options'].UISpec
    if not tool_name in tools_dict:
        # Make sure all support functions are in tools_dict!      
        #  
        #if tool_name in support_component_names:
        #    def support_tool_wrapper(ghenv, f_name, Geom, Data, opts, args):  
        #        return globals()[tool_name](ghenv, f_name, Geom, Data)
        #    tools_dict[tool_name] = support_tool_wrapper   
            #
            #
        if hasattr(UISpec, tool_name):
            def run_sdna_wrapper(ghenv, f_name, Geom, Data, opts_at_call, args):
                #type(Class, dict(namedtuple), str, Class, DataTree)-> Boolean, str
                #global opts # - deliberate to access global caches
                sDNA, UISpec, run = opts_at_call.sDNA, opts_at_call.UISpec, opts_at_call.run
                
                syntax = get_syntax_dict[sDNA][tool_name](opts_at_call[nick_name]._asdict())   #opts[nick_name] was initialised to defaults in UISpec
                
                if opts_at_call['options'].supply_sDNA_file_names:
                    syntax = fill_in_invalid_file_names(syntax, tool_name, opts_at_call)

                return_code = run.runsdnacommand(    syntax
                                                    ,sdnapath = dirname(UISpec.__file__)  #opts['options'].sDNA_UISpec_path
                                                    ,progress = FakeProgress()
                                                    ,pythonexe = opts_at_call['options'].python_exe
                                                    ,pythonpath = None)   # TODO:  Work out if this is important or not! 
                                                                        # os.environ["PYTHONPATH"] not found in Iron Python
                return return_code==0, getattr(opts_at_call[nick_name],'output')
            tools_dict[tool_name] = run_sdna_wrapper
            #
            # #
            # # self.GHsDNA.tools.parse_options()
            # map_options_to_sDNA_tool
            # runsdnacommand.runsdnacommand(getattr(sDNAUISpec,self.name_map.get(n,n))
                                        # Abbreviations take priority if there is a clash.
            # return ran_OK, output_file_path, Geometry, Data, a

            #return True, None, None, None, "Manaa manaa"


        elif tool_name=='Python':   # Dev tool to build launcher comoponents for the other tools with, via metahopper.
            #return True, None, None, None, "Manaa manaa.  do doo do do do. "  
            #return True, None, None, None, self.special_names + self.support_component_names +  [x+'  :  '+y for x,y in zip(sDNA_tool_names,sDNA_tool_categories)]
            tools_dict[tool_name] = component_names_wrapper(name_map)
            #
            #
        elif tool_name=='Main_Sequence': 
            tools_dict[tool_name] = main_sequence
        else:
            tools_dict[tool_name] = lambda *args :  (True,) + args
        # Memoising ends.
        tools_dict[tool_name] = [ tools_dict[tool_name] ]
    return tools_dict[tool_name] 

def tool_factory(nick_name, name_map, local_opts):  
    #type( list or str, dict ) -> 

    #sDNA, UISpec, run = local_opts['options'].sDNA, local_opts['options'].UISpec, local_opts['options'].run

    #global tools_dict # mutable - access through normal parent module namespace
    if nick_name not in tools_dict:
        tools =[]

        map_result = name_map.get(nick_name, nick_name)
        map_result = map_result if isinstance(map_result, list) else [map_result]
                
        for name in map_result:
            if name in name_map:
                tools += tool_factory(nick_name, name_map, local_opts)
            elif name in special_names:
                def tool_factory_wrapper(ghenv, f_name, Geom, Data, opts_at_call, args):
                    return tool_factory(opts_at_call['options'].tool_name, name_map, opts_at_call)(ghenv, f_name, Geom, Data, opts_at_call, args)
                tools += tools_dict.setdefault(name, [tool_factory_wrapper])
            #    n = args['tool_name']   # This isn't necessarily universal in future.  TODO: Write extra code to handle 
                                        # other special cases if any others crop up.
            elif name in support_component_names + ['Python']:
                update_component_tool(nick_name, name, local_opts)
                tools += tools_dict.setdefault(name,  get_specific_tool(name, nick_name, name_map, local_opts)  )
        tools_dict[nick_name] = tools
    return tools_dict[nick_name] 

#tool = tool_factory(tool_name)




###############################################################################
#Main root process
#
from os.path import isdir, isfile, sep, normpath, join, split
if      '__file__' in dir(__builtins__)  and  __name__ in __file__ and '__main__' not in __file__ and '<module>' not in __file__:                     
    # Assert:  We're in a module!
    pass
else:
    pass



    ###############################################################################
    # Functions (hidden from module imports)
    #
    ###############################################################################
"""     ap=ArgumentParser()
    lower_case_hex_digit_pattern = r'[a-f|\d]'
    uuid_pattern_no_hyphens = lower_case_hex_digit_pattern + r'{32}'
    grasshopper_compiled_component___name___pattern = r'\APython_'+uuid_pattern_no_hyphens + r'\Z'
    # This regex will match __test_name__='Python_d396a1fb0e6441508fa6555b4d306ff5' for example
    #TODO: Test for Rhinoscript (not in GH, BSOC?)
    # we could assert ap.prog == 'GHsDNA.py' but perhaps the user has renamed this file.
    #
    if (__name__ == '__main__' and ap.prog == '') or match(grasshopper_compiled_component___name___pattern,__name__):
        logger.info("We're neither ina  module nor being run as a script.  We're probably in a Grasshopper component.  ")
        main_sequence(True)
 
    else:
        #running in a script        
        logger.info('First if block.  Running module as script e.g. from the command line')

    if __name__ == '__main__':  # Name is still '__main__' in an uncompiled grasshopper component as well as in scripts.
        if ap.prog != '':   
            logger.info('Second if block.  Running module as script e.g. from the command line')
            #ap.add_argument('Rhino_file',help='The .3dm file defining the spatial network',type=str)
            #ap.add_argument('output_file',help='The name of the .shp file (suite) to write the results from sDNA to',type=str)
            #args=ap.parse_args()
            #TODO Use command line args to run test definitions, e.g. if '--test True'
            test_cases = import_module_or_search_for_it('test_cases')
        else:  
            pass # code to run only if in an uncompiled grasshopper component
                # in an uncompiled grasshopper component ap.prog == '' (also when imported as a module)
            logger.info('Running module in an uncompiled grasshopper component (plain source in a python component in a .gh file)')
    else:

        if match(grasshopper_compiled_component___name___pattern,__name__):
            logger.info('Running module in a compiled grasshopper component (in a .ghpy file within a .gh file)')
            pass
            # code to run only if in a compiled grasshopper component
        else:
            pass         
            logger.error(  'Running module in a module import.  __name__ == '
                         + __name__ + 'inside an if block that checked we are not in a module.  '
                         + '__file__ == ' + __file__)
            #code to run only if we're imported as a module """
###############################################################################



"""         col_max = rs.CreateColor(*rgb_max)
        col_min = rs.CreateColor(*rgb_min) """

"""         col1 = rs.CreateColor(0, 0, 102)
        output(col1)
        output(dir(col1)) """


""" AngD 	Angular Distance in Radius
BtA 	Betweenness Angular
BtC 	Betweenness Custom
BtE 	Betweenness Euclidean
BtH 	Betweenness Hybrid
Conn 	Connectivity in Radius
DivA 	Diversion Ratio in Radius Angular
DivC 	Diversion Ratio in Radius Custom
DivE 	Diversion Ratio in Radius Euclidean
DivH 	Diversion Ratio in Radius Hybrid
HMb 	Line Hybrid Metric (backwards direction)
HMf 	Line Hybrid Metric (forwards direction)
HullA 	Convex Hull Area
HullB 	Convex Hull Bearing of Maximum Radius
HullP 	Convex Hull Perimeter
HullR 	Convex Hull Maximum (Crow Flight) Radius
HullSI 	Convex Hull Shape Index
Jnc 	Junctions in Radius
LAC 	Line Angular Curvature
LBear 	Line Bearing
LConn 	Line Connectivity
Len 	Length in Radius
Lfrac 	Link fraction (for current line)
LLen 	Line Length
Lnk 	Links in Radius
LSin 	Line Sinuosity
MAD 	Mean Angular Distance in Radius
MCD 	Mean Custom Distance in Radius
MCF 	Mean Crow Flight Distance in Radius
MED 	Mean Euclidean Distance in Radius
MGLA 	Mean Geodesic Length in Radius Angular
MGLC 	Mean Geodesic Length in Radius Custom
MGLE 	Mean Geodesic Length in Radius Euclidean
MGLH 	Mean Geodesic Length in Radius Hybrid
MHD 	Mean Hybrid Distance in Radius
NQPDA 	Network Quantity Penalized by Distance in Radius Angular
NQPDC 	Network Quantity Penalized by Distance in Radius Custom
NQPDE 	Network Quantity Penalized by Distance in Radius Euclidean
NQPDH 	Network Quantity Penalized by Distance in Radius Hybrid
SAD 	Sum of Angular Distance in Radius *
SCD 	Sum of Custom Distance in Radius *
SCF 	Sum of Crow Flight Distance in Radius *
SED 	Sum of Euclidean Distance in Radius *
SGLA 	Sum of Geodesic Length in Radius Angular *
SGLC 	Sum of Geodesic Length in Radius Custom *
SGLE 	Sum of Geodesic Length in Radius Euclidean *
SGLH 	Sum of Geodesic Length in Radius Hybrid *
SHD 	Sum of Hybrid Distance in Radius *
TPBtA 	Two Phase Betweenness Angular
TPBtC 	Two Phase Betweenness Custom
TPBtE 	Two Phase Betweenness Euclidean
TPBtH 	Two Phase Betweenness Hybrid
TPDA 	Two Phase Destination Angular
TPDC 	Two Phase Destination Custom
TPDE 	Two Phase Destination Euclidean
TPDH 	Two Phase Destination Hybrid
Wl 	Weighted by Length (as opposed to Link)
Wp 	Weighted by Polyline (as opposed to Link)
Wt 	Weight in Radius """



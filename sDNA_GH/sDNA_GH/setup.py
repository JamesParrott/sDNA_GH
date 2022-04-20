#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys, os
from collections import namedtuple, OrderedDict

import Rhino
import scriptcontext as sc

from .custom.options_manager import (load_toml_file
                                    ,make_nested_namedtuple     
                                    ,load_ini_file                             
                                    ,override_namedtuple  
                                    ,get_namedtuple_etc_from_class      
                                    )
from .custom import logging_wrapper
from .launcher import Output, Debugger, load_modules
from .custom.helpers.funcs import (first_item_if_seq
                                  ,valid_re_normalisers
                                  )
from .custom.gdm_from_GH_Datatree import (convert_Data_tree_and_Geom_list_to_gdm
                                         ,override_gdm_with_gdm
                                         ,convert_dictionary_to_data_tree_or_lists
                                         )
from .custom.skel.basic.smart_comp import SmartComponent, custom_retvals
from .custom.skel.basic.ghdoc import ghdoc                                       
from .custom.skel.tools.inserter import insert_tool
from .custom.skel.tools.runner import run_tools, tools_dict
from .custom.skel.tools.name_mapper import tool_factory
from .custom.skel.add_params import add_tool_params
from .custom.tools import (sDNA_GH_Tool
                          ,GetObjectsFromRhino
                          ,ReadUsertext
                          ,WriteShapefile
                          ,ReadShapefile
                          ,WriteUsertext
                          ,BakeUsertext
                          ,ParseData
                          ,RecolourObjects
                          ,sDNAWrapper
                          )
from .dev_tools.dev_tools import ReturnComponentNames, sDNA_GH_Builder



output = Output()
debug = Debugger(output)



class HardcodedMetas(): 
    config = os.path.join(os.path.dirname(  os.path.dirname(__file__)  )
                         ,r'config.toml'  
                         )
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
                    # after loading, assert opts['metas'].sDNA_path == os.path.dirname(opts['options'].sDNAUISpec.__file__)
    #sDNA_UISpec_path = r'C:\Program Files (x86)\sDNA\sDNAUISpec.py'
    #sDNA_search_paths = [sDNA_UISpec_path, 
    sDNA_search_paths  = [r'C:\Program Files (x86)\sDNA']
    sDNA_search_paths += [os.path.join(os.getenv('APPDATA'),'sDNA')]
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
                        ,TestPlot = ['get_Geom', 'read_shapefile', 'parse_data', 'recolour_objects']
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
    shp_file_to_write_to = r'C:\Users\James\Documents\Rhino\Grasshopper\tmp.shp' # None means Rhino .3dm filename is used.
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
    create_new_geom = False
    max_new_UserText_keys_to_make = 20
    #
    #
    rhino_user_text_key_format_str_to_read = 'sDNA input name={name} type={fieldtype} size={size}'  #30,000 characters tested!
    sDNA_output_user_text_key_format_str_to_read = 'sDNA output={name} run time={datetime}'  #30,000 characters tested!
    ####################################################################################
    #sDNA
    Default_sDNA_GH_file_path = __file__
    overwrite_input_shapefile = False
    auto_get_Geom = True
    auto_read_Usertext = True
    auto_write_new_Shp_file = True
    auto_read_Shp = True
    auto_parse_data = True
    auto_plot_data = True
    #Plotting results
    field = 'BtEn'
    plot_max = None
    plot_min = None
    sort_data = True
    base = 10 # base of log and exp spline, not of number representations
    re_normaliser = 'linear' 
    assert re_normaliser in valid_re_normalisers 
    class_bounds = [None] #[2000000, 4000000, 6000000, 8000000, 10000000, 12000000]
    leg_extent = None  # [xmin, ymin, xmax, ymax]
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



class HardcodedLocalMetas():
    sync_to_module_opts = True    
    read_from_shared_global_opts = True
    nick_name = ''


# Pre Python 3.6 the order of an OrderedDict isn't necessarily that of the 
# arguments in its constructor so we build our options and metas namedtuples
# from a class, to avoid re-stating the order of the keys.



default_metas = get_namedtuple_etc_from_class(HardcodedMetas, 'Metas')
default_options = get_namedtuple_etc_from_class(HardcodedOptions, 'Options')
default_local_metas = get_namedtuple_etc_from_class(HardcodedLocalMetas, 'LocalMetas')

empty_NT = namedtuple('Empty','')(**{})

module_opts = OrderedDict( metas = default_metas
                         ,options = default_options
                         )                
           

debug(module_opts['options'].message)



def get_path(opts = module_opts, inst = None):
    #type(dict, type[any]) -> str
    #refers to `magic' global ghdoc so needs to 
    # be in module scope (imported above)
    
    path = Rhino.RhinoDoc.ActiveDoc.Path
                    
    if not isinstance(path, str) or not os.path.isfile(path):
        try:
            path = ghdoc.Path
        except:
            try:
                path = inst.ghdoc.Path 
            except:
                try:
                    path = sc.doc.Path
                except:
                    path = None
        finally:
            if not path:
                path = opts['options'].Default_sDNA_GH_file_path
    
    return path



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
        # main options update function).  So we store 
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

    if (args_metas and 
        'config' in args_metas and 
        os.path.isfile(args_metas['config'])): 
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
        debug('No valid config file in args.  ' + str(args_metas))
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

if os.path.isfile(default_metas.config):
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

possible_pythons = (os.path.join(folder, python) for folder in folders for python in pythons)

while not os.path.isfile(module_opts['options'].python_exe):
    module_opts['options']._replace(python_exe = next(possible_pythons))

assert os.path.isfile(module_opts['options'].python_exe)

if not hasattr(sys.modules['sDNA_GH'], 'logger'):  # TODO.  Right logger name? 'sDNA_GH.tools'
    
    logs_directory = os.path.join(os.path.dirname( get_path(module_opts) )
                                 ,module_opts['options'].logs_subdir_name
                                 )

    if not os.path.isdir(logs_directory):
        os.mkdir(logs_directory)

    # wrapper_logging.logging.shutdown() # Ineffective in GH :(


    logger = logging_wrapper.new_Logger('sDNA_GH'
                                       ,os.path.join(logs_directory, module_opts['options'].log_file)
                                       ,module_opts['options'].logger_file_level
                                       ,module_opts['options'].logger_console_level
                                       ,None # custom_file_object 
                                       ,module_opts['options'].logger_custom_level
                                       )


    output.set_logger(logger) # Flushes cached log messages to above handlers

    debug('Logging set up in sDNA_GH package ')



####################################################################################################################


#
# 



                

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
                ,'class_bounds'
                )

#
do_not_remove += default_metas._fields
do_not_remove += default_options._fields
do_not_remove += default_local_metas._fields
#########################################################


get_Geom = GetObjectsFromRhino()
read_Usertext = ReadUsertext()
write_shapefile = WriteShapefile()
read_shapefile = ReadShapefile()
write_Usertext = WriteUsertext()
bake_Usertext = BakeUsertext()
parse_data = ParseData()
recolour_objects = RecolourObjects()
return_component_names = ReturnComponentNames()
build_components = sDNA_GH_Builder()



tools_dict.update(get_Geom = get_Geom
                 ,read_Usertext = read_Usertext
                 ,write_shapefile = write_shapefile
                 ,read_shapefile = read_shapefile
                 ,write_Usertext = write_Usertext
                 ,bake_Usertext = bake_Usertext
                 ,parse_data = parse_data
                 ,recolour_objects = recolour_objects 
                 ,Python = return_component_names
                 ,Build_components = build_components
                 )

def cache_sDNA_tool(compnt
                   ,mapped_name
                   ,name_map
                   ,tools_dict
                   ):
    sDNA_tool = sDNAWrapper(mapped_name, compnt.opts, compnt.local_metas)
    tools_dict.setdefault(mapped_name
                         ,sDNA_tool
                         )
    sDNA = compnt.opts['metas'].sDNA
    compnt.do_not_remove += tuple(sDNA_tool.tool_opts[sDNA]._fields)   # TODO Add in to update sDNA

            



sDNA_GH_tools = list(tools_dict.values())


# def component_decorator( BaseClass
#                         ,ghenv
#                         ,nick_name = 'Self_test'
#                         ):
#     #type:(type[type], str, object) -> type[type]
class sDNA_GH_Component(SmartComponent):

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
    do_not_remove = do_not_remove
    

    def auto_insert_tools(self, tools = None, Params = None):
        #type(type[any], list) -> None
        if tools is None:
            tools = self.my_tools
        tools = tools[:] if isinstance(tools, list) else [tools]

        if Params is None:
            Params = self.Params

        options = self.opts['options']

        metas = self.opts['metas']

        name_map = metas.name_map
        
        debug('Inserting tools... ')


        # if options.auto_write_new_Shp_file and (
        #     options.overwrite_input_shapefile 
        #     or not os.path.isfile(input_file))


        if options.auto_write_new_Shp_file:
            tools = insert_tool('before'
                               ,tools
                               ,Params
                               ,tool_to_insert = write_shapefile
                               ,is_target = lambda tool : tool.__class__ == sDNAWrapper
                               ,not_a_target = sDNA_GH_tools
                               ,tools_dict = tools_dict
                               ,name_map = name_map
                               )

        if options.auto_read_Usertext:
            tools = insert_tool('before'
                               ,tools
                               ,Params
                               ,tool_to_insert = read_Usertext
                               ,is_target = lambda tool : tool == write_shapefile
                               ,not_a_target = []
                               ,tools_dict = tools_dict
                               ,name_map = name_map
                               )   

        if options.auto_get_Geom:
            tools = insert_tool('before'
                               ,tools
                               ,Params
                               ,tool_to_insert = get_Geom
                               ,is_target = lambda tool : tool == read_Usertext
                               ,not_a_target = []
                               ,tools_dict = tools_dict
                               ,name_map = name_map
                               )   

        if options.auto_read_Shp:
            tools = insert_tool('after'
                               ,tools
                               ,Params
                               ,tool_to_insert = read_shapefile
                               ,is_target = lambda tool : tool.__class__ == sDNAWrapper
                               ,not_a_target = sDNA_GH_tools
                               ,tools_dict = tools_dict
                               ,name_map = name_map
                               )
        
        # if options.auto_parse_data:
        #     tools = insert_tool(self
        #                        ,'after'
        #                        ,tools
        #                        ,Params
        #                        ,parse_data
        #                        ,lambda tool : tool == read_shapefile
        #                        ,[]
        #                        )     
        
        
        if options.auto_plot_data: # already parses if no colours
            tools = insert_tool('after'                
                               ,tools
                               ,Params
                               ,tool_to_insert = recolour_objects
                               ,is_target = lambda tool : tool == read_shapefile #parse_data
                               ,not_a_target = []
                               ,tools_dict = tools_dict
                               ,name_map = name_map
                               ) 
                                          
        return tools



    def update_Params(   self
                        ,Params = None
                        ,tools = None
                        ):
        #type(type[any], type[any, list]) -> type[any]

        if Params is None:
            Params = self.Params
            # If this is tried before __init__ has finished .Params may not be
            # there yet.  But it is still available at ghenv.Component.Params

        if tools is None:
            tools = self.tools


        debug("Updating Params: " + str(tools))
        return add_tool_params(Params
                              ,tools
                              ,do_not_add
                              ,do_not_remove
                              ,wrapper = self.script
                              )


    def update_tools(self, nick_name = None):
        #type(type[any], str) -> type[any]

        if nick_name is None:
            nick_name = self.local_metas.nick_name

        tools = tool_factory(self
                            ,nick_name
                            ,self.opts['metas'].name_map
                            ,tools_dict
                            ,cache_sDNA_tool
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
            new_name = self.Attributes.Owner.NickName 
            # If this is run before __init__ has run, there is no 
            # Attributes attribute yet (ghenv.Component can be used instead).


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
            debug('Path sDNAUISpec imported from == ' + path)
            self.opts['metas'] = self.opts['metas']._replace(    sDNA = self.sDNA
                                                                ,sDNA_path = path 
                                                            )
            self.opts['options'] = self.opts['options']._replace(  sDNAUISpec = self.sDNAUISpec
                                                                    ,run_sDNA = self.run_sDNA 
                                                                )  

            sDNA_path = os.path.dirname(self.sDNAUISpec.__file__)
            assert self.opts['metas'].sDNA_path == sDNA_path                                                                  






    def __init__(self, *args, **kwargs):
        debug('Calling parent initialiser')
        SmartComponent.__init__(self, *args, **kwargs)
        self.load_modules = load_modules
        self.ghdoc = ghdoc
        self.update_sDNA() 




    def script(self, **kwargs):        
        # update_Params is called from inside this method, so the input Params 
        # supplying the args will not updated until after they have been read.
        # If this method is not intended to crash on a missing input param,
        # it needs to accept anything (or a lack thereof) to run in the meantime
        # until the params can be updated.  kwargs are perfect for this.
        debug('self.script started... \n')
        debug(kwargs)

        go = first_item_if_seq(kwargs.get('go', False), False) 
             # Input Params set 
             # to list acess so
             # strip away outer 
             # list container
        Data = kwargs.get('Data', None)
        Geom = kwargs.get('Geom', None)

        if 'file' in kwargs:
            kwargs['f_name'] = first_item_if_seq(kwargs['file'], '')
        elif 'f_name' not in kwargs:
            kwargs['f_name'] = ''
        else:
            kwargs['f_name'] = first_item_if_seq(kwargs['f_name'], '')

        external_opts = first_item_if_seq(kwargs.pop('opts', {}), {})
        external_local_metas = first_item_if_seq(kwargs.pop('local_metas', empty_NT), empty_NT)
        debug(external_opts)

        gdm = first_item_if_seq(kwargs.get('gdm', {}))

        debug('gdm from start of RunScript == ' + str(gdm)[:50])
        #print('#1 self.local_metas == ' + str(self.local_metas))
        
        if self.update_name() == 'Name updated':
            nick_name = self.local_metas.nick_name
            if (nick_name.lower()
                            .replace('_','')
                            .replace(' ','') == 'sdnageneral'
                and 'tool' in kwargs):
                nick_name = kwargs['tool']
            self.my_tools = self.update_tools(nick_name)
        
        self.tools = self.auto_insert_tools(self.my_tools, self.Params)  
                # Other components may mean self.tools needs extra tools adding or /removing
                # but this could - annoy many users.  TODO!  Get early feedback!
        #self.Params = 
        self.update_Params()#self.Params, self.tools)

        
        synced = self.local_metas.sync_to_module_opts
        old_sDNA = self.opts['metas'].sDNA

        self.local_metas = override_all_opts(args_dict = kwargs
                                            ,local_opts = self.opts # mutated
                                            ,external_opts = external_opts 
                                            ,local_metas = self.local_metas 
                                            ,external_local_metas = external_local_metas
                                            )

        kwargs['opts'] = self.opts
        kwargs['l_metas'] = self.local_metas

        debug('Opts overridden....    ')
        debug(self.local_metas)
        #debug('options after override in script == ' + str(self.opts['options']))
        
        if (self.opts['metas'].auto_update_Rhino_doc_path 
            or not os.path.isfile(self.opts['options'].Rhino_doc_path) ):

            path = get_path(self.opts, self)

            self.opts['options'] = self.opts['options']._replace( Rhino_doc_path = path )

        if self.opts['metas'].allow_components_to_change_type: 
            
            if self.local_metas.sync_to_module_opts != synced:
                if self.local_metas.sync_to_module_opts:
                    self.opts = module_opts #resync
                else:
                    self.opts = self.opts.copy() #desync
                    #
                    #
                    # TODO: option so make module_opts = self.opts
                    # Write but not read?  Wouldn't such a component
                    # be synced anyway, with all others on read only?

            if self.opts['metas'].sDNA != old_sDNA:
                self.update_sDNA()
                #self.Params = 
                self.update_Params()#self.Params, self.tools)

        debug(go)

        if go == True: 
            assert isinstance(self.tools, list)

            debug('my_tools == '
                    +str(self.tools)
                    )

            geom_data_map = convert_Data_tree_and_Geom_list_to_gdm(Geom
                                                                  ,Data
                                                                  )
            
            debug('type(geom_data_map) == '
                 +str(type(geom_data_map))
                 )
            

            gdm = override_gdm_with_gdm(gdm
                                       ,geom_data_map
                                       ,self.opts['options'].merge_Usertext_subdicts_instead_of_overwriting
                                       )

            debug('After merge type(gdm) == ' 
                    +str(type(gdm))
                    )                
            
            debug('After merge gdm == ' 
                    +str(gdm.items()[:3])
                    +' ...'
                    )
            kwargs['gdm'] = gdm

            ##################################################################
            ret_vals_dict = run_tools(self.tools, kwargs)
            ##################################################################
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
            if 'f_name' in ret_vals_dict:
                ret_vals_dict['file'] = ret_vals_dict['f_name']
            ret_vals_dict['opts'] = [self.opts.copy()]
            ret_vals_dict['l_metas'] = self.local_metas #immutable
            ret_vals_dict['OK'] = ret_vals_dict.get('retcode', 0) == 0


            tool_opts = self.opts
            nick_name = self.local_metas.nick_name
            sDNA = self.opts['metas'].sDNA
            if nick_name in self.opts:
                tool_opts = self.opts[nick_name]
                if isinstance(tool_opts, dict):
                    tmp = {}
                    for tool_name in tool_opts:
                        tmp.update(tool_opts[tool_name]._asdict())
                    tool_opts = tmp
        else:
            debug('go was not == True')
            ret_vals_dict = {}
            ret_vals_dict['OK'] = False
            tool_opts = {}
        retval_names = [Param.Name for Param in self.Params.Output]
        logger.debug('Returning from self.script ')
        return custom_retvals(retval_names
                             ,[  ret_vals_dict
                              ,  self.opts['metas']
                              ,  self.opts['options']
                              ,  self.local_metas
                              ,  tool_opts
                              ]
                             ,return_locals = True
                             )
    script.input_params = sDNA_GH_Tool.params_list(['go', 'opts'])
    script.output_params = sDNA_GH_Tool.params_list(['OK', 'opts'])



# def component_decorator( BaseClass
#                         ,ghenv
#                         ,nick_name = 'Self_test'
#                         ):
#     #type:(type[type], str, object) -> type[type]
#     class sDNA_GH_Component(BaseClass):

#         # Options from module, from defaults and installation config.toml
#         opts = module_opts  
#         local_metas = default_local_metas   # immutable.  controls syncing /
#                                             # desyncing / read / write of the
#                                             # above (opts).
#                                             # Although local, it can be set on 
#                                             # groups of components using the 
#                                             # default section of a project 
#                                             # config.ini, or passed as a
#                                             # Grasshopper parameter between
#                                             # components.

#         #sDNA_GH_path = sDNA_GH_path
#         #sDNA_GH_package = sDNA_GH_package

#         def remove_component_output(self, name):
#             for param in self.Params.Output:
#                 if param.NickName == name:
#                     self.Params.UnregisterOutputParam(param)
        

#         def auto_insert_tools(self, tools, Params):
#             #type(type[any], list) -> None
#             if tools is None:
#                 tools = self.my_tools
#             tools = tools[:] if isinstance(tools, list) else [tools]

#             options = self.opts['options']
            



#             # if options.auto_write_new_Shp_file and (
#             #     options.overwrite_input_shapefile 
#             #     or not os.path.isfile(input_file))

#             if options.auto_write_new_Shp_file:
#                 tools = insert_tool(self
#                                    ,'before'
#                                    ,tools
#                                    ,Params
#                                    ,write_shapefile
#                                    ,lambda tool : tool.__class__ == sDNAWrapper
#                                    ,sDNA_GH_names
#                                    )
#             if options.auto_read_Usertext:
#                 tools = insert_tool(self
#                                    ,'before'
#                                    ,tools
#                                    ,Params
#                                    ,read_Usertext
#                                    ,lambda tool : tool == write_shapefile
#                                    ,[]
#                                    )   

#             if options.auto_get_Geom:
#                 tools = insert_tool(self
#                                    ,'before'
#                                    ,tools
#                                    ,Params
#                                    ,get_Geom
#                                    ,lambda tool : tool == read_Usertext
#                                    ,[]
#                                    )   

#             if options.auto_read_Shp:
#                 tools = insert_tool(self
#                                    ,'after'
#                                    ,tools
#                                    ,Params
#                                    ,read_shapefile
#                                    ,lambda tool : tool.__class__ == sDNAWrapper
#                                    ,sDNA_GH_names
#                                    )
            
#             # if options.auto_parse_data:
#             #     tools = insert_tool(self
#             #                        ,'after'
#             #                        ,tools
#             #                        ,Params
#             #                        ,parse_data
#             #                        ,lambda tool : tool == read_shapefile
#             #                        ,[]
#             #                        )     
            
            
#             if options.auto_plot_data: # already parses if no colours
#                 tools = insert_tool(self
#                                    ,'after'                
#                                    ,tools
#                                    ,Params
#                                    ,recolour_objects
#                                    ,lambda tool : tool == read_shapefile #parse_data
#                                    ,[]
#                                    )    
#             return tools



#         def update_Params(   self
#                             ,Params = None
#                             ,tools = None
#                             ):
#             #type(type[any], type[any, list]) -> type[any]

#             if Params is None:
#                 try:
#                     Params = ghenv.Component.Params
#                 except:
#                     Params = self.Params

#             if tools is None:
#                 tools = self.tools



#             return add_tool_params(Params
#                                   ,tools
#                                   ,do_not_add
#                                   ,do_not_remove
#                                   ,geom_params
#                                   )
    

#         def update_tools(self, nick_name = None):
#             #type(type[any], str) -> type[any]

#             if nick_name is None:
#                 nick_name = self.local_metas.nick_name

#             tools = tool_factory(nick_name
#                                 ,self.opts['metas'].name_map
#                                 ,tools_dict
#                                 ,cache_sDNA_tool
#                                 )
#             debug(tools)
                 

#             #debug(self.opts)
#             debug('Tool opts == ' + '\n'.join( str(k) + ' : ' + str(v) 
#                                                 for k,v in self.opts.items()
#                                                 if k not in ('options','metas')
#                                               ) 
#                  )

#             return tools






#         def update_name(self, new_name = None):
#             if new_name is None:
#                 new_name = self.Attributes.Owner.NickName 
#                 # IfF this is run before __init__ has run, there is no 
#                 # Attributes attribute yet, but can use ghenv.Component
    

#             if not hasattr(self, 'nick_name') or (
#                self.opts['metas'].allow_components_to_change_type
#                and self.local_metas.nick_name != new_name    ):  
#                 #
#                 self.local_metas = self.local_metas._replace(nick_name = new_name)
#                 self.logger = logger.getChild(self.local_metas.nick_name)

#                 output( ' Component nick name changed to : ' 
#                                 + self.local_metas.nick_name, 'INFO' )
#                 return 'Name updated'
#             return 'Name not updated'


  



            
#         def update_sDNA(self):
#             debug('Self has attr sDNA == ' 
#                  +str(hasattr(self,'sDNA'))
#                  )
#             debug('self.opts[metas].sDNA == (' 
#                  +str(self.opts['metas'].sDNAUISpec)
#                  +', '
#                  +self.opts['metas'].runsdnacommand 
#                  +') '
#                  )

#             if hasattr(self,'sDNA'):
#                 debug('Self has attr sDNA == ' + str(hasattr(self,'sDNA')))
            
#             sDNA = ( self.opts['metas'].sDNAUISpec  # Needs to be hashable to be
#                     ,self.opts['metas'].runsdnacommand )   # a dict key => tuple not list
#                      # these are both just module names.  
#                      # Python can't import two files with the same name
#                      # so changing these triggers the change to input the new one

#             if not hasattr(self,'sDNA') or self.sDNA != sDNA:
#                 self.sDNAUISpec, self.run_sDNA, path = self.load_modules(
#                                                           sDNA
#                                                          ,self.opts['metas'].sDNA_search_paths
#                                                          )
#                 #  self.sDNAUISpec, self.run_sDNA are the two Python modules
#                 #  to allow different components to run different sDNA versions
#                 #  these module references are instance variables

#                 assert self.sDNAUISpec.__name__ == self.opts['metas'].sDNAUISpec
#                 assert self.run_sDNA.__name__ == self.opts['metas'].runsdnacommand




#                 debug('Self has attr sDNAUISpec == ' + str(hasattr(self,'sDNAUISpec')))
#                 debug('Self has attr run_sDNA == ' + str(hasattr(self,'run_sDNA')))

#                 self.sDNA = sDNA
#                 self.sDNA_path = path
#                 self.opts['metas'] = self.opts['metas']._replace(    sDNA = self.sDNA
#                                                                     ,sDNA_path = path 
#                                                                 )
#                 self.opts['options'] = self.opts['options']._replace(  sDNAUISpec = self.sDNAUISpec
#                                                                       ,run_sDNA = self.run_sDNA 
#                                                                     )  

#                 assert self.opts['metas'].sDNA_path == os.path.dirname(self.opts['options'].sDNAUISpec.__file__)                                                                  






#         def __init__(self, *args, **kwargs):

#             BaseClass.__init__(self, *args, **kwargs)
            
#             self.load_modules = load_modules
#             self.ghdoc = ghdoc
#             self.ghenv = ghenv

#             self.update_sDNA() 



#         def RunScript(self, *args): #go, Data, Geom, f_name, *args):
#             # type (bool, str, Rhino Geometry, datatree, tuple(namedtuple,namedtuple), *dict)->bool, str, Rhino_Geom, datatree, str

#             args_dict = {key.Name : val for key, val in zip(self.Params.Input, args) } # .Input[4:] type: ignore
            
#             debug(args_dict)
#             debug('self.Params.Input Names == ' + ' '.join(key.Name for key in self.Params.Input))
#             debug(args)

#             go = args_dict.get('go', False)
#             Data = args_dict.get('Data', None)
#             Geom = args_dict.get('Geom', None)
#             f_name = args_dict.get('file', '')

#             if f_name and not isinstance(f_name, str) and isinstance(f_name, list):
#                     f_name=f_name[0] 

#             external_opts = first_item_if_seq(args_dict.get('opts', {}), {})
#             debug(external_opts)

            

#             external_local_metas = first_item_if_seq(args_dict.get('local_metas', empty_NT), empty_NT)
#             gdm = args_dict.get('gdm', {})

#             debug('gdm from start of RunScript == ' + str(gdm)[:50])
#             #print('#1 self.local_metas == ' + str(self.local_metas))
            
#             if self.update_name() == 'Name updated':
#                 nick_name = self.local_metas.nick_name
#                 if (nick_name.lower()
#                              .replace('_','')
#                              .replace(' ','') == 'sdnageneral'
#                     and 'tool' in args_dict):
#                     nick_name = args_dict['tool']
#                 self.my_tools = self.update_tools(nick_name)
            
#             self.tools = self.auto_insert_tools(self.my_tools, self.Params)  
#                     # Other components may mean self.tools needs extra tools adding or /removing
#                     # but this could - annoy many users.  TODO!  Get early feedback!
#             #self.Params = 
#             self.update_Params()#self.Params, self.tools)

            
#             synced = self.local_metas.sync_to_module_opts
#             old_sDNA = self.opts['metas'].sDNA

#             self.local_metas = override_all_opts(args_dict = args_dict
#                                                 ,local_opts = self.opts # mutated
#                                                 ,external_opts = external_opts 
#                                                 ,local_metas = self.local_metas 
#                                                 ,external_local_metas = external_local_metas
#                                                 )

#             args_dict['opts'] = self.opts
#             args_dict['l_metas'] = self.local_metas

#             debug('Opts overridden....    ')
#             debug(self.local_metas)
#             debug('options after override in RunScript == ' + str(self.opts['options']))
            
#             if (self.opts['metas'].auto_update_Rhino_doc_path 
#                 or not os.path.isfile(self.opts['options'].Rhino_doc_path)        ):

#                 path = get_path(self.opts, self)

#                 self.opts['options'] = self.opts['options']._replace( Rhino_doc_path = path )

#             if self.opts['metas'].allow_components_to_change_type: 
                
#                 if self.local_metas.sync_to_module_opts != synced:
#                     if self.local_metas.sync_to_module_opts:
#                         self.opts = module_opts #sync
#                     else:
#                         self.opts = self.opts.copy() #desync

#                 if self.opts['metas'].sDNA != old_sDNA:
#                     self.update_sDNA()
#                     #self.Params = 
#                     self.update_Params()#self.Params, self.tools)


#             if go in [True, [True]]: # [True] in case go set to List Access in GH component 
#                 returncode = 999
#                 assert isinstance(self.tools, list)

#                 debug('my_tools == '
#                      +str(self.tools)
#                      )

#                 geom_data_map = convert_Data_tree_and_Geom_list_to_gdm(Geom
#                                                                       ,Data
#                                                                       ,self.opts
#                                                                       )
                
#                 debug('type(geom_data_map) == '
#                      +str(type(geom_data_map))
#                      )
                

#                 geom_data_map = override_gdm_with_gdm(gdm
#                                                      ,geom_data_map
#                                                      ,self.opts
#                                                      )

#                 debug('After merge type(geom_data_map) == ' 
#                      +str(type(geom_data_map))
#                      )                
                
#                 debug('After merge geom_data_map == ' 
#                      +str(geom_data_map.items()[:3])
#                      +' ...'
#                      )


#                 ret_vals_dict = run_tools(self.tools, args_dict)

#                 gdm = ret_vals_dict.get('gdm', {})
#                 #print (str(gdm))
#                 if isinstance(gdm, dict):
#                     debug('Converting gdm to Data and Geometry')
#                     (NewData, NewGeometry) = (
#                     convert_dictionary_to_data_tree_or_lists(gdm)
#                                         )    
#                     #debug(NewData)
#                     #debug(NewGeometry)                    
#                 else:
#                     NewData, NewGeometry = None, None

#                 ret_vals_dict['Data'] = NewData
#                 ret_vals_dict['Geom'] = NewGeometry
#                 #if 'leg_frame' in ret_vals_dict:
#                 #    ret_vals_dict['rect'] = ret_vals_dict['leg_frame']
#                 ret_vals_dict['opts'] = [self.opts.copy()]
#                 ret_vals_dict['l_metas'] = self.local_metas #immutable

#                 def get_val(key):
#                     return ret_vals_dict.get(key
#                                             ,getattr(self.opts['metas']
#                                                     ,key
#                                                     ,getattr(self.opts['options']
#                                                             ,key
#                                                             ,getattr(self.local_metas
#                                                                     ,key
#                                                                     ,getattr(self.opts.get(self.local_metas.nick_name
#                                                                                           ,{}
#                                                                                           ).get(self.opts['metas'].sDNA
#                                                                                                ,{}
#                                                                                                )
#                                                                             ,key
#                                                                             ,'No variable or field: ' + key + ' found. '
#                                                                             )
#                                                                     )
#                                                             )
#                                                     )                            
#                                             ) #TODO: Make this a while loop over a list of sources and add in locals()


#                 ret_vals = tuple(get_val(param.NickName) for param in self.Params.Output)
#                 return ret_vals
#             else:   
#                 return (False, ) + tuple(repeat(None, len(self.Params.Output) - 1))

   
#     return sDNA_GH_Component




###############################################################################
#Main script only process
#
if      '__file__' in dir(__builtins__)  and  __name__ in __file__ and '__main__' not in __file__ and '<module>' not in __file__:                     
    # Assert:  We're in a module!
    pass
else:
    pass


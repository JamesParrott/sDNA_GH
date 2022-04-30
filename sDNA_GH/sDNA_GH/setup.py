#! Grasshopper Python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys, os
from collections import namedtuple, OrderedDict

import Rhino
import scriptcontext as sc

from .custom.options_manager import (any_clashes
                                    ,load_toml_file
                                    ,load_ini_file                             
                                    ,override_namedtuple  
                                    ,namedtuple_from_class
                                    ,Sentinel  
                                    ,error_raising_sentinel_factory
                                    )
from .custom import logging_wrapper
from .custom import pyshp_wrapper
from .launcher import Output, load_modules
from .custom.helpers.funcs import (first_item_if_seq
                                  ,valid_re_normalisers
                                  )
from .custom.gdm_from_GH_Datatree import (gdm_from_DataTree_and_list
                                         ,override_gdm
                                         ,dict_from_DataTree_and_lists
                                         )
from .custom.skel.basic.smart_comp import SmartComponent, custom_retvals
from .custom.skel.basic.ghdoc import ghdoc                                       
from .custom.skel.tools.inserter import insert_tool
from .custom.skel.tools.runner import run_tools, tools_dict, RunnableTool
from .custom.skel.tools.name_mapper import tool_factory
from .custom.skel.add_params import add_tool_params
from .custom.tools import (sDNA_GH_Tool
                          ,RhinoObjectsReader
                          ,UsertextReader
                          ,ShapefileWriter
                          ,ShapefileReader
                          ,UsertextWriter
                        #   ,UsertextBaker
                          ,DataParser
                          ,ObjectsRecolourer
                          ,sDNA_ToolWrapper
                          ,sDNA_GeneralDummyTool
                          ,Load_Config_File
                          )
from .dev_tools.dev_tools import GetToolNames, sDNA_GH_Builder



output = Output()



# Pre Python 3.6 the order of an OrderedDict isn't necessarily that of the 
# arguments in its constructor so we build our options and metas namedtuples
# from a class, to avoid re-stating the order of the keys.

class HardcodedMetas(sDNA_ToolWrapper.opts['metas']): 
    config = os.path.join(os.path.dirname(  os.path.dirname(__file__)  )
                         ,r'config.toml'  
                         )
    add_new_opts = False
    cmpnts_change = False
    strict_namedtuples = True
    strict_opts = True
    sDNAUISpec = 'sDNAUISpec'  #Names of sDNA modules to import
                               # The actual modules will be loaded into
                               # options.sDNAUISpec and options.run_sDNA 
    runsdnacommand = 'runsdnacommand' # only used for .map_to_string. 
                            # Kept in case we use work out how
                            # to run runsdnacommand.runsdnacommand in future 
                            # with an env, while being able to get the 
                            # sDNA stderr and stdout to the sDNA_GH logging
    sDNA = (sDNAUISpec, runsdnacommand)  # Read only.  Auto updates from above.
    sDNA_path = ''  
    # Read only.  Determined after loading sDNAUISpec to which ever below
    # it is found in.
    # after loading, 
    # assert 
    #   opts['metas'].sDNA_path 
    #      == os.path.dirname(opts['options'].sDNAUISpec.__file__)
    #sDNA_UISpec_path = r'C:\Program Files (x86)\sDNA\sDNAUISpec.py'
    #sDNA_search_paths = [sDNA_UISpec_path, 
    sDNA_search_paths  = [r'C:\Program Files (x86)\sDNA']
    sDNA_search_paths += [os.path.join(os.getenv('APPDATA'),'sDNA')]
    sDNA_search_paths += [path for path in os.getenv('PATH').split(';')
                               if 'sDNA' in path ]
    update_path = True
                        #Abbreviation = Tool Name
###############################################################################
    name_map = dict(Read_Geom = 'get_Geom'
                   ,Read_Usertext = 'read_Usertext'
                   ,Write_Shp = 'write_shapefile'
                   ,Read_Shp = 'read_shapefile'
                   ,Write_Usertext = 'write_Usertext'
                   #,Bake_UserText = 'bake_Usertext'
                   ,Parse_Data = 'parse_data'
                   ,Recolour_Objects = 'recolour_objects'
                   ,Recolor_Objects = 'recolour_objects'
                   ,Load_Config = 'load_config'
                   ,Comp_Names = 'get_comp_names'
                   #
                   ,sDNA_Integral = 'sDNAIntegral'
                   ,sDNA_Skim = 'sDNASkim'
                   ,sDNA_Int_From_OD = 'sDNAIntegralFromOD'
                   ,sDNA_Geodesics = 'sDNAGeodesics'
                   ,sDNA_Hulls = 'sDNAHulls'
                   ,sDNA_Net_Radii = 'sDNANetRadii'
                   ,sDNA_Access_Map = 'sDNAAccessibilityMap'
                   ,sDNA_Prepare = 'sDNAPrepare'
                   ,sDNA_Line_Measures = 'sDNALineMeasures'
                   ,sDNA_Learn = 'sDNALearn'
                   ,sDNA_Predict = 'sDNAPredict'
                   #,Test_Plot = ['get_Geom', 'read_shapefile', 'parse_data', 'recolour_objects']
                   #,Test_Parse = ['get_Geom', 'write_shapefile', 'sDNAIntegral', 'read_shapefile', 'parse_data']
                   )
                          
    categories = {'get_Geom'         : 'Support'
                 ,'read_Usertext'    : 'Data'
                 ,'write_shapefile'  : '.shp'
                 ,'read_shapefile'   : '.shp'
                 ,'write_Usertext'   : 'Data'
                 # ,'bake_Usertext'    : 'Usertext'
                 ,'parse_data'       : 'Plot'
                 ,'recolour_objects' : 'Plot'
                 ,'sDNAIntegral'     : 'Analysis'
                 ,'sDNASkim'         : 'Analysis'
                 ,'sDNAIntFromOD'    : 'Analysis'
                 ,'sDNAGeodesics'    : 'Geometric analysis'
                 ,'sDNAHulls'        : 'Geometric analysis'
                 ,'sDNANetRadii'     : 'Geometric analysis'
                 ,'sDNAAccessMap'    : 'Analysis'
                 ,'sDNAPrepare'      : 'Prep'
                 ,'sDNALineMeasures' : 'Prep'
                 ,'sDNALearn'        : 'Calibration'
                 ,'sDNAPredict'      : 'Calibration'
                 ,'sDNA_General'     : 'Dev'
                 ,'get_comp_names'   : 'Dev'
                 ,'Self_test'        : 'Dev'
                 ,'Build_components' : 'Dev' 
                 ,'Load_Config'      : 'Support'
                 }


#######################################################################################################################

def get_path_to_users_working_file(inst = None):
    #type(dict, type[any]) -> str
    #refers to `magic' global ghdoc so needs to 
    # be in module scope (imported above)
    
    path_getters = [lambda : Rhino.RhinoDoc.ActiveDoc.Path
                   ,lambda : ghdoc.Path
                   ,lambda : inst.ghdoc.Path  #e.g. via old Component decorator
                   ,lambda : sc.doc.Path
                   ,lambda : __file__
                   ]
    working_file = None
    for path_getter in path_getters:
        try:
            working_file = path_getter()
        except:
            pass
        if isinstance(working_file, str) and os.path.isfile(working_file):
            break
    return working_file 

file_to_work_from = get_path_to_users_working_file()

class HardcodedOptions(logging_wrapper.LoggingOptions
                      ,pyshp_wrapper.ShpOptions
                      ,RhinoObjectsReader.opts['options']
                      ,ShapefileWriter.opts['options']
                      ,ShapefileReader.opts['options']
                      ,UsertextWriter.opts['options']
                    #   ,UsertextBaker.opts['options']
                      ,DataParser.opts['options']
                      ,ObjectsRecolourer.opts['options']
                      ,sDNA_ToolWrapper.opts['options']
                      ):            
    ###########################################################################
    #System
    #
    platform = 'NT' # in {'NT','win32','win64'} only supported for now
    encoding = 'utf-8'
    package_name = os.path.basename(os.path.dirname(__file__))
    sub_module_name = os.path.basename(__file__).rpartition('.')[0]
    #
    ###########################################################################
    #
    # Automatic tool insertion rules ('smart' tools)
    #
    auto_get_Geom = True
    auto_read_Usertext = True
    auto_write_Shp = True
    auto_read_Shp = True
    #auto_parse_data = False  # not used.  ObjectsRecolourer parses if req anyway
    auto_plot_data = True
    ###########################################################################
    #
    # Overrides for .custom.logging_wrapper
    #
    path = file_to_work_from if file_to_work_from else __file__ 
    # Also used by ShapefileWriter, ShapefileReader
    working_folder = os.path.dirname(path)
    logger_name = package_name
    log_file = logger_name + '.log'
    logs_dir = 'logs'
    log_file_level = 'DEBUG'
    log_console_level = 'INFO'
    #
    ##########################################################################
    #
    # Overrides for sDNA_ToolWrapper
    #
    sDNAUISpec = error_raising_sentinel_factory('No sDNA module: sDNAUISpec '
                                               +'loaded yet. '
                                               ,'Module is loaded from the '
                                               +'first files named in '
                                               +'metas.sDNAUISpec and '
                                               +'metas.runsdnacommand both '
                                               +'found in a path in '
                                               +'metas.sDNA_search_paths. '
                                               )
    run_sDNA = error_raising_sentinel_factory('No sDNA module: '
                                             +'runsdnacommand loaded yet. '
                                             ,'Module is loaded from the '
                                             +'first files named in '
                                             +'metas.sDNAUISpec and '
                                             +'metas.runsdnacommand both '
                                             +'found in a path in '
                                             +'metas.sDNA_search_paths. '
                                             )
    python_exe = r'C:\Python27\python.exe' 
    prepped_fmt = '{name}_prepped'
    output_fmt = '{name}_output'   
    del_after_sDNA = False
    strict_no_del = False # Also in ShapefileReader
    ###########################################################################    
    #
    # Overrides for RhinoObjectsReader
    #
    selected = False
    layers = None
    merge_subdicts = True
    #
    #
    ###########################################################################
    #
    #     Shapefiles
    #     Application specific overrides for .custom.pyshp_wrapper
    #
    shape_type = 'POLYLINEZ' # Also in RhinoObjectsReader, ShapefileWriter
    locale = ''  # '' => User's own settings.  Also in DataParser
                 # e.g. 'fr', 'cn', 'pl'. IETF RFC1766,  ISO 3166 Alpha-2 code
                 # Used for locale.setlocale(locale.LC_ALL,  options.locale)
    #
    # coerce_and_get_code
    decimal = True
    precision = 12
    max_dp = 4 # decimal places
    yyyy_mm_dd = False
    keep_floats = True
    use_memo = False # Use the 'M' field code in Shapefiles for uncoerced data
    #
    # get_filename
    overwrite_shp = True
    max_new_files = 20
    suppress_warning = True     
    dupe_file_key_str = '{name}_({number})'
    #
    # ensure_correct & write_iterable_to_shp
    extra_chars = 2
    #
    # write_iterable_to_shp
    field_size = 30
    cache_iterable= False
    uuid_field = 'Rhino3D_' # 'object_identifier_UUID_'  
    # also in ShapefileReader, UsertextWriter  
    uuid_length = 36 # 32 in 5 blocks (2 x 6 & 2 x 5) with 4 seperator characters.
    num_dp = 10 # decimal places
    min_sizes = True
    #
    ###########################################################################
    #
    # Overrides for ShapefileWriter
    #
    input_key_str = 'sDNA input name={name} type={fieldtype} size={size}'
    #30,000 characters tested.
    output_shp = ''
    ###########################################################################
    #
    # Overrides for ShapefileReader
    #
    new_geom = True
    del_after_read = False                 
    sDNA_names_fmt = '{name}.shp.names.csv'  
    ###########################################################################   
    #         
    # Overrides for UsertextWriter
    #   
    output_key_str = 'sDNA output={name} run time={datetime}'  
    #30,000 characters tested.
    overwrite_UserText = True
    max_new_keys = 6
    suppress_overwrite_warning = False
    dupe_key_suffix = r'_{}'
    ###########################################################################   
    #         
    # Overrides for DataParser
    #   
    field = 'BtEn'
    plot_max = Sentinel('plot_max is automatically calculated by sDNA_GH unless overridden.  ')
    plot_min = Sentinel('plot_min is automatically calculated by sDNA_GH unless overridden.  ')
    sort_data = False
    base = 10 # base of log and exp spline, not of number representations
    re_normaliser = 'linear' #['linear', 'exponential', 'logarithmic']
    if re_normaliser not in valid_re_normalisers:
        raise ValueError(str(re_normaliser) 
                        +' must be in '
                        + str(valid_re_normalisers)
                        )
    class_bounds = [Sentinel('class_bounds is automatically calculated by sDNA_GH unless overridden.  ')] 
    # e.g. [2000000, 4000000, 6000000, 8000000, 10000000, 12000000]

    number_of_classes = 7
    class_spacing = 'equal number of members' 
    valid_class_spacings = valid_re_normalisers + ['equal number of members']
    if class_spacing not in valid_class_spacings:
        raise ValueError(str(class_spacing)
                        +' must be in ' 
                        +str(valid_class_spacings)
                        )
    first_leg_tag_str = 'below {upper}'
    gen_leg_tag_str = '{lower} - {upper}' # also supports {mid_pt}
    last_leg_tag_str = 'above {lower}'
    num_format = '{:.5n}'
    leg_frame = ''  # uuid of GH object
    colour_as_class = False
    #
    #
    ###########################################################################   
    #         
    # Overrides for ObjectsRecolourer
    #   
    leg_extent = Sentinel('leg_extent is automatically calculated by sDNA_GH unless overridden.  ')  # [xmin, ymin, xmax, ymax]
    bbox = Sentinel('bbox is automatically calculated by sDNA_GH unless overridden.  ')  # [xmin, ymin, xmax, ymax]
    Col_Grad = False
    Col_Grad_num = 5
    rgb_max = (155, 0, 0) #990000
    rgb_min = (0, 0, 125) #3333cc
    rgb_mid = (0, 155, 0) # guessed
    line_width = 4 # milimetres? 
    ###########################################################################
    #
    # Options override system test field
    #
    message = 'Hardcoded default options from tools.py'



class HardcodedLocalMetas(object):
    sync = True    
    read_only = True
    nick_name = error_raising_sentinel_factory('Nick name has not been read '
                                              +'from component yet! '
                                              ,'nick_name will automatically '
                                              +'be updated on each component.'
                                              )






default_metas = namedtuple_from_class(HardcodedMetas, 'Metas')
default_options = namedtuple_from_class(HardcodedOptions, 'Options')
default_local_metas = namedtuple_from_class(HardcodedLocalMetas, 'LocalMetas')

empty_NT = namedtuple('Empty','')(**{})

module_opts = OrderedDict( metas = default_metas
                         ,options = default_options
                         )                
           

output(module_opts['options'].message,'DEBUG')







#########################################################################
#
#
def override_all_opts(args_dict
                     ,local_opts # mutated
                     ,external_opts
                     ,local_metas = default_local_metas
                     ,external_local_metas = empty_NT
                     ,name = ''
                     ):
    #type(dict, dict, dict, namedtuple, namedtuple, str) -> namedtuple
    #
    # 1) We assume opts has been built from a previous GHPython launcher 
    # component and call to this very function.  This trusts the user and 
    # our components somewhat, in so far as we assume metas and options 
    # in opts have not been crafted to 
    # be of a class named 'Metas', 'Options', yet contain missing options.  
    #
    # 2) A primary meta in opts refers to an old primary meta (albeit the 
    # most recent one) and will not be used in the options_manager.override
    #  order as we assume that file has already been read into a previous 
    # opts in the chain.  If the user wishes 
    # to apply a new project config.ini file, they need to instead specify 
    # it in args (by adding a variable called config to 
    # the GHPython sDNA_GH launcher component.
    metas = local_opts['metas']
    options = local_opts['options']
    def sDNA():
        return local_opts['metas'].sDNA


    # Unlike in all the other functions, sDNA might change in this one, 
    # (in metas in the main options update function).  So we store 
    # tool args ready under this new sDNA version, in advance of the 
    # component importing the new sDNA module, and we just have to 
    # then perform an update in
    # cache_syntax_and_UISpec instead of an overwrite

    args_metas = {}
    args_options = {}
    args_tool_options = {}
    args_local_metas = {}

    for (arg_name, arg_val) in args_dict.items():  # local_metas() will be full
                                                   # of all our other variables
        if arg_val: # Unconnected input variables in a Grasshopper component 
                    # are None.  No sDNA tool inputspec default, no metas and 
                    # no options default is None.
                    # If None values are needed as specifiable inputs, we would 
                    # need to e.g. test ghenv for an input variable's 
                    # connectedness so we don't support this.
            if arg_name in metas._fields:      
                args_metas[arg_name] = arg_val
            elif arg_name in options._fields:   
                args_options[arg_name] = arg_val
            elif arg_name in getattr( local_opts.get(name
                                                    ,{}
                                                    ).get(sDNA()
                                                         ,{} 
                                                         )
                                    ,'_fields' 
                                    ,{} 
                                    ): 
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
         ,strict = local_opts['metas'].strict_namedtuples
         ,check_types = local_opts['metas'].strict_opts
         ,add_new_opts = local_opts['metas'].add_new_opts
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
            output('Loading options from .ini file: ' + path, 'DEBUG')
            config_file_override =  load_ini_file(path
                                                 ,**kwargs(''
                                                          ,local_opts
                                                          ) 
                                                 )
        elif file_ext == 'toml':
            output('Loading options from .toml file: ' + path, 'DEBUG')
            config_file_override =  load_toml_file( path )
        else:
            output('config_file_override = ' 
                  +str(config_file_override)
                  ,'DEBUG'
                  )
    else:
        output('No valid config file in args.  '
              +str(args_metas)
              ,'DEBUG'
              )
        file_ext = ''


    def config_file_reader(key):
        #type(str)->[dict/file object]
        if (isinstance(config_file_override, dict) 
            and key in config_file_override  ):
            #
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
                                 ,config_file_reader('local_metas') 
                                                    # 'nick_name' removed above
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
        if (local_metas.sync or 
            not local_metas.read_only):
            retval = []  
        else: 
            #if not synced but still reading from module opts, 
            # then add module opts to overrides
            retval = [    module_opts.get( key,  {} ).get( sDNA(),  {} )    ]

        
        ext_opts = external_opts.get( key,  {} )
        if key not in ('options','metas') :
            ext_opts = ext_opts.get( sDNA(),  {} )
        
        retval += [ext_opts
                  ,config_file_reader(key)
                  ,sub_args_dict.get(key, {})
                  ]



        return retval

        

    #overrides_list = lambda key : [ 
    #                       external_opts.get(key,{}).get(sDNA(), {})
    #                       config_file_reader, sub_args_dict.get(key, {})]
    if local_metas.sync:
        dict_to_update = module_opts # the opts in module's global scope, 
                                     # outside this function
    else:
        dict_to_update = local_opts
        #if local_metas.read_only:
          #  overrides = lambda key : [
          #                 opts.get(key,{}).get(sDNA(), {})
          #                           ] + overrides(key)

    for key in dict_to_update:
        if key in ('options','metas'):
            dict_to_update[key] = override_namedtuple(dict_to_update[key]
                                                     ,overrides_list(key)
                                                     ,**kwargs(key, local_opts) 
                                                     ) 
            #if key=='options':
            #    print('dict_to_update message == '+dict_to_update['options'].message+' '+'DEBUG')
        else:
            if sDNA() in dict_to_update[key]:
                dict_to_update[key][sDNA()] = override_namedtuple(
                                                    dict_to_update[key][sDNA()]
                                                   ,overrides_list(key)
                                                   ,**kwargs(key, local_opts) 
                                                                 )
            else:
                for tool in dict_to_update[key]:
                    dict_to_update[key][tool][sDNA()] = override_namedtuple( 
                                                          dict_to_update[key][tool][sDNA()]
                                                         ,overrides_list(key) # + '_tool'
                                                         ,**kwargs(key, local_opts) # + '_tool'  
                                                                           ) 
                                                    # TODO: add in tool name to key
    return local_metas


# First options options_manager.override (3), 
# user's installation specific options over (4), 
# hardcoded defaults above
#
# Use the above function to load the user's installation wide defaults by using
#  the primary meta from the hardcoded defaults.

if os.path.isfile(default_metas.config):
    #print('Before override: message == '+opts['options'].message)
    override_all_opts(args_dict = default_metas._asdict() # to get installation config.toml
                     ,local_opts = module_opts #  mutates opts
                     ,external_opts = {}  
                     ) 
    output("After override: opts['options'].message == " 
          + module_opts['options'].message
          , 'DEBUG'
          )
else:
    output('Config file: ' + default_metas.config + ' not found. ','WARNING')    
#
#######################################################################

folders = [r'C:\Program Files\Python27'
          ,r'%appdata%\Python27'
          ,r'C:\Program Files (x86)\Python27'
          ]
pythons = ['python.exe'
          ,'py27.exe'
          ]

possible_pythons = (os.path.join(folder, python) for folder in folders 
                                                 for python in pythons
                   )

while not os.path.isfile(module_opts['options'].python_exe):
    module_opts['options']._replace(python_exe = next(possible_pythons))

if not os.path.isfile(module_opts['options'].python_exe):
    raise ValueError('python_exe is not a file. ')

module_name = '.'.join([module_opts['options'].package_name 
                       ,module_opts['options'].sub_module_name
                       ]
                      )

if ( module_name in sys.modules
    and not hasattr(sys.modules[module_name], 'logger') ):  

    # wrapper_logging.logging.shutdown() # Ineffective in GH :(

    # Create root logger.  All component launchers import this module, 
    # (or access it via Grasshopper's cache in sys.modules) but
    # all their loggers are childs of this module's logger:
    logger = logging_wrapper.new_Logger(custom = None
                                       ,options = module_opts['options']
                                       ) 
                                       


    output.set_logger(logger) # Flushes cached log messages to above handlers

    logger.debug('Logging set up in sDNA_GH package ')



############################################################################


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


get_Geom = RhinoObjectsReader()
read_Usertext = UsertextReader()
write_shapefile = ShapefileWriter()
read_shapefile = ShapefileReader()
write_Usertext = UsertextWriter()
# bake_Usertext = UsertextBaker()
parse_data = DataParser()
recolour_objects = ObjectsRecolourer()
get_tool_names = GetToolNames()
build_components = sDNA_GH_Builder()
sDNA_General_dummy_tool = sDNA_GeneralDummyTool()
load_config_file = Load_Config_File()

tools_dict.update(get_Geom = get_Geom
                 ,read_Usertext = read_Usertext
                 ,write_shapefile = write_shapefile
                 ,read_shapefile = read_shapefile
                 ,write_Usertext = write_Usertext
                #  ,bake_Usertext = bake_Usertext
                 ,parse_data = parse_data
                 ,recolour_objects = recolour_objects 
                 ,get_comp_names = get_tool_names
                 ,Build_components = build_components
                 ,sDNA_General = sDNA_General_dummy_tool
                 ,load_config = load_config_file
                 )

def cache_sDNA_tool(compnt
                   ,nick_name
                   ,mapped_name
                   ,name_map
                   ,tools_dict
                   ):
    sDNA_tool = sDNA_ToolWrapper(mapped_name, nick_name, compnt.opts)
    tools_dict[nick_name] =  sDNA_tool
    sDNA = compnt.opts['metas'].sDNA
    compnt.do_not_remove += tuple(sDNA_tool.tool_opts[sDNA]._fields)   
    # Could also call compnt.update_sDNA

            



sDNA_GH_tools = list(tools_dict.values())


class sDNA_GH_Component(SmartComponent):

    # Options from module, from defaults and installation config.toml
    opts = module_opts  
    local_metas = default_local_metas   # immutable.  controls syncing /
                                        # desyncing / read / write of the
                                        # above (opts).
                                        # Although local, it can be set on 
                                        # groups of components using the 
                                        # default section of a project 
                                        # config.toml, or passed as a
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
        
        logger.debug('Inserting tools... ')

        def is_class(Class):
            #type(type[any]) -> function
            def checker(tool):
                #type(function) -> bool
                return isinstance(tool, Class)
            return checker

        if options.auto_write_Shp:
            insert_tool('before'
                       ,tools
                       ,Params
                       ,tool_to_insert = write_shapefile
                       ,is_target = is_class(sDNA_ToolWrapper)
                       ,not_a_target = sDNA_GH_tools
                       ,tools_dict = tools_dict
                       ,name_map = name_map
                       )

        if options.auto_read_Usertext:
            insert_tool('before'
                       ,tools
                       ,Params
                       ,tool_to_insert = read_Usertext
                       ,is_target = is_class(ShapefileWriter)
                       ,not_a_target = []
                       ,tools_dict = tools_dict
                       ,name_map = name_map
                       )   

        if options.auto_get_Geom:
            insert_tool('before'
                       ,tools
                       ,Params
                       ,tool_to_insert = get_Geom
                       ,is_target = is_class(UsertextReader)
                       ,not_a_target = []
                       ,tools_dict = tools_dict
                       ,name_map = name_map
                       )   

        if options.auto_read_Shp:
            insert_tool('after'
                       ,tools
                       ,Params
                       ,tool_to_insert = read_shapefile
                       ,is_target = is_class(sDNA_ToolWrapper)
                       ,not_a_target = sDNA_GH_tools
                       ,tools_dict = tools_dict
                       ,name_map = name_map
                       )
        
      
        
        if options.auto_plot_data: # already parses if Data not all colours
            insert_tool('after'                
                       ,tools
                       ,Params
                       ,tool_to_insert = recolour_objects
                       ,is_target = is_class(ShapefileReader)
                       ,not_a_target = []
                       ,tools_dict = tools_dict
                       ,name_map = name_map
                       ) 
                                          
        return tools



    def update_Params(self
                     ,Params = None
                     ,tools = None
                     ):
        #type(type[any], type[any, list]) -> type[any]

        if Params is None:
            Params = self.Params
            # If this is run before __init__ has finished .Params may not be
            # there yet.  But it is still available at ghenv.Component.Params
            # if ghenv is available (unlike here in a module).

        if tools is None:
            tools = self.tools


        logger.debug("Updating Params: " + str(tools))

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

        tools = tool_factory(inst = self
                            ,nick_name = nick_name
                            ,name_map = self.opts['metas'].name_map
                            ,tools_dict = tools_dict
                            ,tool_not_found = cache_sDNA_tool
                            )
        logger.debug(tools)
                

        #logger.debug(self.opts)
        logger.debug('Tool opts == ' + '\n'.join( str(k) + ' : ' + str(v) 
                                                for k, v in self.opts.items()
                                                if k not in ('options','metas')
                                                ) 
                    )

        return tools






    def update_name(self, new_name = None):
        if new_name is None:
            new_name = self.Attributes.Owner.NickName 
            # If this is run before __init__ has run, there is no 
            # Attributes attribute yet (ghenv.Component can be used instead).
            logger.debug('new_name == ' + new_name)

        if (isinstance(self.local_metas.nick_name, Sentinel)) or (
           self.opts['metas'].cmpnts_change and 
           self.local_metas.nick_name != new_name ):  
            #
            self.local_metas = self.local_metas._replace(nick_name = new_name)
            self.logger = logger.getChild(self.local_metas.nick_name)

            logger.info(' Component nick name changed to : ' 
                       +self.local_metas.nick_name
                       )
            return 'Name updated'
        logger.debug('Old name kept == ' + self.local_metas.nick_name)

        return 'Old name kept'






        
    def update_sDNA(self):
        logger.debug('Self has attr sDNA == ' 
                +str(hasattr(self,'sDNA'))
                )
        logger.debug('self.opts[metas].sDNAUISpec == ' 
                +str(self.opts['metas'].sDNAUISpec)
                +', self.opts[metas].runsdnacommand == '
                +str(self.opts['metas'].runsdnacommand )
                )

        logger.debug('before update, self.opts[options].sDNAUISpec == ' 
                +str(self.opts['options'].sDNAUISpec)
                +', self.opts[options].run_sDNA == '
                +str(self.opts['options'].run_sDNA )
                )

        if hasattr(self,'sDNA'):
            logger.debug('Self has old attr sDNA == ' + str(hasattr(self,'sDNA')))

        self.sDNA = (self.opts['metas'].sDNAUISpec
                    ,self.opts['metas'].runsdnacommand
                    ) 

        if ( isinstance(self.opts['options'].sDNAUISpec, Sentinel) or
             isinstance(self.opts['options'].run_sDNA, Sentinel) or
             (self.opts['options'].sDNAUISpec.__name__
                       ,self.opts['options'].run_sDNA.__name__) != self.sDNA ):
            #
            # Import sDNAUISpec.py and runsdnacommand.py from metas.sDNA_search_paths
            #
            sDNAUISpec, run_sDNA, _ = self.load_modules(self.sDNA
                                                       ,self.opts['metas'].sDNA_search_paths
                                                       )
            self.opts['options'] = self.opts['options']._replace(sDNAUISpec = sDNAUISpec
                                                                ,run_sDNA = run_sDNA 
                                                                )  






    def __init__(self, *args, **kwargs):
        logger.debug('Calling sDNA_GH_Components parent initialiser')
        SmartComponent.__init__(self, *args, **kwargs)
        self.load_modules = load_modules
        self.ghdoc = ghdoc
        self.update_sDNA() 




    def script(self, **kwargs):        
        # update_Params is called from inside this method, so the input Params 
        # supplying the args will not updated until after they have been read.
        # If this method is not intended to crash on a missing input param,
        # it needs to accept anything (or a lack thereof) to run in the 
        # meantime until the params can be updated.  kwargs enable this.
        logger.debug('self.script started... \n')
        logger.debug(kwargs)

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

        external_opts = first_item_if_seq(kwargs.pop('opts'
                                                    ,{}
                                                    )
                                         ,{}
                                         )

        external_local_metas = first_item_if_seq(kwargs.pop('local_metas'
                                                           ,empty_NT
                                                           )
                                                ,empty_NT
                                                )
        logger.debug(external_opts)

        gdm = first_item_if_seq(kwargs.get('gdm', {}))

        logger.debug('gdm from start of RunScript == ' + str(gdm)[:50])
        #print('#1 self.local_metas == ' + str(self.local_metas))
        
        if self.update_name() == 'Name updated': # True 1st run after __init__
            nick_name = self.local_metas.nick_name
            if (nick_name.lower()
                         .replace('_','')
                         .replace(' ','') == 'sdnageneral'
                and 'tool' in kwargs ):
                #
                nick_name = kwargs['tool']
            self.my_tools = self.update_tools(nick_name)
        
            self.tools = self.auto_insert_tools(self.my_tools, self.Params)  


            self.update_Params()#self.Params, self.tools)
            return (None,) * len(self.Params.Output)
            # Grasshopper components can have a glitchy one off error if
            # not-None outputs are given to params that 
            # have just been added, in the same RunScript call.  In our 
            # design the user probably doesn't want the new tool and 
            # updated component params to run before they've had chance to
            # look at them, even if 'go' still is connected to True.

        
        synced = self.local_metas.sync
        old_sDNA = self.opts['metas'].sDNA
        self.local_metas = override_all_opts(
                                 args_dict = kwargs
                                ,local_opts = self.opts # mutated
                                ,external_opts = external_opts 
                                ,local_metas = self.local_metas 
                                ,external_local_metas = external_local_metas
                                )
        kwargs['opts'] = self.opts
        kwargs['l_metas'] = self.local_metas

        logger.debug('Opts overridden....    ')
        logger.debug(self.local_metas)
        
        if (self.opts['metas'].update_path 
            or not os.path.isfile(self.opts['options'].path) ):

            path = get_path_to_users_working_file(self)

            self.opts['options'] = self.opts['options']._replace(path = path)

        if self.opts['metas'].cmpnts_change: 
            
            if self.local_metas.sync != synced:
                if self.local_metas.sync:
                    self.opts = module_opts #resync
                else:
                    self.opts = self.opts.copy() #desync
                    #

            if self.opts['metas'].sDNA != old_sDNA:
                self.update_sDNA()
                #self.Params = 
                self.update_Params()#self.Params, self.tools)

        logger.debug(go)

        if go == True: 
            if not isinstance(self.tools, list):
                msg = 'self.tools is not a list'
                logger.error(msg)
                raise TypeError(msg)

            invalid_tools = [tool for tool in self.tools 
                                  if not isinstance(tool, RunnableTool)
                            ]
            if invalid_tools:
                msg = ('Tools are not RunnableTool : ' 
                      +' '.join(map(str, invalid_tools))
                      )
                logger.error(msg)
                raise ValueError(msg)

            logger.debug('my_tools == '
                    +str(self.tools)
                    )



            geom_data_map = gdm_from_DataTree_and_list(Geom, Data)



            logger.debug('type(geom_data_map) == '
                        +str(type(geom_data_map))
                        )
            
            logger.debug('Before merge gdm[:3] == ' 
                        +str(gdm.items()[:3])
                        +' ...'
                        )

            logger.debug('Before merge geom_data_map[:3] == ' 
                        +str(geom_data_map.items()[:3])
                        +' ...'
                        )

            gdm = override_gdm(gdm
                                       ,geom_data_map
                                       ,self.opts['options'].merge_subdicts
                                       )

            logger.debug('After merge type(gdm) == ' 
                        +str(type(gdm))
                        )                
            
            logger.debug('After merge gdm[:3] == ' 
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
                logger.debug('Converting gdm to Data and Geometry')
                (NewData, NewGeometry) = dict_from_DataTree_and_lists(gdm)
                                        
            else:
                NewData, NewGeometry = None, None

            ret_vals_dict['Data'] = NewData
            ret_vals_dict['Geom'] = NewGeometry
            if 'f_name' in ret_vals_dict:
                ret_vals_dict['file'] = ret_vals_dict['f_name']

            ret_vals_dict['OK'] = ret_vals_dict.get('retcode', 0) == 0


            tool_opts = self.opts
            nick_name = self.local_metas.nick_name
            sDNA = self.opts['metas'].sDNA
            if nick_name in self.opts:
                tool_opts = self.opts[nick_name]
                if isinstance(tool_opts, dict):
                    tmp = {}
                    for tool_name in tool_opts:
                        sub_tools_dict = tool_opts[tool_name]
                        if sDNA in sub_tools_dict:
                            sub_tools_dict = sub_tools_dict[sDNA]
                        if hasattr(sub_tools_dict, '_asdict'):
                            sub_tools_dict = sub_tools_dict._asdict()
                        tmp.update(sub_tools_dict)
                    tool_opts = tmp
        else:
            logger.debug('go == ' + str(True))
            ret_vals_dict = {}
            ret_vals_dict['OK'] = False
            tool_opts = {}
        ret_vals_dict['opts'] = [self.opts.copy()]
        ret_vals_dict['l_metas'] = self.local_metas #immutable

        logger.debug('Returning from self.script ')
        locs = locals().copy()
        ret_args = self.component_Outputs( 
                              [  ret_vals_dict
                              ,  self.opts['metas']
                              ,  self.opts['options']
                              ,  self.local_metas
                              ,  tool_opts
                              ,  locs
                              ]
                             )
        return ret_args
    script.input_params = lambda : sDNA_GH_Tool.params_list(['go', 'opts'])
    script.output_params = lambda : sDNA_GH_Tool.params_list(['OK', 'opts'])



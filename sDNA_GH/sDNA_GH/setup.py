#! Grasshopper Python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys, os
from collections import namedtuple, OrderedDict

import Rhino
import scriptcontext as sc

from .custom.options_manager import (load_toml_file
                                    ,load_ini_file                             
                                    ,override_namedtuple  
                                    ,namedtuple_from_class
                                    ,sentinel_factory    
                                    ,Sentinel  
                                    )
from .custom import logging_wrapper
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
                          ,UsertextBaker
                          ,DataParser
                          ,ObjectsRecolourer
                          ,sDNA_ToolWrapper
                          ,sDNA_GeneralDummyTool
                          )
from .dev_tools.dev_tools import GetToolNames, sDNA_GH_Builder



output = Output()


class HardcodedMetas(object): 
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
                   ,Bake_UserText = 'bake_Usertext'
                   ,Parse_Data = 'parse_data'
                   ,Recolour_Objects = 'recolour_objects'
                   ,Recolor_Objects = 'recolour_objects'
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
                        ,'sDNA_General'     : 'Dev tools'
                        ,'Python'           : 'Dev tools'
                        ,'Self_test'        : 'Dev tools'
                        ,'Build_components' : 'Dev tools' 
                    }


#######################################################################################################################



class HardcodedOptions(object):            
    ###########################################################################
    #System
    platform = 'NT' # in {'NT','win32','win64'} only supported for now
    encoding = 'utf-8'
    sDNAUISpec = sentinel_factory('No sDNA module: sDNAUISpec loaded yet')
    run_sDNA = sentinel_factory('No sDNA module: runsdnacommand loaded yet')
    Rhino_doc_path = ''  # tbc by auto update
    sDNA_prepare = r'C:\Program Files (x86)\sDNA\bin\sdnaprepare.py'
    sDNA_integral = r'C:\Program Files (x86)\sDNA\bin\sdnaintegral.py'
    python_exe = r'C:\Python27\python.exe' 
    # Default installation path of Python 2.7.3 release (32 bit ?) 
    # http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi

    # copied from sDNA manual 
    # https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/installation_usage.html    
    ###########################################################################    #Logging    
    #os.getenv('APPDATA'),'Grasshopper','Libraries','sDNA_GH','sDNA_GH.log')
    logs_dir = 'logs'
    log_file = 'sDNA_GH.log'

    log_file_level = 'DEBUG'
    log_console_level = 'INFO'
    log_custom_level = 'INFO'

    ###########################################################################
    #     #GDM
    merge_data = True
    ###########################################################################
    #     #Shapefiles
    shape_type = 'POLYLINEZ'
    include_groups = False
    cache_iterable= False
    dot_shp = '.shp' # file extensions are actually optional in PyShp, but just to be safe and future proof
    #supply_sDNA_file_names = True
    output_shp = r'C:\Users\James\Documents\Rhino\Grasshopper\tmp.shp' # None means Rhino .3dm filename is used.
    overwrite_shp = True
    overwrite_UserText = True
    dupe_key_suffix = r'_{}'
    prepped_shp_suffix = "_prepped"
    output_shp_suffix = "_output"
    dupe_file_suffix = r'_({})' # Needs to contain a replacement field {} that .format can target.  No f strings in Python 2.7 :(
    max_new_files = 20
    suppress_warning = True     
    uuid_field = 'Rhino3D_' # 'object_identifier_UUID_'     
    uuid_length = 36 # 32 in 5 blocks (2 x 6 & 2 x 5) with 4 seperator characters.
    min_sizes = True
    del_shp = False
    field_size = 30
    num_dp = 10 # decimal places
    extra_chars = 2
    yyyy_mm_dd = False
    decimal = True
    keep_floats = True
    precision = 12
    max_dp = 4 # decimal places
    ###########################################################################
    #Writing and Reading Usertext to/from Rhino
    new_geom = False
    max_new_keys = 20
    #
    #
    input_key_str = 'sDNA input name={name} type={fieldtype} size={size}'  
    #30,000 characters tested!
    output_key_str = 'sDNA output={name} run time={datetime}'  
    #30,000 characters tested!
    ###########################################################################
    #sDNA
    default_path = __file__
    overwrite_shp = False
    auto_get_Geom = True
    auto_read_Usertext = True
    auto_write_Shp = True
    auto_read_Shp = True
    #auto_parse_data = False  # not used.  Recolour_data parses if req anyway
    auto_plot_data = True
    #Plotting results
    field = 'BtEn'
    plot_max = sentinel_factory('plot_max not overridden yet')
    plot_min = sentinel_factory('plot_min not overridden yet')
    sort_data = False
    base = 10 # base of log and exp spline, not of number representations
    re_normaliser = 'linear' #['linear', 'exponential', 'logarithmic']
    if re_normaliser not in valid_re_normalisers:
        raise ValueError(str(re_normaliser) 
                        +' must be in '
                        + str(valid_re_normalisers)
                        )
    class_bounds = [sentinel_factory('class_bounds is not initialised yet. ')] 
    # e.g. [2000000, 4000000, 6000000, 8000000, 10000000, 12000000]
    leg_extent = sentinel_factory('leg_extent is not initialised yet. ')  # [xmin, ymin, xmax, ymax]
    bbox = sentinel_factory('bbox is not initialised yet. ')  # [xmin, ymin, xmax, ymax]
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
    locale = '' # ''=> auto. 
                # Used for locale.setlocale(locale.LC_ALL,  options.locale)
    colour_as_class = False
    Col_Grad = False
    Col_Grad_num = 5
    rgb_max = (155, 0, 0) #990000
    rgb_min = (0, 0, 125) #3333cc
    rgb_mid = (0, 155, 0) # guessed
    line_width = 4 # milimetres? 
    ###########################################################################
    #Test
    message = 'Hardcoded default options from tools.py'



class HardcodedLocalMetas(object):
    sync = True    
    read_only = True
    nick_name = ''


# Pre Python 3.6 the order of an OrderedDict isn't necessarily that of the 
# arguments in its constructor so we build our options and metas namedtuples
# from a class, to avoid re-stating the order of the keys.



default_metas = namedtuple_from_class(HardcodedMetas, 'Metas')
default_options = namedtuple_from_class(HardcodedOptions, 'Options')
default_local_metas = namedtuple_from_class(HardcodedLocalMetas, 'LocalMetas')

empty_NT = namedtuple('Empty','')(**{})

module_opts = OrderedDict( metas = default_metas
                         ,options = default_options
                         )                
           

output(module_opts['options'].message,'DEBUG')



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
                path = opts['options'].default_path
    
    return path



#########################################################################
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

if not hasattr(sys.modules['sDNA_GH.setup'], 'logger'):  
    
    logs_directory = os.path.join(os.path.dirname( get_path(module_opts) )
                                 ,module_opts['options'].logs_dir
                                 )

    if not os.path.isdir(logs_directory):
        os.mkdir(logs_directory)

    # wrapper_logging.logging.shutdown() # Ineffective in GH :(


    logger = logging_wrapper.new_Logger(
                                 'sDNA_GH'
                                ,os.path.join(logs_directory
                                             ,module_opts['options'].log_file
                                             )
                                ,module_opts['options'].log_file_level
                                ,module_opts['options'].log_console_level
                                ,None # custom_file_object 
                                ,module_opts['options'].log_custom_level
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
bake_Usertext = UsertextBaker()
parse_data = DataParser()
recolour_objects = ObjectsRecolourer()
get_tool_names = GetToolNames()
build_components = sDNA_GH_Builder()
sDNA_General_dummy_tool = sDNA_GeneralDummyTool()


tools_dict.update(get_Geom = get_Geom
                 ,read_Usertext = read_Usertext
                 ,write_shapefile = write_shapefile
                 ,read_shapefile = read_shapefile
                 ,write_Usertext = write_Usertext
                 ,bake_Usertext = bake_Usertext
                 ,parse_data = parse_data
                 ,recolour_objects = recolour_objects 
                 ,Python = get_tool_names
                 ,Build_components = build_components
                 ,sDNA_General = sDNA_General_dummy_tool
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
        
      
        
        if options.auto_plot_data: # already parses if not all colours in Data
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
            # If this is tried before __init__ has finished .Params may not be
            # there yet.  But it is still available at ghenv.Component.Params

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
            self.opts['metas'].cmpnts_change
            and self.local_metas.nick_name != new_name    ):  
            #
            self.local_metas = self.local_metas._replace(nick_name = new_name)
            self.logger = logger.getChild(self.local_metas.nick_name)

            output( ' Component nick name changed to : ' 
                            + self.local_metas.nick_name, 'INFO' )
            return 'Name updated'
        return 'Name not updated'






        
    def update_sDNA(self):
        logger.debug('Self has attr sDNA == ' 
                +str(hasattr(self,'sDNA'))
                )
        logger.debug('self.opts[metas].sDNAUISpec == ' 
                +str(self.opts['metas'].sDNAUISpec)
                +', self.opts[metas].runsdnacommand == '
                +str(self.opts['metas'].runsdnacommand )
                )

        if hasattr(self,'sDNA'):
            logger.debug('Self has attr sDNA == ' + str(hasattr(self,'sDNA')))
        
        sDNA = ( self.opts['metas'].sDNAUISpec  # Needs to be hashable to be
                ,self.opts['metas'].runsdnacommand )   # a dict key => tuple not list
                    # these are both just module names.  
                    # Python can't import two files with the same name
                    # so changing these triggers the change to input the new one

        if not hasattr(self,'sDNA') or self.sDNA != sDNA:
            self.sDNAUISpec, self.run_sDNA, path = self.load_modules(sDNA
                                                                    ,self.opts['metas'].sDNA_search_paths
                                                                    )
            #  self.sDNAUISpec, self.run_sDNA are the two Python modules
            #  to allow different components to run different sDNA versions
            #  these module references are instance variables

            if (self.sDNAUISpec.__name__ != self.opts['metas'].sDNAUISpec
               or self.run_sDNA.__name__ != self.opts['metas'].runsdnacommand):
                msg = ('sDNAUISpec and run_sDNA imported, but '
                      +' module names do not match meta options '
                      +'.sDNAUISpec and .runsdnacommand'
                      )          
                logger.error(msg)
                raise ValueError(msg)



            logger.debug('Self has attr sDNAUISpec == ' 
                        +str(hasattr(self,'sDNAUISpec'))
                        )
            logger.debug('Self has attr run_sDNA == ' 
                        +str(hasattr(self,'run_sDNA'))
                        )

            self.sDNA = sDNA
            self.sDNA_path = path
            logger.debug('Path sDNAUISpec imported from == ' + path)
            self.opts['metas'] = self.opts['metas']._replace(sDNA = self.sDNA
                                                            ,sDNA_path = path 
                                                            )
            self.opts['options'] = self.opts['options']._replace(
                                                 sDNAUISpec = self.sDNAUISpec
                                                ,run_sDNA = self.run_sDNA 
                                                                )  

            sDNA_path = os.path.dirname(self.sDNAUISpec.__file__)
            if self.opts['metas'].sDNA_path == sDNA_path:                                                              
                raise ValueError('sDNAUISpec imported, but '
                                +' module __file__ does not match meta option '
                                +' .sDNA_path'
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
        # it needs to accept anything (or a lack thereof) to run in the meantime
        # until the params can be updated.  kwargs are perfect for this.
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
        
        if self.update_name() == 'Name updated': # True immediately after __init__
            nick_name = self.local_metas.nick_name
            if (nick_name.lower()
                         .replace('_','')
                         .replace(' ','') == 'sdnageneral'
                and 'tool' in kwargs ):
                #
                nick_name = kwargs['tool']
            self.my_tools = self.update_tools(nick_name)
        
        self.tools = self.auto_insert_tools(self.my_tools, self.Params)  
                # Other components may mean self.tools needs extra tools adding
                # or /removing but this could - annoy many users.  
                # TODO!  Get feedback!
                # TODO:  Move this to after the opts override?!  But params 
                # need to feed into the opts?

        self.update_Params()#self.Params, self.tools)

        
        synced = self.local_metas.sync
        old_sDNA = self.opts['metas'].sDNA
        #logger.debug('kwargs["field"] == ' + str(kwargs['field']))
        self.local_metas = override_all_opts(
                                 args_dict = kwargs
                                ,local_opts = self.opts # mutated
                                ,external_opts = external_opts 
                                ,local_metas = self.local_metas 
                                ,external_local_metas = external_local_metas
                                            )
        #logger.debug('self.opts["options"].field == ' + str(self.opts['options'].field))
        kwargs['opts'] = self.opts
        kwargs['l_metas'] = self.local_metas

        logger.debug('Opts overridden....    ')
        logger.debug(self.local_metas)
        #logger.debug('options after override in script == ' + str(self.opts['options']))
        
        if (self.opts['metas'].update_path 
            or not os.path.isfile(self.opts['options'].Rhino_doc_path) ):

            path = get_path(self.opts, self)

            self.opts['options'] = self.opts['options']._replace(Rhino_doc_path = path)

        if self.opts['metas'].cmpnts_change: 
            
            if self.local_metas.sync != synced:
                if self.local_metas.sync:
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
            

            gdm = override_gdm(gdm
                                       ,geom_data_map
                                       ,self.opts['options'].merge_data
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
                                        
                #logger.debug(NewData)
                #logger.debug(NewGeometry)                    
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
            logger.debug('go was not == True')
            ret_vals_dict = {}
            ret_vals_dict['OK'] = False
            tool_opts = {}
        retval_names = [Param.Name for Param in self.Params.Output]
        logger.debug('Returning from self.script ')
        locs = locals().copy()
        return custom_retvals(retval_names
                             ,[  ret_vals_dict
                              ,  self.opts['metas']
                              ,  self.opts['options']
                              ,  self.local_metas
                              ,  tool_opts
                              ,  locs
                              ]
                             )
    script.input_params = sDNA_GH_Tool.params_list(['go', 'opts'])
    script.output_params = sDNA_GH_Tool.params_list(['OK', 'opts'])



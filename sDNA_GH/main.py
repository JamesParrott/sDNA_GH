#! /usr/bin/awk NR==3
# -*- coding: utf-8 -*-
# This module requires Grasshopper Python (Rhino3D)

# MIT License

# Copyright (c) [2021] [Cardiff University, a body incorporated
# by Royal Charter and a registered charity (number:
# 1136855) whose administrative offices are at 7th floor 30-
# 36 Newport Road, UniversityCF24 0DE, Wales, UK]

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.



""" Main sDNA_GH module imported by copies of launcher.py in the Grasshopper
    component files.  All functionality is via the sDNA_GH_Component class, 
    which Grasshopper reads from launcher.py and instantiates itself.  Multiple
    components share the same imported instance of this module.  If it has not 
    been changed, the same code in launcher.py is also imported here.

    The default module options are defined here, and the main options override 
    logic for the supported opts structure is defined in override_all_opts.

    The function to import sDNA is defined here (update_sDNA()), but this is
    passed to sDNA_Tool_Wrapper instances, the only things that call it.
"""

__author__ = 'James Parrott'
__version__ = '0.02'

import sys
import os
from collections import namedtuple, OrderedDict

from . import launcher
from .custom import options_manager
from .custom import logging_wrapper
from .custom import pyshp_wrapper
from .custom.helpers import funcs 
from .custom import gdm_from_GH_Datatree
from .custom.skel.basic import smart_comp
from .custom.skel.basic.ghdoc import ghdoc #GhPython 'magic' global variable
from .custom.skel.tools.helpers import checkers                         
from .custom.skel.tools import inserter 
from .custom.skel.tools import runner
from .custom.skel.tools import name_mapper
from .custom.skel import add_params
from .custom import tools
from .dev_tools import dev_tools


output = launcher.Output()



# Pre Python 3.6 the order of an OrderedDict isn't necessarily that of the 
# arguments in its constructor so we build our options and metas namedtuples
# from a class, to avoid re-stating the order of the keys.

default_name_map = dict(Read_Geom = 'get_Geom'
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

class HardcodedMetas(tools.sDNA_ToolWrapper.opts['metas']
                    ,tools.ConfigManager.opts['metas'] # has config.toml path
                    ): 
    add_new_opts = False
    cmpnts_change = False
    strict = True
    check_types = True
    sDNAUISpec = 'sDNAUISpec'  #Names of sDNA modules to import
                               # The actual modules will be loaded into
                               # options.sDNAUISpec and options.run_sDNA 
    runsdnacommand = 'runsdnacommand' # only used for .map_to_string. 
                            # Kept in case we use work out how
                            # to run runsdnacommand.runsdnacommand in future 
                            # with an env, while being able to get the 
                            # sDNA stderr and stdout to the sDNA_GH logging
    sDNA = (sDNAUISpec, runsdnacommand)  # Read only.  Auto updates from above.
    #sDNA_path = ''  
    # Read only.  Determined after loading sDNAUISpec to which ever below
    # it is found in.
    # after loading, 
    # assert 
    #   opts['metas'].sDNA_path 
    #      == os.path.dirname(opts['options'].sDNAUISpec.__file__)
    #sDNA_UISpec_path = r'C:\Program Files (x86)\sDNA\sDNAUISpec.py'
    #sDNA_paths = [sDNA_UISpec_path, 
    sDNA_paths  = [r'C:\Program Files (x86)\sDNA']
    sDNA_paths += [os.path.join(os.getenv('APPDATA'),'sDNA')]
    sDNA_paths += [path for path in os.getenv('PATH').split(';')
                               if 'sDNA' in path ]
    update_path = True
    ##########################################################################
    #
    # Override for tools.sDNA_ToolWrapper
    #
    show_all = True
    ###########################################################################
    #
    #               Abbreviation = Tool Name
    #


    name_map = default_name_map.copy()
                   # Long names for some Rhino installs that use component Name not Nickname
                   # (these can be removed if the components are all rebuilt s.t. name == nickname) 
    name_map.update({'Read Rhino geometry' : 'get_Geom'
                   ,'Read user text' : 'read_Usertext'
                   ,'Write shapefile' : 'write_shapefile'
                   ,'Read shapefile' : 'read_shapefile'
                   ,'Write user text' : 'write_Usertext'
                   #,Bake_UserText : 'bake_Usertext'
                   ,'Parse data' : 'parse_data'
                   ,'Recolour objects' : 'recolour_objects'
                   ,'Recolor objects' : 'recolour_objects'
                   ,'Load configuration' : 'load_config'
                   ,'Get component names' : 'get_comp_names'
                   #
                   ,'Integral Analysis' : 'sDNAIntegral'
                   ,'Skim Matrix' : 'sDNASkim'
                   ,'Integral from OD Matrix (assignment model)' : 'sDNAIntegralFromOD'
                   ,'Geodesics' : 'sDNAGeodesics'
                   ,'Convex Hulls' : 'sDNAHulls'
                   ,'Network Radii' : 'sDNANetRadii'
                   ,'Specific Origin Accessibility Maps' : 'sDNAAccessibilityMap'
                   ,'Prepare network' : 'sDNAPrepare'
                   ,'Individual Line Measures' : 'sDNALineMeasures'
                   ,'Learn' : 'sDNALearn'
                   ,'Predict' : 'sDNAPredict'                   
                   })
                          
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


file_to_work_from = checkers.get_path(fallback = __file__)

class HardcodedOptions(logging_wrapper.LoggingOptions
                      ,pyshp_wrapper.ShpOptions
                      ,tools.RhinoObjectsReader.opts['options']
                      ,tools.ShapefileWriter.opts['options']
                      ,tools.ShapefileReader.opts['options']
                      ,tools.UsertextWriter.opts['options']
                    #   ,tools.UsertextBaker.opts['options']
                      ,tools.DataParser.opts['options']
                      ,tools.ObjectsRecolourer.opts['options']
                      ,tools.sDNA_ToolWrapper.opts['options']
                      ):            
    ###########################################################################
    #System
    #
    platform = 'NT' # in {'NT','win32','win64'} only supported for now
    encoding = 'utf-8' # used by .custom.pyshp_wrapper
                       # get_fields_recs_and_shapes and write_iterable_to_shp
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
    # Overrides for tools.sDNA_ToolWrapper
    #
    sDNAUISpec = options_manager.error_raising_sentinel_factory('No sDNA module:'
                                               +' sDNAUISpec loaded yet. '
                                               ,'Module is loaded from the '
                                               +'first files named in '
                                               +'metas.sDNAUISpec and '
                                               +'metas.runsdnacommand both '
                                               +'found in a path in '
                                               +'metas.sDNA_paths. '
                                               )
    run_sDNA = options_manager.error_raising_sentinel_factory('No sDNA module:'
                                               +' run_sDNA loaded yet. '
                                               ,'Module is loaded from the '
                                               +'first files named in '
                                               +'metas.sDNAUISpec and '
                                               +'metas.runsdnacommand both '
                                               +'found in a path in '
                                               +'metas.sDNA_paths. '
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
    layer = None
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
    plot_max = options_manager.Sentinel('plot_max is automatically calculated'
                                       +' by sDNA_GH unless overridden.  '
                                       )
    plot_min = options_manager.Sentinel('plot_min is automatically calculated'
                                       +' by sDNA_GH unless overridden.  '
                                       )
    sort_data = False
    base = 10 # base of log and exp spline, not of number representations
    re_normaliser = 'linear' #['uniform', 'linear', 'exponential', 'logarithmic']
    if re_normaliser not in funcs.valid_re_normalisers:
        raise ValueError('%s must be in %s' 
                        %(re_normaliser, funcs.valid_re_normalisers)
                        )
    class_bounds = [options_manager.Sentinel('class_bounds is automatically '
                                            +'calculated by sDNA_GH unless '
                                            +'overridden.  '
                                            )
                   ] 
    # e.g. [2000000, 4000000, 6000000, 8000000, 10000000, 12000000]

    num_classes = 7
    class_spacing = 'quantile' 
    #_valid_class_spacings = (funcs.valid_re_normalisers
    #                         + ('quantile', 'cluster', 'nice'))
    if class_spacing not in tools.DataParser.opts['options']._valid_class_spacings:
        raise ValueError('%s must be in %s' 
                        %(class_spacing
                         ,tools.DataParser.opts['options']._valid_class_spacings
                         )
                        )
    first_leg_tag_str = 'below {upper}'
    gen_leg_tag_str = '{lower} - {upper}' # also supports {mid_pt}
    last_leg_tag_str = 'above {lower}'
    num_format = '{:.5n}'
    leg_frame = ''  # uuid of GH object
    colour_as_class = False
    exclude = False
    suppress_small_classes_error = False
    suppress_class_overlap_error = False

    #
    #
    ###########################################################################   
    #         
    # Overrides for ObjectsRecolourer
    #   
    leg_extent = options_manager.Sentinel('leg_extent is automatically '
                                         +'calculated by sDNA_GH unless '
                                         +'overridden.  '
                                         ) # [xmin, ymin, xmax, ymax]
    bbox = options_manager.Sentinel('bbox is automatically '
                                   +'calculated by sDNA_GH unless '
                                   +'overridden.  '
                                   )  # [xmin, ymin, xmax, ymax]
    Col_Grad = False
    Col_Grad_num = 5
    rgb_max = [155, 0, 0] #990000
    rgb_min = [0, 0, 125] #3333cc
    rgb_mid = [0, 155, 0] # guessed
    line_width = 4 # milimetres? 
    ###########################################################################
    #
    # Options override system test field
    #
    message = 'Hardcoded default options from tools.py'



class HardcodedLocalMetas(object):
    sync = True    
    read_only = True
    nick_name = options_manager.error_raising_sentinel_factory('Nick name has '
                                              +'not been read '
                                              +'from component yet! '
                                              ,'nick_name will automatically '
                                              +'be updated on each component.'
                                              )




namedtuple_from_class = options_manager.namedtuple_from_class

default_metas = namedtuple_from_class(HardcodedMetas, 'Metas')
default_options = namedtuple_from_class(HardcodedOptions, 'Options')
default_local_metas = namedtuple_from_class(HardcodedLocalMetas, 'LocalMetas')

empty_NT = namedtuple('Empty','')(**{})

module_opts = OrderedDict(metas = default_metas
                         ,options = default_options
                         )                
           

output.debug(module_opts['options'].message)







#########################################################################
#
override_namedtuple = options_manager.override_namedtuple
#
def override_all_opts(args_dict
                     ,local_opts # mutated
                     ,external_opts
                     ,local_metas = default_local_metas
                     ,external_local_metas = empty_NT
                     ):
    #type(dict, dict, dict, namedtuple, namedtuple, str) -> namedtuple
    #
    # 1) We assume external_opts has been built from another GHPython launcher 
    # component, importing this module and also calling this very function.  
    # This trusts the user and 
    # our components somewhat, in so far as we assume metas and options 
    # in opts have not been crafted to 
    # be of a class named 'Metas', 'Options', yet contain missing options.  But 
    # generally, while this has been tested a lot, when it fails, it fails noisily.
    #
    # 2) A primary meta in module_opts refers to an old primary meta (albeit the 
    # most recent one) and will not be used in the options_manager.override
    #  order as we assume that file has already been read into a previous 
    # module_opts in the override chain.  If the user wishes 
    # to apply a new project config.toml file, they need to instead specify 
    # the primary meta (config) in the component args which will be read in as args_dict
    #  (by adding a variable called config to the GHPython sDNA_GH launcher component).
    #
    # metas = local_opts['metas']
    # options = local_opts['options']
    # def sDNA():
    #     return local_opts['metas'].sDNA


    # Unlike in all the other functions, sDNA might change in this one, 
    # (in metas in the main options update function).  So we store 
    # tool args ready under this new sDNA version, in advance of the 
    # component importing the new sDNA module, and we just have to 
    # then perform an update in
    # cache_syntax_and_UISpec instead of an overwrite

    # args_metas = {}
    # args_options = {}
    # args_tool_options = {}
    # args_local_metas = {}

    # for (arg_name, arg_val) in args_dict.items():  # local_metas() will be full
    #                                                # of all our other variables
    #     if arg_val is not None: 
    #                 # Unconnected input variables in a Grasshopper component 
    #                 # are None.  
    #                 # If None values are needed as specifiable inputs, we would 
    #                 # need to e.g. test ghenv for an input variable's 
    #                 # connectedness so we don't support this.
    #                 # None is used in the hardcoded options to allow
    #                 # strict typechecking to be avoided (once only), but None 
    #                 # is not supported in .toml files either.   
    #         if arg_name in metas._fields:      
    #             args_metas[arg_name] = arg_val
    #         elif arg_name in options._fields:   
    #             args_options[arg_name] = arg_val
    #         elif arg_name in local_metas._fields:
    #             args_local_metas[arg_name] = arg_val
    #         else:
    #             args_tool_options[arg_name] = arg_val

            # elif any(arg_name in tools.get_tool_opts(name, opts, tool, sDNA())    
            # elif arg_name in getattr( local_opts.get(name
            #                                         ,{}
            #                                         ).get(sDNA()
            #                                              ,{} 
            #                                              )
            #                         ,'_fields' 
            #                         ,{} 
            #                         ): 
            #     args_tool_options[arg_name] = arg_val

    # sub_args_dict = {'metas' : args_metas
    #                 ,'options' : args_options
    #                 ,local_metas.nick_name: args_tool_options
    #                 }


    # def kwargs(local_opts):
    #     d = dict(strict = local_opts['metas'].strict
    #             ,check_types = local_opts['metas'].check_types
    #             ,add_new_opts = local_opts['metas'].add_new_opts
    #             )
    #     return d

    ###########################################################################
    #Primary meta:
    #
    config_toml_dict = {}

    if args_dict and 'config' in args_dict:
        if os.path.isfile(args_dict['config']): 
            path = args_dict['config']
            file_ext = path.rpartition('.')[2]
            if file_ext == 'toml':
                output.debug('Loading options from .toml file: %s' % path)
                config_toml_dict =  options_manager.load_toml_file( path )
            else:
                output.debug('config_toml_dict = %s' % config_toml_dict)
        else:
            msg = ('config in args_dict == %s ' % args_dict['config']
                  +' needs to be an existing .toml file'
                  )
            output.error(msg)
            raise ValueError(msg)

    else:
        output.debug('No config specfied in args_dict == %s' % args_dict)
        file_ext = ''


    # def config_file_reader(key, tool = None, sDNA = None):
    #     #type(str)->[dict/file object]
    #     return tools.get_tool_opts(key, config_toml_dict, tool, sDNA)

        # if (isinstance(config_toml_dict, dict) 
        #     and key in config_toml_dict  ):
        #     #
        #     return tools.get_tool_opts(key, config_toml_dict, tool, sDNA)
        # else:
        #     return config_toml_dict



    ###########################################################################
    #
    # Ensure we don't overwrite a component's nick_name with another's, or 
    # with a nick_name from config.toml (sDNAgeneral components change a 
    # separate local variable to an Input Param, after it was 
    # initialised to this local_meta)
    #



    ext_local_metas_dict = external_local_metas._asdict()
    if 'nick_name' in ext_local_metas_dict:
        ext_local_metas_dict.pop('nick_name')

    if file_ext and (file_ext == 'toml' or 
                     isinstance(config_toml_dict, dict)):
            if ( 'local_metas' in config_toml_dict and
                 'nick_name' in config_toml_dict['local_metas'] ):
                config_toml_dict['local_metas'].pop('nick_name')

    if 'nick_name' in args_dict:
        args_dict.pop('nick_name')

    ###########################################################################
    # Update syncing / desyncing controls in local_metas
    #
    local_metas_overrides_list = [ext_local_metas_dict
                                 ,config_toml_dict.get('local_metas',{}) 
                                                    # 'nick_name' removed above
                                 ,args_dict
                                 ]
    local_metas = override_namedtuple(local_metas
                                     ,local_metas_overrides_list
                                     ,**local_opts['metas']._asdict()

                                     ) 
    ###########################################################################




    # def overrides_list(key, tool = None, sDNA = None):
    #     # type (str) -> list
    #     if (local_metas.sync or 
    #         not local_metas.read_only):
    #         retval = []  
    #     else: 
    #         #if not synced but still reading from module opts, 
    #         # then add module opts to overrides
    #         retval = [tools.get_tool_opts(key, module_opts, tool, sDNA)]

        
    #     # ext_opts = external_opts.get( key,  {} )
    #     # if key not in ('options','metas') :
    #     #     ext_opts = ext_opts.get( sDNA(),  {} )
        
    #     retval += [tools.get_tool_opts(key, external_opts, tool, sDNA)
    #               ,config_file_reader(key, tool, sDNA)
    #               ,sub_args_dict.get(key, args_tool_options)
    #               ]



    #     return retval

        

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

    def is_strict_nested_dict(d):
        #type(dict) -> bool
        return all(isinstance(val, dict) for val in d.values())



    def override_nested_dict_dfs(d, override):
        #type(dict, Optional[dict/namedtuple]
        """ Depth first search. """
        if not isinstance(d, dict):
            metas = local_opts['metas']
            return options_manager.override_namedtuple(d
                                                      ,override
                                                      ,**metas._asdict()
                                                      )
        if isinstance(override, dict):
            if is_strict_nested_dict(override):
                #
                # Insert or update d with any 
                # pure nested dict structure in override
                #
                for key_ov in override:
                    if key_ov in d:
                        d[key_ov] = override_nested_dict_dfs(d[key_ov], override[key_ov])
                    else:
                        d[key_ov] = override[key_ov]
            else:  
                # override has non-dict vals, e.g has flattened out.  
                # Override all subdicts of d with them.
                for key_d in d:
                    d[key_d] = override_nested_dict_dfs(d[key_d], override)

    # for (key, val) in d.items():
    #     if (key in override and 
    #         isinstance(val, tuple) and 
    #         hasattr(val, '_fields')):
    #         #
    #         d[key] = 
    #     elif isinstance():

    #     d_keys = list(d.keys())
    #     override_keys = list( getattr(override,'keys', []))
    #     new_keys = [key for key in override_keys if key not in d_keys]
    #     for key in d:
    #         output.debug('Overriding : %s' % key)

    overrides = [external_opts
                ,config_toml_dict
                ,OrderedDict((key, val )
                             for (key, val) in args_dict.items() 
                             if val is not None
                            )
                ]            

    if (local_metas.sync or 
            not local_metas.read_only):
        overrides.insert(0,module_opts)

    dict_to_update['metas'] = options_manager.override_namedtuple(
                                         dict_to_update['metas']
                                        ,map(lambda x : x.pop('metas',{}), overrides)
                                        ,**local_opts['metas']._asdict()
                                        )
    # Update metas first, then we don't have to code up a breadth first search.

    for override in overrides:
        override_nested_dict_dfs(dict_to_update, override)

    # for key in dict_to_update:
    #     output.debug('Overriding : %s' % key)
    #     if key in ('options','metas'):
    #         dict_to_update[key] = override_namedtuple(dict_to_update[key]
    #                                                  ,overrides_list(key)
    #                                                  ,**kwargs(key, local_opts) 
    #                                                  ) 
    #     else:
    #         sDNA = sDNA()
    #         if sDNA in dict_to_update[key]:
    #             dict_to_update[key][sDNA] = override_namedtuple(
    #                                                 dict_to_update[key][sDNA]
    #                                                ,overrides_list(key, tool = None, sDNA = sDNA)
    #                                                ,**kwargs(key, local_opts) 
    #                                                              )
    #         else:
    #             for tool in dict_to_update[key]:
    #                 dict_to_update[key][tool][sDNA] = override_namedtuple( 
    #                                                       dict_to_update[key][tool][sDNA]
    #                                                      ,overrides_list(key, tool, sDNA) 
    #                                                      ,**kwargs(key, local_opts)  
    #                                                                        ) 
    #                                                 # TODO: add in tool name to key
    return local_metas


# First options options_manager.override (3), 
# user's installation specific options over (4), 
# hardcoded defaults above
#
# Use the above function to load the user's installation wide defaults by using
#  the primary meta from the hardcoded defaults.

if os.path.isfile(default_metas.config):
    #logger.debug('Before override: message == '+opts['options'].message)
    override_all_opts(args_dict = default_metas._asdict() 
                     # to get installation config.toml only once, for this call
                     ,local_opts = module_opts #  mutates opts
                     ,external_opts = {}  
                     ) 


    output.debug("After override: opts['options'].message == " 
          + module_opts['options'].message
          )
else:
    output.warning('Config file: %s not found. ' % default_metas.config)    
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
    module_opts['options'] = module_opts['options']._replace(python_exe = next(possible_pythons))

if not os.path.isfile(module_opts['options'].python_exe):
    raise ValueError('python_exe is not a file. ')

module_name = '.'.join([module_opts['options'].package_name 
                       ,module_opts['options'].sub_module_name
                       ]
                      )

if ( module_name in sys.modules
    and hasattr(sys.modules[module_name], 'logger') ):  
    #
    # Unlikely?
    #
    logger = sys.modules[module_name].logger
    #
    logger.warning('Using sys.modules[%s].logger. ' % module_name
                  +'Previous import failed?'
                  )
else:

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


get_Geom = tools.RhinoObjectsReader()
read_Usertext = tools.UsertextReader()
write_shapefile = tools.ShapefileWriter()
read_shapefile = tools.ShapefileReader()
write_Usertext = tools.UsertextWriter()
# bake_Usertext = UsertextBaker()
parse_data = tools.DataParser()
recolour_objects = tools.ObjectsRecolourer()
get_tool_names = dev_tools.ToolNamesGetter()
build_components = dev_tools.sDNA_GH_Builder()
sDNA_General_dummy_tool = tools.sDNA_GeneralDummyTool()
load_config = tools.ConfigManager()

runner.tools_dict.update(get_Geom = get_Geom
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
                        ,load_config = load_config
                        )

def import_sDNA_modules(opts, load_modules = launcher.load_modules, logger = logger):
    #type(dict, function, type[any]) -> tuple(str)
    """ Imports sDNAUISpec.py and runsdnacommand.py and stores them in
        opt['options'], when a new
        module name is specified in opts['metas'].sDNAUISpec or 
        opts['metas'].runsdnacommand.  

        Returns a tuple of the latest modules names.
    """
    
    metas = opts['metas']
    options = opts['options']

    logger.debug('metas.sDNAUISpec == %s ' % metas.sDNAUISpec
                +', metas.runsdnacommand == % ' % metas.runsdnacommand 
                )

    logger.debug('before update, options.sDNAUISpec == %s ' % options.sDNAUISpec
                +', options.run_sDNA == %s ' % options.run_sDNA
                )


    requested_sDNA = (metas.sDNAUISpec, metas.runsdnacommand)

    # To load new sDNA modules, specify the new module names in
    # metas.sDNAUISpec and metas.runsdnacommand

    # If they are loaded successfully the actual corresponding modules are
    # in options.sDNAUISpec and options.run_sDNA

    if ( isinstance(options.sDNAUISpec, options_manager.Sentinel) or
         isinstance(options.run_sDNA, options_manager.Sentinel) or
         (options.sDNAUISpec.__name__
                    ,options.run_sDNA.__name__) != requested_sDNA ):
        #
        # Import sDNAUISpec.py and runsdnacommand.py from metas.sDNA_paths
        sDNAUISpec, run_sDNA, _ = load_modules(m_names = requested_sDNA
                                              ,folders = metas.sDNA_paths
                                              ,logger = logger
                                              ,module_name_error_msg = "Please supply valid names of 'sDNAUISpec.py' "
                                                                       +"and 'runsdnacommand.py' files in "
                                                                       +"metas.sDNAUISpec and metas.runsdnacommand "
                                                                       +"respectively. "
                                              ,folders_error_msg = "Please supply names of valid folders in "
                                                                  +"metas.sDNA_paths.  "
                                                                  +"And ensure one of them contains "
                                                                  +"'sDNAUISpec.py' "
                                                                  +"and 'runsdnacommand.py' files in "
                                                                  +"metas.sDNAUISpec and metas.runsdnacommand "
                                                                  +"respectively. "
                                              ,modules_not_found_msg = "Please ensure one of the folders in "
                                                                      +"metas.sDNA_paths contain valid "
                                                                      +"'sDNAUISpec.py' "
                                                                      +"and 'runsdnacommand.py' files, as named in "
                                                                      +"metas.sDNAUISpec and metas.runsdnacommand "
                                                                      +"respectively. "
                                              )
        new_sDNA_key = tools.sDNA_key(opts)
        opts['metas'] = opts['metas']._replace(sDNA = new_sDNA_key)
        opts['options'] = opts['options']._replace(sDNAUISpec = sDNAUISpec
                                                  ,run_sDNA = run_sDNA 
                                                  ) 
        # we want to mutate the value in the original dict 
        # - so we can't use options for this assignment.  Latter for clarity.



def cache_sDNA_tool(compnt # instead of self
                   ,nick_name
                   ,mapped_name
                   ,name_map = default_metas.name_map
                   ,tools_dict = runner.tools_dict
                   ,update_sDNA = import_sDNA_modules
                   ):
    #type(type[any], str, str, dict, dict, function) -> None
    """ Custom tasks to be carried out by tool factory when no tool named 
        mapped_name is found in tools_dict.  
        
        Imports sDNAUISpec and runsdnacommand if necessary.  
        Builds a new sDNA tool from tools.py (and thence from sDNAUISpec.py).
        Inserts this new tool into tools_dict (only under its nick_name).
        Adds in any new tool option fields to the list of Params not to 
        be removed.  """
    sDNA = compnt.opts['metas'].sDNA
    sDNA_tool = tools.sDNA_ToolWrapper(mapped_name, nick_name, compnt.opts, update_sDNA)
    tools_dict[nick_name] =  sDNA_tool
    compnt.do_not_remove += tuple(sDNA_tool.tool_opts[sDNA]._fields)   

            



sDNA_GH_tools = list(runner.tools_dict.values())


class sDNA_GH_Component(smart_comp.SmartComponent):

    """ The main sDNA_GH Grasshopper Component class.  
    
    """
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
            inserter.insert_tool('before'
                                ,tools
                                ,Params
                                ,tool_to_insert = write_shapefile
                                ,is_target = is_class(tools.sDNA_ToolWrapper)
                                ,not_a_target = sDNA_GH_tools
                                ,tools_dict = runner.tools_dict
                                ,name_map = name_map
                                )

        if options.auto_read_Usertext:
            inserter.insert_tool('before'
                                ,tools
                                ,Params
                                ,tool_to_insert = read_Usertext
                                ,is_target = is_class(tools.ShapefileWriter)
                                ,not_a_target = []
                                ,tools_dict = runner.tools_dict
                                ,name_map = name_map
                                )   

        if options.auto_get_Geom:
            inserter.insert_tool('before'
                                ,tools
                                ,Params
                                ,tool_to_insert = get_Geom
                                ,is_target = is_class(tools.UsertextReader)
                                ,not_a_target = []
                                ,tools_dict = runner.tools_dict
                                ,name_map = name_map
                                )   

        if options.auto_read_Shp:
            inserter.insert_tool('after'
                                ,tools
                                ,Params
                                ,tool_to_insert = read_shapefile
                                ,is_target = is_class(tools.sDNA_ToolWrapper)
                                ,not_a_target = sDNA_GH_tools
                                ,tools_dict = runner.tools_dict
                                ,name_map = name_map
                                )
        
      
        
        if options.auto_plot_data: # already parses if Data not all colours
            inserter.insert_tool('after'                
                                ,tools
                                ,Params
                                ,tool_to_insert = recolour_objects
                                ,is_target = is_class(tools.ShapefileReader)
                                ,not_a_target = []
                                ,tools_dict = runner.tools_dict
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


        logger.debug('Updating Params: %s ' % tools)

        result = add_params.add_tool_params(Params
                                           ,tools
                                           ,do_not_add
                                           ,do_not_remove
                                           ,wrapper = self.script
                                           )

        return result


    def update_tools(self, nick_name = None):
        #type(type[any], str) -> type[any]

        if nick_name is None:
            nick_name = self.local_metas.nick_name

        tools = name_mapper.tool_factory(inst = self
                                        ,nick_name = nick_name
                                        ,name_map = self.opts['metas'].name_map
                                        ,tools_dict = runner.tools_dict
                                        ,tool_not_found = cache_sDNA_tool
                                        )
        # The component nick_name
        # is mapped to a tool_name or list of tool_name via name_map. 
        # cache_sDNA_tool is defined in this module.  It is called
        # for any tool_name not in tools_dict, and then looks for 
        # that tool_name in sDNAUISpec.py .  
        logger.debug(tools)
                

        #logger.debug(self.opts)
        logger.debug('Tool opts == %s ' % '\n'.join('%s : %s' % (k, v)
                                                    for k, v in self.opts.items()
                                                    if k not in ('options','metas')
                                                   ) 
                    )

        return tools






    def try_to_update_nick_name(self, new_name = None):
        if new_name is None:
            new_name = self.Attributes.Owner.NickName 
            # If this is run before __init__ has run, there is no 
            # Attributes attribute yet (ghenv.Component can be used instead).
            logger.debug('new_name == %s' % new_name)

        if ( (isinstance(self.local_metas.nick_name, options_manager.Sentinel)) 
              or (self.opts['metas'].cmpnts_change 
                  and self.local_metas.nick_name != new_name )):  
            #
            self.local_metas = self.local_metas._replace(nick_name = new_name)
            self.logger = logger.getChild(self.local_metas.nick_name)

            logger.info(' Component nick name changed to : ' 
                       +self.local_metas.nick_name
                       )
            return 'Name updated'
        logger.debug('Old name kept == %s' % self.local_metas.nick_name)

        return 'Old name kept'


    def __init__(self, *args, **kwargs):
        logger.debug('Calling sDNA_GH_Components parent initialiser')
        super(smart_comp.SmartComponent, self).__init__(self, *args, **kwargs)
        self.ghdoc = ghdoc
        # self.update_sDNA() moved to cache_sDNA_tool




    def script(self, **kwargs):        
        # update_Params is called from inside this method, so the input Params 
        # supplying the args will not updated until after they have been read.
        # If this method is not intended to crash on a missing input param,
        # it needs to accept anything (or a lack thereof) to run in the 
        # meantime until the params can be updated.  kwargs enable this.
        logger.debug('self.script started... \n')
        #logger.debug(kwargs)

        go = funcs.first_item_if_seq(kwargs.get('go', False), False) 
             # Input Params set 
             # to list acess so
             # strip away outer 
             # list container
        Data = kwargs.get('data', None)
        Geom = kwargs.get('geom', None)

        if 'file' in kwargs:
            kwargs['f_name'] = funcs.first_item_if_seq(kwargs['file'], '')
        elif 'f_name' not in kwargs:
            kwargs['f_name'] = ''
        else:
            kwargs['f_name'] = funcs.first_item_if_seq(kwargs['f_name'], '')

        external_opts = funcs.first_item_if_seq(kwargs.pop('opts', {}), {})

        external_local_metas = funcs.first_item_if_seq(kwargs.pop('local_metas'
                                                                 ,empty_NT
                                                                 )
                                                      ,empty_NT
                                                      )
        logger.debug(external_opts)

        gdm = funcs.first_item_if_seq(kwargs.get('gdm', {}))

        logger.debug(('gdm from start of RunScript == %s' % gdm)[:80])
        
        result = self.try_to_update_nick_name()
        if result == 'Name updated': # True 1st run after __init__
            nick_name = self.local_metas.nick_name
            if (nick_name.lower()
                         .replace('_','')
                         .replace(' ','') == 'sdnageneral'
                and 'tool' in kwargs ):
                #
                nick_name = kwargs['tool']
            self.my_tools = self.update_tools(nick_name)
        
            self.tools = self.auto_insert_tools(self.my_tools, self.Params)  

            logger.debug('self.tools == %s ' % self.tools)

            extra_params_added = self.update_Params() #self.Params, self.tools)

            if extra_params_added != 'No extra Params required. ':
                # Extra Input Params are actually OK as RunScript has already 
                # been called already by this point.
                logger.debug('Output Params updated.  Returning None.  ')
                return (None,) * len(self.Params.Output)
                # Grasshopper components can have a glitchy one off error if
                # not-None outputs are given to params that 
                # have just been added, in the same RunScript call.  In our 
                # design the user probably doesn't want the new tool and 
                # updated component params to run before they've had chance to
                # look at them, even if 'go' still is connected to True.  But 
                # e.g. config, and anything there that they already configured
                # and saved should still run when the canvas loads. 

        
        synced = self.local_metas.sync
        #######################################################################
        logger.debug('kwargs == %s ' % kwargs)
        self.local_metas = override_all_opts(
                                 args_dict = kwargs
                                ,local_opts = self.opts # mutated
                                ,external_opts = external_opts 
                                ,local_metas = self.local_metas 
                                ,external_local_metas = external_local_metas
                                )
        #######################################################################
        kwargs['opts'] = self.opts
        kwargs['l_metas'] = self.local_metas

        logger.debug('Opts overridden....    ')
        logger.debug(self.local_metas)
        
        if (self.opts['metas'].update_path 
            or not os.path.isfile(self.opts['options'].path) ):

            path = checkers.get_path(fallback = __file__,  inst = self)

            self.opts['options'] = self.opts['options']._replace(path = path)

        if self.opts['metas'].cmpnts_change: 
            
            if self.local_metas.sync != synced:
                if self.local_metas.sync:
                    self.opts = module_opts #resync
                else:
                    self.opts = self.opts.copy() #desync
                    #

        if tools.sDNA_key(self.opts) != self.opts['metas'].sDNA:
            has_any_sDNA_tools = False
            for tool in self.tools:
                if isinstance(tool, tools.sDNA_ToolWrapper):
                    has_any_sDNA_tools = True
                    tool.update_tool_opts_and_syntax()
                    # this isn't necessary just to run these tools later.
                    # they're just being updated now so they can get their 
                    # inputs from sDNAUISpec, and so the component's input 
                    # Params can be updated to reflect the new sDNA

            if has_any_sDNA_tools:
                #self.Params = 
                self.update_Params()#self.Params, self.tools)
                # to add in any new sDNA inputs to the component's Params
            
            return (None,) * len(self.Params.Output)
            # to allow running the component again, with any new inputs
            # supplied as Params


        logger.debug(go)

        if go is True: 
            if not isinstance(self.tools, list):
                msg = 'self.tools is not a list'
                logger.error(msg)
                raise TypeError(msg)

            invalid_tools = [tool for tool in self.tools 
                                  if not isinstance(tool, runner.RunnableTool)
                            ]
            if invalid_tools:
                msg = ('Tools are not runner.RunnableTool : %s' % invalid_tools)
                logger.error(msg)
                raise ValueError(msg)

            logger.debug('my_tools == $s' % self.tools)



            geom_data_map = gdm_from_GH_Datatree.gdm_from_DataTree_and_list(Geom
                                                                           ,Data
                                                                           )



            logger.debug('type(geom_data_map) == %s ' % geom_data_map)
            
            logger.debug('Before merge gdm[:3] == %s ' % gdm.items()[:3])


            logger.debug('Before merge geom_data_map[:3] == %s ' 
                        % geom_data_map.items()[:3]
                        )

            gdm = gdm_from_GH_Datatree.override_gdm(
                                        gdm
                                       ,geom_data_map
                                       ,self.opts['options'].merge_subdicts
                                       )

            logger.debug('After merge type(gdm) == %s ' % type(gdm))
            
            logger.debug('After merge gdm[:3] == %s ' % gdm.items()[:3])

            kwargs['gdm'] = gdm

            ##################################################################
            ret_vals_dict = runner.run_tools(self.tools, kwargs)
            ##################################################################
            gdm = ret_vals_dict.get('gdm', {})
            if isinstance(gdm, dict):
                logger.debug('Converting gdm to Data and Geometry')
                (NewData
                ,NewGeometry
                ) = gdm_from_GH_Datatree.dict_from_DataTree_and_lists(gdm)
                                        
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
            logger.debug('go == %s ' % go)
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
    script.input_params = lambda : tools.sDNA_GH_Tool.params_list(['go', 'opts'])
    script.output_params = lambda : tools.sDNA_GH_Tool.params_list(['OK', 'opts'])



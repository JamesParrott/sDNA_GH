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
__version__ = '0.10'

import sys
import os
from collections import namedtuple, OrderedDict
import locale

from Grasshopper.Kernel.Parameters import Param_ScriptVariable, Param_Boolean

from . import launcher
from .custom import options_manager
from .custom import logging_wrapper
from .custom import data_cruncher 
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


try:
    basestring #type: ignore
except NameError:
    basestring = str

output = launcher.Output()

# Pre Python 3.6 the order of an OrderedDict isn't necessarily that of the 
# arguments in its constructor so we build our options and metas namedtuples
# from a class, to avoid re-stating the order of the keys, and to run other
# code too (e.g. checks, validations and assertions).

DEFAULT_NAME_MAP = OrderedDict([('Read_Geom', 'get_Geom')
                               ,('Read_Usertext', 'read_User_Text')
                               ,('Write_Shp', 'write_shapefile')
                               ,('Read_Shp', 'read_shapefile')
                               ,('Write_Usertext', 'write_User_Text')
                               ,('Parse_Data', 'parse_data')
                               ,('Config', 'config')
                               ,('Self_test', launcher.SELFTEST)
                               #
                               ,('sDNA_Integral', 'sDNAIntegral')
                               ,('sDNA_Skim', 'sDNASkim')
                               ,('sDNA_Int_From_OD', 'sDNAIntegralFromOD')
                               ,('sDNA_Geodesics', 'sDNAGeodesics')
                               ,('sDNA_Hulls', 'sDNAHulls')
                               ,('sDNA_Net_Radii', 'sDNANetRadii')
                               ,('sDNA_Access_Map', 'sDNAAccessibilityMap')
                               ,('sDNA_Prepare', 'sDNAPrepare')
                               ,('sDNA_Line_Measures', 'sDNALineMeasures')
                               ,('sDNA_Learn', 'sDNALearn')
                               ,('sDNA_Predict', 'sDNAPredict')
                               ]
                              )

LANGUAGE_CODE = locale.getdefaultlocale()[0].lower()  # e.g. 'en_gb' or 'en_us'

if 'en' in LANGUAGE_CODE and 'us' in LANGUAGE_CODE:
    Recolour = 'Recolor'
else:
    Recolour = 'Recolour'


DEFAULT_NAME_MAP[Recolour+'_Objects'] = 'recolour_objects' #Dynamic calculation
                                                           # of constant's value


class HardcodedMetas(tools.sDNA_ToolWrapper.Metas
                    ,tools.ConfigManager.Metas # has config.toml path
                    ): 
    # config from 
    add_new_opts = False
    cmpnts_change = False
    strict = True
    check_types = True
    sDNAUISpec = 'sDNAUISpec'  #Names of sDNA modules to import

    runsdnacommand = 'runsdnacommand' # only used for .map_to_string. 
                            # Kept in case we use work out how
                            # to run runsdnacommand.runsdnacommand in future 
                            # with an env, while being able to pipe 
                            # sDNA's stderr and stdout to the sDNA_GH logger
    sDNA = ''  # Read only.  Auto updates from above.
    python = ''
    #python = r'C:\Python27\python.exe' 

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


    name_map = DEFAULT_NAME_MAP.copy()
                   # Long names for some Rhino installs that use component Name not Nickname
                   # (these can be removed if the components are all rebuilt s.t. name == nickname) 
    name_map.update(OrderedDict([('Read Rhino geometry', 'get_Geom')
                                ,('Read User Text', 'read_User_Text')
                                ,('Write shapefile', 'write_shapefile')
                                ,('Read shapefile', 'read_shapefile')
                                ,('Write User Text', 'write_User_Text')
                                ,('Parse data', 'parse_data')
                                #
                                ,('Integral Analysis', 'sDNAIntegral')
                                ,('Skim Matrix', 'sDNASkim')
                                ,('Integral from OD Matrix (assignment model)', 'sDNAIntegralFromOD')
                                ,('Geodesics', 'sDNAGeodesics')
                                ,('Convex Hulls', 'sDNAHulls')
                                ,('Network Radii', 'sDNANetRadii')
                                ,('Specific Origin Accessibility Maps', 'sDNAAccessibilityMap')
                                ,('Prepare network', 'sDNAPrepare')
                                ,('Individual Line Measures', 'sDNALineMeasures')
                                ,('Learn', 'sDNALearn')
                                ,('Predict', 'sDNAPredict')                   
                                ]
                               )
                   )

    name_map[Recolour+' objects'] = 'recolour_objects'
                          
    categories = {'get_Geom'         : 'Extra'
                 ,'read_User_Text'   : 'Data'
                 ,'write_shapefile'  : '.shp'
                 ,'read_shapefile'   : '.shp'
                 ,'write_User_Text'  : 'Data'
                 ,'parse_data'       : 'Plot'
                 ,'recolour_objects' : 'Plot'
                 ,'sDNA_General'     : 'Dev'
                 ,'Unload_sDNA'      : 'Dev'
                 ,launcher.SELFTEST  : 'Dev'
                 ,'config'           : 'Extra'
                 }

    category_abbrevs = {'Analysis geometry' : 'Geom'}
    make_new_comps = True
    move_user_objects = False


#######################################################################################
if (not isinstance(HardcodedMetas.config, basestring) 
    or not os.path.isfile(HardcodedMetas.config)):
    output.warning('Config file: %s not found. ' % HardcodedMetas.config 
                +'If no sDNA install or Python is automatically found (or to '
                +'choose a different one), or to create an options file '
                +' please place a Config component.  '
                +'To use sDNA_GH with a specific sDNA installation, firstly '
                +'ensure sDNA_paths contains only your sDNA folder, and secondly set '
                +'sdnauispec and runsdnacommand to the names of the sdnauispec.py and '
                +'runsdnacommand.py files respectively (to use more than one sDNA you '
                +'must rename these files in any extra versions).  '
                +'To use sDNA_GH with a specific python.exe, set python to its path or '
                +'to search for it ensure python_exes only '
                +'contains its name, and python_paths only contains the path of its '
                +' folder.  '
                +'To save these and any other options, set go to true on the Config '
                +'component. '
                +'If no project options file is specified in save_to, an '
                +'installation wide options file (config.toml) will be created. '
                )  
#######################################################################################


FILE_TO_WORK_FROM = checkers.get_path(fallback = __file__)

class HardcodedOptions(logging_wrapper.LoggingOptions
                      ,tools.RhinoObjectsReader.Options
                      ,tools.UsertextReader.Options
                      ,tools.ShapefileWriter.Options
                      ,tools.ShapefileReader.Options
                      ,tools.UsertextWriter.Options
                      ,tools.DataParser.Options
                      ,tools.ObjectsRecolourer.Options
                      ,tools.sDNA_ToolWrapper.Options
                      ,tools.ConfigManager.Options
                      ):            
    ###########################################################################
    #System
    #
    platform = 'NT' # in {'NT','win32','win64'} only supported for now
    encoding = 'utf-8' # For shapefiles only, not toml files or names.csv.
                       # Used by .custom.pyshp_wrapper
                       # get_fields_recs_and_shapes and write_iterable_to_shp
    package_name = os.path.basename(os.path.dirname(__file__))
    sub_module_name, _ = os.path.splitext(os.path.basename(__file__))
    #
    ###########################################################################
    #
    # Automatic tool insertion rules ('smart' tools)
    #
    auto_get_Geom = False
    auto_read_User_Text = False
    auto_write_Shp = False
    auto_read_Shp = False
    #auto_parse_data = False  # not used.  ObjectsRecolourer parses if req anyway
    auto_plot_data = False
    ###########################################################################
    #
    # Overrides for .custom.logging_wrapper
    #
    path = FILE_TO_WORK_FROM
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
    prepped_fmt = '{name}_prepped'
    output_fmt = '{name}_output'   
    del_after_sDNA = True
    strict_no_del = False # Also in ShapefileReader
    ###########################################################################    
    #
    # Overrides for RhinoObjectsReader
    #
    selected = False
    layer = ''
    merge_subdicts = True
    #
    #
    ###########################################################################
    #
    #     Shapefiles
    #     Application specific overrides for .custom.pyshp_wrapper
    #
    shp_type = 'POLYLINEZ' # Also in RhinoObjectsReader, ShapefileWriter
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
    use_memo = False # Use the 'M' field code in Shapefiles for un-coerced data
    #
    # get_filename
    overwrite_shp = False
    max_new_files = 20
    suppress_warning = True     
    dupe_file_suffix = '{name}_({number})'
    #
    # ensure_correct & write_iterable_to_shp
    extra_chars = 2
    #
    # write_iterable_to_shp
    field_size = 30
    cache_iterable= False
    uuid_field = 'Rhino3D_' # 'object_identifier_UUID_'  
    # also in ShapefileReader, UsertextWriter  
    uuid_length = 36 # 32 in 5 blocks (2 x 6 & 2 x 5) with 4 separator characters.
    num_dp = 10 # decimal places
    min_sizes = True
    #
    ###########################################################################
    #
    # Overrides for ShapefileWriter
    #
    input_key_str = '{name}'
    #30,000 characters tested.
    output_shp = ''
    ###########################################################################
    #
    # Overrides for ShapefileReader
    #
    bake = False
    new_geom = False
    del_after_read = True
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
    if re_normaliser not in data_cruncher.VALID_RE_NORMALISERS:
        raise ValueError('%s must be in %s' 
                        %(re_normaliser, data_cruncher.VALID_RE_NORMALISERS)
                        )
    class_bounds = [options_manager.Sentinel('class_bounds is automatically '
                                            +'calculated by sDNA_GH unless '
                                            +'overridden.  '
                                            )
                   ] 
    # e.g. [2000000, 4000000, 6000000, 8000000, 10000000, 12000000]

    num_classes = 7
    class_spacing = 'quantile' 
    if class_spacing not in tools.DataParser.Options.valid_class_spacings:
        raise ValueError('%s must be in %s' 
                        %(class_spacing
                         ,tools.DataParser.Options.valid_class_spacings
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
    line_width = 4 # millimetres? 
    ###########################################################################
    #
    # Options override system test field
    #
    message = 'Hardcoded default options from tools.py'



class HardcodedLocalMetas(object):
    sync = True    
    read_only = True
    no_state = True


namedtuple_from_class = options_manager.namedtuple_from_class

DEFAULT_METAS = namedtuple_from_class(HardcodedMetas, 'Metas')
DEFAULT_OPTIONS = namedtuple_from_class(HardcodedOptions, 'Options')
DEFAULT_LOCAL_METAS = namedtuple_from_class(HardcodedLocalMetas, 'LocalMetas')

EMPTY_NT = namedtuple('Empty','')(**{})

DEFAULT_OPTS = OrderedDict(metas = DEFAULT_METAS
                          ,options = DEFAULT_OPTIONS
                          )                

module_opts = DEFAULT_OPTS.copy()           

output.debug(module_opts['options'].message)







#########################################################################
#
override_namedtuple = options_manager.override_namedtuple
#
def override_all_opts(local_opts #  mutated
                     ,overrides
                     ,args_dict
                     ,local_metas = DEFAULT_LOCAL_METAS
                     ,external_local_metas = EMPTY_NT
                     ):
    #type(dict, list, dict, namedtuple, namedtuple) -> dict, namedtuple
    """    
    The options override function for sDNA_GH.  

    1) args_dict is a flat dict, e.g. from Input Params on the component.

    2) Local_opts needs to be, and external_opts may be, a string keyed
       nested dict of namedtuples   
    
    3) Only primary metas (config.toml files) in args_dict are loaded.  

    4) The nested dict from config.toml will be a nested dict of dicts and
       possibly other general data fields.

    5) The named tuple Local metas will be overridden with external_local_metas 
       if present, and is returned.
    
    Mutates: local_opts
    Returns: local_metas, local_opts
    """

    metas = local_opts['metas']

    args_dict = OrderedDict((key, value) 
                            for key, value in args_dict.items() 
                            if value is not None
                           )




    project_file_opts = {}
    if (args_dict and 
        'config' in args_dict and 
        isinstance(args_dict['config'], basestring)):
        #
        project_file_opts = options_manager.dict_from_toml_file(args_dict['config'])
    else:
        msg = 'No config specified in args_dict'
        output.debug(msg + ' == %s' % args_dict.keys())


    ext_local_metas_dict = external_local_metas._asdict()

    old_sync = local_metas.sync

    ###########################################################################
    # Update syncing / de-syncing controls in local_metas
    #
    local_metas_overrides_list = [ext_local_metas_dict]
    local_metas_overrides_list += [override_['local_metas'] 
                                   for override_ in overrides
                                   if 'local_metas' in override_
                                  ]
    local_metas_overrides_list += [project_file_opts.get('local_metas',{})
                                  ,args_dict
                                  ]

    local_metas = override_namedtuple(local_metas
                                     ,local_metas_overrides_list
                                     ,**metas._asdict()
                                     ) 


    ###########################################################################


    output.debug('overrides == %s' % overrides)

    overrides += [project_file_opts, args_dict]

    output.debug('overrides == %s' 
                % [override_.keys() for override_ in overrides]
                )


    if local_metas.sync:
        local_opts = module_opts
    else:
        if local_metas.read_only: 
            overrides = [module_opts] + overrides

        if local_metas.no_state:
            local_opts = {} # Clear the state
            if not local_metas.read_only: 
                installation_opts = options_manager.dict_from_toml_file(metas.config)
                overrides = [DEFAULT_OPTS, installation_opts] + overrides # rebuild the state
        elif old_sync:  # Desynchronise
            local_opts = module_opts.copy()


    metas_overrides = map(lambda x : x.pop('metas', x), overrides)

    metas = local_opts['metas'] = options_manager.override_namedtuple(
                                                            local_opts['metas']
                                                           ,metas_overrides
                                                           ,**metas._asdict()
                                                           )

    for override in overrides:
        tools.update_opts(current_opts = local_opts
                         ,override = override
                         ,metas = metas
                         )
        output.debug('override.keys() == %s' % override.keys())
        output.debug('local_opts.keys() == %s' % local_opts.keys())


    #output.debug('local_opts (opts) == %s' % local_opts)

    return local_opts, local_metas

##############################################################################
# First options options_manager.override, reading the
# user's installation wide options stored in the
# hardcoded defaults above under config.
#

if os.path.isfile(DEFAULT_METAS.config):
    #output.debug('Before override: message == %s' % opts['options'].message)
    installation_opts = options_manager.dict_from_toml_file(DEFAULT_METAS.config)

    module_opts, setup_default_local_metas = override_all_opts(
                                                 local_opts = module_opts
                                                ,overrides = [installation_opts]
                                                ,args_dict = {}  
                                                )
    output.debug(module_opts)

    output.debug("After override: opts['options'].message == %s" 
                % module_opts['options'].message
                )
else:
    output.warning('Config file: %s not found. ' % DEFAULT_METAS.config 
                  +'If no sDNA install or Python is automatically found (or to '
                  +'choose a different one), or to create an options file '
                  +' please place a Config component.  '
                  +'To use sDNA_GH with a specific sDNA installation, firstly '
                  +'ensure sDNA_paths contains only your sDNA folder, and secondly set '
                  +'sdnauispec and runsdnacommand to the names of the sdnauispec.py and '
                  +'runsdnacommand.py files respectively (to use more than one sDNA you '
                  +'must rename these files in any extra versions).  '
                  +'To use sDNA_GH with a specific python.exe, set python to its path or '
                  +'to search for it ensure python_exes only '
                  +'contains its name, and python_paths only contains the path of its '
                  +' folder.  '
                  +'To save these and any other options, set go to true on the Config '
                  +'component. '
                  +'If no project options file is specified in save_to, an '
                  +'installation wide options file (config.toml) will be created '
                  +'for you for all future use.  '
                  )    
#
#######################################################################

#######################################################################
#
# Set up root logger
#
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
    # all their loggers are children of this module's logger:
    logger, log_file_handler, console_log_handler, _ = logging_wrapper.new_Logger(
                                               stream = None
                                              ,options = module_opts['options']
                                              ) 

     # Flushes cached log messages to above handlers

    logger.debug('Logging set up in sDNA_GH package ')

output.set_logger(logger, flush = True)

############################################################################


get_Geom = tools.RhinoObjectsReader(opts = module_opts)
read_User_Text = tools.UsertextReader(opts = module_opts)
write_shapefile = tools.ShapefileWriter(opts = module_opts)
read_shapefile = tools.ShapefileReader(opts = module_opts)
write_User_Text = tools.UsertextWriter(opts = module_opts)
parse_data = tools.DataParser(opts = module_opts)
recolour_objects = tools.ObjectsRecolourer(opts = module_opts)
build_components = dev_tools.sDNA_GH_Builder(opts = module_opts)
sDNA_General_dummy_tool = tools.sDNA_GeneralDummyTool(opts = module_opts)
config = tools.ConfigManager(opts = module_opts)

runner.tools_dict.update(get_Geom = get_Geom
                        ,read_User_Text = read_User_Text
                        ,write_shapefile = write_shapefile
                        ,read_shapefile = read_shapefile
                        ,write_User_Text = write_User_Text
                        ,parse_data = parse_data
                        ,recolour_objects = recolour_objects 
                        ,Build_components = build_components
                        ,sDNA_General = sDNA_General_dummy_tool
                        ,config = config
                        )

               

####################################################################
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
do_not_remove += DEFAULT_METAS._fields
do_not_remove += DEFAULT_OPTIONS._fields
do_not_remove += DEFAULT_LOCAL_METAS._fields
######################################################################





def cache_sDNA_tool(compnt # instead of self
                   ,nick_name
                   ,mapped_name
                   ,name_map = None # unused; just for tool_not_found ArgSpec
                   ,tools_dict = runner.tools_dict # mutated
                   ):
    #type(type[any], str, str, dict, dict, function) -> None
    """ Custom tasks to be carried out by tool factory when no tool named 
        mapped_name is found in tools_dict.  
        
        Imports sDNAUISpec and runsdnacommand if necessary.  
        Builds a new sDNA tool from tools.py (and thence from sDNAUISpec.py).
        Inserts this new tool into tools_dict (only under its nick_name).
        Adds in any new tool option fields to the list of Params not to 
        be removed.  

        Appends to Mutates compnt.do_not_remove and adds item to tools_dict.
    """
    sDNA_tool = tools.sDNA_ToolWrapper(opts = compnt.opts
                                      ,tool_name = mapped_name
                                      ,nick_name = nick_name
                                      ,component = compnt
                                      )                                      
    tools_dict[nick_name] =  sDNA_tool
    sDNA = compnt.opts['metas'].sDNA # updated by update_sDNA, when called by 
                                # sDNA_ToolWrapper.update_tool_opts_and_syntax
    compnt.do_not_remove += tuple(sDNA_tool.defaults.keys()) 
    compnt.tools_default_opts.update(sDNA_tool.default_tool_opts)

            



sDNA_GH_tools = list(runner.tools_dict.values())


class sDNA_GH_Component(smart_comp.SmartComponent):

    """ The main sDNA_GH Grasshopper Component class.  
    """
    # Options from module, from defaults and installation config.toml
    opts = module_opts  
    local_metas = setup_default_local_metas   # immutable.  controls syncing /
                                              # de-syncing / read / write of the
                                              # above (opts).
                                              # Although local, it can be set on 
                                              # groups of components using the 
                                              # default section of a project 
                                              # config.toml, or passed as a
                                              # Grasshopper parameter between
                                              # components.
    tools_default_opts = {}
    #sDNA_GH_path = sDNA_GH_path
    #sDNA_GH_package = sDNA_GH_package
    do_not_remove = do_not_remove
    
    @property
    def metas(self):
        return self.opts['metas']

    @property
    def options(self):
        return self.opts['options']



    def auto_insert_tools(self, my_tools = None, Params = None):
        #type(type[any], list) -> None
        if my_tools is None:
            my_tools = self.my_tools
        my_tools = my_tools[:] if isinstance(my_tools, list) else [my_tools]

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
                                ,my_tools
                                ,Params
                                ,tool_to_insert = write_shapefile
                                ,is_target = is_class(tools.sDNA_ToolWrapper)
                                ,not_a_target = sDNA_GH_tools
                                ,tools_dict = runner.tools_dict
                                ,name_map = name_map
                                )

        if options.auto_read_User_Text:
            inserter.insert_tool('before'
                                ,my_tools
                                ,Params
                                ,tool_to_insert = read_User_Text
                                ,is_target = is_class(tools.ShapefileWriter)
                                ,not_a_target = []
                                ,tools_dict = runner.tools_dict
                                ,name_map = name_map
                                )   

        if options.auto_get_Geom:
            inserter.insert_tool('before'
                                ,my_tools
                                ,Params
                                ,tool_to_insert = get_Geom
                                ,is_target = is_class(tools.UsertextReader)
                                ,not_a_target = []
                                ,tools_dict = runner.tools_dict
                                ,name_map = name_map
                                )   

        if options.auto_read_Shp:
            inserter.insert_tool('after'
                                ,my_tools
                                ,Params
                                ,tool_to_insert = read_shapefile
                                ,is_target = is_class(tools.sDNA_ToolWrapper)
                                ,not_a_target = sDNA_GH_tools
                                ,tools_dict = runner.tools_dict
                                ,name_map = name_map
                                )
        
      
        
        if options.auto_plot_data: # already parses if Data not all colours
            inserter.insert_tool('after'                
                                ,my_tools
                                ,Params
                                ,tool_to_insert = recolour_objects
                                ,is_target = is_class(tools.ShapefileReader)
                                ,not_a_target = []
                                ,tools_dict = runner.tools_dict
                                ,name_map = name_map
                                ) 
                                          
        return my_tools



    def update_Params(self
                     ,Params = None
                     ,tools = None
                     ):
        #type(type[any], type[any, list]) -> type[any]

        if Params is None:
            Params = self.Params
            # If this is run before __init__ has finished .Params may not be
            # there yet.  But it is still available at ghenv.Component.Params
            # if ghenv is available (ghenv is not available here in a module).

        if not hasattr(self, 'params_adder'):
            self.params_adder = add_params.ParamsToolAdder(self.Params)

        if tools is None:
            tools = self.tools


        logger.debug('Updating Params: %s ' % tools)

        result = self.params_adder.add_tool_params(Params
                                                  ,tools
                                                  ,do_not_add
                                                  ,do_not_remove
                                                  ,wrapper = self.script
                                                  )

        return result


    def update_tools(self, nick_name = None):
        #type(type[any], str) -> type[any]

        if nick_name is None:
            nick_name = self.nick_name

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
        logger.debug('Tool opts == ' + '\n'.join('%s : %s' % (k, v)
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

        if ( (isinstance(self.nick_name, options_manager.Sentinel)) 
              or (self.opts['metas'].cmpnts_change 
                  and self.nick_name != new_name )):  
            #
            self.nick_name = new_name
            self.logger = logger.getChild(self.nick_name)

            logger.info(' Component nick name changed to : ' 
                       +self.nick_name
                       )
            return 'Name updated'
        logger.debug('Old name kept == %s' % self.nick_name)

        return 'Old name kept'


    def __init__(self, *args, **kwargs):
        logger.debug('Calling sDNA_GH_Components parent initialiser')
        super(sDNA_GH_Component, self).__init__()
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

        go = smart_comp.first_item_if_seq(kwargs.pop('go', False), False) 
             # Input Params set 
             # to list access so
             # strip away outer 
             # list container
        Data = kwargs.pop('Data', None)
        Geom = kwargs.pop('Geom', None)

        if  'file' in kwargs:
            kwargs['f_name'] = smart_comp.first_item_if_seq(kwargs['file'], '')
        elif 'f_name' not in kwargs:
             kwargs['f_name'] = ''
        else:
             kwargs['f_name'] = smart_comp.first_item_if_seq(kwargs['f_name'], '')

        external_opts = smart_comp.first_item_if_seq(kwargs.pop('opts', {}), {})

        external_local_metas = smart_comp.first_item_if_seq(kwargs.pop('local_metas'
                                                                 ,EMPTY_NT
                                                                 )
                                                      ,EMPTY_NT
                                                      )
        logger.debug(external_opts)

        gdm = smart_comp.first_item_if_seq(kwargs.get('gdm', {}))

        logger.debug(('gdm from start of RunScript == %s' % gdm)[:80])
        
        result = self.try_to_update_nick_name()
        nick_name = self.nick_name

        if result == 'Name updated': # True 1st run after __init__
            if (nick_name.lower()
                         .replace('_','')
                         .replace(' ','') == 'sdnageneral'
                and 'tool' in kwargs ):
                #
                nick_name = kwargs['tool']
            self.my_tools = self.update_tools(nick_name)
        
            self.tools = self.auto_insert_tools(self.my_tools, self.Params)  

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

                    
        logger.info('Tools == %s ' % self.tools)

        sync = self.local_metas.sync
        #######################################################################
        logger.debug('kwargs.keys() == %s ' % kwargs.keys())
        self.opts, self.local_metas = override_all_opts(
                                 local_opts = self.opts # mutated
                                ,overrides = [self.tools_default_opts, external_opts]
                                ,args_dict = kwargs
                                ,local_metas = self.local_metas 
                                ,external_local_metas = external_local_metas
                                )
        #######################################################################
        kwargs['opts'] = self.opts
        kwargs['l_metas'] = self.local_metas

        for handler, level in ((console_log_handler
                               ,self.opts['options'].log_console_level
                               )
                              ,(log_file_handler
                               ,self.opts['options'].log_file_level
                               )
                              ):
            logging_wrapper.set_handler_level(handler, level)


        logger.debug('Opts overridden....    ')
        logger.debug(self.opts)
        logger.debug(self.local_metas)
        
        if (self.metas.update_path 
            or not os.path.isfile(self.options.path) ):

            path = checkers.get_path(fallback = __file__,  inst = self)
            self.opts['options'] = self.opts['options']._replace(path = path)

        if self.metas.cmpnts_change: 
            
            if self.local_metas.sync != sync:
                if self.local_metas.sync:
                    self.opts = module_opts #re-sync
                else:
                    self.opts = self.opts.copy() #de-sync
                    # noisy sentinels and imported modules are in 
                    # opts['options'].sDNA so best to avoid deep copying.

        if tools.sDNA_key(self.opts) != self.opts['metas'].sDNA:
            # If new sDNA module names are specified or metas.sDNA is None
            has_any_sDNA_tools = False
            for tool in self.tools:
                if isinstance(tool, tools.sDNA_ToolWrapper):
                    has_any_sDNA_tools = True
                    tool.update_tool_opts_and_syntax(opts = self.opts)
                    # This isn't necessary just to run these tools later.
                    # They're just being updated now so they can get their 
                    # inputs from sDNAUISpec the next run, and so the 
                    # component's input 
                    # Params can be updated to reflect the new sDNA

            if has_any_sDNA_tools:
                #self.Params = 
                self.update_Params()#self.Params, self.tools)
                # to add in any new sDNA inputs to the component's Params
            
                logger.info('sDNA has been updated.  '
                           +'Returning None to allow new Params to be set. '
                           )
                return (None,) * len(self.Params.Output)
                # to allow running the component again, with any new inputs
                # supplied as Params
            elif (self.metas.make_new_comps and
                  nick_name.replace(' ','').replace('_','').lower() == 'config'):
                #
                tools.import_sDNA(opts = self.opts)
                logger.info('Building missing sDNA components (if any). ')
                tools.build_missing_sDNA_components(opts = self.opts
                                                   ,category_abbrevs = self.metas.category_abbrevs
                                                   ,plug_in_name = dev_tools.plug_in_name #'sDNA'
                                                   ,plug_in_sub_folder = dev_tools.plug_in_sub_folder # 'sDNA_GH' 
                                                   ,user_objects_location = tools.default_user_objects_location
                                                   ,add_to_canvas = False
                                                   ,overwrite = True
                                                   ,move_user_objects = self.metas.move_user_objects
                                                   )



        logger.debug(go)

        if go is True: 
            if not hasattr(self, 'tools'):
                msg = 'component name: %s unrecognised? ' % nick_name
                msg += 'sDNA_GH has not found any tools to run.  '
                msg += 'Change component name, or define tools for name in name_map.'
                logger.error(msg)
                raise ValueError(msg)                
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

            logger.debug('my_tools == %s' % self.tools)



            geom_data_map = gdm_from_GH_Datatree.gdm_from_DataTree_and_list(Geom
                                                                           ,Data
                                                                           )



            logger.debug('type(geom_data_map) == %s ' % type(geom_data_map))
            
            logger.debug('Before merge gdm[:3] == %s ' % gdm.items()[:3])


            logger.debug('Before merge geom_data_map[:3] == %s ' 
                        % geom_data_map.items()[:3]
                        )

            gdm = gdm_from_GH_Datatree.override_gdm(
                                        gdm  # External one from args
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
            sDNA = self.opts['metas'].sDNA
            if self.nick_name in self.opts:
                tool_opts = self.opts[self.nick_name]
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
        ret_vals_dict['opts'] = [self.opts.copy()] # could become external_opts
                                                   # in another component
        ret_vals_dict['l_metas'] = self.local_metas #immutable

        logger.debug('Returning from self.script. opts.keys() == %s ' % self.opts.keys() )
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

    param_infos = (('OK', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: tools ran successfully.  '
                                           +'false: tools did not run, or '
                                           +'there was an error.'
                                           )
                            ))
                  ,('go', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: runs tools.  false: do not '
                                           +'run tools but still read other '
                                           +'Params.'
                                           )
                            ))
                  ,('opts', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('sDNA_GH options data structure. '
                                           +'Python dictionary.'
                                           )
                            ))
                  )                                          
    script.input_params = tools.list_of_param_infos(['go', 'opts'], param_infos)
    script.output_params = tools.list_of_param_infos(['OK', 'opts'], param_infos)




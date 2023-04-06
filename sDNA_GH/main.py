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
__version__ = '2.3.0'

import sys
import os
import collections
if hasattr(collections, 'Iterable'):
    Iterable = collections.Iterable 
else:
    import collections.abc
    Iterable = collections.abc.Iterable
import functools
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
from .custom.skel.tools.helpers import funcs                         
from .custom.skel.tools import inserter 
from .custom.skel.tools import runner
from .custom.skel.tools import name_mapper
from .custom.skel import add_params
from .custom import tools
from .dev_tools import dev_tools



namedtuple, OrderedDict = collections.namedtuple, collections.OrderedDict

try:
    basestring #type: ignore
except NameError:
    basestring = str

output = launcher.Output()

# Pre Python 3.6 the order of an OrderedDict isn't necessarily that of the 
# arguments in its constructor so we build our options and metas namedtuples
# from a class, to avoid re-stating the order of the keys, and to run other
# code too (e.g. checks, validations and assertions).


class HardcodedMetas(tools.sDNA_ToolWrapper.Metas
                    ,tools.ConfigManager.Metas # has config.toml path
                    ): 
    # config from tools.ConfigManager.Metas
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

    language_code = locale.getdefaultlocale()[0].lower()  # e.g. 'en_gb' or 'en_us'

    if 'en' in language_code and 'us' in language_code:
        Recolour = 'Recolor'
    else:
        Recolour = 'Recolour'


    DEFAULT_NAME_MAP[Recolour+'_Objects'] = 'recolour_objects' # tool name

    skip_caps = True
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
                 ,'Unload_sDNA'      : 'Dev'
                 ,launcher.SELFTEST  : 'Dev'
                 ,'config'           : 'Extra'
                 }

    category_abbrevs = {'Analysis geometry' : 'Geom'}
    make_new_comps = True
    move_user_objects = False
    make_advanced = False


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

class AutoRunToolOptions(object):
    auto_get_Geom = False
    auto_read_User_Text = False
    auto_write_Shp = True
    auto_read_Shp = True
    #auto_parse_data = False  # not used.  ObjectsRecolourer parses if req anyway
    auto_plot_data = False

DEFAULT_AUTOS = options_manager.namedtuple_from_class(AutoRunToolOptions,'Autos')

def auto_run_tool_options(options):
    retval = tuple((name, getattr(options, name)) 
                 for name in dir(AutoRunToolOptions)
                 if name in DEFAULT_AUTOS._fields and not name.startswith('_')
                )
    return retval

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
                      ,AutoRunToolOptions
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
    auto_write_Shp = True
    auto_read_Shp = True
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
    log_file = '' # logger_name + '.log'
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
    # Override for sDNA_ToolWrapper
    python = ''
    #python = r'C:\Python27\python.exe' 
    ###########################################################################
    #
    # Overrides for ShapefileWriter
    #
    input_key_str = '{name}'
    #30,000 characters tested.
    output_shp = ''
    prj = ''
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
    if class_spacing not in tools.DataParser.Options.VALID_CLASS_SPACINGS:
        raise ValueError('%s must be in %s' 
                        %(class_spacing
                         ,tools.DataParser.Options.VALID_CLASS_SPACINGS
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
    sync = False # Can be set globally to true in installation wide config.toml
                 # This really should be False here as it's more laborious for 
                 # the user to desynchronise all sync == True components
    read_only = False
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
setup_local_metas = DEFAULT_LOCAL_METAS

output.debug('message == %s ' % module_opts['options'].message)


#########################################################################
#
def override_all_opts(local_opts #  mutated
                     ,overrides
                     ,params
                     ,local_metas = DEFAULT_LOCAL_METAS
                     ,not_shared = ('advanced', 'input', 'output')
                     ):
    #type(dict, list, dict, namedtuple, namedtuple, tuple) -> dict, namedtuple
    """    
    The options override function for sDNA_GH.  

    1) params is a flat dict, e.g. from Input Params on the component.

    2) Local_opts needs to be, and items in overrides may be, a string keyed
       nested dict of namedtuples   
    
    3) The nested dict from config.toml can contain other general data 
       fields at higher levels.  These are applied to all tools below them 
       in the tree.
   
    Mutates: local_opts
    Returns: local_metas, local_opts
    """

    metas = local_opts['metas']

    params = params.copy()# OrderedDict((key, value) 
    local_only = OrderedDict()

    for key, value in params.items() :
        if value is None or key in not_shared:
            local_only[key] = params.pop(key)
            #
            # advanced is handled in the sDNA tools, as it can be 
            # automatically built from user added input Params.
            #
            # input and output will cause clashes between sDNA tools
            # so have been made function args not options.




    project_file_opts = {}
    if (params and 
        'config' in params and 
        isinstance(params['config'], basestring)):
        #
        project_file_opts = options_manager.dict_from_toml_file(params['config'])
    else:
        msg = 'No config specified in params'
        output.debug(msg + ' == %s' % params.keys())


    external_local_metas = funcs.get_main_else_get_aliases(
                                         dict_ = params # mutated - val popped
                                        ,main = 'local_metas'
                                        ,aliases = ('l_metas',)
                                        ,fallback_value = EMPTY_NT
                                        ,mangler = smart_comp.first_item_if_seq
                                        )


    ext_local_metas_dict = external_local_metas._asdict()

    overrides += [project_file_opts
                 ,{'local_metas' : ext_local_metas_dict}
                 ,params
                 ]

    output.debug('overrides == %s' % (overrides,))

    old_sync = local_metas.sync

    ###########################################################################
    # Update syncing / de-syncing controls in local_metas
    #
    # local_metas_overrides_list += [override.pop('local_metas', override)
    #                                for override in overrides
    #                               ]
    # We probably could put this in overrides, and also apply it 
    # to override local_opts, but probably best not to risk a 
    # name clash.

    # local metas override order
    # local_metas <- overrides <- project_file_opts <- ext_local_metas_dict <- params

    local_metas = options_manager.override_nt_with_vals_for_key_else_dict(
                                                             local_metas
                                                            ,overrides
                                                            ,'local_metas'
                                                            ,**metas._asdict()
                                                            ) 


    ###########################################################################




    output.debug('overrides == %s' 
                % [override.keys() for override in overrides]
                )


    if local_metas.sync:
        output.debug('Using shared module_opts. ')
        local_opts = module_opts
    else:
        if local_metas.read_only: 
            overrides = [module_opts] + overrides

        if local_metas.no_state:
            output.debug('no_state == %s, resetting opts to hardcoded defaults' 
                        % local_metas.no_state
                        )
            local_opts = DEFAULT_OPTS.copy() # Clear the state
            if (not local_metas.read_only and 
                os.path.isfile(DEFAULT_METAS.config)): 
                #
                output.debug('Adding installation wide config.toml '
                            +'file: %s to overrides'
                            % DEFAULT_METAS.config
                            )
                installation_opts = options_manager.dict_from_toml_file(
                                                          DEFAULT_METAS.config)
                overrides = [installation_opts] + overrides

                local_metas = (options_manager
                                    .override_nt_with_vals_for_key_else_dict(
                                                             local_metas
                                                            ,overrides
                                                            ,'local_metas'
                                                            ,**metas._asdict()
                                                            )
                              ) 
                # Repeat of previous call.  The double update is to allow the
                # user to change sync to True in all components in which 
                # it is False, by setting sync = true in the installation wide 
                # config.toml.  To switch all components with sync == True 
                # back to False again is harder, e.g. Rhino must be restarted.
                # so they start off False by default.

        elif old_sync:  # Desynchronise
            output.debug('Desynchronising opts to copy of module opts. ')
            local_opts = module_opts.copy()


    metas = options_manager.override_nt_with_vals_for_key_else_dict(
                                                            local_opts['metas']
                                                           ,overrides
                                                           ,'metas'
                                                           ,**metas._asdict()
                                                           )

    output.debug('metas == %s' % (metas,))

    local_opts['metas'] = metas

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

    module_opts, setup_local_metas = override_all_opts(
                                                 local_opts = module_opts
                                                ,overrides = [installation_opts]
                                                ,params = {}  
                                                )
    output.debug('module_opts == %s' % module_opts)

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
# Set up parent logger
#

# wrapper_logging.logging.shutdown() # Ineffective in GH :(

# Create package self.logger.  All component launchers import this module, 
# (or access it via Grasshopper's cache in sys.modules) but
# all their loggers will be children of this module's logger:
logger, log_file_handler, console_log_handler, __ = logging_wrapper.get_logger_and_handlers(
                                             stream = None
                                            ,options = module_opts['options']
                                            ) 


logger.info('Logging set up in sDNA_GH package ')

output.set_logger(logger, flush = True)     
# Flushes cached log messages to above handlers


############################################################################


get_Geom = tools.RhinoObjectsReader(opts = module_opts)
read_User_Text = tools.UsertextReader(opts = module_opts)
write_shapefile = tools.ShapefileWriter(opts = module_opts)
read_shapefile = tools.ShapefileReader(opts = module_opts)
write_User_Text = tools.UsertextWriter(opts = module_opts)
parse_data = tools.DataParser(opts = module_opts)
recolour_objects = tools.ObjectsRecolourer(opts = module_opts)
build_components = dev_tools.sDNA_GH_Builder(opts = module_opts)
config = tools.ConfigManager(opts = module_opts)

runner.tools_dict.update(get_Geom = get_Geom
                        ,read_User_Text = read_User_Text
                        ,write_shapefile = write_shapefile
                        ,read_shapefile = read_shapefile
                        ,write_User_Text = write_User_Text
                        ,parse_data = parse_data
                        ,recolour_objects = recolour_objects 
                        ,Build_components = build_components
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
    tools_dict[nick_name] = sDNA_tool
    sDNA = tools.sDNA_key(compnt.opts)
    compnt.do_not_remove += sDNA_tool.default_named_tuples[sDNA]._fields 
    compnt.tools_default_opts.update(sDNA_tool.default_tool_opts)
    compnt.not_shared.update(sDNA_tool.not_shared)




sDNA_GH_tools = list(runner.tools_dict.values())


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


class sDNA_GH_Component(smart_comp.SmartComponent):

    """ The main sDNA_GH Grasshopper Component class.  
    """
    # Options from module, from defaults and installation config.toml
    opts = module_opts  
    local_metas = setup_local_metas   # immutable.  controls syncing /
                                      # de-syncing / read / write of the
                                      # above (opts).
                                      # Although local, it can be set on 
                                      # groups of components using the 
                                      # default section of a project 
                                      # config.toml, or passed as a
                                      # Grasshopper parameter between
                                      # components.
    nick_name = options_manager.error_raising_sentinel_factory('No name yet'
                                                              ,'nick_name should'
                                                              +'be set by '
                                                              +'try_to_update_nick_name'
                                                              )
    logger = logger

    @property
    def metas(self):
        return self.opts['metas']

    @property
    def options(self):
        return self.opts['options']

    old_autos = auto_run_tool_options(opts['options'])

    def auto_insert_tools(self):
        #type(type[any], list) -> None
        my_tools = self.my_tools
        self.tools = my_tools[:] if isinstance(my_tools, list) else [my_tools]

        options = self.opts['options']

        metas = self.opts['metas']

        name_map = metas.name_map
        
        self.logger.debug('Inserting tools... ')

        def is_class(Class):
            #type(type[any]) -> function
            def checker(tool):
                #type(function) -> bool
                return isinstance(tool, Class)
            return checker

        if options.auto_write_Shp:
            inserter.insert_tool('before'
                                ,self.tools
                                ,tool_to_insert = write_shapefile
                                ,is_target = is_class(tools.sDNA_ToolWrapper)
                                ,not_a_target = sDNA_GH_tools
                                )

        if options.auto_read_User_Text:
            inserter.insert_tool('before'
                                ,self.tools
                                ,tool_to_insert = read_User_Text
                                ,is_target = is_class(tools.ShapefileWriter)
                                ,not_a_target = []
                                )   

        if options.auto_get_Geom:
            inserter.insert_tool('before'
                                ,self.tools
                                ,tool_to_insert = get_Geom
                                ,is_target = is_class(tools.UsertextReader)
                                ,not_a_target = []
                                )   

        if options.auto_read_Shp:
            inserter.insert_tool('after'
                                ,self.tools
                                ,tool_to_insert = read_shapefile
                                ,is_target = is_class(tools.sDNA_ToolWrapper)
                                ,not_a_target = sDNA_GH_tools
                                )
        
      
        
        if options.auto_plot_data: # already parses if Data not all colours
            inserter.insert_tool('after'                
                                ,self.tools
                                ,tool_to_insert = recolour_objects
                                ,is_target = is_class(tools.ShapefileReader)
                                ,not_a_target = []
                                ) 



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


        self.logger.debug('Updating Params: %s ' % tools)

        interpolations = self.local_metas._asdict()

        params_updated = self.params_adder.add_tool_params(
                                             Params
                                            ,tools
                                            ,do_not_add
                                            ,do_not_remove
                                            ,wrapper = self.script
                                            ,interpolations = interpolations
                                            )

        return params_updated


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
        self.logger.debug(tools)
                

        #self.logger.debug(self.opts)
        self.logger.debug('Tool opts == ' + '\n'.join(
                                                 '%s : %s' % (k, v)
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
            self.logger.debug('new_name == %s' % new_name)

        if ( (isinstance(self.nick_name, options_manager.Sentinel)) 
              or (self.opts['metas'].cmpnts_change 
                  and self.nick_name != new_name )):  
            #
            self.nick_name = new_name
            self.logger = self.logger.getChild(self.nick_name)

            self.logger.info(' Component nick name changed to : ' 
                       +self.nick_name
                       )
            return 'Name updated'
        self.logger.debug('Old name kept == %s' % self.nick_name)

        return 'Old name kept'


    def __init__(self, *args, **kwargs):
        self.logger.debug('Calling sDNA_GH_Components parent initialiser')
        super(sDNA_GH_Component, self).__init__()
        self.ghdoc = ghdoc
        self.tools_default_opts = {}
        self.not_shared = set()
        #sDNA_GH_path = sDNA_GH_path
        #sDNA_GH_package = sDNA_GH_package
        self.do_not_remove = do_not_remove

        if not self.local_metas.sync:
            self.opts = self.opts.copy()
        #else all synchronised instances can share the class variable




    def script(self, **kwargs):        
        # update_Params is called from inside this method, so the input Params 
        # supplying the args will not updated until after they have been read.
        # If this method is not intended to crash on a missing input param,
        # it needs to accept anything (or a lack thereof) to run in the 
        # meantime until the params can be updated.  kwargs enable this.
        self.logger.debug('self.script started... \n')
        #self.logger.debug(kwargs)

        go = smart_comp.first_item_if_seq(kwargs.pop('go', False), False) 
             # Input Params set 
             # to list access so
             # strip away outer 
             # list container
        Data = kwargs.pop('Data', None)
        Geom = kwargs.pop('Geom', None)
        f_name = funcs.get_main_else_get_aliases(
                     dict_ = kwargs
                    ,main = 'file'
                    ,aliases = ('f_name',)
                    ,fallback_value = ''
                    ,mangler = functools.partial(smart_comp.first_item_if_seq
                                                ,null_container = ''
                                                )
                    )

        external_opts = smart_comp.first_item_if_seq(kwargs.pop('opts', {}), {})

        self.logger.debug(external_opts)

        gdm = smart_comp.first_item_if_seq(kwargs.get('gdm', {}))

        self.logger.debug(('gdm from start of RunScript == %s' % gdm)[:80])
        
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
        
            self.auto_insert_tools()  

            params_updated = self.update_Params() #self.Params, self.tools)

            if params_updated:
                # Extra Input Params are actually OK as RunScript has already 
                # been called already by this point.
                self.logger.debug('Output Params updated.  Returning None.  ')
                return (None,) * len(self.Params.Output)
                # Grasshopper components can have a glitchy one off error if
                # not-None outputs are given to params that 
                # have just been added, in the same RunScript call.  In our 
                # design the user probably doesn't want the new tool and 
                # updated component params to run before they've had chance to
                # look at them, even if 'go' is still connected to True.  But 
                # e.g. config, and anything there that they already configured
                # and saved should still run when the canvas loads. 

                    
        self.logger.info('Tools == %s ' % self.tools)

        #######################################################################
        self.logger.debug('kwargs.keys() == %s ' % kwargs.keys())
        self.opts, self.local_metas = override_all_opts(
                                 local_opts = self.opts # mutated
                                ,overrides = [self.tools_default_opts, external_opts]
                                ,params = kwargs
                                ,local_metas = self.local_metas 
                                ,not_shared = self.not_shared
                                )
        #######################################################################
        kwargs['opts'] = self.opts
        kwargs['local_metas'] = self.local_metas

        for handler, level in ((console_log_handler
                               ,self.opts['options'].log_console_level
                               )
                              ,(log_file_handler
                               ,self.opts['options'].log_file_level
                               )
                              ):
            logging_wrapper.set_handler_level(handler, level)


        self.logger.debug('Opts overridden....    ')
        self.logger.debug(self.opts)
        self.logger.debug(self.local_metas)
        
        if (self.metas.update_path 
            or not os.path.isfile(self.options.path) ):

            path = checkers.get_path(fallback = __file__,  inst = self)
            self.opts['options'] = self.opts['options']._replace(path = path)




         
        any_sDNA_tools_updated = False
        for tool in self.tools:
            if (isinstance(tool, tools.sDNA_ToolWrapper) and 
                not tool.already_loaded(self.opts)): # already loaded sDNA
                #
                self.logger.debug('tool.already_loaded(self.opts) == False')
                tool.load_sDNA_tool(self.opts)
                any_sDNA_tools_updated = True
                # This isn't necessary just to run these tools later.
                # They're just being updated now so they can get their 
                # inputs from sDNAUISpec the next run, and so the 
                # component's input 
                # Params can be updated to reflect the new sDNA

        autos_changed = self.old_autos != auto_run_tool_options(self.options)
        if any_sDNA_tools_updated or autos_changed:
            if autos_changed:
                self.logger.info('New auto options found.  Re-updating tools. ')
                self.auto_insert_tools()
                self.old_autos = auto_run_tool_options(self.options)
                self.logger.info('Tools == %s ' % self.tools)

            params_updated = self.update_Params()#self.Params, self.tools)
            # to add in any new sDNA inputs to the component's Params
            if params_updated:
                self.logger.info('Params have been updated.  '
                                +'Returning None to allow new Params to be set. '
                                )
                return (None,) * len(self.Params.Output)
                # to allow running the component again, with any new inputs
                # supplied as Params
        elif (self.metas.make_new_comps and
                nick_name.replace(' ','').replace('_','').lower() == 'config'):
            #
            tools.import_sDNA(self.opts)
            self.logger.info('Building missing sDNA components (if any). ')
            tools.build_missing_sDNA_components(opts = self.opts
                                               ,category_abbrevs = self.metas.category_abbrevs
                                               ,plug_in_name = dev_tools.plug_in_name #'sDNA'
                                               ,plug_in_sub_folder = dev_tools.plug_in_sub_folder # 'sDNA_GH' 
                                               ,user_objects_location = tools.sDNA_GH_user_objects_location
                                               ,add_to_canvas = False
                                               ,overwrite = True
                                               ,move_user_objects = self.metas.move_user_objects
                                               )



        self.logger.debug(go)

        if go is True: 
            if not hasattr(self, 'tools'):
                msg = 'component name: %s unrecognised? ' % nick_name
                msg += 'sDNA_GH has not found any tools to run.  '
                msg += 'Change component name, or define tools for name in name_map.'
                self.logger.error(msg)
                raise ValueError(msg)                
            if not isinstance(self.tools, list):
                msg = 'self.tools is not a list'
                self.logger.error(msg)
                raise TypeError(msg)

            invalid_tools = [tool for tool in self.tools 
                                  if not isinstance(tool, runner.RunnableTool)
                            ]
            if invalid_tools:
                msg = ('Tools are not runner.RunnableTool instances : %s' 
                      % invalid_tools
                      )
                self.logger.error(msg)
                raise ValueError(msg)

            self.logger.debug('my_tools == %s' % self.tools)



            geom_data_map = (gdm_from_GH_Datatree.GeomDataMapping
                                                 .from_DataTree_and_list(Geom
                                                                        ,Data
                                                                        )
                            )



            self.logger.debug('type(geom_data_map) == %s ' % type(geom_data_map))
            
            self.logger.debug('Before merge gdm[:3] == %s ' % gdm.items()[:3])


            self.logger.debug('Before merge geom_data_map[:3] == %s ' 
                        % geom_data_map.items()[:3]
                        )

            gdm = gdm_from_GH_Datatree.override_gdm(
                                        gdm  # External one from args
                                       ,geom_data_map
                                       ,self.opts['options'].merge_subdicts
                                       )

            self.logger.debug('After merge type(gdm) == %s ' % type(gdm))
            
            self.logger.debug('After merge gdm[:3] == %s ' % gdm.items()[:3])

            kwargs['gdm'] = gdm
            kwargs['f_name'] = f_name # put back in here so it doesn't go in opts

            ##################################################################
            ret_vals_dict = runner.run_tools(self.tools, kwargs)
            ##################################################################
            gdm = ret_vals_dict.get('gdm', {})
            if isinstance(gdm, (Iterable, gdm_from_GH_Datatree.GeomDataMapping)):
                #
                self.logger.info('Converting gdms to Data Tree and Data Tree')
                NewData, NewGeometry = (gdm_from_GH_Datatree
                                            .Data_Tree_and_Data_Tree_from_dicts(gdm)
                                       )  
                if isinstance(gdm, (gdm_from_GH_Datatree.GeomDataMapping)):
                    ret_vals_dict['gdm'] = [gdm]
            else:
                logger.info('Cannot unpack Geom Data Mapping of type: %s' 
                           %type(gdm)
                           )
                NewData, NewGeometry = None, None
            ret_vals_dict['Data'] = NewData
            ret_vals_dict['Geom'] = NewGeometry
            if 'f_name' in ret_vals_dict:
                ret_vals_dict['file'] = ret_vals_dict['f_name']

            ret_vals_dict['OK'] = ret_vals_dict.get('retcode', 0) == 0
            



        else:
            self.logger.debug('go == %s ' % go)
            ret_vals_dict = {}
            ret_vals_dict['OK'] = False
        ret_vals_dict['opts'] = [self.opts.copy()] # could become external_opts
                                                   # in another component
        ret_vals_dict['l_metas'] = self.local_metas #immutable

        self.logger.debug('Returning from self.script. opts.keys() == %s ' % self.opts.keys() )

        all_tool_opts = {}
        for tool in self.tools:
            if hasattr(tool, 'get_tool_opts'):
                tool_opts = tool.get_tool_opts(self.opts)
                tool_opts_dict = tool_opts._asdict()
                all_tool_opts.update(tool_opts_dict)

        self.logger.debug('all_tool_opts: %s '  % all_tool_opts)

        locals_ = locals().copy()
        ret_args = self.component_Outputs( 
                              [ret_vals_dict
                              ,self.opts['metas']
                              ,self.opts['options']
                              ,self.local_metas
                              ,all_tool_opts
                              ,locals_
                              ]
                             )
        return ret_args
    script.input_params = lambda *args : tools.list_of_param_infos(['go', 'opts'], param_infos)
    script.output_params = lambda *args : tools.list_of_param_infos(['OK', 'opts'], param_infos)







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


""" Tool classes for sDNA_GH 

    Except Dev tools.  They're in dev_tools.py  
"""

__author__ = 'James Parrott'
__version__ = '0.08'

import os
import abc
import logging
import subprocess
from .data_cruncher import itertools #pairwise from recipe if we're in Python 2
import re
import string
import warnings
import collections
from time import asctime
from numbers import Number
import locale
import math
import shutil

import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import GhPython
import System
import System.Drawing #.Net / C# Class
            #System is also available in IronPython, but System.Drawing isn't
from Grasshopper.GUI.Gradient import GH_Gradient
from Grasshopper.Kernel.Parameters import (Param_Arc
                                          ,Param_Colour  
                                          ,Param_Curve
                                          ,Param_Boolean
                                          ,Param_Geometry
                                          ,Param_String
                                          ,Param_FilePath
                                          ,Param_Guid
                                          ,Param_Integer
                                          ,Param_Line
                                          ,Param_Rectangle
                                          ,Param_Number
                                          ,Param_ScriptVariable
                                          ,Param_GenericObject
                                          )

from . import data_cruncher 
from .skel.basic.ghdoc import ghdoc
from .skel.tools.helpers import checkers
from .skel.tools.helpers import funcs
from .skel.tools import runner                                       
from .skel import add_params
from .skel import builder
from . import options_manager
from . import pyshp_wrapper
from . import logging_wrapper
from . import gdm_from_GH_Datatree
from .. import launcher

if hasattr(abc, 'ABC'):
    ABC = abc.ABC
else:
    class ABC(object):
        __metaclass__ = abc.ABCMeta
abstractmethod = abc.abstractmethod

try:
    basestring #type: ignore
except NameError:
    basestring = str

OrderedDict, Counter = collections.OrderedDict, collections.Counter
if hasattr(collections, 'Iterable'):
    Iterable = collections.Iterable 
else:
    import collections.abc
    Iterable = collections.abc.Iterable

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
ClassLogger = logging_wrapper.class_logger_factory(logger = logger
                                                  ,module_name = __name__
                                                  )



def list_of_param_infos(param_names
                       ,param_infos
                       ,descriptions = None
                       ,interpolations = None
                       ):
    #type(Iterable, tuple, Iterable) -> list
    """ Returns a list of a selection of ParamInfo entries from Param_infos
        (a tuple of tuples of names and ParamInfos), each selected if its name
        is in param_names, with its NickName set to name, and Description
        taken from descriptions if it doesn't already have one. 
    """
    retvals = []
    param_infos = OrderedDict(param_infos) # e.g. from tuple of key/value pairs.
                                           # OrderedDict overwrites earlier 
                                           # values with later values in 
                                           # the tuple with the same key.
                                           # param_infos need not be in any 
                                           # particular order; the order of the 
                                           # output is that of param_names.
    for param_name in param_names:
        param_info = param_infos[param_name] # instance of ParamInfo
        param_info['NickName'] = param_name  # ParamInfo is a subclass of dict
        if descriptions and 'Description' not in param_info:
            param_info['Description'] = descriptions[param_name]
        if interpolations:
            param_info['Description'] %= interpolations
        retvals.append(param_info)
    return retvals




class sDNA_GH_Tool(runner.RunnableTool, add_params.ToolwithParamsABC, ClassLogger):

    """ General base class for all tools, that is runnable (should have
        retvals implemented), has params (input_params and output_params
        should be implemented), and containing a class logger that adds the subclass
        name to logging messages. 
    """

    def __init__(self, opts):
        self.opts = opts

    @property
    def options(self):
        return self.opts['options']

    @property
    def metas(self):
        return self.opts['metas']

    @property
    def all_options_dict(self):
        retval = self.options._asdict()
        retval.update(self.metas._asdict())
        return retval


    def param_info_list(self, param_names):
        return list_of_param_infos(param_names
                                  ,self.param_infos
                                  ,interpolations = self.all_options_dict
                                  )

    @property
    def input_params(self):
        return self.param_info_list(self.component_inputs)

    @property    
    def output_params(self):
        return self.param_info_list(self.component_outputs)

    @property
    @abstractmethod
    def component_inputs(self):
        pass # Iterable of strings, the names of the input Params required on
             # a component running this tool

    @property
    @abstractmethod
    def component_outputs(self):
        pass # Iterable of strings, the names of the output Params required on
             # a component running this tool

    # Can be both inputs and outputs
    param_infos = (('file', add_params.ParamInfo(
                             param_Class = Param_FilePath
                            ,Description = 'File path of the shape file.'
                            ))                           
                   ,('Geom', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = 'A list of Geometric objects.'
                            ))  
                   ,('Data', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('A Data Tree of a list of keys '
                                           +'and list of corresponding values '
                                           +'for each object in Geom.'
                                           )
                            ,Access = 'tree'
                            ))
                   ,('gdm', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('Geometry and Data Mapping.  '
                                           +'Internal combination of Geom and '
                                           +'Data.  Python dictionary.'
                                           )
                            ))   
                   ,('config', add_params.ParamInfo(
                             param_Class = Param_FilePath
                            ,Description = ('File path to sDNA_GH options '
                                           +'file, e.g. config.toml'
                                           )
                            ))   
                   ,('local_metas', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('Local meta options, controlling '
                                           +'synchronisation to the global '
                                           +'sDNA_GH options. Python named '
                                           +'tuple.'
                                           )
                            ))   
                   ,('l_metas', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('Local meta options, controlling '
                                           +'synchronisation to the global '
                                           +'sDNA_GH options. Python named '
                                           +'tuple.'
                                           )
                            ))  
                  )                     








def delete_shp_files_if_req(f_name
                           ,logger = logger
                           ,delete = True
                           ,strict_no_del = False
                           ,regexes = () # no file extension in regexes
                           ):
    #type(str, type[any], bool, str/tuple) -> None
    logger.debug('strict_no_del == %s ' % strict_no_del)
    if strict_no_del:
        return

    file_name_no_ext = os.path.splitext(f_name)[0]
    logger.debug('delete == %s ' % delete)
    if (delete or funcs.name_matches(file_name_no_ext, regexes)):
        for ext in ('.shp', '.dbf', '.shx', '.shp.names.csv'):
            path = file_name_no_ext + ext
            funcs.delete_file(path, logger)
            

def has_keywords(nick_name, keywords = ('prepare',)):
    return any(substr in nick_name.strip().strip('_').lower() 
              for substr in keywords
              )

sDNA_fmt_str = '{sDNAUISPec}_and_{runsdnacommand}' 
# extra quotes would make it a quoted key string in .toml, 
# which supports an extended character set than ascii (normal keys). 
# But then this string couldn't be used in a NamedTuple class name


def sDNA_key(opts):
    #type(tuple[str]) -> str
    """ Defines the sub-dict key for each sDNA version, from the tuple
        of module names.
        e.g. ('sDNAUISpec','runsdnacommand') -> sDNAUISpec_and_runsdnacommand. 
        Returns a string so the key can be loaded from a toml file.
    """
    metas = opts['metas']
    sDNA = (metas.sDNAUISpec.partition('.')[0]
           ,metas.runsdnacommand.partition('.')[0]
           )
    return sDNA_fmt_str.format(sDNAUISPec = sDNA[0], runsdnacommand = sDNA[1])


def nested_set_default(d, keys, last_default = None):
    #type(dict, Sequence(Hashable), type[any])
    
    if last_default is None:
        last_default = OrderedDict()

    def generator():
        for key in keys[:-1]:
            yield key, OrderedDict()
        yield keys[-1], last_default

    for key, default in generator():
        d = d.setdefault(key, default)
    return d

def get_tool_opts(nick_name, opts, tool_name = None, sDNA = None, val = None):
    #type(str, dict, str, str, type[any])
    # might mutate opts
    keys = (nick_name,)
    if tool_name and tool_name != nick_name:
        keys += (tool_name,)
    if sDNA is not None:
        keys += (sDNA,)
    return nested_set_default(d = opts, keys = keys, last_default = val)

    # tool_opts = opts.setdefault(nick_name, {})
    # if tool_name and tool_name != nick_name:
    #     tool_opts = tool_opts.setdefault(tool_name, {})
    # if sDNA:
    #     if val:
    #         return tool_opts.setdefault(sDNA, val)
    #     else:
    #         return tool_opts.setdefault(sDNA, emptyNT)
    
    # return tool_opts


class sDNAMetaOptions(object):
    """All options needed to import sDNA. """

    sDNAUISpec = 'sDNAUISpec'
    runsdnacommand = 'runsdnacommand'
    sDNA_paths = list( funcs.windows_installation_paths('sDNA') )

sDNA_meta_options = options_manager.namedtuple_from_class(sDNAMetaOptions)


class PythonOptions(object):
    """All options needed to specify a Python interpreter, or search for one. """

    python_paths = list( funcs.windows_installation_paths(('Python27'
                                                          ,'Python_27'
                                                          ,'Python_2.7'
                                                          ,'Python2.7'
                                                          )
                                                         )
                       )
    python_exes = ['python.exe', 'py27.exe']
    python = None #r'C:\Python27\python.exe'

python_options = options_manager.namedtuple_from_class(PythonOptions)


class MissingPythonError(Exception):
    pass


def check_python(opts):
    #type(dict) -> None 
    """ Searches opts['metas'].python_paths, updating opts['metas'].python 
        until it is a file.  Mutates opts.  Raises MissingPythonError if no
        valid file found.
    """

    folders = opts['metas'].python_paths
    pythons = opts['metas'].python_exes

    if isinstance(folders, basestring):
        folders = [folders]

    if isinstance(pythons, basestring):
        pythons = [pythons]

    possible_pythons = (os.path.join(folder, python) for folder in folders 
                                                     for python in pythons
                       )
    try:
        while not opts['metas'].python or not os.path.isfile(opts['metas'].python):
            opts['metas'] = opts['metas']._replace(python = next(possible_pythons))
    except StopIteration:
        msg = ('No Python interpreter file found.  Please specify a valid '
              +'python 2.7 interpreter in python (invalid: %s) ' % opts['metas'].python
              +'or a range of python interpreter names and folder names to '
              +'search for one in python_exes and python_paths.'
              )
        logger.error(msg)
        raise MissingPythonError(msg)


def is_data_key(key
               ,**kwargs
               ):
    depth = kwargs['depth']
    max_depth = kwargs['max_depth']
    specials = kwargs['specials']
    patterns = kwargs['patterns']
    return (key in specials or 
            depth > max_depth or 
            any(re.match(pattern, key) for pattern in patterns)
           )

def categorise_keys(d
                   ,**kwargs
                   ):
    
    sub_dict_keys, data_node_keys, data_field_keys = [], [], []
    for key, value in d.items(): 
        if isinstance(value, dict) or options_manager.isnamedtuple(value):
            #logger.debug('key == %s is a node' % key)
            if is_data_key(key, **kwargs):
                data_node_keys.append(key)
                logger.debug('key == %s is a data_node' % key)
            else:
                sub_dict_keys.append(key)
                logger.debug('key == %s is a sub_dict' % key)
        else: 
            logger.debug('key == %s is a data field' % key)
            data_field_keys.append(key)

    return sub_dict_keys, data_node_keys, data_field_keys




class DefaultMetas(object):
    strict = True
    check_types = True
    add_new_opts = False
    @classmethod
    def _asdict(cls):
        return OrderedDict((attr, getattr(cls, attr)) 
                           for attr in dir(cls)
                           if not attr.startswith('_')
                          )


def update_opts(current_opts
               ,override
               ,depth = 0
               ,update_data_node = options_manager.override_namedtuple
               ,make_new_data_node = options_manager.namedtuple_from_dict
               ,categorise_keys = categorise_keys
               ,**kwargs
               ):
    #type(dict, dict, tuple, int, function, function, function, **kwargs) -> None
    """ Updates or creates a nested dict of data nodes, from a) another one, 
        b) a nested dict including data dicts and c) flat dicts.  
        
        As the tree of override is walked, at each level all data items are read 
        and used to update (override) the data items from previous (shallower) 
        levels.  Recursion proceeds only on sub-dict keys.
        Updating or creating a data node in current_opts is only done when the 
        function can go no deeper in current_opts, or when opts flattens out.
        A nested dict flattens out when get_subdicts_keys_and_data_keys 
        returns no keys of subdicts.
        When the override dict flattens out, the tree walk shifts to the tree of 
        opts instead.

        Depth is counted for possible use by get_subdicts_keys_and_data_keys.
    """


    logger.debug('depth == %s' % depth)
    if not isinstance(current_opts, dict) or not isinstance(override, dict):
        msg = ('opts and override need to be dictionaries. '
              +'depth == %s' % depth
              )
        logger.error(msg)
        raise TypeError(msg)
    logger.debug('current_opts.keys() == %s ' % current_opts.keys())
    logger.debug('override.keys() == %s ' % override.keys())

    if not kwargs:
        kwargs = {}
    metas = kwargs.setdefault('metas', current_opts.get('metas', DefaultMetas))
    logger.debug('metas == %s' % metas)
                #,strict 
                #,check_types
                #,add_new_opts, for update_data_node and make_new_data_node
    kwargs.setdefault('max_depth', 2)
    kwargs.setdefault('specials', ('options', 'metas'))
    kwargs.setdefault('patterns', (funcs.make_regex(sDNA_fmt_str),))
    
    kwargs['depth'] = depth

    sub_dicts_keys, data_node_keys, data_field_keys = categorise_keys(override
                                                                     ,**kwargs
                                                                     )

    logger.debug('sub_dicts_keys == %s' % sub_dicts_keys)
    logger.debug('data_node_keys == %s' % data_node_keys)
    logger.debug('data_field_keys == %s' % data_field_keys)

    current_data_node_keys = []
    if not sub_dicts_keys:  
        # continue walking the tree, only the tree in current_opts instead,
        # starting at the same level.
        sub_dicts_keys, current_data_node_keys, _  = categorise_keys(current_opts
                                                                    ,**kwargs
                                                                    )
                  # Needs explicit type, as general_opts above.
        logger.debug('after current_opts update, sub_dicts_keys == %s' 
                    % sub_dicts_keys
                    )
        logger.debug('after current_opts update, current_data_node_keys == %s' 
                    % current_data_node_keys
                    )

    override_data_fields = OrderedDict((key, override[key]) 
                                       for key in data_field_keys
                                      )

    for key in sub_dicts_keys:
        # assert key not in data_field_keys
        override_data = override_data_fields.copy()
        override_data.update( override.get(key, {}) )
        # Walk the tree, whether that's the tree of current_opts or a new tree
        # in override_data - .setdefault will ensure it exists in
        # current_opts.
        update_opts(current_opts.setdefault(key, {}) # creates a new sub_dict
                                                     # if there isn't a val
                                                     # for key.   
                   ,override = override_data
                   ,depth = depth + 1
                   ,update_data_node = update_data_node
                   ,make_new_data_node = make_new_data_node
                   ,categorise_keys = categorise_keys
                   ,**kwargs
                   )

    logger.debug('depth == %s' % depth)

    for key in data_node_keys + current_data_node_keys:
        override_data = override_data_fields.copy()

        logger.debug('override_data == %s' % override_data)
        logger.debug('key == %s' % key)
        logger.debug('current_opts.keys() == %s' % current_opts.keys())

        if key in current_opts:  #current_data_node_keys
            overrides = [override_data]
            if key in override:
                overrides += [override[key]]
            #logger.debug('Updating current_opts with overrides == %s & key == %s' 
            #            % (overrides, key)
            #            )
            current_opts[key] = update_data_node(current_opts[key]
                                                ,overrides
                                                ,**metas._asdict()
                                                )
        elif options_manager.isnamedtuple(override[key]):
            # Do nothing with override_data
            # 
            # higher level generic options values are not supported from 
            # sDNA_GH opts structures; just from toml files and Params
            current_opts[key] = override[key]
        else:
            override_data.update(override[key])
            logger.debug('Creating node '
                        +'with override_data == %s & key == %s' 
                        % (override_data, key)
                        )

            current_opts[key] = make_new_data_node(override_data
                                                  ,key # NamedTuple type name
                                                  ,**metas._asdict()
                                                  )  
        



def import_sDNA(opts 
               ,load_modules = launcher.load_modules
               ,logger = logger
               ):
    #type(dict, str, function, type[any]) -> tuple(str)
    """ Imports sDNAUISpec.py and runsdnacommand.py and stores them in
        opt['options'], when a new
        module name is specified in opts['metas'].sDNAUISpec or 
        opts['metas'].runsdnacommand.  

        Returns a tuple of the latest modules names.
    """
    
    metas = opts['metas']
    options = opts['options']

    logger.debug('metas.sDNAUISpec == %s ' % metas.sDNAUISpec
                +', metas.runsdnacommand == %s ' % metas.runsdnacommand 
                )


    requested_sDNA = (metas.sDNAUISpec.partition('.')[0]
                     ,metas.runsdnacommand.partition('.')[0]) # remove .py s

    # To load new sDNA modules, specify the new module names in
    # metas.sDNAUISpec and metas.runsdnacommand

    # If they are loaded successfully the actual corresponding modules are
    # in options.sDNAUISpec and options.run_sDNA

    if ( metas.sDNA is not None and
         not isinstance(options.sDNAUISpec, options_manager.Sentinel) and
         not isinstance(options.run_sDNA, options_manager.Sentinel) and
         (options.sDNAUISpec.__name__
                    ,options.run_sDNA.__name__) == requested_sDNA ):
        #
        return None

    logger.info('Attempting import of sDNA '
               +'(sDNAUISpec == %s, runsdnacommand == %s)... ' % requested_sDNA
               )
    #
    # Import sDNAUISpec.py and runsdnacommand.py from metas.sDNA_paths
    if isinstance(metas.sDNA_paths, basestring):
        folders = [metas.sDNA_paths] 
    else:
        folders = metas.sDNA_paths

    folders = [os.path.dirname(folder) if os.path.basename(folder) == 'bin' else folder 
               for folder in folders
              ]

    try:
        sDNAUISpec, run_sDNA, _ = load_modules(
                                             m_names = requested_sDNA
                                            ,folders = folders
                                            ,logger = logger
                                            ,module_name_error_msg = "Invalid file names: %s, %s " % requested_sDNA 
                                                                    +"Please supply valid names of 'sDNAUISpec.py' "
                                                                    +"and 'runsdnacommand.py' files in "
                                                                    +"sDNAUISpec and runsdnacommand "
                                                                    +"respectively. " # names not strings error
                                            ,folders_error_msg = "sDNA_GH could not find a valid folder to look for sDNA in. " 
                                                                +"Please supply the "
                                                                +"correct name of the path to the sDNA folder you "
                                                                +"wish to use with sDNA_GH, in "
                                                                +"sDNA_paths.  This folder should contain the files named in "
                                                                +"sDNAUISpec: %s.py and runsdnacommand: %s.py. " % requested_sDNA
                                                                # not existing folders error
                                            ,modules_not_found_msg = "sDNA_GH failed to find an sDNA file specified in "
                                                                    +"sDNAUISpec (%s.py) or runsdnacommand (%s.py)" % requested_sDNA
                                                                    +" in any of the folders in sDNA_paths. "
                                                                    +" Please either ensure a folder in "
                                                                    +" sDNA_paths contains both the valid "
                                                                    +"'sDNAUISpec.py' named %s and " % requested_sDNA[0]
                                                                    +"'runsdnacommand.py' named %s " % requested_sDNA[0]
                                                                    +"from your chosen sDNA installation, or adjust the "
                                                                    +" file names specified in sDNAUISpec and runsdnacommand"
                                                                    +" to their equivalent files in it (to use more than "
                                                                    +" one sDNA you must rename these files in any extra). "
                                            )
    except launcher.InvalidArgsError as e:
        raise e
    except:
        msg = ("sDNA_GH failed to import the sDNA files specified in "
                +"sDNAUISpec (%s.py) or runsdnacommand (%s.py)" % requested_sDNA
                +" from any of the folders in sDNA_paths."
                +" Please either ensure a folder in"
                +" sDNA_paths contains the two corresponding valid files"
                +" from your chosen sDNA installation, or adjust the"
                +" file names specified in sDNAUISpec and runsdnacommand"
                +" to their equivalent files in it (to import a second"
                +" or third sDNA etc. you must rename these files to different"
                +" names than in the first). "
                )
        logger.error(msg)
        raise ImportError(msg)
    opts['options'] = opts['options']._replace(sDNAUISpec = sDNAUISpec
                                                ,run_sDNA = run_sDNA 
                                                ) 
    # we want to mutate the value in the original dict 
    # - so we can't use options for this assignment.  Latter for clarity.
    return None


default_user_objects_location = os.path.join(launcher.user_install_folder
                                            ,launcher.package_name
                                            ,builder.ghuser_folder
                                            )


def build_sDNA_GH_components(**kwargs):
    #type(kwargs) -> list
    
    
    
    user_objects_location = kwargs.setdefault('user_objects_location'
                                             ,default_user_objects_location
                                             )

    sDNA_GH_path = user_objects_location
    while os.path.basename(sDNA_GH_path) != launcher.package_name:
        sDNA_GH_path = os.path.dirname(sDNA_GH_path)

    README_md_path = os.path.join(sDNA_GH_path, 'README.md')
    if not os.path.isfile(README_md_path):
        README_md_path = os.path.join(os.path.dirname(sDNA_GH_path), 'README.md')
        # Readme.md is a level higher in the repo than in the sDNA_GH
        # folder in a user installation - it is moved intentionally
        # by create_release_sDNA_GH_zip.bat 



    logger.debug('README_md_path == %s' % README_md_path)


    launcher_path = os.path.join(sDNA_GH_path, 'launcher.py')


    return builder.build_comps_with_docstring_from_readme(
                                 default_path = launcher_path
                                ,path_dict = {}
                                ,readme_path = README_md_path
                                ,row_height = None
                                ,row_width = None
                                ,**kwargs
                                )


def build_missing_sDNA_components(opts
                                 ,**kwargs
                                 ):
    #type(dict, str, bool, kwargs) -> list
    metas = opts['metas']
    categories = metas.categories.copy()

    sDNAUISpec = opts['options'].sDNAUISpec

    user_objects_location = kwargs.setdefault('user_objects_location'
                                             ,default_user_objects_location  
                                             )

    def ghuser_file_path(name):
        #type(str)->str
        return os.path.join(user_objects_location, name + '.ghuser') 

    missing_tools = []
    names = []
    for Tool in sDNAUISpec.get_tools():
        names = [nick_name
                 for (nick_name, tool_name) in metas.name_map.items()
                 if tool_name == Tool.__name__
                ]
        names.insert(0, Tool.__name__)
        if not any( os.path.isfile(ghuser_file_path(name)) for name in names ):
            name_to_use = names[-1] if names else Tool.__name__
            logger.debug('Appending tool name to missing_tools: %s' 
                        %name_to_use
                        )
            missing_tools.append(name_to_use)
            categories[Tool.__name__] = Tool.category
    
    if missing_tools:
        names_built = build_sDNA_GH_components(component_names = missing_tools
                                              ,name_map = metas.name_map
                                              # the whole point of the extra call here is
                                              # to overwrite or build missing single tool 
                                              # components without nicknames
                                              ,categories = categories
                                              ,**kwargs
                                              )
        return names_built
    logger.debug('No missing sDNA tools were found. ')
    return []
            




def file_name_formats(base_name, duplicate_suffix):
    #type: (str, str) -> tuple[str, str]
    """ Defines how to produce format strings for default file names. """
    unique_name_fmt = base_name
    dupe_name_fmt = unique_name_fmt + duplicate_suffix 
    #File extensions must be added elsewhere

    return unique_name_fmt, dupe_name_fmt




class ShapeFilesDeleter(ABC):
    
    file_name = None

    def __init__(self
                ,file_name 
                ):
        self.file_name = file_name

    def delete_files(self, delete, opts):
        if isinstance(self.file_name, basestring):
            #
            delete_shp_files_if_req(f_name = self.file_name
                                    ,delete = delete
                                    ,strict_no_del = opts['options'].strict_no_del  
                                    )

class NullDeleter(object):
    pass
ShapeFilesDeleter.register(NullDeleter)

class InputFileDeletionOptions(pyshp_wrapper.GetFileNameOptions):
    del_after_sDNA = True
    strict_no_del = False 
    input_file_deleter = None

class OutputFileDeletionOptions(pyshp_wrapper.GetFileNameOptions):
    strict_no_del = InputFileDeletionOptions.strict_no_del 
    output_file_to_maybe_delete = None
    del_after_read = False
    output_file_deleter = None

class sDNA_ToolWrapper(sDNA_GH_Tool):
    """ Main sDNA_GH tool class for running sDNA tools externally.
    
    In addition to the 
    other necessary attributes of sDNA_GH_Tool, instances know their own name
    and nick name, in self.nick_name
    self.tool_name.  When the instance is called, the version of sDNA
    is looked up in opts['metas'], from its args. 
    """
    
    sDNA_types_to_py_type_names = dict(fc = 'file'
                                      ,ofc = 'file'
                                      ,bool = 'bool'
                                      ,field = 'str'
                                      ,text = 'str'
                                      ,multiinfile = 'file'
                                      ,infile = 'file'
                                      ,outfile = 'file'
                                      )

    py_type_names_to_Params = dict(file = Param_FilePath 
                                  ,bool = Param_Boolean
                                  ,str = Param_String
                                  )

    py_type_names_to_type_description = dict(file = 'File path'
                                            ,bool = 'Boolean'
                                            ,str = 'Text'
                                            )

    class Metas(PythonOptions, sDNAMetaOptions):
        sDNA = None
        show_all = True

    class Options(InputFileDeletionOptions
                 ,OutputFileDeletionOptions
                 ):
        sDNAUISpec = options_manager.Sentinel('Module not imported yet')
        run_sDNA = options_manager.Sentinel('Module not imported yet')
        prepped_fmt = "{name}_prepped"
        output_fmt = "{name}_output"
        overwrite_shp = pyshp_wrapper.ShpOptions.overwrite_shp
        # file extensions are actually optional in PyShp, 
        # but just to be safe and future proof
# Default installation path of Python 2.7.3 release (32 bit ?) 
# http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi copied from sDNA manual:
# https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/installation_usage.html 


    @property
    def all_options_dict(self):
        retval = self.options._asdict()
        retval.update(self.metas._asdict())
        retval.update(self.user_default_tool_opts._asdict())
        return retval

    def update_tool_opts_and_syntax(self, opts = None):
        if opts is None:
            opts = self.opts
        nick_name = self.nick_name
        tool_name = self.tool_name

        check_python(opts)

        if sDNA_key(opts) != opts['metas'].sDNA:
            # Do the sDNA modules in the opts need updating?
            self.import_sDNA(opts, logger = self.logger)
            opts['metas'] = opts['metas']._replace(sDNA = sDNA_key(opts))


        metas = opts['metas']
        sDNA = metas.sDNA

        sDNAUISpec = opts['options'].sDNAUISpec # module
        run_sDNA_command = opts['options'].run_sDNA # module




        try:
            sDNA_Tool = getattr(sDNAUISpec, self.tool_name)()
        except AttributeError:
            msg =   ('No tool called '
                    +self.tool_name
                    +' found in '
                    +sDNAUISpec.__file__
                    +'.  Rename tool_name or change sDNA version.  '
                    )
            self.logger.error(msg)
            raise ValueError(msg)
                            
        self.input_spec = sDNA_Tool.getInputSpec()
        self.get_syntax = sDNA_Tool.getSyntax
        self.run_sDNA_command = run_sDNA_command     

        self.defaults = OrderedDict()






        self.defaults = OrderedDict((tuple_[0], tuple_[4]) 
                                    for tuple_ in self.input_spec
                                   )
        # See below for field names in input_spec

        nt_name = '_'.join([nick_name, tool_name, sDNA])
        defaults_nt = options_manager.namedtuple_from_dict(d = self.defaults
                                                          ,NT_name = nt_name
                                                          )

        default_tool_opts = {}
        # builds the tool opts structure in default_tool_opts,
        # using nested_set_default
        self.user_default_tool_opts = get_tool_opts(nick_name
                                                   ,default_tool_opts
                                                   ,tool_name
                                                   ,sDNA
                                                   ,val = defaults_nt
                                                   )
        self.logger.debug('default_tool_opts == %s ' % default_tool_opts)

        update_opts(current_opts = default_tool_opts # mutated
                   ,override = opts 
                   )
        #override default tool opts with opts


        opts.update(default_tool_opts)
        # get the updated opts back into opts, via .update (have to mutate
        # as assignment will only affect the variable assigned to the local 
        # name of this method arg)

        for varname, display_name, data_type, filter_, default, required in self.input_spec:  
                      
            description = display_name +'. '
            description += 'Default value == %(' + varname + ')s.'
            # to be interpolated by self.param_info_list from self.all_options_dict

            if (isinstance(filter_, Iterable) 
               and not isinstance(filter_, basestring)
               and len(filter_) >= 2): 
                #
                description = '%s. Allowed values: %s. ' % (description
                                                           ,', '.join(map(str
                                                                         ,filter_
                                                                         )
                                                                     )
                                                           ) 
            # if required:     
            #     description = 'REQUIRED. %s' % description
            if data_type:
                if data_type.lower() not in self.sDNA_types_to_py_type_names:
                    py_type_name = ''
                    msg = 'Default types will be assigned to Param '
                    msg +='with unsupported data type: %s, '
                    msg += 'for param: %s, of tool: %s, with nick name: %s'
                    msg %= (data_type, varname, self.tool_name, self.nick_name)
                    self.logger.warning(msg)
                else:
                    py_type_name = self.sDNA_types_to_py_type_names[data_type.lower()]
                    type_description = self.py_type_names_to_type_description[py_type_name]
                    description += 'Type: %s. ' % type_description

            Param_Class = self.py_type_names_to_Params.get(py_type_name
                                                          ,Param_ScriptVariable
                                                          )

            self.param_infos += ((varname
                                 ,add_params.ParamInfo(param_Class = Param_Class
                                                      ,Description = description
                                                      )
                                 ) # Tuple of two elements.
                                ,  
                                )  # Tuple of only one element 
                                   # (a tuple of a tuple of two). 


        self.sDNA = sDNA





        if has_keywords(self.nick_name, keywords = ('prepare',)):
            self.retvals += ('gdm',)

        return 'Successfully updated syntax and tool_opts.  '



    def __init__(self
                ,opts
                ,tool_name
                ,nick_name
                ,component = None
                ,import_sDNA = import_sDNA
                ):
        super(sDNA_ToolWrapper, self).__init__(opts) #self.opts = opts

        metas = opts['metas']
        self.debug('Initialising Class.  Creating Class Logger.  ')
        self.tool_name = tool_name
        self.nick_name = nick_name
        self.component = component
        self.import_sDNA = import_sDNA
        self.update_tool_opts_and_syntax(opts)

        if metas.show_all:
            new_keys = tuple(key 
                             for key in self.defaults.keys() 
                             if key not in self.component_inputs
                            )
            if new_keys:
                self.component_inputs += new_keys

            if 'advanced' not in self.defaults:
                msg = "'advanced' not in defaults_dict"
                self.logger.warning(msg)
                warnings.showwarning(message = msg
                    ,category = UserWarning
                    ,filename = __file__ + self.__class__.__name__
                    ,lineno = 253
                    )

        self.logger.debug('Params built for args from input spec:\n %s' 
                         %'\n'.join(OrderedDict(self.param_infos).keys())
                         )



    
    
    component_inputs = ('file', 'config') 


    def __call__(self # the tool instance not the GH component.
                ,f_name
                ,opts
                ,**kwargs
                ):
        #type(str, dict, dict) -> int, str
        if opts is None:
            opts = self.opts

        sDNA = opts['metas'].sDNA
        sDNAUISpec = opts['options'].sDNAUISpec



        if not hasattr(sDNAUISpec, self.tool_name): 
            raise ValueError(self.tool_name + 'not found in ' + sDNA[0])
        options = opts['options']
        metas = opts['metas']

        if self.sDNA != sDNA:  # last sDNA this tool has seen != metas.sDNA
            outcome = self.update_tool_opts_and_syntax(opts)

            # If sDNA has changed, the component really needs to be called again.
            # The script method in main currently handles this, but if this tool
            # is called from elsewhere this needs checking.  
            # Return or raise Params update error / warning?

            if outcome.lower().startswith('fail'):
                msg = ('Tried to run tool with out of date sDNA tool options. '
                      +'Tool opts and syntax require update, and sDNA modules'
                      +' require (re)importing, but this tool cannot import '
                      +' sDNA modules. '
                      )
                self.logger.error(msg)
                raise ImportError(msg)

        tool_opts_sDNA = get_tool_opts(self.nick_name, opts, self.tool_name, sDNA)


        input_file = tool_opts_sDNA.input
        

        #if (not isinstance(input_file, str)) or not isfile(input_file): 
        if (isinstance(f_name, str) and os.path.isfile(f_name)
            and os.path.splitext(f_name)[1] in ['.shp','.dbf','.shx']):  
            input_file = f_name
        else:
            logger.debug('isinstance(f_name, str) == %s' % isinstance(f_name, str))
            logger.debug('os.path.isfile(f_name) == %s' % os.path.isfile(f_name))
            logger.debug('os.path.splitext(f_name)[1] == %s' % os.path.splitext(f_name)[1])

        self.logger.debug('input == %s, f_name == %s ' % (input_file, f_name))

        if not os.path.isfile(input_file):
            msg = 'input: "%s" is not a file. To run sDNA please set file or input '
            msg += 'to the path of a valid shape file. '
            msg %= input_file
            self.logger.error(msg)
            raise ValueError(msg)
         


        output_file = tool_opts_sDNA.output
        if output_file == '':
            if self.tool_name == 'sDNAPrepare':
                output_file = options.prepped_fmt.format(name = os.path.splitext(input_file)[0])
            else:
                output_file = options.output_fmt.format(name = os.path.splitext(input_file)[0])
            output_file += '.shp'

            output_file = pyshp_wrapper.get_filename(output_file, options)

            self.logger.debug('Using auto generated output_file name: %s' % output_file)

            if (options.del_after_read and 
                not options.strict_no_del and
                not options.overwrite_shp and
                isinstance(options.input_file_deleter, ShapeFilesDeleter)):
                #
                maybe_delete = ShapeFilesDeleter(output_file)
                opts['options'] = opts['options']._replace(
                                            output_file_deleter = maybe_delete
                                            )

        input_args = tool_opts_sDNA._asdict()
        input_args.update(input = input_file, output = output_file)

        advanced = input_args.get('advanced', None)
        if not advanced:
            user_inputs = self.component.params_adder.user_inputs
            # We need this reference because some args this tool doesn't 
            # recognise, may have been added to the component, by another
            # tool on it.

            self.logger.debug('user_inputs == %s' % user_inputs)
            advanced = ';'.join(key if val is None else '%s=%s' % (key, val) 
                                for (key, val) in kwargs.items()
                                if (key in user_inputs and 
                                    key not in self.defaults)
                               )
            input_args['advanced'] = advanced
            self.logger.info('Advanced command string == %s' % advanced)
        else:
            self.logger.debug('Advanced command string == %s' % advanced)

        syntax = self.get_syntax(input_args)
        run_sDNA = self.run_sDNA_command

        f_name = output_file

        command =   (metas.python
                    + ' -u ' 
                    + '"' 
                    + os.path.join(  os.path.dirname(sDNAUISpec.__file__)
                            ,'bin'
                            ,syntax['command'] + '.py'  
                            ) 
                    + '"'
                    + ' --im ' + run_sDNA.map_to_string( syntax["inputs"] )
                    + ' --om ' + run_sDNA.map_to_string( syntax["outputs"] )
                    + ' ' + syntax["config"]
                    )
        self.logger.info('sDNA command run = ' + command)

        try:
            output_lines = subprocess.check_output(command)
            retcode = 0 
        except subprocess.CalledProcessError as e:
            self.logger.error('error.output == %s' % e.output)
            self.logger.error('error.returncode == %s' % e.returncode)
            raise e


        self.logger.info(output_lines)


        # Does not execute if subprocess raises an Exception
        if (options.del_after_sDNA and 
            not options.strict_no_del and 
            not options.overwrite_shp and 
            isinstance(options.input_file_deleter, ShapeFilesDeleter) and
            hasattr(options.input_file_deleter, 'delete_files')):
            #
            options.input_file_deleter.delete_files(
                                                delete = options.del_after_sDNA
                                               ,opts = opts
                                               )
            opts['options'] = opts['options']._replace(input_file_deleter = None)


        if has_keywords(self.nick_name, keywords = ('prepare',)):
            gdm = None
            # To overwrite any inputted gdm (already used) in vals_dict
            # to make sure a subsequent ShapefileReader adds new Geometry


        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    
    retvals = 'retcode', 'f_name'
    component_outputs = ('file',) # retvals[-1])


def get_objs_and_OrderedDicts(only_selected = False
                             ,layers = ()
                             ,shp_type = 'POLYLINEZ'
                             ,include_groups = False
                             ,all_objs_getter = pyshp_wrapper.get_Rhino_objs
                             ,group_getter = checkers.get_all_groups
                             ,group_objs_getter = checkers.get_members_of_a_group
                             ,OrderedDict_getter = checkers.get_OrderedDict()
                             ,is_shape = pyshp_wrapper.is_shape
                             ,is_selected = gdm_from_GH_Datatree.is_selected
                             ,obj_layer = gdm_from_GH_Datatree.obj_layer
                             ,doc_layers = gdm_from_GH_Datatree.doc_layers
                             ):
    #type(bool, tuple, str, bool, function, function, function, function, 
    #                             function, function, function) -> function
    if layers and isinstance(layers, basestring):
        layers = (layers,) if layers in doc_layers() else None


    def generator():
        #type( type[any]) -> list, list
        #
        # Groups first search.  If a special User Text key on member objects 
        # is used to indicate groups, then an objects first search 
        # is necessary instead, to test every object for membership
        # and track the groups yielded to date, in place of group_getter
        objs_already_yielded = []

        if include_groups:
            groups = group_getter()
            for group in groups:
                objs = group_objs_getter(group)
                if not objs:
                    continue
                if any(not is_shape(obj, shp_type) for obj in objs):                                                 
                    continue 
                if layers and any(obj_layer(obj) not in layers for obj in objs):
                    continue 
                if only_selected and any(not is_selected(obj) for obj in objs):
                    continue # Skip this group is any of the 4 conditions not met.  
                             # Correct Polylines will be picked up individually
                             # in the next code block, from the trawl from
                             # rs.ObjectsByType

                #Collate data and Yield group objs as group name.  
                objs_already_yielded += objs
                d = {}
                for obj in objs:
                    d.update(OrderedDict_getter(obj))
                yield group, d

        objs = all_objs_getter(shp_type) # e.g. rs.ObjectsByType(geometry_type = 4
                                         #                      ,select = False
                                         #                      ,state = 0
                                         #                      )
        for obj in objs:
            if obj in objs_already_yielded:
                continue 

            if layers and obj_layer(obj) not in layers:
                continue 
            if only_selected and not is_selected(obj):
                continue
            d = OrderedDict_getter(obj)
            yield str(obj), d
            # We take the str of Rhino geom obj reference (its uuid).
            # This is because Grasshopper changes uuids between 
            # connected components, even of 
            # more static Rhino objects, reducing the usefulness of
            # the original uuid.  
            # Previously was:
            # yield obj, d
        return 

    return generator()


class RhinoObjectsReader(sDNA_GH_Tool):

    class Options(object):
        selected = False
        layer = ''
        shp_type = 'POLYLINEZ'
        merge_subdicts = True
        include_groups = False


    param_infos = sDNA_GH_Tool.param_infos + (
                   ('selected', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true : only read from selection. '
                                           +'false: read all. '
                                           +'Default: %(selected)s'
                                           )
                            ))
                  ,('layer', add_params.ParamInfo(
                             param_Class = Param_String
                            ,Description = ('Text.  Names of the layers : '
                                           +'read geometry only from those '
                                           +'layers. Any value not the name '
                                           +'of a layer: read all layers. '
                                           +'Default: %(layer)s'
                                           )
                            ))
                                               )


    component_inputs = ('config', 'selected', 'layer', 'Geom') 
    
    def __call__(self, opts = None, gdm = None):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts
        self.debug('Creating Class Logger.  ')

        options = opts['options']


        sc.doc = Rhino.RhinoDoc.ActiveDoc 
        
        #rhino_groups_and_objects = make_gdm(get_objs_and_OrderedDicts(options))
        tmp_gdm = gdm if gdm else OrderedDict()

        self.logger.debug('options.selected == %s' % options.selected)
        self.logger.debug('options.layer == %s' % options.layer)
        
        doc_layers = gdm_from_GH_Datatree.doc_layers

        gdm = gdm_from_GH_Datatree.make_gdm( get_objs_and_OrderedDicts(
                                                 only_selected = options.selected
                                                ,layers = options.layer
                                                ,shp_type = options.shp_type
                                                ,include_groups = options.include_groups 
                                                ,doc_layers = doc_layers
                                                ) 
                       )
        # lambda : {}, as User Text is read elsewhere, in read_Usertext



        self.logger.debug('First objects read: \n' 
                         +'\n'.join( str(x) 
                                     for x in gdm.keys()[:3]
                                   )
                         )
        if gdm:
            self.logger.debug('type(gdm[0]) == ' + type(gdm.keys()[0]).__name__ )


        if tmp_gdm:
            gdm = gdm_from_GH_Datatree.override_gdm(gdm
                                                   ,tmp_gdm
                                                   ,options.merge_subdicts
                                                   )

        if not gdm:
            msg = 'Was unable to read any Rhino Geometry.  '
            if options.selected:
                msg += 'selected == %s. Select some objects ' % options.selected
                msg += ' or set selected = false.  '
            elif options.layer and (
                (isinstance(options.layer, basestring) 
                 and options.layer in doc_layers()) or (
                 isinstance(options.layer, Iterable) and
                 any(layer in doc_layers() for layer in options.layer))):
                 #
                msg += 'layer == %s. ' % options.layer
                msg += 'Please set layer to the name of a layer containing objects'
                msg += ', or to select all layers, set layer to any value that is '
                msg += 'not the name of an existing layer.  ' 
            msg += 'gdm == %s' % gdm
            self.logger.error(msg)
            raise ValueError(msg)

        self.logger.debug('after override ....Last objects read: \n'
                         +'\n'.join( str(x) 
                                     for x in gdm.keys()[-3:]
                                   )
                         )

        sc.doc = ghdoc 
        self.logger.debug('retvals == %s ' % self.retvals)
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)


    retvals = ('gdm',)
    component_outputs = ('Geom', ) 


class UsertextReader(sDNA_GH_Tool):

    class Options(object):
        pass

    component_inputs = ('Geom',) 

    def __call__(self, gdm):
        #type(str, dict, dict) -> int, str, dict, list

        self.debug('Starting read_Usertext...  Creating Class logger. ')
        self.logger.debug('type(gdm) == %s ' % type(gdm))
        self.logger.debug('gdm[:3] == %s ' % {key : gdm[key] for key in gdm.keys()[:3]} )
        
        if not gdm:
            msg = 'No Geometric objects to read User Text from, gdm == %s' % gdm
            self.logger.error(msg)
            raise ValueError(msg)
        
        gdm = gdm.copy()

        sc.doc = Rhino.RhinoDoc.ActiveDoc

        for obj in gdm:
            try:
                keys = rs.GetUserText(obj)
                gdm[obj].update( (key, rs.GetUserText(obj, key)) for key in keys )
            except ValueError:
                pass

        # read_Usertext_as_tuples = checkers.get_OrderedDict()
        # for obj in gdm:
        #     gdm[obj].update(read_Usertext_as_tuples(obj))


        sc.doc = ghdoc  
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)


    retvals = ('gdm',)
    component_outputs = ('Data', ) 



   


class ShapefileWriter(sDNA_GH_Tool):

    class Options(InputFileDeletionOptions, pyshp_wrapper.ShpOptions):
        shp_type = 'POLYLINEZ'
        input_key_str = ('sDNA input name={name} '  # User Text keys to read
                        +'type={fieldtype} '
                        +'size={size}'
                        )
        path = __file__
        output_shp = '' 


    param_infos = sDNA_GH_Tool.param_infos + (
                                ('prj'
                                ,add_params.ParamInfo(
                                  param_Class = Param_String
                                 ,Description = ('File path of the projection '
                                                +'file (.prj) to use for the '
                                                +'new shapefile. '
                                                )
                                 )
                                ),
                                             ) 


    

    component_inputs = ('Geom', 'Data', 'file', 'prj', 'config') 

    def __call__(self, f_name, gdm, prj = None, opts = None):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts
        options = opts['options']
        self.debug('Creating Class Logger.  ')


        shp_type = options.shp_type            


        format_string = options.input_key_str
        pattern = funcs.make_regex( format_string )

        def pattern_match_key_names(x):
            #type: (str)-> object #re.MatchObject

            return re.match(pattern, x) 

        def f(z):
            if hasattr(Rhino.Geometry, type(z).__name__):
                z_geom = z
            else:
                z = System.Guid(str(z))
                z_geom = Rhino.RhinoDoc.ActiveDoc.Objects.FindGeometry(z)
                if not z_geom:
                    z_geom = ghdoc.Objects.FindGeometry(z)
            if hasattr(z_geom,'TryGetPolyline'):
                z_geom = z_geom.TryGetPolyline()[1]
            return [list(z_geom[i]) for i in range(len(z_geom))]

        def get_list_of_lists_from_tuple(obj):
            return [f(obj)]

        if gdm:
            self.logger.debug('Test points obj 0: %s ' % get_list_of_lists_from_tuple(gdm.keys()[0]) )
        else:
            msg = 'No geometry and no data to write to shapefile, gdm == %s' % gdm
            self.logger.error(msg)
            raise ValueError(msg)

        def shape_IDer(obj):
            return obj #tupl[0].ToString() # uuid

        def find_keys(obj):
            return gdm[obj].keys() #tupl[1].keys() #rs.GetUserText(x,None)

        def get_data_item(obj, key):
            return gdm[obj][key] #tupl[1][key]

        if not f_name:  
            f_name = options.output_shp

        if (not isinstance(f_name, str) or 
            not os.path.isdir(os.path.dirname(f_name))):
            
            f_name = os.path.splitext(options.path)[0] + '.shp'
            # Copy RhinoDoc or GH definition name without .3dm or .gh

            f_name = pyshp_wrapper.get_filename(f_name, options)
            
            logger.info('Using automatically generated file name: %s' % f_name)

            if (options.del_after_sDNA and 
                not options.strict_no_del and 
                not options.overwrite_shp):
                # Don't delete a shapefile that only just overwrote 
                # another pre-existing shapefile.
                maybe_delete = ShapeFilesDeleter(f_name)
                opts['options'] = opts['options']._replace(
                                            input_file_deleter = maybe_delete
                                            )
            else:
                do_not_delete = NullDeleter() # Slight hack, so sDNA_tool knows
                                              # f_name (input_file) is 
                                              # auto-generated, so it can tell 
                                              # if output_file is also
                                              # auto-generated, and only if so
                                              # maybe making a 
                                              # ShapeFilesDeleter for it.
                opts['options'] = opts['options']._replace(
                                            input_file_deleter = do_not_delete
                                            )

        self.logger.debug(f_name)



        retcode, f_name, fields, gdm = pyshp_wrapper.write_iterable_to_shp(
                                 my_iterable = gdm
                                ,shp_file_path = f_name 
                                ,shape_mangler = get_list_of_lists_from_tuple 
                                ,shape_IDer = shape_IDer
                                ,key_finder = find_keys 
                                ,key_matcher = pattern_match_key_names 
                                ,value_demangler = get_data_item 
                                ,shape_code = shp_type 
                                ,options = options
                                ,field_names = None 
                                )
        
        if (isinstance(prj, str) and 
            prj.endswith('.prj') and 
            os.path.isfile(prj)):
            #
            new_prj = os.path.splitext(f_name)[0] + '.prj'
            shutil.copy2(prj, new_prj)

        # get_list_of_lists_from_tuple() will 
        # switch the targeted file to RhinoDoc if needed, hence the following line 
        # is important:
        sc.doc = ghdoc  
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = 'retcode', 'f_name', 'gdm'
    component_outputs =  ('file',) 
               


class ShapefileReader(sDNA_GH_Tool):

    class Options(OutputFileDeletionOptions):
        new_geom = True
        bake = True
        uuid_field = 'Rhino3D_'
        sDNA_names_fmt = '{name}.shp.names.csv'
        prepped_fmt = '{name}_prepped'
        output_fmt = '{name}_output'
                        
    component_inputs = ('file', 'Geom', 'bake') # existing 'Geom', otherwise new 
                                                # objects need to be created

    def __call__(self, f_name, gdm, opts = None):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts
        options = opts['options']

        self.debug('Creating Class Logger.  Checking shapefile... ')

        if not os.path.isfile(f_name):
            msg = "'File': %s  is not a valid file. " % f_name
            self.logger.error(msg)
            raise ValueError(msg)


        self.logger.debug('Reading shapefile... ')
        (shp_fields
        ,recs
        ,shapes
        ,bbox ) = pyshp_wrapper.get_fields_recs_and_shapes( f_name )

        self.logger.debug('bbox == %s' % bbox)

        self.logger.debug('gdm == %s ' % gdm)

        self.logger.debug('recs[0].as_dict() == %s ' % recs[0].as_dict())

        if not recs:
            self.logger.warning('No data read from Shapefile ' + f_name + ' ')
            return 1, f_name, gdm, None    
            
        if not shapes:
            self.logger.warning('No shapes in Shapefile ' + f_name + ' ')
            if not gdm:
                self.logger.warning('No Geom objects in Geom Data Mapping.  ')
            return 1, f_name, gdm, None


        if not bbox:
            self.logger.warning('No Bounding Box in Shapefile.  '
                   + f_name 
                   + ' '
                   +'Supply bbox manually or create rectangle to plot legend.'
                   )
            

        fields = [ x[0] for x in shp_fields ]

        self.logger.debug('options.uuid_field in fields == ' 
                         +str(options.uuid_field in fields)
                         )
        self.logger.debug(fields) 



        self.logger.debug('Testing existing geom data map.... ')
        if (options.new_geom or not gdm or not isinstance(gdm, dict) 
             or len(gdm) != len(recs) ):
            #shapes_to_output = ([shp.points] for shp in shapes )
            
            objs_maker = pyshp_wrapper.objs_maker_factory(options.shp_type)
                         # this is rs.AddPolyline for shp_type = 'POLYLINEZ'
            shapes_to_output = (
                str(objs_maker(shp.points)) if options.bake else objs_maker(shp.points)
                for shp in shapes 
                )
            #self.logger.debug('shapes == %s' % shapes)
            self.logger.debug('objs_maker == %s' % objs_maker)
        else:
            #elif isinstance(gdm, dict) and len(gdm) == len(recs):
            # an override for different number of overridden geom objects
            # to shapes/recs opens a large a can of worms.  Unsupported.

            self.logger.debug('Geom data map matches shapefile.  ')

            shapes_to_output = list(gdm.keys()) 
            #                  dict.keys() is a dict view in Python 3



        shp_file_gen_exp  = itertools.izip(shapes_to_output
                                          ,(rec.as_dict() for rec in recs)
                                          )

        if options.bake:
            sc.doc = Rhino.RhinoDoc.ActiveDoc
        gdm = gdm_from_GH_Datatree.make_gdm(shp_file_gen_exp)
        sc.doc = ghdoc 

        self.logger.debug('bbox == %s ' % bbox)


        file_name = os.path.splitext(f_name)[0]
        csv_f_name = options.sDNA_names_fmt.format(name = file_name)
        #sDNA_fields = {}
        if os.path.isfile(csv_f_name):
# sDNA writes this file in simple 'w' mode, 
# Line 469
# https://github.com/fiftysevendegreesofrad/sdna_open/blob/master/arcscripts/sdna_environment.py
            with open(csv_f_name, 'r') as f:   # In Python 2 there's no encoding argument
                #https://docs.python.org/2.7/library/functions.html#open
                #
                #sDNA_fields = [OrderedDict( line.split(',') for line in f )]
                abbrevs = [line.split(',')[0] for line in f ]

        else:
            msg = "No sDNA names.csv abbreviations file: %s found. " % csv_f_name
            abbrevs = [msg]
            self.logger.info(msg)


        if ((options.del_after_read and 
            not options.strict_no_del and 
            not options.overwrite_shp) and 
            isinstance(options.output_file_deleter, ShapeFilesDeleter)):
            #
            options.output_file_deleter.delete_files(delete = options.del_after_read
                                                   ,opts = opts
                                                   )
            opts['options'] = opts['options']._replace(
                                        output_file_deleter = None
                                        )
        retcode = 0

        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)


    retvals = 'retcode', 'gdm', 'abbrevs', 'fields', 'bbox'
    component_outputs = ('Geom', 'Data') + retvals[2:]

    param_infos = sDNA_GH_Tool.param_infos + (
            ('bake', add_params.ParamInfo(
                           param_Class = Param_Boolean
                          ,Description = ('If Geom is connected, does nothing.'
                                         +' Otherwise, true (default): bakes '
                                         +'the shapefile polylines to Rhino.  '
                                         +'false: creates Grasshopper '
                                         +'polylines only.'
                                         )
                          ))
            ,('abbrevs', add_params.ParamInfo(
                           param_Class = Param_String
                          ,Description = ('Abbreviations of sDNA results from '
                                         +'the ...names.csv file. '
                                         )
                          ))
            ,('fields', add_params.ParamInfo(
                             param_Class = Param_String
                            ,Description = ('Field names from the Shapefile. '
                                           +'Set field to one of these values '
                                           +'to parse and/or plot it. '
                                           )
                            ))
            ,('bbox', add_params.ParamInfo(
                         param_Class = Param_ScriptVariable
                        ,Description = ('Bounding box from the Shapefile. '
                                       +'Used to calculate leg_frame by '
                                       +'the Recolour_objects component. '
                                       +'[x_min, y_min, x_max, y_max]. All '
                                       +'Numbers.'
                                       ) 
                        ))      
                                             )







class UsertextWriter(sDNA_GH_Tool):

    class Options(object):
        uuid_field = 'Rhino3D_'
        output_key_str = 'sDNA output={name} run time={datetime}'
        overwrite_UserText = True
        max_new_keys = 10
        dupe_key_suffix = '_{}'
        suppress_overwrite_warning = False

                        

    component_inputs = ('Geom', 'Data')


    def __call__(self, gdm, opts):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts        
        options = opts['options']

        date_time_of_run = asctime()
        self.debug('Creating Class logger at: %s ' % date_time_of_run)

        if not gdm:
            msg = 'No Geom objects to write to. '
            msg += 'Connect list of objects to Geom. '
            msg += ' gdm == %s' % gdm
            self.logger.error(msg)
            raise ValueError(msg)

        if all(not value for value in gdm.values()):
            msg = 'No Data to write as User Text. '
            msg += 'Please connect data tree to Data. '
            msg += ' gdm == %s' % gdm
            self.logger.error(msg)
            raise ValueError(msg)




        def write_dict_to_UserText_on_Rhino_obj(d, rhino_obj):
            #type(dict, str) -> None
            if not isinstance(d, dict):
                msg = 'dict required by write_dict_to_UserText_on_Rhino_obj'
                self.logger.error(msg)
                raise TypeError(msg)
            
            #if is_an_obj_in_GH_or_Rhino(rhino_obj):
                # Checker switches GH/ Rhino context
                 
            existing_keys = rs.GetUserText(rhino_obj)
            if options.uuid_field in d:
                obj = d.pop( options.uuid_field )
            
            for key in d:

                s = options.output_key_str
                UserText_key_name = s.format(name = key
                                            ,datetime = date_time_of_run
                                            )
                
                if not options.overwrite_UserText:

                    for i in range(0, options.max_new_keys):
                        tmp = UserText_key_name 
                        tmp += options.dupe_key_suffix.format(i)
                        if tmp not in existing_keys:
                            break
                    UserText_key_name = tmp
                else:
                    if not options.suppress_overwrite_warning:
                        self.logger.warning( "UserText key == " 
                                    + UserText_key_name 
                                    +" overwritten on object with guid " 
                                    + str(rhino_obj)
                                    )

                rs.SetUserText(rhino_obj, UserText_key_name, str( d[key] ), False)                    


                #write_obj_val(rhino_obj, UserText_key_name, str( d[key] ))
            # else:
            #     self.logger.info('Object: ' 
            #              + key[:10] 
            #              + ' is neither a curve nor a group. '
            #              )
        sc.doc = Rhino.RhinoDoc.ActiveDoc
        
        for key, val in gdm.items():
            try:
                write_dict_to_UserText_on_Rhino_obj(val, key)
            except ValueError:
                pass

        sc.doc = ghdoc  
        
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)
    
    retvals = ()
    component_outputs = () 





class DataParser(sDNA_GH_Tool):


    quantile_methods = dict(simple = data_cruncher.simple_quantile
                           ,max_deltas = data_cruncher.class_bounds_at_max_deltas
                           ,adjuster = data_cruncher.quantile_l_to_r
                           ,quantile = data_cruncher.spike_isolating_quantile
                           )


    class Options(data_cruncher.SpikeIsolatingQuantileOptions):
        field = 'BtEn'
        plot_min = options_manager.Sentinel('plot_min is automatically '
                                           +'calculated by sDNA_GH unless '
                                           +'overridden.  '
                                           )
        plot_max = options_manager.Sentinel('plot_max is automatically '
                                           +'calculated by sDNA_GH unless '
                                           +'overridden.  '
                                           )
        re_normaliser = 'linear'
        sort_data = False
        num_classes = 8
        class_bounds = [options_manager.Sentinel('class_bounds is automatically '
                                                +'calculated by sDNA_GH unless '
                                                +'overridden.  '
                                                )
                       ]
        # e.g. [2000000, 4000000, 6000000, 8000000, 10000000, 12000000]
        class_spacing = 'quantile'
        _valid_class_spacings = data_cruncher.valid_re_normalisers + ('quantile'
                                                                     ,'combo'
                                                                     ,'max_deltas'
                                                                     )
        base = 10 # for Log and exp
        colour_as_class = False
        locale = '' # '' => User's own settings.  Also in DataParser
        # e.g. 'fr', 'cn', 'pl'. IETF RFC1766,  ISO 3166 Alpha-2 code
        num_format = '{:.5n}'  #n is a number referring to the current locale setting
        first_leg_tag_str = 'below {upper}'
        gen_leg_tag_str = '{lower} - {upper}'
        last_leg_tag_str = 'above {lower}'
        exclude = False
        remove_overlaps = True
        suppress_small_classes_error = False
        suppress_class_overlap_error = False
        
        assert re_normaliser in data_cruncher.valid_re_normalisers
        assert class_spacing in _valid_class_spacings
                        
    param_infos = sDNA_GH_Tool.param_infos + (
                   ('field', add_params.ParamInfo(
                             param_Class = Param_String
                            ,Description = ('The field name / key value of '
                                           +'the results field to parse '
                                           +'and/or plot. Default: %(field)s'
                                           )
                            ))
                  ,('plot_max', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('Maximum data value to parse. '
                                           +'Higher values (and their '
                                           +'objects) are omitted. '
                                           +'Automatically calculated if unset.'
                                           )
                            ))
                  ,('plot_min', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('Minimum data value to parse. '
                                           +'Lower values (and their '
                                           +'objects) are omitted. '
                                           +'Automatically calculated if unset.'
                                           )
                            ))
                  ,('num_classes', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('Number of classes in the legend. '
                                           +'Integer. Default: %(num_classes)s' 
                                           )
                            ))                        
                  ,('class_spacing', add_params.ParamInfo(
                             param_Class = Param_String
                            ,Description = ('Name of method to use to '
                                           +'classify the data / calculate '
                                           +'the classes for the legend. '
                                           +('Allowed Values: %s' 
                                            % quantile_methods.keys()
                                            ) # can't interpolate before the 
                                              # default field
                                           +'Default: %(class_spacing)s'
                                           ) 
                            ))
                  ,('class_bounds', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('Inter-class boundaries for the '
                                           +'legend. '
                                           +'Automatically calculated using '
                                           +'the method in class_spacing if '
                                           +'unset.'
                                           )
                            ))
                                               )

    component_inputs = ('Geom', 'Data', 'field', 'plot_max', 'plot_min' 
                       ,'num_classes', 'class_spacing', 'class_bounds'
                       )
    #
    # Geom is essentially unused in this function, except that the legend tags
    # are appended to it, to colour them in exactly the same way as the 
    # objects.
    #
    def __call__(self, gdm, opts):
        #type(str, dict, dict) -> int, str, dict, list
        # Note!  opts can be mutated.
        if opts is None:
            opts = self.opts
        self.debug('Starting ParseData tool.  ')
        options = opts['options']

        field = options.field

        if not gdm:
            msg = 'No Geom. Parser requires Geom to preserve correspondence '
            msg += 'if the Data is re-ordered. '
            msg += 'Connect list of objects to Geom. '
            msg += ' gdm == %s' % gdm
            self.logger.error(msg)
            raise ValueError(msg)

        items_missing_field = [(key, val)
                               for (key, val) in gdm.items() 
                               if (not isinstance(val, dict) or
                                   field not in val or 
                                   not isinstance(val[field], Number))
                              ]

        if items_missing_field:
            msg = 'Missing data for field.  '
            msg += 'The following: %s have a non-numeric record '
            msg += 'for the field name: %s (or no record at all), '
            msg += 'and so cannot be parsed for field: %s'
            msg %= (items_missing_field, field, field)
            self.logger.error(msg)
            raise ValueError(msg)



        plot_min, plot_max = options.plot_min, options.plot_max
        if (isinstance(plot_min, Number)  
           and isinstance(plot_max, Number) 
           and plot_min < plot_max ):
            #
            self.logger.info('Valid max and min override will be used. ')
            #
            x_min, x_max = plot_min, plot_max 
            if options.exclude:
                data = OrderedDict( (obj, val[field]) 
                                    for obj, val in gdm.items()
                                    if x_min <= val[field] <= x_max
                                  )
            else:
                data = OrderedDict( (obj, min(x_max, max(x_min, val[field]))) 
                                    for obj, val in gdm.items()
                                  )

        else:
            self.logger.debug('Manually calculating max and min. '
                      +'No valid override found. '
                      )
            data = OrderedDict( (obj, val[field]) 
                                for obj, val in gdm.items() 
                              )
            x_min, x_max = min(data.values()), max(data.values())
            self.logger.debug('x_min == %s, x_max == %s' % (x_min, x_max))
        # bool(0) is False so in case x_min==0 we can't use if options.plot_min
        # so test isinstance of Number ABC. 
        #
        # x_min & x_max are not stored in options, so sDNA_GH will carry on 
        # auto calculating min and max on future runs.  Once they are
        # overridden, the user must set them to an invalid override 
        # (e.g. max <= min) to go back to auto-calculation.

        self.logger.debug('data.values() == %s, ... ,%s' % (tuple(data.values()[:3])
                                                           ,tuple(data.values()[-3:])
                                                           )
                         ) 




        use_manual_classes = (options.class_bounds and
                              isinstance(options.class_bounds, list)
                              and all( isinstance(x, Number) 
                                       for x in options.class_bounds
                                     )
                             )

        if options.sort_data or (
           not use_manual_classes 
           and options.class_spacing in self.quantile_methods ):
            # 
            self.logger.info('Sorting data... ')
            data = OrderedDict( sorted(data.items()
                                      ,key = lambda tupl : tupl[1]
                                      ) 
                              )
            self.logger.debug('data.values() == %s, ... ,%s' % (tuple(data.values()[:3])
                                                               ,tuple(data.values()[-3:])
                                                               )
                             ) 

        param={}
        param['exponential'] = param['logarithmic'] = options.base

        n = len(data)
        m = min(n, options.num_classes)

        class_size = n // m
        if class_size < 1:
            msg = 'Class size == %s  is less than 1 ' % class_size
            if options.suppress_small_classes_error:
                self.logger.warning(msg)
                warnings.showwarning(message = msg
                                    ,category = UserWarning
                                    ,filename = __file__ + '.' + self.__class__.__name__
                                    ,lineno = 1050
                                    )
            else:
                self.logger.error(msg)
                raise ValueError(msg)



        if use_manual_classes:
            class_bounds = options.class_bounds
            self.logger.info('Using manually specified'
                            +' inter-class boundaries. '
                            )
        elif options.class_spacing in self.quantile_methods:
            self.logger.debug('Using: %s class calculation method.' % options.class_spacing)
            class_bounds = self.quantile_methods[options.class_spacing](data = data.values()
                                                                       ,num_classes = m
                                                                       ,options = options
                                                                       )

        else: 
            class_bounds = [data_cruncher.splines[options.class_spacing](i
                                                          ,1
                                                          ,param.get(options.class_spacing
                                                                    ,'Not used'
                                                                    )
                                                          ,options.num_classes
                                                          ,y_min = x_min
                                                          ,y_max = x_max
                                                          )     
                            for i in range(1, options.num_classes) 
                            ]

        count_bound_counts = Counter(class_bounds)

        class_overlaps = [val for val in count_bound_counts
                          if count_bound_counts[val] > 1
                         ]

        if class_overlaps:
            msg = 'Class overlaps at: ' + ' '.join(map(str, class_overlaps))
            if options.remove_overlaps:
                for overlap in class_overlaps:
                    class_bounds.remove(overlap)

            if options.suppress_class_overlap_error:
                self.logger.warning(msg)
                warnings.showwarning(message = msg
                                    ,category = UserWarning
                                    ,filename = 'DataParser.tools.py'
                                    ,lineno = 1001
                                    )
            else:
                self.logger.error(msg)
                raise ValueError(msg)


            if options.re_normaliser not in data_cruncher.valid_re_normalisers:
                # e.g.  'linear', exponential, logarithmic
                msg = 'Invalid re_normaliser : %s ' % options.re_normaliser
                self.logger.error(msg)
                raise ValueError(msg)


        self.logger.debug('num class boundaries == ' 
                    + str(len(class_bounds))
                    )
        self.logger.debug('m == %s' % m)
        self.logger.debug('n == %s' % n)
        if len(class_bounds) + 1 < m:
            logger.warning('It has only been possible to classify data into '
                          +'%s distinct classes, not %s' % (len(class_bounds) + 1, m)
                          )

        msg = 'x_min == %s \n' % x_min
        msg += 'class bounds == %s \n' % class_bounds
        msg += 'x_max == %s ' % x_max
        self.logger.debug(msg)


        def re_normalise(x, p = param.get(options.re_normaliser, 'Not used')):
            spline = data_cruncher.splines[options.re_normaliser]
            return spline(x
                        ,x_min
                        ,p   # base or x_mid.  Can't be kwarg.
                        ,x_max
                        ,y_min = x_min
                        ,y_max = x_max
                        )
        
        def class_mid_point(x): 
            highest_lower_bound = x_min if x < class_bounds[0] else max(
                                            y 
                                            for y in [x_min] + class_bounds
                                            if y <= x                  
                                            )
            #Classes include their lower bound
            least_upper_bound = x_max if x >= class_bounds[-1] else min(
                                            y 
                                            for y in class_bounds + [x_max] 
                                            if y > x
                                            )

            return re_normalise(0.5*(least_upper_bound + highest_lower_bound))



        if options.colour_as_class:
            renormaliser = class_mid_point
        else:
            renormaliser = re_normalise






        mid_points = [0.5*(x_min + min(class_bounds))]
        mid_points += [0.5*(x + y) for (x,y) in zip(class_bounds[0:-1]
                                                   ,class_bounds[1:]  
                                                   )
                      ]
        mid_points += [ 0.5*(x_max + max(class_bounds))]
        self.logger.debug(mid_points)

        locale.setlocale(locale.LC_ALL,  options.locale)

        def format_number(x, format_str):
            #type(Number, str) -> str
            if isinstance(x, int):
                format_str = '{:d}'
            return format_str.format(x)

        x_min_str = format_number(x_min, options.num_format) 
        upper_str = format_number(min( class_bounds ), options.num_format)
        mid_pt_str = format_number(mid_points[0], options.num_format)
        #e.g. first_leg_tag_str = 'below {upper}'

        legend_tags = [options.first_leg_tag_str.format(lower = x_min_str
                                                       ,upper = upper_str
                                                       ,mid_pt = mid_pt_str
                                                       )
                      ]
        for lower_bound, class_mid_point, upper_bound in zip(class_bounds[0:-1]
                                                      ,mid_points[1:-1]
                                                      ,class_bounds[1:]  
                                                      ):
            
            lower_str = format_number(lower_bound, options.num_format)
            upper_str = format_number(upper_bound, options.num_format)
            mid_pt_str = format_number(class_mid_point, options.num_format)
            # e.g. gen_leg_tag_str = '{lower} - {upper}' # also supports {mid}
            legend_tags += [options.gen_leg_tag_str.format(lower = lower_str
                                                          ,upper = upper_str
                                                          ,mid_pt = mid_pt_str 
                                                          )
                           ]

        lower_str =  format_number(max( class_bounds ), options.num_format)
        x_max_str =  format_number(x_max, options.num_format)
        mid_pt_str =  format_number(mid_points[-1], options.num_format)

        # e.g. last_leg_tag_str = 'above {lower}'
        legend_tags += [options.last_leg_tag_str.format(lower = lower_str
                                                       ,upper = x_max_str 
                                                       ,mid_pt = mid_pt_str 
                                                       )        
                       ]                                                       

        self.logger.debug(legend_tags)

        objs = list( gdm.keys() )[:]
        data_vals = [val[field] for val in gdm.values()]

        gdm = OrderedDict(   zip(objs + legend_tags 
                                ,[renormaliser(x) for x in data_vals + mid_points]
                                )
                         )
        plot_min, plot_max = x_min, x_max
        
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = 'plot_min', 'plot_max', 'gdm'
    component_outputs = retvals[:2] + ('Data', 'Geom')



class ObjectsRecolourer(sDNA_GH_Tool):

    class Options(object):
        field = 'BtEn'
        Col_Grad = False
        Col_Grad_num = 5
        rgb_max = (155, 0, 0) #990000
        rgb_min = (0, 0, 125) #3333cc
        rgb_mid = (0, 155, 0) # guessed
        line_width = 4 # millimetres? 
        first_leg_tag_str = 'below {upper}'
        gen_leg_tag_str = '{lower} - {upper}'
        last_leg_tag_str = 'above {lower}'
        leg_extent = options_manager.Sentinel('leg_extent is automatically '
                                             +'calculated by sDNA_GH unless '
                                             +'overridden.  '
                                             )
        # [xmin, ymin, xmax, ymax]
        bbox = options_manager.Sentinel('bbox is automatically calculated by '
                                       +'sDNA_GH unless overridden.  '
                                       ) 
        # [xmin, ymin, xmax, ymax]


    GH_Gradient_preset_names = {0 : 'EarthlyBrown'
                               ,1 : 'Forest'
                               ,2 : 'GreyScale'
                               ,3 : 'Heat'
                               ,4 : 'SoGay'
                               ,5 : 'Spectrum'
                               ,6 : 'Traffic'
                               ,7 : 'Zebra'
                               }

    def __init__(self
                ,opts
                ,parse_data = None
                ):

        super(ObjectsRecolourer, self).__init__(opts)

        if parse_data is None:
            parse_data = DataParser(opts)

        self.parse_data = parse_data


        self.param_infos += (
             ('plot_min', dict(self.parse_data.param_infos)['plot_min'])
            ,('plot_max', dict(self.parse_data.param_infos)['plot_max'])
            ,('field', dict(self.parse_data.param_infos)['field'])
            ,('bbox', add_params.ParamInfo(
                         param_Class = Param_ScriptVariable
                        ,Description = ('Bounding box of geometry. Used '
                                       +'to calculate extent of leg_frame.'
                                       +'Calculated from shapefiles by the '
                                       +'Read_shapefile component. '
                                       +'[x_min, y_min, x_max, y_max], all '
                                       +'Numbers.'
                                       ) 
                        )
             )                        
            )

    
    component_inputs = ('plot_min', 'plot_max', 'Data', 'Geom', 'bbox', 'field')

    def __call__(self, gdm, opts, plot_min, plot_max, bbox):
        #type(str, dict, dict) -> int, str, dict, list
        # Note!  opts can be mutated.
        self.debug('Initialising Class.  Creating Class Logger. ')

        if opts is None:
            opts = self.opts
        options = opts['options']
        
        field = options.field

        if not gdm:
            msg = 'No Geom objects to recolour. '
            msg += 'Connect list of objects to Geom. '
            msg += ' gdm == %s' % gdm
            self.logger.error(msg)
            raise ValueError(msg)




        objs_to_parse = OrderedDict((k, v) for k, v in gdm.items()
                                    if isinstance(v, dict) and field in v    
                                   )  # any geom with a normal gdm dict of keys / vals

        objs_to_get_colour = OrderedDict( (k, v) for k, v in gdm.items()
                                                if isinstance(v, Number) 
                                        )

        if (objs_to_parse or 
           (objs_to_get_colour and (plot_min is None or plot_max is None))):
           #
            self.info('Raw data in ObjectsRecolourer.  Calling DataParser...')
            self.debug('Raw data: %s' % objs_to_parse.items()[:4])
            x_min, x_max, gdm_in = self.parse_data(gdm = objs_to_parse
                                                  ,opts = opts
                                                  )
                                                                            
        else:
            self.logger.debug('Skipping parsing')
            gdm_in = {}
            x_min, x_max = plot_min, plot_max

        self.logger.debug('x_min == %s ' % x_min)
        self.logger.debug('x_max == %s ' % x_max)


        objs_to_get_colour.update(gdm_in)  # no key clashes possible unless some x
                                        # isinstance(x, dict) 
                                        # and isinstance(x, Number)
        if options.Col_Grad:
            grad = getattr( GH_Gradient()
                        ,self.GH_Gradient_preset_names[options.Col_Grad_num])
            def get_colour(x):
                # Number-> Tuple(Number, Number, Number)
                # May need either rhinoscriptsyntax.CreateColor
                # or System.Drawing.Color.FromArgb and even 
                # Grasshopper.Kernel.Types.GH_Colour calling on the result to work
                # in Grasshopper
                linearly_interpolate = data_cruncher.enforce_bounds(
                                            data_cruncher.linearly_interpolate)
                return grad().ColourAt( linearly_interpolate(x
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
                rgb_col =  data_cruncher.map_f_to_three_tuples(
                                         data_cruncher.three_point_quad_spline
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

        objs_to_recolour = OrderedDict( (k, v) 
                                        for k, v in gdm.items()
                                        if isinstance(v, System.Drawing.Color)  
                                      )

        if not objs_to_get_colour and not objs_to_recolour:
            msg = 'No objects to recolour have been found. '
            msg += 'objs_to_parse == %s, ' % objs_to_parse
            msg += 'objs_to_get_colour == %s, ' % objs_to_get_colour
            msg += 'objs_to_recolour == %s.  ' % objs_to_recolour
            self.logger.error(msg)
            raise ValueError(msg)
            
        objs_to_recolour.update( (key,  get_colour(val))
                                 for key, val in objs_to_get_colour.items()
                               )


        legend_tags = OrderedDict()
        legend_first_pattern = funcs.make_regex(options.first_leg_tag_str)
        legend_inner_pattern = funcs.make_regex(options.gen_leg_tag_str)
        legend_last_pattern = funcs.make_regex(options.last_leg_tag_str)

        legend_tag_patterns = (legend_first_pattern
                              ,legend_inner_pattern
                              ,legend_last_pattern
                              )


        GH_objs_to_recolour = OrderedDict()
        recoloured_Rhino_objs = []

        # if hasattr(Rhino.Geometry, type(z).__name__):
        #     z_geom = z
        # else:
        #     z = System.Guid(str(z))
        #     z_geom = Rhino.RhinoDoc.ActiveDoc.Objects.FindGeometry(z)
        #     if not z_geom:
        #         z_geom = ghdoc.Objects.FindGeometry(z)

        sc.doc = Rhino.RhinoDoc.ActiveDoc

        for obj, new_colour in objs_to_recolour.items():
            #self.logger.debug('obj, is_uuid == %s, %s ' % (obj, is_uuid(obj))) 
            
            # try:
            #     obj_guid = System.Guid(str(obj))
            #     obj_geom = Rhino.RhinoDoc.ActiveDoc.Objects.FindGeometry(obj_guid)
            # except:
            #     obj_geom = None

            # if obj_geom:
            if isinstance(obj, str) and any(bool(re.match(pattern, obj)) 
                                            for pattern in legend_tag_patterns 
                                           ):
                #sc.doc = ghdoc it's now never changed, 
                #assert sc.doc == ghdoc #anyway
                legend_tags[obj] = rs.CreateColor(new_colour) # Could glitch if dupe  
            else:
                try:
                    rs.ObjectColor(obj, new_colour)
                    recoloured_Rhino_objs.append(obj)
                except ValueError:
                    GH_objs_to_recolour[obj] = new_colour 
                    
        sc.doc = ghdoc
            


        keys = recoloured_Rhino_objs
        if keys:
            sc.doc = Rhino.RhinoDoc.ActiveDoc                             
            rs.ObjectColorSource(keys, 1)  # 1 => colour from object
            rs.ObjectPrintColorSource(keys, 2)  # 2 => colour from object
            rs.ObjectPrintWidthSource(keys, 1)  # 1 => logger.debug width from object
            rs.ObjectPrintWidth(keys, options.line_width) # width in mm
            rs.Command('_PrintDisplay _State=_On Color=Display Thickness='
                    +str(options.line_width)
                    +' _enter')
            #sc.doc.Views.Redraw()
            sc.doc = ghdoc




        if (bbox or not isinstance(options.leg_extent
                                  ,(options_manager.Sentinel, type(None))
                                  )
                 or not isinstance(options.bbox
                                  ,(options_manager.Sentinel, type(None))
                                  )):
            #
            if (not isinstance(options.leg_extent, options_manager.Sentinel) 
                and options.leg_extent):
                #
                [legend_xmin
                ,legend_ymin
                ,legend_xmax
                ,legend_ymax] = options.leg_extent
                self.logger.debug('legend extent == %s ' % options.leg_extent)
            else: 
                if bbox:
                    self.logger.debug('Using bbox from args')
                    [bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax] = bbox
                elif not isinstance(options.bbox, options_manager.Sentinel):
                    self.logger.debug('Using options.bbox override. ')
                    [bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax] = options.bbox
                    bbox = options.bbox

                leg_width = math.sqrt((bbox_xmax - bbox_xmin)**2 
                                     +(bbox_ymax - bbox_ymin)**2
                                     ) / 2
                tag_height = max(1, 0.4 * leg_width / 7)
                leg_height = min(options.num_classes * tag_height * 1.04
                                ,bbox_ymax - bbox_ymin
                                )
                legend_xmin = bbox_xmax - leg_width
                legend_ymin = bbox_ymax - leg_height

                # legend_xmin = bbox_xmin + (1 - 0.4)*(bbox_xmax - bbox_xmin)
                # legend_ymin = bbox_ymin + (1 - 0.4)*(bbox_ymax - bbox_ymin)
                legend_xmax, legend_ymax = bbox_xmax, bbox_ymax
                
                self.logger.debug('bbox == %s ' % bbox)


            plane = rs.WorldXYPlane()
            leg_frame = rs.AddRectangle( plane
                                        ,leg_width
                                        ,leg_height 
                                        )

            self.logger.debug('Rectangle width * height == '
                             +'%s * %s' % (leg_width, leg_height)
                             )


            rs.MoveObject(leg_frame, [1.07*bbox_xmax, legend_ymin])


        else:
            self.logger.info('No legend rectangle dimensions.  ')
            leg_frame = None

    


        self.logger.debug(leg_frame)


        gdm = GH_objs_to_recolour
        leg_cols = list(legend_tags.values())
        leg_tags = list(legend_tags.keys())  #both are used by smart component


        sc.doc =  ghdoc 
        sc.doc.Views.Redraw()

        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)
    
    retvals = 'gdm', 'leg_cols', 'leg_tags', 'leg_frame', 'opts'
    component_outputs = ('Geom', 'Data') + retvals[1:-1]
    param_infos = sDNA_GH_Tool.param_infos + (
                   ('leg_cols', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = 'Colour values for a legend.'
                            ))
                   ,('leg_tags', add_params.ParamInfo(
                             param_Class = Param_String
                            ,Description = 'Tag names, for a legend.'
                            ))
                   ,('leg_frame', add_params.ParamInfo(
                            Description = ('A Rectangle, suitable for a '
                                          +'legend frame.'
                                          )
                            )),
                                             )



class sDNA_GeneralDummyTool(sDNA_GH_Tool):

    component_inputs = ('tool',)

    def __call__(self, *args, **kwargs):
        raise NotImplementedError('this function should never run '
                                 +'(there is a problem with sDNA_General).'
                                 )
    component_outputs = ()


toml_no_tuples = options_manager.toml_types[:]
if tuple in toml_no_tuples:
    toml_no_tuples.remove(tuple)
#Internally in sDNA_GH opts, tuples are read only.

bare_key_chars = string.ascii_letters + string.digits + '_-' 
#https://toml.io/en/v1.0.0#keys



def parse_values_for_toml(x, supported_types = toml_no_tuples):
    #type(type[any]) -> type[any]
    """ Strips out keys and values for which the key is not a string 
        or contains whitespace, or for which the value is not a 
        supported type.  
    """
    if options_manager.isnamedtuple(x) and hasattr(x, '_asdict'):
        x = x._asdict()
    if isinstance(x, list):
        return [parse_values_for_toml(y, supported_types) 
                for y in x 
                if isinstance(y, tuple(supported_types))
               ]
    if isinstance(x, dict):
        return OrderedDict((key, parse_values_for_toml(val, supported_types)
                           ) 
                           for key, val in x.items() 
                           if (isinstance(key, basestring) 
                               and (options_manager.isnamedtuple(val) or 
                                    isinstance(val, tuple(supported_types))))
                          )
    return x



class ConfigManager(sDNA_GH_Tool):

    """ Updates opts objects, and loads and saves config.toml files.  

        All args connected to its input Params are loaded into opts,
        even if go is False.  

        If go is True, tries to save the options to the toml file in 
        save_to (needs to be a valid file path ending 
        in toml) overwriting an existing file, the installation-wide
        options file by default, or if specified by the user e.g. 
        creating a project specific options file.  
        
        Only string keyed str, bool, int, float, list, tuple, and dict 
        values in opts are saved to the toml file on disk.
    """


    class Metas(PythonOptions, sDNAMetaOptions):
        config = os.path.join(launcher.user_install_folder
                              ,launcher.package_name  
                              ,'config.toml'
                              )

    class Options(object):
        pass
    Options.save_to = Metas.config


    param_infos = sDNA_GH_Tool.param_infos + (
                   ('save_to', add_params.ParamInfo(
                             param_Class = Param_FilePath
                            ,Description = ('The field name / key value of '
                                           +'the results field to parse '
                                           +'and/or plot. Default: %(save_to)s'
                                           )
                            ))
                  ,('python', add_params.ParamInfo(
                             param_Class = Param_FilePath
                            ,Description = ('Maximum data value to parse. '
                                           +'Higher values (and their '
                                           +'objects) are omitted. '
                                           +'Automatically calculated if unset.'
                                           )
                            ))
                  ,('sDNA_paths', add_params.ParamInfo(
                             param_Class = Param_FilePath
                            ,Description = ('Minimum data value to parse. '
                                           +'Lower values (and their '
                                           +'objects) are omitted. '
                                           +'Automatically calculated if unset.'
                                           )
                            ))
                  ,('auto_get_Geom', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: Run Read Rhino geometry '
                                           +'before Read User Text.  ' 
                                           +"false: don't. "
                                           +'Default: %(auto_get_Geom)s' 
                                           )
                            )) 
                  ,('auto_read_User_Text', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: Run Read User Text before'
                                           +" Write shapefile.  false: don't. "
                                           +'Default: %(auto_read_User_Text)s' 
                                           )
                            )) 
                  ,('auto_write_Shp', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: Run Write shapefile before'
                                           +" sDNA tools.  false: don't. "
                                           +'Default: %(auto_write_Shp)s' 
                                           )
                            )) 
                  ,('auto_read_Shp', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: Run Read shapefile after'
                                           +" sDNA tools.  false: don't. "
                                           +'Default: %(auto_read_Shp)s' 
                                           )
                            )) 
                  ,('auto_plot_data', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: Run Recolour objects after'
                                           +" Read shapefile.  false: don't. "
                                           +'Default: %(auto_plot_data)s' 
                                           )
                            ))         
                  ,('show_all', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: show all possible input '
                                           +'Params on sDNA tools.  '
                                           +'false: only show required '
                                           +'Params. '
                                           +'Default: %(show_all)s' 
                                           )

                            ))                       

                                               )
    component_inputs = ('save_to' # Primary Meta
                       ,'python'
                       ,'sDNA_paths'
                       ,'auto_get_Geom' 
                       ,'auto_read_User_Text'
                       ,'auto_write_Shp'
                       ,'auto_read_Shp'
                       ,'auto_plot_data'
                       ,'show_all'
                       )

    def __call__(self, opts):
        self.debug('Starting class logger')

        metas = opts['metas']
        options = opts['options']
                
        python, sDNA_paths = metas.python, metas.sDNA_paths
        save_to = options.save_to

        self.debug('save_to : %s, python : %s, sDNA_paths : %s' 
                  % (save_to, python, sDNA_paths)
                  )


        if python:
            opts['metas'] = opts['metas']._replace(python = python)
            check_python(opts)
        if sDNA_paths:
            opts['metas'] = opts['metas']._replace(sDNA_paths = sDNA_paths)
            import_sDNA(opts)

        self.logger.debug('options == %s ' % options)

        # self.logger.debug('opts == %s' % '\n\n'.join(str(item) 
        #                                      for item in opts.items()
        #                                      )
        #           )


        parsed_dict = parse_values_for_toml(opts)   
        del parsed_dict['metas']['config'] # no nested options files

        if 'sDNA' in parsed_dict['metas']:
            del parsed_dict['metas']['sDNA'] # read only.  auto-updated.

        # self.logger.debug('parsed_dict == %s' % '\n\n'.join(str(item) 
        #                                              for item in parsed_dict.items()
        #                                             )
        #           )

        save_to = options.save_to

        if not isinstance(save_to, basestring):
            msg = 'File path to save to: %s needs to be a string' % save_to
            self.logger.error(msg)            
            raise TypeError(msg)
        if not save_to.endswith('.toml'):
            msg = 'File path to save to: %s needs to end in .toml' % save_to
            self.logger.error(msg)
            raise ValueError(msg)

        if save_to == self.Metas.config:
            self.logger.warning('Saving opts to installation wide '
                               +'file: %s' % save_to
                               )
            del parsed_dict['options']['path'] # no project-specific paths are
                                               # saved to the installation wide 
                                               # config file's options
            del parsed_dict['options']['working_folder']
            parsed_dict['options']['message'] = 'Installation wide user options file. '
        else:
            parsed_dict['options']['message'] = 'Project specific user options file. '

        options_manager.save_toml_file(save_to, parsed_dict)
        
        retcode = 0
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = ('retcode',)
    component_outputs = ()

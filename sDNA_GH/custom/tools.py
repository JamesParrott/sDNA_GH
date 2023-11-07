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
__version__ = '2.6.2'

import os
import sys
import abc
import logging
import functools
import subprocess
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
import Grasshopper
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
from .skel.tools.helpers import rhino_gh_geom
from .skel.tools import runner                                       
from .skel import add_params
from .skel import builder
from . import options_manager
from . import pyshp_wrapper
from . import logging_wrapper
from . import gdm_from_GH_Datatree
from .. import launcher


itertools = funcs.itertools #contains pairwise recipe if Python < 3.10
                            #and zip_longest if Python > 2


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

# def inst_of_all_in(module, parent = Grasshopper.Kernel.Parameters.IGH_TypeHint):
#     #type(str, Module) ->  list
#     return [getattr(module, cls)() 
#             for cls in dir(module) 
#             if issubclass(getattr(module, cls), parent)
#            ]

# from System.Collections.Generic import List

# TypeHintList = List[Grasshopper.Kernel.Parameters.IGH_TypeHint]

class sDNA_GH_Tool(runner.RunnableTool
                  ,add_params.ToolwithParamsABC
                  ,ClassLogger
                  ):

    """ General base class for all tools, that is runnable (should have
        retvals implemented), has params (input_params and output_params
        should be implemented), and containing a class logger that adds 
        the subclass name to logging messages. 
    """

    def __init__(self, opts):
        self.opts = opts

    def built_in_options(self, opts = None):
        if opts is None:
            opts = self.opts
        options, metas = opts['options'], opts['metas']
        retval = options._asdict()
        retval.update(metas._asdict())
        return retval


    def param_info_list(self, param_names, extras = None):
        interpolations = self.built_in_options()
        if extras is not None:
            interpolations.update(extras)
        return list_of_param_infos(param_names
                                  ,self.param_infos
                                  ,interpolations = interpolations 
                                  )

    def input_params(self, interpolations = None):
        return self.param_info_list(param_names = self.component_inputs
                                   ,extras = interpolations
                                   )

    def output_params(self, interpolations = None):
        return self.param_info_list(param_names = self.component_outputs
                                   ,extras = interpolations
                                   )

    @property
    @abstractmethod
    def component_inputs(self):
        """ Iterable of strings, the names of the input Params required on
           a component running this tool
        """

    @property
    @abstractmethod
    def component_outputs(self):
         """ Iterable of strings, the names of the output Params required on
             a component running this tool
         """

    # Can be both inputs and outputs
    # param_infos is a tuple of key/val pairs so sub classes and 
    # instances need only self.param_infos += tuple_of_extras.  It 
    # can later be made 
    # into a dictionary where needed.  This avoids making a 
    # copy of a list or dictionary for each subclass and 
    # each instance to avoid everything changing the parent 
    # class's variable, to separate concerns and support 
    # customisation.
    param_infos = (('file', add_params.ParamInfo(
                             param_Class = Param_FilePath
                            ,Description = 'File path of the shape file.'
                            ))                           
                   ,('Geom', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('A list of geometric objects. '
                                           +'Requires GUIDs of Rhino objects '
                                           +'or native/embedded Grasshopper '
                                           +'geometry. To use Rhino objects '
                                           +'referenced from '
                                           +'Grasshopper parameter objects '
                                           +'(instead of '
                                           +'their Grasshopper versions which '
                                           +'are often obscured unless the '
                                           +'Rhino shapes are set to Hidden) '
                                           +'run the output of the '
                                           +'Geometry (Geo) or Curve (Crv) '
                                           +'through a Guid (ID) parameter '
                                           +'object first. '
                                           +'Note: For sDNA tools all the '
                                           +'geometric objects must all be '
                                           +'polylines. For write_Shp all the '
                                           +'objects must be of the type in '
                                           +'shp_type (default: %(shp_type)s).'
                                           )
                            # ,Hints = TypeHintList(
                            #  (Grasshopper.Kernel.Parameters.Hints.GH_GuidHint()
                            #  ,GhPython.Component.GhDocGuidHint()
                            #  ))
                            # ,ShowHints = True
                            #,TypeHint = Grasshopper.Kernel.Parameters.Hints.GH_GuidHint()
                            #,Access = 'tree'
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
                            ,Description = ('Geometry and Data Mapping(s).  '
                                           +'Internal combination of Geom and '
                                           +'Data. Python Ordered Dictionary  '
                                           +'(or Iterable thereof) '
                                           +'mapping objects to their own '
                                           +'key/val data dictionary, keys '
                                           +'corresponding to User Text keys '
                                           +'or shape file field names. '
                                           )
                            ))   
                   ,('config', add_params.ParamInfo(
                             param_Class = Param_FilePath
                            ,Description = ('File path to sDNA_GH options '
                                           +'file. Default: %(config)s '
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
                   ,('sync', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('false: desynchronise from other '
                                           +"components' options.  true: "
                                           +'synchronise with other '
                                           +'synchronised components, sharing '
                                           +'the global sDNA_GH options. '
                                           +'Default: %(sync)s'
                                           )
                            )) 
                  )                     









            

def has_keywords(nick_name, keywords = ('prepare', 'integral')):
    return any(substr in nick_name.strip().strip('_').lower() 
              for substr in keywords
              )

sDNA_KEY_FORMAT = '{sDNAUISPec}_and_{runsdnacommand}' 
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
    sDNA = (os.path.splitext(metas.sDNAUISpec)[0]
           ,os.path.splitext(metas.runsdnacommand)[0]
           )
    return sDNA_KEY_FORMAT.format(sDNAUISPec = sDNA[0], runsdnacommand = sDNA[1])


def nested_set_default_or_get(d, keys, last_default = None):
    #type(dict, Sequence(Hashable), type[any])
    
    logger.debug('d == %s' % d)

    keys = list(keys)
    last_key = keys.pop()

    for key in keys:
        d = d.setdefault(key, OrderedDict())

    if last_default is None:
        d = d.get(last_key, None)
    else:
        d = d.setdefault(last_key, last_default)

    logger.debug('before return, d == %s' % (d,))

    return d

def get_tool_opts(opts, nick_name, tool_name = None, sDNA = None, val = None):
    #type(dict, str, str, str, type[any])
    # might mutate opts
    keys = (nick_name,)
    if tool_name is not None and tool_name != nick_name:
        keys += (tool_name,)
    if sDNA is not None:
        keys += (sDNA,)
    return nested_set_default_or_get(d = opts, keys = keys, last_default = val)

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
    python = '' #r'C:\Python27\python.exe'

python_options = options_manager.namedtuple_from_class(PythonOptions)


class MissingPythonError(Exception):
    pass


def check_python(opts):
    #type(dict) -> None 
    """ Searches opts['options'].python_paths, updating opts['options'].python 
        until it is a file.  
        
        Mutates: opts
        Returns: None
        
        Raises MissingPythonError if no valid file found.
    """

    options = opts['options']

    folders = options.python_paths
    pythons = options.python_exes

    if isinstance(folders, basestring):
        folders = [folders]

    if isinstance(pythons, basestring):
        pythons = [pythons]

    if (isinstance(options.python, basestring) 
        and os.path.isdir(options.python)):
        #
        folders = itertools.chain( (options.python,), folders)

    possible_pythons = (os.path.join(dirpath, python) 
                        for folder in folders 
                        for dirpath, __, __ in os.walk(folder)
                        for python in pythons
                        if isinstance(folder, basestring) and os.path.isdir(folder)
                       )

    for python in itertools.chain((opts['options'].python,), possible_pythons):
        if isinstance(python, basestring) and os.path.isfile(python):
            opts['options'] = opts['options']._replace(python = python)
            break  
    else:  # for/else, i.e. if the for loop wasn't left early by break
        msg = ('No Python interpreter file found.  Please specify a valid '
              +'python 2.7 interpreter or its parent folder in python '
              +', or a range of python interpreter names and folder names to '
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
    #type(dict, **kwargs) -> list, list, list
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

DEFAULT_METAS_NT = options_manager.namedtuple_from_class(Class = DefaultMetas
                                                        ,name = 'DEFAULT_METAS'
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
        msg = ('opts and override both need to be dictionaries. '
              +'depth == %s' % depth
              )
        logger.error(msg)
        raise TypeError(msg)
    logger.debug('current_opts.keys() == %s ' % current_opts.keys())
    logger.debug('override.keys() == %s ' % override.keys())

    if not kwargs:
        kwargs = {}
    metas = kwargs.setdefault('metas', current_opts.get('metas', DEFAULT_METAS_NT))
    if 'add_new_opts' in kwargs:
        metas = metas._replace(add_new_opts = kwargs['add_new_opts'])
    logger.debug('metas == %s' % (metas,))
                #,strict 
                #,check_types
                #,add_new_opts, for update_data_node and make_new_data_node
    kwargs.setdefault('max_depth', 2)
    kwargs.setdefault('specials', ('options', 'metas'))
    kwargs.setdefault('patterns', (funcs.make_regex(sDNA_KEY_FORMAT),))
    
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
        update_opts(current_opts.setdefault(key, OrderedDict()) 
                                                     # creates a new sub_dict
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


    requested_sDNA = (os.path.splitext(metas.sDNAUISpec)[0]
                     ,os.path.splitext(metas.runsdnacommand)[0] # remove .py s
                     )

    # To load new sDNA modules, specify the new module names in
    # metas.sDNAUISpec and metas.runsdnacommand

    # If they are loaded successfully the actual corresponding modules are
    # returned


    if requested_sDNA[0] in sys.modules and requested_sDNA[1] in sys.modules:
        sDNAUISpec = sys.modules[requested_sDNA[0]]
        run_sDNA = sys.modules[requested_sDNA[1]]
        logger.debug('sDNA: %s, %s already imported. ' % requested_sDNA)
        return sDNAUISpec, run_sDNA

    logger.info('Attempting import of sDNA '
               +'(sDNAUISpec == %s, runsdnacommand == %s)... ' % requested_sDNA
               )
    #
    # Import sDNAUISpec.py and runsdnacommand.py from metas.sDNA_paths
    if isinstance(metas.sDNA_paths, basestring):
        folders = [metas.sDNA_paths] 
    else:
        folders = metas.sDNA_paths

    for i, folder in enumerate(folders):
        if os.path.isfile(folder):
            folder = folders[i] = os.path.dirname(folder)
        if os.path.basename(folder) == 'bin':
            folders[i] = os.path.dirname(folder)

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

    logger.info('Successfully imported sDNA: '
               +'(sDNAUISpec == %s, runsdnacommand == %s)... ' % requested_sDNA
               )

    return sDNAUISpec, run_sDNA


sDNA_GH_user_objects_location = os.path.join(launcher.USER_INSTALLATION_FOLDER
                                            ,launcher.PACKAGE_NAME
                                            ,builder.ghuser_folder
                                            )


def build_sDNA_GH_components(**kwargs):
    #type(kwargs) -> list
    
    
    
    user_objects_location = kwargs.setdefault('user_objects_location'
                                             ,sDNA_GH_user_objects_location
                                             )

    sDNA_GH_path = user_objects_location
    while os.path.basename(sDNA_GH_path) != launcher.PACKAGE_NAME:
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

    sDNAUISpec, _ = import_sDNA(opts)
    # = opts['options'].sDNAUISpec

    user_objects_location = kwargs.setdefault('user_objects_location'
                                             ,sDNA_GH_user_objects_location  
                                             )

    def ghuser_file_path(name, folder = user_objects_location):
        #type(str)->str
        return os.path.join(folder, name + '.ghuser') 

    components_folders = (user_objects_location
                         ,sDNA_GH_user_objects_location
                         ,launcher.USER_INSTALLATION_FOLDER
                         )

    missing_tools = []
    names = []
    for Tool in sDNAUISpec.get_tools():
        default_names = [nick_name
                         for nick_name, tool_name in metas.DEFAULT_NAME_MAP.items()
                         if tool_name == Tool.__name__
                        ]
        names = default_names + [nick_name
                                 for nick_name, tool_name in metas.name_map.items()
                                 if tool_name == Tool.__name__
                                ]
        names.insert(0, Tool.__name__)
        if not any(os.path.isfile(ghuser_file_path(name, folder)) 
                   for name in names for folder in components_folders):
            #
            name_to_use = default_names[-1] if default_names else Tool.__name__
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




class sDNA_ToolWrapper(sDNA_GH_Tool):
    """ Main sDNA_GH tool class for running sDNA tools externally.
    
    In addition to the 
    other necessary attributes of sDNA_GH_Tool, instances know their own name
    and nick name, in self.nick_name
    self.tool_name.  When the instance is called, the version of sDNA
    is looked up in opts['metas'], from its args. 
    """
            
    sDNA = None

    sDNAUISpec = options_manager.error_raising_sentinel_factory(
                                                'No sDNA module: '
                                               +'sDNAUISpec loaded yet. '
                                               ,'Module is loaded from the '
                                               +'first files named in '
                                               +'metas.sDNAUISpec and '
                                               +'metas.runsdnacommand both '
                                               +'found in a path in '
                                               +'metas.sDNA_paths. '
                                               )
    run_sDNA = options_manager.error_raising_sentinel_factory(
                                                'No sDNA module: '
                                               +'run_sDNA loaded yet. '
                                               ,'Module is loaded from the '
                                               +'first files named in '
                                               +'metas.sDNAUISpec and '
                                               +'metas.runsdnacommand both '
                                               +'found in a path in '
                                               +'metas.sDNA_paths. '
                                               )

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

    class Metas(sDNAMetaOptions):
        show_all = True
        make_advanced = False

    class Options(PythonOptions
                 ,pyshp_wrapper.InputFileDeletionOptions
                 ,pyshp_wrapper.OutputFileDeletionOptions
                 ):
        prepped_fmt = "{name}_prepped"
        output_fmt = "{name}_output"
        overwrite_shp = pyshp_wrapper.ShpOptions.overwrite_shp
        # file extensions are actually optional in PyShp, 
        # but just to be safe and future proof
# Default installation path of Python 2.7.3 release (32 bit ?) 
# http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi copied from sDNA manual:
# https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/installation_usage.html 

    def get_tool_opts(self, opts, sDNA = None, val = None):
        if sDNA is None:
            sDNA = sDNA_key(opts) # opts requires 'metas'
        if val is None:
            val = self.default_named_tuples.get(sDNA, None)
        return get_tool_opts(opts = opts
                            ,nick_name = self.nick_name
                            ,tool_name = self.tool_name
                            ,sDNA = sDNA
                            ,val = val
                            )

    def built_in_options(self, opts = None):
        retval = super(sDNA_ToolWrapper, self).built_in_options(opts)
        for default_tool_options in self.default_named_tuples.values():
            retval.update(default_tool_options._asdict())
        return retval

    def already_loaded(self, opts, sDNA = None):
        if sDNA is None:
            sDNA = sDNA_key(opts)
        return (sDNA in self.get_syntaxes and 
                sDNA in self.default_named_tuples and
                self.get_tool_opts(opts, sDNA, val = None) is not None and
                sDNA in self.input_specs and
                (set(funcs.first_of_each(self.param_infos))
                       .issuperset(funcs.first_of_each(self.input_specs[sDNA]))
                )
               )

                

    def load_sDNA_tool(self, opts = None):
        if opts is None:
            opts = self.opts
        metas = opts['metas']
        nick_name = self.nick_name
        tool_name = self.tool_name

        check_python(opts)

        sDNAUISpec, run_sDNA = self.import_sDNA(opts, logger = self.logger)

        sDNA = sDNA_key(opts)

        if self.already_loaded(opts, sDNA):
            get_syntax = self.get_syntaxes[sDNA]
            defaults = self.default_named_tuples[sDNA]._asdict()
            return sDNAUISpec, run_sDNA, get_syntax, defaults
        self.logger.info('Loading sDNA info for tool: %s' % tool_name)
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
                            
        self.input_specs[sDNA] = input_spec = sDNA_Tool.getInputSpec()
        self.get_syntaxes[sDNA] = get_syntax = sDNA_Tool.getSyntax

        defaults = OrderedDict((tuple_[0], tuple_[4]) for tuple_ in input_spec)
                              
        # varname : default.  See below for other names in tuple_ in input_spec

        nt_name = '_'.join([nick_name, tool_name, sDNA])
        defaults_NT = options_manager.namedtuple_from_dict(d = defaults
                                                          ,NT_name = nt_name
                                                          )
        self.default_named_tuples[sDNA] = defaults_NT

        # self.get_tool_opts(opts = self.default_tool_opts
        #                   ,sDNA = sDNA
        #                   ,val = defaults_NT
        #                   )


        new_tool_opts = OrderedDict()
        # builds the tool opts structure in default_tool_opts,
        # using nested_set_default
        for new_opts in (self.default_tool_opts, new_tool_opts):
            self.get_tool_opts(opts = new_opts # mutated
                              ,sDNA = sDNA
                              ,val = defaults_NT
                              )
        # This feels weird, but minor repetition is a lot easier than a 
        # deep copy / clone.


        self.logger.debug('default_tool_opts == %s ' % self.default_tool_opts)

        update_opts(current_opts = new_tool_opts # mutated again
                   ,override = opts # in case opts for this tool were already
                                    # loaded from a file before its first 
                                    # component was first placed
                   ,add_new_opts = True
                   )
        #override new_tool_opts with opts


        opts.update(new_tool_opts)
        # get the updated opts back into opts, via .update (have to mutate
        # to cause an intentional lasting side effect, assignment will only 
        # affect the local name)

        for varname, display_name, data_type, filter_, default, required in input_spec:  
                      
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

        if metas.show_all:
            new_keys = tuple(key 
                             for key in defaults
                             if key not in self.component_inputs
                            )
            if new_keys:
                self.component_inputs += new_keys

            if 'advanced' not in defaults:
                msg = "'advanced' not in defaults_dict"
                self.logger.warning(msg)
                warnings.showwarning(message = msg
                    ,category = UserWarning
                    ,filename = __file__ + self.__class__.__name__
                    ,lineno = 253
                    )

        self.logger.debug('Params added to component_inputs for args '
                         +'in input spec:\n %s' 
                         %'\n'.join(OrderedDict(self.param_infos).keys())
                         )

        return sDNAUISpec, run_sDNA, get_syntax, defaults



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

        self.default_tool_opts = OrderedDict()
        self.default_named_tuples = OrderedDict()
        self.get_syntaxes = OrderedDict()
        self.input_specs = OrderedDict()

        #__, __, __, defaults = 
        
        self.load_sDNA_tool(opts)

        self.not_shared = ('input', 'output', 'advanced')
        

        if has_keywords(self.tool_name, keywords = ('prepare',)):
            self.retvals += ('gdm',)


    
    
    component_inputs = ('file', 'config') 


    def __call__(self # the tool instance not the GH component.
                ,f_name
                ,opts
                ,input = None
                ,output = None
                ,advanced = None
                ,**kwargs
                ):
        #type(str, dict, str, str, str, dict) -> int, str
        if opts is None:
            opts = self.opts

        sDNAUISpec, run_sDNA, get_syntax, __ = self.load_sDNA_tool(opts)

        if not hasattr(sDNAUISpec, self.tool_name): 
            msg = self.tool_name + 'not found in ' + sDNAUISpec.__name__
            self.logger.error(msg)
            raise ValueError(msg)

        options = opts['options']
        metas = opts['metas']

        sDNA = sDNA_key(opts)

        tool_opts_sDNA = self.get_tool_opts(opts, sDNA = sDNA)

        input_file = input # the builtin function input doesn't 
                           # work in a GhPython component and input is a
                           # method argument so there is no namespace issue

        

        if (isinstance(f_name, basestring) and os.path.isfile(f_name)
            and os.path.splitext(f_name)[1] in ['.shp','.dbf','.shx']):  
            input_file = f_name
        else:
            logger.debug('isinstance(f_name, basestring) == %s' % isinstance(f_name, basestring))
            logger.debug('os.path.isfile(f_name) == %s' % os.path.isfile(f_name))
            logger.debug('os.path.splitext(f_name)[1] == %s' % os.path.splitext(f_name)[1])

        self.logger.debug('input == %s, f_name == %s ' % (input_file, f_name))

        if not os.path.isfile(input_file):
            msg = 'input: "%s" is not a file. To run sDNA please set file or input '
            msg += 'to the path of a valid shape file. '
            msg %= input_file
            self.logger.error(msg)
            raise ValueError(msg)
         


        output_file = output 
        if not output_file:
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
                isinstance(options.INPUT_FILE_DELETER
                          ,pyshp_wrapper.ShapeFilesDeleter)):
                #
                maybe_delete = pyshp_wrapper.ShapeFilesDeleter(output_file)
                opts['options'] = opts['options']._replace(
                                            OUTPUT_FILE_DELETER = maybe_delete
                                            )
        else:
            output = ''  # returned, to stop subsequent sDNA components 
                         # using the same name and overwriting it.

        tool_opts = tool_opts_sDNA._asdict()
        tool_opts.update(input = input_file, output = output_file)

        f_name = output_file # File name to be outputted
        input = input_file # Can be safely returned for informational
                           # purposes as the f_name/file 
                           # just defined will take priority in a 
                           # subsequent second sDNA tool.

        LIST_ARGS = ('radius'
                    ,'radii'
                    ,'preserve_absolute'
                    ,'preserve_unitlength'
                    ,'origins'
                    ,'destinations'
                    ,'predictors'
                    ,'reglambda'
                    )

        for key, val in tool_opts.items():
            if key in LIST_ARGS and isinstance(val, list) and len(val) >= 2:
                tool_opts[key] = ','.join(str(element) for element in val)
                self.logger.info('Converted list to str: %s' % tool_opts[key])

        if 'advanced' in tool_opts:
            if advanced is None:
                advanced = tool_opts['advanced']
            if metas.make_advanced and not advanced:
                user_inputs = self.component.params_adder.user_inputs
                # We need this reference because some args this tool doesn't 
                # recognise, may have been added to the component, by another
                # tool on it.

                self.logger.debug('user_inputs == %s' % user_inputs)
                self.logger.debug('needed_inputs == %s' 
                                % self.component.params_adder.needed_inputs
                                )
                advanced = ';'.join(key if val is None else '%s=%s' % (key, val)
                                    for key, val in kwargs.items()
                                    if (key in user_inputs and 
                                        key not in self.built_in_options(opts)
                                    )
                                )
                tool_opts['advanced'] = advanced
                self.logger.info('Built advanced config string: %s' % advanced)

            else:
                self.logger.debug('Advanced config string: %s' % advanced)

            # user needs to set sync = false to avoid sharing advanced.
            all_sDNA_tool_opts = get_tool_opts(opts
                                              ,nick_name = self.nick_name
                                              ,tool_name = self.tool_name
                                              ,sDNA = None
                                              ,val = None
                                              )
            all_sDNA_tool_opts[sDNA] = tool_opts_sDNA._replace(advanced = advanced)


        syntax = get_syntax(tool_opts)

        command = (options.python
                  +' -u ' 
                  +'"' 
                  +os.path.join(os.path.dirname(sDNAUISpec.__file__)
                               ,'bin'
                               ,syntax['command'] + '.py'  
                               ) 
                  +'"'
                  +' --im ' + run_sDNA.map_to_string(syntax["inputs"])
                  +' --om ' + run_sDNA.map_to_string(syntax["outputs"])
                  +' ' + syntax["config"]
                  )
        self.logger.info('sDNA command run: %s' % command)

        output_lines = ''

        try:
            output_lines = subprocess.check_output(command)
            retcode = 0 
        except subprocess.CalledProcessError as e:
            self.logger.info(output_lines)
            self.logger.error('error.output: %s' % e.output)
            self.logger.error('error.returncode: %s' % e.returncode)
            raise e


        self.logger.info(output_lines)


        # Does not execute if subprocess raises an Exception
        if (options.del_after_sDNA and 
            not options.strict_no_del and 
            not options.overwrite_shp and 
            isinstance(options.INPUT_FILE_DELETER
                      ,pyshp_wrapper.ShapeFilesDeleter) and
            hasattr(options.INPUT_FILE_DELETER, 'delete_files')):
            #
            options.INPUT_FILE_DELETER.delete_files(
                                                delete = options.del_after_sDNA
                                               ,opts = opts
                                               )
            opts['options'] = opts['options']._replace(INPUT_FILE_DELETER = None)


        if has_keywords(self.tool_name, keywords = ('prepare',)):
            gdm = None
            # To overwrite any inputted gdm (already used) in vals_dict
            # to make sure a subsequent ShapefileReader adds new Geometry
            #
            # TODO add in names of other tools that change the network


        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    
    retvals = 'retcode', 'f_name', 'input', 'output', 'advanced'
    component_outputs = ('file',) # retvals[-1])


def get_objs_and_OrderedDicts(only_selected = False
                             ,layers = ()
                             ,shp_type = 'POLYLINEZ'
                             ,all_objs_getter = rhino_gh_geom.get_Rhino_objs
                             ,OrderedDict_getter = lambda *args : OrderedDict()
                             ,is_shape = rhino_gh_geom.is_shape
                             ,is_selected = gdm_from_GH_Datatree.is_selected
                             ,obj_layer = gdm_from_GH_Datatree.obj_layer
                             ,doc_layers = gdm_from_GH_Datatree.doc_layers
                             ):
    #type(bool, tuple, str, bool, function, function, function, function, 
    #                             function, function, function) -> function
    """ Generator for creating GDMs of Rhino geometry.  
    
        Use with sc.doc = Rhino.RhinoDoc.ActiveDoc 
    """
    if layers and isinstance(layers, basestring):
        layers = (layers,) if layers in doc_layers() else None




    #type( type[any]) -> list, list
    #

    objs = all_objs_getter(shp_type) # Note!:  may include non-polylines, 
                                     # arcs etc. for geometry_type = 4
                                     # e.g. rs.ObjectsByType(geometry_type = 4
                                     #                      ,select = False
                                     #                      ,state = 0
                                     #                      )


    for obj in objs:
        if not is_shape(obj, shp_type):                                                 
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



class RhinoObjectsReader(sDNA_GH_Tool):

    class Options(object):
        selected = False
        layer = ''
        shp_type = 'POLYLINEZ'
        merge_subdicts = True


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
        user_gdms = gdm if gdm else [gdm_from_GH_Datatree.GeomDataMapping()]

        if isinstance(user_gdms, gdm_from_GH_Datatree.GeomDataMapping):
            user_gdms = [gdm_from_GH_Datatree.GeomDataMapping()]

        self.logger.debug('options.selected == %s' % options.selected)
        self.logger.debug('options.layer == %s' % options.layer)
        
        doc_layers = gdm_from_GH_Datatree.doc_layers

        gdm = gdm_from_GH_Datatree.GeomDataMapping(
                    get_objs_and_OrderedDicts(only_selected = options.selected
                                             ,layers = options.layer
                                             ,shp_type = options.shp_type
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

        for sub_gdm in user_gdms:
            if sub_gdm:
                self.logger.debug('Overriding provided gdm. ')
                gdm = gdm_from_GH_Datatree.override_gdm(gdm
                                                       ,sub_gdm
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
        self.logger.debug('type(gdm) == %s'  % type(gdm))
        self.logger.debug('retvals == %s ' % (self.retvals,))
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)


    retvals = ('gdm',)
    component_outputs = ('Geom', ) 


class UsertextReader(sDNA_GH_Tool):

    class Options(object):
        compute_vals = True

    param_infos = sDNA_GH_Tool.param_infos + (
                   ('compute_vals', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true : apply '
                                           +'Rhino.RhinoApp.ParseTextField to '
                                           +'vals that are attribute User Text'
                                           +' computed fields. '
                                           +'false: do nothing. '
                                           +'Default: %(compute_vals)s'
                                           )
                            )),

                                              )

    component_inputs = ('Geom', 'compute_vals') 

    def __call__(self, gdm, opts = None):
        #type(str, dict, dict) -> int, str, dict, list

        options = self.Options if opts is None else opts['options']

        self.debug('Starting read_Usertext...  Creating Class logger. ')
        self.logger.debug('type(gdm) == %s ' % type(gdm))
        
        if not gdm:
            msg = 'No Geometric objects to read User Text from, gdm == %s' % gdm
            self.logger.error(msg)
            raise ValueError(msg)

        if isinstance(gdm, gdm_from_GH_Datatree.GeomDataMapping):
            self.logger.debug('gdm[:3] == %s ' % {key : gdm[key] for key in gdm.keys()[:3]} )
            gdm = [gdm]
        
        gdm = [sub_gdm.copy() for sub_gdm in gdm]

        sc.doc = Rhino.RhinoDoc.ActiveDoc
        for sub_gdm in gdm:
            for obj in sub_gdm:
                try:
                    keys = rs.GetUserText(obj)
                except ValueError:
                    keys =[]
                for key in keys:
                    val = rs.GetUserText(obj, key)

                    # Expand/parse computed vals like:
                    #  %<CurveLength("ac4669e5-53a6-4c2b-9080-bbc67129d93e")>%
                    if (options.compute_vals and 
                        val.startswith(r'%') and val.endswith(r'%') and
                        re.search(funcs.uuid_pattern, val)):
                        #
                        coerced_obj = rs.coercerhinoobject(obj)
                        val = Rhino.RhinoApp.ParseTextField(val, coerced_obj, None)


                    sub_gdm[obj][key] = val

        # read_Usertext_as_tuples = checkers.OrderedDict_from_User_Text_factory()
        # for obj in gdm:
        #     gdm[obj].update(read_Usertext_as_tuples(obj))


        sc.doc = ghdoc  
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)


    retvals = ('gdm',)
    component_outputs = ('Data', ) 



   


class ShapefileWriter(sDNA_GH_Tool):

    class Options(pyshp_wrapper.InputFileDeletionOptions
                 ,pyshp_wrapper.ShpOptions
                 ):
        shp_type = 'POLYLINEZ'
        input_key_str = '{name}'
        path = __file__
        output_shp = '' 
        prj = ''


    param_infos = sDNA_GH_Tool.param_infos + (
                                ('prj'
                                 ,add_params.ParamInfo(
                                  param_Class = Param_String
                                 ,Description = ('File path of the projection '
                                                +'file (.prj) to use for the '
                                                +'new shapefile. '
                                                +'Default : %(prj)s'
                                                )
                                 )
                                ),
                                ('input_key_str'
                                 ,add_params.ParamInfo(
                                  param_Class = Param_String
                                 ,Description = ('Format string containing a '
                                                +r'prefix, a {name} field, '
                                                +'and a postfix, to enable '
                                                +'more descriptive User Text '
                                                +'key names. '
                                                +'Default: %(input_key_str)s  '
                                                +'Only User Text key names '
                                                +'matching this pattern will '
                                                +' have their values written '
                                                +'to shape files by Write_Shp,'
                                                +'under the field name in '
                                                +r'{name}, which can have a '
                                                +'max of 10 chars in '
                                                +'Write_Shp. The actual '
                                                +' values of name in User Text'
                                                +' keys must also be '
                                                +' specified to the sDNA tools'
                                                +' that use them.'     
                                                )
                                 )
                                ),
                                             ) 


    

    component_inputs = ('Geom', 'Data', 'file', 'prj', 'input_key_str', 'config') 

    def __call__(self, f_name, gdm, opts = None):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts
        options = opts['options']
        self.debug('Creating Class Logger.  ')

        self.logger.debug('gdm == %s' % gdm)
        shp_type = options.shp_type            


        format_string = options.input_key_str
        pattern = funcs.make_regex( format_string )

        def pattern_match_key_names(x):
            #type: (str)-> object #re.MatchObject

            return re.match(pattern, x) 

        def get_list_of_points_from_obj(obj):
            #type: (type[any]) -> list

            if not rhino_gh_geom.is_shape(obj, shp_type):
                msg = 'Shape: %s cannot be converted to shp_type: %s' 
                msg %= (obj, shp_type)
                self.logger.error(msg)
                raise TypeError(msg)

            geom, __ = rhino_gh_geom.get_geom_and_source_else_leave(obj)

            # if hasattr(Rhino.Geometry, type(obj).__name__):
            #     geom = obj
            # else:
            #     obj = System.Guid(str(obj))
            #     geom = Rhino.RhinoDoc.ActiveDoc.Objects.FindGeometry(obj)
            #     if not geom:
            #         geom = ghdoc.Objects.FindGeometry(obj)



            points = rhino_gh_geom.get_points_from_obj(geom, shp_type)

            if not points:
                return []

            return [list(point) for point in points]

        def get_list_of_list_of_pts_from_obj(obj):
            #type: (list) -> list
            return [get_list_of_points_from_obj(obj)]



        if isinstance(gdm, Iterable) and not isinstance(gdm, gdm_from_GH_Datatree.GeomDataMapping):
            cached_gdms = [] # to cache lazy iterators
            all_items_are_gdms = True
            for item in gdm:
                cached_gdms.append(item) 
                if not isinstance(item, gdm_from_GH_Datatree.GeomDataMapping):
                    all_items_are_gdms = False
                

            if cached_gdms and all_items_are_gdms:
                #
                # combine all objects into one dict - sDNA requires single 
                # polyline links
                #


                all_keys_and_vals = ((key, val) 
                                    for sub_gdm in cached_gdms 
                                    for key, val in sub_gdm.items()
                                    )
                gdm = gdm_from_GH_Datatree.GeomDataMapping(all_keys_and_vals)
            else:
                gdm = cached_gdms

        if not gdm:
            msg = 'No geometry and no data to write to shapefile, gdm == %s' % gdm
            self.logger.error(msg)
            raise ValueError(msg)
            
        if not isinstance(gdm, gdm_from_GH_Datatree.GeomDataMapping):
            msg = ('Geometry or Data in unsupported format. type(gdm) == %s '
                  +'provided, not a GeomDataMapping. gdm == %s' 
                  )
            msg %= (type(gdm), gdm)
            self.logger.error(msg)
            raise TypeError(msg)

        # bad_shapes = [obj for obj in gdm if not rhino_gh_geom.is_shape(obj, shp_type)]
        bad_shapes = collections.defaultdict(list)
        for obj in gdm:
            if rhino_gh_geom.is_shape(obj, shp_type):
                continue
            geom, source = get_geom_and_source_else_leave(obj)
    
            bad_shapes[(type(obj).__name__, type(geom).__name__)].append(obj)
    


        if bad_shapes:
            msg = 'Shape(s): %s cannot be converted to shp_type: %s' 
            msg %= ('\n'.join('# of (Obj type: %s, geom_type: %s) : %s' % (k + (v,))
                              for k, v in bad_shapes.items()
                             )           
                   ,shp_type
                   )
            self.logger.error(msg)

            raise TypeError(msg)
        else:
            self.logger.debug('Points for obj 0: %s ' 
                                % get_list_of_list_of_pts_from_obj(gdm.keys()[0]) 
                                )

        def shape_IDer(obj):
            return obj #tupl[0].ToString() # uuid

        def find_keys(obj):
            return gdm[obj].keys() #tupl[1].keys() #rs.GetUserText(x,None)

        def get_data_item(obj, key):
            return gdm[obj][key] #tupl[1][key]

        if not f_name:  
            f_name = options.output_shp

        if (not isinstance(f_name, basestring) or 
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
                maybe_delete = pyshp_wrapper.ShapeFilesDeleter(f_name)
                opts['options'] = opts['options']._replace(
                                            INPUT_FILE_DELETER = maybe_delete
                                            )
            else:
                do_not_delete = pyshp_wrapper.NullDeleter() 
                                              # Slight hack, so sDNA_tool knows
                                              # f_name (input_file) is 
                                              # auto-generated, so it can tell 
                                              # if output_file is also
                                              # auto-generated, and only if so
                                              # maybe making a 
                                              # ShapeFilesDeleter for it.
                opts['options'] = opts['options']._replace(
                                            INPUT_FILE_DELETER = do_not_delete
                                            )

        self.logger.debug('f_name == %s' % f_name)



        retcode, f_name, fields, gdm = pyshp_wrapper.write_iterable_to_shp(
                                             my_iterable = gdm
                                            ,shp_file_path = f_name
                                            ,is_shape = rhino_gh_geom.is_shape
                                            ,shape_mangler = get_list_of_list_of_pts_from_obj 
                                            ,shape_IDer = shape_IDer
                                            ,key_finder = find_keys 
                                            ,key_matcher = pattern_match_key_names 
                                            ,value_demangler = get_data_item 
                                            ,shape_code = shp_type 
                                            ,options = options
                                            ,field_names = None
                                            ,AttributeTablesClass = gdm_from_GH_Datatree.GeomDataMapping
                                            )
        
        prj = options.prj

        if (isinstance(prj, basestring) and 
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
               



class ShapefileReaderAddShapeError(Exception):
    pass




class ShapefileReader(sDNA_GH_Tool):

    class Options(pyshp_wrapper.ShapeRecordsOptions):
        new_geom = False
        bake = False
        uuid_field = 'Rhino3D_'
        sDNA_names_fmt = '{name}.shp.names.csv'
        prepped_fmt = '{name}_prepped'
        output_fmt = '{name}_output'
        ensure_3D = True
        ignore_invalid = False
                        
    component_inputs = ('file', 'Geom', 'bake', 'ignore_invalid') 
                                                # existing 'Geom', otherwise new 
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


        self.logger.debug('Reading shapefile meta data... ')
        shp_fields, bbox, shape_type, num_entries = pyshp_wrapper.shp_meta_data(
                                                                         f_name
                                                                        ,options
                                                                        )

        self.logger.debug('bbox == %s' % bbox)

        invalid = []
        objs_maker = rhino_gh_geom.obj_maker_for_shape_type(shape_type)
        invalid_obj_handler = rhino_gh_geom.Rhino_obj_adder_invalid_handlers.get(
                                                                        shape_type
                                                                       ,None
                                                                       )

        if num_entries == 0:
            self.logger.warning('No entries in Shapefile: %s ' % f_name)
            return 1, f_name, gdm, None    


        if not bbox:
            self.logger.warning('No Bounding Box in Shapefile: %s '
                               % f_name
                               +'Supply bbox manually or create '
                               +'rectangle to plot legend.'
                               )

        fields = [ x[0] for x in shp_fields ]

        self.logger.debug('options.uuid_field in fields == ' 
                         +str(options.uuid_field in fields)
                         )
        self.logger.debug(fields) 

        if hasattr(options, 'field') and options.field not in fields:
            msg = 'field: %s not found in shape file fields: %s \n\n' 
            msg %= (options.field, fields)
            msg += 'Before using Parse_Data or Recolour_Objects on Data, '
            msg += 'set field to one of the shape file fields. '
            
            self.logger.warning(msg)
            warnings.warn(msg)

        self.logger.debug('Testing existing geom data map.... ')

        if (isinstance(gdm, Iterable) and len(gdm) == 1 and 
            isinstance(gdm[0], gdm_from_GH_Datatree.GeomDataMapping)):
                #
                gdm = gdm[0]

        if isinstance(gdm, gdm_from_GH_Datatree.GeomDataMapping):

            self.logger.debug('gdm == %s, ..., %s ' % (gdm.items()[:2], gdm.items()[-2:]))

            existing_geom_compatible = len(gdm) == num_entries
        else:
            existing_geom_compatible = False
            msg = 'Shape file is incompatible with existing gdm: %s' % str(gdm)[:50]
            logger.debug(msg)


        if options.new_geom or not existing_geom_compatible: 
            #shapes_to_output = ([shp.points] for shp in shapes )
            
            #e.g. rs.AddPolyline for shp_type = 'POLYLINEZ'

            if options.ensure_3D:
                objs_maker = funcs.compose(objs_maker, funcs.ensure_3D)

            if options.bake:
                objs_maker = funcs.compose(str, objs_maker)

            self.shape_num = 0

            def get_points(obj, *args):
                return funcs.list_of_lists(obj)

            def add_geom(points, obj, *args):
                self.shape_num += 1
                return (objs_maker(points),) + args

            def add_geom_from_obj(obj, *args):
                points = get_points(obj, *args)
                return add_geom(points, obj, *args)

            error_msg = ('The error: {{ %s }}  occurred '
                        +'when adding shape number: %s.'
                        )

            def added_geom_generator(group):
                for x in group:
                          # obj, *data = x 
                    points = get_points(*x)
                    try:
                        yield add_geom(points, *x)
                    except Exception as e:
                        # The error of interest inside rhinoscriptsyntax.AddPolyline comes from:
                        #
                        # if rc==System.Guid.Empty: raise Exception("Unable to add polyline to document")
                        # https://github.com/mcneel/rhinoscriptsyntax/blob/c49bd0bf24c2513bdcb84d1bf307144489600fd9/Scripts/rhinoscript/curve.py#L563


                        if invalid_obj_handler:
                            why_invalid = invalid_obj_handler(points, self.shape_num, e)
                        else:
                            why_invalid =  error_msg % (e, self.shape_num)

                        invalid.append(why_invalid)




            def gdm_of_new_geom_from_group(group):
                return gdm_from_GH_Datatree.GeomDataMapping(
                                                added_geom_generator(group))



            gdm_iterator = (gdm_of_new_geom_from_group(group) 
                            for group in pyshp_wrapper
                                          .TmpFileDeletingShapeRecordsIterator(
                                                                 reader = f_name
                                                                ,opts = opts
                                                                )
                            )

            gdm_partial = functools.partial(list, gdm_iterator)
                    
            # gdm = gdm_from_GH_Datatree.make_list_of_gdms(generator())
            #self.logger.debug('shapes == %s' % shapes)
            self.logger.debug('objs_maker == %s' % objs_maker)
        else:
            #elif isinstance(gdm, dict) and len(gdm) == len(recs):
            # an override for different number of overridden geom objects
            # to shapes/recs opens a large a can of worms.  Unsupported.

            self.logger.warning('Geom data map matches shapefile. Using existing Geom. ')

            gdm_iterator = itertools.zip_longest( # instead of izip to raise 
                                                  # StopIteration in
                                                  # TmpFileDeletingRecordsIterator
                     gdm.keys()
                    ,pyshp_wrapper.TmpFileDeletingRecordsIterator(reader = f_name
                                                                 ,opts = opts
                                                                 )
                    )
            
            gdm_partial = functools.partial(gdm_from_GH_Datatree.GeomDataMapping
                                           ,gdm_iterator
                                           )
            #                  dict.keys() is a dict view in Python 3


        # shp_file_gen_exp  = itertools.izip(shapes_to_output
        #                                   ,(rec.as_dict() for rec in recs)
        #                                   )

        if options.bake:
            sc.doc = Rhino.RhinoDoc.ActiveDoc
        gdm = gdm_partial()
        # Exhausts the above generator into a list
        sc.doc = ghdoc 
        
        if invalid:
            invalid = '\n %s \n\n' % invalid
            if options.ignore_invalid:
                logger.warning(invalid)
            else:
                logger.error(invalid)
                raise ShapefileReaderAddShapeError(invalid)

        self.logger.debug('gdm defined.  sc.doc == ghdoc.  ')

        file_name = os.path.splitext(f_name)[0]
        csv_f_name = options.sDNA_names_fmt.format(name = file_name)
        self.logger.debug('Looking for csv_f_name == %s ' % csv_f_name)

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



        retcode = 0

        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)


    retvals = 'retcode', 'gdm', 'abbrevs', 'fields', 'bbox', 'invalid'
    component_outputs = ('Geom', 'Data') + retvals[2:]

    param_infos = sDNA_GH_Tool.param_infos + (
            ('bake', add_params.ParamInfo(
                           param_Class = Param_Boolean
                          ,Description = ('If new shapes are created, then'
                                         +'true: bakes '
                                         +'the shapefile polylines to Rhino.  '
                                         +'false: creates Grasshopper '
                                         +'polylines only. '
                                         +'Default: %(bake)s'
                                         )
                          ))
            ,('new_geom', add_params.ParamInfo(
                           param_Class = Param_Boolean
                          ,Description = ('True: Always create new shapes. '
                                         +'False: Create new shapes only if '
                                         +'the number of supplied shapes does '
                                         +'not match the number of data '
                                         +'records in the shape file. '
                                         +'Default: %(new_geom)s'
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
            ,('ignore_invalid', add_params.ParamInfo(
                     param_Class = Param_Boolean
                    ,Description = ('True: suppress errors from failing '
                                   +'to add shapes to Rhino/GH document.  '
                                   +'False: skip shapes that could not be '
                                   +'added to the document. '
                                   +'Default: %(ignore_invalid)s  '
                                   +'If True, the reasons why those shapes are '
                                   +'incompatible with Rhino '
                                   +'are viewable in *invalid*, but they are also logged '
                                   +' as warnings (or errors if False) to *out* and any *log_file* '
                                   +'Five validity criteria are defined here:'
                                   +rhino_gh_geom.InvalidPolyline.rhino_url
                                   )
                    ))
            ,('invalid', add_params.ParamInfo(
                             param_Class = Param_String
                            ,Description = ('Duplicates specific console output in out. '
                                           +'Details why particular shapes (if any) in the shapefile '
                                           +'could not be added to a document in Rhino, raising errors.  '
                                           +'ignore_invalid (currently: %(ignore_invalid)s) must be True '
                                           +'to read invalid, to suppress those same errors '
                                           +'(errors stop this and all output Params '
                                           +'from receiving data). '
                                           )
                            ))       
            )


class UsertextWriterOptions(object):
    uuid_field = 'Rhino3D_'
    output_key_str = 'sDNA output={name} run time={datetime}'
    overwrite_UserText = True
    max_new_keys = 10
    dupe_key_suffix = '_{}'
    suppress_overwrite_warning = False
    suppress_write_failure_error = True

def write_dict_to_UserText_on_Rhino_obj(d
                                       ,rhino_obj
                                       ,time_stamp
                                       ,logger = logger
                                       ,options = None
                                       ):
    #type(dict, str, str, logging.Logger, Options | namedtuple) -> None
    
    if sc.doc == ghdoc:
        msg = 'Ensure sc.doc == %s is a Rhino Document before calling ' % sc.doc
        msg += 'this function.  '
        msg += 'Writing User Text to GH objects is not supported.'
        logger.error(msg)
        raise NotImplementedError(msg)

    if not isinstance(d, dict):
        msg = 'dict required by write_dict_to_UserText_on_Rhino_obj, got: %s, of type: %s'
        msg %= (d, type(d))
        logger.error(msg)
        raise TypeError(msg)
    
    if options is None:
        options = UsertextWriterOptions
    
    #if is_an_obj_in_GH_or_Rhino(rhino_obj):
        # Checker switches GH/ Rhino context
            
    existing_keys = rs.GetUserText(rhino_obj)
    if options.uuid_field in d:
        obj = d.pop( options.uuid_field )
    
    for key in d:

        s = options.output_key_str
        UserText_key_name = s.format(name = key
                                    ,datetime = time_stamp
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
                logger.warning( "UserText key == " 
                            + UserText_key_name 
                            +" overwritten on object with guid " 
                            + str(rhino_obj)
                            )

        rs.SetUserText(rhino_obj, UserText_key_name, str( d[key] ), False)          



class UsertextWriter(sDNA_GH_Tool):

    Options = UsertextWriterOptions

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

        if isinstance(gdm, gdm_from_GH_Datatree.GeomDataMapping):
            gdm = [gdm]

        if all(not value for sub_gdm in gdm for value in sub_gdm.values()):
            msg = 'No Data to write as User Text. '
            msg += 'Please connect data tree to Data. '
            msg += ' gdm == %s' % gdm
            self.logger.error(msg)
            raise ValueError(msg)




        sc.doc = Rhino.RhinoDoc.ActiveDoc
        for sub_gdm in gdm:
            for key, val in sub_gdm.items():
                try:
                    write_dict_to_UserText_on_Rhino_obj(
                                                 d = val
                                                ,rhino_obj = key
                                                ,time_stamp = date_time_of_run
                                                ,logger = self.logger
                                                ,options = options
                                                )
                except ValueError as e: # Tested when rs.SetUserText fails
                    msg = 'Writing dict: %s as User Text to obj: %s failed '
                    msg %= (val, key)
                    msg += 'with error message: %s ' % e.message
                    msg += 'and args: %s' % e.args
                    logger.error(msg)
                    if options.suppress_write_failure_error:
                        warnings.warn(msg)
                    else:
                        raise e

        sc.doc = ghdoc  
        
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)
    
    retvals = ()
    component_outputs = () 



QUANTILE_METHODS = dict(simple = data_cruncher.simple_quantile
                       ,max_deltas = data_cruncher.class_bounds_at_max_deltas
                       ,adjuster = data_cruncher.quantile_l_to_r
                       ,quantile = data_cruncher.spike_isolating_quantile
                       )


def search_for_field(fields, prefix):
    #type: Iterable[str], str -> str
    first = None
    first_that_is_not_id = None

    for k in fields:

        if k.startswith(prefix):
            return k
        
        if first is None:
            first = k

        if (first_that_is_not_id is None and 
            k.lower() != 'id'):
            first_that_is_not_id = k
        

    return first_that_is_not_id or first


class DataParser(sDNA_GH_Tool):

    class Options(data_cruncher.SpikeIsolatingQuantileOptions):
        field = None
        field_prefix = 'BtE'
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
        inter_class_bounds = [options_manager.Sentinel('inter_class_bounds is automatically '
                                                +'calculated by sDNA_GH unless '
                                                +'overridden.  '
                                                )
                       ]
        # e.g. [2000000, 4000000, 6000000, 8000000, 10000000, 12000000]
        class_spacing = 'quantile'
        VALID_CLASS_SPACINGS = data_cruncher.VALID_RE_NORMALISERS + tuple(QUANTILE_METHODS.keys())

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
        
        assert re_normaliser in data_cruncher.VALID_RE_NORMALISERS
        assert class_spacing in VALID_CLASS_SPACINGS
                        
    param_infos = sDNA_GH_Tool.param_infos + (
                   ('field', add_params.ParamInfo(
                             param_Class = Param_String
                            ,Description = ('The field name / key value of '
                                           +'the results field to parse '
                                           +'or plot. Default: %(field)s'
                                           )
                            ))
                  ,('field_prefix', add_params.ParamInfo(
                             param_Class = Param_String
                            ,Description = ('If "field" is not set, the field names / key value of '
                                           +'the results field are searched for the first one '
                                           +'that starts with field_prefix.\n ' 
                                           +'WARNING: without care, this may allow unfair comparisons 
                                           +'and incorrect conclusions to be drawn between '
                                           +'different result sets. The search may return BtE10 '
                                           +'on one component, and BtE10000000 on another (the two '
                                           +'can be very different Network measures).\n '
                                           +'If found, this field is parsed or plotted. '
                                           +'and outputted in "field". Default: %(field_prefix)s'
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
                                           +'Allowed Values: '
                                           +'%(VALID_CLASS_SPACINGS)s.  ' 
                                           +'Default: %(class_spacing)s'
                                           ) 
                            ))
                  ,('inter_class_bounds', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('Inter-class boundaries for the '
                                           +'legend. '
                                           +'Automatically calculated using '
                                           +'the method in class_spacing if '
                                           +'unset.'
                                           )
                            ))
                  ,('mid_points', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('Mid-points of the classes in the '
                                           +'legend. '
                                           )
                            ))
                                               )

    component_inputs = ('Geom', 'Data', 'field', 'field_prefix', 'plot_max', 'plot_min' 
                       ,'num_classes', 'class_spacing', 'inter_class_bounds'
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

        if not gdm:
            msg = 'No Geom. Parser requires Geom to preserve correspondence '
            msg += 'if the Data is re-ordered. '
            msg += 'Connect list of objects to Geom. '
            msg += ' gdm == %s' % gdm
            self.logger.error(msg)
            raise ValueError(msg)

        if isinstance(gdm, gdm_from_GH_Datatree.GeomDataMapping):
            gdm = [gdm]

        if options.field is None:

            all_fields = (k
                          for sub_gdm in gdm
                          for dict_ in sub_gdm.values()
                          for k in dict_
                         )
            field = search_for_field(all_fields, options.field_prefix)
        else:
            field = options.field

        def select(val, field):
            #type( type[any], str) -> Number
            if isinstance(val, Number):
                return val
            if not isinstance(val, dict):
                msg = 'val: %s is not a dict or a Number (type(val) == %s)' 
                msg %= (val, type(val))
                self.logger.error(msg)
                raise TypeError(msg)
            if field not in val:
                msg = 'Key for field: %s not found in val: %s' % (field, val)
                self.logger.error(msg)
                raise KeyError(msg)
            return val[field]

        plot_min, plot_max = options.plot_min, options.plot_max
        if data_cruncher.max_and_min_are_valid(plot_max, plot_min):
            #
            self.logger.info('Valid max and min override will be used. ')
            #
            x_min, x_max = plot_min, plot_max 
            if options.exclude:
                data = OrderedDict( (obj, val[field]) 
                                    for sub_gdm in gdm
                                    for obj, val in sub_gdm.items()                                    
                                    if x_min <= select(val, field) <= x_max
                                  )
            else: # exclude == False => enforce bounds, cap and collar
                data = OrderedDict( (obj, min(x_max, max(x_min, select(val, field)))) 
                                    for sub_gdm in gdm
                                    for obj, val in sub_gdm.items()                                    
                                  )

        else:
            self.logger.debug('Manually calculating max and min. '
                      +'No valid override found. '
                      )
            data = OrderedDict( (obj, select(val, field)) 
                                for sub_gdm in gdm
                                for obj, val in sub_gdm.items()                                    
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




        use_manual_classes = (options.inter_class_bounds and
                              isinstance(options.inter_class_bounds, list)
                              and all( isinstance(x, Number) 
                                       for x in options.inter_class_bounds
                                     )
                             )

        if options.sort_data or (
           not use_manual_classes 
           and options.class_spacing in QUANTILE_METHODS ):
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
            inter_class_bounds = options.inter_class_bounds
            self.logger.info('Using manually specified'
                            +' inter-class boundaries. '
                            )
        elif options.class_spacing in QUANTILE_METHODS:
            self.logger.debug('Using: %s class calculation method.' % options.class_spacing)
            inter_class_bounds = QUANTILE_METHODS[options.class_spacing](data = data.values()
                                                                       ,num_classes = m
                                                                       ,options = options
                                                                       )

        else: 
            inter_class_bounds = [data_cruncher.splines[options.class_spacing](i
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

        count_bound_counts = Counter(inter_class_bounds)

        class_overlaps = [val for val in count_bound_counts
                          if count_bound_counts[val] > 1
                         ]

        if class_overlaps:
            msg = 'Class overlaps at: ' + ' '.join(map(str, class_overlaps))
            if options.remove_overlaps:
                for overlap in class_overlaps:
                    inter_class_bounds.remove(overlap)

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


            if options.re_normaliser not in data_cruncher.VALID_RE_NORMALISERS:
                # e.g.  'linear', exponential, logarithmic
                msg = 'Invalid re_normaliser : %s ' % options.re_normaliser
                self.logger.error(msg)
                raise ValueError(msg)


        self.logger.debug('num class boundaries == ' 
                    + str(len(inter_class_bounds))
                    )
        self.logger.debug('m == %s' % m)
        self.logger.debug('n == %s' % n)
        if len(inter_class_bounds) + 1 < m:
            logger.warning('It has only been possible to classify data into '
                          +'%s distinct classes, not %s' % (len(inter_class_bounds) + 1, m)
                          )

        msg = 'x_min == %s \n' % x_min
        msg += 'class bounds == %s \n' % inter_class_bounds
        msg += 'x_max == %s ' % x_max
        self.logger.debug(msg)


        if (x_max - x_min < options.tol 
            or options.re_normaliser not in data_cruncher.splines):
            #
            re_normalise = lambda x, *args : x
        else:
            spline = data_cruncher.splines[options.re_normaliser]
            def re_normalise(x, p = param.get(options.re_normaliser, 'Not used')):
                return spline(x
                             ,x_min
                             ,p   # base or x_mid.  Can't be kwarg.
                             ,x_max
                             ,y_min = x_min
                             ,y_max = x_max
                             )
        
        def class_mid_point(x): 
            highest_lower_bound = x_min if x < inter_class_bounds[0] else max(
                                            y 
                                            for y in [x_min] + inter_class_bounds
                                            if y <= x                  
                                            )
            #Classes include their lower bound
            least_upper_bound = x_max if x >= inter_class_bounds[-1] else min(
                                            y 
                                            for y in inter_class_bounds + [x_max] 
                                            if y > x
                                            )

            return re_normalise(0.5*(least_upper_bound + highest_lower_bound))



        if options.colour_as_class:
            renormaliser = class_mid_point
        else:
            renormaliser = re_normalise





        if inter_class_bounds:
            mid_points = [0.5*(x_min + min(inter_class_bounds))]
            mid_points += [0.5*(x + y) for x, y in itertools.pairwise(inter_class_bounds)]
            mid_points += [0.5*(x_max + max(inter_class_bounds))]
        else:
            mid_points = [0.5*(x_min + x_max)]
        self.logger.debug(mid_points)

        locale.setlocale(locale.LC_ALL, options.locale)

        def format_number(x, format_str):
            #type(Number, str) -> str
            if isinstance(x, int):
                format_str = '{:d}'
            return format_str.format(x)

        if inter_class_bounds:
            x_min_str = format_number(x_min, options.num_format) 
            upper_str = format_number(min( inter_class_bounds ), options.num_format)
            mid_pt_str = format_number(mid_points[0], options.num_format)
            #e.g. first_leg_tag_str = 'below {upper}'

            legend_tags = [options.first_leg_tag_str.format(lower = x_min_str
                                                        ,upper = upper_str
                                                        ,mid_pt = mid_pt_str
                                                        )
                        ]
            for lower_bound, class_mid_point, upper_bound in zip(inter_class_bounds[0:-1]
                                                        ,mid_points[1:-1]
                                                        ,inter_class_bounds[1:]  
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

            lower_str =  format_number(max( inter_class_bounds ), options.num_format)
            x_max_str =  format_number(x_max, options.num_format)
            mid_pt_str =  format_number(mid_points[-1], options.num_format)

            # e.g. last_leg_tag_str = 'above {lower}'
            legend_tags += [options.last_leg_tag_str.format(lower = lower_str
                                                        ,upper = x_max_str 
                                                        ,mid_pt = mid_pt_str 
                                                        )        
                        ]        
        else:
            x_min_str = format_number(x_min, options.num_format)
            x_max_str = format_number(x_max, options.num_format)
            mid_pt_str = format_number(mid_points[0], options.num_format)
            # e.g. gen_leg_tag_str = '{lower} - {upper}' # also supports {mid}
            legend_tags = [options.gen_leg_tag_str.format(lower = x_min_str
                                                        ,upper = x_max_str
                                                        ,mid_pt = mid_pt_str 
                                                        )
                        ]                                          

        self.logger.debug(legend_tags)

        gen_exp = ((key, renormaliser(val))
                   for key, val in itertools.chain(data.items()
                                                  ,zip(legend_tags, mid_points)
                                                  )
                  )
        gdm = gdm_from_GH_Datatree.GeomDataMapping(gen_exp)

        #rename for retvals
        plot_min, plot_max = x_min, x_max
        
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = 'plot_min', 'plot_max', 'gdm', 'field', 'mid_points', 'inter_class_bounds'
    component_outputs = retvals[:2] + ('Data', 'Geom') + retvals[-3:]


class ObjectsRecolourer(sDNA_GH_Tool):

    class Options(DataParser.Options):
        Col_Grad = False
        Col_Grad_num = 5
        rgb_max = (155, 0, 0) #990000
        rgb_min = (0, 0, 125) #3333cc
        rgb_mid = (0, 155, 0) # guessed
        line_width = 4 # millimetres? 
        leg_extent = options_manager.Sentinel('leg_extent is automatically '
                                             +'calculated by sDNA_GH unless '
                                             +'overridden.  '
                                             )
        # [xmin, ymin, xmax, ymax]
        plane = None # plane for legend frame only. 
                     # add_GH_rectangle sets plane to rs.WorldXYPlane() if None
        bbox = options_manager.Sentinel('bbox is automatically calculated by '
                                       +'sDNA_GH unless overridden.  '
                                       ) 
        # [xmin, ymin, xmax, ymax]
        suppress_no_data_error = False


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
            ,('field_prefix', dict(self.parse_data.param_infos)['field_prefix'])
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

    
    component_inputs = ('plot_min', 'plot_max', 'Data', 'Geom', 'bbox', 'field', 'field_prefix')

    def __call__(self, gdm, opts, bbox):
        #type(str, dict, dict) -> int, str, dict, list
        # Note!  opts can be mutated.
        self.debug('Initialising Class.  Creating Class Logger. ')

        if opts is None:
            opts = self.opts
        options = opts['options']
        
        field = options.field
        plot_min, plot_max = options.plot_min, options.plot_max

        if not gdm:
            msg = 'No Geom objects to recolour. '
            msg += 'Connect list of objects to Geom. '
            msg += 'gdm == %s' % gdm
            self.logger.error(msg)
            raise ValueError(msg)

        if isinstance(gdm, gdm_from_GH_Datatree.GeomDataMapping):
            gdm = [gdm]


        objs_to_parse = gdm_from_GH_Datatree.GeomDataMapping(
                                        (k, v) 
                                        for sub_gdm in gdm
                                        for k, v in sub_gdm.items()
                                        if isinstance(v, dict) and field in v
                                        )  
                                        # any geom with a normal gdm dict of 
                                        # keys / vals containing field

        objs_with_numbers = gdm_from_GH_Datatree.GeomDataMapping(
                                                    (k, v) 
                                                    for sub_gdm in gdm
                                                    for k, v in sub_gdm.items()
                                                    if isinstance(v, Number) 
                                                    ) 
        objs_to_recolour = gdm_from_GH_Datatree.GeomDataMapping( 
                                        (k, v) 
                                        for sub_gdm in gdm
                                        for k, v in sub_gdm.items()
                                        if isinstance(v, System.Drawing.Color)
                                        )


        self.logger.debug('Objects to parse & fields == %s, ... , %s'
                         %(objs_to_parse.items()[:2], objs_to_parse.items()[-2:])
                         )

        self.logger.debug('Objects already parsed & parsed vals == %s, ... , %s'
                         %(objs_with_numbers.items()[:5], objs_with_numbers.items()[-5:])
                         )

        self.logger.debug('Objects that already have colours == %s, ... , %s'
                         %(objs_to_recolour.items()[:5], objs_to_recolour.items()[-5:])
                         )
        
        if data_cruncher.max_and_min_are_valid(plot_max, plot_min):
            objs_to_get_colour = objs_with_numbers
        else:
            objs_to_get_colour = OrderedDict()
            objs_to_parse.update(objs_with_numbers)


        if not objs_to_parse and not objs_with_numbers and not objs_to_recolour:
            msg = 'No data to recolour. Supply raw numbers or colours in Data '
            supported_fields = set(field for sub_gdm in gdm
                                      for val in sub_gdm.values() 
                                      for field in val
                                      if isinstance(val, dict)
                                  )
            if supported_fields:
                msg += 'or set field to one of: %s ' % supported_fields
            if options.suppress_no_data_error:
                self.logger.warning(msg)
                warnings.warn(msg)
            else:
                self.logger.error(msg)
                raise ValueError(msg)

        if objs_to_parse:
            #
            self.info('Raw data in ObjectsRecolourer.  Calling DataParser...')
            self.debug('Raw data: %s' % objs_to_parse.items()[:4])
            x_min, x_max, gdm_in, field, mid_points, class_bounds = self.parse_data(
                                                   gdm = objs_to_parse
                                                  ,opts = opts 
                                                  #includes plot_min, plot_max
                                                  )
                                                                            
        else:
            self.logger.debug('Skipping parsing')
            gdm_in = {}
            x_min, x_max = plot_min, plot_max

        self.logger.debug('x_min == %s ' % x_min)
        self.logger.debug('x_max == %s ' % x_max)


        objs_to_get_colour.update(gdm_in)  # no key clashes possible unless for 
                                           # some x both isinstance(x, dict) 
                                           # and isinstance(x, Number)
        logger.debug('Objects to get colours & vals == %s, ... , %s'
                    %(objs_to_get_colour.items()[:5], objs_to_get_colour.items()[-5:])
                    )

        if not objs_to_get_colour:
            self.logger.debug('No objects need colours to be created. ')
        elif (isinstance(x_max, Number) and 
              isinstance(x_min, Number) and
              abs(x_max - x_min) < options.tol):
            #
            default_colour = rs.CreateColor(options.rgb_mid)
            get_colour = lambda x : default_colour
        elif not data_cruncher.max_and_min_are_valid(x_max, x_min):
            msg = ('Cannot create colours for data without a valid '
                  +'max: %s and min: %s to refer to' % (x_max, x_min)
                  )
            self.logger.error(msg)
            raise NotImplementedError(msg)
        elif options.Col_Grad:
            grad = getattr( GH_Gradient()
                          ,self.GH_Gradient_preset_names[options.Col_Grad_num]
                          )
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
        #elif not 
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

        logger.debug('Objects to recolour & colours == %s, ... , %s'
                    %(objs_to_recolour.items()[:5], objs_to_recolour.items()[-5:])
                    )

        legend_tags = OrderedDict()
        legend_first_pattern = funcs.make_regex(options.first_leg_tag_str)
        legend_inner_pattern = funcs.make_regex(options.gen_leg_tag_str)
        legend_last_pattern = funcs.make_regex(options.last_leg_tag_str)

        legend_tag_patterns = (legend_first_pattern
                              ,legend_inner_pattern
                              ,legend_last_pattern
                              )


        GH_objs_to_recolour = gdm_from_GH_Datatree.GeomDataMapping()
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
            if isinstance(obj, basestring) and any(bool(re.match(pattern, obj)) 
                                                   for pattern in legend_tag_patterns
                                                  ):
                #sc.doc = ghdoc it's now never changed, 
                #assert sc.doc == ghdoc #anyway
                legend_tags[obj] = rs.CreateColor(new_colour) # Could glitch if dupe  
            else:
                try:
                    rs.ObjectColor(obj, new_colour)
                    recoloured_Rhino_objs.append(obj)
                    self.logger.debug('Recoloured: %s' % obj)
                except (ValueError, TypeError):
                    self.logger.debug('Error recolouring obj: %s to colour %s: ' 
                                     % (obj, new_colour)
                                     )
                    GH_objs_to_recolour[obj] = new_colour 
                    
        sc.doc = ghdoc
            
        self.logger.debug('recoloured_Rhino_objs: %s' % recoloured_Rhino_objs)

        if recoloured_Rhino_objs:
            sc.doc = Rhino.RhinoDoc.ActiveDoc
            self.logger.debug('Setting Rhino colour sources and line width.')                 
            rs.ObjectColorSource(recoloured_Rhino_objs, 1)  # 1 => colour from object
            rs.ObjectPrintColorSource(recoloured_Rhino_objs, 2)  # 2 => colour from object
            rs.ObjectPrintWidthSource(recoloured_Rhino_objs, 1)  # 1 => logger.debug width from object
            rs.ObjectPrintWidth(recoloured_Rhino_objs, options.line_width) # width in mm
            rs.Command('_PrintDisplay _State=_On Color=Display Thickness=%s '
                      %options.line_width
                      +' _enter'
                      )
            #sc.doc.Views.Redraw()
            sc.doc = ghdoc




        if (bbox or
           (options.leg_extent is not None and 
            not isinstance(options.leg_extent, options_manager.Sentinel)) or
           (options.bbox is not None and 
            not isinstance(options.bbox, options_manager.Sentinel))):
            #
            if (options.leg_extent is not None and 
                not isinstance(options.leg_extent, options_manager.Sentinel)):
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

                self.logger.debug('bbox == %s ' % bbox)

                leg_width = math.sqrt((bbox_xmax - bbox_xmin)**2 
                                     +(bbox_ymax - bbox_ymin)**2
                                     ) / 2
                tag_height = max(1, 0.4 * leg_width / 7)
                leg_height = min(options.num_classes * tag_height * 1.04
                                ,bbox_ymax - bbox_ymin
                                )

                self.logger.debug('leg_width == %s' % leg_width)
                self.logger.debug('tag_height == %s' % tag_height)
                self.logger.debug('leg_height == %s' % leg_height)

                legend_xmin = bbox_xmax + 0.07 * leg_width
                legend_ymin = bbox_ymax - leg_height

                legend_xmax = legend_xmin + leg_width
                legend_ymax = bbox_ymax
                

            self.logger.debug('leg_bounds == %s ' % [legend_xmin
                                                    ,legend_ymin
                                                    ,legend_xmax
                                                    ,legend_ymax
                                                    ]
                              )

            leg_frame = rhino_gh_geom.add_GH_rectangle(legend_xmin
                                             ,legend_ymin
                                             ,legend_xmax
                                             ,legend_ymax
                                             )



        else:
            self.logger.info('No legend rectangle dimensions.  ')
            leg_frame = None

    


        self.logger.debug(leg_frame)


        gdm = GH_objs_to_recolour
        leg_cols = list(legend_tags.values())
        leg_tags = list(legend_tags.keys())  #both are used by smart component
        self.logger.debug('gdm == %s' % gdm)

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





toml_no_tuples = options_manager.toml_types[:]
if tuple in toml_no_tuples:
    toml_no_tuples.remove(tuple)
#Internally in sDNA_GH opts, tuples are read only.

bare_key_chars = string.ascii_letters + string.digits + '_-' 
# allowed chars in "bare keys" in Toml. https://toml.io/en/v1.0.0#keys
# "quoted keys" support an extended character set



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


    class Metas(sDNAMetaOptions):
        config = os.path.join(launcher.USER_INSTALLATION_FOLDER
                             ,launcher.PACKAGE_NAME  
                             ,'config.toml'
                             )

    class Options(PythonOptions):
        pass
    Options.save_to = Metas.config


    param_infos = sDNA_GH_Tool.param_infos + (
                   ('save_to', add_params.ParamInfo(
                             param_Class = Param_FilePath
                            ,Description = ('The name of the .toml file to '
                                           +'save your options to. '
                                           +'Default: %(save_to)s'
                                           )
                            ))
                  ,('python', add_params.ParamInfo(
                             param_Class = Param_FilePath
                            ,Description = ('File path of the Python 2.7 '
                                           +'executable to run sDNA with, '
                                           +'or its parent folder. '
                                           +'cPython 2.7 is required for sDNA '
                                           +'tools (download link in readme). '
                                           +'Default: %(python)s'
                                           )
                            ))
                  ,('sDNA_paths', add_params.ParamInfo(
                             param_Class = Param_FilePath
                            ,Description = ('File path to the folder of the '
                                           +'sDNA installation to be used with'
                                           +' sDNA_GH. This must contain '
                                           +'%(sDNAUISpec)s.py and '
                                           +'%(runsdnacommand)s.py. '
# metas take priority in all_options_dict so even though there is a name 
# clash, the module names in metas will be interpolated over the Sentinels or
# actual modules in options.
                                           +'Default: %(sDNA_paths)s'
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
                       ,'sync'
                       )

    def __call__(self, opts, local_metas):
        self.debug('Starting class logger')

        metas = opts['metas']
        options = opts['options']
                
        python, sDNA_paths = options.python, metas.sDNA_paths
        save_to = options.save_to

        self.debug('save_to : %s, python : %s, sDNA_paths : %s' 
                  % (save_to, python, sDNA_paths)
                  )


        check_python(opts)
        import_sDNA(opts)

        self.logger.debug('options == %s ' % (opts['options'],))

        # self.logger.debug('opts == %s' % '\n\n'.join(str(item) 
        #                                      for item in opts.items()
        #                                      )
        #           )


        parsed_dict = parse_values_for_toml(opts)   
        parsed_dict['local_metas'] = parse_values_for_toml(local_metas)   
        parsed_dict['metas'].pop('config') # no nested options files

        if 'sDNA' in parsed_dict['metas']:
            parsed_dict['metas'].pop('sDNA') # read only.  auto-updated.

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
            parsed_dict['options'].pop('path') # no project-specific paths are
                                               # saved to the installation wide 
                                               # config file's options
            parsed_dict['options'].pop('working_folder')
            parsed_dict['options']['message'] = 'Installation wide user options file. '
        else:
            parsed_dict['options']['message'] = 'Project specific user options file. '

        options_manager.save_toml_file(save_to, parsed_dict)
        
        retcode = 0
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = ('retcode',)
    component_outputs = ()

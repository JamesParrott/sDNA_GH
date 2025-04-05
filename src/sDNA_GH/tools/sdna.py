#! /usr/bin/awk NR==3
# -*- coding: utf-8 -*-
# This module requires Grasshopper Python (Rhino3D)

# MIT License

# Copyright (c) [2021] [Cardiff University, a body incorporated
# by Royal Charter and a registered charity (number:
# 1136855) whose administrative offices are at 7th floor 30-
# 36 Newport Road, University CF24 0DE, Wales, UK]

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

__authors__ = {'James Parrott', 'Crispin Cooper'}
__version__ = '3.0.1'

import os
import sys
import abc
import logging
import subprocess
import re
import warnings
import collections


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

from ..skel.tools.helpers import funcs
from ..skel.tools import runner                                       
from ..skel import add_params
from ..skel import builder
from .. import options_manager
from .. import pyshp_wrapper
from .. import logging_wrapper
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


def sDNA_plus_installation_site_env_lib_and_python():
    
    where_sDNA = subprocess.check_output(["where","sDNA"])
    
    if len(where_sDNA) <= 1:
        return None, None
    
    found_path = where_sDNA[0].upper() + where_sDNA[1:].rstrip()
    expected_path =  os.path.join(os.getenv("USERPROFILE"),'.local','bin','sdna.exe')
    
    if found_path == expected_path:
        for tool_venvs in [os.path.join(os.getenv('APPDATA'),'uv','tools')
                          ,os.path.join(os.getenv('USERPROFILE'),'pipx','venvs')
                          ]:
            if not os.path.isdir(tool_venvs):
                continue
            for tool_venv in glob.glob(os.path.join(tool_venvs,'*sdna*')):
                sDNA_venv_lib = os.path.join(tool_venv,'Lib','site-packages','sDNA')
                if not (os.path.isfile(os.path.join(sDNA_venv_lib, 'sDNAUISpec.py')) and 
                        os.path.isfile(os.path.join(sDNA_venv_lib, 'runsdnacommand.py'))):
                    continue
                python = os.path.join(tool_venv, 'Scripts', 'python.exe')
                if not os.path.isfile(python):
                    continue
                try:
                    subprocess.check_output([python, "--version"])
                    return sDNA_venv_lib, python
                except:
                    continue
                

    return None, None

site_env_lib, python = sDNA_plus_installation_site_env_lib_and_python()

if site_env_lib is not None and python is not None:
    
    class sDNAMetaOptions(object):
        """All options needed to import sDNA. """

        sDNAUISpec = 'sDNAUISpec'
        runsdnacommand = 'runsdnacommand'
        sDNA_paths = [site_env_lib]

    
    class PythonOptions(object):
        """All options needed to specify a Python interpreter, or search for one. """

        python_paths = []
        python_exes = []
        python = python

else:

    class sDNAMetaOptions(object):
        """All options needed to import sDNA. """

        sDNAUISpec = 'sDNAUISpec'
        runsdnacommand = 'runsdnacommand'
        sDNA_paths = list( funcs.windows_installation_paths('sDNA') )



    class PythonOptions(object):
        """All options needed to specify a Python interpreter, or search for one. """

        python_paths = list( funcs.windows_installation_paths(tuple('Python3%s' % i 
                                                                    for i in range(12, 8, -1)
                                                                )  
                                                            +('Python3'
                                                            ,'Python_3'
                                                            ,'Python'
                                                            ,'Python27'
                                                            ,'Python_27'
                                                            ,'Python_2.7'
                                                            ,'Python2.7'
                                                            )
                                                            )
                        )
        python_exes = ['python.exe', 'python3.exe', 'py27.exe']
        python = '' 




sDNA_meta_options = options_manager.namedtuple_from_class(sDNAMetaOptions)
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
              +'python interpreter or its parent folder in python '
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
            ,module_name_error_msg = (
                 "Invalid file names: %s, %s " % requested_sDNA 
                +"Please supply valid names of 'sDNAUISpec.py' "
                +"and 'runsdnacommand.py' files in "
                +"sDNAUISpec and runsdnacommand "
                +"respectively. " # names not strings error
                )
            ,folders_error_msg = (
                 "sDNA_GH could not find a valid folder to look for sDNA in. " 
                +"Please supply the "
                +"correct name of the path to the sDNA folder you "
                +"wish to use with sDNA_GH, in "
                +"sDNA_paths.  This folder should contain the files named in "
                +"sDNAUISpec: %s.py and runsdnacommand: %s.py. " % requested_sDNA
                # not existing folders error
                )
            ,modules_not_found_msg = (
                 "sDNA_GH failed to find an sDNA file specified in "
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
            )
    except launcher.InvalidArgsError as e:
        raise e
    except BaseException: # Masking is deliberate, to give user a fix
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

ghuser_folder = os.path.join('components', '')

package_root = os.path.dirname(os.path.dirname(__file__))

package_path = os.path.dirname(package_root)

components_folder = os.path.join(
                        package_root
                       ,'components'
                       )

built_user_objects_location = os.path.join(components_folder
                                          ,'automatically_built'
                                          )
     
icons_location = os.path.join(components_folder
                             ,'icons'
                             )


def build_sDNA_GH_components(
     readme_path = os.path.join(package_root, 'README.md')
    ,**kwargs
    ):
    #type(kwargs) -> list
    
    
    
    kwargs.setdefault('dest'
                     ,built_user_objects_location
                     )

    logger.debug('README_md_path == %s' % readme_path)


    launcher_path = os.path.join(package_root, 'launcher.py')


    return builder.build_comps_with_docstring_from_readme(
                                 default_path = launcher_path
                                ,icons_path = icons_location 
                                ,path_dict = {}
                                ,readme_path = readme_path
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

    kwargs.setdefault('dest'
                     ,built_user_objects_location  
                     )

    def ghuser_file_path(name, folder = built_user_objects_location):
        #type(str)->str
        return os.path.join(folder, name + '.ghuser') 

    components_folders = [built_user_objects_location]

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
                   for name in names 
                   for folder in components_folders):
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
                            
        self.get_syntaxes[sDNA] = get_syntax = sDNA_Tool.getSyntax

        
        self.input_specs[sDNA] = input_spec = sDNA_Tool.getInputSpec()

        # Don't add 'advanced' or ADVANCED_ARG_INPUT_PARAMS to sDNA Prepare, Learn or Predict
        if (any(tuple_[0]=='analmet' and 'HYBRID' in tuple_[3] for tuple_ in input_spec) and 
            self.ADVANCED_ARG_INPUT_PARAMS):

            # Not used - advanced is in all the UISpecs that have 'analmet'
            # (all tools except sDNA Prepare, Learn and Predict)
            if not any(tuple_[0]=='advanced' for tuple_ in input_spec):
                defaults['advanced'] = ''

                #                 (varname,    display_name,                  data_type,    default
                #                                                                     filter_,  required)
                input_spec.append(('advanced', 'sDNA Advanced Config string', 'Text', None, '', False))

            input_spec.extend(self.ADVANCED_ARG_INPUT_PARAMS)

        defaults = OrderedDict((tuple_[0], tuple_[4]) for tuple_ in input_spec)
        self.input_specs[sDNA] = input_spec

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

        for spec in input_spec:
            varname, display_name, data_type, filter_, default, required = spec   
            
            if display_name.rstrip().endswith('.'):
                description = display_name
            else:
                description = display_name +'. '
            description += 'Default value == %(' + varname + ')s.'
            # to be interpolated by self.param_info_list from self.all_options_dict

            if (isinstance(filter_, Iterable) 
               and not isinstance(filter_, basestring)
               and len(filter_) >= 2): 
                #
                description += ' Allowed values: %s. ' % ', '.join(map(str, filter_))

            # if required:     
            #     description = 'REQUIRED. %s' % description

            py_type_name = ''

            if data_type:
                if data_type.lower() not in self.sDNA_types_to_py_type_names:
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

            if 'advanced' not in defaults:
                msg = "'advanced' not in defaults_dict"
                self.logger.warning(msg)
                warnings.showwarning(message = msg
                    ,category = UserWarning
                    ,filename = __file__ + self.__class__.__name__
                    ,lineno = 1149
                    )

            new_keys += tuple()

            if new_keys:
                self.component_inputs += new_keys

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


    # Flag arguments not supported, only ones to be included in 
    # sDNA advanced config string as "key=value".
    #   (varname,        display_name,                                data_type,    default
    #                                                                         filter_,  required)
    ADVANCED_ARG_INPUT_PARAMS = (
        ('lineformula', 'Line formula (requires hybrid metric).',     'Text', None, '', False)
       ,('juncformula', 'Junction formula (requires hybrid metric).', 'Text', None, '0', False)
       )


    LIST_ARGS = ('radius'
                ,'radii'
                ,'preserve_absolute'
                ,'preserve_unitlength'
                ,'origins'
                ,'destinations'
                ,'predictors'
                ,'reglambda'
                ) 
    
    component_inputs = ('file', 'config') 




    def __call__(self # the tool instance not the GH component.
                ,f_name
                ,opts
                ,input = None
                ,output = None
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



        for key, val in tool_opts.items():
            if key in self.LIST_ARGS and isinstance(val, list) and len(val) >= 2:
                tool_opts[key] = ','.join(str(element) for element in val)
                self.logger.info('Converted list to str: %s' % tool_opts[key])


        if 'advanced' in tool_opts:
            self.logger.debug('Calling self._add_to_advanced_config_string')
            tool_opts = self._add_to_advanced_config_string(
                                 tool_opts
                                ,opts
                                ,extra_inputs = kwargs
                                )

            # user needs to set sync = false to avoid sharing advanced.
            # Shared advanced strings will duplicate values for args
            # in self.ADVANCED_ARG_INPUT_PARAMS
            #  
            all_sDNA_tool_opts = get_tool_opts(opts
                                              ,nick_name = self.nick_name
                                              ,tool_name = self.tool_name
                                              ,sDNA = None
                                              ,val = None
                                              )
            all_sDNA_tool_opts[sDNA] = tool_opts_sDNA._replace(advanced = tool_opts['advanced'])

        self.logger.debug('tool_opts: %s' % tool_opts)

        syntax = get_syntax(tool_opts)

        command = (options.python
                  +' -u ' 
                  +' -E '
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

        advanced = tool_opts.get('advanced', '')

        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    
    retvals = 'retcode', 'f_name', 'input', 'output', 'advanced'
    component_outputs = ('file',) # retvals[-1])

    def _add_to_advanced_config_string(self, tool_opts, opts, extra_inputs):
        # If the user has specifed an advanced config string, as well as 
        # non-empty values for some params in self.ADVANCED_ARG_INPUT_PARAMS, 
        # strip out the key-value pairs in the advanced config string (to be 
        # overidden by the params in the next step) 
        tool_opts['advanced'] = ';'.join(str_
                                         for str_ in tool_opts.get('advanced', '').split(';')
                                         if not any(spec[0] == str_.partition('=')[0]
                                                    for spec in self.ADVANCED_ARG_INPUT_PARAMS
                                                    if tool_opts.get(spec[0], '')
                                                   )
                                        )

        self.logger.info("repr(tool_opts['advanced']): %s " % repr(tool_opts['advanced']))

        # Mutate tool_opts, removing keys in ADVANCED_ARG_INPUT_PARAMS
        for spec in self.ADVANCED_ARG_INPUT_PARAMS:
            key, __, __, __, __, __ = spec
            val = tool_opts.pop(key, '')
            if val: 
                advanced_config_substring = '%s=%s' % (key, val)

                if not tool_opts['advanced']:
                    tool_opts['advanced'] = advanced_config_substring
                elif advanced_config_substring not in tool_opts['advanced']:
                    tool_opts['advanced'] += (';' + advanced_config_substring)

        self.logger.info("repr(tool_opts['advanced']): %s " % repr(tool_opts['advanced']))

        
        metas = opts['metas']

        if metas.make_advanced:
            user_inputs = self.component.params_adder.user_inputs
            # We need this reference because some args this tool doesn't 
            # recognise, may have been added to the component, by another
            # tool on it.

            self.logger.debug('user_inputs == %s' % user_inputs)
            self.logger.debug('needed_inputs == %s' 
                                % self.component.params_adder.needed_inputs
                                )

            custom_advanced = ';'.join(
                                key if val is None else ('%s=%s' % (key, val))
                                for key, val in extra_inputs.items()
                                if (key in user_inputs and 
                                    key not in self.built_in_options(opts)
                                    )
                                )

            tool_opts['advanced'] = ';'.join([tool_opts['advanced'], custom_advanced])

            self.logger.info('Advanced config string from user added input params: %s' % tool_opts['advanced'])


        else:
            self.logger.debug('Advanced config string: %s' % tool_opts['advanced'])


        return tool_opts
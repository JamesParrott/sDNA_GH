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
__version__ = '0.02'

import os
import logging
import subprocess
from .helpers.funcs import itertools #pairwise from recipe if we're in Python 2
import re
import warnings
from collections import OrderedDict, Counter
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
from System.Drawing import Color as Colour #.Net / C# Class
            #System is also available in IronPython, but System.Drawing isn't
from Grasshopper.GUI.Gradient import GH_Gradient
from Grasshopper.Kernel.Parameters import (Param_Arc
                                          ,Param_Curve
                                          ,Param_Boolean
                                          ,Param_Geometry
                                          ,Param_String
                                          ,Param_FilePath
                                          ,Param_Guid
                                          ,Param_Integer
                                          ,Param_Line
                                          ,Param_Rectangle
                                          ,Param_Colour
                                          ,Param_Number
                                          ,Param_ScriptVariable
                                          ,Param_GenericObject
                                          ,Param_Guid
                                          )

from .helpers import funcs 
from .skel.basic.ghdoc import ghdoc
from .skel.tools.helpers.funcs import is_uuid
from .skel.tools.helpers import checkers
from .skel.tools import runner                                       
from .skel import add_params
from . import options_manager
from . import pyshp_wrapper
from . import logging_wrapper
from . import gdm_from_GH_Datatree

try:
    basestring #type: ignore
except NameError:
    basestring = str

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
ClassLogger = logging_wrapper.class_logger_factory(logger = logger
                                                  ,module_name = __name__
                                                  )







class sDNA_GH_Tool(runner.RunnableTool, add_params.ToolWithParams, ClassLogger):

    factories_dict = dict(go = Param_Boolean
                         #,OK = Param_ScriptVariable
                         ,file = Param_FilePath
                         #,Geom = Param_ScriptVariable
                         #,Data = Param_ScriptVariable
                         #,leg_cols = Param_ScriptVariable
                         #,leg_tags = Param_ScriptVariable
                         #,leg_frame = Param_ScriptVariable
                         #,gdm = Param_ScriptVariable
                         #,opts = Param_ScriptVariable
                         ,config = Param_FilePath
                         #,l_metas = Param_ScriptVariable
                         ,field = Param_String
                         #,fields = Param_ScriptVariable
                         #,plot_min = Param_ScriptVariable
                         #,plot_max = Param_ScriptVariable
                         #,class_bounds = Param_ScriptVariable
                         #,abbrevs = Param_ScriptVariable
                         #,sDNA_fields = Param_ScriptVariable
                         #,bbox = Param_ScriptVariable
                         #,Param_GenericObject
                         #,Param_Guid
                         )

    type_hints_dict = dict(Geom = GhPython.Component.GhDocGuidHint())

    access_methods_dict = dict(Data = 'tree')

    @classmethod
    def params_list(cls, names):
        return [add_params.ParamInfo(
                          factory = cls.factories_dict.get(name
                                                          ,Param_ScriptVariable
                                                          )
                         ,NickName = name
                         ,Access = 'tree' if name == 'Data' else 'list'
                         ) for name in names                            
               ]

def delete_file(path
               ,logger = logger
               ):
    #type(str, type[any]) -> None
    if os.path.isfile(path):
        logger.info('Deleting file ' + path)
        os.remove(path)

def name_matches(file_name, regexes = ()):
    if isinstance(regexes, str):
        regexes = (regexes,)
    return any(bool(re.match(regex, file_name)) for regex in regexes)

def delete_shp_files_if_req(f_name
                           ,logger = logger
                           ,delete = True
                           ,strict_no_del = False
                           ,regexes = () # no file extension in regexes
                           ):
    #type(str, type[any], bool, str/tuple) -> None
    if not strict_no_del:
        file_name = f_name.rpartition('.')[0]
        logger.debug('Delete == %s ' % delete)
        if (delete or name_matches(file_name, regexes)):
            for ending in ('.shp', '.dbf', '.shx'):
                path = file_name + ending
                delete_file(path, logger)

def has_keywords(nick_name, keywords = ('prepare',)):
    return any(substr in nick_name.strip().strip('_').lower() 
              for substr in keywords
              )

sDNA_fmt_str = '"({sDNAUISPec},{runsdnacommand})"'


def sDNA_key(opts):
    #type(tuple[str]) -> str
    """ Defines the sub-dict key for each sDNA version, from the tuple
        of module names.
        e.g. ('sDNAUISpec','runsdnacommand') -> sDNAUISpec. 
        Returns a string so the key can be loaded from a toml file.
    """
    metas = opts['metas']
    sDNA = (metas.sDNAUISpec, metas.runsdnacommand)
    return sDNA_fmt_str.format(sDNAUISPec = sDNA[0], runsdnacommand = sDNA[1])

def nested_set_default(d, keys, last_default = None):
    #type(dict, Sequence[Hashable], type[any])
    if last_default is None:
        defaults = itertools.repeat({})
    else:
        defaults = itertools.chain(itertools.repeat({}, len(keys) - 1)
                                  ,[last_default]
                                  )

    for key, default in zip(keys, defaults):
        d = d.setdefault(key, default)
    return d

def get_tool_opts(nick_name, opts, tool_name = None, sDNA = None, val = None):
    #type(str, dict, str, str, type[any])
    # might mutate opts
    if tool_name and tool_name != nick_name:
        keys = [nick_name, tool_name]
    else:
        keys = [nick_name]
    if sDNA is not None:
        keys += [sDNA]
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

def is_strict_nested_dict(d):
    #type(dict) -> bool
    return all(isinstance(val, dict) for val in d.values())

def update_opts(opts
               ,override
               ,metas = None
               ,keys = []
               ,depth = 1
               ,max_depth = None 
               ,end_conditions = None
               ,key_patterns = (funcs.make_regex(sDNA_fmt_str),)
               ):
    #type(type[any], dict, Sequence[Hashable], int, dict, Sequence[function]) -> NamedTuple

    current_opts = nested_set_default(opts, keys)  # returns opts if keys == []

    if not isinstance(current_opts, dict) or not isinstance(override, dict):
        msg = ('opts and override need to be dictionaries. '
              +'keys == %s, depth == %s' % (keys, depth)
              )
        logger.error(msg)
        raise TypeError(msg)
    if max_depth is None:
        max_depth = {'options' : 1, 'metas' : 1, None : 3}
    if end_conditions is None:
        
        end_conditions = [lambda key, value : not isinstance(value, dict)
                     ,lambda key, value : max_depth.get(keys[0], max_depth[None]) >= depth
                     ]
        end_conditions += list(lambda key, value : bool(re.match(pattern, key))
                           for pattern in key_patterns
                          )  # list( generator expression) is used here
                             # to avoid getting path as a class variable in Python 2 from
                             # the leaky scope of list comprehensions.  
    sub_dicts = override.copy()
    general_opts = {key : sub_dicts.pop(key) 
                    for key, value in override.items() 
                    if any(end_condition(key, value) 
                           for end_condition in end_conditions)
                   }
    if not sub_dicts:  # Shallow enough dicts, whose keys aren't 
                       # "(sDNAUISpec,runsdnacommand)"
        sub_dicts = {key : {} 
                     for (key, value) in current_opts.items()
                     if all(not end_condition(key, value) 
                            for end_condition in end_conditions)
                    }
    if sub_dicts:
        for key, val in sub_dicts.items():
            new_override = general_opts.copy()
            new_override.update(val)
            update_opts(opts
                       ,override = new_override 
                       ,metas = metas
                       ,keys = keys + [key]
                       ,depth = depth + 1
                       ,max_depth = max_depth
                       ,end_conditions = end_conditions
                       ,key_patterns = key_patterns
                       )
    else:
        for key, val in general_opts.items():
            if key in current_opts:
                current_opts[key] = options_manager.override_namedtuple(
                                             current_opts[key]
                                            ,val
                                            ,**metas._asdict()
                                            )
            else:
                current_opts[key] = options_manager.namedtuple_from_dict(
                                                 general_opts
                                                ,'NT_%s' % key
                                                ,strict = True
                                                )  





class sDNA_ToolWrapper(sDNA_GH_Tool):
    # In addition to the 
    # other necessary attributes of sDNA_GH_Tool, instances know their own name
    # and nick name, in self.nick_name
    # self.tool_name.  When the instance is called, the version of sDNA
    # is looked up in opts['metas'], from its args.
    # 
    opts = options_manager.get_dict_of_Classes(
                               metas = dict(sDNAUISpec = 'sDNAUISpec'
                                           ,runsdnacommand = 'runsdnacommand'
                                           ,sDNA = None
                                           ,show_all = True
                                           #,strict 
                                           #,check_types
                                           #,add_new_opts
                                           )
                              ,options = dict(sDNAUISpec = options_manager.Sentinel('Module not imported yet')
                                             ,run_sDNA = options_manager.Sentinel('Module not imported yet')
                                             ,prepped_fmt = "{name}_prepped"
                                             ,output_fmt = "{name}_output"   
                                             # file extensions are actually optional in PyShp, 
                                             # but just to be safe and future proof
                                             ,python_exe = r'C:\Python27\python.exe'
                                             ,del_after_sDNA = True
                                             ,strict_no_del = False # for debugging
# Default installation path of Python 2.7.3 release (32 bit ?) 
# http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi copied from sDNA manual:
# https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/installation_usage.html 
                                             )
                              )


    def update_tool_opts_and_syntax(self, opts = None):
        if opts is None:
            opts = self.opts
        nick_name = self.nick_name
        tool_name = self.tool_name

        if sDNA_key(opts) != opts['metas'].sDNA:
            # Do the sDNA modules in the opts need updating?
            if self.import_sDNA_modules:
                self.import_sDNA_modules(opts)
                opts['metas'] = opts['metas']._replace(sDNA = sDNA_key(opts))
            else:
                self.logger.warning(
                            'Tool opts and syntax need updating but'
                           +' this tool cannot import sDNA modules. '
                           +' Waiting for next call to this method.'
                           )
                # Pointless updating tool_opts
                # to out of date modules that should be changed.
                return 'Failed to update sDNA, and modules need (re)importing. '

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
            self.error(msg)
            raise ValueError(msg)
                            
        self.input_spec = sDNA_Tool.getInputSpec()
        self.get_syntax = sDNA_Tool.getSyntax
        self.run_sDNA_command = run_sDNA_command     

        defaults_dict = OrderedDict((varname, default) for (varname
                                                           ,displayname
                                                           ,datatype
                                                           ,filtr
                                                           ,default
                                                           ,required
                                                           ) in self.input_spec  
                                   )         

        # tool_opts = get_tool_opts(self.nick_name, opts, self.tool_name)
        # if sDNA in tool_opts:
        #     tool_opts_dict = defaults_dict.update( tool_opts[sDNA]._asdict() ) 
        # else:
        #     tool_opts_dict = defaults_dict

        # namedtuple_class_name = (nick_name + '_'
        #                         +(self.tool_name if self.tool_name != nick_name
        #                                          else '') + '_'
        #                         +os.path.basename(sDNAUISpec.__file__).rpartition('.')[0]
        #                         )
        # self.logger.debug('Making tool opts namedtuple called %s ' % namedtuple_class_name)

        default_tool_opts = get_tool_opts(nick_name
                                         ,{}
                                         ,tool_name
                                         ,sDNA
                                         ,val = defaults_dict
                                         )
        update_opts(opts = opts
                   ,override = default_tool_opts
                   ,metas = opts['metas']
                   )

        # tool_opts[sDNA] = options_manager.namedtuple_from_dict(
        #                                        tool_opts_dict
        #                                       ,namedtuple_class_name
        #                                       ,strict = True
        #                                       ) 
        print(opts)
        # self.tool_opts = tool_opts
        # self.opts = opts
        self.sDNA = sDNA


        if metas.show_all:
            self.component_inputs += tuple(defaults_dict.keys())

            if 'advanced' not in defaults_dict:
                msg = "'advanced' not in defaults_dict"
                self.logger.warning(msg)
                warnings.showwarning(message = msg
                    ,category = UserWarning
                    ,filename = __file__ + self.__class__.__name__
                    ,lineno = 253
                    )


        if has_keywords(self.nick_name, keywords = ('prepare',)):
            self.retvals += ('gdm',)

        return 'Successfully updated syntax and tool_opts.  '



    def __init__(self
                ,tool_name
                ,nick_name
                ,opts = None
                ,import_sDNA_modules = None
                ):

        if opts is None:
            opts = self.opts  # the class property, tool default opts
        self.debug('Initialising Class.  Creating Class Logger.  ')
        self.tool_name = tool_name
        self.nick_name = nick_name
        self.import_sDNA_modules = import_sDNA_modules
        self.update_tool_opts_and_syntax(opts)



    
    
    component_inputs = ('file', 'config') 


    def __call__(self # the callable instance / func, not the GH component.
                ,f_name
                ,opts
                ,**kwargs
                ):
        #type(Class, str, dict, namedtuple) -> Boolean, str
        if opts is None:
            opts = self.opts  # the class property, tool default opts

        sDNA = opts['metas'].sDNA
        sDNAUISpec = opts['options'].sDNAUISpec



        if not hasattr(sDNAUISpec, self.tool_name): 
            raise ValueError(self.tool_name + 'not found in ' + sDNA[0])
        options = opts['options']

        if self.sDNA != sDNA:  # last sDNA this tool has seen != metas.sDNA
            outcome = self.update_tool_opts_and_syntax(opts)
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
            and f_name.rpartition('.')[2] in ['shp','dbf','shx']):  
            input_file = f_name

        self.logger.debug('input file == %s ' % input_file)
         


        output_file = tool_opts_sDNA.output
        if output_file == '':
            if self.tool_name == 'sDNAPrepare':
                output_file = options.prepped_fmt.format(name = input_file.rpartition('.')[0])
            else:
                output_file = options.output_fmt.format(name = input_file.rpartition('.')[0])
            output_file += '.shp'

        output_file = pyshp_wrapper.get_filename(output_file, options)

        input_args = tool_opts_sDNA._asdict()
        input_args.update(input = input_file, output = output_file)

        advanced = input_args.get('advanced', None)
        if not advanced:
            advanced = ';'.join(key if val is None else '%s=%s' % (key, val) 
                                for (key, val) in kwargs.items()
                               )
            input_args['advanced'] = advanced
            self.logger.info('Advanced command string == %s' % advanced)
        else:
            self.logger.debug('Advanced command string == %s' % advanced)

        syntax = self.get_syntax(input_args)
        run_sDNA = self.run_sDNA_command

        f_name = output_file

        command =   (options.python_exe 
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

        output_lines = subprocess.check_output(command)
        retcode = 0 # An error in subprocess.check_output will cease execution
                    # in the previous line.  Can set retcode =0 and proceed 
                    # safely to delete files.

        self.logger.info(output_lines)



        delete_shp_files_if_req(input_file
                               ,logger = self.logger
                               ,delete = options.del_after_sDNA
                               ,strict_no_del = options.strict_no_del
                               )

        if has_keywords(self.nick_name, keywords = ('prepare',)):
            gdm = None
            # To overwrite any inputted gdm (already used) in vals_dict
            # to makesure a subsequent ShapefileReader adds new Geometry


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
    if layers and isinstance(layers, str):
        layers = (layers,) if layers in doc_layers() else None


    def generator():
        #type( type[any]) -> list, list
        #
        # Groups first search.  If a special Usertext key on member objects 
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

    opts = options_manager.get_dict_of_Classes(metas = {}
                              ,options = dict(selected = False
                                             ,layer = ''
                                             ,shape_type = 'POLYLINEZ'
                                             ,merge_subdicts = True
                                             ,include_groups = False
                                             )
                              )

    component_inputs = ('config', 'selected', 'layer') 
    
    def __call__(self, opts = None, gdm = None):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts
        self.debug('Creating Class Logger.  ')

        options = opts['options']


        sc.doc = Rhino.RhinoDoc.ActiveDoc 
        
        #rhino_groups_and_objects = make_gdm(get_objs_and_OrderedDicts(options))
        tmp_gdm = gdm if gdm else OrderedDict()

            
        gdm = gdm_from_GH_Datatree.make_gdm(get_objs_and_OrderedDicts(
                                                 only_selected = options.selected
                                                ,layers = options.layer
                                                ,shp_type = options.shape_type
                                                ,include_groups = options.include_groups 
                                                ) 
                       )
        # lambda : {}, as Usertext is read elsewhere, in read_Usertext



        self.logger.debug('First objects read: \n' 
                         +'\n'.join( str(x) 
                                     for x in gdm.keys()[:3]
                                   )
                         )
        if gdm:
            self.debug('type(gdm[0]) == ' + type(gdm.keys()[0]).__name__ )


        if tmp_gdm:
            gdm = gdm_from_GH_Datatree.override_gdm(gdm
                                                   ,tmp_gdm
                                                   ,options.merge_subdicts
                                                   )
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
    opts = options_manager.get_dict_of_Classes(metas = {}
                        ,options = {}
                        )
    component_inputs = ('Geom',) 

    def __call__(self, gdm):
        #type(str, dict, dict) -> int, str, dict, list

        self.debug('Starting read_Usertext..  Creating Class logger. ')
        self.debug('type(gdm) == %s ' % type(gdm))
        self.debug('gdm[:3] == %s ' % {key : gdm[key] for key in gdm.keys()[:3]} )

        sc.doc = Rhino.RhinoDoc.ActiveDoc

        for obj in gdm:
            keys = rs.GetUserText(obj)
            gdm[obj].update( (key, rs.GetUserText(obj, key)) for key in keys )

        # read_Usertext_as_tuples = checkers.get_OrderedDict()
        # for obj in gdm:
        #     gdm[obj].update(read_Usertext_as_tuples(obj))


        sc.doc = ghdoc  
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)


    retvals = ('gdm',)
    component_outputs = ('Data', ) 



   


class ShapefileWriter(sDNA_GH_Tool):

    opts = options_manager.get_dict_of_Classes(metas = {}
                        ,options = dict(shape_type = 'POLYLINEZ'
                                       ,input_key_str = 'sDNA input name={name} type={fieldtype} size={size}'
                                       ,path = __file__
                                       ,output_shp = os.path.join( os.path.dirname(__file__)
                                                                 ,'tmp.shp'
                                                                 )
                                       )
                        )

    component_inputs = ('file', 'prj', 'Geom', 'Data', 'config') 

    def __call__(self, f_name, gdm, prj = None, opts = None):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts
        options = opts['options']
        self.debug('Creating Class Logger.  ')


        shp_type = options.shape_type            


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
            # target_doc = get_sc_doc_of_obj(obj)    
            # if target_doc:
            #     sc.doc = target_doc
            #     if is_shape(obj, shp_type):
            #         return [get_points_from_obj(obj, shp_type)]
            #     else:
            #         return []      
            #     #elif is_a_group_in_GH_or_Rhino(obj):
            # else:
            #     target_doc = get_sc_doc_of_group(obj)    
            #     if target_doc:
            #         sc.doc = target_doc                  
            #         return [get_points_from_obj(y, shp_type) 
            #                 for y in checkers.get_members_of_a_group(obj)
            #                 if is_shape(y, shp_type)]
            #     else:
            #         return []

        self.debug('Test points obj 0: %s ' % get_list_of_lists_from_tuple(gdm.keys()[0]) )

        def shape_IDer(obj):
            return obj #tupl[0].ToString() # uuid

        def find_keys(obj):
            return gdm[obj].keys() #tupl[1].keys() #rs.GetUserText(x,None)

        def get_data_item(obj, key):
            return gdm[obj][key] #tupl[1][key]

        if not f_name:  
            if (options.output_shp and isinstance(options.output_shp, str) and
                os.path.isfile( options.output_shp )  ):   
                #
                f_name = options.output_shp
            else:
                f_name = options.path.rpartition('.')[0] + '.shp'
                # Copy RhinoDoc or GH definition name without .3dm or .gh
                # file extensions are actually optional in PyShp, 
                # but just to be safe and future proof we remove
                # '.3dm'                                        
        self.logger.debug(f_name)

        (retcode
        ,f_name
        ,fields
        ,gdm) = pyshp_wrapper.write_iterable_to_shp(
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
            new_prj = f_name.rpartition('.')[0] + '.prj'
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

    opts = options_manager.get_dict_of_Classes(metas = {}
                        ,options = dict(new_geom = True
                                       ,uuid_field = 'Rhino3D_'
                                       ,sDNA_names_fmt = '{name}.shp.names.csv'
                                       ,prepped_fmt = '{name}_prepped'
                                       ,output_fmt = '{name}_output'
                                       ,del_after_read = False
                                       ,strict_no_del = False
                                       )
                        )
                        
    component_inputs = ('file', 'Geom') # existing 'Geom', otherwise new 
                                        # objects need to be created

    def __call__(self, f_name, gdm, opts = None):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts
        options = opts['options']
        self.debug('Creating Class Logger.  Reading shapefile... ')

        (shp_fields
        ,recs
        ,shapes
        ,bbox ) = pyshp_wrapper.get_fields_recs_and_shapes( f_name )

        self.debug('gdm == %s ' % gdm)

        self.debug('recs[0].as_dict() == %s ' % recs[0].as_dict())

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
            
            objs_maker = pyshp_wrapper.objs_maker_factory() 
            shapes_to_output = (objs_maker(shp.points) for shp in shapes )
        else:
            #elif isinstance(gdm, dict) and len(gdm) == len(recs):
            # an override for different number of overrided geom objects
            # to shapes/recs opens a large a can of worms.  Unsupported.

            self.logger.debug('Geom data map matches shapefile.  ')

            shapes_to_output = list(gdm.keys()) # Dict view in Python 3

        # else:
        #     # Unsupported until can round trip uuid through sDNA 
        #     # objs_maker = get_shape_file_rec_ID(options.uuid_field) 
        #     # # key_val_tuples
        #     # i.e. if options.uuid_field in fields but also otherwise
        #     msg =   ('Geom data map and shapefile have unequal'
        #             +' lengths len(gdm) == %s ' % len(gdm))
        #             +' len(recs) == %s ' % len(recs))
        #             +' (or invalid gdm), and bool(new_geom)'
        #             +' != True'
        #             )
        #     self.logger.error(msg)
        #     raise ValueError(msg)
   

        shp_file_gen_exp  = itertools.izip(shapes_to_output
                                          ,(rec.as_dict() for rec in recs)
                                          )
      
        sc.doc = Rhino.RhinoDoc.ActiveDoc
        gdm = gdm_from_GH_Datatree.make_gdm(shp_file_gen_exp)
        sc.doc = ghdoc 
        
        file_name = f_name.rpartition('.')[0]
        csv_f_name = options.sDNA_names_fmt.format(name = file_name)
        #sDNA_fields = {}
        if os.path.isfile(csv_f_name):
# sDNA writes this file in simple 'w' mode, 
# Line 469
# https://github.com/fiftysevendegreesofrad/sdna_open/blob/master/arcscripts/sdna_environment.py
            with open(csv_f_name, 'r') as f:  
                #sDNA_fields = [OrderedDict( line.split(',') for line in f )]
                abbrevs = [line.split(',')[0] for line in f ]
            if not options.strict_no_del:
                delete_file(csv_f_name, self.logger)


        self.logger.debug('bbox == %s ' % bbox)

        delete_shp_files_if_req(f_name
                               ,logger = self.logger
                               ,delete = options.del_after_read
                               ,strict_no_del = options.strict_no_del
                               ,regexes = (funcs.make_regex(options.output_fmt)
                                          ,funcs.make_regex(options.prepped_fmt)
                                          )
                               )


        retcode = 0

        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)


    retvals = 'retcode', 'gdm', 'abbrevs', 'fields', 'bbox'
    component_outputs = ('Geom', 'Data') + retvals[1:]
               




class UsertextWriter(sDNA_GH_Tool):

    opts = options_manager.get_dict_of_Classes(metas = {}
                        ,options = dict(uuid_field = 'Rhino3D_'
                                       ,output_key_str = 'sDNA output={name} run time={datetime}'
                                       ,overwrite_UserText = True
                                       ,max_new_keys = 10
                                       ,dupe_key_suffix = ''
                                       ,suppress_overwrite_warning = False
                                       )
                        )
                        

    component_inputs = ('Geom', 'Data')


    def __call__(self, gdm, opts):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts        
        options = opts['options']

        date_time_of_run = asctime()
        self.debug('Creating Class logger at: %s ' % date_time_of_run)


        def write_dict_to_UserText_on_Rhino_obj(d, rhino_obj):
            #type(dict, str) -> None
            if not isinstance(d, dict):
                msg = 'dict required by write_dict_to_UserText_on_Rhino_obj'
                self.logger.error(msg)
                raise TypeError(msg)
            
            #if is_an_obj_in_GH_or_Rhino(rhino_obj):
                # Checker switches GH/ Rhino context
                 
            existing_keys = checkers.get_obj_keys(rhino_obj)
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
            write_dict_to_UserText_on_Rhino_obj(val, key)

        sc.doc = ghdoc  
        
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)
    
    retvals = ()
    component_outputs = () 



class DataParser(sDNA_GH_Tool):


    opts = options_manager.get_dict_of_Classes(metas = {}
                              ,options = dict(
                                     field = 'BtEn'
                                    ,plot_min = options_manager.Sentinel('plot_min is automatically calculated by sDNA_GH unless overridden.  ')
                                    ,plot_max = options_manager.Sentinel('plot_max is automatically calculated by sDNA_GH unless overridden.  ')
                                    ,re_normaliser = 'linear'
                                    ,sort_data = False
                                    ,num_classes = 8
                                    ,class_bounds = [options_manager.Sentinel('class_bounds is automatically calculated by sDNA_GH unless overridden.  ')]
                                    # e.g. [2000000, 4000000, 6000000, 8000000, 10000000, 12000000]
                                    ,class_spacing = 'quantile'
                                    ,_valid_class_spacings = funcs.valid_re_normalisers + ('quantile', 'combo', 'max_deltas')
                                    ,base = 10 # for Log and exp
                                    ,colour_as_class = False
                                    ,locale = '' # '' => User's own settings.  Also in DataParser
                                    # e.g. 'fr', 'cn', 'pl'. IETF RFC1766,  ISO 3166 Alpha-2 code
                                    ,num_format = '{:.5n}'
                                    ,first_leg_tag_str = 'below {upper}'
                                    ,gen_leg_tag_str = '{lower} - {upper}'
                                    ,last_leg_tag_str = 'above {lower}'
                                    ,exclude = False
                                    ,remove_overlaps = True
                                    ,suppress_small_classes_error = False
                                    ,suppress_class_overlap_error = False
                                    )
                              )
    assert opts['options'].re_normaliser in funcs.valid_re_normalisers
                        

    def __init__(self):
        self.debug('Initialising Class.  Creating Class Logger. ')
        self.component_inputs = ('Geom', 'Data', 'field', 'plot_max'
                                ,'plot_min', 'num_classes', 'class_spacing', 'class_bounds')
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

        plot_min, plot_max = options.plot_min, options.plot_max
        if (isinstance(plot_min, Number)  
           and isinstance(plot_max, Number) 
           and plot_min < plot_max ):
            #
            self.info('Valid max and min override will be used. ')
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
            self.debug('Manually calculating max and min. '
                      +'No valid override found. '
                      )
            data = OrderedDict( (obj, val[field]) 
                                for obj, val in gdm.items() 
                              )
            x_min, x_max = min(data.values()), max(data.values())
        # bool(0) is False so in case x_min==0 we can't use if options.plot_min
        # so test isinstance of Number ABC. 
        #
        # x_min & x_max are not stored in options, so sDNA_GH will carry on 
        # auto calculating min and max on future runs.  Once they are
        # overridden, the user must set them to an invalid override 
        # (e.g. max <= min) to go back to auto-calculation.

        self.logger.debug('data.values() == ' 
                         +str(data.values()[:3]) 
                         +' ... ' 
                         +str(data.values()[-3:])
                         )



        use_manual_classes = (isinstance(options.class_bounds, list)
                             and all( isinstance(x, Number) 
                                               for x in options.class_bounds
                                    )
                             )

        if options.sort_data or (
           not use_manual_classes 
           and options.class_spacing in ('quantile', 'max_deltas', 'combo')  ):
            # 
            data = OrderedDict( sorted(data.items()
                                      ,key = lambda tupl : tupl[1]
                                      ) 
                              )

        param={}
        param['exponential'] = param['logarithmic'] = options.base

        def quantile_classes():
            m = options.num_classes
            n = len(data)
            class_size = n // m
            if class_size < 2:
                msg = 'Class size == %s  is less than 2 ' % class_size
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

            # assert gdm is already sorted
            class_bound_indices = list(range(class_size, m*class_size, class_size))
            data_vals = data.values()
            #
            class_bounds = [data_vals[index] for index in class_bound_indices] 
            # class_bounds = [ val for val in 
            #                  data.values()[class_size:m*class_size:class_size] 
            #                ]  
                            # classes include their lower bound
            #
            count_bound_counts = Counter(class_bounds)
            class_overlaps = [val for val in count_bound_counts
                                if count_bound_counts[val] > 1
                                ]

            if class_overlaps:
                msg = 'Class overlaps at: ' + ' '.join(class_overlaps)
                if options.remove_overlaps:
                    for overlap in class_overlaps:
                        pass
                        #remove 
                        class_bounds.remove(overlap)
                if options.class_spacing == 'combo':
                    msg += ' but in combo mode. Setting classes around max_deltas'
                    self.logger.warning(msg)
                    class_bounds = funcs.class_bounds_at_max_deltas()
                else:
                    msg += (' Maybe try a) fewer classes,'
                            +' b) class_spacing == combo, or'
                            +' c) class_spacing == max_deltas'
                            )
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
            #
            self.logger.debug('num class boundaries == ' 
                                + str(len(class_bounds))
                                )
            self.logger.debug(options.num_classes)
            self.logger.debug(n)
            assert len(class_bounds) + 1 == options.num_classes

            msg = 'x_min == %s \n' % x_min
            msg += 'class bounds == %s \n' % class_bounds
            msg += 'x_max == %s ' % x_max
            self.logger.debug(msg)

            return class_bounds

        if use_manual_classes:
            class_bounds = options.class_bounds
            self.logger.info('Using manually specified'
                            +' inter-class boundaries. '
                            )
            #
        elif options.class_spacing == 'max_deltas':
            class_bounds = funcs.class_bounds_at_max_deltas()
        elif options.class_spacing in ('quantile', 'combo'):
            class_bounds = quantile_classes()
        else: 
            class_bounds = [funcs.splines[options.class_spacing](i
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


        if options.re_normaliser not in funcs.valid_re_normalisers:
            # e.g.  'linear', exponential, logarithmic
            msg = 'Invalid re_normaliser : %s ' % options.re_normaliser
            self.error(msg)
            raise ValueError(msg)

        def re_normalise(x, p = param.get(options.re_normaliser, 'Not used')):
            spline = funcs.splines[options.re_normaliser]
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

        x_min_str = options.num_format.format(x_min) 
        upper_str = options.num_format.format(min( class_bounds ))
        mid_pt_str = options.num_format.format( mid_points[0] )

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
            
            lower_str = options.num_format.format(lower_bound)
            upper_str = options.num_format.format(upper_bound)
            mid_pt_str = options.num_format.format(class_mid_point)
            # e.g. gen_leg_tag_str = '{lower} - {upper}' # also supports {mid}
            legend_tags += [options.gen_leg_tag_str.format(lower = lower_str
                                                          ,upper = upper_str
                                                          ,mid_pt = mid_pt_str 
                                                          )
                           ]

        lower_str = options.num_format.format(max( class_bounds ))
        x_max_str = options.num_format.format(x_max)
        mid_pt_str = options.num_format.format(mid_points[-1])

        # e.g. last_leg_tag_str = 'above {lower}'
        legend_tags += [options.last_leg_tag_str.format(lower = lower_str
                                                       ,upper = x_max_str 
                                                       ,mid_pt = mid_pt_str 
                                                       )        
                       ]                                                       

        assert len(legend_tags) == options.num_classes == len(mid_points)

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
    component_outputs = retvals[:2] + ('Data', 'Geom') + retvals[2:]



class ObjectsRecolourer(sDNA_GH_Tool):

    opts = options_manager.get_dict_of_Classes(metas = {}
                        ,options = dict(field = 'BtEn'
                                       ,Col_Grad = False
                                       ,Col_Grad_num = 5
                                       ,rgb_max = (155, 0, 0) #990000
                                       ,rgb_min = (0, 0, 125) #3333cc
                                       ,rgb_mid = (0, 155, 0) # guessed
                                       ,line_width = 4 # milimetres? 
                                       ,first_leg_tag_str = 'below {upper}'
                                       ,gen_leg_tag_str = '{lower} - {upper}'
                                       ,last_leg_tag_str = 'above {lower}'
                                       ,leg_extent = options_manager.Sentinel('leg_extent is automatically calculated by sDNA_GH unless overridden.  ')
                                       # [xmin, ymin, xmax, ymax]
                                       ,bbox = options_manager.Sentinel('bbox is automatically calculated by sDNA_GH unless overridden.  ') 
                                       # [xmin, ymin, xmax, ymax]

                                       )
                        )
                        
    def __init__(self):
        self.debug('Initialising Class.  Creating Class Logger. ')
        self.parse_data = DataParser()
        self.GH_Gradient_preset_names = {0 : 'EarthlyBrown'
                                        ,1 : 'Forest'
                                        ,2 : 'GreyScale'
                                        ,3 : 'Heat'
                                        ,4 : 'SoGay'
                                        ,5 : 'Spectrum'
                                        ,6 : 'Traffic'
                                        ,7 : 'Zebra'
                                        }

    
    component_inputs = ('plot_min', 'plot_max', 'Data', 'Geom', 'bbox', 'field')

    def __call__(self, gdm, opts, plot_min, plot_max, bbox):
        #type(str, dict, dict) -> int, str, dict, list
        # Note!  opts can be mutated.
        if opts is None:
            opts = self.opts
        options = opts['options']
        
        field = options.field
        objs_to_parse = OrderedDict((k, v) for k, v in gdm.items()
                                   if isinstance(v, dict) and field in v    
                                   )  # any geom with a normal gdm dict of keys / vals
        if objs_to_parse or plot_min is None or plot_max is None:
            x_min, x_max, gdm_in = self.parse_data(objs_to_parse, opts)
                                                                            
        else:
            self.debug('Skipping parsing')
            gdm_in = {}
            x_min, x_max = plot_min, plot_max

        self.logger.debug('x_min == %s ' % x_min)
        self.logger.debug('x_max == %s ' % x_max)

        objs_to_get_colour = OrderedDict( (k, v) for k, v in gdm.items()
                                                if isinstance(v, Number) 
                                        )
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
                linearly_interpolate = funcs.enforce_bounds(funcs.linearly_interpolate)
                return grad().ColourAt(linearly_interpolate( x
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
                rgb_col =  funcs.map_f_to_three_tuples(funcs.three_point_quad_spline
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

        objs_to_recolour = OrderedDict( (k, v) for k, v in gdm.items()
                                            if isinstance(v, Colour)  
                                    )
            
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
            self.logger.debug('obj, is_uuid == %s, %s ' % (obj, is_uuid(obj))) 
            
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
                except TypeError:
                    GH_objs_to_recolour[obj] = new_colour 
                    
        sc.doc = ghdoc
            
            # if is_uuid(obj): 
            #     target_doc = get_sc_doc_of_obj(obj)    

            #     if target_doc:
            #         sc.doc = target_doc
            #         if target_doc == ghdoc:
            #             GH_objs_to_recolour[obj] = new_colour 
            #         #elif target_doc == Rhino.RhinoDoc.ActiveDoc:
            #         else:
            #             rs.ObjectColor(obj, new_colour)
            #             Rhino_objs_to_recolour.append(obj)

            #     else:

            #         msg =   ('sc.doc == %s ' % sc.doc) 
            #                 +' i.e. neither Rhinodoc.ActiveDoc '
            #                 +'nor ghdoc'
            #                 )
            #         self.logger.error(msg)
            #         raise ValueError(msg)

            # elif any(  bool(re.match(pattern, str(obj)))
            #             for pattern in legend_tag_patterns ):
            #     sc.doc = ghdoc
            #     legend_tags[obj] = rs.CreateColor(new_colour) # Could glitch if dupe
            # else:
            #     self.logger.debug(obj)
            #     self.logger.debug('is_uuid(obj) == %s ' % is_uuid(obj)))
            #     msg = 'Valid colour in Data but no geom obj or legend tag.'
            #     self.logger.error(msg)
            #     raise NotImplementedError(msg)

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




        if (bbox or not isinstance(options.leg_extent, (options_manager.Sentinel, type(None)))
                 or not isinstance(options.bbox, (options_manager.Sentinel, type(None)))):
            if not isinstance(options.leg_extent, options_manager.Sentinel) and options.leg_extent:
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
                    bbox = [bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax] = options.bbox

                leg_width = math.sqrt((bbox_xmax - bbox_xmin)**2 
                                     +(bbox_ymax - bbox_ymin)**2
                                     )
                tag_height = max( 10, 0.4 * leg_width / 0.7)
                leg_height = options.num_classes * tag_height * 1.04
                legend_xmin = bbox_xmax - leg_width
                legend_ymin = bbox_ymax - leg_height

                # legend_xmin = bbox_xmin + (1 - 0.4)*(bbox_xmax - bbox_xmin)
                # legend_ymin = bbox_ymin + (1 - 0.4)*(bbox_ymax - bbox_ymin)
                legend_xmax, legend_ymax = bbox_xmax, bbox_ymax
                
                self.logger.debug('bbox == %s ' % bbox)


            plane = rs.WorldXYPlane()
            leg_frame = rs.AddRectangle( plane
                                        ,legend_xmax - legend_xmin
                                        ,legend_ymax - legend_ymin 
                                        )

            self.logger.debug('Rectangle width * height == ' 
                                +str(legend_xmax - legend_xmin)
                                +' * '
                                +str(legend_ymax - legend_ymin)
                                )


            rs.MoveObject(leg_frame, [1.07*bbox_xmax, legend_ymin])


        else:
            self.logger.info('No legend rectangle dimensions.  ')
            leg_frame = None

    


        self.logger.debug(leg_frame)


        gdm = GH_objs_to_recolour
        leg_cols = list(legend_tags.values())
        leg_tags = list(legend_tags.keys())


        sc.doc =  ghdoc 
        sc.doc.Views.Redraw()

        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)
    
    retvals = 'gdm', 'leg_cols', 'leg_tags', 'leg_frame', 'opts'
    component_outputs = ('Geom', 'Data') + retvals[1:]
          # To recolour GH Geom with a native Preview component


class sDNA_GeneralDummyTool(sDNA_GH_Tool):
    component_inputs = ('tool',)

    def __call__(self, *args, **kwargs):
        raise NotImplementedError('this function should never run '
                                 +' (there may be a problem with sDNA_General). '
                                 )
    component_outputs = ()


toml_no_tuples = options_manager.toml_types[:]
if tuple in toml_no_tuples:
    toml_no_tuples.remove(tuple)
#Internally in sDNA_GH opts, tuples are read only.

def parse_values_for_toml(x, supported_types = toml_no_tuples):
    #type(type[any]) -> type[any]
    """ Strips out keys and values for which the key is not a string 
        or contains whitespace, or for which the value is not a 
        supported type.  
    """
    if isinstance(x, list):
        return [parse_values_for_toml(y) for y in x]
    if isinstance(x, dict):
        return OrderedDict((key, parse_values_for_toml(val)) 
                            for key, val in x.items() 
                            if (isinstance(key, basestring) 
                                and all(not char.isspace() for char in key) 
                                and isinstance(val, supported_types)
                               )
                          )
    return x



class ConfigManager(sDNA_GH_Tool):

    """ Updates opts objects, and loads and saves config.toml files.  

        All args connected to its input Params are loaded into opts,
        even if go is False.  

        If go is True, tries to save the options. 
        If save_to is a valid file path ending 
        in toml, the opts are saved to it (overwriting an existing file), 
        e.g. creating a project specific options file.  
        Otherwise if save_to is not specified and no installation wide config.toml 
        file is found (in the sDNA_GH installation directory 
        %appdata%/Grasshopper/UserObjects/sDNA_GH) e.g. on the first use of
        sDNA_GH after installation, string keyed str, bool, int, float, list, tuple, and dict 
        values in opts are saved to the installation wide config.toml.
    """

    save_to = os.path.join(os.path.dirname(os.path.dirname(__file__))
                          ,'config.toml'
                          ) 

    opts = options_manager.get_dict_of_Classes(metas = dict(config = save_to)
                                              ,options = {}
                                              )





    component_inputs = ('save_to' # Primary Meta
                       ,'python_exe'
                       ,'sDNA_paths'
                       ,'auto_get_Geom' 
                       ,'auto_read_Usertext'
                       ,'auto_write_Shp'
                       ,'auto_read_Shp'
                       ,'auto_plot_data'

                       )

    def __call__(self, save_to, opts):
        self.debug('Starting class logger')
        options = opts['options']
        metas = opts['metas']
        self.debug('options == %s ' % options)
        if ( (not isinstance(save_to, str) or
              not save_to.endswith('.toml') or
              not os.path.isfile(save_to)) 
             and not os.path.isfile(self.save_to)):
            #
            save_to = self.save_to
            self.logger.warning('Saving opts to installation wide save_to.toml')
        parsed_dict = parse_values_for_toml(opts)        
        options_manager.save_toml_file(save_to, parsed_dict)

        
        retcode = 0
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)
    retvals = ('retcode',)
    component_outputs = ()

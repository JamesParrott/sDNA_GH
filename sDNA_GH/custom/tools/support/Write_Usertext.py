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

__author__ = 'James Parrott'
__version__ = '3.0.0.alpha_3'

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
    
    for key, val in d.items():

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

        rs.SetUserText(rhino_obj, UserText_key_name, str(val), False)          



class UsertextWriter(sDNA_GH_Tool):

    Options = UsertextWriterOptions

    component_inputs = ('Geom', 'Data', 'output_key_str')

    param_infos = sDNA_GH_Tool.param_infos + (
                   ('output_key_str', add_params.ParamInfo(
                             param_Class = Param_String
                            ,Description = ('The format string of the Usertext keys. '
                                           +'Supports "{name}" and "{datetime}" fields. '
                                           +'Default: %(output_key_str)s'
                                           )
                            )),
                   )
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



        





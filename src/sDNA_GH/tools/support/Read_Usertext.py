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
__version__ = '3.0.0.alpha_4'

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
                keys = rs.GetUserText(obj)
                # try:
                #     keys = rs.GetUserText(obj)
                # except ValueError:
                #     keys =[]
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



   
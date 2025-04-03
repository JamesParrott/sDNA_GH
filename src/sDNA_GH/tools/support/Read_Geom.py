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

from ... import data_cruncher 
from ...skel.basic.ghdoc import ghdoc
from ...skel.tools.helpers import checkers
from ...skel.tools.helpers import funcs
from ...skel.tools.helpers import rhino_gh_geom
from ...skel.tools import runner                                       
from ...skel import add_params
from ...skel import builder
from ... import options_manager
from ... import pyshp_wrapper
from ... import logging_wrapper
from ... import gdm_from_GH_Datatree
from ... import launcher
from ..sdna import sDNA_GH_Tool


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
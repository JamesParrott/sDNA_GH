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
               

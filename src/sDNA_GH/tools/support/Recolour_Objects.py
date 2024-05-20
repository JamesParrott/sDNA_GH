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


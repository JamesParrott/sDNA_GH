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




QUANTILE_METHODS = {'simple' : data_cruncher.simple_quantile
                   ,'max_deltas' : data_cruncher.class_bounds_at_max_deltas
                   ,'Equal Count (Quantile)' : data_cruncher.quantile_l_to_r
                   ,'quantile' : data_cruncher.spike_isolating_quantile
                   ,'geometric' : data_cruncher.geometric
                   ,'Natural Breaks (Jenks)' : data_cruncher.fisher_jenks
                   }







def search_for_field(fields, prefix):
    #type(Iterable[str], str) -> str
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
        field_prefix = 'Bt'
        plot_min = options_manager.Sentinel('plot_min is automatically '
                                           +'calculated by sDNA_GH unless '
                                           +'overridden.  '
                                           )
        plot_max = options_manager.Sentinel('plot_max is automatically '
                                           +'calculated by sDNA_GH unless '
                                           +'overridden.  '
                                           )
        re_normaliser = 'none'
        sort_data = False
        num_classes = 8
        inter_class_bounds = [options_manager.Sentinel('inter_class_bounds is automatically '
                                                +'calculated by sDNA_GH unless '
                                                +'overridden.  '
                                                )
                       ]
        # e.g. [2000000, 4000000, 6000000, 8000000, 10000000, 12000000]
        class_spacing = 'quantile'
        VALID_RE_NORMALISERS = data_cruncher.VALID_RE_NORMALISERS
        VALID_CLASS_SPACINGS = VALID_RE_NORMALISERS + tuple(QUANTILE_METHODS.keys())

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
        y_max = None
        y_min = None
        
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
                                           +'WARNING: without care, this may allow unfair comparisons '
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
                                           +'Outlying values higher than plot_max are set to plot_max '
                                           +'if exclude is false, or omitted (as are their '
                                           +'objects). '
                                           +"Automatically calculated to the data's actual max if unset."
                                           )
                            ))
                  ,('plot_min', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('Minimum data value to parse. '
                                           +'Outlying values lower than plot_min are set to plot_min '
                                           +'if exclude is false, or omitted (as are their '
                                           +'objects). '
                                           +"Automatically calculated to the data's actual min if unset."
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
                  ,('re_normaliser', add_params.ParamInfo(
                             param_Class = Param_String
                            ,Description = ('Name of method to use to '
                                           +'renormalise the data. '
                                           +'Allowed Values: '
                                           +'%(VALID_RE_NORMALISERS)s.  ' 
                                           +'Default: %(re_normaliser)s'
                                           ) 
                            ))
                  ,('y_max', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = 'Value (if any) to re_normalise plot_max to. '
                            ))
                  ,('y_min', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = 'Value (if any) to re_normalise plot_min to. '
                            ))
                  ,('colour_as_class', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: Replace each data value with the '
                                           +'value of the midpoint of its class.  ' 
                                           +"false: don't. "
                                           +'Default: %(colour_as_class)s' 
                                           )
                            )) 
                  # Output Param          
                  ,('mid_points', add_params.ParamInfo(
                             param_Class = Param_ScriptVariable
                            ,Description = ('Mid-points of the classes in the '
                                           +'legend. '
                                           )
                            ))
                                               )

    def make_field_selector(self, gdm, options):

        self.field = options.field or self.Options.field
        prefix = options.field_prefix or self.Options.field_prefix

        def select(val):
            #type( type[any] ) -> Number
            
            if isinstance(val, Number):
                return val

            if not isinstance(val, dict):
                msg = 'val: %s is not a dict or a Number (type(val) == %s)' 
                msg %= (val, type(val))
                self.logger.error(msg)
                raise TypeError(msg)

            if self.field is None:
                self.field = search_for_field(
                    fields = (k
                              for sub_gdm in gdm
                              for dict_ in sub_gdm.values()
                              for k in dict_
                             )
                    ,prefix = prefix
                    )

            if self.field not in val:
                msg = 'Key for field: %s not found in val: %s' % (self.field, val)
                self.logger.error(msg)
                raise KeyError(msg)
            return val[self.field]
        
        return select

    component_inputs = ('Geom', 'Data', 'field', 'field_prefix', 'plot_max', 'plot_min' 
                       ,'num_classes', 'class_spacing', 'inter_class_bounds'
                       ,'re_normaliser', 'y_max', 'y_min', 'colour_as_class'
                       )
    #
    # Geom is essentially unused in this function, except if it is sorted when sort_data = True
    # or class_spacing == 'quantile', and that the legend tags
    # are appended to Geom, to colour them in exactly the same way as the 
    # objects.
    #

    def filter_or_bound_data_from_selected_field(self, gdm, options):
        # This method may set self.field.  
        select_data_pt_or_field = self.make_field_selector(gdm, options)

        user_min, user_max = options.plot_min, options.plot_max
        if data_cruncher.max_and_min_are_valid(user_max, user_min):
            #
            self.logger.info('Valid max and min override will be used. ')
            #
            x_min, x_max = user_min, user_max
            if options.exclude:
                data = OrderedDict( (obj, select_data_pt_or_field(val)) 
                                    for sub_gdm in gdm
                                    for obj, val in sub_gdm.items()                                    
                                    if x_min <= select_data_pt_or_field(val) <= x_max
                                  )
            else: # exclude == False => enforce bounds, cap and collar
                data = OrderedDict( (obj, min(x_max, max(x_min, select_data_pt_or_field(val)))) 
                                    for sub_gdm in gdm
                                    for obj, val in sub_gdm.items()                                    
                                  )

        else:
            self.logger.debug('Manually calculating max and min. '
                             +'No valid override found. '
                             )
            data = OrderedDict( (obj, select_data_pt_or_field(val)) 
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

        self.logger.debug('len(data)== %s ' % len(data.values()))




        return data, x_min, x_max


    def classify_data(self, data, x_min, x_max, options):


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
                                    ,lineno = 2740
                                    )
            else:
                self.logger.error(msg)
                raise ValueError(msg)



        if self.use_manual_classes:
            inter_class_bounds = options.inter_class_bounds
            self.logger.info('Using manually specified'
                            +' inter-class boundaries. '
                            )
        elif options.class_spacing in QUANTILE_METHODS:
            self.logger.debug('Using: %s class calculation method.' % options.class_spacing)
            inter_class_bounds = QUANTILE_METHODS[options.class_spacing](
                                                                     data = data.values()
                                                                    ,num_classes = m
                                                                    ,options = options
                                                                    )

        else: 
            inter_class_bounds = [data_cruncher.basic_class_spacings[options.class_spacing](
                                                           i
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
                                    ,lineno = 2792
                                    )
            else:
                self.logger.error(msg)
                raise ValueError(msg)






        self.logger.debug('num class boundaries == ' 
                    + str(len(inter_class_bounds))
                    )
        self.logger.debug('m == %s' % m)
        self.logger.debug('n == %s' % n)
        if len(inter_class_bounds) + 1 < m:
            self.logger.warning(
                           'It has only been possible to classify data into '
                          +'%s distinct classes, not %s' % (len(inter_class_bounds) + 1, m)
                          )

        msg = 'x_min == %s \n' % x_min
        msg += 'class bounds == %s \n' % inter_class_bounds
        msg += 'x_max == %s ' % x_max
        self.logger.debug(msg)

        return inter_class_bounds

    def mid_points(self, inter_class_bounds, x_min, x_max):
        
        if inter_class_bounds:
            mid_points = [0.5*(x_min + min(inter_class_bounds))]
            mid_points += [0.5*(x + y) for x, y in itertools.pairwise(inter_class_bounds)]
            mid_points += [0.5*(x_max + max(inter_class_bounds))]
        else:
            mid_points = [0.5*(x_min + x_max)]
        self.logger.debug(mid_points)

        return mid_points

    def legend_tags(self, inter_class_bounds, mid_points, x_min, x_max, options):

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
            for lower_bound, class_mid_point, upper_bound in zip(
                                                         inter_class_bounds[0:-1]
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

        return legend_tags


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

        self.use_manual_classes = (options.inter_class_bounds and
                                   isinstance(options.inter_class_bounds, list) and
                                   all(isinstance(x, Number) 
                                       for x in options.inter_class_bounds
                                      )
                                   )

        data, x_min, x_max = self.filter_or_bound_data_from_selected_field(gdm, options)


        if options.sort_data or (
           not self.use_manual_classes 
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


        inter_class_bounds = self.classify_data(data, x_min, x_max, options)


        


        if options.colour_as_class:

        
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

                return 0.5*(least_upper_bound + highest_lower_bound)


            for obj, data_val in data.items():
                data[obj] = class_mid_point(data_val)



        if (x_max - x_min >= options.tol and
            options.re_normaliser in data_cruncher.splines):
            #



            param={}
            param['exponential'] = param['logarithmic'] = options.base

            spline = data_cruncher.splines[options.re_normaliser]
            p = param.get(options.re_normaliser, 'Not used')

            y_min = x_min if options.y_min is None else options.y_min 
            y_max = x_max if options.y_max is None else options.y_max


            def renormalise(x):
                return spline(
                         x
                        ,x_min
                        ,p   # base or x_mid.  Can't be a kwarg.
                        ,x_max
                        ,y_min = y_min
                        ,y_max = y_max
                        )

            for i, inter_class_bound in enumerate(inter_class_bounds):
                inter_class_bounds[i] = renormalise(inter_class_bound)

            for obj, data_val in data.items():
                data[obj] = renormalise(data_val)

            x_max, x_min = y_max, y_min

        
        mid_points = self.mid_points(
                             inter_class_bounds
                            ,x_min
                            ,x_max
                            )

        legend_tags = self.legend_tags(
                             inter_class_bounds
                            ,mid_points
                            ,x_min
                            ,x_max
                            ,options
                            )

        gen_exp = itertools.chain(data.items(), zip(legend_tags, mid_points))

        gdm = gdm_from_GH_Datatree.GeomDataMapping(gen_exp)

        # rename for retvals
        plot_min, plot_max, field = x_min, x_max, self.field
        
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = 'plot_min', 'plot_max', 'gdm', 'field', 'mid_points', 'inter_class_bounds'
    component_outputs = retvals[:2] + ('Data', 'Geom') + retvals[-3:]


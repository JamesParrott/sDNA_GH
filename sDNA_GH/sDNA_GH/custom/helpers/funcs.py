#! Grasshopper Python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys
import os
import logging
from math import log
from tabnanny import check
if sys.version_info.major <= 2 or (
   sys.version_info.major == 3 and sys.version_info.minor <= 3):
    from collections import Sequence
else:
    from collections.abc import Sequence

import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

from ..skel.basic.ghdoc import ghdoc


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def get_path(inst = None):
    #type(dict, type[any]) -> str
    #refers to `magic' global ghdoc so needs to be in main
    
    path = Rhino.RhinoDoc.ActiveDoc.Path
                    
    if not isinstance(path, str) or not os.path.isfile(path):
        try:
            path = ghdoc.Path
        except:
            try:
                path = inst.ghdoc.Path 
            except:
                try:
                    path = sc.doc.Path
                except:
                    path = None
        finally:
            if not path:
                path = None
    
    return path


def first_item_if_seq(l, null_container = {}):
    #type(type[any])-> dict
    #hopefully!
    if not l:
        return null_container        

    if isinstance(l, Sequence) and not isinstance(l, str):
        l = l[0]
    
    return l


def make_regex(pattern):
    # type (str) -> str
    # Makes a regex from its opposite: a format string.  
    # Turns format string fields: {name} 
    # into regex named capturing groups: (?P<name>.*)
    #
    the_specials = '.^$*+?[]|():!#<='
    for c in the_specials:
        pattern = pattern.replace(c,'\\' + c)
    pattern = pattern.replace( '{', r'(?P<' ).replace( '}', r'>.*)' )
    return r'\A' + pattern + r'\Z'

def check_strictly_less_than(a, b, a_name = 'a', b_name = 'b'):
    #type(Number, Number, str, str) -> None
    if a >= b:
        msg = str(a) + ' == ' + a_name + ' >= ' + b_name + ' == ' + str(b)
        logger.error(msg)
        raise ValueError(msg)

def enforce_bounds(spline):
    def wrapper(x, x_min, x_mid, x_max, y_min, y_max):
        x = min(x_max, max(x_min, x))
        return spline(x, x_min, x_mid, x_max, y_min, y_max)
    return wrapper


def linearly_interpolate(x, x_min, x_mid, x_max, y_min, y_max):
    # type(Number, Number, Number, Number, Number, Number) -> Number
    check_strictly_less_than(x_min, x_max, 'x_min', 'x_max')
    return y_min + ( (y_max - y_min) * (x - x_min) / (x_max - x_min) )

def check_not_eq(a, b, a_name = 'a', b_name = 'b'):
    #type(Number, Number, str, str) -> None
    if a == b:
        msg = str(a) + ' == ' + a_name + ' == ' + b_name + ' == ' + str(b)
        logger.error(msg)
        raise ValueError(msg)

def quadratic_mid_spline(x, x_min, x_mid, x_max, y_min, y_max):
    # type(Number, Number, Number, Number, Number, Number) -> Number
    check_not_eq(x_min, x_mid, 'x_min', 'x_mid')
    check_not_eq(x_mid, x_max, 'x_mid', 'x_max')
    retval = y_max*((x - x_max)*(x - x_min)/((x_mid - x_max)*(x_mid - x_min)))
    retval += y_min
    return retval


def log_spline(x, x_min, base, x_max, y_min, y_max):        
    # type(Number, Number, Number, Number, Number, Number) -> Number
    check_strictly_less_than(x_min, x_max, 'x_min', 'x_max')
    log_2 = log(2, base)

    return y_min + (y_max / log_2) * log(1 + ( (x-x_min)/(x_max-x_min) )
                                        ,base
                                        )


def exp_spline(x, x_min, base, x_max, y_min, y_max):
    # type(Number, Number, Number, Number, Number, Number) -> Number
    check_strictly_less_than(x_min, x_max, 'x_min', 'x_max')


    return y_min + ( -1 + pow(base
                             ,((x - x_min)/(x_max - x_min))*log(1 + y_max - y_min
                                                               ,base 
                                                               )
                             )
                   )


valid_re_normalisers = ('linear', 'exponential', 'logarithmic')


splines = dict(zip(valid_re_normalisers 
                  ,[linearly_interpolate
                   ,exp_spline
                   ,log_spline
                   ]
                  )
              )


def three_point_quad_spline(x, x_min, x_mid, x_max, y_min, y_mid, y_max):
    #z = 2
    check_strictly_less_than(x_min, x_mid, 'x_min', 'x_mid')
    check_strictly_less_than(x_mid, x_max, 'x_mid', 'x_max')

    z =  quadratic_mid_spline(x, x_mid, x_min, x_max, 0, y_min) #y_min*((x - x_max)*(x - x_mid)/((x_min - x_max)*(x_min - x_mid)))
    z += quadratic_mid_spline(x, x_min, x_mid, x_max, 0, y_mid) #y_mid*((x - x_max)*(x - x_min)/((x_mid - x_max)*(x_mid - x_min)))
    z += quadratic_mid_spline(x, x_min, x_max, x_mid, 0, y_max) #y_max*((x - x_mid)*(x - x_min)/((x_max - x_mid)*(x_max - x_min)))
    return z   


def map_f_to_tuples(f, x, x_min, x_max, tuples_min, tuples_max): 
    # (x,x_min,x_max,triple_min = rgb_min, triple_max = rgb_max)
    return [f(x, x_min, x_max, a, b) for (a, b) in zip(tuples_min, tuples_max)]


def map_f_to_three_tuples(f
                         ,x
                         ,x_min
                         ,x_med
                         ,x_max
                         ,tuple_min
                         ,tuple_med
                         ,tuple_max
                         ): 
    #type(function, Number, Number, Number, Number, tuple, tuple, tuple)->list
    # (x,x_min,x_max,triple_min = rgb_min, triple_max = rgb_max)
    return [f(x, x_min, x_med, x_max, a, b, c) 
            for (a, b, c) in zip(tuple_min, tuple_med, tuple_max)]


def change_line_thickness(obj, width, rel_or_abs = False):  
    #The default value in Rhino for wireframes is zero so rel_or_abs==True will not be effective if the width has not already been increased.
    #type(str, Number, bool)
    x = rs.coercerhinoobject(obj, True, True)
    x.Attributes.PlotWeightSource = Rhino.DocObjects.ObjectPlotWeightSource.PlotWeightFromObject
    if rel_or_abs:
        width = width * x.Attributes.PlotWeight
    x.Attributes.PlotWeight = width
    x.CommitChanges()
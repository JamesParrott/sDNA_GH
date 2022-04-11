import sys, UUID
from math import log
from os.path import isfile
if sys.version < '3.3':
    from collections import Iterable
else:
    from collections.abc import Iterable

import Rhino, GhPython
import rhinoscriptsynax as rs
import scriptcontext as sc

if 'ghdoc' not in globals():
    if sc.doc == Rhino.RhinoDoc.ActiveDoc:
        raise ValueError('sc.doc == Rhino.RhinoDoc.ActiveDoc. '
                        +'Switch sc.doc = ghdoc and re-import module. '
                        )
    if isinstance(sc.doc, GhPython.DocReplacement.GrasshopperDocument):
        ghdoc = sc.doc  # Normally a terrible idea!  But the check conditions
                        # are strong, and we need to get the `magic variable'
                        # ghdoc in this 
                        # namespace as a global, from launcher and GH.
    else:
        raise TypeError('sc.doc is not of type: '
                       +'GhPython.DocReplacement.GrasshopperDocument '
                       +'Ensure sc.doc == ghdoc and re-import module.'
                       )

class GetPathDefaults:
    Default_sDNA_GH_file_path = None
get_path_default_opts = dict(options = GetPathDefaults)

def get_path(opts = get_path_default_opts, inst = None):
    #type(dict, type[any]) -> str
    #refers to `magic' global ghdoc so needs to be in main
    
    path = Rhino.RhinoDoc.ActiveDoc.Path
                    
    if not isinstance(path, str) or not isfile(path):
        try:
            path = ghdoc.Path
        except:
            try:
                path = inst.ghdoc.Path #type: ignore
            except:
                try:
                    path = sc.doc.Path
                except:
                    path = None
        finally:
            if not path:
                path = opts['options'].Default_sDNA_GH_file_path
    
    return path



def func_name(f):
    #type(function)->str
    if hasattr(f,'__qualname__'):
        return f.__qualname__  
    elif hasattr(f,'__name__'):
        return f.__name__  
    else:
        return f.func_name

def unpack_first_item_from_list(l, null_container = {}):
    #type(type[any])-> dict
    #hopefully!
    if l:
        if isinstance(l, Iterable) and not isinstance(l, str):
            return l[0]
        else:
            return l
    else:
        return null_container        

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



def is_uuid(val):
    try:
        UUID(str(val))
        return True
    except ValueError:
        return False
#https://stackoverflow.com/questions/19989481/how-to-determine-if-a-string-is-a-valid-v4-uuid



def linearly_interpolate(x, x_min, x_mid, x_max, y_min, y_max):
    # type(Number, Number, Number, Number, Number, Number) -> Number
    assert x_min != x_max
    return y_min + ( (y_max - y_min) * (x - x_min) / (x_max - x_min) )


def quadratic_mid_spline(x, x_min, x_mid, x_max, y_min, y_max):
    # type(Number, Number, Number, Number, Number, Number) -> Number
    assert x_min != x_mid != x_max    
    retval = y_max*((x - x_max)*(x - x_min)/((x_mid - x_max)*(x_mid - x_min)))
    #retval == 0 at x == x_min and x == x_max 
    #retval == y_max at x == x_mid
    retval += y_min
    return retval


def log_spline(x, x_min, base, x_max, y_min, y_max):        
    # type(Number, Number, Number, Number, Number, Number) -> Number
    assert x_min != x_max
    log_2 = log(2, base)

    return y_min + (y_max / log_2) * log(  1 + ( (x-x_min)/(x_max-x_min) )
                                          ,base  )


def exp_spline(x, x_min, base, x_max, y_min, y_max):
    # type(Number, Number, Number, Number, Number, Number) -> Number
    assert y_min != 0 != x_max - x_min
    return y_min * pow(base, ((x - x_min)/(x_max - x_min))*log(y_max/ y_min
                                                              ,base 
                                                              )
                       )

valid_re_normalisers = ['linear', 'exponential', 'logarithmic']


splines = dict(zip(  valid_re_normalisers 
                    ,[   linearly_interpolate
                        ,exp_spline
                        ,log_spline
                        ]
                   )
               )


def three_point_quadratic_spline(x, x_min, x_mid, x_max, y_min, y_mid, y_max):
    #z = 2
    z =  quadratic_mid_spline(x, x_mid, x_min, x_max, 0, y_min) #y_min*((x - x_max)*(x - x_mid)/((x_min - x_max)*(x_min - x_mid)))
    z += quadratic_mid_spline(x, x_min, x_mid, x_max, 0, y_mid) #y_mid*((x - x_max)*(x - x_min)/((x_mid - x_max)*(x_mid - x_min)))
    z += quadratic_mid_spline(x, x_min, x_max, x_mid, 0, y_max) #y_max*((x - x_mid)*(x - x_min)/((x_max - x_mid)*(x_max - x_min)))
    return max(0, min( z, 255))        


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
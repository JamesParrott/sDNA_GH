#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys
import logging
import itertools
from math import log
if sys.version_info.major <= 2 or (
   sys.version_info.major == 3 and sys.version_info.minor <= 3):
    from collections import Sequence
else:
    from collections.abc import Sequence


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

if not hasattr(itertools, 'pairwise'):
    #https://docs.python.org/2.7/library/itertools.html
    def pairwise(iterable):
        "s -> (s0,s1), (s1,s2), (s2, s3), ..."
        a, b = itertools.tee(iterable)
        next(b, None)
        return itertools.izip(a, b)
    itertools.pairwise = pairwise




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
    #escape special characters
    for c in the_specials:
        pattern = pattern.replace(c,'\\' + c)

    # turn all named fields '{name}' in the format string 
    # into named capturing groups r'(?P<name>.*)' in a regex
    pattern = pattern.replace( '{', r'(?P<' ).replace( '}', r'>.*)' )

    # Anchor to beginning and end.
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


valid_re_normalisers = ('uniform', 'linear', 'exponential', 'logarithmic')


splines = dict(zip(valid_re_normalisers 
                  ,[linearly_interpolate
                   ,linearly_interpolate
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





def highest_strict_LB(data_point, data):
    #type(Number, Iterable[Number]) -> Number
    """ Highest strict upper bound of an 
    element in an Iterable.  data may be unsorted and
    need not be a Sequence (i.e. as well as a list/tupl,
    it can be a set or even a dict too, as 
    long as its elements and keys respectively can 
    be compared with <)"""
    return max(x for x in data if x < data_point)

def lowest_strict_UB(data_point, data):
    #type(Number, Iterable[Number]) -> Number
    """ Highest strict upper bound of an 
    element in an Iterable.  data may be unsorted and
    need not be a Sequence (i.e. as well as a list/tupl,
    it can be a set or even a dict too, as 
    long as its elements and keys respectively can 
    be compared with >)"""
    return min(x for x in data if x > data_point)

def search_one_way_only_from_index(condition, search_direction):
    #type(function, str) -> function
    """ Decorator to make partial search functions for the first 
        item for which condition == True, in the specified 
        search_direction, e.g. for making efficient functions to 
        find the lowest / highest strict upper / lower bound of an 
        element in a Sequence (e.g. tuple or list) if 
        it exists, and its index.  
        If known, the index of the element can 
        be provided to make the search faster.  
        If no item
        satisfying condition(element, item) == True is found
        in the specified search direction, the first return value 
        (the variable success) is False. """
    if search_direction.lower() == 'ascending': 
        def r(data, index):
            return range(index + 1, len(data)) 
    elif search_direction.lower() == 'descending':
        def r(data, index):
            return reversed(range(0, index))
    else:
        msg = ('Unsupported search direction: ' 
              +str(search_direction)
              +', not in (ascending, descending)'
              )
        logger.error(msg)
        raise ValueError(msg)

    def searcher(data_point, data, index = None):
    # type(Number, List[Number], int) -> bool, Number, int
        if not isinstance(index, int):
            index = data.index(data_point)
        if data[index] != data_point:
            msg = ('Incorrect index of data_point in data: '
                  'data[' + str(index) + '] == ' 
                  +str(data[index]) 
                  +' != ' + str(data_point) 
                  +' == data_point'
                  )
            logger.error(msg)
            raise ValueError(msg)

        success, lub = False, None
        for i in r(data, index):   
            if condition(data[i], data_point):
                success, lub = True, data[i]
                break
        
        return success, lub, i
    return searcher

@search_one_way_only_from_index('ascending')
def indexed_lowest_strict_UB(a, b):
    return a > b
    
@search_one_way_only_from_index('descending')
def indexed_highest_strict_LB(a, b):
    return a < b

def data_point_midpoint_and_next(data, index):
    #type(Sequence, int) -> Number, float, Number
    data_point = data[index]
    next_data_point = data[index + 1]
    midpoint = 0.5*(data_point + next_data_point)
    return data_point, midpoint, next_data_point

def quantile(data, num_classes, de_dupe = True, tol = 128 * 2e-17):
    #type(list[Number], int, bool, float) -> list[Number]
    """ Calculate inter-class boundaries of an ordered data Sequence
        (sorted in ascending order) using a quantile method. 
        This particular quantile method, as near as possible, 
        places an equal number of the remaining data points in each 
        of the remaining classes / bins, adjusting for repeated data 
        items, without being skewed by outliers.  

        Placing a class bound evenly in the theoratically ideal position for
        a sequnce with no repeated values may result in a bin with a different 
        number of data points to the previous one 
        (i.e. in a sorted data Sequence, if the data items either 
        side of the bound are equal).  If so, then if the items in the bin 
        are not all identical (i.e. in a sorted data Sequence, the 
        same as the upper side of the previous bound), either 
        the previous bound or the current bound is moved to the highest
        lower bound of the repeated data values (whichever is closest; the 
        previous bound if they're equidistant from it).  If the bound's ideal 
        position would result in all data items in 
        the bin having the same value, the bound is moved to the lowest upper 
        bound of the repeated data values.  
    """
    num_data_points_left = len(data) 
    # n-1 is number of gaps between data points. max num of bounds
    class_bounds = []
    data_index = 0
    data_indices = [] #[data_index] 
    indices = [] # of the highest data point below each bound
    data_points_per_class = num_data_points_left // num_classes
    for num_bounds_left in reversed(range(1, num_classes)):
        num_classes_left = num_bounds_left + 1
        data_points_per_class = num_data_points_left // num_classes_left
        data_point_below_index = data_indices[-1] + data_points_per_class

        (data_point_below
        ,candidate_bound
        ,data_point_above) = data_point_midpoint_and_next(
                                                     data
                                                    ,data_point_below_index
                                                    )
        previous_bound = class_bounds[-1] if class_bounds else data[0] 

        if data_point_above - candidate_bound < tol:
            # data is sorted so we don't need abs() < tol
            # data_point_below is in the class for this candidate bound
            # so we don't need to test it
            if data_point_below - previous_bound < tol:
                success, lub, lub_index = indexed_lowest_strict_UB(data_point_below
                                                                  ,data
                                                                  ,data_point_below_index
                                                                  )
                if not success:
                    # all further items are the same ( tol-indistinguishable) 
                    # until the end of data so can't place anymore 
                    # inter-class bounds.
                    msg = (' Rest of data is repeated indistinguishable data '
                          +'points. Cannot place anymore inter-class bounds so' 
                          +'skipping. To avoid this, try selecting fewer '
                          +'classes or choose a different classification '
                          +'method.  '
                          )
                    logger.warning(msg)
                    warnings.showwarning(message = msg
                                        ,category = UserWarning
                                        ,filename = __file__ 
                                        ,lineno = 979
                                        )
                    break
                # assert success # !
                data_point_below_index = lub_index - 1
                (data_point_below
                ,candidate_bound
                ,data_point_above) = data_point_midpoint_and_next(data
                                                                 ,data_point_below_index
                                                                 )
            else:
                success, hlb, hlb_index = indexed_highest_strict_LB(data_point_below
                                                                   ,data
                                                                   ,data_point_below_index
                                                                   )
                if not success:
                    msg = ('Bug report: Failed to search for an upper '
                          +'bound when it was already known there would be no '
                          +'lower bound. Leading to failure to find a lower '
                          +'bound that should have already been known not '
                          +'to exist! Code to catch this not implemented'
                          )
                    logger.error(msg)
                    raise NotImplementedError(msg)
                (data_point_below
                ,candidate_bound
                ,data_point_above) = data_point_midpoint_and_next(data
                                                                 ,hlb_index
                                                                 )
                indices_to_move_class_bound_R = hlb_index - previous_bound
                indices_to_move_candidate_L = data_point_below_index - hlb_index
                if indices_to_move_class_bound_R <= indices_to_move_candidate_L:
                    class_bounds[-1] = candidate_bound
                    data_indices[-1] = hlb_index
                    continue
                else:
                    data_point_below_index = hlb_index

        class_bounds += [candidate_bound]
        data_indices += [data_point_below_index]
    return class_bounds
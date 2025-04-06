#! /usr/bin/python
# -*- coding: utf-8 -*-

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


""" Data parsing functions and classes, for sDNA_GH.  

    Mainly numerical interpolation and inter_class bound calculation 
    functions and classes used by DataParser and ObjectsRecolourer, 
    plus a type coercer and a format string 'inverter'.
    They rely only on core Python modules, and are independent of Grasshopper
    and of other sDNA_GH modules.
"""

__authors__ = {'James Parrott', 'Crispin Cooper'}
__version__ = '3.0.3'

import logging
import warnings
import itertools
import math
from numbers import Number
import collections

from mapclassif_Iron.classifiers import _fisher_jenks_means_without_numpy

from .skel.tools.helpers.funcs import itertools # for pairwise if Python < 3.10

OrderedDict, Counter = collections.OrderedDict, collections.Counter




logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())



class OrderedCounter(Counter, OrderedDict):
     """Counter that remembers the order elements are first encountered.  
        https://docs.python.org/2.7/library/collections.html#collections.OrderedDict
        https://rhettinger.wordpress.com/2011/05/26/super-considered-super/
     """

     def __repr__(self):
         return '%s(%r)' % (self.__class__.__name__, OrderedDict(self))

     # __reduce__ is only used to defined how OrderedCounter should be pickled
     # def __reduce__(self):
         # return self.__class__, (OrderedDict(self),)

TOL = 24 * 2e-17  # eps s.t. 1 + eps == 1 on my machine is ~1.1102e-16



def check_strictly_less_than(a, b, a_name = 'a', b_name = 'b'):
    #type(Number, Number, str, str) -> None
    """ A simple validation function to both avoid dividing by zero and
        check arguments are provided in the correct ascending/descending 
        order.  
    """
    if a >= b:
        msg = '%s == %s >= %s == %s ' % (a, a_name, b_name, b)
        logger.error(msg)
        raise ValueError(msg)


def enforce_bounds(spline):
    #type(function) -> function
    """ A decorator for interpolation functions and splines that stops 
        extrapolation away from the known data points.
        It input arguments are bounded by the max and 
        min already provided to it.  
    """
    def wrapper(x, x_min, x_mid, x_max, y_min, y_max):
        x = min(x_max, max(x_min, x))
        return spline(x, x_min, x_mid, x_max, y_min, y_max)
    return wrapper


def linearly_interpolate(x, x_min, x_mid, x_max, y_min, y_max):
    # type(Number, Number, Number, Number, Number, Number) -> float
    """ Linear interpolation to find y.  """
    check_strictly_less_than(x_min, x_max, 'x_min', 'x_max')
    return y_min + ( (y_max - y_min) * (x - x_min) / (x_max - x_min) )


def check_not_eq(a, b, a_name = 'a', b_name = 'b', tol = TOL/20):
    #type(Number, Number, str, str) -> None
    """ A simple validation function, e.g. avoid dividing by zero.  
        To check for floating point errors, tol can be set slightly 
        higher than the approx machine epsilon ~1.11e-16
    """
    if abs(a - b) < tol:
        msg = '%s == %s ~= %s == %s ' % (a, a_name, b_name, b)
        logger.error(msg)
        raise ValueError(msg)


def quadratic_mid_spline(x, x_min, x_mid, x_max, y_min, y_mid):
    # type(Number, Number, Number, Number, Number, Number) -> float
    """Second order Lagrange basis polynomial multiplied by y_mid to
       determine the degree of curvature. y_min is not used but is 
       present to keep the calling signature the same as the
       other spline functions in this module.  The ascending order
       of the x is not checked as the arguments are permuted in
       the three point spline that depends on this.  
    """
    check_not_eq(x_min, x_mid, 'x_min', 'x_mid')
    check_not_eq(x_mid, x_max, 'x_mid', 'x_max')
    retval = y_mid*((x - x_max)*(x - x_min)/((x_mid - x_max)*(x_mid - x_min)))
    return retval


def log_spline(x, x_min, base, x_max, y_min, y_max):        
    # type(Number, Number, Number, Number, Number, Number) -> float
    """ A logarithmic interpolation function.    Linear interpolation 
        is first performed inside the logarithm, instead of outside it.  
    """
    check_strictly_less_than(x_min, x_max, 'x_min', 'x_max')
    log_2 = math.log(2, base)

    return y_min + (y_max / log_2) * math.log(1 + ((x-x_min)/(x_max-x_min))
                                             ,base
                                             )


def exp_spline(x, x_min, base, x_max, y_min, y_max):
    # type(Number, Number, Number, Number, Number, Number) -> float
    """ An exponential interpolation function.  Linear interpolation is performed
        inside the exponential, instead of outside it.  
    """
    check_strictly_less_than(x_min, x_max, 'x_min', 'x_max')
    return y_min + ( -1 + pow(base
                             ,((x - x_min)/(x_max - x_min)) * math.log(1 + y_max - y_min
                                                                      ,base 
                                                                      )
                             )
                   )


VALID_RE_NORMALISERS = ('none', 'linear', 'exponential', 'logarithmic')


splines = dict(zip(VALID_RE_NORMALISERS[1:] 
                  ,[linearly_interpolate
                   ,exp_spline
                   ,log_spline
                   ]
                  )
              )

# repeat basically the same dictionary, to customise
# the options of class_spacings, e.g. to match the 
# corresponding ones in QGIS.
basic_class_spacings = {'Equal Interval' : linearly_interpolate
                       ,'Exponential (inverse log)' : exp_spline
                       ,'Logarithmic scale' : log_spline
                       }


def three_point_quad_spline(x, x_min, x_mid, x_max, y_min, y_mid, y_max):
    # type(Number, Number, Number, Number, Number, Number, Number) -> float
    """ Lagrange interpolation polynomial through three points.  """

    check_strictly_less_than(x_min, x_mid, 'x_min', 'x_mid')
    check_strictly_less_than(x_mid, x_max, 'x_mid', 'x_max')

    z =  quadratic_mid_spline(x, x_mid, x_min, x_max, 0, y_min) 
    z += quadratic_mid_spline(x, x_min, x_mid, x_max, 0, y_mid) 
    z += quadratic_mid_spline(x, x_min, x_max, x_mid, 0, y_max) 
    return z   


def map_f_to_tuples(f, x, x_min, x_max, tuples_min, tuples_max): 
    # type(function, Number, Number, Number, tuple, tuple) -> list
    """A generalisation of map that returns a list of calls to the 
       specified function using the specified 3 args, with the last two args
       taking their values from the specified pair of iterable. 
    """
    return [f(x, x_min, x_max, a, b) for a, b in zip(tuples_min, tuples_max)]


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
    """A generalisation of map that returns a list of calls to the 
       specified function using the specified 4 args, with the last 3 args
       taking their values from the specified 3 iterable. 
    """

    return [f(x, x_min, x_med, x_max, a, b, c) 
            for (a, b, c) in zip(tuple_min, tuple_med, tuple_max)]

   


def class_bounds_at_max_deltas(data
                              ,num_classes
                              ,options = None):
    #type(Iterable[Number], int, float, NamedTuple) -> list
    """ Calculates inter-class boundaries for a legend or histogram,
        by placing bounds at the highest jumps between consecutive data 
        points.  Requires the values of data to be Number, and for data
        to have been sorted based on them.
        This method is prone to over-classify extreme 
        outlying values. 
    """
    if options is None:
        options = SpikeIsolatingQuantileOptions
    deltas = [(i, b - a )
              for i, (b, a) in enumerate(itertools.pairwise(data))
             ]
    class_bounds = []
    for _ in range(num_classes - 1):
        max_delta = max(deltas)
        for index, delta in deltas: 
            if math.abs(max_delta - delta) < options.tol:
                max_index = index
                break
        deltas.remove(deltas[max_index])
        
        class_bounds += [ data[max_index] + 0.5 * max_delta] #midpoint
    return class_bounds


class InclusiveInterval:
    
    def __init__(self, a, i_a, b, i_b, num_data_points):
        self.a = a
        self.index_a = i_a
        self.b = b
        self.index_b = i_b
        self.num_data_points = num_data_points

    def __repr__(self):
        str_ = 'InclusiveInterval(a = %s, i_a = %s, b = %s, i_b = %s, num_data_points = %s)'
        str_ = str_ % (self.a, self.index_a, self.b, self.index_b, self.num_data_points)
        return str_


def max_interval_lt_width_w_with_most_data_points(ordered_counter
                                                 ,min_num_of_data_pts
                                                 ,w = TOL
                                                 ):
    #type(OrderedCounter, Number) -> dict 
    """Given a discrete frequency distribution of Numbers in the form of an 
       OrderedCounter (defined earlier in this module or e.g. the Python 
       collections recipe), calculates a closed interval [a, b] of
       width b - a <= w that maximises the number of data points contained 
       within it, containing at least min_num_of_data_pts data points.  
       In a histogram this would be the largest bin of width less than w.
       This implementation calculates a moving sum using a moving interval 
       between a and b taking values of the sorted data keys.  The attributes of 
       the returned InclusiveInterval may not satisfy b-a = w (this function 
       is designed for discrete data sequences with duplicates or tight
       clusters, so widening the interval will only cause it to contain more 
       data points, if its bound crosses another data point value).  
    """
    interval_width = w
    keys = tuple(ordered_counter.keys())
    a_iter = iter(enumerate(keys))
    b_iter = iter(enumerate(keys))
    i_a, a = next(a_iter)
    i_b, b = next(b_iter)
    last_key = max(keys)
    num_data_points = ordered_counter[b]

                        
    interval = InclusiveInterval(a, i_a, b, i_b, num_data_points)
    # num_data_points = sum(ordered_counter[key] 
                      # for key in keys
                      # if a <= key <= b
                     # )

    while b < last_key:
        i_b, b = next(b_iter)
        num_data_points += ordered_counter[b]
        while b - a > interval_width:
            num_data_points -= ordered_counter[a]
            i_a, a = next(a_iter)
            
        if num_data_points > interval.num_data_points: 
            # stick with first if equal
            interval = InclusiveInterval(a, i_a, b, i_b, num_data_points) 
            
    if interval.num_data_points > min_num_of_data_pts:
        return interval
    return None
        




def highest_strict_LB(data_point, data):
    #type(Number, Iterable[Number]) -> Number
    """ Highest strict lower bound of an 
    element in an Iterable.  data may be unsorted and
    need not be a Sequence (i.e. as well as a list/tupl,
    it can be a set or even a dict too, as 
    long as its elements and keys respectively can 
    be compared with <)
    """
    return max(x for x in data if x < data_point)

def lowest_strict_UB(data_point, data):
    #type(Number, Iterable[Number]) -> Number
    """ Lowest strict upper bound of an 
    element in an Iterable.  data may be unsorted and
    need not be a Sequence (i.e. as well as a list/tupl,
    it can be a set or even a dict too, as 
    long as its elements and keys respectively can 
    be compared with >)
    """
    return min(x for x in data if x > data_point)

def search_one_way_only_from_index(search_direction):
    #type(function, str) -> function
    """ Factory that makes decorator that makes partial search functions for the first 
        item for which condition is True, in the specified 
        search_direction, e.g. for making efficient functions to 
        find the lowest / highest strict upper / lower bound of an 
        element in a Sequence (e.g. tuple or list) if 
        it exists, and its index.  
        If known, the index of the element can 
        be provided to make the search faster.  
        If no item
        satisfying condition(element, item) is True is found
        in the specified search direction, the first return value 
         is False. 
    """
    if search_direction.lower() == 'ascending': 
        def make_range(data, index):
            return range(index + 1, len(data)) 
    elif search_direction.lower() == 'descending':
        def make_range(__, index):
            return reversed(range(0, index))
    else:
        msg = ('Unsupported search direction: ' 
              +str(search_direction)
              +', not in (ascending, descending)'
              )
        logger.error(msg)
        raise ValueError(msg)


    def decorator(condition):
        def searcher(data_point, data, index = None, **kwargs):
        # type(Number, List[Number], int) -> bool, Number, int
            if not isinstance(index, int):
                index = data.index(data_point)
            if data[index] != data_point:
                msg = ('Incorrect index of data_point in data: '
                      +'data[%s ' % index + '] == ' 
                      +str(data[index]) 
                      +' != %s ' % data_point 
                      +' == data_point'
                      )
                logger.error(msg)
                raise ValueError(msg)

            for i in make_range(data, index):   
                if condition(data[i], data_point, **kwargs):
                    return True, data[i], i
            return False, None, None

        return searcher
    return decorator

@search_one_way_only_from_index('ascending')
def indexed_lowest_strict_UB(a, b, tol = TOL):
    return a > b + tol
    
@search_one_way_only_from_index('descending')
def indexed_highest_strict_LB(a, b, tol = TOL):
    return tol + a < b

def data_point_midpoint_and_next(data, index):
    #type(Sequence, int) -> Number, float, Number
    """ A support function defining the logic for calculating the midpoint
        of a data point in a Sequence with a known index, and the next one.  
    """
    data_point = data[index]
    next_data_point = data[index + 1]
    midpoint = 0.5*(data_point + next_data_point)
    return data_point, midpoint, next_data_point


def simple_quantile(data_vals, m):
    #type(Sequence(Number), int) -> Sequence(float)
    """ Returns a list of m-1 numbers that splits a sorted sequence into 
        m sub sequences, with roughly the same number of values (remainder is
        not reallocated).  
    """
    # assert data_vals is already sorted
    n = len(data_vals)
    class_size = n // m

    class_bound_indices = list(range(class_size, m*class_size, class_size))
    class_bounds = [data_vals[index] for index in class_bound_indices] 



    return class_bounds



def quantile_l_to_r(data
                   ,num_classes_wanted
                   ,options = None
                   ):
    #type(Sequence[Number], int, float, NamedTuple) -> list
    """ Calculate inter-class boundaries of an ordered data Sequence
        (sorted in ascending order) using a quantile method. 
        This particular quantile method, as near as possible, 
        places an equal number of the remaining data points in each 
        of the remaining classes / bins, adjusting for repeated data 
        items, without being skewed by outliers.  

        Requires data to be sorted in ascending order.

        Placing a class bound evenly in the theoretically ideal position for
        a sequence with no repeated values, may result in a bin with a different 
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
    if options is None:
        options = SpikeIsolatingQuantileOptions


    # n-1 is number of gaps between data points. max num of bounds
    class_bounds = []



    num_classes_wanted = min(num_classes_wanted, len(data))
    num_classes_left = num_classes_wanted
    # everything in data is already in one (big) class

    while num_classes_left >= 2:
        # try to place an inter-class bound amidst the remaining data_points 
        # if there are 2 or more classes left
        
        # When we're considering dividing the remainder into new classes, we
        # only count classes to the left of inter-class bounds in class_bounds
        #logger.debug(num_classes_left)
        logger.debug('class_bounds == %s' % class_bounds)

        if num_classes_left == num_classes_wanted:
            # Initialised correctly, so nothing with to do with 'old val'

            # Calc new candidate index
            data_point_below_index = (len(data) // num_classes_left) - 1
            previous_bound = None
        else:
            # Update using Old val
            num_data_points_left = len(data) - (data_point_below_index + 1) 
            data_points_per_class = num_data_points_left // num_classes_left
            # Calc new candidate index
            data_point_below_index += data_points_per_class
            previous_bound = class_bounds[-1]

        (data_point_below
        ,candidate_bound
        ,data_point_above) = data_point_midpoint_and_next(data
                                                         ,data_point_below_index
                                                         )
        
        logger.debug('num_classes_wanted == %s' % num_classes_wanted)
        logger.debug('data_point_below == %s' % data_point_below
                    +', candidate_bound == %s, ' % candidate_bound
                    +', data_point_above == %s' % data_point_above
                    )

        if data_point_above - candidate_bound < options.tol:
            # data is sorted so we don't need abs() < tol
            # data_point_below is in the class for this candidate bound
            # so we don't need to test it against candidate_bound
            # if previous_bound is not None:
            hlb_found, hlb, hlb_index = indexed_highest_strict_LB(
                                                        data_point_below
                                                    ,data
                                                    ,data_point_below_index
                                                    ,tol = options.tol
                                                    )
            if (previous_bound is None or 
                not hlb_found or
                hlb <= previous_bound or
                data_point_below - previous_bound < options.tol):
                # the data point just below candidate_bound, not the one just
                # below previous_bound
                lub_found, lub, lub_index = indexed_lowest_strict_UB(
                                                         data_point_below
                                                        ,data
                                                        ,data_point_below_index
                                                        ,tol = options.tol
                                                        )
                if not lub_found:
                    # all further items are the same (tol - indistinguishable) 
                    # until the end of data so can't place any more 
                    # inter-class bounds.
                    msg = (' Rest of data is repeated indistinguishable data '
                          +'points. Cannot place any more inter-class bounds so ' 
                          +'skipping. To avoid this, try selecting fewer '
                          +'classes or choose a different classification '
                          +'method.  '
                          )
                    logger.warning(msg)
                    warnings.showwarning(message = msg
                                        ,category = UserWarning
                                        ,filename = __file__ 
                                        ,lineno = 544
                                        )
                    break
                # assert lub_found # !

                # Need this to update num_data_points_left in next iteration.
                data_point_below_index = lub_index - 1

                # Move candidate_bound to the right, to the midpoint of
                # the class and its lowest upper bound in data.
                (data_point_below
                ,candidate_bound
                ,data_point_above) = data_point_midpoint_and_next(
                                                         data
                                                        ,data_point_below_index
                                                        )
            else:
                # hlb_found, hlb, hlb_index = indexed_highest_strict_LB(
                #                                          data_point_below
                #                                         ,data
                #                                         ,data_point_below_index
                #                                         ,tol = options.tol
                #                                         )
                # if not hlb_found or ( previous_bound is not None 
                #                     and hlb <= previous_bound ):
                #     msg = ('highest lower bound search failed, or '
                #           +'hlb was at or above previous bound, '
                #           +'but should have had '
                #           +'data_point_below - previous_bound >= tol.  '
                #           +'hlb_found == %s'
                #           +', data_point_below - previous_bound == %s'
                #           +', tol == %s, data_point_below == %s'
                #           +', candidate_bound == %s, data_point_above == %s'
                #           +', previous_bound == %s'
                #           +', hlb == %s, hlb_index == %s'
                #           +', data_point_below_index == %s'
                #           +', data == %s'
                #           +', class_bounds == %s'
                #           )
                #     msg %= (hlb_found
                #            ,data_point_below - previous_bound
                #            ,options.tol
                #            ,data_point_below
                #            ,candidate_bound
                #            ,data_point_above
                #            ,previous_bound
                #            ,hlb
                #            ,hlb_index
                #            ,data_point_below_index
                #            ,data
                #            ,class_bounds
                #            )
                #     logger.error(msg)
                #     raise NotImplementedError(msg)

                # update candidate_bound to a lower value, that splits the 
                # data_point_below the previous candidate_bound and its 
                # highest lower bound in data 
                (data_point_below
                ,candidate_bound
                ,data_point_above) = data_point_midpoint_and_next(data
                                                                 ,hlb_index
                                                                 )
                logger.debug('new candidate_bound past highest lower bound == %s' % candidate_bound)
                data_point_below_index = hlb_index
                # Need this to update num_data_points_left in next iteration.
                #
                # The number of remaining data points to classify is the same 
                # regardless of whether we add an extra class bound to those of the 
                # preceding already classified data points or not.

                indices_to_move_class_bound_R = hlb_index - previous_bound
                indices_to_move_candidate_L = data_point_below_index - hlb_index
                if indices_to_move_candidate_L > indices_to_move_class_bound_R:
                    # move previous class bound to the R to candidate 
                    # (overwrite previous class bound with candidate_bound)
                    class_bounds[-1] = candidate_bound
                    continue # Haven't added an extra class or bound, just 
                             # extended the previous class, so skip extending 
                             # class_bounds
                else:
                    pass
                    # move candidate bound L to highest lower bound of 
                    # data_point_below prev candidate bound


        class_bounds += [candidate_bound]
        num_classes_left = num_classes_wanted - (len(class_bounds))


    return class_bounds





def pro_rata(n, N_1, N_2, tol = TOL):
    #type(Number, Number, Number) -> int, int
    """ Divides n up pro-rata into n = n_1 + n_2, with 
        n_1 and n_2 proportional to N_1 and N_2.
    
        If n, N_1 and N_2 are all integers, attempts to return 
        the number of summands in the collectively most evenly 
        distributed partitions (into integers) of N_1 and N_2.
    """
    # N_1 + N_2 = N = n * m + r   0 <= r < n
    #N_1 = m*n_1 + r_1            0 <= r_1 < m
    #N_2 = m*n_2 + r_2            0 <= r_2 < m
    logger.debug('n = %s, N_1 = %s, N_2 = %s' % (n, N_1, N_2))
    not_numbers = [x for x in (n, N_1, N_2) if not isinstance(x, Number) ]
    if not_numbers:
        msg = 'All args need to be numbers. Invalid args: %s' % not_numbers
        logger.error(msg)
        raise TypeError(msg)

    N = N_1 + N_2
    #if math.abs(N) < tol:
    if N == 0:
        msg = ('Cannot divide n pro-rata with respect to a total of zero. '
                +' Choose N_1 != - N2.  '
                +'Invalid args: N_1 == %s, N_2 == %s' % (N_1, N_2)
                )
        logger.error(msg)
        raise TypeError(msg)  

    if any(isinstance(x, float) for x in (n, N_1, N_2)):
        # Normal floating point pro-rata
        return n * N_1 / N, n * N_2 / N
        


    m = float(N) / n

    n_1, n_2 = N_1 / m, N_2 / m
    r_1, r_2 = N_1 - int(n_1) *m, N_2 - int(n_2) * m
    logger.debug('m == %s, n_1 == %s, r_1 == %s, n_2 == %s, r_2 == %s' % (m, n_1, r_1, n_2, r_2))
    if N_1 <= m:
        return 1, n-1
    if N_2 <= m:
        return n-1, 1
    logger.debug('r_1 / n_1 == %s, r_2 / n_2 == %s' % (r_1 / n_1, r_2 / n_2))
    if (r_1 / n_1) >= (r_2 / n_2):
        retvals = n - int(n_2), int(n_2)
    else:
        retvals = int(n_1), n - int(n_1)
    logger.debug('pro_rata retvals (n_1, n_2) == %s, %s' % retvals)
    return retvals





class SpikeIsolatingQuantileOptions(object):
    max_width = 200 * TOL
    min_num = None
    tol = TOL


def spike_isolating_quantile(data
                            ,num_classes
                            ,ordered_counter = None
                            ,options = SpikeIsolatingQuantileOptions
                            ):
    #type(Sequence[Number], int, float, NamedTuple) -> list
    """ Classify largest spike in the frequency distribution; 
        allocate remaining classes using pro_rata
        call self on the gaps, or quantile_l_to_r if no spikes.
    
        Places interclass bounds in data, a Sequence (e.g. 
        list / tuple) of Numbers that has been sorted (in ascending order).  
        It first isolates the largest / narrowest spike in the frequency 
        distribution, then calls itself on both remaining sub-Sequences 
        either side of the spike, with 
        classes allocated via pro_rata.  If there are no spikes 
        narrower than the max width, containing at least the minimum number of 
        data points, the corresponding number of classes to it are allocated 
        within each sub-Sequence using quantile_l_to_r.  The lists of 
        inter-class bounds returned by these recursive calls are appended 
        together and returned.  
    """
    if ordered_counter is None:
        ordered_counter = OrderedCounter(data)
    logger.debug(ordered_counter)
    num_inter_class_bounds = num_classes - 1
    if num_inter_class_bounds <= 0:
        return []
    if num_inter_class_bounds == 1:
        return quantile_l_to_r(data, num_inter_class_bounds + 1, options)
    inter_class_bounds = []
    if num_inter_class_bounds >= 2:
        if options.min_num is None:
            min_num = len(data) // num_classes
        else:
            min_num = options.min_num
        logger.debug('min_num == %s' % min_num)
        logger.debug('max_width == %s ' % options.max_width)
        logger.debug('data == %s,...,%s' % (tuple(data[:4]), tuple(data[-4:])))
        logger.debug('len(data) == %s ' % len(data))
        spike_interval = max_interval_lt_width_w_with_most_data_points(ordered_counter
                                                                      ,min_num
                                                                      ,w = options.max_width
                                                                      )
        if spike_interval:
            logger.debug('num_classes - 1 == %s' % (num_classes - 1))
            logger.debug('index_a (in OrderedCounter)== %s' % spike_interval.index_a)
            logger.debug('index_b (in OrderedCounter) == %s' % spike_interval.index_b)
            spike_data_index_a = data.index(ordered_counter.keys()[spike_interval.index_a])
            spike_data_index_b = tuple(reversed(data)).index(ordered_counter.keys()[spike_interval.index_b])
            spike_data_index_b = len(data) - 1 - spike_data_index_b
            logger.debug('spike_data_index_a == %s' % spike_data_index_a)
            logger.debug('spike_data_index_b == %s' % spike_data_index_b)
            if (num_classes - 3 <= 0 or 
               (spike_data_index_a == 0 and spike_data_index_b == len(data)- 1)):
                extra_classes_a, extra_classes_b = 0, 0
            else:
                logger.debug('n == %s, N_1 == %s, N_2 == %s ' %   (num_classes - 3
                                                           ,spike_data_index_a
                                                           ,len(data) - spike_data_index_b - 1
                                                           )
                            )
                extra_classes_a, extra_classes_b = pro_rata(num_classes - 3
                                                           ,spike_data_index_a
                                                           ,len(data) - spike_data_index_b - 1
                                                           ,tol = options.tol
                                                           )
            logger.debug('extra_classes_a == %s, extra_classes_b == %s' % (extra_classes_a, extra_classes_b))
            inter_class_bounds = []
            if spike_data_index_a >= 1:
                __, midpoint_i_a, __ = data_point_midpoint_and_next(data
                                                                  ,spike_data_index_a - 1
                                                                  )
                logger.debug('midpoint_i_a == %s' % midpoint_i_a)
                inter_class_bounds += spike_isolating_quantile(data[:spike_data_index_a]
                                                              ,extra_classes_a + 1
                                                              ,options = options
                                                              ) 
                inter_class_bounds += [midpoint_i_a]
                logger.debug('left of a inter_class_bounds == %s ' % inter_class_bounds)
            if spike_data_index_b <= len(data) - 2:

                __, midpoint_i_b, __ = data_point_midpoint_and_next(data
                                                                  ,spike_data_index_b
                                                                  )
                logger.debug('midpoint_i_b == %s' % midpoint_i_b)
                inter_class_bounds += [midpoint_i_b]
                inter_class_bounds += spike_isolating_quantile(data[spike_data_index_b + 1:]
                                                              ,extra_classes_b + 1
                                                              ,options = options
                                                              )
                logger.debug('right of b inter_class_bounds == %s ' % inter_class_bounds)




        else:
            inter_class_bounds = quantile_l_to_r(data, num_classes, options)
    return inter_class_bounds
    
            
def max_and_min_are_valid(max_, min_):
    #type(type[any], type[any]) -> bool
    return (isinstance(max_, Number) and 
            isinstance(min_, Number) and 
            max_ > min_ 
           )


def geometric(
         data
        ,num_classes
        ,options = None
        ):

    _min = min(data)
    _max = max(data) + 0.00001 

    if _min == _max:
        raise ValueError(
            "Cannot compute geometric classification of data points "
            +"that are all same value, max: %s == min: %s"
            % (_min, _max)
            +"Set class_spacing to a different classification method. "
            )

    if _min == 0:
        if _max == 1:
            raise ValueError(
                "Geometric classification is not meaningful "
                "if min == 0 and max == 1a unit range is data points "
                +"that are all same value, max: %s == min: %s"
                % (_min, _max)
                +"Set class_spacing to a different classification method. "
                )

        if _max < 1:
            return [_max**k for k in range(num_classes, 1, -1)]

        ratio = _max ** (1 / float(num_classes))

        return [ratio**k for k in range(1, num_classes)]


    ratio = (_max / _min) ** (1 / float(num_classes))
    return [_min * ratio**k for k in range(1, num_classes)]



def fisher_jenks(
             data
            ,num_classes
            ,options = None
            ):
    return _fisher_jenks_means_without_numpy(data, num_classes)
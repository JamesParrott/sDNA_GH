#! /usr/bin/python
# -*- coding: utf-8 -*-

""" Python 2 / 3 helper functions and classes, for sDNA_GH.  

    Mainly numerical interpolation and inter_class bound calculation 
    functions and classes used by DataParser and ObjectsRecolourer, 
    plus a type coercer and a format string 'inverter'.
    They rely only on core Python modules, and are independent of Grasshopper
    and of other sDNA_GH modules.
"""

__author__ = 'James Parrott'
__version__ = '0.02'

import sys
import logging
import itertools
import math
from collections import OrderedDict, Counter
if sys.version_info.major <= 2 or (
   sys.version_info.major == 3 and sys.version_info.minor <= 3):
    from collections import Sequence
else:
    from collections.abc import Sequence
import warnings




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

class OrderedCounter(Counter, OrderedDict):
     """Counter that remembers the order elements are first encountered.  
        https://docs.python.org/2.7/library/collections.html#collections.OrderedDict
     """

     def __repr__(self):
         return '%s(%r)' % (self.__class__.__name__, OrderedDict(self))

     # __reduce__ is only used to defined how OrderedCounter should be pickled
     # def __reduce__(self):
         # return self.__class__, (OrderedDict(self),)

TOL = 24 * 2e-17  # eps s.t. 1 + eps == 1 on my machine is ~1.1102e-16



def first_item_if_seq(l, null_container = {}):
    #type(type[any], type[any])-> dict
    """A function to strip out unnecessary wrappping containers, e.g. 
       first_item_if_seq([[1,2,3,4,5]]) == [1,2,3,4,5] without breaking 
       up strings.  
       
       Returns the second argument if the first argument is null.
       Returns the first item of a Sequence, otherwise returns the 
       not-a-Sequence first argument.  
    """
    if not l:
        return null_container        

    if isinstance(l, Sequence) and not isinstance(l, str):
        l = l[0]
    
    return l


def make_regex(pattern):
    # type (str) -> str
    """ Makes a regex from its 'opposite'/'inverse': a format string.  
        Escapes special characters.
        Turns format string fields: {name} 
        into regex named capturing groups: (?P<name>.*) 
    """
    
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
    """ A simple validation function to both avoid dividing by zero and
        check arguments are provided in the correct ascending/descending 
        order.  
    """
    if a >= b:
        msg = str(a) + ' == ' + a_name + ' >= ' + b_name + ' == ' + str(b)
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


def check_not_eq(a, b, a_name = 'a', b_name = 'b', tol = 0):
    #type(Number, Number, str, str) -> None
    """ A simple validation function, e.g. avoid dividing by zero.  
        To check for floating point errors, tol can be set slightly 
        higher than the approx machine espilon ~1.11e-16
    """
    if abs(a - b) < tol:
        msg = str(a) + ' == ' + a_name + ' == ' + b_name + ' == ' + str(b)
        logger.error(msg)
        raise ValueError(msg)


def quadratic_mid_spline(x, x_min, x_mid, x_max, y_min, y_mid):
    # type(Number, Number, Number, Number, Number, Number) -> float
    """Second order Lagrange basis polynomial multipled by y_mid to
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
    """ An expontial interpolation function.  Linear interpolation is performed
        inside the exponential, instead of outside it.  
    """
    check_strictly_less_than(x_min, x_max, 'x_min', 'x_max')
    return y_min + ( -1 + pow(base
                             ,((x - x_min)/(x_max - x_min)) * math.log(1 + y_max - y_min
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
    """A generalisation of map that returns a list of calls to the 
       specified function using the specified 4 args, with the last 3 args
       taking their values from the specified 3 iterable. 
    """

    return [f(x, x_min, x_med, x_max, a, b, c) 
            for (a, b, c) in zip(tuple_min, tuple_med, tuple_max)]

   


def class_bounds_at_max_deltas(data
                              ,num_classes
                              ,tol = TOL
                              ,options = None):
    #type(Iterable[Number], int, float, NamedTuple) -> list
    """ Calculates inter-class boundaries for a legend or histogram,
        by placing bounds at the highest jumps between consecutive data 
        points.  Requires the values of data to be Number, and for data
        to have been sorted based on them.
        This method is prone to over-classify extreme 
        outlying values. 
    """
    deltas = [(i, b - a )
              for i, (b, a) in enumerate(itertools.pairwise(data))
             ]
    class_bounds = []
    for _ in range(num_classes - 1):
        max_delta = max(deltas)
        for index, delta in deltas: 
            if math.abs(max_delta - delta) < tol:
                max_index = index
                break
        deltas.remove(deltas[max_index])
        
        class_bounds += [ data[max_index] + 0.5 * max_delta] #midpoint
    return class_bounds




def min_interval_lt_width_w_with_most_data_points(ordered_counter
                                                 ,minimum_num
                                                 ,w = TOL
                                                 ):
    #type(OrderedCounter, Number) -> dict 
    """Given a frequency distribution of Numbers in the form of an 
       OrderedCounter (defined earlier in this module or e.g. the Python 2.7 
       collections recipe), calculate a minimum closed interval [a, b] of
       width b - a <= w that contains the most data points.  In a 
       histogram this would be the largest bin of width less than w.
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
    class InclusiveInterval:
        def __init__(self):
            self.a = a
            self.index_a = i_a
            self.b = b
            self.index_b = i_b
            self.num_data_points = num_data_points
                        
    interval = InclusiveInterval()
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
            interval = InclusiveInterval() 
            
    if interval.num_data_points > minimum_num:
        return interval
    return None
        




def highest_strict_LB(data_point, data):
    #type(Number, Iterable[Number]) -> Number
    """ Highest strict upper bound of an 
    element in an Iterable.  data may be unsorted and
    need not be a Sequence (i.e. as well as a list/tupl,
    it can be a set or even a dict too, as 
    long as its elements and keys respectively can 
    be compared with <)
    """
    return max(x for x in data if x < data_point)

def lowest_strict_UB(data_point, data):
    #type(Number, Iterable[Number]) -> Number
    """ Highest strict upper bound of an 
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
        (the variable success) is False. 
    """
    if search_direction.lower() == 'ascending': 
        def make_range(data, index):
            return range(index + 1, len(data)) 
    elif search_direction.lower() == 'descending':
        def make_range(data, index):
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
                    'data[' + str(index) + '] == ' 
                    +str(data[index]) 
                    +' != ' + str(data_point) 
                    +' == data_point'
                    )
                logger.error(msg)
                raise ValueError(msg)

            success, lub = False, None
            for i in make_range(data, index):   
                if condition(data[i], data_point, **kwargs):
                    success, lub = True, data[i]
                    break
            
            return success, lub, i
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





def quantile_l_to_r(data
                   ,num_classes_wanted
                   ,tol = TOL
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

        if data_point_above - candidate_bound < tol:
            # data is sorted so we don't need abs() < tol
            # data_point_below is in the class for this candidate bound
            # so we don't need to test it against candidate_bound
            if previous_bound is None or data_point_below - previous_bound < tol:
                # the data point just below candidate_bound, not the one just
                # below previous_bound
                success, lub, lub_index = indexed_lowest_strict_UB(data_point_below
                                                                  ,data
                                                                  ,data_point_below_index
                                                                  )
                if not success:
                    # all further items are the same (tol - indistinguishable) 
                    # until the end of data so can't place anymore 
                    # inter-class bounds.
                    msg = (' Rest of data is repeated indistinguishable data '
                          +'points. Cannot place anymore inter-class bounds so ' 
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

                # Need this to update num_data_points_left in next iteration.
                data_point_below_index = lub_index - 1

                # Move candidate_bound to the right, to the midpoint of
                # the class and its lowest upper bound in data.
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
                if not success or ( previous_bound is not None 
                                    and hlb <= previous_bound ):
                    msg = (' highest lower bound search failed, or '
                          +' hlb was at or below previous bound, '
                          +' but should have had '
                          +' data_point_below - previous_bound >= tol.  '
                          +' data_point_below - previous_bound == '
                          + str(data_point_below - previous_bound)
                          +' and tol == '
                          + str(tol)
                          )
                    logger.error(msg)
                    raise NotImplementedError(msg)

                # update candidate_bound to a lower value, that splits the 
                # data_point_below the previous candidate_bound and its 
                # highest lower bound in data 
                (data_point_below
                ,candidate_bound
                ,data_point_above) = data_point_midpoint_and_next(data
                                                                 ,hlb_index
                                                                 )

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
                    # move candidate bound L to highest lower bound of 
                    # data_point_below prev candidate bound

                    class_bounds += [candidate_bound]

        class_bounds += [candidate_bound]
        num_classes_left = num_classes_wanted - (len(class_bounds))


    return class_bounds

class SpikeIsolatingQuantileOptions(object):
    max_width = 200 * TOL
    min_num = None

class NumberPartition(object):
    """ Adds some extra methods to normal integer division numbers to allow
        calculation of partitions of a number that can be decomposed into
        subpartitions as 'even as possible', that sum to specified constraints.
    """

    def divide_by(self, divisor):
        #type(int) -> None
        """Type check divisor, then carry out standard integer division of
           self.val by it, saving quotient and remainder as instance 
           variables.
        """
        if not isinstance(divisor, int):
            msg = ('Integer division attempted with values of type '
                  +' type(divisor) == ' + type(divisor).__name__ 
                  )
            logger.error(msg)
            raise TypeError(msg)
        self.divisor = divisor
        self.quotient = self.val // divisor
        self.remainder = self.val % divisor    
        # val = divisor * self.quotient + self.remainder, all integers
        #       where 0 <= self.remainder < divisor
     

    def __init__(self, val, divisor):
        #type(int, int) -> None
        """Type check val and call self.divide_by. """
        if not isinstance(val, int):
            msg = ('Integer division attempted with values of type '
                  +' type(val) == ' 
                  + type(val).__name__ 
                  )
            logger.error(msg)
            raise TypeError(msg)

        self.val = val
        self.divide_by(divisor)
      

    def divisor_increase(self):
        #type() -> int
        """Return the increase in the highest summand of the partition by reallocation
           of the remainder across the summands.  The increase every summand, 
           + 1 if there is still a remainder for the increase resulting in the highest.

           r_2 = self.remainder
           n_2 = self.quotient
           N_2 = self.value
           
           r_2 = b * n_2 + r_b,   0 <= r_b < n_2,  
           r_b = B.remainder
           b = B.quotient

           Reallocate the remainder of N_2 across its partition's summands
           producing distortion N_2.remainder // N_2.quotient, 
                                + 1 if N_2.remainder % N_2.quotient  
        """
        B = NumberPartition(val = self.remainder, divisor = self.quotient)
        b = B.quotient
        retval = b  + ( 1 if B.remainder > 0 else 0 ) 
        #    B.remainder < B.divisor == N_2.quotient, so is in {1,0}
        #    if r_b > 0, it will be reallocated to a summand in the partition, 
        #    making the highest summand higher, and the distortion higher.
        
        return retval

    def divisor_decrease(self):
        #type() -> int
        """ Try dividing self.val by a smaller than ideal divisor, self.divisor - a, 
            to result in a 
            slightly higher quotient, self.quotient + 1, absorbing the split 
            class/summand with minimum distortion.  Return the decrease in the divisor
            a minus any increase of the smallest summand (if any) from reallocating 
            the remainder across all the summands.
            
            m = self.divisor
            n_1 = self.quotient
            r_1 = self.remainder
            
            a = (m - r_1) // n_1, 
            so that n_1 * (a+1) >= m - r_1, 
            i.e. n_1 * a + r_1 = m - a + r_a for r_a > 0 
            thus N_1 = (n_1 + 1) * (m - a) + r_a
        """
        a =  (self.divisor - self.remainder) // self.quotient
        retval = a - ((self.quotient * a + self.remainder) // (self.quotient + 1))
        return retval


    def distortion(self, reallocator):
        #type(IntegerDivision) -> int
        return reallocator.divisor_increase() + self.divisor_decrease()

    def partition(self, smallest_first = True):
        #type(int, bool) -> Iterator
        def generator():
            if smallest_first:
                for _ in range(self.remainder, self.divisor):
                    yield self.quotient
                for _ in range (self.remainder):
                    yield self.quotient + 1
            else:
                for _ in range (self.remainder):
                    yield self.quotient + 1
                for _ in range(self.remainder, self.divisor):
                    yield self.quotient
        return generator()



def discrete_pro_rata(n, N_1, N_2):
    #type(int, int, int) -> int, int
    """ A mathematical algorithm using integer division and modular 
        arithmetic to find a pair of generalised integer divisors n_1 and n_2
        of N_1 and N_2 respectively, s.t. n = n_1 + n_2 with N_1 // n_1 
        and N_2 // n_2 are both as close as possible to (N_1 + N_2) // n.    
        
        Given a desired number of summands n of a partition of N = N_1 + N_2,
        this function finds the number of summands of partitions of 
        N_1 and N_2, n_1 and n_2 respectively, such that the max - min of
        the superset of the summands of both these sub partitions is minimised.
        E.g. normally if we wanted to divide 90 into 9 even summands, we could 
        split it into 9 summands of 10 (==90 // 9).  However if we also 
        required that the summands be abel to be split into two subpartitions, 
        both summing to 45, we would have to split 90 into 5 * 9 and 3*11 + 12.
        This is the most even least distorted pair of partitions of 45 of 
        with 4 and 5 summands, that generalises the integer division of 90 // 9
        to satisfy our additional constraints.  

        Note, just using the floating point approximation, and the ceil of the 
        ratio on the smaller interval, and rounding down on the larger one can
        produce unneccessary extra distortion, e.g. dividing 100//100 split 
        between two sub partitions of 21 and 79, would divide 21 by 2.1 rounded up
    """ 
    N = N_1 + N_2
    N =   NumberPartition(val = N_1 + N_2, divisor = n)
    N_1 = NumberPartition(val = N_1,       divisor = N.quotient)
    N_2 = NumberPartition(val = N_2,       divisor = N.quotient)

    def error(msg):
        m, r = N.quotient, N.remainder           #N   = m   * n + r,   0 <= r   < n
        n_1, r_1 = N_1.quotient, N_1.remainder;  #N_1 = n_1 * m + r_1, 0 <= r_1 < m
        n_2, r_2 = N_2.quotient, N_2.remainder;  #N_2 = n_2 * m + r_2, 0 <= r_2 < m
        msg +=  ('n == ' + str(N.divisor) 
                +'!= n_1 + n_2, '
                +'N == ' + str(N.val) + ' ?= '
                +'n*m + r == ' + str(n*m + r) + ', '
                +'m == ' + str(m) + ', '
                +'r == ' + str(r) + ', '
                +'N_1 == ' + str(N_1) + ' ?= '
                +'m*n_1 + r_1 == ' + str(m*n_1 + r_1) + ', '
                +'n_1 == ' + str(n_1) + ', '
                +'r_1 == ' + str(r_1) + ', '
                +'N_2 == ' + str(N_2) + ' ?= '
                +'m*n_2 + r_2 == ' + str(m*n_2 + r_2) + ', '
                +'n_2 == ' + str(n_2) + ', '
                +'r_2 == ' + str(r_2) 
                )
        logger.error(msg)
        raise NotImplementedError(msg)

    if N_1.remainder + N_2.remainder == N.remainder:
        if N_1.quotient + N_2.quotient == n:
            return N_1.quotient, N_2.quotient
        else:
            # N_1 + N_2 == N should mean (n_1 + n_2)*m + r_1 + r_2 == m * n + r
            error('r_1 + r_2 == r but n_1 + n_2 != n.  Possible mistake? ')
    elif N_1.remainder + N_2.remainder != N.remainder + N.quotient:
        error('r_1 + r_2 should= r mod m and r_1 + r_2 should< 2 * m. Possible mistake? ')
    elif N_1.quotient + N_2.quotient != n - 1:
        error('r_1 + r_2 == r + m but n_1 + n_2 != n - 1.  Possible mistake? ')


    #What if we divide N_2 or N_2 by m + b using any factors of n_2 or 
    # n_1 in r_2 or r_1 respectively?  And what if we also reallocate 
    # the remainder of N_1 or N_2, r_1 or r_2 to divide N_1 or N_2 by m - a 
    # instead, to try and increase the quotients n_1 or n_2, respectively?
    #
    #We calculate the distortion in both cases and pick the one with the lowest

    if N_1.distortion(N_2) <= N_2.distortion(N_1):
        return N_1.quotient + 1, N_2.quotient 
    else:
        return N_1.quotient, N_2.quotient + 1


def spike_isolating_quantile(data
                            ,num_classes
                            ,tol = TOL
                            ,options = SpikeIsolatingQuantileOptions
                            ):
    #type(OrderedDict, int, float, NamedTuple) -> list
    """ This function places interclass bounds in data, a Sequence (e.g. 
        list / tuple) of Numbers that has been sorted (in ascending order).  
        It first isolates the largest / narrowest spike in the frequency 
        distribution, then calls itself on both remaining sub-Sequences 
        either side of the spike, with a smartly determined allocation of 
        classes.  This allocation is from discrete_pro_rata.  If there are no spikes 
        narrower than the max width, containing at least the minimum number of 
        data points, the corresponding number of classes to it are allocated 
        within each sub-Sequence using quantile_l_to_r.  The lists of 
        inter-class bounds returned by these recursive calls are appended 
        together and returned.  
    """

    ordered_counter = OrderedCounter(data)
    num_inter_class_bounds = num_classes - 1
    if num_inter_class_bounds <= 0:
        return []
    if num_inter_class_bounds == 1:
        return quantile_l_to_r(data, num_inter_class_bounds + 1, tol, options)
    inter_class_bounds = []
    if num_inter_class_bounds >= 2:
        if options.min_num is None:
            min_num = len(data) // num_classes
        else:
            min_num = options.min_num
        spike_interval = min_interval_lt_width_w_with_most_data_points(ordered_counter
                                                                      ,options.max_width
                                                                      ,min_num
                                                                      )
        if spike_interval:
            num_classes_a, num_classes_b = discrete_pro_rata(num_classes - 1
                                                            ,spike_interval.index_a
                                                            ,len(data) - spike_interval.index_b
                                                            )
            _, midpoint_i_a, _1 = data_point_midpoint_and_next(data
                                                              ,spike_interval.index_a - 1
                                                              )
            _, midpoint_i_b, _1 = data_point_midpoint_and_next(data
                                                              ,spike_interval.index_b
                                                              )

            inter_class_bounds = spike_isolating_quantile(data[:spike_interval.index_a]
                                                         ,num_classes_a
                                                         ,tol
                                                         ,options
                                                         )                                  
            inter_class_bounds += [midpoint_i_a, midpoint_i_b]
            inter_class_bounds += spike_isolating_quantile(data[spike_interval.index_b + 1:]
                                                          ,num_classes_b
                                                          ,tol
                                                          ,options
                                                          )
        else:
            inter_class_bounds = quantile_l_to_r(data, num_classes, tol, options)
    return inter_class_bounds
    
            


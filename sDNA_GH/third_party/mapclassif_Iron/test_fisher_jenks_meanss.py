import unittest
import functools


from . import classifiers
from .datasets import calemp

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


try:
    from numba import njit

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

    def njit(_type):  # noqa ARG001
        def decorator_njit(func):
            @functools.wraps(func)
            def wrapper_decorator(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper_decorator

        return decorator_njit



class Testfisher_jenks_meanss(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.V = sorted(calemp.load())

    def _assert_func_reproduces_mapclassify_test_case(self, func):

        result = func(self.V)

        expecteds = [75.29, 192.05, 370.5, 722.85, 4111.45]
        
        for actual, expected in zip(result, expecteds):
            self.assertAlmostEqual(actual, expected)

    @unittest.skipUnless(HAS_NUMPY, "Requires numpy")    
    def test_mapclassify_fisher_jenks_means(self):
        import numpy as np
        self._assert_func_reproduces_mapclassify_test_case(
            lambda y: _fisher_jenks_means(np.asarray(y))
        )

    def test_mapclassif_Iron_fisher_jenks_means_without_numpy(self):
        self._assert_func_reproduces_mapclassify_test_case(
            classifiers._fisher_jenks_means_without_numpy
        )






@njit("f8[:](f8[:], u2)")
def _fisher_jenks_means(values, classes=5):
    """
    Jenks Optimal (Natural Breaks) algorithm implemented in Python.

    Notes
    -----

    The original Python code comes from here:
    http://danieljlewis.org/2010/06/07/jenks-natural-breaks-algorithm-in-python/
    and is based on a JAVA and Fortran code available here:
    https://stat.ethz.ch/pipermail/r-sig-geo/2006-March/000811.html

    Returns class breaks such that classes are internally homogeneous while
    assuring heterogeneity among classes.

    """
    n_data = len(values)
    mat1 = np.zeros((n_data + 1, classes + 1), dtype=np.int32)
    mat2 = np.zeros((n_data + 1, classes + 1), dtype=np.float32)
    mat1[1, 1:] = 1
    mat2[2:, 1:] = np.inf

    v = np.float32(0)
    for _l in range(2, len(values) + 1):
        s1 = np.float32(0)
        s2 = np.float32(0)
        w = np.float32(0)
        for m in range(1, _l + 1):
            i3 = _l - m + 1
            val = np.float32(values[i3 - 1])
            s2 += val * val
            s1 += val
            w += np.float32(1)
            v = s2 - (s1 * s1) / w
            i4 = i3 - 1
            if i4 != 0:
                for j in range(2, classes + 1):
                    if mat2[_l, j] >= (v + mat2[i4, j - 1]):
                        mat1[_l, j] = i3
                        mat2[_l, j] = v + mat2[i4, j - 1]
        mat1[_l, 1] = 1
        mat2[_l, 1] = v

    k = len(values)

    kclass = np.zeros(classes + 1, dtype=values.dtype)
    kclass[classes] = values[len(values) - 1]
    kclass[0] = values[0]
    for countNum in range(classes, 1, -1):
        pivot = mat1[k, countNum]
        _id = int(pivot - 2)
        kclass[countNum - 1] = values[_id]
        k = int(pivot - 1)
    return np.delete(kclass, 0)


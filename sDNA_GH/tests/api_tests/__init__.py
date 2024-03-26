import os
import unittest


def make_unit_test_TestCase_instance_generator(
    Class,
    method,
    ):


    def API_unittest_TestCase_instances(
            N = int(os.getenv('NUM_SDNA_GH_API_TESTS', '5')),
            ):

        class Class(unittest.TestCase):
            pass

        for i in range(1, N+1):        
            method_name = '%s_%s' % (method.__name__, i)
            setattr(Class
                ,method_name
                ,method
                )

            yield Class(method_name)

    return API_unittest_TestCase_instances
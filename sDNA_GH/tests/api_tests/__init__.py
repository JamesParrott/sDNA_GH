import os
import unittest


def make_unit_test_TestCase_instance_generator(
    method,
    ):

    def API_unittest_TestCase_instances(
            N = int(os.getenv('NUM_SDNA_GH_API_TESTS', '5')),
            ):

        class APITestCase(unittest.TestCase):
            pass

        for i in range(1, N+1):
            method_name = 'test_%s_%s' % (method.__name__, i)
            print('Adding test method: %s' % method_name)
            setattr(APITestCase
                ,method_name
                ,method
                )

            yield APITestCase(method_name)

    return API_unittest_TestCase_instances
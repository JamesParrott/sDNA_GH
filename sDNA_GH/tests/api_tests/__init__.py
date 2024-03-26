import importlib

def make_unit_test_TestCase_instance_generator(
    RandomNumberOfRandomObjectsRandomlyRecolourTests,
    test_recolouring_random_num_of_random_objs_random_cols
    
    ):


    def API_unittest_TestCase_instances():


        class RandomNumberOfRandomObjectsRandomlyRecolourTests(unittest.TestCase):
            pass


        # NUM_TESTS = 5

        # method_names = []

        while True:
        #    test_recolouring_random_num_of_random_objs_random_cols(None)
            method_name = 'test_recolouring_random_num_of_random_objs_random_cols_%s' % (i+1)
            setattr(RandomNumberOfRandomObjectsRandomlyRecolourTests
                ,method_name
                ,test_recolouring_random_num_of_random_objs_random_cols
                )
            # method_names.append(method_name)

            yield RandomNumberOfRandomObjectsRandomlyRecolourTests(method_name)

    return API_unittest_TestCase_instances
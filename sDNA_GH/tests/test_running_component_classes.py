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
import unittest
import time
import itertools
import importlib

from ghpythonlib.componentbase import executingcomponent as component

from ..custom.skel.tools.helpers import checkers
from .. import launcher
from .helpers import FileAndStream, UDPStream, exit_Rhino



tests_log_file_suffix = '_unit_test_results'

API_TEST_MODULES = [os.path.splitext(file_)[0] 
                    for file_ in os.listdir(os.path.join(os.path.dirname(__file__), 'api_tests'))
                    if file_.endswith('.py')
                    if file_ not in ('__init__.py')
                   ]

print('API_TEST_MODULES: %s' % API_TEST_MODULES)

def make_test_running_component_class(package_location
                                     ,run_launcher_tests = None
                                     ,output_stream = sys.stderr
                                     ,test_suite = ()
                                     ):
    #type(ghpythonlib.componentbase.executingcomponent, str, Callable) -> TestRunningComponent
    """ Class Decorator to add in package location and replace 
        RunScript with a test launcher. 
    """


    if run_launcher_tests is None:

        output_stream.write('Exit Rhino after tests: %s (env var SDNA_GH_NON_INTERACTIVE)'
                           % ('Yes' if os.getenv('SDNA_GH_NON_INTERACTIVE', '') else 'No')
                           )

        exit = False if os.getenv('SDNA_GH_NON_INTERACTIVE', '').lower() in ('', '0', 'false') else True


        start_dir = package_location #os.path.join(package_location, launcher.package_name)

        if not test_suite:

            output_stream.write('Loading unit tests from: %s \n' % start_dir)
            test_suite = unittest.TestLoader().discover(start_dir = start_dir
                                                        # Non standard pattern ensures 
                                                        # tests requiring Grasshopper are
                                                        # skipped by the default discovery 
                                                        ,pattern = '*test*.py'
                                                        )
        else:
            print('Using test_suite: %s' % test_suite)

        def run_launcher_tests(self, *args):
            """ Set MyComponent.RunScript to this function to run sDNA_GH 
                unit tests in Grasshopper. 
            """            

            print('Starting RunScript')

            log_file_dir = os.path.dirname(checkers.get_path(fallback = package_location))
            if os.path.isfile(log_file_dir):
                log_file_path = os.path.splitext(log_file_dir)[0]
            else:
                log_file_path =  os.path.join(log_file_dir, launcher.PACKAGE_NAME)
            test_log_file_path = log_file_path + tests_log_file_suffix + '.log'
            test_log_file = open(test_log_file_path,'at')

            output_double_stream = FileAndStream(
                                         test_log_file
                                        ,output_stream
                                        ,print_too = output_stream is not sys.stderr
                                        )


            with output_double_stream as o:

                o.write('Unit test run started at: %s ... \n\n' % time.asctime())

                result = unittest.TextTestRunner(o, verbosity=2).run(test_suite)
                
                o.write('sDNA Test Summary\n')
                o.write('Errors: %s\n' % (result.errors,))
                o.write('Failures: %s\n' % (result.failures,))

                if not result.wasSuccessful():
                    # Special string to tell run_api_tests to return non-zero exit code
                    o.write('SDNA_GH_TESTS_FAILED')


            if exit and result.wasSuccessful():
                exit_Rhino()
                # exit_Rhino(23)
                # exit_Rhino(not result.wasSuccessful())
                
            
            # return (False, ) + tuple(repeat(None, len(self.Params.Output) - 1))
            # False is for "ok" not "output"
            return tuple(itertools.repeat(None, len(self.Params.Output) - 1))



    class TestRunningComponent(component):
        RunScript = run_launcher_tests


    return TestRunningComponent

def make_noninteractive_api_test_running_component_class(
                                                     package_location
                                                    ,test_name
                                                    ,port=9999
                                                    ,host='127.0.0.1'
                                                    ):
    if test_name in API_TEST_MODULES:
        module_names = [test_name]
    elif test_name.lower() == 'all':
        module_names = API_TEST_MODULES
    else:
        raise Exception('Invalid API test name: %s' % test_name)
    
    test_modules = {name : importlib.import_module('.tests.api_tests.%s' % name, 'sDNA_GH')
                    for name in module_names
                   }
    
    test_suite = unittest.TestSuite()

    for name, module in test_modules.items():
        if not hasattr(module, 'test_case_generator'):
            continue
        print('Adding test cases for module: %s' % name)
        test_case_generator = getattr(module, 'test_case_generator')
        for test_case in test_case_generator():
            test_suite.addTest(test_case)

    udp_stream = UDPStream(port, host)
    return make_test_running_component_class(package_location
                                            ,output_stream = udp_stream
                                            ,test_suite = test_suite
                                            )
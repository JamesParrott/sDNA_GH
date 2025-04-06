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

__authors__ = {'James Parrott', 'Crispin Cooper'}
__version__ = '3.0.2'

import os
import sys
import unittest
import time
import itertools
import importlib


import Cheetah_GH.unittest_runner

from ..skel.basic.smart_comp import NonObsoleteGHPythonComponent
from ..skel.tools.helpers import checkers
from .. import launcher
# from .helpers import (FileAndStream
#                      ,UDPStream
#                      ,exit_Rhino
#                      )



tests_log_file_suffix = '_unit_test_results'

API_TEST_MODULES = [os.path.splitext(file_)[0] 
                    for file_ in os.listdir(os.path.join(os.path.dirname(__file__), 'api_tests'))
                    if file_.endswith('.py')
                    if file_ not in ('__init__.py')
                   ]

print('API_TEST_MODULES: %s' % API_TEST_MODULES)

def make_test_running_component_class(run_launcher_tests = None
                                     ,log_file_dir = ''
                                     ,test_suite = ()
                                     ,start_dir = ''
                                     ,port=9999
                                     ,host='127.0.0.1'
                                     ):
    """ Class Decorator to add in package location and replace 
        RunScript with a test launcher. 
    """


    if os.path.isfile(log_file_dir):
        log_file_path = os.path.splitext(log_file_dir)[0]
    else:
        log_file_path =  os.path.join(log_file_dir, launcher.PACKAGE_NAME)
    log_file = log_file_path + tests_log_file_suffix + '.log'

    if run_launcher_tests is None:

        def run_launcher_tests(self, *args):
            """ Set MyComponent.RunScript to this function to run
                unit tests in Grasshopper. 
            """            

            print('Starting RunScript')
            Cheetah_GH.unittest_runner.start(log_file = log_file
                                            ,test_suite = test_suite
                                            ,start_dir = start_dir
                                            ,port = port
                                            ,host = host
                                            )

            return tuple(itertools.repeat(None, len(self.Params.Output) - 1))


    class TestRunningComponent(NonObsoleteGHPythonComponent):
        RunScript = run_launcher_tests


    return TestRunningComponent

def make_noninteractive_api_test_running_component_class(
                                                     test_name
                                                    ,log_file_dir
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



    return make_test_running_component_class(log_file_dir = log_file_dir
                                            ,test_suite = test_suite
                                            )
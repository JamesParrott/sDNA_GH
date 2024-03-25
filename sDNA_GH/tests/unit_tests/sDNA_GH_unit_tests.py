#! /usr/bin/awk NR==3
# -*- coding: utf-8 -*-
# This module requires Grasshopper Python (Rhino3D)

# MIT License

# Copyright (c) [2021] [Cardiff University, a body incorporated
# by Royal Charter and a registered charity (number:
# 1136855) whose administrative offices are at 7th floor 30-
# 36 Newport Road, UniversityCF24 0DE, Wales, UK]

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
__version__ = '3.0.0.alpha_1'

import sys
import os
import unittest
from time import asctime    
from itertools import repeat, izip
from collections import OrderedDict
import ctypes
import socket
import tempfile

from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
from ghpythonlib import treehelpers 

from ...custom.skel.basic.ghdoc import ghdoc 
from ... import main
from ... import launcher
from ...custom import tools
from ...custom.skel.tools.helpers import checkers

from ...custom import data_cruncher
from ...custom import gdm_from_GH_Datatree


TMP = tempfile.gettempdir()

DIR = TMP

for SUB_DIR in ( 'sDNA_GH', 'tests'):
    DIR = os.path.join(DIR, SUB_DIR)
    if not os.path.isdir(DIR):
        os.mkdir(DIR)


class FileAndStream():
    def __init__(self, file, stream):
        self.file = file
        self.stream = stream
        if hasattr(file, 'fileno'):
            self.fileno = file.fileno
        
    def write(self, *args):
        self.stream.write(*args)
        self.file.write(*args)
        
    def flush(self, *args):
        self.stream.flush()
        self.file.flush()
        
    def __enter__(self):
        self.file.__enter__()
        return self
        
    def __exit__(self, *args):
        return self.file.__exit__(*args)    







class TestDataCruncher(unittest.TestCase):
    def assert_raises_ValueError_when_same(self, f):
        with self.assertRaises(ValueError):
            f(2, 2)
        with self.assertRaises(ValueError):
            f(2.0, 2.0)
        with self.assertRaises(ValueError):
            f(0, 0)
        with self.assertRaises(ValueError):
            f(0.0, 0.0)
        with self.assertRaises(ValueError):
            f(0, 0.0)    

    def test_check_strictly_less_than(self):
        f = data_cruncher.check_strictly_less_than
        self.assertIsNone(f(4.5, 4.500001))
        self.assertIsNone(f(45, 46))
        self.assert_raises_ValueError_when_same(f)
        with self.assertRaises(ValueError):
            f(42, 40)
        with self.assertRaises(ValueError):
            f(42.0, 40.0)
        with self.assertRaises(ValueError):
            f(1, 0)
        with self.assertRaises(ValueError):
            f(1.0, 0.0)
        with self.assertRaises(ValueError):
            f(1, 0.0)
        
    def test_enforce_bounds(self):
        f = data_cruncher.enforce_bounds(lambda x, x_min, x_mid, x_max, *args : x)
        x_min, x_mid, x_max = 0, 'Not used', 10
        self.assertEqual(f(-5, x_min, x_mid, x_max, None, None), x_min)
        self.assertEqual(f(15, x_min, x_mid, x_max, None, None), x_max)

    def test_linearly_interpolate(self):
        f = data_cruncher.linearly_interpolate
        self.assertEqual(243, f(x = 8, x_min = 0, x_mid = 'Not used', x_max = 10, y_min = 3, y_max = 303))
        with self.assertRaises(ValueError):
            f(x = 10, x_min = 10, x_mid = 'Not used', x_max = 10, y_min = 3, y_max = 303)
        with self.assertRaises(ValueError):
            f(x = 10, x_min = 10, x_mid = 'Not used', x_max = 9, y_min = 3, y_max = 303)

    def test_check_not_eq(self):
        f = data_cruncher.check_not_eq
        self.assert_raises_ValueError_when_same(f)
        with self.assertRaises(ValueError):
            f(1499, -499, tol = 2000)
        with self.assertRaises(ValueError):
            f(-99.0, 1899.0, tol = 2000)

    def test_quadratic_mid_spline(self):
        f = data_cruncher.quadratic_mid_spline
        K = 87
        n = 10
        for i in range(n):
            x = i / (n+1)
            self.assertAlmostEqual(K*x*(2-x), f(x, x_min = 0, x_mid = 1, x_max = 2, y_min = 'not used', y_mid = K))

    def assert_in_bounds(self, f, P, K, n):
        for i in range(n):
            x = i / (n+1)
            self.assertLessEqual(f(x, x_min = 0, base = 10, x_max = 2, y_min = P, y_max = K), K)
            self.assertGreaterEqual(P, f(x, x_min = 0, base = 3, x_max = 2, y_min = P, y_max = K))

    def test_log_spline(self):
        self.assert_in_bounds(data_cruncher.log_spline, 29, 73, 10)

    def test_exp_spline(self):
        self.assert_in_bounds(data_cruncher.exp_spline, -53, 8, 10)

    def test_three_point_quad_spline(self):
        f = data_cruncher.three_point_quad_spline
        x_min, x_mid, x_max, y_min, y_mid, y_max = 0, 1, 2, -35, 53, 21
        self.assertAlmostEqual(y_min, f(x_min, x_min, x_mid, x_max, y_min, y_mid, y_max))
        self.assertAlmostEqual(y_mid, f(x_mid, x_min, x_mid, x_max, y_min, y_mid, y_max))
        self.assertAlmostEqual(y_max, f(x_max, x_min, x_mid, x_max, y_min, y_mid, y_max))
        # special case interpolation points

    def test_class_bounds_at_max_deltas(self):
        """ Even if correctly implemented, this is a poor classification method
            anyway.  Low priority for testing.
        """
        pass

    def test_max_interval_lt_width_w_with_most_data_points(self):
        f = lambda *args : str(data_cruncher.max_interval_lt_width_w_with_most_data_points(*args))
        Interval = data_cruncher.InclusiveInterval
        OrderedCounter = data_cruncher.OrderedCounter
        test_data = [#'expected' : 'input_'  
                    (str(Interval(5, 5, 5, 5, 7)), ([0,0,0,1,1,2,2,3,3,4,4,4,5,5,5,5,5,5,5,6,6,6,6,7,8,9,9], 5, 0.00001))
                    ]
        for element in test_data:
            expected, input_ = element
            actual = f(OrderedCounter(input_[0]), input_[1], input_[2])
            self.assertEqual(expected, actual)

    def test_spike_isolating_quantile(self):
        f = data_cruncher.spike_isolating_quantile  
        #input data must be sorted in ascending order
        test_data = [#'expected' : 'input_'  
                     ([], ([2,]*9, 7))
                    ,([0.5, 1.5], ([0,0] +[1]*9 + [2] * 9,7))
                    ,([[2.2651515007, 2.3030302524549997, 2.3409091234199999
                       ,2.4848486185050001, 2.6868686676050002, 2.99494946003]]
                     ,([2.24242424965, 2.25757575035, 2.25757575035 
                       ,2.2727272510500001, 2.2727272510500001, 2.3333332538599998
                       ,2.34848499298, 2.34848499298, 2.34848499298, 2.34848499298
                       ,2.6212122440300001, 2.6363637447400001, 2.6363637447400001
                       ,2.7373735904699998, 2.7373735904699998, 3.2525253295900001, 
                       3.5303030014000001
                       ], 7))
                    ]

GDM = gdm_from_GH_Datatree.GeomDataMapping

class TestCreateGeomDataMapping(unittest.TestCase):


    uuids = ['64ff5ea2-fc0a-4d0d-b5f2-0953156b8484'
            ,'48ea417c-42cf-4d4a-8df4-ea4da6a2489a'
            ,'8da406be-06f2-4527-8de9-e6a9720b63cd'
            ,'aae5eb82-a28b-4ae0-99db-03b76ebd86c0'
            ]

    opts = main.DEFAULT_OPTIONS

    #inputs = list(tuple(tuple(Geom_input, Data_input), expected_output))

    input_discrete_expected = [  
        ( ([], [[[],[]],[[],[]],[[],[]]])          , GDM([((),  [OrderedDict(), OrderedDict()])]) )
        ,( (None, None)                             , GDM() )
        ,( (list('abcd'),[[[],[]]]*4 + [1,2,3]) , GDM(izip(list('abcd'), repeat(OrderedDict()) )) )
        ,((uuids, None)                               , GDM(izip(uuids, repeat(OrderedDict()) ))  )
        ,( (None, [[['a','b','c'],['x','y','z'],[2,3,4]],[[1,2,3],[7,6.0,'A2'],['p','q','r']]]),
                     GDM([((), [ OrderedDict([('a',1),('b',2),('c',3)])
                                        ,OrderedDict([('x',7),('y',6.0),('z','A2')])
                                        ,OrderedDict([(2,'p'),(3,'q'),(4,'r')])
                                        ])]) 
          )
          ,(  ( uuids , [[['a','b','c'],['x','y','z'],[2,3,4]],[[1,2,3],[7,6.0,'A2'],['p','q','r']]] 
              ),   
                               GDM( zip(uuids, [ OrderedDict([('a',1),('b',2),('c',3)])
                                        ,OrderedDict([('x',7),('y',6.0),('z','A2')])
                                        ,OrderedDict([(2,'p'),(3,'q'),(4,'r')])
                                        ,OrderedDict()]) )                           
            )                     
                              ]

    input_almost_expected = [ ( ( []
                                 ,[12,34,23,68,45,23,3.0]
                                 )
                                ,GDM(   [( ()
                                        ,[12, 34, 23, 68, 45, 23, 3.0] 
                                        )
                                        ]
                                            ) 
                              )

                            ]

    input_not_equal = [ ((None
                         ,[[['a','b','c'],[1,2,3]]
                          ,[['x','y','z'],[7,6.0,'A2']]
                          ,[[2,3,4],['p','q','r']]
                          ]
                         )
                        ,GDM([((), [OrderedDict(a=1,b=2,c=2)
                                   ,OrderedDict(x=7,y=6.0,z='A2')
                                   ,OrderedDict([(2,'p'),(3,'q'),(4,'r')])
                                   ])]) #type: ignore
                        )
                      ]
   
    def conv_opts(self, x):
        return gdm_from_GH_Datatree.GeomDataMapping.from_DataTree_and_list(x[0], x[1])
    def get_expected_and_actual(self, f, l):
        for x in l:
            yield x[1], f(x[0])

    def test_discrete_input(self):
        self.assertEqual(*zip(*list(self.get_expected_and_actual(
                                                 self.conv_opts
                                                ,self.input_discrete_expected
                                                ))))


    def test_floating_point_input(self):
        for expected, actual in self.get_expected_and_actual(
                                                     self.conv_opts
                                                    ,self.input_almost_expected
                                                    ):
            self.assertEqual(expected, actual)

    def test_not_equal(self):
        self.assertNotEqual(*zip(*list(self.get_expected_and_actual(
                                                            self.conv_opts
                                                           ,self.input_not_equal
                                                           ))))

def test_empty_DataTree(self):
        
        #inputs = list(tuple(tuple(Geom_input, Data_input), expected_output))
    self.input_data_tree = [(([None], treehelpers.list_to_tree(None)), OrderedDict())]
    self.assertEqual(*zip(*list(self.get_expected_and_actual(
                                                 self.conv_opts
                                                ,self.input_data_tree
                                                ))))

#if GH_env_exists:
TestCreateGeomDataMapping.test_empty_DataTree = test_empty_DataTree

tests_log_file_suffix = '_unit_test_results'





class UDPStream(object):
    def __init__(self, port, host):
        self.port = port
        self.host = host
        # SOCK_DGRAM is the socket type to use for UDP sockets
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    def write(self, str_):
        # https://docs.python.org/3/library/socketserver.html#socketserver-udpserver-example
        data = str_.encode("utf-8")
        self.sock.sendto(data, (self.host, self.port))

    def flush(self):
        pass






def save_doc_to_DIR(name = 'tmp_sDNA_GH_api_tests_working_file.3dm'):
    # 'Dale Fugier'
    # https://discourse.mcneel.com/t/sys-exit-shows-popup-window-instead-of-just-exiting/163811/7

    path = os.path.join(DIR, name)
    Rhino.RhinoApp.RunScript('_-SaveAs ' + path, True)
    





def exit_Rhino():
    #'Dale Fugier'
    # https://discourse.mcneel.com/t/sys-exit-shows-popup-window-instead-of-just-exiting/163811/7

    save_doc_to_DIR()
    Rhino.RhinoDoc.ActiveDoc.Modified = False

    hWnd = Rhino.RhinoApp.MainWindowHandle()
    ctypes.windll.user32.PostMessageW(hWnd, 0x0010, 0, 0) # - quits but doesn't set return code
    # ctypes.windll.user32.PostQuitMessage(ret_code) # - doesn't quit, even if Rhino doc saved.
    # ctypes.windll.user32.PostMessageW(hWnd, 0x0010, ret_code, 0) # - quits but doesn't set return code
    # ctypes.windll.user32.PostMessageW(hWnd, 0x0012, ret_code, 0) # - makes Rhino hang. ret code 1 is set
    #                                                              # after killing it from Task Manager.


def make_test_running_component_class(Component
                                     ,package_location
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

        def run_launcher_tests(self, *args):
            """ Set MyComponent.RunScript to this function to run sDNA_GH 
                unit tests in Grasshopper. 
            """            

            log_file_dir = os.path.dirname(checkers.get_path(fallback = package_location))
            if os.path.isfile(log_file_dir):
                log_file_path = os.path.splitext(log_file_dir)[0]
            else:
                log_file_path =  os.path.join(log_file_dir, launcher.PACKAGE_NAME)
            test_log_file_path = log_file_path + tests_log_file_suffix + '.log'
            test_log_file = open(test_log_file_path,'at')
            output_double_stream = FileAndStream(test_log_file, output_stream)

            with output_double_stream as o:

                o.write('Unit test run started at: %s ... \n\n' % asctime())

                result = unittest.TextTestRunner(o, verbosity=2).run(test_suite)
                
                o.write('sDNA API Test Summary')
                o.write('Errors: %s' % (result.errors,))
                o.write('Failures: %s' % (result.failures,))

                if not result.wasSuccessful():
                    # Special string to tell run_api_tests to return non-zero exit code
                    o.write('SDNA_GH_API_TESTS_FAILED')


            if exit:
                exit_Rhino()
                # exit_Rhino(23)
                # exit_Rhino(not result.wasSuccessful())
                
            
            # return (False, ) + tuple(repeat(None, len(self.Params.Output) - 1))
            # False is for "ok" not "output"
            return tuple(repeat(None, len(self.Params.Output) - 1))



    class TestRunningComponent(Component):
        _RunScript = Component.RunScript
        RunScript = run_launcher_tests


    return TestRunningComponent

def make_noninteractive_test_running_component_class(Component
                                                    ,package_location
                                                    ,test_suite
                                                    ,port=9999
                                                    ,host='127.0.0.1'
                                                    ):
    udp_stream = UDPStream(port, host)
    return make_test_running_component_class(Component
                                            ,package_location
                                            ,output_stream = udp_stream
                                            ,test_suite = test_suite
                                            )
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
__version__ = '0.05'

import sys
import os
import unittest
from time import asctime    
from itertools import repeat, izip
from collections import OrderedDict


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
from ...custom import gdm_from_GH_Datatree
from ...custom.skel.tools.helpers import checkers
                            


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





class TestStringMethods(unittest.TestCase):
    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')
    
    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())
    
    def test_split(self):
        s = 'hello world'
        print(s)
        self.assertEqual(s.split(), ['hello', 'world'])
        
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)





class TestCreateGeomDataMapping(unittest.TestCase):


    uuids = ['64ff5ea2-fc0a-4d0d-b5f2-0953156b8484'
            ,'48ea417c-42cf-4d4a-8df4-ea4da6a2489a'
            ,'8da406be-06f2-4527-8de9-e6a9720b63cd'
            ,'aae5eb82-a28b-4ae0-99db-03b76ebd86c0'
            ]

    opts = main.default_options

    #inputs = list(tuple(tuple(Geom_input, Data_input), expected_output))

    input_discrete_expected = [  
        ( ([], [[[],[]],[[],[]],[[],[]]])          , OrderedDict([((),  [OrderedDict(), OrderedDict()])]) )
        ,( (None, None)                             , OrderedDict() )
        ,( (list('abcd'),[[[],[]]]*4 + [1,2,3]) , OrderedDict(izip(list('abcd'), repeat(OrderedDict()) )) )
        ,((uuids, None)                               , OrderedDict(izip(uuids, repeat(OrderedDict()) ))  )
        ,( (None, [[['a','b','c'],['x','y','z'],[2,3,4]],[[1,2,3],[7,6.0,'A2'],['p','q','r']]]),
                     OrderedDict([((), [ OrderedDict([('a',1),('b',2),('c',3)])
                                        ,OrderedDict([('x',7),('y',6.0),('z','A2')])
                                        ,OrderedDict([(2,'p'),(3,'q'),(4,'r')])
                                        ])]) 
          )
          ,(  ( uuids , [[['a','b','c'],['x','y','z'],[2,3,4]],[[1,2,3],[7,6.0,'A2'],['p','q','r']]] 
              ),   
                               OrderedDict( zip(uuids, [ OrderedDict([('a',1),('b',2),('c',3)])
                                        ,OrderedDict([('x',7),('y',6.0),('z','A2')])
                                        ,OrderedDict([(2,'p'),(3,'q'),(4,'r')])
                                        ,OrderedDict()]) )                           
            )                     
                              ]

    input_almost_expected = [ ( ( []
                                 ,[12,34,23,68,45,23,3.0]
                                 )
                                ,OrderedDict( [( ()
                                                ,[12, 34, 23, 68, 45, 23, 3.0] 
                                               )
                                              ]
                                            ) 
                              )

                            ]

    input_not_equal = [ ( (None, [[['a','b','c'],[1,2,3]],[['x','y','z'],[7,6.0,'A2']],[[2,3,4],['p','q','r']]]),
                     OrderedDict([((), [ OrderedDict(a=1,b=2,c=2)
                                        ,OrderedDict(x=7,y=6.0,z='A2')
                                        ,OrderedDict([(2,'p'),(3,'q'),(4,'r')])
                                        ])]) #type: ignore
                        )
                      ]
   
    def conv_opts(self, x):
        return gdm_from_GH_Datatree.gdm_from_DataTree_and_list(x[0], x[1])
    def get_expected_and_actual(self, f, l):
        return [x[1] for x in l], [f(x[0]) for x in l]

    def test_discrete_input(self):
        self.assertEqual(  *self.get_expected_and_actual(self.conv_opts
                                                        ,self.input_discrete_expected
                                                        )
                        )
    def test_floating_point_input(self):
        self.assertAlmostEqual(  *self.get_expected_and_actual(self.conv_opts
                                                              ,self.input_almost_expected
                                                              )
                              )

    def test_not_equal(self):
        self.assertNotEqual(  *self.get_expected_and_actual(self.conv_opts
                                                           ,self.input_not_equal
                                                           )
                           )

def test_empty_DataTree(self):
        
        #inputs = list(tuple(tuple(Geom_input, Data_input), expected_output))
    self.input_data_tree = [(([None], treehelpers.list_to_tree(None)), OrderedDict())]
    self.assertEqual(  *self.get_expected_and_actual(self.conv_opts
                                                ,self.input_data_tree
                                                )
                    )

#if GH_env_exists:
TestCreateGeomDataMapping.test_empty_DataTree = test_empty_DataTree

tests_log_file_suffix = '_unit_test_results'

def run_launcher_tests(self, *args):
    """ Set MyComponent.RunScript to this function to unit tests in Grasshopper. """
    log_file_dir = os.path.dirname(checkers.get_path(fallback = self.fallback))
    if os.path.isfile(log_file_dir):
        log_file_path = os.path.splitext(log_file_dir)[0]
    else:
        log_file_path =  os.path.join(log_file_dir, launcher.package_name)

    test_log_file_path = log_file_path + tests_log_file_suffix + '.log'
    test_log_file = open(test_log_file_path,'at')
    output_double_stream = FileAndStream(test_log_file, sys.stderr)
    output_double_stream.write( 'Unit test run started at: ' 
                                +asctime()
                                +' ... \n\n')
    with output_double_stream as o:

        discovered_suite = unittest.TestLoader().discover( self.fallback 
                                                        ,'*test*.py'
                                                        )
        unittest.TextTestRunner(o, verbosity=2).run(discovered_suite)
        
        
    
    return (False, ) + tuple(repeat(None, len(self.Params.Output) - 1))

""" if ( __name__ == '__main__' and
     '__file__' in dir(__builtins__) and
     sys.argv[0] == __file__):   
        class ProxyComponentForRunLauncher():
            sDNA_GH_path = dirname(dirname(sys.path[0]))
            sDNA_GH_package = ''
        run_launcher_tests(ProxyComponentForRunLauncher(), True, [], [], '') """



""" class MyComponent(component):
    
    def RunScript(self, x, y):
        
        import sys
        
        class TestStringMethods(unittest.TestCase):
        
            def test_upper(self):
                self.assertEqual('foo'.upper(), 'FOO')
        
            def test_isupper(self):
                self.assertTrue('FOO'.isupper())
                self.assertFalse('Foo'.isupper())
        
            def test_split(self):
                s = 'hello world'
                self.assertEqual(s.split(), ['hello', 'world'])
                
                # check that s.split fails when the separator is not a string
                with self.assertRaises(TypeError):
                    s.split(2)
                    
        test_log_file = open(test_log_file_path,'at')
        output_double_stream = FileAndStream(test_log_file, sys.stderr)
        output_double_stream.write( 'Unit test run started at: ' 
                                   +asctime()
                                   +' ... \n\n')
        with output_double_stream as o:
            suite = unittest.TestLoader().loadTestsFromTestCase(TestStringMethods)
            unittest.TextTestRunner(o, verbosity=2).run(suite)
            
        a=''
        return a """

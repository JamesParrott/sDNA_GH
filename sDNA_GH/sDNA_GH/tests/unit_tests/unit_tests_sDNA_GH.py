import unittest, sys
from os.path import dirname, join
from time import asctime    
from itertools import repeat, izip
from collections import OrderedDict

#from ghpythonlib.componentbase import executingcomponent as component
#import Grasshopper, GhPython
#import System
#import Rhino
#import rhinoscriptsyntax as rs

from ...tools import (  opts
                        ,convert_Data_tree_and_Geom_list_to_gdm
                        )





class FileAndStream():
    def __init__(self, file, stream):
        self.file = file
        self.stream = stream
        
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


    uuids = [ '64ff5ea2-fc0a-4d0d-b5f2-0953156b8484'
           ,'48ea417c-42cf-4d4a-8df4-ea4da6a2489a'
           ,'8da406be-06f2-4527-8de9-e6a9720b63cd'
           ,'aae5eb82-a28b-4ae0-99db-03b76ebd86c0'
          ]

    opts = opts['options']
    input_discrete_expected = [  
        ( ([], [[[],[]],[[],[]],[[],[]]])          , OrderedDict([((),  [OrderedDict(), OrderedDict()])]) )
        ,( (None, None)                             , OrderedDict() )
        ,( (list('abcd'),[[[],[]]]*4 + [1,2,3]) , OrderedDict(izip(list('abcd'), repeat(OrderedDict()) )) )
        ,((uuids, None)                               , OrderedDict(izip(uuids, repeat(OrderedDict()) ))  )
        ,( (None, [[['a','b','c'],['x','y','z'],[2,3,4]],[[1,2,3],[7,6.0,'A2'],['p','q','r']]]),
                     OrderedDict([((), [ OrderedDict([('a',1),('b',2),('c',3)])
                                        ,OrderedDict([('x',7),('y',6.0),('z','A2')])
                                        ,OrderedDict([(2,'p'),(3,'q'),(4,'r')])
                                        ])]) #type: ignore
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

    #print('From testCreateGDM: ' + str([x[0] for x in input_discrete_expected]))
    #print('From testCreateGDM: ' + str(input_discrete_expected[0][0]))
    #print('From testCreateGDM: ' + ' '.join( str(x[0][i]) for x in [ input_discrete_expected[0] ] for i in (0,1)) )
    #print('From testCreateGDM: ' + str(convert_Data_tree_and_Geom_list_to_gdm( input_discrete_expected[0][0][0]
    #                                        ,input_discrete_expected[0][0][1]
    #                                        ,opts 
    #                                        )
    #                                    )
    #      )

    #print('From testCreateGDM: ' + str(input_discrete_expected[0][0]))
    #print('From testCreateGDM: ' + str(input_discrete_expected[0][0]))
    
    def conv_opts(self, x):
        return convert_Data_tree_and_Geom_list_to_gdm(x[0], x[1], self.opts)

    def get_expected_and_actual(self, f, l):
        return [x[1] for x in l], [f(x[0]) for x in l]

    def test_discrete_input(self):
        self.assertEqual(  *self.get_expected_and_actual(self.conv_opts
                                                        ,self.input_discrete_expected
                                                        )
                        )
    def test_floating_point_input(self):
        self.assertAlmostEqual(  *self.get_expected_and_actual( self.conv_opts
                                                                ,self.input_almost_expected
                                                                )
                              )

    def test_not_equal(self):
        self.assertNotEqual(  *self.get_expected_and_actual(self.conv_opts
                                                        ,self.input_not_equal
                                                        )
                        )
    #print conv([], [[[],[]],[[],[]],[[],[]]], opts)
    #print conv(Geom, Data, opts)
    #sc.doc = Rhino.RhinoDoc.ActiveDoc
    #objs = rs.ObjectsByType(4)
    #print( conv( ['a','b','c','d']
    #            ,[[[],[]]]*4+ [1,2,3]
    #            ,opts).items() 
    #        )
    #sc.doc = ghdoc
    #print( conv([], [12,34,23,68,45,23,3.0], opts))


def run_launcher_tests(self, go, Data, Geom, f_name, *args):
    import sys
    tests_log_file_suffix = '_test_results'
    test_log_file_path = (    self.ghdoc.Path.rpartition('.')[0]  #type: ignore
                            + tests_log_file_suffix
                            + '.log' )
    test_log_file = open(test_log_file_path,'at')
    output_double_stream = FileAndStream(test_log_file, sys.stderr)
    output_double_stream.write( 'Unit test run started at: ' 
                                +asctime()
                                +' ... \n\n')
    with output_double_stream as o:
        #suite = unittest.TestLoader().loadTestsFromTestCase(TestStringMethods)
        path = self.sDNA_GH_path
        discovered_suite = unittest.TestLoader().discover( path 
                                                          ,'*test*.py'
                                                          )
        #unittest.TextTestRunner(o, verbosity=2).run(suite)
        unittest.TextTestRunner(o, verbosity=2).run(discovered_suite)
        
        
    a=''
    return a   

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

from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import unittest
from time import asctime



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
        suite = unittest.TestLoader().loadTestsFromTestCase(TestStringMethods)
        unittest.TextTestRunner(o, verbosity=2).run(suite)
        
    a=''
    return a   


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

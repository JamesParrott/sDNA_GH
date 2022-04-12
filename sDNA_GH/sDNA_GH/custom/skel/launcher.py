#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys
from os.path import join

from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper

plug_in_name = 'test_plug_in'

module_path = join(Grasshopper.Folders.DefaultUserObjectFolder, plug_in_name)

if module_path not in sys.path:
    sys.path.insert(0, module_path)

class MyComponent(component):   # needed by parser, even if 
    pass                        # in code that doesn't run

from test_module.skel.basic.smart_comp import SmartComponent
MyComponent = SmartComponent
# import sys

# from ghpythonlib.componentbase import executingcomponent as component
# import Grasshopper, GhPython
# import System
# import Rhino
# import rhinoscriptsyntax as rs

# module_path = r'C:\Users\James\Documents\Rhino\Grasshopper'
# if module_path not in sys.path:
#     sys.path.insert(0, module_path)

# if 'define_new_GH_comp_class' in sys.modules:
#     define_new_GH_comp_class = sys.modules['define_new_GH_comp_class']
#     reload(define_new_GH_comp_class)
# else:
#     import define_new_GH_comp_class
    
# class MyComponent(component):   # needed by parser, even if 
#     pass                        # in code that doesn't run
# MyComponent = define_new_GH_comp_class.MyComponent  
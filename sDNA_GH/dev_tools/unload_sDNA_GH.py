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
__version__ = '0.00'

import sys

from ghpythonlib.componentbase import executingcomponent as component
import rhinoscriptsyntax as rs

class MyComponent(component):
    
    def RunScript(self, unload, update):

        #print('\n'.join([key for key in sys.modules if 'sDNA' in key]))
        #print('functools' in sys.modules)
        print('sDNA_GH packages and modules in sys.modules:')
        print('\n'.join([key for key in sys.modules if 'sdna' in key.lower()]))# and not '.' in key]))
        #print os.getenv('APPDATA')
        #print ghdoc.Path
        #print Grasshopper.Folders.DefaultAssemblyFolder
        #print Grasshopper.Folders.AppDataFolder
        #print sys.argv[0]
        #print("Classmethod found == " + str('classmethod' in __builtins__))
        def is_imported(s):
            return s in sys.modules
        if unload is True:
            if 'logging' in sys.modules:
                sys.modules['logging'].shutdown()
            shared_cached_modules_etc = sys.modules.copy().keys()
            for y in shared_cached_modules_etc:
                if 'sDNA' in y or y == 'runsdnacommand':
                    del sys.modules[y]
        
        
                
        print('sDNA_GH imported == %s' % is_imported('sDNA_GH'))
        print('sDNA_GH.tools imported == %s' % is_imported('sDNA_GH.tools'))
        print('sDNAUISpec imported == %s' % is_imported('sDNAUISpec'))
        print('runsdnacommand == %s' % is_imported('runsdnacommand'))
        if False: #is_imported('sDNA_GH'):
            print(sys.modules['sDNA_GH'].__all__)
            print(dir(sys.modules['sDNA_GH']))
            if is_imported('sDNA_GH.tools'):
                print( dir(sys.modules['sDNA_GH.tools']))
            if hasattr(sys.modules['sDNA_GH'],'third_party_python_modules'):
                print(dir(sys.modules['sDNA_GH'].third_party_python_modules))
        

        #print('\n'.join(dir(sys.modules['sDNA_GH'].third_party_python_modules)))
        
        return 
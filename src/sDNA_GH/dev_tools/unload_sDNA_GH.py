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

""" Unload the sDNA_GH Python package and all sDNA modules, by removing them from GhPython's shared cache (sys.modules).  The 
    next sDNA_GH component to run will then reload the package and installation-wide options file (config.toml), and any specified 
    options including a project specific config.toml, without otherwise having to restart Rhino to clear its cache.
"""

__authors__ = {'James Parrott', 'Crispin Cooper'}
__version__ = '3.0.0'


from ghpythonlib.componentbase import executingcomponent as component


ghenv.Component.ToggleObsolete(False)

IMPORTS_TO_UNLOAD = {'sdna'
                    ,'shapefile'
                    ,'toml_tools' 
                    ,'mapclassif'
                    ,'anteater'
                    ,'cheetah'
                    }   

class MyComponent(component):
    
    def RunScript(self, unload, update):
        import sys  #Imported here to avoid weird bug 
                    # (unloading/forgetting of sys - IronPython only?)
        #https://discourse.mcneel.com/t/failed-import-of-sys-library-in-ghpython/98696


        print('sDNA_GH packages and modules in sys.modules:')
        print('\n'.join([key for key in sys.modules if 'sdna' in key.lower()]))
        def is_imported(s):
            return s in sys.modules
        if unload is True:
            if 'logging' in sys.modules:
                sys.modules['logging'].shutdown()
            shared_cached_modules_etc = sys.modules.copy().keys()
            for y in shared_cached_modules_etc:
                if any(s in y.lower() for s in IMPORTS_TO_UNLOAD):
                    del sys.modules[y]
        
        
                
        print('sDNA_GH imported == %s' % is_imported('sDNA_GH'))
        print('sDNA_GH.tools imported == %s' % is_imported('sDNA_GH.tools'))
        print('sDNAUISpec imported == %s' % is_imported('sDNAUISpec'))
        print('runsdnacommand == %s' % is_imported('runsdnacommand'))

        
        return 
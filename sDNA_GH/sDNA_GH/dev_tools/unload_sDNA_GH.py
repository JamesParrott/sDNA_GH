#! Grasshopper Python
# -*- coding: utf-8 -*-
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
#! Grasshopper Python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.00'

import sys

from ghpythonlib.componentbase import executingcomponent as component
import rhinoscriptsyntax as rs

class MyComponent(component):
    
    def RunScript(self, unload, update):

        #logger.debug('\n'.join([key for key in sys.modules if 'sDNA' in key]))
        #logger.debug('functools' in sys.modules)
        logger.debug('sDNA_GH packages and modules in sys.modules:')
        logger.debug('\n'.join([key for key in sys.modules if 'sdna' in key.lower()]))# and not '.' in key]))
        #logger.debug os.getenv('APPDATA')
        #logger.debug ghdoc.Path
        #logger.debug Grasshopper.Folders.DefaultAssemblyFolder
        #logger.debug Grasshopper.Folders.AppDataFolder
        #logger.debug sys.argv[0]
        #logger.debug("Classmethod found == " + str('classmethod' in __builtins__))
        def is_imported(s):
            return s in sys.modules
        if unload is True:
            if 'logging' in sys.modules:
                sys.modules['logging'].shutdown()
            shared_cached_modules_etc = sys.modules.copy().keys()
            for y in shared_cached_modules_etc:
                if 'sDNA' in y or y == 'runsdnacommand':
                    del sys.modules[y]
        
        
                
        logger.debug('sDNA_GH imported == %s' % is_imported('sDNA_GH'))
        logger.debug('sDNA_GH.tools imported == %s' % is_imported('sDNA_GH.tools'))
        logger.debug('sDNAUISpec imported == %s' % is_imported('sDNAUISpec'))
        logger.debug('runsdnacommand == %s' % is_imported('runsdnacommand'))
        if False: #is_imported('sDNA_GH'):
            logger.debug(sys.modules['sDNA_GH'].__all__)
            logger.debug(dir(sys.modules['sDNA_GH']))
            if is_imported('sDNA_GH.tools'):
                logger.debug( dir(sys.modules['sDNA_GH.tools']))
            if hasattr(sys.modules['sDNA_GH'],'third_party_python_modules'):
                logger.debug(dir(sys.modules['sDNA_GH'].third_party_python_modules))
        

        #logger.debug('\n'.join(dir(sys.modules['sDNA_GH'].third_party_python_modules)))
        
        return 
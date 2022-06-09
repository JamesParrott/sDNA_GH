#! /usr/bin/python as module, Grasshopper Python as script / main
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys
import os
import functools
from importlib import import_module

def is_builtin(name):
    #type(str) -> bool
    """ Checks if a variable named name is in __builtins__, even if it's a dict
    
        In some Python implementations (such as in GhPython), __builtins__ is 
        a dict, not a module as normal elsewhere.
    """
    return hasattr(__builtins__, 'reload') or (isinstance(__builtins__, dict)
                                               and name in __builtins__ )

if not is_builtin('reload'):
    from importlib import reload 
    # reload was builtin until Python 3.4



if not is_builtin('basestring'):
    basestring = str
    # basestring is the ABC of str and unicode in Python 2
    # In Python 3 str supports unicode and there is no unicode type

sDNA_GH_subfolder = 'sDNA_GH' 
sDNA_GH_package = 'sDNA_GH'               
reload_already_imported = False


# There may be multiple components, all running this same launcher code.
# Therefore we want the root logger to live in the sDNA_GH.main module
# that they each import.  The logging system is configurable by the user,
# but only through the options that are read in during the main package
# import, and we want to create logs before this too.  So before a 
# component has imported sDNA_GH.main, logging is routed through output, 
# a callable instance of Output, with a cache, defined below.  output's cache 
# is flushed through the normal logging system, after a logger has been set up 
# according to the user's configuration, after the main package import.
#
# This Output class is used to define two Classes from this single 
# code definition.  Python scripts can happily import themselves, but here
# this is because all the code in this file 
# must be read into a GhPython component via its the code input (which 
# essentially copy and pastes it to there).
# The first function definition is when the code in this file runs 
# in a GH component.  
# The second function definition is during import of sDNA_GH below, 
# as it itself imports this function from .launcher
# Therefore there really are two functions in Python, with two separate caches.
#
# The behaviours can be different of course if changes are made to one and not
# the other, e.g. if updated code is forgotten to be copied into the component.

class Output(object): 

    def set_logger(self, logger, flush = True):
        self.logger = logger
        if flush and self.tmp_logs:
            self.flush()

    def __init__(self
                ,tmp_logs = None
                ,logger = None
                ):
        if not isinstance(tmp_logs, list): #assert not isinstance(None, list)
            tmp_logs = []
        self.tmp_logs = tmp_logs
        if logger is not None:
            self.set_logger(logger, flush = False)



    def store(self, message, logging_level):
        self.tmp_logs.append( (message, logging_level) )

    def __call__(self, message, logging_level = "INFO", logging_dict = {}):
        #type: (str, str, dict, list) -> str
        
        #print(s)

        if logging_dict == {} and hasattr(self, 'logger'): 
            logging_dict = dict( DEBUG = self.logger.debug
                                ,INFO = self.logger.info
                                ,WARNING = self.logger.warning
                                ,ERROR = self.logger.error
                                ,CRITICAL = self.logger.critical
                                )

        logging_level = logging_level.upper()
        if logging_level in logging_dict:
            logging_dict[logging_level](message)
        else:
            self.store(message, logging_level)

        return logging_level + ' : ' + message + ' '

    def __getattr__(self, attr):
        return functools.partial(self.__call__, logging_level = attr.upper())

    def flush(self):
        tmp_logs = self.tmp_logs[:] # __call__ might cache back to tmp_logs
        self.tmp_logs[:] = [] # Mutate list initialised with.  Avoid double 
                              # logging in case re - stored in tmp_logs
        for tmp_log_message, tmp_log_level in tmp_logs:
            self.__call__(tmp_log_message, tmp_log_level)

output = Output()


class InvalidArgsError(Exception):
    
    """Custom exception to log the error message, and to at least allow 
       attempts to give users actionable advice to fix the issue, in 
       the event of a problem.  
    """
    message_fmt = 'Invalid import args: %s'
    def __init__(self
                ,message_fmt = ''
                ,message = ''
                ,logger = output
                , **kwargs
                ):
        if message_fmt and isinstance(message_fmt, basestring):
            self.message_fmt = message_fmt
        if not message or not isinstance(message, basestring):
            message = self.message_fmt % kwargs
        logger.error(message)
        self.kwargs = kwargs
        super(Exception, self).__init__(message)    


class ModuleNameError(Exception):
    message_fmt = 'Invalid module name: %s'


class FilePathError(Exception):
    message_fmt = 'Invalid path to import module from: %s'


# We only know the sDNA version to import as a string.  This is more secure too.
def strict_import(module_name = ''
                 ,folder = ''
                 ,sub_folder = ''
                 ,logger = output
                 ,reload_already_imported = reload_already_imported
                 ,search_folder_only = False
                 ):

    # type: (str, str, str, type[any], bool, bool) -> type[any]
    """ Imports the named module from the specified folder\subfolder only, 
        and returns it.
        
        Avoids name clashes and casual hijack attempts.  In some 
        environments supporting a Python implementation (such as 
        GhPython in Grasshopper) it may not be desireable to ask the user 
        to set PYTHONPATH.  Hence here, we save sys.path to a tmp 
        variable, set sys.path to the specified folders, attempt the 
        import in a try: block, and restore sys.path in a finally: block
    """
    if not module_name or not isinstance(module_name, basestring):
        raise ModuleNameError(module_name = module_name
                             ,folder = folder
                             ,sub_folder = sub_folder
                             ,logger = logger
                             )
    logger.debug(module_name)
    if module_name in sys.modules:   # sys.modules is also shared between GHPython components 
                                     # (and is even saved until Rhino is closed).
        logger.debug('Module %s already in sys.modules' % module_name)
        if reload_already_imported:
            logger.debug('Reloading %s.... ' % module_name)
            reload(sys.modules[module_name]) # type: ignore
        return sys.modules[module_name]
    #
    #
    # Load module_name for first time:
    #
    #
    search_path = os.path.join(folder, sub_folder)

    tmp = sys.path
    if (search_path 
        and isinstance(search_path, basestring) 
        and os.path.isdir(search_path)):
        #
        logger.debug('Search path == %s' % search_path)
        if search_folder_only:
            sys.path = [search_path]
        else:
            sys.path.insert(0, search_path)
    else:
        raise FilePathError(module_name = module_name
                           ,search_path = search_path
                           ,logger = logger
                           )

    logger.debug('Trying import... ')
    tmp = sys.path
    sys.path = [search_path]
    try:
        module = import_module(module_name, '')           
    except ImportError:
        pass
    finally:
        sys.path = tmp
    return module       


class ModulesNotFoundError(Exception):
    message_fmt = 'Modules not found in any location %s'


def load_modules(m_names
                ,folders
                ,logger = output
                ,module_name_error_msg = 'Please supply valid names of modules to import, %s'
                ,folders_error_msg = 'Please supply valid folders to import from, %s'
                ,modules_not_found_msg = 'Specified modules not found in any folder, %s'):
    #type(str/ Iterable, list, type[any], str, str) -> tuple / None
    """ Tries to import all modules in m_names, from the first folder in 
        folders to contain a .py or .pyc files with the same name as each 
        module.

        Returns a tuple of all the modules and the folder, else 
        raises a ModuleNotFoundError.
    """
    if not m_names or not any( isinstance(m_name, basestring) 
                               for m_name in m_names ):
        raise ModuleNameError(message_fmt = module_name_error_msg
                             ,m_names = m_names
                             ,logger = logger
                             )
    
    if isinstance(m_names, basestring):
        m_names = [m_names] 
    logger.debug('m_names == %s of type : %s' % (m_names, type(m_names).__name__))

    logger.debug('Testing paths : %s ' % folders)
    logger.debug('Type(folders) : %s' % type(folders).__name__)

    if not any(os.path.isdir(folder) or os.path.isdir(os.path.dirname(folder)) 
               for folder in folders
              ):
        raise FilePathError(message_fmt = folders_error_msg
                           ,m_names = m_names
                           ,logger = logger
                           )

    for folder in folders:
        logger.debug('Type(folder) : %s' % type(folder).__name__)
        logger.debug('Type(path) : %s path == %s' %(type(folder).__name__, folder))

        if os.path.isfile(folder):
            folder = os.path.dirname(folder)
        if all( any(os.path.isfile(os.path.join(folder, name.replace('.', os.sep) + ending)) 
                    for ending in ['.py','.pyc'] 
                   )
                for name in m_names
                if isinstance(name, basestring)
              ):
            #
            logger.debug('Importing %s' % m_names)

            return tuple(strict_import(name, folder, '', logger = logger) 
                            for name in m_names
                        ) + (folder,)
            # tuple of modules, followed by the path to them
    raise ModuleNotFoundError(message_fmt = modules_not_found_msg
                             ,m_names = m_names
                             ,folders = folders
                             ,logger = logger
                             )



if __name__ == '__main__': # False in a compiled component.  But then the user
                           # can't add or remove Params to the component.  
    
    # Grasshopper will look for class MyComponent(component) in global scope
    # so a main function is a little tricky to define.

    from ghpythonlib.componentbase import executingcomponent as component
    import Grasshopper
    import scriptcontext as sc
    # Do Grasshopper API imports here separately to
    # Let the above functions be accessed outside the GhPython


    sDNA_GH_search_paths = [ os.path.join(Grasshopper.Folders.DefaultUserObjectFolder
                                         , sDNA_GH_subfolder
                                         ) 
                           ]
                                            #join(Grasshopper.Folders.DefaultAssemblyFolder, sDNA_GH_subfolder) ]  
                                            # Grasshopper.Folders.AppDataFolder + r'\Libraries'
                                            # %appdata%  + r'\Grasshopper\Libraries'
                                            # os.getenv('APPDATA') + r'\Grasshopper\Libraries'
                                            # Grasshopper.Folders.AppDataFolder + r'\UserObjects'
                                            # %appdata%  + r'\Grasshopper\UserObjects'
                                            # os.getenv('APPDATA') + r'\Grasshopper\UserObjects'

    sDNA_GH_search_paths += [os.path.join(Grasshopper.Folders.DefaultAssemblyFolder
                                         ,sDNA_GH_subfolder
                                         ) 
                            ]  # Might need to install sDNA_GH 
                               # in \Grasshopper\Libraries in Rhino 6?

    nick_name = ghenv.Component.NickName #type: ignore


    sc.doc = ghdoc #type: ignore

    print(sDNA_GH_search_paths)

    ModuleNameError

    class sDNA_GH_Installation_Path_Error(FilePathError):
        message_fmt = ''

    class sDNA_GH(object):
        pass

    error_message =1
    sDNA_GH.main, _ = load_modules(sDNA_GH_package + '.main'
                                   ,sDNA_GH_search_paths
                                   ,folders_error_msg = 'Please install sDNA_GH according to README.md,'
                                                        +' ensuring a folder called '
                                                        +sDNA_GH_subfolder + os.sep + sDNA_GH_package
                                                        +' is created in '
                                                        +Grasshopper.Folders.DefaultUserObjectFolder                                                                    
                                                        +', and that main.py and all sDNA_GH python' 
                                                        +' files and subfolders are inside it. ' 
                                   ,modules_not_found_msg = 'Please install sDNA_GH according to README.md,'
                                                            +' ensuring that main.py and all sDNA_GH python' 
                                                            +' files and subfolders are inside '
                                                            +os.sep.join(
                                                                 Grasshopper.Folders.DefaultUserObjectFolder
                                                                ,sDNA_GH_subfolder
                                                                ,sDNA_GH_package
                                                                        )
                                   )         


    logger = sDNA_GH.main.logger.getChild('launcher')
    output.set_logger(logger, flush = True)


    class MyComponent(component):
        pass  # Required.  Idiomatic to Grasshopper.  Must be called "MyComponent"  
            # too, otherwise Grasshopper may not find the class building on 
            # component.  Despite component being passed to the class decorator
            # and overwriting this very class immediately below.  
            # Initial parser step / scope check trips this?

    MyComponent = sDNA_GH.main.sDNA_GH_Component


    if nick_name.replace(' ','').replace('_','').lower() == 'selftest':  

        if sys.argv[0].endswith(os.path.join(sDNA_GH_package,'__main__.py')):   
            from .tests.unit_tests import unit_tests_sDNA_GH
        else:
            unit_tests_sDNA_GH, _ = load_modules('sDNA_GH.tests.unit_tests.unit_tests_sDNA_GH'
                                                ,sDNA_GH_search_paths
                                                )

        MyComponent._RunScript = MyComponent.RunScript
        MyComponent.RunScript = unit_tests_sDNA_GH.run_launcher_tests  



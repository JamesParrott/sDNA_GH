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



""" Main entry point to launch sDNA_GH if run as a script from an sDNA_GH GhPython component.

    Imports the python package sDNA_GH and (re)defining the MyComponent(component) 
    class.  Grasshopper instantiates this class in each such component, then 
    calls its RunScript method 
    (and recalls it on each Param update / recalculation).

    There may be multiple components, all running this same launcher code.
    Therefore we want the root logger to live in the sDNA_GH.main module
    that they each import.  The logging system is configurable by the user,
    but only through the options that are read in during the main package
    import, and we want to create logs before this too, in this module.  So 
    before a component has imported sDNA_GH.main, logging is routed through output, 
    a callable instance of Output, with a cache, defined below.  After a logger has 
    been set up according to the user's configuration, after the main package import,
    output's cache is flushed through the normal logging system, 

    Also, the Output class is used to define two Classes from this single 
    code definition.  Python scripts can happily import themselves, but here
    this is because launcher.py is itself part of the imported sDNA_GH python
    package, imported by launcher.py in a GhPython component.  To achieve this, the 
    code in this file needs to be copied into the sDNA_GH GhPython components 
    during building of the components (e.g. via the code input Param), 

    The behaviours can be different of course if changes are made to one and not
    the other. e.g. if updated code is forgotten to be copied into the component.

    A dummy MyComponent(component) class is defined in the script to appease
    GhPython's parser, even though the definition we use is imported from the package

    launcher.py can also run unit tests in a component named "selftest" 
"""

__author__ = 'James Parrott'
__version__ = '2.10.0'



import sys
import os
import functools
import importlib

from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper
import scriptcontext as sc

import_module = importlib.import_module
try:
    reload #type: ignore
except NameError:
    reload = importlib.reload

try:
    basestring #type: ignore
except NameError:
    basestring = str

try:
    ghdoc #type: ignore
except NameError:
    from .custom.skel.basic.ghdoc import ghdoc

ZIP_FILE_NAME = 'sdna-gh'
PACKAGE_NAME = 'sDNA_GH'
PLUG_IN_NAME = 'sDNA'               
RELOAD_IF_ALREADY_IMPORTED = False
REPOSITORY = os.path.dirname(os.path.dirname(ghdoc.Path)) if ghdoc.Path else None
# Assume we are in repo_folder/dev/sDNA_build_components.gh

USER_INSTALLATION_FOLDER = os.path.join(
                                    Grasshopper.Folders.DefaultUserObjectFolder
                                   ,ZIP_FILE_NAME
                                   )
SELFTEST = 'selftest'




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
        self.set_logger(logger, flush = False)



    def store(self, message, logging_level):
        self.tmp_logs.append( (message, logging_level) )

    def __call__(self, message, logging_level = "INFO", logging_dict = {}):
        #type: (str, str, dict, list) -> str
        
        #logger.debug(s)

        if logging_dict == {} and self.logger is not None: 
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

        return '%s : %s ' % (logging_level, message)

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
        if kwargs and (not message or not isinstance(message, basestring)):
            message = self.message_fmt % kwargs
        logger.error(message)
        self.kwargs = kwargs
        super(InvalidArgsError, self).__init__(message)    


class ModuleNameError(InvalidArgsError):
    message_fmt = 'Invalid module name: %s'


class FilePathError(InvalidArgsError):
    message_fmt = 'Invalid path to import module from: %s'


# We only know the sDNA version to import as a string.  This is more secure too.
def strict_import(module_name = ''
                 ,folder = ''
                 ,sub_folder = ''
                 ,logger = output
                 ,reload_already_imported = RELOAD_IF_ALREADY_IMPORTED
                 ):

    # type: (str, str, str, type[any], bool) -> type[any]
    """ Imports the named module from the specified folder\subfolder only, 
        and returns it.
        
        Avoids name clashes and casual hijack attempts.  In some 
        environments supporting a Python implementation (such as 
        GhPython in Grasshopper) it may not be desirable to ask the user 
        to set PYTHONPATH.  Hence here, we insert the specified folder
        into sys.path (if they are not already in there).
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

    if (search_path 
        and isinstance(search_path, basestring) 
        and os.path.isdir(search_path)):
        #
        logger.debug('Search path == %s' % search_path)
        #if search_folder_only:
        #    sys.path = [search_path]
        if search_path not in sys.path:
            sys.path.insert(0, search_path)
    else:
        raise FilePathError(module_name = module_name
                           ,search_path = search_path
                           ,logger = logger
                           )

    logger.debug('Trying import... ')
    module = import_module(module_name, '')           

    return module       


class ModulesNotFoundError(InvalidArgsError):
    message_fmt = 'Modules not found in any location %s'


def load_modules(m_names
                ,folders
                ,logger = output
                ,module_name_error_msg = 'Please supply valid names of modules to import, %s'
                ,folders_error_msg = 'Please supply valid folders to import from. %s'
                ,modules_not_found_msg = 'Specified modules not found in any folder, %s'):
    #type(str/ Iterable, list, type[any], str, str) -> tuple / None
    """ Tries to import all modules in m_names, from the first folder in 
        folders to contain a .py or .pyc files with the same name as each 
        module.

        Returns a tuple of all the modules and the path they were found in.  Else 
        raises a ModulesNotFoundError.
    """
    if not m_names:
        raise ModuleNameError(message_fmt = 'No module names supplied, m_names = %s'
                             ,m_names = m_names
                             ,logger = logger
                             )

    if any( not isinstance(m_name, basestring) for m_name in m_names ):
        # if m_names is a basestring, the error is not raised 
        raise ModuleNameError(message_fmt = module_name_error_msg
                             ,m_names = m_names
                             ,logger = logger
                             )
    
    if isinstance(m_names, basestring):
        m_names = [m_names] 

    logger.debug('m_names == %s of type : %s' % (m_names, type(m_names).__name__))

    logger.debug('Testing paths : %s ' % folders)
    
    if isinstance(folders, basestring):
        folders = [folders]

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
              ):
            #
            logger.debug('Importing %s' % repr(m_names))

            return tuple(strict_import(name, folder, '', logger = logger) 
                         for name in m_names
                        ) + (folder,)
            # tuple of modules, followed by the path to them
    raise ModulesNotFoundError(message_fmt = modules_not_found_msg
                              ,m_names = m_names
                              ,folders = folders
                              ,logger = logger
                              )




if __name__ == '__main__': # False in a compiled component.  But then the user
                           # can't add or remove Params to the component.  
    
    # Grasshopper will look for class MyComponent(component) in global scope
    # so a main function is a little tricky to define.

    nick_name = ghenv.Component.NickName #type: ignore


    if (REPOSITORY and 
        nick_name == 'Build_components'):
        #
        sDNA_GH_search_path = REPOSITORY 
        # builder can only load sDNA_GH from its parent directory, 
        # e.g. if in a dir one level up in the main repo
        # such as sDNA_build_components.gh.
    else:
        sDNA_GH_search_path = USER_INSTALLATION_FOLDER


    sc.doc = ghdoc #type: ignore

    output.debug(sDNA_GH_search_path)

    class sDNA_GH(object):
        pass

    if 'sDNA_GH.main' in sys.modules:
        sDNA_GH.main = sys.modules['sDNA_GH.main']
    else:
        sDNA_GH.main, _ = load_modules(m_names = PACKAGE_NAME + '.main'
                                      ,folders = sDNA_GH_search_path
                                      ,folders_error_msg = 'Please unzip %s.zip '
                                                           %ZIP_FILE_NAME
                                                           +' in the folder %s '
                                                           %Grasshopper.Folders.DefaultUserObjectFolder
                                                           +'and ensure a subfolder called %s is created '
                                                           %os.path.join(ZIP_FILE_NAME, PACKAGE_NAME)
                                                           +'inside it, containing main.py ' 
                                                           +'and all the sDNA_GH python files '
                                                           +'including those within other subfolders. ' 
                                      ,modules_not_found_msg = 'Some sDNA_GH files may be missing.  '
                                                              +'Please: 1) Copy %s.zip into: %s '
                                                              %(ZIP_FILE_NAME
                                                               ,Grasshopper.Folders.DefaultUserObjectFolder
                                                               )
                                                              +'2) Unblock it if necessary. '
                                                              +'3) Right click '
                                                              +'it, select Extract All... and click Extract, '
                                                              +'to extract it to that location. '
                                                              +'4) Ensure that main.py and all sDNA_GH python' 
                                                              +' files and subfolders are inside: %s '
                                                              %os.path.join(USER_INSTALLATION_FOLDER
                                                                           ,PACKAGE_NAME
                                                                           )
                                                              +'5) Reinitialise the component or restart Rhino.'
                                      )         


    logger = sDNA_GH.main.logger.getChild('launcher')
    output.set_logger(logger, flush = True)


    class MyComponent(component):
        pass  # Required.  Idiomatic to Grasshopper.  Must be called "MyComponent"  
            # too (it is looked for by the parser or scope checker?) otherwise 
            # Grasshopper may not find the subclass of on 
            # component.  Even though we overwrite this class on the next line
            # immediately below.  

    MyComponent = sDNA_GH.main.sDNA_GH_Component
    # Grasshopper calls MyComponent.RunScript automatically.


    if nick_name.replace(' ','').replace('_','').lower() == SELFTEST:  


        unit_tests, _ = load_modules('%s.tests.unit_tests.%s_unit_tests' % ((PACKAGE_NAME,)*2)
                                    ,sDNA_GH_search_path
                                    )

        
        MyComponent = unit_tests.make_test_running_component_class(
                                         MyComponent
                                        ,package_location = sDNA_GH_search_path
                                        )
        # Grasshopper calls MyComponent.RunScript automatically.


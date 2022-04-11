#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.01'


import os, sys, inspect
from os.path import isfile, isdir, join, split, dirname
from importlib import import_module
     

sDNA_GH_subfolder = 'sDNA_GH' 
sDNA_GH_package = 'sDNA_GH'               
reload_config_and_other_modules_if_already_loaded = False



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
# the other, e.g. if the code is forgotten to be copied into the component.

class Output: #def output

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

    def flush(self):
        tmp_logs = self.tmp_logs[:] # __call__ might cache back to tmp_logs
        self.tmp_logs[:] = [] # Mutate list initialised with
        for tmp_log_message, tmp_log_level in tmp_logs:
            self.__call__(tmp_log_message, tmp_log_level)

output = Output()


class Debugger:
    def __init__(self, output = None):
        #type(type[any], function) -> None  # callable object
        if output is None:
            output = Output()
        self.output = output # want to call an instance that we also use for
                             # higher logging level messages so 
                             # composition instead of inheritance is used
    def __call__(self, x):
        c = inspect.currentframe().f_back.f_locals.items()

        names = [name.strip("'") for name, val in c if val is x]
        # https://stackoverflow.com/questions/18425225/getting-the-name-of-a-variable-as-a-string
        # https://stackoverflow.com/a/40536047

        if names:
            return self.output(str(names) + ' == ' + str(x)+' ','DEBUG')
        else:
            return self.output(str(x)+' ','DEBUG')



def strict_import(  module_name = ''
                   ,folder = ''
                   ,sub_folder = ''
                   ,output = output
                   ,search_folder_only = False
                   ):

    # type: (str, str, str, function, bool) -> type[any]
    #
    if module_name == '':
        output('No module to import','INFO')
        return None
    output(module_name,'DEBUG')
    if module_name in sys.modules:   # sys.modules is also shared between GHPython components 
                                     # (and is even saved until Rhino is closed).
        output('Module ' + module_name + ' already in sys.modules.  ','DEBUG')
        if reload_config_and_other_modules_if_already_loaded:
            output('Reloading ' +  module_name  + '.... ','DEBUG')
            reload(sys.modules[module_name]) # type: ignore
        return sys.modules[module_name]
    #
    #
    # Load module_name for first time:
    #
    #
    search_path = join(folder, sub_folder)

    tmp = sys.path
    if search_path and isinstance(search_path, str) and isdir(search_path):
        output('Search path == ' + search_path, 'DEBUG')
        if search_folder_only:
            sys.path = [search_path]
        else:
            sys.path.insert(0, search_path)
    else:
        output('Invalid search path : ' + search_path, 'DEBUG')
        if search_folder_only:
            return None

    output('Trying import... ','DEBUG')
    module = import_module(module_name, '')           
    sys.path = tmp
    return module       



def load_modules(m_names, path_lists):
    m_names = m_names if isinstance(m_names, tuple) else [m_names] 
    output('m_names == ' + str(m_names) + ' of type : ' + type(m_names).__name__,'DEBUG')
    if any((name.startswith('.') or name.startswith('..')) in name for name in m_names):
        output(m_names,'DEBUG')
        raise ImportError( output('Relative import attempted, but not supported','CRITICAL') )

    output('Testing paths : ' + '\n'.join(map(str,path_lists)),'DEBUG')
    output('Type(path_lists) : ' + type(path_lists).__name__,'DEBUG')


    for path_list in path_lists:
        test_paths = path_list if isinstance(path_list, list) else [path_list]
        test_paths = test_paths[:]
        output('Type(path_list) : ' + type(path_list).__name__,'DEBUG')
        output('Type(test_paths) : ' + type(test_paths).__name__,'DEBUG')

        for path in test_paths:
            output('Type(path) : ' + type(path).__name__ + ' path == ' + path,'DEBUG')
            if isfile(path):
                path = dirname(path)
            if all( any(isfile(join(path, name.replace('.', os.sep) + ending)) 
                        for ending in ['.py','.pyc'] 
                        )
                    for name in m_names
                ):
                output('Importing ' + str(m_names) +' ','DEBUG')
                return tuple(strict_import(name, path, '') for name in m_names) + (path,)
                # tuple of modules, followed by the path to them
    return None


if __name__ == '__main__': # False in a compiled component.  But then the user
                           # can't add or remove Params to the component.  
    
    from ghpythonlib.componentbase import executingcomponent as component
    import Grasshopper
    import scriptcontext as sc
    sDNA_GH_search_paths = [ join(Grasshopper.Folders.DefaultUserObjectFolder, sDNA_GH_subfolder) ]
                                            #join(Grasshopper.Folders.DefaultAssemblyFolder, sDNA_GH_subfolder) ]  
                                            # Grasshopper.Folders.AppDataFolder + r'\Libraries'
                                            # %appdata%  + r'\Grasshopper\Libraries'
                                            # os.getenv('APPDATA') + r'\Grasshopper\Libraries'
                                            # Grasshopper.Folders.AppDataFolder + r'\UserObjects'
                                            # %appdata%  + r'\Grasshopper\UserObjects'
                                            # os.getenv('APPDATA') + r'\Grasshopper\UserObjects'

    sDNA_GH_search_paths += [join(Grasshopper.Folders.DefaultAssemblyFolder
                                ,sDNA_GH_subfolder
                                ) 
                            ]  # Might need to install sDNA_GH 
                               # in \Grasshopper\Libraries in Rhino 6?

    nick_name = ghenv.Component.NickName #type: ignore


    sc.doc = ghdoc #type: ignore

    sDNA_GH, _ = load_modules(sDNA_GH_package + '.setup'
                             ,sDNA_GH_search_paths
                             )         


    logger = sDNA_GH.logger.getChild('launcher')
    output.set_logger(logger, flush = True)


    class MyComponent(component):
        pass  # Required.  Idiomatic to Grasshopper.  Must be called "MyComponent"  
            # too, otherwise Grasshopper may not find the class building on 
            # component.  Despite component being passed to the class decorator
            # and overwriting this very class immediately below.  
            # Initial parser step / scope check trips this?

    MyComponent = sDNA_GH.component_decorator( component
                                             ,ghenv #type: ignore
                                             ,nick_name
                                             )


    if nick_name.replace(' ','').replace('_','').lower() == 'selftest':  

        if sys.argv[0].endswith(join(sDNA_GH_package,'__main__.py')):   
            from .tests.unit_tests import unit_tests_sDNA_GH
        else:
            unit_tests_sDNA_GH, _ = load_modules('sDNA_GH.tests.unit_tests.unit_tests_sDNA_GH'
                                                ,sDNA_GH_search_paths
                                                )

        MyComponent._RunScript = MyComponent.RunScript
        MyComponent.RunScript = unit_tests_sDNA_GH.run_launcher_tests  



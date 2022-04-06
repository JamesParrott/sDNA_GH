#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.01'


import os, sys 
from os.path import isfile, isdir, join, split, dirname
from importlib import import_module

try:        
    from ghpythonlib.componentbase import executingcomponent as component
    import Grasshopper
    import scriptcontext as sc
except ImportError:
    print( "No Grasshopper env found.  Building test environment.  ")
    
    component = object

    class Grasshopper:
        class Folders:
            #DefaultAssemblyFolder = r'C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.01'
            DefaultAssemblyFolder = os.getenv('APPDATA') + r'\Grasshopper\Libraries'

sDNA_GH_subfolder = 'sDNA_GH' 
sDNA_GH_package = 'sDNA_GH'               
reload_config_and_other_modules_if_already_loaded = False
#sDNA_GH_search_paths = [r'C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.01\sDNA_GH']
sDNA_GH_search_paths = [ join(Grasshopper.Folders.DefaultAssemblyFolder, sDNA_GH_subfolder) ]  
                                            # Grasshopper.Folders.AppDataFolder + r'\Libraries'
                                            # %appdata%  + r'\Grasshopper\Libraries'
                                            # os.getenv('APPDATA') + r'\Grasshopper\Libraries'



def output(s, level='INFO', inst = None):        # e.g. inst is a MyComponent.  
                         # Inst is a proxy argument for both 'self' and 'cls'.
    #type: (str, MyComponent, str) -> None
    message = s
    if hasattr(inst,'nick_name'):
        message = inst.nick_name + ' : ' + message
    message_with_level =  'sDNA_GH_launcher' + '  ' + level + ' : ' + message
    #print(message_with_level)
    try:
        sDNA_GH_tools.output(message, level, inst)
    except:
        try:
            getattr(sDNA_GH_tools.wrapper_logging.logging,level.lower())("From sDNA_GH_launcher via logging: " + message)
        except:
            print(message_with_level)
    return message_with_level


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
                                    # and is even saved until Rhino is closed.
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
    m = import_module(module_name, '')           
    sys.path = tmp
    return m       


def load_modules(self, m_names, path_lists):
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
        #output('Type(path_list) : ' + type(path_list).__name__,'DEBUG')
        #output('Type(test_paths) : ' + type(test_paths).__name__,'DEBUG')

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
    return None


#try:
from Grasshopper.Folders import DefaultAssemblyFolder
sDNA_GH_search_paths += [join(DefaultAssemblyFolder
                                ,sDNA_GH_subfolder
                                ) 
                        ]            
# except:
#     raise ImportError(output( 'Unable to import the main sDNA_GH Python Package.  '
#                              +'Check the folder sDNA_GH containing the package '
#                              +'is a sub folder of the '
#                              +'sDNA_GH folder containing the plug-in components'
#                              +'and the installation procedure was done correctly'
#                              +'as per README.md'
#                              ,'ERROR'
#                              )
#                       )


try:
    nick_name = ghenv.Component.NickName #type: ignore
except:
    nick_name = 'selftest'

sc.doc = ghdoc #type: ignore

sDNA_GH_tools, _ = load_modules( None
                                ,sDNA_GH_package + '.tools'
                                ,sDNA_GH_search_paths
                                )         

class MyComponent(component):
    pass  # Required.  Idiomatic to Grasshopper.  Must be called "MyComponent"  
          # too, otherwise Grasshopper may not find the class building on 
          # component.  Despite component being passed to the class decorator
          # and overwriting this very class immediately below.  
          # Initial parser step / scope check trips this?

MyComponent = sDNA_GH_tools.component_decorator( component
                                                ,ghenv #type: ignore
                                                ,nick_name
                                                ,load_modules
                                                )


if nick_name.replace(' ','').replace('_','').lower() == 'selftest':  

    if sys.argv[0].endswith(join(sDNA_GH_package,'__main__.py')):   
        from .tests.unit_tests import unit_tests_sDNA_GH
    else:
        unit_tests_sDNA_GH, _ = load_modules( None
                                             ,'sDNA_GH.tests.unit_tests.unit_tests_sDNA_GH'
                                             ,sDNA_GH_search_paths
                                             )

    MyComponent._RunScript = MyComponent.RunScript
    MyComponent.RunScript = unit_tests_sDNA_GH.run_launcher_tests  

#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.01'



sDNA_GH_subfolder = 'sDNA_GH' 
sDNA_GH_package = 'sDNA_GH'               
reload_config_and_other_modules_if_already_loaded = False
sDNA_GH_search_paths = [r'C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.01\sDNA_GH']



#                     #Abbreviation = Tool Name
# #######################################################################################################################
# name_map = dict(    sDNA_Demo = [ 'Read_From_Rhino'
#                                  ,'Read_Usertext'
#                                  ,'Write_Shp'
#                                  ,'sDNAIntegral'
#                                  ,'Read_Shp'
#                                  ,'Write_Usertext'
#                                  ,'Parse_Data'
#                                  ,'Recolour_objects'
#                                  ]
#                     ,test_write_Usertext_req = [ 'Read_From_Rhino'
#                                  ,'Read_Usertext'
#                                  ,'Write_Shp'
#                                  ,'sDNAIntegral'
#                                  ,'Read_Shp'
#                                  ,'Write_Usertext'
#                                  ,'Parse_Data'
#                                  ,'Recolour_objects'
#                                  ]
#                     ,sDNA_Demo_old_plot = [
#                                   'Read_From_Rhino'
#                                  ,'Read_Usertext'
#                                  ,'Write_Shp'
#                                  ,'sDNAIntegral'
#                                  ,'Read_Shp'
#                                  ,'Write_Usertext'
#                                  ,'Visualise_Data' #TODO: Delete.  Deprecated.
#                                  ]
#                     ,Read_From_Rhino = 'get_objects_from_Rhino'
#                     ,Read_Usertext = 'read_Usertext'
#                     ,Write_Shp = 'write_objects_and_data_to_shapefile'
#                     ,Read_Shp = 'read_shapes_and_data_from_shapefile'
#                     ,Write_Usertext = 'write_data_to_Usertext'
#                     ,Bake_UserText = 'bake_and_write_data_as_Usertext_to_Rhino'
#                     ,Visualise_Data = 'plot_data_on_Rhino_objects'  #TODO: Delete.  Deprecated.
#                     ,Parse_Data = 'parse_data'
#                     ,Recolour_objects='recolour_objects'
#                     ,Recolor_objects ='recolour_objects'
#                     #,'main_sequence'
#                     #,'sDNAIntegral'
#                     #,'sDNASkim'
#                     ,sDNAIntFromOD = 'sDNAIntegralFromOD'
#                     #,'sDNAGeodesics'
#                     #,'sDNAHulls'
#                     #,'sDNANetRadii'
#                     ,sDNAAccessMap = 'sDNAAccessibilityMap'
#                     #,'sDNAPrepare'
#                     #,'sDNALineMeasures'
#                     #,'sDNALearn'
#                     #,'sDNAPredict'
#                 )
# #######################################################################################################################



import os, sys 
from os.path import isfile, isdir, join, split, dirname
from importlib import import_module



#import System, GhPython
#import rhinoscriptsyntax as rs
#import scriptcontext as sc
#import ghpythonlib.treehelpers as th
import Rhino


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
            if hasattr(inst,'a') and hasattr(inst.a,'write'):
                inst.a.write("From sDNA_GH_launcher via inst: " + message_with_level)
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


try:
    from Grasshopper.Folders import DefaultAssemblyFolder
    sDNA_GH_search_paths += [join(DefaultAssemblyFolder
                                 ,sDNA_GH_subfolder
                                 ) 
                            ]
except:
    raise ImportError(output( 'Unable to import the main sDNA_GH Python Package.  '
                             +'Check the folder sDNA_GH containing the package '
                             +'is a sub folder of the '
                             +'sDNA_GH folder containing the plug-in components'
                             +'and the installation procedure was done correctly'
                             +'as pe as per README.md'
                             ,'ERROR'
                             )
                      )




#global sDNA_GH, sDNA_GH_search_paths, component_tool

                        





  

#def is_file_any_type(s):
#    return isinstance(s, str) and isfile(s)

    #@staticmethod
    #load_modules = load_modules




    # log_file = opts['options'].log_file  
    # log_file_dir = opts['options'].logs_subdirectory
    # if isdir(log_file_dir):
    #     logger = sDNA_GH.tools.wrapper_logging.new_Logger( 
    #                                     'sDNA_GH'
    #                                     ,log_file 
    #                                     ,opts['options'].logger_file_level
    #                                     ,opts['options'].logger_console_level
    #                                     )
    # else:
    #     pass
    #     output('Invalid log file dir ' + log_file_dir + ' ', 'ERROR')




try:
    nick_name = ghenv.Component.NickName #type: ignore
except:
    nick_name = 'selftest'

if nick_name.replace(' ','').replace('_','').lower() != 'selftest':  

    sDNA_GH_tools, _ = load_modules( None
                                    ,sDNA_GH_package + '.tools'
                                    ,sDNA_GH_search_paths
                                    )                  
    MyComponent = sDNA_GH_tools.sDNA_GH_Component(load_modules)
    # MyComponent = sDNA_GH_tools.sDNA_GH_component_deco(MyComponent) 
else: # Run self tests:
    if sys.argv[0].endswith(join(sDNA_GH_package,'__main__.py')):   
        from .tests.unit_tests import unit_tests_sDNA_GH
    else:
        unit_tests_sDNA_GH, _ = load_modules( None
                                             ,'sDNA_GH.tests.unit_tests.unit_tests_sDNA_GH'
                                             ,sDNA_GH_search_paths
                                             )
    #FileAndStream = unit_tests_sDNA_GH.FileAndStream
      
 

    MyComponent = unit_tests_sDNA_GH.sDNA_GH_Test_Runner_Component #run_launcher_tests 
    
    #import unittest
    #TestComponent = sDNA_GH.tools.sDNA_GH_component_deco(unittest.TestCase)

    #TestStringMethods = unit_tests_sDNA_GH.TestStringMethods

        
    #from time import asctime
    
   # tests_log_file_suffix = '_test_results'
    #try:
    #    file_path_no_ext = ghdoc.Path.rpartition('.')[0] #type: ignore
    #except:
    #    file_path_no_ext = join( sys.path[0]
    #                            ,__file__.rpartition('.')[0]
    #                            )
    #
    #test_log_file_path = (    file_path_no_ext
    #                        + tests_log_file_suffix
    #                        + '.log' 
    #                     )

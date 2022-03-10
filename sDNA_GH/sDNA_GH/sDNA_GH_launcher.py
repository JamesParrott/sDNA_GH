#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.01'



sDNA_GH_subfolder = 'sDNA_GH' 
sDNA_GH_package = 'sDNA_GH'               
reload_config_and_other_modules_if_already_loaded = False
sDNA_GH_search_paths = [r'C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.01\sDNA_GH']

#######################################################################################################################
# Please note!
# 
#
component_tool = None    # Note to user, if you rename this component in Grasshopper, 
                                        # EITHER: add an entry in name_map dictionary below from the name you've
                                        # given it to the name of the tool you want
                                        # this component to actually run.
                                        # 
                                        # OR: hardcode component_tool here to the name in support_component_names,
                                        # special_names, names_map, or in sDNA_tool_names, of the tool you want 
                                        # and make sure metas.allow_components_to_change_type_on_rename == False
                                        # Abbreviations are supported via the name_map dictionary below
                    #Abbreviation = Tool Name
name_map = dict(    sDNA_Demo = [ 'Read_From_Rhino'
                                 ,'Read_Usertext'
                                 ,'Write_Shp'
                                 ,'sDNAIntegral'
                                 ,'Read_Shp'
                                 ,'Write_Usertext'
                                 ,'Parse_Data'
                                 ,'Recolour_objects'
                                 ]
                    ,sDNA_Demo_old_plot = [
                                  'Read_From_Rhino'
                                 ,'Read_Usertext'
                                 ,'Write_Shp'
                                 ,'sDNAIntegral'
                                 ,'Read_Shp'
                                 ,'Write_Usertext'
                                 ,'Visualise_Data'
                                 ]
                    ,Read_From_Rhino = 'get_objects_from_Rhino'
                    ,Read_Usertext = 'read_Usertext'
                    ,Write_Shp = 'write_objects_and_data_to_shapefile'
                    ,Read_Shp = 'read_shapes_and_data_from_shapefile'
                    ,Write_Usertext = 'write_data_to_Usertext'
                    ,Bake_UserText = 'bake_and_write_data_as_Usertext_to_Rhino'
                    ,Visualise_Data = 'plot_data_on_Rhino_objects'
                    ,Parse_Data = 'parse_data'
                    ,Recolour_objects='recolour_objects'
                    ,Recolor_objects ='recolour_objects'
                    #,'main_sequence'
                    #,'sDNAIntegral'
                    #,'sDNASkim'
                    ,sDNAIntFromOD = 'sDNAIntegralFromOD'
                    #,'sDNAGeodesics'
                    #,'sDNAHulls'
                    #,'sDNANetRadii'
                    ,sDNAAccessMap = 'sDNAAccessibilityMap'
                    #,'sDNAPrepare'
                    #,'sDNALineMeasures'
                    #,'sDNALearn'
                    #,'sDNAPredict'
                )
#######################################################################################################################



import os, sys 
from os.path import isfile, isdir, join, split, dirname
from importlib import import_module
if component_tool == None:
    try:
        component_tool = ghenv.Component.NickName #type: ignore
    except:
        component_tool = "selftest"
        import unittest
try:        
    from ghpythonlib.componentbase import executingcomponent as component
except ImportError:
    component = object

#import System, GhPython
#import rhinoscriptsyntax as rs
#import scriptcontext as sc
#import ghpythonlib.treehelpers as th


def output(s, level='INFO', inst = None):        # e.g. inst is a MyComponent.  
                         # Inst is a proxy argument for both 'self' and 'cls'.
    #type: (str, MyComponent, str) -> None
    message = s
    if hasattr(inst,'nick_name'):
        message = inst.nick_name + ' : ' + message
    message_with_level = level + ' : ' + message
    #print(message_with_level)
    try:
        sDNA_GH.tools.output("From sDNA_GH_launcher: " + message, level, inst)
    except:
        try:
            getattr(sDNA_GH.tools.wrapper_logging.logging,level.lower())("From sDNA_GH_launcher via logging: " + message)
        except:
            print(message_with_level)
            if hasattr(inst,'a') and hasattr(inst.a,'write'):
                inst.a.write("From sDNA_GH_launcher via inst: " + message_with_level)
    return message_with_level

def strict_import(  module_name = ''
                   ,folder = ''
                   ,sub_folder = ''
                   ,output = output
                  ):

    # type: (str,str,str,function) -> type[any]
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
    search_path = join(folder,sub_folder)
    output("Search path == " + search_path,'DEBUG')
    tmp = sys.path
    sys.path.insert(0, search_path)
    m = import_module(module_name, '')           
    sys.path = tmp
    return m       

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
    pass

class sDNA_GH():
    pass

sDNA_GH.tools, sDNA_GH_path = load_modules( 'sDNA_GH.tools'
                                            ,sDNA_GH_search_paths
                                            )


#global sDNA_GH, sDNA_GH_search_paths, component_tool

                        





  

def is_file_any_type(s):
    return isinstance(s, str) and isfile(s)


class MyComponent(component):
    opts = sDNA_GH.tools.opts                       
                        # mutable.  Reference breakable and remakeable 
                        # to de sync / sync local opts to global opts
    tools_dict = sDNA_GH.tools.tools_dict
    local_metas = sDNA_GH.tools.local_metas   # immutable.  controls syncing /
                                        # desyncing / read / write of the
                                        # above, opts.
                                        # Although local, can be set on 
                                        # groups of components using the 
                                        # default section of a project 
                                        # config.ini, or passed as a
                                        # Grasshopper parameter between
                                        # components
    ghdoc = ghdoc #type: ignore

    if sDNA_GH.tools.logger.__class__.__name__ == 'WriteableFlushableList':
        log_file = (  ghdoc.Path.rpartition('.')[0]  #type: ignore
                    + opts['options'].log_file_suffix + '_tracker1'
                    + '.log' ) 
        log_file_dir = split(log_file)[0]    #os.path.split
        if isdir(log_file_dir):
            logger = sDNA_GH.tools.wrapper_logging.new_Logger( 
                                            'sDNA_GH'
                                            ,log_file 
                                            ,opts['options'].logger_file_level
                                            ,opts['options'].logger_console_level
                                            )
        else:
            pass
            output('Invalid log file dir ' + log_file_dir + ' ', 'ERROR')
            logger = sDNA_GH.tools.logger 



    my_tools = None
    #@staticmethod
    load_modules = load_modules


run_normally = component_tool.replace(' ','').replace('_','').lower() != 'selftest'
if run_normally:  # if running from command line, no ghenv so previous code 
                  # should've set component_tool=='selftest'
    MyComponent = sDNA_GH.tools.sDNA_GH_component_deco(MyComponent) 
else: # Run self tests:
    sDNA_GH.unit_tests, _ = load_modules('sDNA_GH.tests.unit_tests.unit_tests_sDNA_GH'
                                        ,sDNA_GH_search_paths
                                        )
    FileAndStream = sDNA_GH.unit_tests.FileAndStream
      
 

    MyComponent.RunScript = sDNA_GH.unit_tests.run_launcher_tests 
    
    import unittest
    TestComponent = sDNA_GH.tools.sDNA_GH_component_deco(unittest.TestCase)

    TestStringMethods = sDNA_GH.unit_tests.TestStringMethods

        
    from time import asctime
    
    tests_log_file_suffix = '_test_results'
    try:
        file_path_no_ext = ghdoc.Path.rpartition('.')[0] #type: ignore
    except:
        file_path_no_ext = join( sys.path[0]
                                ,__file__.rpartition('.')[0]
                                )

    test_log_file_path = (    file_path_no_ext
                            + tests_log_file_suffix
                            + '.log' 
                         )

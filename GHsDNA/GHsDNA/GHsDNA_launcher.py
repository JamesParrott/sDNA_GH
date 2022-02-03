#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.00'
__copyright__ = 'Cardiff University'
__license__ = {  'Python standard library modules and ' : 'Python Software Foundation 2.7.18' # https://docs.python.org/2.7/license.html
                ,'wrapper_logging' : 'Python Software Foundation 2.7.18'
                ,'wrapper_pyshp' : 'MIT' # https://pypi.org/project/pyshp/ 
                ,'sDNAUISpec.py' : 'MIT' # https://github.com/fiftysevendegreesofrad/sdna_open/blob/master/LICENSE.md
                ,'everything else' : 'same as for sDNA ' # https://sdna.cardiff.ac.uk/sdna/legal-license/ 
               }

GHsDNA_subfolder = 'GHsDNA' 
GHsDNA_package = 'GHsDNA'               
reload_config_and_other_modules_if_already_loaded = False

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
                                        # T
#######################################################################################################################

from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
import ghpythonlib.treehelpers as th

from os.path import isfile, join, split, dirname
# import logging
from importlib import import_module

######################################################################################
#
#From sDNA, runsdnacommand.py:
import os,sys #,time,re
#from subprocess import PIPE, Popen, STDOUT
#try:
#    from Queue import Queue, Empty
#except ImportError:
#    from queue import Queue, Empty
#from threading import Thread
#
#

######################################################################################
#
#From shapefile.py
#from struct import pack, unpack, calcsize, error, Struct
#import os
#import sys
#import time
#import array
#import tempfile
#import warnings
#import io
#from datetime import date


# a = Rhino.RhinoDoc.ActiveDoc.Path

class WriteableFlushableList(list):
    # a simple input for a StreamHandler https://docs.python.org/2.7/library/logging.handlers.html#logging.StreamHandler
    # that stacks logging messages in a list of strings.  Instances are lists wth two extra methods, not streams akin to 
    # generators - memory use is not optimised.
    #
    def write(self,s):
    #type: ( str) -> None
    # https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code
    #
        self.append(s)
    def flush(self):  
    #type: () -> None
        pass  # A flush method is needed by logging

def output(s, level='INFO', inst = None):     # e.g. inst is an instance of this whole Class
    #type: (str, MyComponent, str) -> None
    message = s
    if hasattr(inst,'nick_name'):
        message = inst.nick_name + ' : ' + message
    message_with_level = level + ' : ' + message
    #print(message_with_level)
    try:
        GHsDNA.tools.output(message, level, inst)
    except:
        try:
            getattr(GHsDNA.tools.wrapper_logging.logging,level.lower())(message)
        except:
            #print(message_with_level)
            if hasattr(inst,'a') and hasattr(inst.a,'write'):
                inst.a.write(message_with_level)
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
        output('Module ' + module_name + ' already in sys.modules.  ','INFO')
        if reload_config_and_other_modules_if_already_loaded:
            output('Reloading ' +  module_name  + '.... ','INFO')
            reload(sys.modules[module_name]) 
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

#print '\n'.join(sys.path)
def load_GHsDNA():
    #GH_Components_Folder = r'C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.00'
    GH_Components_Folder = Grasshopper.Folders.DefaultAssemblyFolder
    #GHsDNA = strict_import(GHsDNA_package, GH_Components_Folder, GHsDNA_subfolder, '') 
    class GHsDNA():
        pass
    GHsDNA.tools = strict_import(GHsDNA_package + '.tools', GH_Components_Folder, GHsDNA_subfolder)
    output(' GHsDNA.tools  == ' + str(GHsDNA.tools)[:31],'DEBUG')
    return GHsDNA #, tools

#GHsDNA = load_GHsDNA()
#GHsDNA, tools = load_GHsDNA()

#tools = strict_import('.tools', r'C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.00\GHsDNA', 'GHsDNA', 'GHsDNA')
#GHsDNA = strict_import('GHsDNA', r'C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.00\GHsDNA', 'GHsDNA', '')
#reload(GHsDNA)
#tmp=sys.path
#sys.path=[r'C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.00\GHsDNA']
#from GHsDNA import GHsDNA
#sys.path=tmp

#GHsDNA = strict_import('.GHsDNA', r'C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.00\GHsDNA', '', 'GHsDNA')

class GHsDNA():
    pass

def load_modules(m_names, path_lists):
    m_names = m_names if isinstance(m_names, tuple) else [m_names]  # Need this one to be immmutable, so it's hashable to use as a dict key
    output('m_names == ' + str(m_names) + ' of type : ' + type(m_names).__name__,'DEBUG')
    if any(name.startswith('.') or '..' in name for name in m_names):
        raise ImportError( output('Relative import attempted, but not supported','CRITICAL') )

    output('Testing paths : ' + '\n'.join(map(str,path_lists)),'INFO')
    output('Type(path_lists) : ' + type(path_lists).__name__,'DEBUG')


    for path_list in path_lists:
        test_paths = path_list if isinstance(path_list, list) else [path_list]
        test_paths = test_paths[:]
        #output('Type(path_list) : ' + type(path_list).__name__,'DEBUG')
        #output('Type(test_paths) : ' + type(test_paths).__name__,'DEBUG')

        for path in test_paths:
            output('Type(path) : ' + type(path).__name__,'DEBUG')
            if isfile(path):
                path = dirname(path)
            if all(any(isfile(join(path, name.replace('.', os.sep) + ending)) 
                        for ending in ['.py','.pyc'] )
                            for name in m_names):
                # We haven't checked every folder in a package has an __init__.py
                output('Importing ' + str(m_names) + ' from ' + path,'INFO')
                return tuple(strict_import(name, path, '') for name in m_names) + (path,)
    return None


def load_sDNA(sDNA_folder, options):
    
    if sDNA_folder == None:
        try:
            sDNA_folder = split(options.sDNA_UISpec_path)[0]     #os.path.split
        except:
            sDNA_folder = '' #default_sDNAUISpec_path
    runsdnacommand = strict_import('runsdnacommand',sDNA_folder,'')
    sDNAUISpec = strict_import('sDNAUISpec',sDNA_folder,'') 
    return runsdnacommand, sDNAUISpec

# runsdnacommand, sDNAUISpec = load_sDNA()




#sDNA_tools, sDNA_tool_instances, sDNA_tool_names, sDNA_tool_categories = sc.sticky[metas.share_sDNA_tools_key]
#else:

    #sc.sticky[metas.share_sDNA_tools_key] = sDNA_tools, sDNA_tool_instances, sDNA_tool_names, sDNA_tool_categories


                    #Abbreviation = Tool Name
name_map = dict(     Read_Network = 'Read_Network_Links'
                    ,Write_shp = 'Write_Links_Data_To_Shapefile'
                    ,Read_shp = 'Read_Links_Data_From_Shapefile'
                    ,Plot_data = 'Plot_Data_On_Links'
                    #,'sDNAIntegral'
                    #,'sDNASkim'
                    ,sDNAIntFromOD = 'sDNAIntegralFromOD'
                    #,'sDNAGeodesics'
                    #,'sDNAHulls'
                    #,'sDNANetRadii'
                    #,'sDNAAccessibilityMap'
                    #,'sDNAPrepare'
                    #,'sDNALineMeasures'
                    #,'sDNALearn'
                    #,'sDNAPredict'
                )






def convert_nested_list_to_data_tree(nested_list):
        # type (list(list(str)))->DataTree
    return th.list_to_tree(nested_list)
    #layerTree = []

    #for i in range(len(layernames)):
    #    objs = Rhino.RhinoDoc.ActiveDoc.Objects.FindByLayer(layernames[i])
    #    
    #    if objs:
    #        geoms = [obj.Geometry for obj in objs]
    #        layerTree.append(geoms)

    #layerTree = th.list_to_tree(layerTree, source=[0,0])
    #return layerTree

def convert_data_tree_to_nested_list(self, data_tree):
    # type (DataTree)->list(list(str))
    return th.tree_to_list(data_tree)

    #x = th.tree_to_list(data_tree)

    #a = []

    #for i,branch in enumerate(x):
    #    
    #    for j,item in enumerate(branch):
    #        s = str(i) + "[" + str(j) + "] "
    #        s += type(item).__name__ + ": "
    #        s += str(item)
    #        
    #        a.append(s)
    #return a



class MyComponent(component):

    global GHsDNA
    GHsDNA_search_paths = [join(Grasshopper.Folders.DefaultAssemblyFolder, GHsDNA_subfolder)
                          ,r'C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.00\GHsDNA']
    GHsDNA.tools, GHsDNA_path = load_modules('GHsDNA.tools', GHsDNA_search_paths)


    opts = GHsDNA.tools.opts                 # mutable.  Refernce broken and remade to de sync / sync
    local_metas = GHsDNA.tools.local_metas   # immutable.  Can be set on groups of components using the default section of a project config.ini
    tools_dict = GHsDNA.tools.tools_dict

    global component_tool



    def update_tools(self):
        global name_map
        
        self.nick_name = ghenv.Component.NickName if component_tool==None else component_tool
        self.logger = GHsDNA.tools.wrapper_logging.logging.getLogger(self.nick_name)
        output('Self has attr sDNA == ' + str(hasattr(self,'sDNA'))+' ','DEBUG')
        output("self.opts[options].sDNA == "+ str(self.opts['options'].sDNA)+' ','DEBUG')
        if hasattr(self,'sDNA'):
            print('Self has attr sDNA == ' + str(hasattr(self,'sDNA'))+' '+'DEBUG')
        if not hasattr(self,'sDNA') or self.sDNA != self.opts['options'].sDNA:
            self.UISpec, self.run, path = load_modules(self.opts['options'].sDNA, self.opts['options'].sDNA_search_paths)
            print('Self has attr UISpec == ' + str(hasattr(self,'UISpec'))+' ' + 'DEBUG')
            print('Self has attr run == ' + str(hasattr(self,'run'))+' ' +'DEBUG')

            self.sDNA = self.opts['options'].sDNA
            self.sDNA_path = path
            self.opts['options'] = self.opts['options']._replace(sDNA = self.sDNA
                                                                ,sDNA_path = path
                                                                ,UISpec = self.UISpec
                                                                ,run = self.run)  
            #
            # Initialise caches if necessary:
            GHsDNA.tools.opts.setdefault(self.sDNA,{})
            GHsDNA.tools.get_syntax_dict.setdefault(self.sDNA,{})
            GHsDNA.tools.input_spec_dict.setdefault(self.sDNA,{})


        self.opts = GHsDNA.tools.opts if self.local_metas.sync_to_shared_global_opts else self.opts.copy()

        self.my_tools = GHsDNA.tools.tool_factory( self.nick_name, name_map, self.opts)


    def __init__(self):

        self.logger = GHsDNA.tools.wrapper_logging.logging.getLogger("MyComponent Class : ")
        
        self.a = WriteableFlushableList()
        GHsDNA.tools.wrapper_logging.add_custom_file_to_logger(GHsDNA.tools.logger, self.a, 'INFO')

        #runsdnacommand, sDNAUISpec = load_sDNA(options)


        
        self.update_tools()
        component.__init__(self)

  



    #GHsDNA = strict_import('GHsDNA', join(Grasshopper.Folders.DefaultAssemblyFolder,'GHsDNA'), sub_folder = 'GHsDNA')   
                                        # Grasshopper.Folders.AppDataFolder + r'\Libraries'
                                        # %appdata%  + r'\Grasshopper\Libraries'
                                        # os.getenv('APPDATA') + r'\Grasshopper\Libraries'
    def RunScript(self, go, f_name, Geom, Data, *args):
        # type (bool, str, Rhino Geometry, datatree, tuple(namedtuple,namedtuple), *dict)->bool, str, Rhino_Geom, datatree, str
        #if not 'opts' in globals():
        #    global opts
        self.a = WriteableFlushableList() #Reset. Discard output persisting from previous calls to this method (should be logged anyway).
        args_dict = {key.Name : val for key, val in zip(ghenv.Component.Params.Input[1:], args) }
        
        external_opts = args_dict.get('opts',{})
        external_local_metas = args_dict.get('local_metas',{})
        print('#1 self.local_metas == ' + str(self.local_metas))
        synched = self.local_metas.sync_to_shared_global_opts

        print('#1.05 self.local_metas == ' + str(self.local_metas))

        #if not self.local_metas.sync_to_shared_global_opts and self.local_metas.read_from_shared_global_opts:
        #    self.opts = GHsDNA.tools.opts.copy() 
        
        self.local_metas = GHsDNA.tools.override_all_opts( args_dict
                                                          ,self.opts 
                                                          ,external_opts 
                                                          ,self.local_metas 
                                                          ,external_local_metas
                                                          ,self.nick_name)
        print('#2 self.local_metas == ' + str(self.local_metas))
        #if not self.local_metas.sync_to_shared_global_opts and self.local_metas.write_to_shared_global_opts:
        #    GHsDNA.tools.override_all_opts(args_dict, GHsDNA.tools.opts, self.local_metas, self.nick_name)
        
        if self.opts['metas'].allow_components_to_change_type: 
            assert False
            if self.nick_name != ghenv.Component.NickName or self.local_metas.sync_to_shared_global_opts != synched:
                self.update_tools()
                
        #load_GHsDNA()
        #reload(tools)
        
        #y = globals().copy(); 
        #print([x for x in y if not x.startswith('__') ])        
        #z = locals().copy();
        #print([x for x in z if not x.startswith('__') ])
        #
        #
        ############################################################################################
        # TODO: Wrap sDNAPrepare, to map subprocess.returncode to True if 1
        # Check with Crispin if return code 0 means preparation was successful, or just successful execution.
        # And if we have to delete links based on deletion flag or can leave that to sDNA
        ############################################################################################
        #

        if go in [True, [True]]: # [True] in case go set to List Access in GH component but only connected to a normal boolean
            returncode = 999
            for tool in self.my_tools:
                returncode, f_name, Geom, Data, tmp_a = tool(ghenv, f_name, Geom, Data, self.opts, args)
                if isinstance(tmp_a, str):
                    self.a.write(tmp_a)
                else:
                    self.a = self.a.__add__(tmp_a)
                if returncode != 0:
                    break

            return returncode==0, f_name, Geom, Data, self.a, self.opts.copy(), self.local_metas

        else:   # e.g. if go not in= [True,[True]]
            return False, f_name, Geom, Data, self.a
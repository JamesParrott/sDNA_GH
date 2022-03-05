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



import os,sys 
from os.path import isfile, isdir, join, split, dirname
from importlib import import_module

from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
import ghpythonlib.treehelpers as th


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


class sDNA_GH():
    pass


def load_modules(m_names, path_lists):
    m_names = m_names if isinstance(m_names, tuple) else [m_names]  # Need this one to be immmutable, so it's hashable to use as a dict key
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
            if all(any(isfile(join(path, name.replace('.', os.sep) + ending)) 
                        for ending in ['.py','.pyc'] )
                            for name in m_names):
                # We haven't checked every folder in a package has an __init__.py
                output('Importing ' + str(m_names) +' ','DEBUG')
                return tuple(strict_import(name, path, '') for name in m_names) + (path,)
    return None



def is_file_any_type(s):
    return isinstance(s, str) and isfile(s)

class MyComponent(component):

    global sDNA_GH, sDNA_GH_search_paths, component_tool, log_file
    sDNA_GH_search_paths += [join(Grasshopper.Folders.DefaultAssemblyFolder
                                ,sDNA_GH_subfolder
                                ) 
                            ]
                          
    sDNA_GH.tools, sDNA_GH_path = load_modules('sDNA_GH.tools'
                                             ,sDNA_GH_search_paths)

    opts = sDNA_GH.tools.opts   # mutable.  Reference breakable and remakeable 
                               # to de sync / sync local opts to global opts
    local_metas = sDNA_GH.tools.local_metas   # immutable.  controls syncing /
                                             # desyncing / read / write of the
                                             # above, opts.
                                             # Although local, can be set on 
                                             # groups of components using the 
                                             # default section of a project 
                                             # config.ini, or passed as a
                                             # Grasshopper parameter between
                                             # components
    tools_dict = sDNA_GH.tools.tools_dict

  
    class_logger_name = "MyComponent"
    if sDNA_GH.tools.logger.__class__.__name__ == 'WriteableFlushableList':
        log_file = (  ghdoc.Path.rpartition('.')[0]  #type: ignore
                    + opts['options'].log_file_suffix + '_tracker1'
                    + '.log' ) 
        log_file_dir = split(log_file)[0]
        if isdir(log_file_dir):
            sDNA_GH.tools.logger = sDNA_GH.tools.wrapper_logging.new_Logger( 
                                            'sDNA_GH'
                                            ,log_file 
                                            ,opts['options'].logger_file_level
                                            ,opts['options'].logger_console_level
                                            )
        else:
            pass
            output('Invalid log file dir ' + log_file_dir + ' ', 'ERROR')

    logger = sDNA_GH.tools.logger #.getChild( class_logger_name)
   


    my_tools = None

    def update_tools(self):
        self.my_tools = sDNA_GH.tools.tool_factory( self.nick_name
                                                  ,name_map
                                                  ,self.opts)
        output('My_tools ==\n'
                +'\n'.join([tool.func_name for tool in self.my_tools])
                ,'DEBUG')


    def update_name(self):
        global name_map
        
        self.nick_name = ghenv.Component.NickName if component_tool==None else component_tool # type: ignore
        self.logger = self.logger.getChild(self.nick_name)
        self.update_tools()


        
    def update_sDNA(self):
        output('Self has attr sDNA == ' + str(hasattr(self,'sDNA'))+' ','DEBUG')
        output('self.opts[metas].sDNA == (' + str(self.opts['metas'].sDNAUISpec)
                + ', ' + self.opts['metas'].runsdna + ') ','DEBUG')

        if hasattr(self,'sDNA'):
            output('Self has attr sDNA == ' + str(hasattr(self,'sDNA'))+' ','DEBUG')
        
        sDNA = ( self.opts['metas'].sDNAUISpec  # Needs to be hashable to be
                ,self.opts['metas'].runsdna )   # a dict key => tuple not list

        if not hasattr(self,'sDNA') or self.sDNA != sDNA:
            self.UISpec, self.run, path = load_modules(sDNA, self.opts['metas'].sDNA_search_paths)

            output('Self has attr UISpec == ' + str(hasattr(self,'UISpec'))+' ' , 'DEBUG')
            output('Self has attr run == ' + str(hasattr(self,'run'))+' ' ,'DEBUG')

            self.sDNA = sDNA
            self.sDNA_path = path
            self.opts['metas'] = self.opts['metas']._replace(    sDNA = self.sDNA
                                                                ,sDNA_path = path 
                                                             )
            self.opts['options'] = self.opts['options']._replace(  UISpec = self.UISpec
                                                                  ,run = self.run 
                                                                  )  

            assert self.opts['metas'].sDNA_path == dirname(self.opts['options'].UISpec.__file__)                                                                  






    def __init__(self):

        
        self.a = sDNA_GH.tools.WriteableFlushableList()
        sDNA_GH.tools.wrapper_logging.add_custom_file_to_logger( self.logger
                                                               ,self.a
                                                               ,self.opts['options'].logger_custom_level)

        #runsdnacommand, sDNAUISpec = load_sDNA(options)


        self.update_sDNA()
        self.update_name()

        component.__init__(self)

  



    #sDNA_GH = strict_import('sDNA_GH', join(Grasshopper.Folders.DefaultAssemblyFolder,'sDNA_GH'), sub_folder = 'sDNA_GH')   
                                        # Grasshopper.Folders.AppDataFolder + r'\Libraries'
                                        # %appdata%  + r'\Grasshopper\Libraries'
                                        # os.getenv('APPDATA') + r'\Grasshopper\Libraries'
    def RunScript(self, go, Data, Geom, f_name, *args):
        # type (bool, str, Rhino Geometry, datatree, tuple(namedtuple,namedtuple), *dict)->bool, str, Rhino_Geom, datatree, str
        #if not 'opts' in globals():
        #    global opts
        if f_name and not isinstance(f_name, str) and isinstance(f_name, list):
            f_name=f_name[0]
        self.a = sDNA_GH.tools.WriteableFlushableList() #Reset. Discard output persisting from previous calls to this method (should be logged anyway).
        options = self.opts['options']

        args_dict = {key.Name : val for key, val in zip(ghenv.Component.Params.Input[1:], args) } # type: ignore
        
        external_opts = args_dict.get('opts',{})
        external_local_metas = args_dict.get('local_metas',{})
        gdm = args_dict.get('gdm',{})

        #print('#1 self.local_metas == ' + str(self.local_metas))
        
        if self.nick_name != ghenv.Component.NickName:  # type: ignore
            self.update_name()
            output( ' Tools in ' + self.nick_name + ' changed to : ' 
                            + str(self.my_tools), 'WARNING' )
        
        
        synched = self.local_metas.sync_to_shared_global_opts
        old_sDNA = self.opts['metas'].sDNA

        #print('#1.05 self.local_metas == ' + str(self.local_metas))

        #if not self.local_metas.sync_to_shared_global_opts and self.local_metas.read_from_shared_global_opts:
        #    self.opts = sDNA_GH.tools.opts.copy() 
        
        self.local_metas = sDNA_GH.tools.override_all_opts( args_dict 
                                                          ,self.opts # also mutates self.opts; local_metas immutable
                                                          ,external_opts 
                                                          ,self.local_metas 
                                                          ,external_local_metas
                                                          ,self.nick_name)
        #output('#2 self.local_metas == ' + str(self.local_metas),'DEBUG')
        
        if (self.opts['metas'].auto_update_Rhino_doc_path 
            and not isfile(self.opts['options'].Rhino_doc_path)):
            path = Rhino.RhinoDoc.ActiveDoc.Path
            if not isinstance(path, str) or not isfile(path):
                path = ghdoc.Path #type: ignore
            self.opts['options'] = self.opts['options']._replace(
                                                    Rhino_doc_path = path)

        if self.opts['metas'].allow_components_to_change_type: 
            #assert False
            
            if self.local_metas.sync_to_shared_global_opts != synched:
                self.opts = sDNA_GH.tools.opts if self.local_metas.sync_to_shared_global_opts else self.opts.copy()

            if self.opts['metas'].sDNA != old_sDNA:
                self.update_sDNA()
                self.update_tools()

                
        #load_sDNA_GH()
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
        # And if we have to delete groups based on deletion flag or can leave that to sDNA
        ############################################################################################
        #
        Defined_tools = [y for z in self.tools_dict.values() for y in z]
        Undefined_tools = [x for x in self.my_tools if x not in Defined_tools]

        if Undefined_tools:
            output('Defined_tools == ' + str(Defined_tools), 'DEBUG')
            output('Undefined tools == ' + str(Undefined_tools), 'DEBUG')
            raise ValueError(output('Tool function not in cache, possibly ' 
                                    + 'unsupported.  Check input tool_name '
                                    +'if sDNAGeneral, else tool_factory '
                                    ,'ERROR',self))


        if go in [True, [True]]: # [True] in case go set to List Access in GH component but only connected to a normal boolean
            returncode = 999
            assert isinstance(self.my_tools, list)

            output('my_tools == '+str(self.my_tools),'DEBUG')

            geom_data_map = sDNA_GH.tools.convert_Data_tree_and_Geom_list_to_gdm(Geom, Data, self.opts)
            
            output('geom_data_map == '+str(type(geom_data_map)),'DEBUG')

            geom_data_map = sDNA_GH.tools.override_gdm_with_gdm(gdm, geom_data_map, self.opts)

            output('After merge geom_data_map == '+str(type(geom_data_map)),'DEBUG')


            returncode, ret_f_name, gdm, a = sDNA_GH.tools.run_tools(self.my_tools, f_name, geom_data_map, self.opts)
            print (str(gdm))
            if isinstance(gdm, dict):
                (NewData, Geometry) = (
                  sDNA_GH.tools.convert_dictionary_to_data_tree_or_lists(gdm)
                                      )                
            else:
                NewData, Geometry = None, None

            ret_vals = (returncode==0), NewData, Geometry, ret_f_name, [gdm], a, [self.opts.copy()], [self.local_metas]
            #ret_vals = (returncode==0), NewData, Geometry, ret_f_name, a 

            if self.my_tools[-1] == sDNA_GH.tools.parse_data:
                ret_vals = (ret_vals[0], self.opts['options'].plot_min, self.opts['options'].plot_max) + ret_vals[1:]

            return ret_vals
                                         #In Python 3 .keys() returns a dictview not a list
        else:   
            #return False, Data, Geom, f_name, self.a #, self.opts.copy(), self.local_metas
            return False, Data, Geom, f_name, [gdm], self.a, [self.opts.copy()], [self.local_metas]

#! python2

import os 
import time
import random
import inspect
import logging
from collections import OrderedDict
import unittest

import System

import scriptcontext as sc 
import Rhino
import Rhino.NodeInCode.Components
import Grasshopper
import rhinoscriptsyntax as rs
import ghpythonlib.treehelpers as th
from ghpythonlib.componentbase import executingcomponent as component 

from sDNA_GH.tests.unit_tests.sDNA_GH_unit_tests import make_noninteractive_test_running_component_class


def GH_doc_components(doc = None):
    if doc is None:
        doc = ghdoc.Component.Attributes.DocObject.OnPingDocument()
    return {component.NickName : component
            for component in doc.Objects
           }

def set_data_on(param, val):
    param.ClearData()
    param.AddVolatileData(Grasshopper.Kernel.Data.GH_Path(0), 0, val)

def get_data_from(param):
    branch = Grasshopper.DataTree[object](param.VolatileData).Branch(0)
    return branch[0] if branch else None


# GH_Doc_components = GH_doc_components(GH_Doc)

#all_docs_comps = {
#    os.path.splitext(os.path.basename(doc.FilePath))[0] : (doc, GH_doc_components(doc)) 
#    for doc in Grasshopper.Instances.DocumentServer.GetEnumerator() 
#    }



def get_plugin_files(plugin = ''):

    gh_comp_server = Grasshopper.Kernel.GH_ComponentServer()
    #print(list(gh_comp_server.FindObjects(guid)))

    return OrderedDict((os.path.splitext(file_.FileName)[0], file_)
                        for file_ in gh_comp_server.ExternalFiles(True, True)
                        if plugin.lower() in file_.FilePath.lower()
                       )
def add_instance_of_userobject_to_canvas(name, plugin_files = None, comp_number=1, pos = (200, 550)):
    
    plugin_files = plugin_files or get_plugin_files('sDNA_GH')
    
    file_obj = next((v
                     for k, v in plugin_files.items() 
                     if name.lower() in k.lower()
                    )
                    ,None)
                    
    if file_obj is None:
        raise Exception('No user object found called: %s' % name)
    
#    print(dir(file_obj))
#    print(file_obj.GetHashCode())
#    guid = file_obj.FileHash
#    print(guid)
                    
    user_obj = Grasshopper.Kernel.GH_UserObject(file_obj.FilePath)

    comp_obj = user_obj.InstantiateObject()
    
    comp_obj.Locked = False
    
    
    
    sizeF = System.Drawing.SizeF(*get_position(comp_number, pos=pos))
    
    
    comp_obj.Attributes.Pivot = System.Drawing.PointF.Add(comp_obj.Attributes.Pivot, sizeF)
    
    success = GH_doc.AddObject(docObject = comp_obj, update = False)
    
    if not success:
        raise Exception('Could not add comp: %s to GH canvas' % comp_obj)
    
    return comp_obj 


if 'Recolour_Objects' not in GH_Doc_components:
    Recolour_Objects = add_instance_of_userobject_to_canvas('Recolour_Objects')
else:
    Recolour_Objects = GH_Doc_components['Recolour_Objects']


#info = Rhino.NodeInCode.Components.FindComponent('read')

#assert info


# Recolour_Objects = GH_Doc_components['Recolour_Objects'] 

# print(type(Recolour_Objects))

def run_comp(comp, **kwargs):
    
    comp.ClearData()
    #    comp.ExpireSolution(False)
    for param in comp.Params.Input:
        if param.NickName in kwargs:
            set_data_on(param, kwargs[param.NickName])
    comp.CollectData()
    comp.ComputeData()
    
    return {param.NickName : get_data_from(param) 
            for param in comp.Params.Output
           }




class UDPStream(object):
    def __init__(self, port, host):
        self.port = port
        self.host = host
        # SOCK_DGRAM is the socket type to use for UDP sockets
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    def write(self, str_):
        # https://docs.python.org/3/library/socketserver.html#socketserver-udpserver-example
        data = str_.encode("utf-8")
        self.sock.sendto(data, (self.host, self.port))

    def flush(self):
        pass






def save_doc_to_DIR(name = 'tmp_sDNA_GH_api_tests_working_file.3dm'):
    # 'Dale Fugier'
    # https://discourse.mcneel.com/t/sys-exit-shows-popup-window-instead-of-just-exiting/163811/7

    path = os.path.join(DIR, name)
    Rhino.RhinoApp.RunScript('_-SaveAs ' + path, True)
    





def exit_Rhino():
    #'Dale Fugier'
    # https://discourse.mcneel.com/t/sys-exit-shows-popup-window-instead-of-just-exiting/163811/7

    save_doc_to_DIR()
    Rhino.RhinoDoc.ActiveDoc.Modified = False

    hWnd = Rhino.RhinoApp.MainWindowHandle()
    ctypes.windll.user32.PostMessageW(hWnd, 0x0010, 0, 0) # - quits but doesn't set return code
    # ctypes.windll.user32.PostQuitMessage(ret_code) # - doesn't quit, even if Rhino doc saved.
    # ctypes.windll.user32.PostMessageW(hWnd, 0x0010, ret_code, 0) # - quits but doesn't set return code
    # ctypes.windll.user32.PostMessageW(hWnd, 0x0012, ret_code, 0) # - makes Rhino hang. ret code 1 is set
    #                                                              # after killing it from Task Manager.




#def run_Recolour_Objects(Data, Geom):
#    set_data_on(Recolour_Objects.Params.Input[0], True) #go
#    set_data_on(Recolour_Objects.Params.Input[4], Data) 
#    set_data_on(Recolour_Objects.Params.Input[5], Geom)

#    run_comp(Recolour_Objects, go=True, Data=Data, Geom=Geom)

    # a = get_data_from(Recolour_Objects.Params.Output[0])

    # print(a)


# cols = th.tree_to_list(colours)[0]

# print(len(cols[0]))


def make_callable_using_node_in_code(name):
    func_info = Rhino.NodeInCode.Components.FindComponent(name);
    
    #    if (func_info == null) { Print("Error finding function"); return; }
    
    func = func_info.Delegate #as dynamic;


    
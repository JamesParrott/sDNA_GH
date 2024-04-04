
#! /usr/bin/awk NR==3
# -*- coding: utf-8 -*-
# This module requires Grasshopper Python (Rhino3D)

# MIT License

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

__author__ = 'James Parrott'
__version__ = '3.0.0.alpha_3'



import os 
import time
import random
import inspect
import logging
from collections import OrderedDict
import unittest
import ctypes
import socket
import tempfile

import System

import scriptcontext as sc 
import Rhino
import Rhino.NodeInCode.Components
import Grasshopper
import rhinoscriptsyntax as rs
import ghpythonlib.treehelpers as th
from ghpythonlib.componentbase import executingcomponent as component 

from ..custom.skel.basic.ghdoc import ghdoc


TMP = tempfile.gettempdir()

DIR = TMP

for SUB_DIR in ( 'sDNA_GH', 'tests'):
    DIR = os.path.join(DIR, SUB_DIR)
    if not os.path.isdir(DIR):
        os.mkdir(DIR)

GH_DOC = ghdoc.Component.Attributes.DocObject.OnPingDocument()


def GH_doc_components(doc = GH_DOC):
    return {component.NickName : component
            for component in doc.Objects
           }

GH_DOC_COMPONENTS = GH_doc_components()

def set_data_on(param, val):
    param.ClearData()    
    print(param.Access)
    # "and isinstance(val, Grasshopper.DataTree[object])""
    # mimicks Grasshopper support for passing a list into a Tree access param
    if (param.Access == Grasshopper.Kernel.GH_ParamAccess.tree
        and isinstance(val, Grasshopper.DataTree[object])):
        #
        param.AddVolatileDataTree(val)
    elif isinstance(val, (list, tuple)):
        for i, item in enumerate(val):
            param.AddVolatileData(Grasshopper.Kernel.Data.GH_Path(0), i, item)
    else: 
        param.AddVolatileData(Grasshopper.Kernel.Data.GH_Path(0), 0, val)

def DataTree_to_DH_struct(data_tree, Type_ = None):
    # https://mcneel.github.io/grasshopper-api-docs/api/grasshopper/html/T_Grasshopper_Kernel_Data_GH_Structure_1.htm
    #
    # https://mcneel.github.io/grasshopper-api-docs/api/grasshopper/html/T_Grasshopper_DataTree_1.htm
    #
    Type_ = Type_ or Grasshopper.Kernel.Types.GH_String
    gh_struct = Grasshopper.Kernel.Data.GH_Structure[Type_]()

    for path in data_tree.Paths:
        for item in data_tree.Branch(path):
            gh_str = Type_(item)
            gh_struct.Append(gh_str, path)

def GH_struct_to_DataTree(gh_struct):
    # https://mcneel.github.io/grasshopper-api-docs/api/grasshopper/html/T_Grasshopper_Kernel_Data_GH_Structure_1.htm
    #
    # https://mcneel.github.io/grasshopper-api-docs/api/grasshopper/html/T_Grasshopper_DataTree_1.htm
    #
        data_tree = Grasshopper.DataTree[object]()
        for path in gh_struct.Paths:
            branch = gh_struct.Branch[path]
            for item in branch:
                data_tree.Add(item, path)

        return data_tree

def get_data_from(param):


    if param.Access == Grasshopper.Kernel.GH_ParamAccess.tree:
        # return param.VolatileData

        return GH_struct_to_DataTree(param.VolatileData)

    
    data_tree = Grasshopper.DataTree[object](param.VolatileData)
    
    if data_tree.DataCount >= 1: # Alternative: param.VolatileDataCount >= 1 
        return list(data_tree.AllData())
    else:
        branch = data_tree.Branch(0)
        return branch[0] if branch else None

    

    raise NotImplementedError('Unsupported Param.Access value %s. '
                             +'Supported: item, list and tree. '
                             % param.Access
                             )
    


def all_docs_comps():
   return {os.path.splitext(os.path.basename(doc.FilePath))[0] : (doc, GH_doc_components(doc)) 
           for doc in Grasshopper.Instances.DocumentServer.GetEnumerator() 
          }



def get_plugin_files(plugin = ''):

    gh_comp_server = Grasshopper.Kernel.GH_ComponentServer()
    #print(list(gh_comp_server.FindObjects(guid)))

    return OrderedDict((os.path.splitext(file_.FileName)[0], file_)
                        for file_ in gh_comp_server.ExternalFiles(True, True)
                        if plugin.lower() in file_.FilePath.lower()
                       )


def get_position(comp_number, row_width = 800, row_height = 175, pos = (200, 550)):
    l = comp_number * row_height
    x = pos[0] + (l % row_width)
    y = pos[1] + 220 * (l // row_width)
    return x, y

def add_instance_of_userobject_to_canvas(name, plugin_files = None, comp_number=1, pos = (200, 550)):
    
    plugin_files = plugin_files or get_plugin_files('sDNA_GH')
    
    file_obj = next((v
                     for k, v in plugin_files.items() 
                     if name.lower() in k.lower()
                    )
                    ,None)
                    
    if file_obj is None:
        raise Exception('No user object found called: %s' % name)
    

                    
    user_obj = Grasshopper.Kernel.GH_UserObject(file_obj.FilePath)

    comp_obj = user_obj.InstantiateObject()
    
    comp_obj.Locked = False
    
    
    
    sizeF = System.Drawing.SizeF(*get_position(comp_number, pos=pos))
    
    
    comp_obj.Attributes.Pivot = System.Drawing.PointF.Add(comp_obj.Attributes.Pivot, sizeF)
    
    success = GH_DOC.AddObject(docObject = comp_obj, update = False)
    
    if not success:
        raise Exception('Could not add comp: %s to GH canvas' % comp_obj)
    
    return comp_obj 



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


def get_user_obj_comp_from_or_add_to_canvas(name):
    
    if name not in GH_DOC_COMPONENTS:
        comp = add_instance_of_userobject_to_canvas(name)
        GH_DOC_COMPONENTS[name] = comp

    return GH_DOC_COMPONENTS[name]


class FileAndStream(object):
    def __init__(self, file, stream, print_too = False):
        self.file = file
        self.stream = stream
        if hasattr(file, 'fileno'):
            self.fileno = file.fileno
        self.print_too = print_too
        
    def write(self, *args):
        self.stream.write(*args)
        self.file.write(*args)
        if self.print_too:
            print(', '.join(args))
        
    def flush(self, *args):
        self.stream.flush()
        self.file.flush()
        
    def __enter__(self):
        self.file.__enter__()
        return self
        
    def __exit__(self, *args):
        return self.file.__exit__(*args)    


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






def make_callable_using_node_in_code(name):
    func_info = Rhino.NodeInCode.Components.FindComponent(name);
    
    #    if (func_info == null) { Print("Error finding function"); return; }
    
    func = func_info.Delegate #as dynamic;


    
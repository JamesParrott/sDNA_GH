#! /usr/bin/awk NR==3
# -*- coding: utf-8 -*-
# This module requires Grasshopper Python (Rhino3D)

# MIT License

# Copyright (c) [2021] [Cardiff University, a body incorporated
# by Royal Charter and a registered charity (number:
# 1136855) whose administrative offices are at 7th floor 30-
# 36 Newport Road, UniversityCF24 0DE, Wales, UK]

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
__version__ = '0.11'


import os
import logging
from collections import OrderedDict
import System  #.Net from IronPython

import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

from ...basic.ghdoc import ghdoc

try:
    basestring #type: ignore
except NameError:
    basestring = str

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())



###################################################################



Rhino_obj_for_shape = dict(NULL = None
                          ,POINT = 'PointCoordinates'
                          ,MULTIPATCH = 'MeshVertices'  
                          # Unsupported.  Complicated. 
                          ,POLYLINE = 'PolylineVertices'  
                          ,POLYGON = 'PolylineVertices'
                          ,MULTIPOINT = 'PointCloudPoints'  
                          # Unsupported
                          # Needs chaining to list or POINT
                          ,POINTZ = 'PointCoordinates'
                          ,POLYLINEZ = 'PolylineVertices'
                          ,POLYGONZ = 'PolylineVertices'  
                          ,MULTIPOINTZ = 'PointCloudPoints'  
                          #see MULTIPOINT
                          ,POINTM = 'PointCoordinates'
                          ,POLYLINEM = 'PolylineVertices'
                          ,POLYGONM = 'PolylineVertices'    
                          ,MULTIPOINTM = 'PointCloudPoints'  
                          #see MULTIPOINT
                          )  

def get_points_from_obj(x, shp_type='POLYLINEZ'):
    #type(str, dict) -> list
    f = getattr(rs, Rhino_obj_for_shape[shp_type])
    return [list(y) for y in f(x)]

Rhino_obj_checkers_for_shape = dict(NULL = [None]
                                   ,POINT = ['IsPoint']
                                   ,MULTIPATCH = ['IsMesh']  # Unsupported  
                                   # (too complicated).
                                   ,POLYLINE = ['IsLine','IsPolyline']  
                                   #IsPolyline ==False for lines, 
                                   # on which PolylineVertices works fine
                                   ,POLYGON = ['IsPolyline'] 
                                   #2 pt Line not a Polygon.
                                   # Doesn't check closed
                                   ,MULTIPOINT = ['IsPoint']   
                                   # e.g. 
                                   # lambda l : any(IsPoint(x) for x in l)
                                   ,POINTZ = ['IsPoint']
                                   ,POLYLINEZ = ['IsLine','IsPolyline']
                                   ,POLYGONZ = ['IsPolyline']   
                                   #Doesn't check enclosed shape
                                   ,MULTIPOINTZ = ['IsPoints']  
                                   # see MULTIPOINT
                                   ,POINTM = ['IsPoint']
                                   ,POLYLINEM = ['IsLine','IsPolyline']
                                   ,POLYGONM = ['IsPolyline']   
                                   #Doesn't check enclosed shape
                                   ,MULTIPOINTM = ['IsPoints']  
                                   # see MULTIPOINT
                                   )  

def is_shape(obj, shp_type):   #e.g. polyline
    # type(type[any], str) -> bool

    if hasattr(Rhino.Geometry, type(obj).__name__):
        geom = obj
    else:
        obj = System.Guid(str(obj))
        geom = Rhino.RhinoDoc.ActiveDoc.Objects.FindGeometry(obj)
        if not geom:
            geom = ghdoc.Objects.FindGeometry(obj)

    allowers = Rhino_obj_checkers_for_shape[shp_type]
    if isinstance(allowers, basestring):
        allowers = [allowers] 
    logger.debug('type(obj) == %s, obj == %s' % (type(obj), obj))
    logger.debug('type(geom) == %s, geom == %s' % (type(geom), geom))
    return any( getattr(rs, allower )( geom ) for allower in allowers)

Rhino_obj_code_for_shape = dict(NULL = None
                               ,POINT = 1         
                               # Untested.  
                               ,MULTIPATCH = 32    
                               # Unsupported.  Complicated.  
                               ,POLYLINE = 4
                               ,POLYGON = 4  
                               ,MULTIPOINT = 2     
                               # Untested.  
                               ,POINTZ = 1         
                               ,POLYLINEZ = 4
                               ,POLYGONZ = 4   
                               ,MULTIPOINTZ = 2 
                               ,POINTM = 1
                               ,POLYLINEM = 4
                               ,POLYGONM = 4  
                               ,MULTIPOINTM = 2
                               )  

def get_Rhino_objs(shp_type='POLYLINEZ'):
    #type (None) -> list
    return rs.ObjectsByType(geometry_type = Rhino_obj_code_for_shape[shp_type]
                           ,select = False
                           ,state = 0
                           )

Rhino_obj_adder_for_shape = dict(NULL = None
                                ,POINT = 'AddPoint'
                                ,MULTIPATCH = 'AddMesh'    
                                # Unsupported.  Complicated.
                                ,POLYLINE = 'AddPolyline'
                                ,POLYGON = 'AddPolyline'   
                                # Pyshp closes them
                                ,MULTIPOINT = 'AddPoints'
                                ,POINTZ = 'AddPoint'
                                ,POLYLINEZ = 'AddPolyline'
                                ,POLYGONZ = 'AddPolyline'   
                                #  Pyshp closes them
                                ,MULTIPOINTZ = 'AddPoints'
                                ,POINTM = 'AddPoint'
                                ,POLYLINEM = 'AddPolyline'
                                ,POLYGONM = 'AddPolyline'    
                                # Pyshp closes them
                                ,MULTIPOINTM = 'AddPoints'
                                )  


def obj_makers(
       shp_type = 'POLYLINEZ'
      #,make_new_group = make_group
      #,add_objects_to_group = add_objs_to_group
      ,Rhino_obj_adder_for_shape = Rhino_obj_adder_for_shape
      ):
    #type(str, dict) -> function
    rhino_obj_maker = getattr(rs, Rhino_obj_adder_for_shape[shp_type])
    return rhino_obj_maker
    # e.g. rhino_obj_maker = rs.AddPolyline


def add_objs_to_group(objs, group_name):
    #type(list, str) -> int
    return rs.AddObjectsToGroup(objs, group_name)  

def make_group(group_name = None):
    #type(str) -> str
    return rs.AddGroup(group_name)




def add_GH_rectangle(xmin, ymin, xmax, ymax, plane = None):
    """ Adds a Grasshopper rectangle defined by xmin, ymin, xmax, ymax."""
    #type(Number, Number, Number, Number) -> Rectangle


    width = xmax - xmin
    length = ymax - ymin

    logger.debug('Rectangle (width, length) == (%s,  %s)' % (width, length))

    if width == 0:
        raise ValueError('Rectangle cannot have zero width')
    if length == 0:
        raise ValueError('Rectangle cannot have zero length')

    tmp = sc.doc

    sc.doc = ghdoc


    if plane is None:
        plane = rs.WorldXYPlane()

    leg_frame = rs.AddRectangle(plane
                               ,width
                               ,length 
                               )

    rs.MoveObject(leg_frame, [xmin, ymin])
    
    sc.doc = tmp

    return leg_frame
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
__version__ = '2.7.1'


import os
import logging
import itertools
from collections import namedtuple
import System  #.Net from IronPython #type: ignore

import Rhino #type: ignore
import rhinoscriptsyntax as rs #type: ignore
import scriptcontext as sc #type: ignore

from ...basic.ghdoc import ghdoc
from . import funcs

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

def is_degree_1_Nurbs_Curve(obj):
    return rs.IsCurve(obj) and rs.CurveDegree(obj) == 1

Rhino_obj_checkers_for_shape = dict(NULL = [None]
                                   ,POINT = ['IsPoint']
                                   ,MULTIPATCH = ['IsMesh']  # Unsupported  
                                   # (too complicated).
                                   ,POLYLINE = ['IsLine','IsPolyline',is_degree_1_Nurbs_Curve]  
                                   #IsPolyline ==False for lines, 
                                   # on which PolylineVertices works fine
                                   ,POLYGON = ['IsPolyline',is_degree_1_Nurbs_Curve] 
                                   #2 pt Line not a Polygon.
                                   # Doesn't check closed
                                   ,MULTIPOINT = ['IsPoint']   
                                   # e.g. 
                                   # lambda l : any(IsPoint(x) for x in l)
                                   ,POINTZ = ['IsPoint']
                                   ,POLYLINEZ = ['IsLine','IsPolyline',is_degree_1_Nurbs_Curve]
                                   ,POLYGONZ = ['IsPolyline', is_degree_1_Nurbs_Curve]   
                                   #Doesn't check enclosed shape
                                   ,MULTIPOINTZ = ['IsPoints']  
                                   # see MULTIPOINT
                                   ,POINTM = ['IsPoint']
                                   ,POLYLINEM = ['IsLine','IsPolyline',is_degree_1_Nurbs_Curve]
                                   ,POLYGONM = ['IsPolyline',is_degree_1_Nurbs_Curve]   
                                   #Doesn't check enclosed shape
                                   ,MULTIPOINTM = ['IsPoints']  
                                   # see MULTIPOINT
                                   )  


SOURCES = namedtuple('SOURCES', 'IS_ALREADY_GEOM STRING')(0,1)



def get_geom_and_source_else_leave(obj):
    #type(type[any])-> type[any], type[any]
    """ Leaves Geometric objects and non-guid strings alone.
        Otherwise searches Rhino doc and ghdoc with obj as guid.
    """
    if hasattr(Rhino.Geometry, type(obj).__name__):
        return obj, SOURCES.IS_ALREADY_GEOM
        # So that we can call it on curves and it will leave them alone

    if isinstance(obj, basestring):
        # To leave legend tags, group names and layer names alone
        try:
            obj = System.Guid(obj)
        except: # (TypeError, ValueError):
            return obj, SOURCES.STRING

    for source in (Rhino.RhinoDoc.ActiveDoc, ghdoc):
        geom = source.Objects.FindGeometry(obj)
        if geom is not None:
            return geom, source
    else:
        msg = 'Type: %s, val: %s, not supported by get_geom_and_source_else_leave' 
        msg %= (type(obj), obj)
        logger.error(msg)
        raise NotImplementedError



# def try_to_get_Rhino_GH_geom_obj_else_leave(obj):
#     #type(type[any])-> type[any]
#     if hasattr(Rhino.Geometry, type(obj).__name__):
#         return obj
#     if isinstance(obj, basestring) and not funcs.is_uuid(obj):
#         # To leave legend tags, group names and layer names alone
#         return obj
#     obj = System.Guid(str(obj))
#     geom = Rhino.RhinoDoc.ActiveDoc.Objects.FindGeometry(obj)
#     if geom is not None:
#         return geom
#     return ghdoc.Objects.FindGeometry(obj)


# One call in Read_Geom, 3 calls in Write_Shp
def is_shape(obj, shp_type):   #e.g. polyline
    # type(type[any], str) -> bool

    # if hasattr(Rhino.Geometry, type(obj).__name__):
    #     geom = obj
    # else:
    #     obj = System.Guid(str(obj))
    #     geom = Rhino.RhinoDoc.ActiveDoc.Objects.FindGeometry(obj)
    #     if not geom:
    #         geom = ghdoc.Objects.FindGeometry(obj)
    geom, source = get_geom_and_source_else_leave(obj)

    logger.log(level = 1,msg = 'type(obj): %s, obj: %s' % (type(obj), obj)) 
    logger.log(level = 1,msg = 'type(geom): %s, geom: %s' % (type(geom), geom))
    logger.log(level = 1,msg = 'source: %s' % source)
    #logger.log(level = 1, 
    #rs.IsPolyLine etc. need to be called on guids, not geom objects or strings
    if hasattr(Rhino.Geometry, type(obj).__name__): 
        msg = 'Call is_shape on Rhino or Grasshopper Guid, '
        msg += 'not object Geometry: %s, obj: %s ' % (type(obj), obj)
        raise NotImplementedError(msg) 
    
    if not funcs.is_uuid(obj):
        return False
        #We might have legend tags, group names or layer names in the gdm

    allowers = Rhino_obj_checkers_for_shape[shp_type]
    if isinstance(allowers, basestring):
        allowers = [allowers] 
    # logging.DEBUG == 10
    # This module logger, the package logger, and one of its handlers need to 
    # be set to level 1 to see these log messages
    tmp = sc.doc
    sc.doc = source
    retval = any( getattr(rs, allower )( obj ) if isinstance(allower, basestring) else allower(obj)
                  for allower in allowers
                )
    sc.doc = tmp
    
    return retval

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


def add_degree_one_NurbsCurve(points):
    Point3Ds = [Rhino.Geometry.Point3d(*list_) 
                for list_ in points
               ]
    nurbs_curve = Rhino.Geometry.NurbsCurve.Create(periodic = False
                                                  ,degree = 1
                                                  ,points = Point3Ds
                                                  )

    # https://github.com/mcneel/rhinoscriptsyntax/blob/c49bd0bf24c2513bdcb84d1bf307144489600fd9/Scripts/rhinoscript/curve.py#L562
    rc = sc.doc.Objects.AddCurve(nurbs_curve)

    if rc==System.Guid.Empty: 
        raise Exception("Could not add NurbsCurve to document")
    sc.doc.Views.Redraw()

    return rc


Rhino_fallback_obj_adder_for_shape = dict(
                                 POLYLINE = add_degree_one_NurbsCurve
                                ,POLYGON = add_degree_one_NurbsCurve   
                                ,POLYLINEZ = add_degree_one_NurbsCurve
                                ,POLYGONZ = add_degree_one_NurbsCurve   
                                ,POLYLINEM = add_degree_one_NurbsCurve
                                ,POLYGONM = add_degree_one_NurbsCurve   
                                ) 



def L2(X, Y):
    retval = 0
    for x, y in zip(X,Y):
        retval += (x - y)**2
    return retval**0.5


TOL = 1e-15  # 2e-17 is near machine eps on my machine


class InvalidPolyline(list):
    """ Criteria from: rhino_url
    
        "Valid polylines have at least one segment, no Invalid points and no zero length segments.

        Closed polylines with only two segments are also not considered valid.    "
    """

    rhino_url = 'https://developer.rhino3d.com/api/RhinoCommon/html/P_Rhino_Geometry_Polyline_IsValid.htm'
    sDNA_url = 'https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/network_preparation.html#connectivity-errors-at-key-locations'


    @classmethod
    def from_points(cls, points_list, num, error):
    #type(InvalidPolyline, list(list(Number), ...) -> bool)

        instance = cls()

        instance.append(('While adding shape number: %s error: {{ %s }} occurred, '
                       +' possibly due to not meeting the criteria here: %s'  )
                       % (num, error, cls.rhino_url)
                       )

        if not points_list:
            instance.append('** Zero-length (or falsey) list of points. ')

        if len(points_list) == 1:
            instance.append('** Polylines must have at least one segment. '
                           +' Only one point in list. '
                           )

        d_ = {0: 'x', 1: 'y', 2: 'z'}

        # https://developer.rhino3d.com/api/RhinoCommon/html/P_Rhino_Geometry_Point3d_IsValid.htm
        # "Each coordinate of the point must pass the IsValidDouble(Double) test "

        invalid_points = ['%s: %s, point number %s' % (d_[j], coord, i)
                          for i, point in enumerate(points_list)
                          for j, coord in enumerate(point)
                          if not Rhino.RhinoMath.IsValidDouble(coord)
                         ]

        if invalid_points:
            instance.append('** The following points are invalid: %s ' 
                           +'(Rhino.RhinoMath.IsValidDouble(coord) is False). '
                           % str(invalid_points)
                           )

        zero_length_segments = ['point num %s, %s too close to num %s, %s' % (i, x, i+1, points_list[i+1])
                                for i, x in enumerate(points_list[:-1])
                                if L2(x, points_list[i+1]) < TOL
                               ] 
        
        if zero_length_segments:
            instance.append('** The following pairs of points are too close: %s '
                           +'(sqrt of sum of squares of diffs, TOL = %s). ' 
                           % (str(zero_length_segments), TOL)
                           )

        if not zero_length_segments and len(points_list) == 3:
            start = points_list[0]
            mid = points_list[1]
            end = points_list[2]
            tol = 100*TOL
            if L2(start, end) < tol:


                instance.append(('** Valid closed polylines must have more than two segments. '
                               +'start = %s and end = %s may be too close (mid = %s). '
                               +'There is probably an error in the data the shapefile came from. '
                               +'sDNA recommends breaking *loop links* - %s  ')
                               % (start, end, mid, cls.sDNA_url)
                               )

        return instance

    def __str__(self):
        return '\n'.join(reason_invalid for reason_invalid in self)


def obj_maker_for_shape_type(
       shp_type = 'POLYLINEZ'
      #,make_new_group = make_group
      #,add_objects_to_group = add_objs_to_group
      ,Rhino_obj_adder_for_shape = Rhino_obj_adder_for_shape
      ):
    #type(str, dict) -> function
    # rhino_obj_maker = getattr(rs, Rhino_obj_adder_for_shape[shp_type])
    # #return rhino_obj_maker
    # # e.g. rhino_obj_maker = rs.AddPolyline
    # def f(x):
    #     return rhino_obj_maker(x)
    # return f

    first = getattr(rs, Rhino_obj_adder_for_shape[shp_type])
    fallback = Rhino_fallback_obj_adder_for_shape[shp_type]

    def obj_maker(points):

        # rhinoscriptsyntax.AddPolyline just raises a plain Exception:
        # """"
        # if rc==System.Guid.Empty: raise Exception("Unable to add polyline to document")
        # """"
        # https://github.com/mcneel/rhinoscriptsyntax/blob/c49bd0bf24c2513bdcb84d1bf307144489600fd9/Scripts/rhinoscript/curve.py#L563
        try:
            return first(points)
        except Exception as e_first:
            try:
                return fallback(points)
            except Exception as e_fallback:
                # optionally handled in tools.ShapefileReader added_geom_generator by invalid_obj_handler
                pass
                
    return obj_maker


Rhino_obj_adder_invalid_handlers = dict(
                                 POLYLINE = InvalidPolyline.from_points
                                ,POLYGON = InvalidPolyline.from_points   
                                ,POLYLINEZ = InvalidPolyline.from_points
                                ,POLYGONZ = InvalidPolyline.from_points   
                                ,POLYLINEM = InvalidPolyline.from_points
                                ,POLYGONM = InvalidPolyline.from_points   
                                ) 
# def obj_makers(
#        shp_type = 'POLYLINEZ'
#       #,make_new_group = make_group
#       #,add_objects_to_group = add_objs_to_group
#       ,Rhino_obj_adder_for_shape = Rhino_obj_adder_for_shape
#       ):
#     #type(str, dict) -> function
#     rhino_obj_maker = getattr(rs, Rhino_obj_adder_for_shape[shp_type])
#     #return rhino_obj_maker
#     # e.g. rhino_obj_maker = rs.AddPolyline
#     def f(x):
#         return rhino_obj_maker(x)
#     return f


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
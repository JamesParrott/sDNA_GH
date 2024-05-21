#! /usr/bin/awk NR==3
# -*- coding: utf-8 -*-
# This module requires Grasshopper Python (Rhino3D)

# MIT License

# Copyright (c) [2021] [Cardiff University, a body incorporated
# by Royal Charter and a registered charity (number:
# 1136855) whose administrative offices are at 7th floor 30-
# 36 Newport Road, University CF24 0DE, Wales, UK]

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

__authors__ = {'James Parrott', 'Crispin Cooper'}
__version__ = '3.0.0.alpha_4'

import os
import itertools

import System
import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs

from Cheetah.helpers import run_comp, get_user_obj_comp_from_or_add_to_canvas, GH_DOC_COMPONENTS
from Anteater_GH.fuzzers import random_Geometry, random_int

from ...skel.basic.ghdoc import ghdoc
from . import make_unit_test_TestCase_instance_generator

if Rhino.RhinoDoc.ActiveDoc.Name:
    raise Exception("These tests require a clean Rhino Document to test in. "
                    "To protect your document: save your Rhino file"
                    ", create a new one (and don't save it)"
                    ", run an Unload_sDNA component"
                    ", and re-initialise this component to restart the tests. "
                   )


Write_Shp = get_user_obj_comp_from_or_add_to_canvas('Write_Shp')
Read_Shp = get_user_obj_comp_from_or_add_to_canvas('Read_Shp')

# Run now to prevent the first test spuriously failing.
#   
# Most sDNA_GH components need to run RunScript, to 
# add their params etc. before they can be used.  
# 
# This call can be removed if a test fail is needed 
# e.g. in dev, to test the result of a test failure.
run_comp(Write_Shp)
run_comp(Read_Shp)


def get_polyline(id):
    guid = System.Guid(id)
    geom = Rhino.RhinoDoc.ActiveDoc.Objects.FindGeometry(guid)
    success, polyline = geom.TryGetPolyline()
    if not success:
        raise Exception('Could not get polyline for geom: %s, guid: %s' % (geom, guid))
    return polyline


def roundtrip_a_random_num_of_random_polylines_through_a_ShapeFile(self):
    # Can be called with None or used as a unittest.TestCase 
    # method, if assigned on to an instance at run-time, dynamically.
    # Allows configurable fuzz testing and parametric testing.
    sc.doc = Rhino.RhinoDoc.ActiveDoc
    Geom = random_Geometry(gens = [rs.AddPolyline,])

    Curves = [rs.PolylineVertices(geom) for geom in Geom]


    write_shp_retvals = run_comp(Write_Shp, go = True, Geom = Geom)

    shp_file = write_shp_retvals['file'][0]

    sc.doc = ghdoc
    read_shp_retvals = run_comp(Read_Shp, go = True, file = shp_file)

    # Delete test artefacts.  The safety of this assumes
    # Write_Shp has correctly avoided pre-existing files.
    shp_file_name = os.path.splitext(shp_file)[0]
    for ext in ('shp', 'shx', 'dbf'):
        shp_file_part = '%s.%s' % (shp_file_name, ext)
        if os.path.isfile(shp_file_part):
            os.remove(shp_file_part)

    Shp_Geom = read_shp_retvals['Geom']

    for j, (expected, actual_geom) in enumerate(zip(Curves, Shp_Geom), start=1):

        success, actual = actual_geom.Value.TryGetPolyline() #get_polyline(actual_geom)
        

        if self is not None:
            self.assertTrue(success)
            msg = (' test number: %s\n expected: %s\n actual: %s\n' 
                  % (j, expected, actual)
                  )
            for point_ex, point_act in itertools.zip_longest(expected, actual, fillvalue = None):
                self.assertAlmostEqual(
                    point_ex
                    ,point_act
                    ,msg=  msg
                    )
        else:
            print('Expected: %s, Actual: %s: Correctly round tripped: %s' 
                 % (expected, actual, expected == actual)
                 )
      




test_case_generator = make_unit_test_TestCase_instance_generator(
                            method = roundtrip_a_random_num_of_random_polylines_through_a_ShapeFile,
                            )
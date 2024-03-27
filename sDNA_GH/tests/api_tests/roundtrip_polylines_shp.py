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

__author__ = 'James Parrott'
__version__ = '3.0.0.alpha_3'


import System
import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs

from . import make_unit_test_TestCase_instance_generator
from ..helpers import run_comp, get_user_obj_comp_from_or_add_to_canvas, GH_DOC_COMPONENTS
from ..fuzzers import random_Geometry, random_int



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
    geom = sc.doc.Objects.FindGeometry(guid)
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

    # N = len(Geom)


    
    # for __ in range(N):

    # TODO: Work out how to pass in, and extract lists from Grasshopper components.
    write_shp_retvals = run_comp(Write_Shp, go = True, Geom = Geom)

    read_shp_retvals = run_comp(Read_Shp, go = True, bake = True, file = write_shp_retvals['file'])


    for j, (expected_initial_geom, actual_geom) in enumerate(zip(Geom, read_shp_retvals['Geom']), start=1):
        # actual_guid = System.Guid(actual_geom)


        expected = get_polyline(expected_initial_geom)
        actual = get_polyline(actual_geom)

        if self is not None:
            self.assertAlmostEqual(
                 expected
                ,actual
                ,msg=(' test number: %s\n expected: %s, guid: %s\n actual: %s\n guid: %s' 
                        % (j, expected, expected_initial_geom, actual, actual_guid)
                     )  
                )
        else:
            print('%s: Correctly round tripped: %s' % (actual_guid, expected == actual))
      




test_case_generator = make_unit_test_TestCase_instance_generator(
                            method = roundtrip_a_random_num_of_random_polylines_through_a_ShapeFile,
                            )
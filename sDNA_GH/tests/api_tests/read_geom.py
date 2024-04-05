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
from ..fuzzers import random_Geometry, random_int, random_nurbs_curve



if Rhino.RhinoDoc.ActiveDoc.Name:
    raise Exception("These tests require a clean Rhino Document to test in. "
                    "To protect your document: save your Rhino file"
                    ", create a new one (and don't save it)"
                    ", run an Unload_sDNA component"
                    ", and re-initialise this component to restart the tests. "
                   )




Read_Geom = get_user_obj_comp_from_or_add_to_canvas('Read_Geom')

# Run now to prevent the first test spuriously failing.
#   
# The Read_Geom component needs to run RunScript, to 
# add its params etc. before we can test it.  
# 
# This call can be removed if a test fail is needed 
# e.g. in dev, to test the result of a test failure.
run_comp(Read_Geom)

def read_geom(self):
    # Can be called with None or used as a unittest.TestCase 
    # method, if assigned on to an instance at run-time, dynamically.
    # Allows configurable fuzz testing and parametric testing.
    sc.doc = Rhino.RhinoDoc.ActiveDoc
    obj_gens = OBJECT_GENERATORS.copy()
    polyline_gens = (rs.AddPolyline, rs.AddLine, rs.AddCurve, random_nurbs_curve)

    for polyline_gen in polyline_gens:
        obj_gens.remove(polyline_gen)

    
    for polyline_gen in polyline_gens:

        # Or delete polylines
        save_rhino_document_to_tmp()
        create_fresh_rhino_document()


        Other_Geom = random_Geometry(gens = obj_gens)

        # How to add some to layers?
        # How to select some?
        Polylines = random_Geometry(gens = [polyline_gen,])



        # TODO: Work out how to pass in, and extract lists from Grasshopper components.
        # for __ in range(N):

        #     random_retvals = run_comp(GHRandomComponent, R = domain_retvals['I'], N=1, S = random_int(0, 250000))

        #     gradient_retvals = run_comp(GHGradientComponent, L0=L0, L1=L1, t = random_retvals['nums'])

        #     col = gradient_retvals['C']
        #     colours.append(col.Value)

        layer = 
        selected = 


        Read_Geom_retvals = run_comp(Read_Geom, go=True, selected = selected, layer = layer)
        Actual_Polylines = set(Read_Geom_retvals['Geom'])

        Expected_Polylines = set((obj.guid for obj in polyline_gens
                                  if (not selected or rs.ObjectSelected(obj))
                                  if (layer is None or obj.layer == layer)
                                 )
                                )

        if self is not None:
            self.assertEqual(
                Expected_Polylines
                Actual_Polylines
                ,msg=('expected: %s\n actual: %s\n, layer: %s, selected: %s' 
                     % (Expected_Polylines, Actual_Polylines, layer, selected)
                     )
                )  
        else:   
            print('Selected correctly: %s' % (guid, Expected_Polylines == Actual_Polylines))
        




test_case_generator = make_unit_test_TestCase_instance_generator(
                            method = read_geom,
                            )
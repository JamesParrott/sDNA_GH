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

import os
import itertools


import System
import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs

from ...custom.skel.tools.helpers.funcs import recycle_file

from . import make_unit_test_TestCase_instance_generator
from ..helpers import (run_comp,
                       get_user_obj_comp_from_or_add_to_canvas,
                       GH_DOC_COMPONENTS,
                       save_doc_to_,
                       DIR
                      )
from ..fuzzers import (random_Geometry,
                       random_int,
                       random_nurbs_curve,
                       random_string,
                       random_boolean,
                       OBJECT_GENERATORS
                      )



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

def settings():
    yield False, None
    # yield True, None
    # yield False, random_string()
    # yield True, random_string()


def randomly_either_call_f_or_remove(set_, f):
    
    sc.doc = Rhino.RhinoDoc.ActiveDoc

    to_be_removed = []
    for item in set_:
        if random_boolean():
            f(item)
        else:
            to_be_removed.append(item)

    for item in to_be_removed:
        # This just deselects item.  If it's an object id, 
        # the object will still exist in the Rhino Doc.
        set_.remove(item)


def call_f_on_all_Objects(f):
    
    sc.doc = Rhino.RhinoDoc.ActiveDoc

    f(rs.AllObjects(include_lights=True, include_grips=True, include_references=True))
    f(rs.HiddenObjects(include_lights=True, include_grips=True, include_references=True))
    f(rs.LockedObjects(include_lights=True, include_grips=True, include_references=True))


def read_geom(self):
    # Can be called with None or used as a unittest.TestCase 
    # method, if assigned on to an instance at run-time, dynamically.
    # Allows configurable fuzz testing and parametric testing.
    
    polyline_gens = (rs.AddPolyline, rs.AddLine, lambda : random_nurbs_curve(order=1))

    
    other_obj_gens = [obj_gen 
                      for obj_gen in OBJECT_GENERATORS
                      if obj_gen not in polyline_gens + (rs.AddRectangle, random_nurbs_curve)
                     ] 

    file_prefix = 'read_geom_working_file_(%s).3dm'

    # Save any pre-existing Rhino file to tmp_file
    for i in itertools.count():
        name = file_prefix % i
        tmp_file = os.path.join(DIR, name)
        if not os.path.isfile(tmp_file):
            break

    save_doc_to_(tmp_file, dir_ = '')

    for j, polyline_gen in enumerate(polyline_gens):
        # Don't use itertools.product 
        # Generate new random strings for layer,
        # for each polyline_gen
        for selected, layer in settings():

            sc.doc = Rhino.RhinoDoc.ActiveDoc

            call_f_on_all_Objects(rs.DeleteObjects)



            Other_Geom = random_Geometry(gens = other_obj_gens)

            # How to add some to layers?
            # How to select some?
            Polylines = set(random_Geometry(gens = [polyline_gen,]))

            if selected:
                call_f_on_all_Objects(rs.UnselectObjects)
                randomly_either_call_f_or_remove(Polylines, rs.SelectObject)

            kwargs = dict()

            if layer is not None:
                rs.AddLayer(layer)
                kwargs['layer'] = layer

                randomly_either_call_f_or_remove(Polylines, lambda obj: rs.ObjectLayer(obj, layer))

            

            Read_Geom_retvals = run_comp(Read_Geom, go=True, selected = False, **kwargs)
            Actual_Polylines = set(Read_Geom_retvals['Geom'] if Read_Geom_retvals['Geom'] else [])

            unexpected = Actual_Polylines - Polylines
            missing = Polylines - Actual_Polylines

            if self is not None:
                self.assertFalse(
                     bool(unexpected)
                    ,msg=('%s) unexpected: %s\n layer: %s, selected: %s, polyline_gen: %s' 
                         % (j, unexpected, layer, selected, polyline_gen)
                         )
                    )  
                self.assertFalse(
                     bool(missing)
                    ,msg=('%s) missing: %s\n layer: %s, selected: %s, polyline_gen: %s' 
                         % (j, missing, layer, selected, polyline_gen)
                         )
                    )  
            else:   
                print('%s).  Selected correctly: %s' % (j, Actual_Polylines == Polylines))
            




test_case_generator = make_unit_test_TestCase_instance_generator(
                            method = read_geom,
                            )
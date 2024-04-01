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



try:
    GHRandomComponent = GH_DOC_COMPONENTS['Random']
    GHGradientComponent = GH_DOC_COMPONENTS['Gradient']
    GHDomainComponent = GH_DOC_COMPONENTS['Dom']
except KeyError:
    raise Exception("These tests require a Random Sequence component"
                    ", a Gradient component "
                    ", and a Construct Domain (Dom) component"
                    " on the canvas. "
                    "Place these components, run an Unload_sDNA component"
                    ", and then re-initialise this component to restart the tests. "
                   )

Recolour_Objects = get_user_obj_comp_from_or_add_to_canvas('Recolour_Objects')

# Run now to prevent the first test spuriously failing.
#   
# The Recolour_Objects component needs to run RunScript, to 
# add its params etc. before we can test it.  
# 
# This call can be removed if a test fail is needed 
# e.g. in dev, to test the result of a test failure.
run_comp(Recolour_Objects)

def recolouring_random_num_of_random_objs_random_cols(self):
    # Can be called with None or used as a unittest.TestCase 
    # method, if assigned on to an instance at run-time, dynamically.
    # Allows configurable fuzz testing and parametric testing.
    sc.doc = Rhino.RhinoDoc.ActiveDoc
    Geom = random_Geometry()

    N = len(Geom)

    colours = []

    L0, L1 = -123, 172

    domain_retvals = run_comp(GHDomainComponent, A=L0, B=L1)

    
    random_retvals = run_comp(GHRandomComponent, R = domain_retvals['I'], N=N, S = random_int(0, 250000))

    # raise Exception('random, type: %s, val: %s' % (type(random_retvals), random_retvals))

    gradient_retvals = run_comp(GHGradientComponent, L0=L0, L1=L1, t = random_retvals['nums'])

    # raise Exception('random, type: %s, val: %s' % (type(gradient_retvals), gradient_retvals))

    colours = gradient_retvals['C']

    # TODO: Work out how to pass in, and extract lists from Grasshopper components.
    # for __ in range(N):

    #     random_retvals = run_comp(GHRandomComponent, R = domain_retvals['I'], N=1, S = random_int(0, 250000))

    #     gradient_retvals = run_comp(GHGradientComponent, L0=L0, L1=L1, t = random_retvals['nums'])

    #     col = gradient_retvals['C']
    #     colours.append(col.Value)




    run_comp(Recolour_Objects, go=True, Data=colours, Geom=Geom)

    for j, (geom, colour) in enumerate(zip(Geom, colours), start=1):
        guid = System.Guid(geom)
        if not guid:
            print('j: %s, Falsey guid: %s' % (j, guid))
            continue
        obj = Rhino.RhinoDoc.ActiveDoc.Objects.Find(guid)
        if not obj:
            print('j: %s, Falsey obj: %s' % (j, obj))
            continue

        # Just test the numbers.
        # It would be nice, but we don't need to require that both 
        # colours are of exactly the same type (from our test machinery
        # and the attribute on the recoloured object).  
        expected = colour.Value
        actual = obj.Attributes.ObjectColor

        if self is not None:
            self.assertEqual(
                 expected
                ,actual
                ,msg=('\n obj: %s\n test number: %s\n expected: %s\n actual: %s\n guid: %s' 
                        # % (Rhino.RhinoDoc.ActiveDoc.Objects.FindGeometry(guid), j, colour, obj.Attributes.ObjectColor, guid)
                        % (obj, j, expected, actual, guid)
                     )  
                )   
        print('%s: Correct colour: %s' % (guid, obj.Attributes.ObjectColor == colour))
      




test_case_generatore = make_unit_test_TestCase_instance_generator(
                            method = recolouring_random_num_of_random_objs_random_cols,
                            )
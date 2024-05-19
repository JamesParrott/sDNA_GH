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

import itertools

import System
import Rhino
import Grasshopper
import scriptcontext as sc
import rhinoscriptsyntax as rs
from ghpythonlib import treehelpers as th

from ...custom.skel.basic.ghdoc import ghdoc

from . import make_unit_test_TestCase_instance_generator
from Cheetah_GH.helpers import (run_comp,
                                get_user_obj_comp_from_or_add_to_canvas,
                                GH_DOC_COMPONENTS,
                                )

from Anteater_GH.fuzzers import random_Geometry, random_int, random_string, random_number, OBJECT_GENERATORS



if Rhino.RhinoDoc.ActiveDoc.Name:
    raise Exception("These tests require a clean Rhino Document to test in. "
                    "To protect your document: save your Rhino file"
                    ", create a new one (and don't save it)"
                    ", run an Unload_sDNA component"
                    ", and re-initialise this component to restart the tests. "
                   )


Parse_Data = get_user_obj_comp_from_or_add_to_canvas('Parse_Data')

# Run now to prevent the first test spuriously failing.
#   
# Most sDNA_GH components need to run RunScript, to 
# add their params etc. before they can be used.  
# 
# This call can be removed if a test fail is needed 
# e.g. in dev, to test the result of a test failure.
run_comp(Parse_Data)


def factory(obj_gens = None):

    def parse_synthetic_data(self):
        # Can be called with None or used as a unittest.TestCase 
        # method, if dynamically assigned on to an instance at run-time.
        # Allows configurable fuzz testing and parametric testing.
        sc.doc = Rhino.RhinoDoc.ActiveDoc

        Geom = random_Geometry(obj_gens)
        keys_lists, vals_lists = [], []
        Data_list = [keys_lists, vals_lists]
        
        test_key = random_string()
        
        expected = []

        for __ in range(len(Geom)):
            keys = [(random_string() for ___ in range(random_int() - 1))]

            index = random_int(0, len(keys))

            keys.insert(index, test_key)

            # If test_key was already in keys, there'll just be
            # one less test value
            unique_keys = list(set(keys))

            vals = [random_number() for __ in range(len(keys))]
            
            keys_lists.append(keys)
            vals_lists.append(vals)

            expected.append(vals[index])



        Data = th.list_to_tree(Data_list)

        parse_data_retvals = run_comp(Parse_Data, go = True, Geom = Geom, Data = Data, field = test_key)
        
        Data_read_from_parse_data = parse_data_retvals['Data']

        Actual_Data_list = th.tree_to_list(Data_read_from_parse_data, retrieve_base = None)


        for j, (exp, actual) in enumerate(zip(expected, Actual_Data_list), start=1):

            msg = 'Test: %s) expected: %s, actual: %s' % (j, exp, actual)

            if self is not None:
                self.assertAlmostEqual(float(exp), float(actual), msg)
            else:
                print(msg)
    return parse_synthetic_data

parse_synthetic_data = factory()

test_case_generator = make_unit_test_TestCase_instance_generator(
                            method = parse_synthetic_data,
                            )
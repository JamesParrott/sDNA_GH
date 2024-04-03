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

import itertools

import System
import Rhino
import Grasshopper
import scriptcontext as sc
import rhinoscriptsyntax as rs
from ghpythonlib import treehelpers as th

from ...custom.skel.basic.ghdoc import ghdoc

from . import make_unit_test_TestCase_instance_generator
from ..helpers import run_comp, get_user_obj_comp_from_or_add_to_canvas, GH_DOC_COMPONENTS
from ..fuzzers import random_Geometry, random_int, random_string, OBJECT_GENERATORS



if Rhino.RhinoDoc.ActiveDoc.Name:
    raise Exception("These tests require a clean Rhino Document to test in. "
                    "To protect your document: save your Rhino file"
                    ", create a new one (and don't save it)"
                    ", run an Unload_sDNA component"
                    ", and re-initialise this component to restart the tests. "
                   )


Write_Usertext = get_user_obj_comp_from_or_add_to_canvas('Write_Usertext')
Read_Usertext = get_user_obj_comp_from_or_add_to_canvas('Read_Usertext')

# Run now to prevent the first test spuriously failing.
#   
# Most sDNA_GH components need to run RunScript, to 
# add their params etc. before they can be used.  
# 
# This call can be removed if a test fail is needed 
# e.g. in dev, to test the result of a test failure.
run_comp(Write_Usertext)
run_comp(Read_Usertext)


def factory(obj_gens = None):

    def roundtrip_UserText(self):
        # Can be called with None or used as a unittest.TestCase 
        # method, if dynamically assigned on to an instance at run-time.
        # Allows configurable fuzz testing and parametric testing.
        sc.doc = Rhino.RhinoDoc.ActiveDoc

        Geom = random_Geometry(obj_gens)
        keys_lists, vals_lists = [], []
        Data_list = [keys_lists, vals_lists]
        for __ in range(len(Geom)):

            unique_keys = set((random_string() for ___ in range(random_int())))

            keys = list(unique_keys)
            vals = [random_string() for __ in range(len(keys))]
            
            keys_lists.append(keys)
            vals_lists.append(vals)

        Data = th.list_to_tree(Data_list)

        gh_struct = Grasshopper.Kernel.Data.GH_Structure[Grasshopper.Kernel.Types.GH_String]()

        for path in Data.Paths:
            for i, item in enumerate(Data.Branch(path)):
                gh_str = Grasshopper.Kernel.Types.GH_String(item)
                gh_struct.Append(gh_str, path)

        write_usertext_retvals = run_comp(Write_Usertext, go = True, Geom = Geom, Data = gh_struct, output_key_str='{name}')

        # read_usertext_retvals = run_comp(Read_Usertext, go = True, compute_vals = False, Geom = Geom)

        # for path in Data.Paths:
        #     for i, item in enumerate(Data.Branch(path)):
        #         gh_str = Grasshopper.Kernel.Types.GH_String(item)
        #         gh_struct.Append(gh_str, path)

        # write_usertext_retvals = run_comp(Write_Usertext, go = True, Geom = Geom, Data = gh_struct) #, output_key_str='{name}')

        #    return

        #    Data_Read = next(param
        #                     for param in Read_Usertext.Params.Output
        #                     if param.NickName == 'Data'
        #                    )
        #                    
        #    print('Badoom')
        #    print(dir(Data_Read))
        
        read_usertext_retvals = run_comp(Read_Usertext, go = True, compute_vals = False, Geom = Geom)
        
        # Data_Read = next(param
        #             for param in Read_Usertext.Params.Output
        #             if param.NickName == 'Data'
        #             )

        # Data_read_from_geom = Grasshopper.DataTree[object]()
        # for path in Data_Read.VolatileData.Paths:
        #     branch = Data_Read.VolatileData.Branch[path]
        #     for item in branch:
        #         Data_read_from_geom.Add(item, path)

        Data_read_from_geom = read_usertext_retvals['Data']

        Actual_Data_list = th.tree_to_list(Data_read_from_geom, retrieve_base = None)


        for j, ((k_exp, v_exp), (k_act, v_act)) in enumerate(zip(zip(*Data_list), zip(*Actual_Data_list)), start=1):

            for expected, actual, name in ((k_exp, k_act, 'Keys')
                                        ,(v_exp, v_act, 'Vals')):


                    # Make sure tests are not trivial
                msg_exp = '%s , test %s), expected: \n%s\n' % (name, j, expected)
                msg_act = '%s, test %s), actual: \n%s\n' % (name, j, actual)

                if self is not None:
                    self.assertTrue(expected, msg_exp)
                    self.assertTrue(actual, msg_act)
                else:
                    assert expected, msg_exp
                    assert actual, msg_act

                actual = set((str(gh_string) for gh_string in actual))
                in_exp_not_act = set(expected) - set(actual)
                in_act_not_exp = set(actual) - set(expected)
                msg = ('%s test number: %s. \n Exp - Actual: %s\n Actual - Exp: %s\n' 
                    % (name, j, in_exp_not_act, in_act_not_exp)
                    )


                if self is not None:

                    self.assertFalse(bool(in_exp_not_act), msg = msg)
                    self.assertFalse(bool(in_act_not_exp), msg = msg)
                else:
                    print(msg)
    return roundtrip_UserText

roundtrip_UserText = factory()

# import unittest
# from ..fuzzers import OBJECT_GENERATORS

# def make_unit_test_TestCase_instance_different_geom_generator(
#     factory,
#     ):

#     def API_unittest_TestCase_instances():

#         class APITestCase(unittest.TestCase):
#             pass

#         for i, obj_gen in enumerate(OBJECT_GENERATORS):
#             method_name = 'test_%s_%s' % ('roundtrip_UserText', i)
#             print('Adding test method: %s' % method_name)
#             setattr(APITestCase
#                 ,method_name
#                 ,factory([obj_gen])
#                 )

#             yield APITestCase(method_name)

#     return API_unittest_TestCase_instances


# test_case_generator = make_unit_test_TestCase_instance_different_geom_generator(
#                             factory,
#                             )
test_case_generator = make_unit_test_TestCase_instance_generator(
                            method = roundtrip_UserText,
                            )
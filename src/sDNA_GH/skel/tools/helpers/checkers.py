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
__version__ = '3.0.2'


import os
import logging
from collections import OrderedDict
import System  #.Net from IronPython

import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

from ...basic.ghdoc import ghdoc
from . import rhino_gh_geom

try:
    basestring #type: ignore
except NameError:
    basestring = str

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class NullPathError(Exception):
    pass


def get_path(fallback = None, inst = None):
    #type(dict, type[any]) -> str
    #refers to `magic' global ghdoc so needs to 
    # be in module scope (imported above)
    
    path_getters = [lambda : Rhino.RhinoDoc.ActiveDoc.Path
                   ,lambda : ghdoc.Path
                   ,lambda : inst.ghdoc.Path  #e.g. via old Component decorator
                   ,lambda : sc.doc.Path
                   ,lambda : fallback
                   ]
    path = None
    for path_getter in path_getters:
        try:
            path = path_getter()
        except AttributeError:
            continue
        if isinstance(path, basestring) and (os.path.isfile(path) or os.path.isdir(path)):
            return path 
    return None 


def get_obj_keys(obj):
    # type(str) -> list
    return rs.GetUserText(obj)


def get_obj_val(obj, key):
    # type(str, str) -> str
    return rs.GetUserText(obj, key)








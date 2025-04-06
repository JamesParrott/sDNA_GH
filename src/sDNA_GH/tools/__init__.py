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
__version__ = '3.0.4'


# Import classes etc. from sub modules, to allow the existing imports 
# (for old_tools.py) to be reused unchanged.
from .sdna import (update_opts
                  ,sDNA_ToolWrapper
                  ,sDNA_key
                  ,build_sDNA_GH_components
                  ,build_missing_sDNA_components
                  ,import_sDNA
                  ,list_of_param_infos
                  ,package_path
                  ,sDNA_GH_Tool
                  )
from .config import ConfigManager

from .support.Read_Geom import RhinoObjectsReader
from .support.Read_Usertext import UsertextReader
from .support.Write_Shp import ShapefileWriter
from .support.Read_Shp import ShapefileReader
from .support.Write_Usertext import UsertextWriter
from .support.Parse_Data import DataParser
from .support.Recolour_Objects import ObjectsRecolourer
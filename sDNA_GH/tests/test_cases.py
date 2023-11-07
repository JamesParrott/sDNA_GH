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


import sys
from random import random as random_num
from math import floor

try:
    xrange #type: ignore
except NameError:
    range = xrange #type: ignore

def create_random_grid_network(go, x, y, p):
    import rhinoscriptsyntax as rs



    def grid_point_coords(n, m):
        for y in range(n):
            for x in range(m):
                yield x, y

    def make_poly_line(x1, y1, x2, y2, store, offset = [x, y]):
        if random_num() > p:
            x1 += offset[0]; x2 += offset[0]
            y1 += offset[1]; y2 += offset[1]
            store += [rs.AddLine([x1, y1, 0], [x2, y2, 0])]

    if go is True:  
        M, N = map(floor,[M, N])
        geometries = []
        for col,row in grid_point_coords(N, M):
                if col < M-1:
                    make_poly_line(col, row, col+1, row, geometries)
                if row < N-1:
                    make_poly_line(col, row, col, row+1, geometries)
        a1 = geometries                

#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

from random import random as random_num
from math import trunc as floor  # for an int, not a float.  math.floor(2.33) == 2.0;  math.trunc(2.33) == 2

import shapefile

N, M = 50, 40
x, y = 0, 0
p = 0.2
go = True

def grid_point_coords(n,m):
    for i in range(n):
        for j in range(m):
            yield j,i

def make_poly_line(x1,y1,x2,y2,store,func,offset=[x,y]):
    if random_num() > p:
        x1 += offset[0]; x2 += offset[0];
        y1 += offset[1]; y2 += offset[1];
        new_poly_line = [[x1,y1,0], [x2,y2,0]]
        store += [new_poly_line]
        func(new_poly_line)

if go is True:  
    M,N=map( floor,  [M, N] )
    geometries = []
    with shapefile.Writer('test_random_grid.shp', shapeType = shapefile.POLYLINEZ) as w:
        w.field('Name.  ','C')
        def write_poly_line_to_w(poly_line):
            w.linez([poly_line])
            w.record('From ' + ', to '.join(map(str,poly_line)))
        for col,row in grid_point_coords(N,M):
                if col < M-1:
                    make_poly_line(col,row,col+1,row,geometries,write_poly_line_to_w)
                if row < N-1:
                    make_poly_line(col,row,col,row+1,geometries,write_poly_line_to_w)

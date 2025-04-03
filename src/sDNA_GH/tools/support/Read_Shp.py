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


""" Tool classes for sDNA_GH 

    Except Dev tools.  They're in dev_tools.py  
"""

__authors__ = {'James Parrott', 'Crispin Cooper'}
__version__ = '3.0.1'

import os
import sys
import abc
import logging
import functools
import subprocess
import re
import string
import warnings
import collections
from time import asctime
from numbers import Number
import locale
import math
import shutil

import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import GhPython
import System
import System.Drawing #.Net / C# Class
            #System is also available in IronPython, but System.Drawing isn't
import Grasshopper
from Grasshopper.GUI.Gradient import GH_Gradient
from Grasshopper.Kernel.Parameters import (Param_Arc
                                          ,Param_Colour  
                                          ,Param_Curve
                                          ,Param_Boolean
                                          ,Param_Geometry
                                          ,Param_String
                                          ,Param_FilePath
                                          ,Param_Guid
                                          ,Param_Integer
                                          ,Param_Line
                                          ,Param_Rectangle
                                          ,Param_Number
                                          ,Param_ScriptVariable
                                          ,Param_GenericObject
                                          )

from ... import data_cruncher 
from ...skel.basic.ghdoc import ghdoc
from ...skel.tools.helpers import checkers
from ...skel.tools.helpers import funcs
from ...skel.tools.helpers import rhino_gh_geom
from ...skel.tools import runner                                       
from ...skel import add_params
from ...skel import builder
from ... import options_manager
from ... import pyshp_wrapper
from ... import logging_wrapper
from ... import gdm_from_GH_Datatree
from ... import launcher
from ..sdna import sDNA_GH_Tool


itertools = funcs.itertools #contains pairwise recipe if Python < 3.10
                            #and zip_longest if Python > 2


if hasattr(abc, 'ABC'):
    ABC = abc.ABC
else:
    class ABC(object):
        __metaclass__ = abc.ABCMeta
abstractmethod = abc.abstractmethod

try:
    basestring #type: ignore
except NameError:
    basestring = str

OrderedDict, Counter = collections.OrderedDict, collections.Counter
if hasattr(collections, 'Iterable'):
    Iterable = collections.Iterable 
else:
    import collections.abc
    Iterable = collections.abc.Iterable

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
ClassLogger = logging_wrapper.class_logger_factory(logger = logger
                                                  ,module_name = __name__
                                                  )


class ShapefileReaderAddShapeError(Exception):
    pass




class ShapefileReader(sDNA_GH_Tool):

    class Options(pyshp_wrapper.ShapeRecordsOptions):
        new_geom = False
        bake = False
        uuid_field = 'Rhino3D_'
        sDNA_names_fmt = '{name}.shp.names.csv'
        prepped_fmt = '{name}_prepped'
        output_fmt = '{name}_output'
        ensure_3D = True
        ignore_invalid = False
                        
    component_inputs = ('file', 'Geom', 'bake', 'ignore_invalid') 
                                                # existing 'Geom', otherwise new 
                                                # objects need to be created

    def __call__(self, f_name, gdm, opts = None):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts
        options = opts['options']

        self.debug('Creating Class Logger.  Checking shapefile... ')

        if not os.path.isfile(f_name):
            msg = "'File': %s  is not a valid file. " % f_name
            self.logger.error(msg)
            raise ValueError(msg)


        self.logger.debug('Reading shapefile meta data... ')
        shp_fields, bbox, shape_type, num_entries = pyshp_wrapper.shp_meta_data(
                                                                         f_name
                                                                        ,options
                                                                        )

        self.logger.debug('bbox == %s' % bbox)

        invalid = []
        objs_maker = rhino_gh_geom.obj_maker_for_shape_type(shape_type)
        invalid_obj_handler = rhino_gh_geom.Rhino_obj_adder_invalid_handlers.get(
                                                                        shape_type
                                                                       ,None
                                                                       )

        if num_entries == 0:
            self.logger.warning('No entries in Shapefile: %s ' % f_name)
            return 1, f_name, gdm, None    


        if not bbox:
            self.logger.warning('No Bounding Box in Shapefile: %s '
                               % f_name
                               +'Supply bbox manually or create '
                               +'rectangle to plot legend.'
                               )

        
        fields = [ x[0] for x in shp_fields ]

        self.logger.debug('options.uuid_field in fields == ' 
                         +str(options.uuid_field in fields)
                         )
        self.logger.debug(fields) 

        if hasattr(options, 'field') and options.field not in fields:
            msg = 'field: %s not found in shape file fields: %s \n\n' 
            msg %= (options.field, fields)
            msg += 'Before using Parse_Data or Recolour_Objects on Data, '
            msg += 'set field to one of the shape file fields. '
            
            self.logger.warning(msg)
            warnings.warn(msg)


   
        def get_prefix(field):

            # Return prefix if field has metric (A, E, H or C) appended, as well as radius
            for prefix in ('Bt', 'Div', 'MGL', 'NQPD', 'SGL', 'TPBt', 'TPD'):
                if field.startswith(prefix):
                    return prefix

            # Strip off default value for radii ('n') unless field never has radius appended
            # to it, but also ends in n.
            if field not in ('LSin', 'LConn', 'Conn', 'LLen', 'Len') and field.endswith('n'):
                return field[:-1]            
            
            # Strip off any trailing digits and decimal point
            return re.split(r'\d+(\.\d+)?$', fld)[0]


        field_prefixes = [get_prefix(fld) for fld in fields]



        self.logger.debug('Testing existing geom data map.... ')

        if (isinstance(gdm, Iterable) and len(gdm) == 1 and 
            isinstance(gdm[0], gdm_from_GH_Datatree.GeomDataMapping)):
                #
                gdm = gdm[0]

        if isinstance(gdm, gdm_from_GH_Datatree.GeomDataMapping):

            self.logger.debug('gdm == %s, ..., %s ' % (gdm.items()[:2], gdm.items()[-2:]))

            existing_geom_compatible = len(gdm) == num_entries
        else:
            existing_geom_compatible = False
            msg = 'Shape file is incompatible with existing gdm: %s' % str(gdm)[:50]
            logger.debug(msg)


        if options.new_geom or not existing_geom_compatible: 
            #shapes_to_output = ([shp.points] for shp in shapes )
            
            #e.g. rs.AddPolyline for shp_type = 'POLYLINEZ'

            if options.ensure_3D:
                objs_maker = funcs.compose(objs_maker, funcs.ensure_3D)

            if options.bake:
                objs_maker = funcs.compose(str, objs_maker)

            self.shape_num = 0

            def get_points(obj, *args):
                return funcs.list_of_lists(obj)

            def add_geom(points, obj, *args):
                self.shape_num += 1
                return (objs_maker(points),) + args

            def add_geom_from_obj(obj, *args):
                points = get_points(obj, *args)
                return add_geom(points, obj, *args)

            error_msg = ('The error: {{ %s }}  occurred '
                        +'when adding shape number: %s.'
                        )

            def added_geom_generator(group):
                for x in group:
                          # obj, *data = x 
                    points = get_points(*x)
                    try:
                        yield add_geom(points, *x)
                    except Exception as e:
                        # The error of interest inside rhinoscriptsyntax.AddPolyline comes from:
                        #
                        # if rc==System.Guid.Empty: raise Exception("Unable to add polyline to document")
                        # https://github.com/mcneel/rhinoscriptsyntax/blob/c49bd0bf24c2513bdcb84d1bf307144489600fd9/Scripts/rhinoscript/curve.py#L563


                        if invalid_obj_handler:
                            why_invalid = invalid_obj_handler(points, self.shape_num, e)
                        else:
                            why_invalid =  error_msg % (e, self.shape_num)

                        invalid.append(why_invalid)




            def gdm_of_new_geom_from_group(group):
                return gdm_from_GH_Datatree.GeomDataMapping(
                                                added_geom_generator(group))



            gdm_iterator = (gdm_of_new_geom_from_group(group) 
                            for group in pyshp_wrapper
                                          .TmpFileDeletingShapeRecordsIterator(
                                                                 reader = f_name
                                                                ,opts = opts
                                                                )
                            )

            gdm_partial = functools.partial(list, gdm_iterator)
                    
            # gdm = gdm_from_GH_Datatree.make_list_of_gdms(generator())
            #self.logger.debug('shapes == %s' % shapes)
            self.logger.debug('objs_maker == %s' % objs_maker)
        else:
            #elif isinstance(gdm, dict) and len(gdm) == len(recs):
            # an override for different number of overridden geom objects
            # to shapes/recs opens a large a can of worms.  Unsupported.

            self.logger.warning('Geom data map matches shapefile. Using existing Geom. ')

            gdm_iterator = itertools.zip_longest( # instead of izip to raise 
                                                  # StopIteration in
                                                  # TmpFileDeletingRecordsIterator
                     gdm.keys()
                    ,pyshp_wrapper.TmpFileDeletingRecordsIterator(reader = f_name
                                                                 ,opts = opts
                                                                 )
                    )
            
            gdm_partial = functools.partial(gdm_from_GH_Datatree.GeomDataMapping
                                           ,gdm_iterator
                                           )
            #                  dict.keys() is a dict view in Python 3


        # shp_file_gen_exp  = itertools.izip(shapes_to_output
        #                                   ,(rec.as_dict() for rec in recs)
        #                                   )

        if options.bake:
            sc.doc = Rhino.RhinoDoc.ActiveDoc
        gdm = gdm_partial()
        # Exhausts the above generator into a list
        sc.doc = ghdoc 
        
        if invalid:
            invalid = '\n %s \n\n' % invalid
            if options.ignore_invalid:
                logger.warning(invalid)
            else:
                logger.error(invalid)
                raise ShapefileReaderAddShapeError(invalid)

        self.logger.debug('gdm defined.  sc.doc == ghdoc.  ')

        file_name = os.path.splitext(f_name)[0]
        csv_f_name = options.sDNA_names_fmt.format(name = file_name)
        self.logger.debug('Looking for csv_f_name == %s ' % csv_f_name)

        #sDNA_fields = {}
        if os.path.isfile(csv_f_name):
# sDNA writes this file in simple 'w' mode, 
# Line 469
# https://github.com/fiftysevendegreesofrad/sdna_open/blob/master/arcscripts/sdna_environment.py
            with open(csv_f_name, 'r') as f:   # In Python 2 there's no encoding argument
                #https://docs.python.org/2.7/library/functions.html#open
                #
                #sDNA_fields = [OrderedDict( line.split(',') for line in f )]
                abbrevs = [line.split(',')[0] for line in f ]

        else:
            msg = "No sDNA names.csv abbreviations file: %s found. " % csv_f_name
            abbrevs = [msg]
            self.logger.info(msg)



        retcode = 0

        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)


    retvals = 'retcode', 'gdm', 'abbrevs', 'fields', 'field_prefixes', 'bbox', 'invalid'
    component_outputs = ('Geom', 'Data') + retvals[2:]

    param_infos = sDNA_GH_Tool.param_infos + (
            ('bake', add_params.ParamInfo(
                           param_Class = Param_Boolean
                          ,Description = ('If new shapes are created, then'
                                         +'true: bakes '
                                         +'the shapefile polylines to Rhino.  '
                                         +'false: creates Grasshopper '
                                         +'polylines only. '
                                         +'Default: %(bake)s'
                                         )
                          ))
            ,('new_geom', add_params.ParamInfo(
                           param_Class = Param_Boolean
                          ,Description = ('True: Always create new shapes. '
                                         +'False: Create new shapes only if '
                                         +'the number of supplied shapes does '
                                         +'not match the number of data '
                                         +'records in the shape file. '
                                         +'Default: %(new_geom)s'
                                         )
                          ))
            ,('abbrevs', add_params.ParamInfo(
                           param_Class = Param_String
                          ,Description = ('Abbreviations of sDNA results from '
                                         +'the ...names.csv file. '
                                         )
                          ))
            ,('fields', add_params.ParamInfo(
                             param_Class = Param_String
                            ,Description = ('Field names from the Shapefile. '
                                           +'Set field to one of these values '
                                           +'to parse and/or plot it. '
                                           )
                            ))
            ,('field_prefixes', add_params.ParamInfo(
                             param_Class = Param_String
                            ,Description = ('sDNA_prefixes of field names from the Shapefile. '
                                           +'Set field_prefix to one of these values '
                                           +'to search for a field to parse and/or plot. \n'
                                           +'WARNING!:  May lead to meaningless comparisons '
                                           +'(changing the measure "moves the goal posts"). '
                                           )
                            ))
            ,('bbox', add_params.ParamInfo(
                         param_Class = Param_ScriptVariable
                        ,Description = ('Bounding box from the Shapefile. '
                                       +'Used to calculate leg_frame by '
                                       +'the Recolour_objects component. '
                                       +'[x_min, y_min, x_max, y_max]. All '
                                       +'Numbers.'
                                       ) 
                        ))
            ,('ignore_invalid', add_params.ParamInfo(
                     param_Class = Param_Boolean
                    ,Description = ('True: suppress errors from failing '
                                   +'to add shapes to Rhino/GH document.  '
                                   +'False: skip shapes that could not be '
                                   +'added to the document. '
                                   +'Default: %(ignore_invalid)s  '
                                   +'If True, the reasons why those shapes are '
                                   +'incompatible with Rhino '
                                   +'are viewable in *invalid*, but they are also logged '
                                   +' as warnings (or errors if False) to *out* and any *log_file* '
                                   +'Five validity criteria are defined here:'
                                   +rhino_gh_geom.InvalidPolyline.rhino_url
                                   )
                    ))
            ,('invalid', add_params.ParamInfo(
                             param_Class = Param_String
                            ,Description = ('Duplicates specific console output in out. '
                                           +'Details why particular shapes (if any) in the shapefile '
                                           +'could not be added to a document in Rhino, raising errors.  '
                                           +'ignore_invalid (currently: %(ignore_invalid)s) must be True '
                                           +'to read invalid, to suppress those same errors '
                                           +'(errors stop this and all output Params '
                                           +'from receiving data). '
                                           )
                            ))       
            )
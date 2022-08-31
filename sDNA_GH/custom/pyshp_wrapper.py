#! /usr/bin/python
# -*- coding: utf-8 -*-

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
__version__ = '0.11'
""" Reads .shp files, and parses data and writes .shp files from any iterable.   
"""

import os
import re
import logging
import locale
from collections import OrderedDict
from datetime import date
import re
import collections
if hasattr(collections, 'Iterable'):
    Iterable = collections.Iterable 
else:
    import collections.abc
    Iterable = collections.abc.Iterable



from ..third_party.PyShp import shapefile as shp  

try:
    basestring #type: ignore
except NameError:
    basestring = str              

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


file_name_no_ext = os.path.splitext(os.path.basename(__file__))[0]







SHP_FIELD_CODES = {int: 'N'
                  ,float: 'F'
                  ,bool: 'L'
                  ,str: 'C'
                  ,date: 'D'
                  }
                

# We omit 'M' for Memo 
# int = 'N'  here.  In PyShp, 'N' can also be a float 

pyshp_writer_method = dict(NULL = 'null'
                          ,POINT = 'point'
                          ,MULTIPATCH = 'multipatch'
                          ,POLYLINE = 'line'
                          ,POLYGON = 'poly'
                          ,MULTIPOINT = 'multipoint'
                          ,POINTZ = 'pointz'
                          ,POLYLINEZ = 'linez'
                          ,POLYGONZ = 'polyz'
                          ,MULTIPOINTZ = 'multipointz'
                          ,POINTM = 'pointm'
                          ,POLYLINEM = 'linem'
                          ,POLYGONM = 'polym'
                          ,MULTIPOINTM = 'multipointm'
                          )    # should be the same as val names in shp.shapefile.SHAPETYPE_LOOKUP.values()


if hasattr(shp, 'SHAPETYPE_LOOKUP'): 
# SHAPETYPE_LOOKUP not in older versions of shapefile.py 
# (especially 1.2.12 from Hiteca's GHshp)
    shp_vals = set(shp.SHAPETYPE_LOOKUP.values())
    pyshp_wrapper_shapes = set(pyshp_writer_method.keys())
    if shp_vals > pyshp_wrapper_shapes:
        msg = 'pyshp supports shape(s) '
        msg += str(shp_vals - pyshp_wrapper_shapes) 
        msg += ' not supported by pyshp_wrapper'
        logger.warning(msg)
    elif shp_vals < pyshp_wrapper_shapes:
        msg = 'pyshp_wrapper supports shape(s) '
        msg += str(shp_vals - pyshp_wrapper_shapes) 
        msg += ' not supported by pyshp'
        logger.warning(msg)


class CoerceAndGetCodeOptions(object):
    decimal = True
    precision = 12
    max_dp = 4 # decimal places
    yyyy_mm_dd = False
    keep_floats = True
    use_memo = False # Use the 'M' field code in Shapefiles for un-coerced data


def coerce_and_get_code(x, options = CoerceAndGetCodeOptions):
    #type coercer function

    if options.decimal:
        import decimal as dec
    dec.getcontext().prec = options.precision #if else options.precision    # significant figures,  >= # decimal places
    if      x in [True, False] or (hasattr(x, 'lower')
        and x.lower() in ['true','false']):   # if isinstance(x,bool):.  Don't test coercion with bool() first or everything truthy will be 'L'
        return x, SHP_FIELD_CODES[bool]   # i.e. 'L'
    try:
        y = int(x)   # if isinstance(x,int):  # Bool test needs to come before this as int(True) == 1
        return y, SHP_FIELD_CODES[int]    # i.e.   'N'
    except ValueError:
        try:
            n = options.max_dp
            if options.decimal:
                y = dec.Decimal(x)
                y = y.quantize(  dec.Decimal('.'*int( bool(n) ) + '0'*(n-1) + '1')  )   # e.g. '1' if n=0, else '0.000... (#n 0s) ...0001'
            else:
                y = float(x)   
                
                # float('12345' ) == 12345.0 so int test needs to come 
                # before this if 'N' and 'F' are utilised differently
                
                y = round(y, n)  
                #  Beware:  
                # https://docs.python.org/2.7/tutorial/floatingpoint.html#tut-fp-issues                                                      
                
            return x if options.keep_floats else y, SHP_FIELD_CODES[float]  
                    # Tuple , binds to result of ternary operator
        except (dec.InvalidOperation, ValueError):
            if isinstance(x, date):
                return x, SHP_FIELD_CODES[date]   # i.e. 'D'   

            if isinstance(x, list) and len(x) == 3 and all(isinstance(z, int) for z in x):
                x = ':'.join(map(str, x))
    
            if isinstance(x, basestring):
                year=r'([0-3]?\d{3})|\d{2}'
                month=r'([0]?\d)|(1[0-2])'
                day=r'([0-2]?\d)|(3[01])'
                sep=r'([-.,:/ \\])' # allows different seps r'(?P<sep>[-.,:\\/ ])'
                test_patterns =  [ year + sep + month + sep + day ]   # datetime.date requires yyyy, mm, dd
                if not options.yyyy_mm_dd:
                    test_patterns += [  day + sep + month + sep + year   # https://en.wikipedia.org/wiki/Date_format_by_country
                                       ,month + sep + day + sep + year]  # 
                if any(re.match(pattern, x) for pattern in test_patterns):
                    return x, SHP_FIELD_CODES[date]                # TODO, optionally, return datetime.date() object?
                else:
                    return x, SHP_FIELD_CODES[str]  # i.e. 'C'  
            else:
                msg = 'Failed to coerce UserText to PyShp record data type.  '
                if options.use_memo:
                    logger.warning(msg + 'Using Memo.  ')
                    return str(x), 'M'
                else:
                    logger.error(msg)
                    raise TypeError(msg)


class LocaleOptions(object):
    locale = ''  # '' => User's own settings.  



def dec_places_req(x, options = LocaleOptions):
    #type(Number, type[any]) -> int
    locale.setlocale(locale.LC_ALL,  options.locale)
    radix_char = locale.localeconv()['decimal_point']
    fractional_part = str(x).rpartition(radix_char)[2]
    return len(fractional_part)


class GetFileNameOptions(object):
    overwrite_shp = True
    max_new_files = 20
    suppress_warning = True     
    duplicate_suffix ='_({number})'

def get_filename(f, options = GetFileNameOptions):
    #type: (str, type[any]) -> str

    i = 1
    prev_f = f
    file_dir, full_file_name = os.path.split(f)   
    [file_name, file_extension] = os.path.splitext(full_file_name) 
    while os.path.isfile(f) and i <= options.max_new_files:
        prev_f = f
        f = os.path.join(file_dir
                        ,(file_name
                         +options.duplicate_suffix.format(number = str(i))
                         +file_extension
                         )
                        ) 
        i += 1
    if not options.overwrite_shp:
        if options.max_new_files < i:
            # If the while loop never found an f that is not a file
            logger.warning('max_new_files == %s exceeded, Overwriting file: %s' 
                          %(options.max_new_files, f)
                          )
        return f
    elif not options.suppress_warning:
        logger.warning('Overwriting file: %s ! ' % prev_f)
    return prev_f


class EnsureCorrectOptions(object):
    # ensure_correct & write_iterable_to_shp
    extra_chars = 2


def ensure_correct(fields
                  ,nice_key
                  ,value
                  ,val_type
                  ,attribute_tables
                  ,options = EnsureCorrectOptions
                  ): 
    # type(dict, str, type[any], str, dict namedtuple) -> None
    if nice_key in fields:
        fields[nice_key]['size'] = max(fields[nice_key]['size']
                                      ,len(str(value)) + max(0, options.extra_chars)
                                      )
        if (val_type == SHP_FIELD_CODES[float] 
            and 'decimal' in fields[nice_key] ):
            fields[nice_key]['decimal'] = max(fields[nice_key]['decimal']
                                             ,dec_places_req(value) 
                                             )
        if val_type != fields[nice_key]['fieldType']:
            if (value in [0,1] #Python list. Discrete. Not math closed interval
                and fields[nice_key]['fieldType'] == SHP_FIELD_CODES[bool] 
                or (val_type == SHP_FIELD_CODES[bool] 
                    and fields[nice_key]['fieldType'] == SHP_FIELD_CODES[int] 
                    and all( attribute_tables[i][nice_key] in [0,1] 
                             for i in attribute_tables
                           )
                   )
               ):
                pass   #1s and 0s are in a Boolean field as integers or a 1 or a 0 
                       # in a Boolean field is type checking as an integer
                # TODO:  Check options and rectify - flag as Bool for now 
                #        (rest of loop will recheck others), 
                #        or flag for recheck all at end
            elif (val_type == SHP_FIELD_CODES[float] 
                  and fields[nice_key]['fieldType'] == SHP_FIELD_CODES[int]):
                fields[nice_key]['fieldType'] = SHP_FIELD_CODES[float]
                fields[nice_key]['decimal'] = dec_places_req(value)
            else:
                fields[nice_key]['fieldType'] = SHP_FIELD_CODES[str]
                #logger.error('Type mismatch in same field.  Cannot store ' 
                #            +str(value) + ' as .shp record type ' 
                #            + fields[nice_key]['fieldType']
                #            )
    else:
        fields[nice_key] = dict( size = (len(str(value)) 
                                        +max(0,options.extra_chars)
                                        )
                               ,fieldType = val_type
                               )                    
        # could add a 'name' field, to save looping over the keys to this
        # dict:
        # fields[nice_key][name] = nice_key
        #  and then just unpack a fields dict for each one:
        # shapefile.Writer.field(**fields[nice_key]).  
        # But it seems to be
        # an undocumented feature of Writer.fields, doesn't reduce the amount
        #  of code (actually needs an extra line), requires duplicate data 
        # in fields.  If we wanted to rename it in the shape file to
        # something different than the dictionary key then this is a neat way 
        # of doing so.
        if val_type == SHP_FIELD_CODES[float]:
            fields[nice_key]['decimal'] = dec_places_req(value)    
    # Mutates fields.  Nothing returned.


class WriteIterableToShpOptions(object):
    field_size = 30
    cache_iterable= False
    uuid_field = 'Rhino3D_' # 'object_identifier_UUID_'     
    uuid_length = 36 # 32 in 5 blocks (2 x 6 & 2 x 5) with 4 separator characters.
    num_dp = 10 # decimal places
    min_sizes = True
    encoding = 'utf-8' # also used by get_fields_recs_and_shapes


def write_iterable_to_shp(my_iterable 
                         ,shp_file_path
                         ,is_shape 
                         ,shape_mangler
                         ,shape_IDer # to make dict key
                         ,key_finder
                         ,key_matcher
                         ,value_demangler
                         ,shape_code # e.g. 'POLYLINEZ'
                         ,options = WriteIterableToShpOptions
                         ,field_names = None
                         ):
    #type(type[Iterable]
    #    ,str
    #    ,function
    #    ,function
    #    ,function
    #    ,function
    #    ,function
    #    ,function
    #    ,str
    #    ,namedtuple
    #    ,dict
    #    )  -> int, str, dict, list, list
    #
    is_iterable = isinstance(my_iterable, Iterable)
    is_str = isinstance(my_iterable, basestring)
    is_path_str = isinstance(shp_file_path, basestring)


    if ((not is_iterable) 
        or is_str 
        or not is_path_str
        or not os.path.isdir(os.path.dirname(shp_file_path))):
        #
        logger.error ('returning.  Not writing to .shp file')
        msg_1 = ' Is Iterable == %s' % is_iterable
        logger.info (msg_1)
        msg_2 = ' Is my_iterable str == %s' % is_str
        logger.info (msg_2)
        msg_3 = ' Is path str == %s' % is_path_str
        logger.info (msg_3)
        msg_4 = 'my_iterable == %s ' % my_iterable
        logger.info(msg_4)
        
        try:
            msg_5 = (' Is path path == %s ' 
                    % os.path.isdir( os.path.dirname(shp_file_path))
                    )
            logger.info (msg_5)
        except TypeError:
            msg_5 = 'Invalid path type == %s ' % shp_file_path
        logger.info ('Path == %s' %shp_file_path)
        msg = '\n'.join([msg_1, msg_1, msg_3, msg_4, msg_5])
        raise TypeError(msg)
        


    max_size = (options.field_size
            + options.extra_chars)

    fields = OrderedDict( {options.uuid_field 
                                : dict(fieldType = SHP_FIELD_CODES[str]
                                      ,size = (options.uuid_length
                                              +max(0, options.extra_chars)
                                              )
                                      )
                          }
                         )

    attribute_tables = OrderedDict()

    if field_names is None or options.cache_iterable: 
        
        for item in my_iterable:    
            keys = key_finder(item) # e.g. rhinoscriptsyntax.GetUserText(item,None)
            values = OrderedDict( {options.uuid_field : shape_IDer(item) } )   
            for key in keys:
                # Demangle and cache the user text keys and values
                nice_match = key_matcher(key)            
                if nice_match:
                    nice_key = nice_match.group('name')
                    #TODO: Support more fields, e.g. type, size
                    value = value_demangler(item, key) 

                    value, val_type = coerce_and_get_code(value, options)
                    values[nice_key] = value 


                    # Update the shp field sizes if they aren't big enough or the field is new, and type check
                    if options.min_sizes:
                        ensure_correct(fields, nice_key, value, val_type, attribute_tables, options)
                        # mutates fields, adding nice_key to it if not already there, else updating its val
                    else:
                        fields[nice_key] = dict(size = max_size
                                               ,fieldType = val_type
                                               ) 
                        if val_type == SHP_FIELD_CODES[float]:
                            fields[nice_key]['decimal'] = options.num_dp
            attribute_tables[item] = values.copy()  # item may not be hashable so can't use dict of dicts
    else:
        for name in field_names:
            fields[name] = dict(size = max_size
                               ,fieldType = SHP_FIELD_CODES[str]
                               )
        #TODO setup basic fields dict from list without looping over my_iterable        

    def default_record_dict(item):
        retval = { key_matcher(key).group('name') : 
                         str( value_demangler(item, key) )[:max_size] 
                            for key in key_finder(item) 
                            if (key_matcher(key) and
                                key_matcher(key).group('name') in fields
                               )
                 }
        retval[options.uuid_field ] = shape_IDer(item)
        return retval


    shapefile_path = get_filename(shp_file_path
                                 ,options
                                 )
       



    
    with shp.Writer(os.path.normpath( shapefile_path )
                   ,getattr(shp, shape_code)
                   ,encoding = options.encoding
                   ) as w:

        for key, val in fields.items():
            w.field(key, **val)
        #w.field('Name', 'C')

        logger.debug(str(fields))

        add_geometric_object = getattr( w,  pyshp_writer_method[shape_code] )
        # e.g. add_geometric_object = w.linez

        for shape, attribute_table in attribute_tables.items():
            if not is_shape(shape, shape_code):
                msg = 'Shape: %s cannot be converted to shape_code: %s' 
                msg %= (shape, shape_code)
                logger.error(msg)
                raise TypeError(msg)

            list_of_shapes = shape_mangler(shape)
            if list_of_shapes:

                add_geometric_object( list_of_shapes ) 
                #e.g. w.linez(list_of_shapes)  

                w.record( **attribute_table )    



    return 0, shapefile_path, fields, attribute_tables


class FieldRecsShapesOptions(object):
    encoding = 'utf-8'


def get_fields_recs_and_shapes(shapefile_path, options = FieldRecsShapesOptions):
    with shp.Reader(shapefile_path, encoding = options.encoding) as r:
        fields = r.fields[1:] # skip first field (deletion flag)
        recs = r.records()
        shapes = r.shapes()
        bbox = r.bbox
    #gdm = {shape : {k : v for k,v in zip(fields, rec)} 
    #               for shape, rec in zip(shapes, recs)  }
    
    return fields, recs, shapes, bbox






class ShpOptions(CoerceAndGetCodeOptions
                ,GetFileNameOptions
                ,EnsureCorrectOptions
                ,WriteIterableToShpOptions
                ,LocaleOptions
                ,FieldRecsShapesOptions
                ):
                shp_type = 'POLYLINEZ'

                 # e.g. 'fr', 'cn', 'pl'. IETF RFC1766,  ISO 3166 Alpha-2 code
    #
    # coerce_and_get_code

    #
    # get_filename

    #

    #
    # write_iterable_to_shp 


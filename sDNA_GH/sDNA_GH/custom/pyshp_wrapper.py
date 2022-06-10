#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'
# Convenience wrappers to read and write .shp files 
# from any iterable object and to any function


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


import rhinoscriptsyntax as rs

from ..third_party.PyShp import shapefile as shp  
                                  

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


file_name_no_ext = os.path.split(__file__)[-1].split('.')[0]   

class ShpOptions(object):
    shape_type = 'POLYLINEZ'
    locale = ''  # '' => User's own settings.  
                 # e.g. 'fr', 'cn', 'pl'. IETF RFC1766,  ISO 3166 Alpha-2 code
    #
    # coerce_and_get_code
    decimal = True
    precision = 12
    max_dp = 4 # decimal places
    yyyy_mm_dd = False
    keep_floats = True
    use_memo = False # Use the 'M' field code in Shapefiles for uncoerced data
    #
    # get_filename
    overwrite_shp = True
    max_new_files = 20
    suppress_warning = True     
    dupe_file_key_str ='{name}_({number})'
    #
    # ensure_correct & write_iterable_to_shp
    extra_chars = 2
    #
    # write_iterable_to_shp
    field_size = 30
    cache_iterable= False
    uuid_field = 'Rhino3D_' # 'object_identifier_UUID_'     
    uuid_length = 36 # 32 in 5 blocks (2 x 6 & 2 x 5) with 4 seperator characters.
    num_dp = 10 # decimal places
    min_sizes = True
    encoding = 'utf8' # also used by get_fields_recs_and_shapes


###################################################################



Rhino_obj_for_shape = dict(NULL = None
                          ,POINT = 'PointCoordinates'
                          ,MULTIPATCH = 'MeshVertices'  
                          # Unsupported.  Complicated. 
                          ,POLYLINE = 'PolylineVertices'  
                          # Works on Line too.
                          ,POLYGON = 'PolylineVertices'   
                          ,MULTIPOINT = 'PointCloudPoints'  
                          # Unsupported
                          # Needs chaining to list or POINT
                          ,POINTZ = 'PointCoordinates'
                          ,POLYLINEZ = 'PolylineVertices'
                          ,POLYGONZ = 'PolylineVertices'  
                          ,MULTIPOINTZ = 'PointCloudPoints'  
                          #see MULTIPOINT
                          ,POINTM = 'PointCoordinates'
                          ,POLYLINEM = 'PolylineVertices'
                          ,POLYGONM = 'PolylineVertices'    
                          ,MULTIPOINTM = 'PointCloudPoints'  
                          #see MULTIPOINT
                          )  

def get_points_from_obj(x, shp_type='POLYLINEZ'):
    #type(str, dict) -> list
    f = getattr(rs, Rhino_obj_for_shape[shp_type])
    return [list(y) for y in f(x)]

Rhino_obj_checkers_for_shape = dict(NULL = [None]
                                   ,POINT = ['IsPoint']
                                   ,MULTIPATCH = ['IsMesh']  # Unsupported  
                                   # (too complicated).
                                   ,POLYLINE = ['IsLine','IsPolyline']  
                                   #IsPolyline ==False for lines, 
                                   # on which PolylineVertices works fine
                                   ,POLYGON = ['IsPolyline'] 
                                   #2 pt Line not a Polygon.
                                   # Doesn't check closed
                                   ,MULTIPOINT = ['IsPoint']   
                                   # e.g. 
                                   # lambda l : any(IsPoint(x) for x in l)
                                   ,POINTZ = ['IsPoint']
                                   ,POLYLINEZ = ['IsLine','IsPolyline']
                                   ,POLYGONZ = ['IsPolyline']   
                                   #Doesn't check enclosed shape
                                   ,MULTIPOINTZ = ['IsPoints']  
                                   # see MULTIPOINT
                                   ,POINTM = ['IsPoint']
                                   ,POLYLINEM = ['IsLine','IsPolyline']
                                   ,POLYGONM = ['IsPolyline']   
                                   #Doesn't check enclosed shape
                                   ,MULTIPOINTM = ['IsPoints']  
                                   # see MULTIPOINT
                                   )  

def is_shape(obj, shp_type):   #e.g. polyline
    # type(str) -> bool

    allowers = Rhino_obj_checkers_for_shape[ shp_type]
    if isinstance(allowers, str):
        allowers = [allowers] 
    return any( getattr(rs, allower )( obj ) for allower in allowers)

Rhino_obj_code_for_shape = dict(NULL = None
                               ,POINT = 1         
                               # Untested.  
                               ,MULTIPATCH = 32    
                               # Unsupported.  Complicated.  
                               ,POLYLINE = 4
                               ,POLYGON = 4  
                               ,MULTIPOINT = 2     
                               # Untested.  
                               ,POINTZ = 1         
                               ,POLYLINEZ = 4
                               ,POLYGONZ = 4   
                               ,MULTIPOINTZ = 2 
                               ,POINTM = 1
                               ,POLYLINEM = 4
                               ,POLYGONM = 4  
                               ,MULTIPOINTM = 2
                               )  

def get_Rhino_objs(shp_type='POLYLINEZ'):
    #type (None) -> list
    return rs.ObjectsByType(geometry_type = Rhino_obj_code_for_shape[shp_type]
                           ,select = False
                           ,state = 0
                           )

Rhino_obj_adder_for_shape = dict(NULL = None
                                ,POINT = 'AddPoint'
                                ,MULTIPATCH = 'AddMesh'    
                                # Unsupported.  Complicated.
                                ,POLYLINE = 'AddPolyline'
                                ,POLYGON = 'AddPolyline'   
                                # check Pyshp closes them
                                ,MULTIPOINT = 'AddPoints'
                                ,POINTZ = 'AddPoint'
                                ,POLYLINEZ = 'AddPolyline'
                                ,POLYGONZ = 'AddPolyline'   
                                # check Pyshp closes them
                                ,MULTIPOINTZ = 'AddPoints'
                                ,POINTM = 'AddPoint'
                                ,POLYLINEM = 'AddPolyline'
                                ,POLYGONM = 'AddPolyline'    
                                # check Pyshp closes them
                                ,MULTIPOINTM = 'AddPoints'
                                )  


type_dict = {}
for x in (int, float, bool, str, date):
    type_dict[x] = x.__name__

shp_field_codes = dict(int = 'N'
                      ,str = 'C'
                      ,float = 'F'
                      ,date = 'D'
                      ,bool = 'L'
                      )   
# We omit 'M' for Memo 
# int = 'N'  here.  In PyShp, 'N' can also be a float
                
def get_field_code(x):
    # typelookup function
    return shp_field_codes[  type_dict[ type(x) ]  ]   

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



def coerce_and_get_code(x, options = ShpOptions):
    #typecoercer function

    if options.decimal:
        import decimal as dec
    dec.getcontext().prec = options.precision #if else options.precision    # significant figures,  >= # decimal places
    if      x in [True, False] or (hasattr(x, 'lower')
        and x.lower() in ['true','false']):   # if isinstance(x,bool):.  Don't test coercion with bool() first or everything truthy will be 'L'
        return x, shp_field_codes['bool']   # i.e. 'L'
    try:
        y = int(x)   # if isinstance(x,int):  # Bool test needs to come before this as int(True) == 1
        return y, shp_field_codes['int']    # i.e.   'N'
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
                
            return x if options.keep_floats else y, shp_field_codes['float']  
                    # Tuple , binds to result of ternary operator
        except ValueError:
            if isinstance(x, date):
                return x, shp_field_codes['date']   # i.e. 'D'   

            if isinstance(x, list) and len(x) == 3 and all(isinstance(z, int) for z in x):
                x = ':'.join(map(str, ))
    
            if isinstance(x, str):
                year=r'([0-3]?\d{3})|\d{2}'
                month=r'([0]?\d)|(1[0-2])'
                day=r'([0-2]?\d)|(3[01])'
                sep=r'([-.,:/ \\])' # allows different seps r'(?P<sep>[-.,:\\/ ])'
                test_patterns =  [ year + sep + month + sep + day ]   # datetime.date requires yyyy, mm, dd
                if not options.yyyy_mm_dd:
                    test_patterns += [  day + sep + month + sep + year   # https://en.wikipedia.org/wiki/Date_format_by_country
                                       ,month + sep + day + sep + year]  # 
                if any(re.match(pattern, x) for pattern in test_patterns):
                    return x, shp_field_codes['date']                # TODO, optionally, return datetime.date() object?
                else:
                    return x, shp_field_codes['str']  # i.e. 'C'  
            else:
                msg = 'Failed to coerce UserText to PyShp record data type.  '
                if options.use_memo:
                    logger.warning(msg + 'Using Memo.  ')
                    return str(x), 'M'
                else:
                    logger.error(msg)
                    raise TypeError(msg)

def dec_places_req(x, options = ShpOptions):
    #type(Number, type[any]) -> int
    locale.setlocale(locale.LC_ALL,  options.locale)
    radix_char = locale.localeconv()['decimal_point']
    fractional_part = str(x).rpartition(radix_char)[2]
    return len(fractional_part)

def get_filename(f, options = ShpOptions):
    #type: (str,dict) -> str

    if not options.overwrite_shp:
        i = 1
        file_dir, full_file_name = os.path.split(f)   
        [file_name, _, file_extension] = full_file_name.rpartition('.') 
        while os.path.isfile(f) and i <= options.max_new_files:
            f = os.path.join(file_dir
                            ,options.dupe_file_key_str.format(name = file_name 
                                                             ,number = str(i)
                                                             )
                            + '.' + file_extension
                            ) 
            i += 1
    elif not options.suppress_warning:
        logger.warning('Overwriting file %s ! ' % f)
    return f

def ensure_correct(fields
                  ,nice_key
                  ,value
                  ,val_type
                  ,attribute_tables
                  ,options = ShpOptions
                  ): 
    # type(dict, str, type[any], str, dict namedtuple) -> None
    if nice_key in fields:
        fields[nice_key]['size'] = max(fields[nice_key]['size']
                                      ,len(str(value)) + max(0, options.extra_chars)
                                      )
        if (val_type == shp_field_codes['float'] 
            and 'decimal' in fields[nice_key] ):
            fields[nice_key]['decimal'] = max(fields[nice_key]['decimal']
                                             ,dec_places_req(value) 
                                             )
        if val_type != fields[nice_key]['fieldType']:
            if (value in [0,1] #Python list. Discrete. Not math closed interval
                and fields[nice_key]['fieldType'] == shp_field_codes['bool'] 
                or (val_type == shp_field_codes['bool'] 
                    and fields[nice_key]['fieldType'] == shp_field_codes['int'] 
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
            elif (val_type == shp_field_codes['float'] 
                  and fields[nice_key]['fieldType'] == shp_field_codes['int']):
                fields[nice_key]['fieldType'] = shp_field_codes['float']
                fields[nice_key]['decimal'] = dec_places_req(value)
            else:
                fields[nice_key]['fieldType'] = shp_field_codes['str']
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
        if val_type == shp_field_codes['float']:
            fields[nice_key]['decimal'] = dec_places_req(value)    
    # Mutates fields.  Nothing returned.


def write_iterable_to_shp(my_iterable 
                         ,shp_file_path 
                         ,shape_mangler
                         ,shape_IDer # to make dict key
                         ,key_finder
                         ,key_matcher
                         ,value_demangler
                         ,shape_code # e.g. 'POLYLINEZ'
                         ,options = ShpOptions
                         ,field_names = None
                         ):
    #type(type[Iterable]
    #    ,str
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
    is_str = isinstance(my_iterable, str)
    is_path_str = isinstance(shp_file_path, str)


    if ( (not is_iterable) 
         or is_str 
         or not is_path_str
         or not os.path.isdir( os.path.dirname(shp_file_path) ) 
        ):
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
                                : dict(fieldType = shp_field_codes['str']
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
                    # TODO: use .group('fieldtype') and .group('size') if there
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
                        if val_type == shp_field_codes['float']:
                            fields[nice_key]['decimal'] = options.num_dp
            attribute_tables[item] = values.copy()  # item may not be hashable so can't use dict of dicts
    else:
        for name in field_names:
            fields[name] = dict(size = max_size
                               ,fieldType = shp_field_codes['str']
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
    # wrapper_pyshp can work outside of rhino and grasshopper, so we don't know the name of the Rhino .3dm file.
    # Instead we'll wrap this wrapper function again in the Rhino / GH process in sDNA_GH.py to supply this inner 
    # function it as a normal parameter value for shp_file_path.
        



    
    with shp.Writer(os.path.normpath( shapefile_path )
                   ,getattr(shp, shape_code)
                   ,encoding = options.encoding
                   ) as w:

        for key, val in fields.items():
            w.field(key, **val)
        #w.field('Name', 'C')

        logger.debug(str(fields))

        add_geometric_object = getattr( w,  pyshp_writer_method[shape_code] )
        for item, attribute_table in attribute_tables.items():
            list_of_shapes = shape_mangler(item)
            if list_of_shapes:

                add_geometric_object( list_of_shapes )   

                w.record( **attribute_table )    



    return 0, shapefile_path, fields, attribute_tables

def get_fields_recs_and_shapes(shapefile_path, options = ShpOptions):
    with shp.Reader(shapefile_path, encoding = options.encoding) as r:
        fields = r.fields[1:] # skip first field (deletion flag)
        recs = r.records()
        shapes = r.shapes()
        bbox = r.bbox
    #gdm = {shape : {k : v for k,v in zip(fields, rec)} 
    #               for shape, rec in zip(shapes, recs)  }
    
    return fields, recs, shapes, bbox

def add_objs_to_group(objs, group_name):
    #type(list, str) -> int
    return rs.AddObjectsToGroup(objs, group_name)  

def make_group(group_name = None):
    #type(str) -> str
    return rs.AddGroup(group_name)

def objs_maker_factory(
       shp_type = 'POLYLINEZ'
      ,make_new_group = make_group
      ,add_objects_to_group = add_objs_to_group
      ,Rhino_obj_adder_for_shape = Rhino_obj_adder_for_shape
      ):
    #type(namedtuple, function, function, dict) -> function
    rhino_obj_maker = getattr(rs, Rhino_obj_adder_for_shape[shp_type])
    # e.g. rhino_obj_maker = rs.AddPolyline

    def g(obj, rec):  # The shape from pyshp is a list of polylines, 
                      # even if there is only 1 polyline
        objs_list = [rhino_obj_maker(points_list) for points_list in obj] 
    # Creates not necessarily returned Rhino object as intentional side effect
        if len(objs_list) > 1:
            new_group_name = make_new_group()
            add_objects_to_group(objs_list, new_group_name)
            return new_group_name
        elif len(objs_list)==1:  #The normal case
            return objs_list[0]
        else: 
            return None
    return g




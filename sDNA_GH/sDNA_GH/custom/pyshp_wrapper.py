#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'
# Convenience wrappers to read and write .shp files 
# from any iterable object and to any function


import sys, os, logging
from collections import OrderedDict
from datetime import date
import re
if sys.version < '3.3':
    from collections import Iterable
else:
    from collections.abc import Iterable


import rhinoscriptsyntax as rs
import scriptcontext as sc

from .skel.tools.helpers.funcs import is_uuid
from .skel.tools.helpers.checkers import is_an_obj_in_GH_or_Rhino
                                  

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


file_name_no_ext = os.path.split(__file__)[-1].split('.')[0]             #os.path.split and string.split

if __name__=='__main__':
    sys.path += [os.path.join(sys.path[0], '..')]
    sys.path += [os.path.join(sys.path[0], r'..',r'third_party_python_modules')]
    import shapefile as shp  
else:
    from ..third_party.PyShp import shapefile as shp  



###################################################################



Rhino_obj_converter_Shp_file_shape_map = dict(NULL = None
                                             ,POINT = 'PointCoordinates'
                                             ,MULTIPATCH = 'MeshVertices'  # Unsupported.  Complicated.  TODO!  
                                             ,POLYLINE = 'PolylineVertices'  # Works on Line too, unlike the checker.
                                             ,POLYGON = 'PolylineVertices'   
                                             ,MULTIPOINT = 'PointCloudPoints'  # Unsupported.  Needs chaining to list or POINT
                                             ,POINTZ = 'PointCoordinates'
                                             ,POLYLINEZ = 'PolylineVertices'
                                             ,POLYGONZ = 'PolylineVertices'  
                                             ,MULTIPOINTZ = 'PointCloudPoints'  #see MULTIPOINT
                                             ,POINTM = 'PointCoordinates'
                                             ,POLYLINEM = 'PolylineVertices'
                                             ,POLYGONM = 'PolylineVertices'    
                                             ,MULTIPOINTM = 'PointCloudPoints'  #see MULTIPOINT
                                             )  

def get_points_list_from_geom_obj(x, shp_type='POLYLINEZ'):
    #type(str, dict) -> list
    f = getattr(rs, Rhino_obj_converter_Shp_file_shape_map[shp_type])
    return [list(y) for y in f(x)]

Rhino_obj_checker_Shp_file_shape_map = dict( 
     NULL = [None]
    ,POINT = ['IsPoint']
    ,MULTIPATCH = ['IsMesh']    # Unsupported.  Complicated.  TODO!
    ,POLYLINE = ['IsLine','IsPolyline']  #IsPolyline ==False for lines, 
#                                        # on which PolylineVertices works fine
    ,POLYGON = ['IsPolyline'] #2 pt Line not a Polygon.Doesn't check closed
    ,MULTIPOINT = ['IsPoint']   # Need to define lambda l : any(IsPoint(x) for x in l)
    ,POINTZ = ['IsPoint']
    ,POLYLINEZ = ['IsLine','IsPolyline']
    ,POLYGONZ = ['IsPolyline']   #Doesn't check closed
    ,MULTIPOINTZ = ['IsPoints']  # see MULTIPOINT
    ,POINTM = ['IsPoint']
    ,POLYLINEM = ['IsLine','IsPolyline']
    ,POLYGONM = ['IsPolyline']   #Doesn't check closed 
    ,MULTIPOINTM = ['IsPoints']  # see MULTIPOINT
                                            )  

def check_is_specified_obj_type(obj, shp_type):   #e.g. polyline
    # type(str) -> bool

    allowers = Rhino_obj_checker_Shp_file_shape_map[ shp_type]
    return any( getattr(rs, allower )( obj ) for allower in allowers)

Rhino_obj_getter_code_Shp_file_shape_map = dict(NULL = None
                                               ,POINT = 1          # Untested.  TODO
                                               ,MULTIPATCH = 32    # Unsupported.  Complicated.  TODO!
                                               ,POLYLINE = 4
                                               ,POLYGON = 4  
                                               ,MULTIPOINT = 2     # Untested.  TODO
                                               ,POINTZ = 1         
                                               ,POLYLINEZ = 4
                                               ,POLYGONZ = 4   
                                               ,MULTIPOINTZ = 2 
                                               ,POINTM = 1
                                               ,POLYLINEM = 4
                                               ,POLYGONM = 4  
                                               ,MULTIPOINTM = 2
                                               )  

def get_all_shp_type_Rhino_objects(shp_type='POLYLINEZ'):
    #type (None) -> list
    return rs.ObjectsByType(geometry_type = Rhino_obj_getter_code_Shp_file_shape_map[shp_type]
                           ,select = False
                           ,state = 0
                           )

Rhino_obj_adder_Shp_file_shape_map = dict(NULL = None
                                         ,POINT = 'AddPoint'
                                         ,MULTIPATCH = 'AddMesh'    # Unsupported.  Complicated.  TODO!
                                         ,POLYLINE = 'AddPolyline'
                                         ,POLYGON = 'AddPolyline'   # check Pyshp closes them
                                         ,MULTIPOINT = 'AddPoints'
                                         ,POINTZ = 'AddPoint'
                                         ,POLYLINEZ = 'AddPolyline'
                                         ,POLYGONZ = 'AddPolyline'   # check Pyshp closes them
                                         ,MULTIPOINTZ = 'AddPoints'
                                         ,POINTM = 'AddPoint'
                                         ,POLYLINEM = 'AddPolyline'
                                         ,POLYGONM = 'AddPolyline'    # check Pyshp closes them
                                         ,MULTIPOINTM = 'AddPoints'
                                         )  


type_dict = {}
for x in [int,float,bool,str,date]:
    type_dict[x] = x.__name__

shp_field_codes = dict(int = 'N',str = 'C', float = 'F', date = 'D', bool = 'L')   # We omit 'M' for Memo 
# int = 'N' is our choice here.  This is stricter than in PyShp, in which 'N' can also be a float
                
def look_up_shp_type(x):
    # typelookup function
    return shp_field_codes[  type_dict[ type(x) ]  ]   # Elegant :) .  But naive - beware e.g. look_up_shp_type('3.14159') == 'C' (str)

shaperback_writer = dict(NULL = 'null'
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



assert set(shp.SHAPETYPE_LOOKUP.values()) == set(shaperback_writer.keys())   
# SHAPETYPE_LOOKUP not in older versions of shapefile.py (especially 1.2.12 from Hiteca's GHshp)


def shp_type_coercer(x, options):
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
    except:
        try:
            n = options.max_dp
            if options.decimal:
                y = dec.Decimal(x)
                y = y.quantize(  dec.Decimal('.'*int( bool(n) ) + '0'*(n-1) + '1')  )   # e.g. '1' if n=0, else '0.000... (#n 0s) ...0001'
            else:
                y = float(x)   # if isinstance(x,float):  # float('12345' ) == 12345.0 so int test needs to come 
                                                          # before this if 'N' and 'F' are utilised differently
                y = round(y, n)  #  Beware:  https://docs.python.org/2.7/tutorial/floatingpoint.html#tut-fp-issues                                                      
                
            return x if options.keep_floats else y, shp_field_codes['float']  # Tuple binds to result of ternary operator,
                                                                                               # not just to y
        except:
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
                logger.error("Failed to coerce UserText to PyShp record data type.  ")
                if options.use_memo:
                    logger.info("Using Memo.  ")
                    return str(x), 'M'

def dec_places_req(x):
    return len(str(x).lstrip('0123456789').rstrip('0')) - 1

def get_unique_filename_if_not_overwrite(f, opts):
    #type: (str,dict) -> str

    if not opts.overwrite_shp:
        i = 1
        file_dir, full_file_name = os.path.split(f)   #os.path.split
        [file_name, _, file_extension] = full_file_name.rpartition('.')  #str.split
        while os.path.isfile(f) and i <= opts['options'].max_new_files:
            f = os.path.join(file_dir, file_name + opts.dupe_file_suffix.format(i) + '.' + file_extension) #os.path.join
            i += 1  # Not good practice to change the value of the input argument shp_file_path, but if it's a str it's immutable, so no side effects
                    # even if we give it a default value
    elif not opts.suppress_warning:
        logger.warning('Overwriting file ' + f + ' !')
    return f

def ensure_field_size_and_types_correct(fields, nice_key, value, val_type, attribute_tables, options): 
    # type(dict, str, type[any], namedtuple) -> None
    if nice_key in fields:
        fields[nice_key]['size'] = max( fields[nice_key]['size']
                                    ,len(str(value)) + max(0, options.extra_chars)
                                    )
        if val_type == shp_field_codes['float'] and 'decimal' in fields[nice_key]:
            fields[nice_key]['decimal'] = max( fields[nice_key]['decimal'], dec_places_req(value) )
        if val_type != fields[nice_key]['fieldType']:
            if (value in [0,1]) and fields[nice_key]['fieldType'] == shp_field_codes['bool'] or (val_type == shp_field_codes['bool'] 
                    and fields[nice_key]['fieldType'] == shp_field_codes['int'] 
                        and all(attribute_tables[i][nice_key] in [0,1] for i in attribute_tables.keys())):
                pass   #1s and 0s are in a Boolean field as integers or a 1 or a 0 in a Boolean field is type checking as an integer
                # TODO:  Check options and rectify - flag as Bool for now (rest of loop will recheck others), 
                #                                  or flag for recheck all at end
            elif val_type == shp_field_codes['float'] and fields[nice_key]['fieldType'] == shp_field_codes['int']:
                fields[nice_key]['fieldType'] = shp_field_codes['float']
                fields[nice_key]['decimal'] = dec_places_req(value)
            else:
                fields[nice_key]['fieldType'] = shp_field_codes['str']
                #logger.error('Type mismatch in same field.  Cannot store ' + str(value) + ' as .shp record type ' + fields[nice_key]['fieldType'])
    else:
        fields[nice_key] = { 'size' : len(str(value)) + max(0,options.extra_chars)
                            ,'fieldType' : val_type
                            }                          # could add a 'name' field, to save looping over the keys to this
                                                    # dict:
                                                    # fields[nice_key][name] = nice_key
                                                    #  and then just unpack a fields dict for each one:
                                                    # shapefile.Writer.field(**fields[nice_key]).  
                                                    # But it seems to be
                                                    # an undocumented feature of Writer.fields, doesn't reduce the amount of code
                                                    # (actually needs an extra line), requires duplicate data 
                                                    # in fields.  If we wanted to rename it in the shape file to
                                                    # something different than the dictionary key then this is a neat way.of doing so.
        if val_type == shp_field_codes['float']:
            fields[nice_key]['decimal'] = dec_places_req(value)    
    # Mutates fields.  Nothing returned.


def write_from_iterable_to_shapefile_writer( my_iterable 
                                            ,shp_file_path 
                                            ,shape_mangler
                                            ,shape_IDer # to make hashable dict key
                                            ,key_finder
                                            ,key_matcher
                                            ,value_demangler
                                            ,shape_code # e.g. 'POLYLINEZ'
                                            ,options
                                            ,field_names = None):
    #type(type[any], str, function, function, function, function,  function, str, dict)  -> int, str, dict, list, list
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
        msg_1 = ' Is Iterable == ' + str(is_iterable) 
        logger.info (msg_1)
        msg_2 = ' Is str ==' + str(is_str)
        logger.info (msg_2)
        msg_3 = ' Is path str ==' + str(is_path_str)
        logger.info (msg_3)
        msg_4 = 'my_iterable == ' + str(my_iterable)
        logger.info(msg_4)
        try:
            logger.info (' Is path path ==' + str(os.path.isdir(os.path.dirname(shp_file_path))))
        except:
            pass
        logger.info ('Path == ' + str(shp_file_path))
        raise TypeError('\n'.join([msg_1, msg_1, msg_3, msg_4]))
        


    max_size = (options.field_size 
            + options.extra_chars)

    fields = OrderedDict( {options.uuid_field 
                                : { 'fieldType' : shp_field_codes['str']
                                    ,'size' : options.uuid_length
                                            +max( 0,  options.extra_chars )
                                    }
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

                    value, val_type = shp_type_coercer(value, options)
                    values[nice_key] = value 


                    # Update the shp field sizes if they aren't big enough or the field is new, and type check
                    if options.min_sizes:
                        ensure_field_size_and_types_correct(fields, nice_key, value, val_type, attribute_tables, options)
                        # mutates fields, adding nice_key to it if not already there, else updating its val
                    else:
                        fields[nice_key] = { 'size' : max_size
                                            ,'fieldType' : val_type
                                            } 
                        if val_type == shp_field_codes['float']:
                            fields[nice_key]['decimal'] = options.num_dp 
            attribute_tables[item] = values.copy()  # item may not be hashable so can't use dict of dicts
    else:
        for name in field_names:
            fields[name] = { 'size' : max_size
                            ,'fieldType' : shp_field_codes['str']
                           }
        #TODO setup basic fields dict from list without looping over my_iterable        

    def default_record_dict(item):
        retval = { key_matcher(key).group('name') : 
                         str( value_demangler(item, key) )[:max_size] 
                            for key in key_finder(item) 
                            if (key_matcher(key) and
                                key_matcher(key).group('name') in fields)}
        retval[options.uuid_field ] = shape_IDer(item)
        return retval


    shapefile_path_to_write_to = get_unique_filename_if_not_overwrite(shp_file_path
                                                                     ,options
                                                                     )
    # wrapper_pyshp can work outside of rhino and grasshopper, so we don't know the name of the Rhino .3dm file.
    # Instead we'll wrap this wrapper function again in the Rhino / GH process in sDNA_GH.py to supply this inner 
    # function it as a normal parameter value for shp_file_path.
        



    
    with shp.Writer(  os.path.normpath( shapefile_path_to_write_to ), getattr(shp, shape_code)  ) as w:
        for key, val in fields.items():
            w.field(key, **val)
        #w.field('Name', 'C')

        logger.debug(str(fields))

        add_geometric_object = getattr( w,  shaperback_writer[shape_code] )
        for item, attribute_table in attribute_tables.items():
            list_of_shapes = shape_mangler(item)
            if list_of_shapes:

                add_geometric_object( list_of_shapes )   
                # e.g. start_and_end_points(my_iterable)

                #shp_ID = shape_IDer(item)
                #if shp_ID in attribute_tables:
                #    attribute_table = attribute_tables[ shp_ID ]
                #else:
                #    attribute_table = default_record_dict( item )
                #logger.debug('Attr table == ' + str(attribute_table))
                w.record( **attribute_table )    



    return 0, shapefile_path_to_write_to, fields, attribute_tables

def get_fields_recs_and_shapes_from_shapefile(shapefile_path):
    with shp.Reader(shapefile_path) as r:
        fields = r.fields[1:] # skip first field (deletion flag)
        recs = r.records()
        shapes = r.shapes()
        bbox = r.bbox
    #gdm = {shape : {k : v for k,v in zip(fields, rec)} for shape, rec in zip(shapes, recs)  }
    
    return fields, recs, shapes, bbox

def add_objects_to_group(objs, group_name):
    #type(list, str) -> int
    return rs.AddObjectsToGroup(objs, group_name)  

def make_new_group(group_name = None):
    #type(str) -> str
    return rs.AddGroup(group_name)

def create_new_groups_layer_from_points_list(
       shp_type = 'POLYLINEZ'
      ,make_new_group = make_new_group
      ,add_objects_to_group = add_objects_to_group
      ,Rhino_obj_adder_Shp_file_shape_map = Rhino_obj_adder_Shp_file_shape_map
      ):
    #type(namedtuple, function, function, dict) -> function
    rhino_obj_maker = getattr(rs, Rhino_obj_adder_Shp_file_shape_map[shp_type])
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

def get_shape_file_rec_ID(uuid_field): 
    #type(str) -> function
    def f(obj, record):
        if is_uuid(obj):
            target_doc = is_an_obj_in_GH_or_Rhino(obj)    
            if target_doc:
                sc.doc = target_doc
                # and is_an_obj_in_GH_or_Rhino(obj):
                return obj
        if hasattr(record, 'as_dict'):
            d = record.as_dict()
            if uuid_field in d:
                obj_ID = d[uuid_field]     
                # For future use.  Not possible until sDNA round trips through
                # Userdata into the output .shp file, including our uuid
                target_doc = is_an_obj_in_GH_or_Rhino(obj_ID)    
                if target_doc:
                    sc.doc = target_doc
                    return obj_ID
                #if (is_an_obj_in_GH_or_Rhino(obj_ID) or 
                #    is_a_group_in_GH_or_Rhino(obj_ID) ):
                #    return obj_ID
        g = create_new_groups_layer_from_points_list()
        return g(obj, record)
    return f 

if __name__=='__main__':
    pass
else:
    pass
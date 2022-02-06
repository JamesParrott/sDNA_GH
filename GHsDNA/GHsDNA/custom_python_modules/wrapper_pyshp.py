#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Convenience wrappers to read and write .shp files 
# from any iterable object and to any function
#
__author__ = 'James Parrott'
__version__ = '0.00'

import sys
from os.path import normpath, join, split, isfile 
from collections import OrderedDict,namedtuple
from datetime import date
from re import match


file_name_no_ext = split(__file__)[-1].split('.')[0]             #os.path.split and string.split

if __name__=='__main__':
    sys.path += [join(sys.path[0], '..')]
    sys.path += [join(sys.path[0], r'..',r'third_party_python_modules')]
    import shapefile as shp  
    class Stdout_logger():
        pass
    for attr in ['debug','info','warning','error','critical']:
        setattr(Stdout_logger, attr, lambda s : sys.stdout.write('attr'.upper() + ' : ' + s + '\n'))
    logger=Stdout_logger()
else:
    import logging
    logger = logging.getLogger(file_name_no_ext)
    from ..third_party_python_modules import shapefile as shp  


    #print("Wrapper_Pyshp Being imported as a module.  __name__ == " + __name__)



#try:
#    print("type(options) == ",type(options))
#except:
#    print("options not present")

###################################################################
#
# TODO: Make functions take options and metas as argument.
#
#if 'options' not in globals():
#    from config import options
#    if isinstance(options,dict):
#        from options_manager import makeNestedNamedTuple
#        options = makeNestedNamedTuple( options ,'Options','')

#################################################################


#if 'logging' in globals() and 'logger' in globals():
#    print "Logger found"
#else:
#    import logging, wrapper_logging
#    logger = wrapper_logging.new_Logger( __name__
#                                        ,join(sys.path[0],file_name_no_ext) + '.log')


#print("After config import if block type(options) == " + str(type(options)))




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


#print(dir(shp))

assert set(shp.SHAPETYPE_LOOKUP.values()) == set(shaperback_writer.keys())   
# SHAPETYPE_LOOKUP not in older versions of shapefile.py (especially 1.2.12 from Hiteca's GHshp)


def shp_type_coercer(x, options):
    #typecoercer function

    if options.use_str_decimal:
        import decimal as dec
    dec.getcontext().prec = options.decimal_module_prec #if else options.decimal_module_prec    # significant figures,  >= # decimal places
    if x in [True,False]:   # if isinstance(x,bool):.  Don't test coercion with bool() first or everything truthy will be 'L'
        return x, shp_field_codes['bool']   # i.e. 'L'
    try:
        y = int(x)   # if isinstance(x,int):  # Bool test needs to come before this as int(True) == 1
        return y, shp_field_codes['int']    # i.e.   'N'
    except:
        try:
            n = options.shp_record_max_decimal
            if options.use_str_decimal:
                y = dec.Decimal(x)
                y = y.quantize(  dec.Decimal('.'*int( bool(n) ) + '0'*(n-1) + '1')  )   # e.g. '1' if n=0, else '0.000... (#n 0s) ...0001'
            else:
                y = float(x)   # if isinstance(x,float):  # float('12345' ) == 12345.0 so int test needs to come 
                                                          # before this if 'N' and 'F' are utilised differently
                y = round(y, n)  #  Beware:  https://docs.python.org/2.7/tutorial/floatingpoint.html#tut-fp-issues                                                      
                
            return x if options.do_not_convert_floats else y, shp_field_codes['float']  # Tuple binds to result of ternary operator,
                                                                                               # not just to y
        except:
            if isinstance(x,date):
                return x, shp_field_codes['date']   # i.e. 'D'   

            if isinstance(x,list) and len(x) == 3 and all(isinstance(z,int) for z in x):
                x = ':'.join(map(str,x))
    
            if isinstance(x,str):
                year=r'([0-3]?\d{3})|\d{2}'
                month=r'([0]?\d)|(1[0-2]'
                day=r'([0-2]?\d)|(3[01])'
                sep=r'(?P<sep>[-.,:\\/ ])'
                test_patterns =  [ year + sep + month + sep + day ]   # datetime.date requires yyyy, mm, dd
                if not options.enforce_yyyy_mm_dd:
                    test_patterns += [  day + sep + month + sep + year   # https://en.wikipedia.org/wiki/Date_format_by_country
                                       ,month + sep + day + sep + year]  # 
                if any(match(pattern,x) for pattern in test_patterns):
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

def get_unique_filename_if_not_overwrite(f,opts):
    #type: (str,dict) -> str

    if not opts.overwrite_shp_file:
        i = 1
        file_dir, full_file_name = split(f)   #os.path.split
        [file_name, dot, file_extension] = full_file_name.rpartition('.')  #str.split
        while isfile(f):
            f = join(file_dir, file_name + opts.duplicate_file_name_suffix.format(i) + '.' + file_extension) #os.path.join
            i += 1  # Not good practice to change the value of the input argument shp_file_path, but if it's a str it's immutable, so no side effects
                    # even if we give it a default value
    elif not opts.suppress_overwrite_warning:
        logger.warning('Overwriting file ' + f + ' !')
    return f

def write_from_iterable_to_shapefile_writer( my_iterable 
                                            ,shp_file_path 
                                            ,shape_mangler
                                            ,key_finder
                                            ,key_matcher
                                            #,key_mangler
                                            #,value_mangler
                                            ,value_demangler
                                            ,shape
                                            ,options):
    #type: (iter , str , function, function, function,  function, str, dict)  -> str
    #shape_mangler type: (Bob) -> list(list(3),list(3)) Shapefile geometric object
    #
    #
    #
    fields = OrderedDict({options.uuid_shp_file_field_name : {        'fieldType' : shp_field_codes['str']
                                                                     , 'size' : options.uuid_length
                                                                              + max(0,options.shp_file_field_size_num_extra_chars)}})
    attribute_table_data = OrderedDict()
    
    #######################################
    # If my_iterable is not a list, cache it in my_list
    #
    my_iterable_is_a_list = isinstance(my_iterable, list)
    if my_iterable_is_a_list:
        my_list = my_iterable
    else:
        my_list = []

    for item in my_iterable:    
        if not my_iterable_is_a_list:   # and options.cache_rhino_objects: #  ?
            my_list += [item]

        keys = key_finder(item) # e.g. rhinoscriptsyntax.GetUserText(item,None)
        values = OrderedDict( {options.uuid_shp_file_field_name : item} )   
        for key in keys:
            # Demangle and cache the user text keys and values
            key_match = key_matcher(key)            # e.g. cPickle.loads.split('_')[1]
            if key_match:
                nice_key = key_match.group('name') 
                value = value_demangler(item, key) # e.g. cPickle.loads(rhinoscriptsyntax.GetUserText(item,key)

                value, val_type = shp_type_coercer(value, options)
                values[nice_key] = value 


                # Update the shp field sizes if they aren't big enough or the field is new, and type check
                if options.calculate_smallest_field_sizes:
                    if nice_key in fields:
                        fields[nice_key]['size'] = max( fields[nice_key]['size']
                                                    ,len(str(value)) + max(0, options.shp_file_field_size_num_extra_chars)
                                                    )
                        if val_type == shp_field_codes['float'] and 'decimal' in fields[nice_key]:
                            fields[nice_key]['decimal'] = max( fields[nice_key]['decimal'], dec_places_req(value) )
                        if val_type != fields[nice_key]['fieldType']:
                            if (value in [0,1]) and fields[nice_key]['fieldType'] == shp_field_codes['bool'] or (val_type == shp_field_codes['bool'] 
                                    and fields[nice_key]['fieldType'] == shp_field_codes['int'] 
                                        and all(attribute_table_data[i][nice_key] in [0,1] for i in attribute_table_data.keys())):
                                pass   #1s and 0s are in a Boolean field as integers or a 1 or a 0 in a Boolean field is type checking as an integer
                                # TODO:  Check options and rectify - flag as Bool for now (rest of loop will recheck others), 
                                #                                  or flag for recheck all at end
                            elif val_type == shp_field_codes['float'] and fields[nice_key]['fieldType'] == shp_field_codes['int']:
                                fields[nice_key]['fieldType'] = shp_field_codes['float']
                                fields[nice_key]['decimal'] = dec_places_req(value)
                            else:
                                logger.error('Type mismatch in same field.  Cannot store ' + str(value) + ' as .shp record type ' + fields[nice_key]['fieldType'])
                    else:
                        fields[nice_key] = { 'size' : len(str(value)) + max(0,options.shp_file_field_size_num_extra_chars)
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
                else:
                    fields[nice_key] = { 'size' : options.global_shp_file_field_size + options.shp_file_field_size_num_extra_chars
                                        ,'fieldType' : val_type
                                        } 
                    if val_type == shp_field_codes['float']:
                        fields[nice_key]['decimal'] = options.global_shp_number_of_decimal_places 
        attribute_table_data[item] = values.copy()  # Dict of dicts




    shapefile_path_to_write_to = get_unique_filename_if_not_overwrite(shp_file_path,options)
    # wrapper_pyshp can work outside of rhino and grasshopper, so we don't know the name of the Rhino .3dm file.
    # Instead we'll wrap this wrapper function again in the Rhino / GH process in GHsDNA.py to supply this inner 
    # function it as a normal parameter value for shp_file_path.
        



    
    with shp.Writer(  normpath( shapefile_path_to_write_to ), getattr(shp,shape)  ) as w:
        for key,val in fields.items():
            w.field(key,**val)
        #w.field('Name', 'C')

        add_geometric_object = getattr( w, shaperback_writer[shape] )
        #print(add_geometric_object)
        for item in my_list:
            list_of_shapes_to_write = [shape_mangler(item)]
            add_geometric_object( list_of_shapes_to_write )   # e.g. start_and_end_points(my_iterable)
            w.record( **attribute_table_data[item] )    # when used on a nested dict[key] ** unpacks the inner dict of key 
            #except:    print "Failed to add geometry to shapefile: ",  str(list_of_shapes_to_write)
        #w.linez(map(shape_mangler, my_iterable))
    #

    return shapefile_path_to_write_to, fields, attribute_table_data, my_list
    # Todo:  optionally, return my_list

def get_fields_and_records_from_shapefile(shapefile_path):
    with shp.Reader(shapefile_path) as r:
        fields = r.fields
        recs = r.records()
    return fields, recs


if __name__=='__main__':
    pass
else:
    pass
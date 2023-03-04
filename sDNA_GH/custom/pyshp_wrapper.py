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
__version__ = '2.2.0'
""" Reads .shp files, and parses data and writes .shp files from any iterable.   
"""

import os
import abc
import re
import logging
import warnings
import itertools
import locale
from collections import OrderedDict
from datetime import date
import collections

if hasattr(collections, 'Iterable'):
    Iterable, Callable = collections.Iterable, collections.Callable
else:
    import collections.abc
    Iterable, Callable = collections.abc.Iterable, collections.abc.Callable

if hasattr(abc, 'ABC'):
    ABC = abc.ABC
else:
    class ABC(object):
        __metaclass__ = abc.ABCMeta

from ..third_party.PyShp import shapefile as shp

from .options_manager import isnamedtuple
from .skel.tools.helpers import funcs


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
    x = str(x)  # To convert False to 'False' and 0 to '0'
    dec.getcontext().prec = options.precision #if else options.precision    # significant figures,  >= # decimal places
    if  x.lower() in ['true','false']:   
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
                         ,AttributeTablesClass = None
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
    
    if AttributeTablesClass is None:
        attribute_tables = OrderedDict()
    else:
        attribute_tables = AttributeTablesClass()

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
       



    
    with shp.Writer(os.path.normpath(shapefile_path)
                   ,getattr(shp, shape_code)
                   ,encoding = options.encoding
                   ) as w:

        for key, val in fields.items():
            w.field(key, **val)
        #w.field('Name', 'C')

        logger.debug(str(fields))

        add_geometric_object = getattr(w,  pyshp_writer_method[shape_code])
        # e.g. add_geometric_object = w.linez

        for shape, attribute_table in attribute_tables.items():
            if not is_shape(shape, shape_code):
                msg = 'Shape: %s cannot be converted to shape_code: %s' 
                msg %= (shape, shape_code)
                logger.error(msg)
                raise TypeError(msg)

            list_of_shapes = shape_mangler(shape)
            if list_of_shapes:

                add_geometric_object(list_of_shapes) 
                #e.g. w.linez(list_of_shapes)  

                w.record(**attribute_table)    



    return 0, shapefile_path, fields, attribute_tables


class FieldRecsShapesOptions(object):
    encoding = 'utf-8'


def get_fields_recs_and_shapes(shapefile_path, options = FieldRecsShapesOptions):
    # type(str, type[any]) -> list, Generator[dict], Generator[type[any]], list[Number], str, int
    with shp.Reader(shapefile_path, encoding = options.encoding) as r:
        fields = r.fields[1:] # skip first field (deletion flag)
        recs = (record.as_dict() for record in r.iterRecords())
        shapes = r.iterShapes()
        bbox = r.bbox
        shape_type = shp.SHAPETYPE_LOOKUP[r.shapeType]
        num_entries = len(r)

    #gdm = {shape : {k : v for k,v in zip(fields, rec)} 
    #               for shape, rec in zip(shapes, recs)  }
    
    return fields, recs, shapes, bbox, shape_type, num_entries


def shp_meta_data(shapefile_path, options = FieldRecsShapesOptions):
    # type(str, type[any]) -> list, list[Number], str, int
    with shp.Reader(shapefile_path, encoding = options.encoding) as r:
        fields = r.fields[1:] # skip first field (deletion flag)
        bbox = r.bbox
        shape_type = shp.SHAPETYPE_LOOKUP[r.shapeType]
        num_entries = len(r)

    #gdm = {shape : {k : v for k,v in zip(fields, rec)} 
    #               for shape, rec in zip(shapes, recs)  }
    
    return fields, bbox, shape_type, num_entries


def delete_file(path
               ,logger = logger
               ):
    #type(str, type[any]) -> None
    if os.path.isfile(path):
        logger.info('Deleting file: %s ' % path)
        os.remove(path)


def name_matches(file_name, regexes = ()):
    #type(str, Iterable) -> bool
    if isinstance(regexes, basestring):
        regexes = (regexes,)
    return any(bool(re.match(regex, file_name)) for regex in regexes)


def delete_shp_files_if_req(f_name
                           ,logger = logger
                           ,delete = True
                           ,strict_no_del = False
                           ,regexes = () # no file extension in regexes
                           ):
    #type(str, type[any], bool, str/tuple) -> None
    logger.debug('strict_no_del == %s ' % strict_no_del)
    if strict_no_del:
        return

    file_name_no_ext = os.path.splitext(f_name)[0]
    logger.debug('delete == %s ' % delete)
    if (delete or name_matches(file_name_no_ext, regexes)):
        for ext in ('.shp', '.dbf', '.shx', '.shp.names.csv'):
            path = file_name_no_ext + ext
            delete_file(path, logger)


class ShapeFilesDeleter(ABC):  # ABC for register
    
    file_name = None

    def __init__(self
                ,file_name 
                ):
        self.file_name = file_name

    def delete_files(self, delete, opts):
        if isinstance(self.file_name, basestring):
            #
            delete_shp_files_if_req(f_name = self.file_name
                                    ,delete = delete
                                    ,strict_no_del = opts['options'].strict_no_del  
                                    )

class InputFileDeletionOptions(GetFileNameOptions, FieldRecsShapesOptions):
    del_after_sDNA = True
    strict_no_del = False 
    INPUT_FILE_DELETER = None

class OutputFileDeletionOptions(GetFileNameOptions, FieldRecsShapesOptions):
    strict_no_del = InputFileDeletionOptions.strict_no_del 
    del_after_read = True
    OUTPUT_FILE_DELETER = None

class ShapeRecordsOptions(OutputFileDeletionOptions):
    copy_dicts = False
    shp_type = 'POLYLINEZ'


class NullDeleter(object):
    pass
ShapeFilesDeleter.register(NullDeleter)
#assert issubclass(NullDeleter, ShapeFilesDeleter)


class SizedIterator(object):
    """ An wrapper for iterator that knows its own length.
    
        Instances can yield the same values as from an iterator
        from any generator function, but can also be duck-typed 
        for lists and tuples that require a length (but that are 
        still only iterated over, i.e. that don't have __getitem__ 
        or other list methods called on them, such as:
        ghpythonlib.treehelpers.list_to_tree
        https://gist.github.com/piac/ef91ac83cb5ee92a1294#file-list_to_tree-py ). 
        
        Class instances are initialised with any iterator and 
        a length.  The intended usage case is for generator 
        functions, for whom a length may still be known by other 
        trusted means e.g. from reliable file meta-data (or whose 
        value is unimportant as long as it's non-zero).  The iterators 
        returned by generator functions do not have lengths, as such 
        a 'length', the number yield statements executed, depends 
        dynamically on the code in the generator function's body.  
    """

    def __init__(self, iterator, length):
        self.iterator = iterator
        self.length = length
    
    def next(self):
        return next(self.iterator)
    
    def __iter__(self):
        return self

    def __len__(self):
        return self.length


class TmpFileDeletingIterator(SizedIterator):
    """ Iterator wrapper for a file object that calls 
        self.close and thence self.maybe_delete_file 
        when the iterator is exhausted.

        This is fine just to safely delete a temporary 
        shape file.  In general there are many issues 
        with this pattern, e.g.
        if the user breaks out of the for loop early, 
        clean up will not happen automatically for them.  
        https://peps.python.org/pep-0533/ 
    """
    def __init__(self, reader, opts = None):
        # type(shp.Reader, dict, dict) -> None
        if opts is None:
            opts = dict(options = ShapeRecordsOptions)
        self.opts = opts
        
        if isinstance(reader, basestring) and os.path.isfile(reader):
            self.file_path = reader
            encoding = opts['options'].encoding.replace('-','')
            reader = shp.Reader(reader, encoding = encoding)
        elif not isinstance(reader, shp.Reader):
            raise ValueError('No shapefile reader or file path supplied. ')

        self.reader = reader
        
        self.file_path = reader.shp.name

        if reader.shapeTypeName != opts['options'].shp_type:
            msg = 'Shape type of file: %s, %s does not match '
            msg %= (self.file_path, reader.shapeTypeName)
            msg += 'shape type in options: %s. '
            msg %= opts['options'].shp_type
            msg += "Using the shape file's shape type. "
            
            logger.warning(msg)
            warnings.warn(msg)
            
            
        self.shp_type = reader.shapeTypeName

        

        super(TmpFileDeletingIterator, self).__init__(
                                                   iterator = self.generator()
                                                  ,length = len(reader)
                                                  )
        
    def generator(self):
        """ Generator to process the shp file reader, used to produce the 
            desired iterator that yields what ever is wanted.  """
        return self.reader.iterShapes()

    def next(self):
        try:
            retval = next(self.iterator)
        except StopIteration as e:
            logger.debug('Iterator exhausted.  Closing...')
            self.close()
            raise e
    
        return retval

    def maybe_delete_file(self, *args):
        logger.debug('maybe_delete_file called.')
        options = self.opts['options']
        if (options.del_after_read and 
            not options.strict_no_del and 
            not options.overwrite_shp and 
            isinstance(options.OUTPUT_FILE_DELETER, ShapeFilesDeleter) and
            self.file_path == options.OUTPUT_FILE_DELETER.file_name):
            #
            options.OUTPUT_FILE_DELETER.delete_files(
                                                delete = options.del_after_read
                                               ,opts = self.opts
                                               )
            self.opts['options'] = self.opts['options']._replace(
                                                    OUTPUT_FILE_DELETER = None
                                                    )

    def close(self):
        logger.debug('Closing reader: %s' % self.reader)
        self.reader.close()
        logger.debug('Attempting to delete file: %s ' % self.file_path)
        self.maybe_delete_file()


def is_single_shape(shapeRecord):
    shape = getattr(shapeRecord, 'shape', shapeRecord)
    if not hasattr(shape, 'parts'):
        msg = ('shape has no attr "parts", the indices of sub-shapes '
              +'in shape.points.  Assuming it is a single shape. '
              )
        logger.warning(msg)
        warnings.warn(msg)
        return True
    else:
        return len(shape.parts) <= 1


class TmpFileDeletingRecordsIterator(TmpFileDeletingIterator):
    """ If zipping another iterator that is shorter or the same length
        with this one (e.g. that yields 
        existing shapes), to ensure the temporary file deleter is 
        called when this iterator is used up, be sure to zip it with
        zip_longest or, izip_longest, make an iterator the same size
        artificially longer.  Otherwise the file deleter's
        delete_files method must be called directly.
    """
    def generator(self):
        return (record.as_dict() for record in self.reader.iterRecords())




class MultipleShapes(list):
    """ Trivial flag class. """
    pass

def identity(*args):
    return args


def clone_dicts(group):
    return [[(obj, dict_.copy()) for obj, dict_ in list_] for list_ in group]

    
def shape_and_rec_as_dict(shape_record):
    return shape_record.shape, shape_record.record.as_dict()

def shapes_and_recs_as_dicts(shape_records):
        return [shape_and_rec_as_dict(shape_record)
                for shape_record in shape_records
                ]



class TmpFileDeletingShapeRecordsIterator(TmpFileDeletingIterator):

    def is_3D_shape_type(self):
        #  POLYLINEZ or LINEM etc.
        return self.reader.shapeTypeName[-1] in 'ZM'

    def points_and_rec_2D(self, shape, record):
        return shape.points, record

    def points_and_rec_3D(self, shape, record):
        # z coordinate is not simply in points
        return [(x,y,z) for ((x,y), z) in zip(shape.points, shape.z)], record

    def points_and_records(self, shapes_and_records):
        return [self.points_and_rec(shape, record) 
                for shape, record in shapes_and_records]    

    def unpack_multi_shape_entry_repeat_rec_as_dict(self, multi_shape_record):
        shapes, rec = shape_and_rec_as_dict(multi_shape_record)
        points, _ = self.points_and_rec(shapes, rec)
        parts = shapes.parts
        return ((points[start:end], rec) for start, end in itertools.pairwise(parts))

    def setup_manglers(
                    self
                    ,extra_manglers
                    ,copy_dicts = ShapeRecordsOptions.copy_dicts
                    ):
        # manglers will be applied to groups of consecutive single shapes 
        # and groups of consecutive multi-shape shp file entries


        self.manglers = {True:  funcs.compose(self.points_and_records, shapes_and_recs_as_dicts)
                        ,False: self.unpack_multi_shape_entry_repeat_rec_as_dict
                        }

        if extra_manglers is not None or copy_dicts:

            if extra_manglers is None: # assert copy_dicts
                extra_manglers = {False : [clone_dicts]}
            elif copy_dicts:
                if isinstance(extra_manglers[False], Callable):
                    extra_manglers[False] = [extra_manglers[False]]
                extra_manglers[False].insert(0, clone_dicts)


            for key, val in extra_manglers.items():
                new_manglers = [val] if isinstance(val, Callable) else val
                    
                if key in self.manglers:
                    new_manglers += [self.manglers[key]]
                
                logger.debug('new_manglers == %s' % (new_manglers,))
                
                new_mangler = funcs.compose(*new_manglers)
                logger.debug('new_mangler == %s' % (new_mangler,))


                self.manglers[key] = new_mangler

        for mangler in self.manglers.values():
            if not isinstance(mangler, Callable):
                msg = 'mangler == %s not Callable' % (mangler,)
                logger.error(msg)
                raise ValueError(msg)


    def __init__(self, reader, extra_manglers = None, opts = None):
        #type(shp.Reader, dict, dict)

        if opts is None:
            opts = dict(options = ShapeRecordsOptions)

        self.setup_manglers(
                         extra_manglers
                        ,copy_dicts = opts['options'].copy_dicts
                        )

        super(TmpFileDeletingShapeRecordsIterator, self).__init__(reader, opts)

        self.points_and_rec = self.points_and_rec_3D if self.is_3D_shape_type() else self.points_and_rec_2D



    def generator(self):
        return funcs.multi_item_unpacking_iterator(
                                         items = self.reader.iterShapeRecords()
                                        ,is_single_item = is_single_shape
                                        ,manglers = self.manglers
                                        )


 




class ShpOptions(ShapeRecordsOptions
                ,CoerceAndGetCodeOptions
                ,GetFileNameOptions
                ,EnsureCorrectOptions
                ,WriteIterableToShpOptions
                ,LocaleOptions
                ,FieldRecsShapesOptions
                ):
    pass


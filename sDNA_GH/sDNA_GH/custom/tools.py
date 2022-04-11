import sys, logging
from collections import OrderedDict
from abc import abstractmethod
if sys.version < '3.4':
    from abc import ABCMeta
    class ABC:
        __metaclass__ = ABCMeta
else:
    from abc import ABC

import sys, os  
from os.path import (join, split, isfile, dirname, isdir, sep, normpath
                     ,basename as filename
                     )

from re import match
from subprocess import check_output, call
from time import asctime
from collections import namedtuple, OrderedDict
from itertools import chain, izip, repeat #, cycle
from uuid import UUID
import csv
from numbers import Number
import locale
from math import log
from importlib import import_module
if sys.version < '3.3':
    from collections import Hashable, Iterable, MutableMapping
else:
    from collections.abc import Hashable, Iterable, MutableMapping


import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import ghpythonlib.treehelpers as th
from System.Drawing import Color as Colour
from System.Drawing import PointF, SizeF
from Grasshopper.GUI.Gradient import GH_Gradient
import GhPython
import Grasshopper.Kernel 
from ghpythonlib.components import ( BoundingBox
                                    ,Rectangle
                                    ,Legend 
                                    ,XYPlane
                                    ,XZPlane
                                    ,YZPlane
                                    ,CustomPreview
                                    )
from .helpers.funcs import (ghdoc
                           ,is_uuid
                           ,func_name
                           ,make_regex
                           ,splines
                           ,linearly_interpolate
                           ,map_f_to_three_tuples
                           ,three_point_quadratic_spline

                           )
from .helpers.quacks_like import quacks_like
from ..launcher import Output, Debugger
from .options_manager import (make_nested_namedtuple
                             ,
                             )
from .wrapper_pyshp import (get_unique_filename_if_not_overwrite
                           ,get_points_list_from_geom_obj
                           ,write_from_iterable_to_shapefile_writer
                           ,get_fields_recs_and_shapes_from_shapefile
                           ,create_new_groups_layer_from_points_list
                           )

from .gdm_from_GH_Datatree import (make_gdm
                                  ,get_objs_and_OrderedDicts
                                  ,get_all_shp_type_Rhino_objects
                                  ,get_all_groups
                                  ,get_members_of_a_group
                                  ,check_is_specified_obj_type
                                  ,override_gdm_with_gdm
                                  ,get_OrderedDict
                                  ,get_shape_file_rec_ID
                                  ,get_obj_keys
                                  ,write_obj_val
                                  ,is_an_obj_in_GH_or_Rhino
                                  ,is_a_group_in_GH_or_Rhino
                                  )



#import logging
logger = logging.getLogger('sDNA_GH').addHandler(logging.NullHandler())
#logger = logging.getLogger(__name__)

output = Output(tmp_logs = [], logger = logger)
debug = Debugger(output)


class ToolABC(ABC):    #Template for tools that can be run by run_tools()
                    # Subclass of this is not enforced, to permit tools from
                    # functions with attributes via ducktyping
    @abstractmethod
    def args(self):
        return ()   # Only the order need correspond to 
                # __call__'s args. The names can be 
                # different.  The ones in the args tuple
                # are used as keys in vals_dict.  
                # show['Inputs'] defines the
                # input Param names of the component 

    @abstractmethod
    def __call__(self, *args):
        assert len(args) == len(self.args)
        '''  Main tool function'''
        retcode=0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    @abstractmethod
    def retvals(self): 
        return ('retcode',) # strings of variable names inside __call__, to be used 
                 # keys in vals_dict.  show['Outputs'] defines the required 
                 # output Param names on the 
                 # GH component

    @abstractmethod
    def show(self):
        return dict(Inputs = ()
                   ,Outputs = ()
                   )

class Tool(ToolABC):
    def __str__(self):
        s = self.tool_name if hasattr(self, 'tool_name') else ''
        s += ' an instance of ' + self.__class__ +'.  '
        return s

def run_tools(tools
             ,args_dict
             ):  #f_name, gdm, opts):
    #type(list[Tool], dict)-> dict

    if not isinstance(tools, list):
        tools = list(tools)
    invalid_tools = [tool for tool in tools 
                          if not ( isinstance(tool, ToolABC) 
                                   or quacks_like(ToolABC, tool)
                                 )
                    ]
    if invalid_tools:
        raise ValueError(output('Invalid tool(s) == ' + str(invalid_tools),'ERROR'))
    
    opts = args_dict['opts']
    metas = opts['metas']
    name_map = metas.name_map._asdict()

    #tool_names = []
    #assert not any(key == name_map[key] for key in name_map)
    # return_component_names checked for clashes and cycles etc.

    # def get_tools(name):
    #     for tool_name in name_map[name]:
    #         if tool_name in name_map:
    #             tool_names += get_tools(tool_name)  
    #         else:
    #             tool_names += [tool_name]

    # assert len(tool_names) == len(tools)

    vals_dict = args_dict 
                #OrderedDict( [   ('f_name', f_name)
                #                ,('gdm', gdm)
                #                ,('opts', opts)
                #             ]
                #            )

    debug(tools)                            
    for tool in tools:
        debug(tool)


        inputs = [vals_dict.get(input, None) for input in tool.args]
        retvals = tool( *inputs)
                        #  if input not in (('Data','Geom','go')
                        #  +opt)] 
                        # vals_dict['f_name']
                        #,vals_dict['gdm']
                        #,vals_dict['opts'] 
                        #)
        vals_dict.update( OrderedDict(zip(tool.retvals, retvals)) )
        vals_dict.setdefault( 'file'
                            , vals_dict.get('f_name')
                            )
        vals_dict['OK'] = (vals_dict['retcode'] == 0)

        retcode = vals_dict['retcode']
        debug(' return code == ' + str(retcode))
        if retcode != 0:
            raise Exception(output(  'Tool ' + func_name(tool) + ' exited '
                                    +'with status code ' 
                                    + str(retcode)
                                    ,'ERROR'
                                    )
                            )

    return vals_dict        

sDNA_tool_logger = logging.getLogger('sDNA')

class sDNAWrapper(Tool):
    # This class is instantiated once per sDNA tool name.  In addition to the 
    # other necessary attributes of Tool, instances know their own name, in
    # self.tool_name.  Only when instances are called, are Nick_names and sDNA
    # are looked up in local_metas, and opts['metas'], in the args.
    # 
    def get_tool_opts_and_syntax(self
                                ,opts
                                ,local_metas
                                ):
        metas = opts['metas']
        nick_name = local_metas.nick_name
        sDNAUISpec = opts['options'].sDNAUISpec
        sDNA = opts['metas'].sDNA

        tool_opts = opts.setdefault(nick_name, {})
        debug(tool_opts)
        tool_opts = tool_opts.setdefault(self.tool_name, tool_opts)
        # Note, this is intended to do nothing if nick_name == self.tool_name
        try:
            sDNA_Tool = getattr(sDNAUISpec, self.tool_name)
        except:
            raise ValueError(output('No tool called '
                                   +self.tool_name
                                   +sDNAUISpec.__name__
                                   +'.  Rename tool_name or change sDNA version.  '
                                   )
                            )
        input_spec = sDNA_Tool.getInputSpec()
        get_syntax = sDNA_Tool.getSyntax     

        defaults_dict = { varname : default for (varname
                                                ,displayname
                                                ,datatype
                                                ,filtr
                                                ,default
                                                ,required
                                                ) in input_spec  
                        }            
        if sDNA in tool_opts:
            tool_opts_dict = defaults_dict.update( tool_opts[sDNA]._asdict() ) 
        else:
            tool_opts_dict = defaults_dict
        namedtuple_class_name = (nick_name 
                                +(self.tool_name if self.tool_name != nick_name else '') 
                                +sDNAUISpec.__file__
                                )
        tool_opts[sDNA] = make_nested_namedtuple(tool_opts_dict
                                                ,namedtuple_class_name
                                                ,strict = True
                                                ) 

        return tool_opts, get_syntax


    def __init__(self
                ,tool_name
                ,opts
                ,local_metas
                ):
        #if tool_name in support_component_names:
        #    def support_tool_wrapper(f_name, Geom, Data, opts):  
        #        return globals()[tool_name](f_name, Geom, Data)
        #    tools_dict[tool_name] = support_tool_wrapper   
            #
            #
        self.tool_name = tool_name
        tool_opts, _ = self.get_tool_opts_and_syntax(opts, local_metas)

        sDNA = opts['metas'].sDNA
        global do_not_remove
        do_not_remove += tuple(tool_opts[sDNA]._fields)


    args = ('file', 'opts', 'l_metas')
    component_inputs = ('go', ) + args[:2]


    def __call__(self # the callable instance / func, not the GH component.
                ,f_name
                ,opts
                ,local_metas
                ):
        #type(Class, dict(namedtuple), str, Class, DataTree)-> Boolean, str

        sDNA = opts['metas'].sDNA
        sDNAUISpec = opts['options'].sDNAUISpec
        run_sDNA = opts['options'].run_sDNA 



        if not hasattr(sDNAUISpec, self.tool_name): 
            raise ValueError(self.tool_name + 'not found in ' + sDNA[0])
        options = opts['options']

        tool_opts, get_syntax = self.get_tool_opts_and_syntax(opts, local_metas)


        dot_shp = options.shp_file_extension

        input_file = tool_opts[sDNA].input
        

        #if (not isinstance(input_file, str)) or not isfile(input_file): 
        if (isinstance(f_name, str) and isfile(f_name)
            and f_name.rpartition('.')[2] in [dot_shp[1:],'dbf','shx']):  
            input_file = f_name
    
            # if options.auto_write_new_Shp_file and (
            #     options.overwrite_input_shapefile 
            #     or not isfile(input_file)):
            #     retcode, input_file, gdm = write_shapefile( 
            #                                                  input_file
            #                                                 ,gdm
            #                                                 ,opts
            #                                                 )
            


        output_file = tool_opts[sDNA].output
        if output_file == '':
            output_suffix = options.output_shp_file_suffix
            if self.tool_name == 'sDNAPrepare':
                output_suffix = options.prepped_shp_file_suffix   
            output_file = input_file.rpartition('.')[0] + output_suffix + dot_shp

        output_file = get_unique_filename_if_not_overwrite(output_file, options)

            
        syntax = get_syntax(tool_opts[sDNA]._asdict().update(input = input_file))

        f_name = output_file

        command =   (options.python_exe 
                    + ' -u ' 
                    + '"' 
                    + join(  dirname(sDNAUISpec.__file__)
                            ,'bin'
                            ,syntax['command'] + '.py'  
                            ) 
                    + '"'
                    + ' --im ' + run_sDNA.map_to_string( syntax["inputs"] )
                    + ' --om ' + run_sDNA.map_to_string( syntax["outputs"] )
                    + ' ' + syntax["config"]
                    )
        
        sDNA_tool_logger.debug(command)

        try:
            output_lines = check_output(command)
            #print output_lines
            retcode = 0
        except:
            retcode = 1
        finally:
            try:
                line_end = '\r\n' if '\r\n' in output_lines else '\n'
                for line in output_lines.split(line_end):
                    sDNA_tool_logger.debug(line)
            except:
                pass
        #return_code = call(command)   
        
        #return_code = run_sDNA.runsdnacommand(    syntax
        #                                    ,sdnapath = dirname(sDNAUISpec.__file__)  #opts['options'].sDNA_UISpec_path
        #                                    ,progress = IllusionOfProgress()
        #                                    ,pythonexe = options.python_exe
        #                                    ,pythonpath = None)   # TODO:  Work out if this is important or not! 
                                                                # os.environ["PYTHONPATH"] not found in Iron Python

        #return return_code, tool_opts[sDNA].output, gdm, a
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    retvals = 'retcode', 'f_name', 'gdm', 'opts'
    show = dict(Input = component_inputs
                ,Output = ('OK', 'file', retvals[-1])
                )



class GetObjectsFromRhino(Tool):
    args = ('gdm', 'opts') # Only the order need correspond to the 
                           # function's args. The names can be 
                           # different.  The ones in the args tuple
                           # are used as keys in vals_dict and for 
                           # input Param names on the component
    component_inputs = ('go', args[1]) # 'Geom', 'Data') + args
    
    def __call__(self, geom_data_map, opts):
        #type(str, dict, dict) -> int, str, dict, list

        options = opts['options']
        #if 'ghdoc' not in globals():
        #    global ghdoc
        #    ghdoc = sc.doc  

        sc.doc = Rhino.RhinoDoc.ActiveDoc 
        
        #rhino_groups_and_objects = make_gdm(get_objs_and_OrderedDicts(options))
        gdm = make_gdm(get_objs_and_OrderedDicts(
                                                options
                                                ,get_all_shp_type_Rhino_objects
                                                ,get_all_groups
                                                ,get_members_of_a_group
                                                ,lambda *args, **kwargs : {} 
                                                ,check_is_specified_obj_type
                                                            ) 
                                )
        # lambda : {}, as Usertext is read elsewhere, in read_Usertext




        debug('First objects read: \n' + '\n'.join(str(x) for x in gdm.keys()[:3]))
        if len(gdm) > 0:
            debug('type(gdm[0]) == ' + type(gdm.keys()[0]).__name__ )
        debug('....Last objects read: \n' + '\n'.join(str(x) for x in gdm.keys()[-3:]))

        gdm = override_gdm_with_gdm(gdm, geom_data_map, opts)
        sc.doc = ghdoc # type: ignore 

        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]

    retvals = 'retcode', 'gdm'
    show = dict(Input = component_inputs
               ,Output = ('OK', 'Geom') + retvals[1:]
               )


class ReadUsertext(Tool):
    args = ('gdm', 'opts')
    component_inputs = ('go', 'Data', args[0])

    def __call__(self, gdm, opts):
        #type(str, dict, dict) -> int, str, dict, list

        debug('Starting read_Usertext... ')
        options = opts['options']

        # if (options.auto_get_Geom and
        #    (not geom_data_map or not hasattr(geom_data_map, 'keys') or
        #    (len(geom_data_map.keys()) == 1 and geom_data_map.keys()[0] == tuple() ))):
        #     #
        #     retcode, gdm = get_Geom( geom_data_map
        #                             ,opts
        #                             )
        #     #
        # else:
        #     retcode = 0
        #     gdm = geom_data_map
        #if opts['options'].read_overides_Data_from_Usertext:

        read_Usertext_as_tuples = get_OrderedDict()
        for obj in gdm:
            gdm[obj].update(read_Usertext_as_tuples(obj))

        # get_OrderedDict() will get Usertext from both the GH and Rhino docs
        # switching the target to RhinoDoc if needed, hence the following line 
        # is important:
        sc.doc = ghdoc # type: ignore 
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]

    retvals = 'retcode', 'gdm'

    show = dict(Input = component_inputs
               ,Output = ('OK', 'Geom', 'Data') + retvals[1:]
               )


class WriteShapefile(Tool):
    args = ('file', 'gdm', 'opts')
    component_inputs = ('go', args[0], 'Geom', 'Data') + args[1:]

    def __call__(self, f_name, geom_data_map, opts):
        #type(str, dict, dict) -> int, str, dict, list
        
        options = opts['options']

        shp_type = options.shp_file_shape_type            
        #print geom_data_map
        # if (options.auto_read_Usertext and
        #         (not geom_data_map or not hasattr(geom_data_map, 'values')
        #         or all(len(v) ==0  for v in geom_data_map.values()))):
        #     retcode, f_name, geom_data_map = read_Usertext(  f_name
        #                                                     ,geom_data_map
        #                                                     ,opts
        #                                                     )

        format_string = options.rhino_user_text_key_format_str_to_read
        pattern = make_regex( format_string )

        def pattern_match_key_names(x):
            #type: (str)-> object #re.MatchObject

            return match(pattern, x) 
            #           if m else None #, m.group('fieldtype'), 
                                                # m.group('size') if m else None
                                                # can get 
                                                # (literal_text, field_name, 
                                                #                  f_spec, conv) 
                                                # from iterating over
                                                # string.Formatter.parse(
                                                #                 format_string)

        def get_list_of_lists_from_tuple(obj):
            #debug(obj)
            #if is_an_obj_in_GH_or_Rhino(obj):
            target_doc = is_an_obj_in_GH_or_Rhino(obj)    
            if target_doc:
                sc.doc = target_doc
                if check_is_specified_obj_type(obj, shp_type):
                    return [get_points_list_from_geom_obj(obj, shp_type)]
                else:
                    return []      
                #elif is_a_group_in_GH_or_Rhino(obj):
            else:
                target_doc = is_a_group_in_GH_or_Rhino(obj)    
                if target_doc:
                    sc.doc = target_doc                  
                    return [get_points_list_from_geom_obj(y, shp_type) 
                            for y in get_members_of_a_group(obj)
                            if check_is_specified_obj_type(y, shp_type)]
                else:
                    return []

        def shape_IDer(obj):
            return obj #tupl[0].ToString() # uuid

        def find_keys(obj):
            return geom_data_map[obj].keys() #tupl[1].keys() #rs.GetUserText(x,None)

        def get_data_item(obj, key):
            return geom_data_map[obj][key] #tupl[1][key]

        if not f_name:  
            if (   options.shape_file_to_write_Rhino_data_to_from_sDNA_GH
                and isdir(dirname( options.shape_file_to_write_Rhino_data_to_from_sDNA_GH ))   ):
                f_name = options.shape_file_to_write_Rhino_data_to_from_sDNA_GH
            else:
                f_name = options.Rhino_doc_path.rpartition('.')[0] + options.shp_file_extension
                            # file extensions are actually optional in PyShp, 
                            # but just to be safe and future proof we remove
                            # '.3dm'                                        

        #debug('Type of geom_data_map == '+ type(geom_data_map).__name__)                         
        #debug('Size of geom_data_map == ' + str(len(geom_data_map)))
        #debug('Gdm keys == ' + ' '.join( map(lambda x : x[:5],geom_data_map.keys() )) )
        #debug('Gdm.values == ' + ' '.join(map(str,geom_data_map.values())))
        sc.doc = Rhino.RhinoDoc.ActiveDoc 
        (retcode, f_name, fields, gdm) = ( 
                            write_from_iterable_to_shapefile_writer(
                                                geom_data_map
                                        #my_iter 
                                                ,f_name 
                                        #shp_file 
                                                ,get_list_of_lists_from_tuple 
                                        # shape_mangler, e.g. start_and_end_points
                                                ,shape_IDer
                                                ,find_keys 
                                        # key_finder
                                                ,pattern_match_key_names 
                                        #key_matcher
                                                ,get_data_item 
                                        #value_demangler e.g. rs.GetUserText
                                                ,shp_type 
                                        #"POLYLINEZ" #shape
                                                ,options 
                                                ,None 
                                        # field names
                            )
        ) 
        # get_list_of_lists_from_tuple() will 
        # switch the targeted file to RhinoDoc if needed, hence the following line 
        # is important:
        sc.doc = ghdoc # type: ignore 
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]

    retvals = 'retcode', 'f_name', 'gdm'

    show = dict(Input = component_inputs
               ,Output = ('OK', 'file') #+ write_shp.retvals[2:]
               )


class ReadShapefile(Tool):
    #type() -> function
    args = ('file', 'gdm', 'opts')
    component_inputs = ('go', args[0], 'Geom') + args[1:]

    def __call__(self, f_name, geom_data_map, opts ):
        #type(str, dict, dict) -> int, str, dict, list
        options = opts['options']

        ( fields
        ,recs
        ,shapes
        ,bbox ) = get_fields_recs_and_shapes_from_shapefile( f_name )

        if not recs:
            output('No data read from Shapefile ' + f_name + ' ','WARNING')
            return 1, f_name, geom_data_map, None    
            
        if not shapes:
            output('No shapes in Shapefile ' + f_name + ' ','WARNING')
            return 1, f_name, geom_data_map, None

        if not bbox:
            output('No Bounding Box in Shapefile.  '
                   + f_name 
                   + ' '
                   +'Supply bbox manually or create rectangle to plot legend.  '
                   ,'WARNING')
            

        field_names = [ x[0] for x in fields ]

        debug('options.uuid_shp_file_field_name in field_names == ' + str(options.uuid_shp_file_field_name in field_names))
        debug(field_names)

        shapes_to_output = ([shp.points] for shp in shapes )
        
        obj_key_maker = create_new_groups_layer_from_points_list( options ) 



        if not options.create_new_groups_layer_from_shapefile:   #TODO: put new objs in a new layer or group
            obj_key_maker = get_shape_file_rec_ID(options) # key_val_tuples
            # i.e. if options.uuid_shp_file_field_name in field_names but also otherwise
        
            if isinstance(geom_data_map, dict) and len(geom_data_map) == len(recs):
                # figuring out an override for different number of overrided geom objects
                # to shapes/recs is to open a large a can of worms.  Unsupported.
                # If the override objects are in Rhino anyway then the uuid field in the shape
                # file will be picked up in any case in get_shape_file_rec_ID
                if sys.version_info.major < 3:
                    shape_keys = geom_data_map.viewkeys()  
                else: 
                    shape_keys = geom_data_map.keys()
                shapes_to_output = [shp_key for shp_key in shape_keys]
                    # These points shouldn't be used, as by definition they 
                    # come from objects that already
                    # exist in Rhino.  But if they are to be used, then use this!
                #debug(shapes_to_output)    


        shp_file_gen_exp  = izip( shapes_to_output
                                ,(rec.as_dict() for rec in recs)
                                )
        
        #(  (shape, rec) for (shape, rec) in 
        #                                       izip(shapes_to_output, recs)  )              
        sc.doc = Rhino.RhinoDoc.ActiveDoc
        gdm = make_gdm(shp_file_gen_exp, obj_key_maker)
        sc.doc = ghdoc # type: ignore
        
        dot_shp = options.shp_file_extension
        csv_f_name = f_name.rpartition('.')[0] + dot_shp + '.names.csv'
        sDNA_fields = {}
        if isfile(csv_f_name):
            f = open(csv_f_name, 'rb')
            f_csv = csv.reader(f)
            sDNA_fields = [OrderedDict( (line[0], line[1]) for line in f_csv )]
            abbrevs = [line[0] for line in f_csv ]


        debug(bbox)

        #override_gdm_with_gdm(gdm, gdm, opts)   # TODO:What for?

        if options.delete_shapefile_after_reading and isfile(f_name): 
            os.remove(f_name)  # TODO: Fix, currently Win32 error

        retcode = 0

        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]

    retvals = 'retcode', 'gdm', 'abbrevs', 'sDNA_fields', 'bbox', 'opts'
    show = dict(Input = component_inputs
               ,Output = ('OK', 'Geom', 'Data') + retvals[1:]
               ) 




class WriteUsertext(Tool):
    args = ('gdm', 'opts')
    component_inputs = ('go', 'Geom', 'Data') + args


    def __call__(self, gdm, opts):
        #type(str, dict, dict) -> int, str, dict, list
        options = opts['options']

        date_time_of_run = asctime()

        def write_dict_to_UserText_on_obj(d, rhino_obj):
            #type(dict, str) -> None
            if not isinstance(d, dict):
                return
            
            #if is_an_obj_in_GH_or_Rhino(rhino_obj):
                # Checker switches GH/ Rhino context
            
            target_doc = is_an_obj_in_GH_or_Rhino(rhino_obj)    
            if target_doc:
                sc.doc = target_doc        
                existing_keys = get_obj_keys(rhino_obj)
                #TODO Move key pattern matching into ReadSHP
                if options.uuid_shp_file_field_name in d:
                    obj = d.pop( options.uuid_shp_file_field_name )
                
                for key in d:

                    s = options.sDNA_output_user_text_key_format_str_to_read
                    UserText_key_name = s.format(name = key
                                                ,datetime = date_time_of_run
                                                )
                    
                    if not options.overwrite_UserText:

                        for i in range(0, options.max_new_UserText_keys_to_make):
                            tmp = UserText_key_name 
                            tmp += options.duplicate_UserText_key_suffix.format(i)
                            if tmp not in existing_keys:
                                break
                        UserText_key_name = tmp
                    else:
                        if not options.suppress_overwrite_warning:
                            output( "UserText key == " 
                                    + UserText_key_name 
                                    +" overwritten on object with guid " 
                                    + str(rhino_obj)
                                    ,'WARNING'
                                    )
                    write_obj_val(rhino_obj, UserText_key_name, str( d[key] ))
            else:
                output('Object: ' 
                    + key[:10] 
                    + ' is neither a curve nor a group. '
                    ,'INFO'
                    )

        for key, val in gdm.items():
            #if is_a_curve_in_GH_or_Rhino(key):
            target_doc = is_an_obj_in_GH_or_Rhino(key)    
            if target_doc:
                sc.doc = target_doc          
                group_members = [key]
            else:
                target_doc = is_a_group_in_GH_or_Rhino(key)    
                if target_doc:
                    sc.doc = target_doc              
                    #elif is_a_group_in_GH_or_Rhino(key):
                    # Switches context, but will be switched again
                    # when members checked
                    group_members = get_members_of_a_group(key)
                    # Can't use rs.SetUserText on a group name.  Must be a uuid.
                else:
                    group_members = [key]

                
            for member in group_members:
                write_dict_to_UserText_on_obj(val, member)

        sc.doc = ghdoc # type: ignore 
        
        retcode = 0

        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    retvals = ('retcode', 'gdm')
    show = dict(Input = component_inputs
               ,Output = ('OK',) #[0] + ('Geom', 'Data') + write_Usertext.retvals[1:]
               )



class BakeUsertext(Tool):
    args = ('gdm', 'opts')
    component_inputs = ('go', 'Geom') + args

    write_Usertext = WriteUsertext.__call__

    def __call__(self, geom_data_map, opts):
        #type(str, dict, dict) -> int, str, dict, list  

        gdm = OrderedDict()
        for obj in geom_data_map:
            doc_obj = ghdoc.Objects.Find(obj)
            if doc_obj:
                geometry = doc_obj.Geometry
                attributes = doc_obj.Attributes
                if geometry:
                    add_to_Rhino = Rhino.RhinoDoc.ActiveDoc.Objects.Add 
                    # trying to avoid constantly switching sc.doc

                    gdm[add_to_Rhino(geometry, attributes)] = geom_data_map[obj] # The bake
        
        retcode, gdm = self.write_Usertext(gdm, opts)
        # write_data_to_USertext context switched when checking so will move
        #sc.doc = Rhino.RhinoDoc.ActiveDoc on finding Rhino objects.
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]

    retvals = ('retcode',) #'f_name', 'gdm'
    show = dict(Input = component_inputs
               ,Output = ('OK',) #bake_Usertext.retvals #[0] + ('Geom', 'Data') + bake_Usertext.retvals[1:]
               )




class ParseData(Tool):
    args = ('gdm', 'opts')
    component_inputs = ('go', 'Geom', 'Data', args[0], 'field', 'plot_max', 'plot_min', 'classes') + args[1:]

    def __call__(self, geom_data_map, opts):
        #type(str, dict, dict) -> int, str, dict, list
        # Note!  opts can be mutated.
        options = opts['options']

        field = options.field

        data = [ val[field] for val in geom_data_map.values()]
        debug('data == ' + str(data[:3]) + ' ... ' + str(data[-3:]))
        x_max = max(data) if options.plot_max is None else options.plot_max
        x_min = min(data) if options.plot_min is None else options.plot_min
        # bool(0) == False so in case x_min==0 we can't use 
        # if options.plot_min if options.plot_min else min(data) 


        no_manual_classes = (not isinstance(options.classes, list)
                            or not all( isinstance(x, Number) 
                                            for x in options.classes
                                        )
                            )

        if options.sort_data or (no_manual_classes 
           and options.class_spacing == 'equal_spacing'  ):
            # 
            gdm = OrderedDict( sorted(geom_data_map.items()
                                    ,key = lambda tupl : tupl[1][field]
                                    ) 
                            )
        else:
            gdm = geom_data_map

        #valid_class_spacers = valid_renormalisers + ['equal number of members'] 

        param={}
        param['exponential'] = param['logarithmic'] = options.base

        if no_manual_classes:
            m = options.number_of_classes
            if options.class_spacing == 'equal number of members':
                n = len(gdm)
                objs_per_class, rem = divmod(n, m)
                # assert gdm is already sorted
                classes = [ val[field] for val in 
                                    gdm.values()[objs_per_class:m*objs_per_class:objs_per_class] 
                                ]  # classes include their lower bound
                debug('num class boundaries == ' + str(len(classes)))
                debug(options.number_of_classes)
                debug(n)
                assert len(classes) + 1 == options.number_of_classes
            else: 
                classes = [
                    splines[options.class_spacing](  
                                    i
                                    ,0
                                    ,param.get(options.class_spacing, 'Not used')
                                    ,m + 1
                                    ,x_min
                                    ,x_max
                                                )     for i in range(1, m + 1) 
                                    ]
        else:
            classes = options.classes
        
        # opts['options'] = opts['options']._replace(
        #                                     classes = classes
        #                                    ,plot_max = x_max
        #                                    ,plot_min = x_min
        #                                                         )


        def re_normaliser(x, p = param.get(options.re_normaliser, 'Not used')):
            return splines[options.re_normaliser](   x
                                                    ,x_min
                                                    ,p
                                                    ,x_max
                                                    ,x_min
                                                    ,x_max
                                                )
        
        if not options.all_in_class_same_colour:
            classifier = re_normaliser
        elif options.re_normaliser:
            #'linear' # exponential, logarithmic
            def classifier(x): 

                highest_lower_bound = x_min if x < classes[0] else max(y 
                                                for y in classes + [x_min] 
                                                if y <= x                       )
                #Classes include their lower bound
                least_upper_bound = x_max if x >= classes[-1] else min(y for y in classes + [x_max] 
                                        if y > x)

                return re_normaliser (0.5*(least_upper_bound + highest_lower_bound))

        #retvals = {}

        # todo:  '{n:}'.format() everything to apply localisation, 
        # e.g. thousand seperators


        mid_points = [0.5*(x_min + min(classes))]
        mid_points += [0.5*(x + y) for (x,y) in zip(  classes[0:-1]
                                                    ,classes[1:]  
                                                )
                    ]
        mid_points += [ 0.5*(x_max + max(classes))]
        debug(mid_points)

        locale.setlocale(locale.LC_ALL,  options.locale)

        x_min_s = options.num_format.format(x_min)
        upper_s = options.num_format.format(min( classes ))
        mid_pt_s = options.num_format.format( mid_points[0] )

        legend_tags = [options.first_legend_tag_format_string.format( 
                                                                lower = x_min_s
                                                                ,upper = upper_s
                                                                ,mid_pt = mid_pt_s
                                                                    )
                                                        ]
        for lower_bound, mid_point, upper_bound in zip( 
                                            classes[0:-1]
                                            ,mid_points[1:-1]
                                            ,classes[1:]  
                                                    ):
            
            lower_s = options.num_format.format(lower_bound)
            upper_s = options.num_format.format(upper_bound)
            mid_pt_s = options.num_format.format(mid_point)

            legend_tags += [options.inner_tag_format_string.format(
                                                    lower = lower_s
                                                    ,upper = upper_s
                                                    ,mid_pt = mid_pt_s 
                                                                )
                            ]

        lower_s = options.num_format.format(max( classes ))
        x_max_s = options.num_format.format(x_max)
        mid_pt_s = options.num_format.format(mid_points[-1])

        legend_tags += [options.last_legend_tag_format_string.format( 
                                                                lower = lower_s
                                                                ,upper = x_max_s 
                                                                ,mid_pt = mid_pt_s 
                                                                    )        
                        ]                                                       

        assert len(legend_tags) == options.number_of_classes == len(mid_points)

        debug(legend_tags)

        #first_legend_tag_format_string = 'below {upper}'
        #inner_tag_format_string = '{lower} - {upper}' # also supports {mid}
        #last_legend_tag_format_string = 'above {lower}'

        #retvals['max'] = x_max = max(data)
        #retvals['min'] = x_min = min(data)

        gdm = OrderedDict(zip( geom_data_map.keys() + legend_tags 
                            ,(classifier(x) for x in data + mid_points)
                            )
                        )
        plot_min, plot_max = x_min, x_max
        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    retvals = 'retcode', 'plot_min', 'plot_max', 'gdm', 'opts', 'classes'
    show = dict(Input = component_inputs
               ,Output = ('OK',) + retvals[1:3] + ('Data', 'Geom') + retvals[3:-1]
               )

GH_Gradient_preset_names = { 0 : 'EarthlyBrown'
                            ,1 : 'Forest'
                            ,2 : 'GreyScale'
                            ,3 : 'Heat'
                            ,4 : 'SoGay'
                            ,5 : 'Spectrum'
                            ,6 : 'Traffic'
                            ,7 : 'Zebra'
                            }

class RecolourObjects(Tool):
    args = ('gdm', 'opts')
    component_inputs = ('go', 'Data', 'Geom', 'bbox') + args

    parse_data = ParseData.__call__

    def __call__(self, geom_data_map, opts):
        #type(str, dict, dict) -> int, str, dict, list
        # Note!  opts can be mutated.

        options = opts['options']
        
        field = options.field
        objs_to_parse = OrderedDict(  (k, v) for k, v in geom_data_map.items()
                                    if isinstance(v, dict) and field in v    
                                    )  # any geom with a normal gdm dict of keys / vals
        if objs_to_parse:
            ret_code, x_min, x_max, gdm_in, opts = self.parse_data(objs_to_parse, opts)
                                                                            
            debug(x_min)
            debug(x_max)
        else:
            gdm_in = {}
            x_min, x_max = options.plot_min, options.plot_max
            debug(options.plot_min)
            debug(options.plot_max)     

        debug(opts['options'].plot_min)
        debug(opts['options'].plot_max)

        objs_to_get_colour = OrderedDict( (k, v) for k, v in geom_data_map.items()
                                                if isinstance(v, Number) 
                                        )
        objs_to_get_colour.update(gdm_in)  # no key clashes possible unless some x
                                        # isinstance(x, dict) 
                                        # and isinstance(x, Number)
        if options.GH_Gradient:
            grad = getattr( GH_Gradient()
                        ,GH_Gradient_preset_names[options.GH_Gradient_preset])
            def get_colour(x):
                # Number-> Tuple(Number, Number, Number)
                # May need either rhinoscriptsyntax.CreateColor
                # or System.Drawing.Color.FromArgb and even 
                # Grasshopper.Kernel.Types.GH_Colour calling on the result to work
                # in Grasshopper
                return grad().ColourAt(linearly_interpolate( x
                                                            ,x_min
                                                            ,None
                                                            ,x_max
                                                            ,0 #0.18
                                                            ,1 #0.82
                                                            )
                                        )
        else:
            def get_colour(x):
                # Number-> Tuple(Number, Number, Number)
                # May need either rhinoscriptsyntax.CreateColor
                # or System.Drawing.Color.FromArgb and even 
                # Grasshopper.Kernel.Types.GH_Colour calling on the result to work
                # in Grasshopper
                rgb_col =  map_f_to_three_tuples( three_point_quadratic_spline
                                                ,x
                                                ,x_min
                                                ,0.5*(x_min + x_max)
                                                ,x_max
                                                ,tuple(options.rgb_min)
                                                ,tuple(options.rgb_mid)
                                                ,tuple(options.rgb_max)
                                                )
                bounded_colour = ()
                for channel in rgb_col:
                    bounded_colour += ( max(0, min(255, channel)), )
                return rs.CreateColor(bounded_colour)

        objs_to_recolour = OrderedDict( (k, v) for k, v in geom_data_map.items()
                                            if isinstance(v, Colour)  
                                    )
            
        objs_to_recolour.update( (key,  get_colour(val))
                                for key, val in objs_to_get_colour.items()
                                )


        legend_tags = OrderedDict()
        legend_first_pattern = make_regex(options.first_legend_tag_format_string)
        legend_inner_pattern = make_regex(options.inner_tag_format_string)
        legend_last_pattern = make_regex(options.last_legend_tag_format_string)

        legend_tag_patterns = (legend_first_pattern
                            ,legend_inner_pattern
                            ,legend_last_pattern
                            )


        GH_objs_to_recolour = OrderedDict()
        objects_to_widen_lines = []

        for obj, new_colour in objs_to_recolour.items():
            #debug(obj)
            if is_uuid(obj): # and is_an_obj_in_GH_or_Rhino(obj):
                target_doc = is_an_obj_in_GH_or_Rhino(obj)    
                if target_doc:
                    sc.doc = target_doc
                    if target_doc == ghdoc:
                        GH_objs_to_recolour[obj] = new_colour 
                    #elif target_doc == Rhino.RhinoDoc.ActiveDoc:
                    else:
                        rs.ObjectColor(obj, new_colour)
                        objects_to_widen_lines.append(obj)

                else:
                    raise ValueError(output( 'sc.doc == ' + str(sc.doc) 
                                            +' i.e. neither Rhinodoc.ActiveDoc '
                                            +'nor ghdoc'
                                            ,'ERROR'
                                            )
                                    )

            elif any(  bool(match(pattern, obj)) 
                        for pattern in legend_tag_patterns ):
                sc.doc = ghdoc
                legend_tags[obj] = rs.CreateColor(new_colour) # Could glitch if dupe
            else:
                raise NotImplementedError(output( 'Valid colour in Data but ' 
                                                    +'no geom obj or legend tag.'
                                                    ,'ERROR'
                                                )
                                        )

        sc.doc = ghdoc
        #[x.Geometry for x in list(GH_objs_to_recolour.keys())]
        #CustomPreview( list(GH_objs_to_recolour.keys())
        #              ,list(GH_objs_to_recolour.values())
        #              )


        keys = objects_to_widen_lines
        if keys:
            sc.doc = Rhino.RhinoDoc.ActiveDoc                             
            rs.ObjectColorSource(keys, 1)  # 1 => colour from object
            rs.ObjectPrintColorSource(keys, 2)  # 2 => colour from object
            rs.ObjectPrintWidthSource(keys, 1)  # 1 => print width from object
            rs.ObjectPrintWidth(keys, options.line_width) # width in mm
            rs.Command('_PrintDisplay _State=_On Color=Display Thickness='
                    +str(options.line_width)
                    +' _enter')
            #sc.doc.Views.Redraw()
            sc.doc = ghdoc


        # "Node in code"
        #pt = rs.CreatePoint(0, 0, 0)
        #bbox = BoundingBox(objs_to_recolour.keys, XYPlane(pt)) # BoundingBox(XYPlane

        #bbox_xmin = min(list(p)[0] for p in bbox.box.GetCorners()[:4] )
        #bbox_xmax = max(list(p)[0] for p in bbox.box.GetCorners()[:4] )
        #bbox_ymin = min(list(p)[1] for p in bbox.box.GetCorners()[:4] )
        #bbox_ymax = max(list(p)[1] for p in bbox.box.GetCorners()[:4] )

        debug(options)

        if options.legend_extent or options.bbox:
            if options.legend_extent:
                [legend_xmin
                ,legend_ymin
                ,legend_xmax
                ,legend_ymax] = options.legend_extent
                debug('legend extent == ' + str(options.legend_extent))
            elif options.bbox:
                bbox = [bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax] = options.bbox

                legend_xmin = bbox_xmin + (1 - 0.4)*(bbox_xmax - bbox_xmin)
                legend_ymin = bbox_ymin + (1 - 0.4)*(bbox_ymax - bbox_ymin)
                legend_xmax, legend_ymax = bbox_xmax, bbox_ymax
                
                debug('bbox == ' + str(bbox))


                #leg_frame = Rectangle( XYPlane(pt)
                #                      ,[legend_xmin, legend_xmax]
                #                      ,[legend_ymin, legend_ymax]
                #                      ,0
                #                      )

                plane = rs.WorldXYPlane()
                leg_frame = rs.AddRectangle( plane
                                            ,legend_xmax - legend_xmin
                                            ,legend_ymax - legend_ymin 
                                            )

                debug( 'Rectangle width * height == ' 
                       +str(legend_xmax - legend_xmin)
                       +' * '
                       +str(legend_ymax - legend_ymin)
                       )


                rs.MoveObject(leg_frame, [1.07*bbox_xmax, legend_ymin])
                #rs.MoveObject(leg_frame, [65,0]) #1.07*bbox_xmax, legend_ymin])

                # opts['options'] = opts['options']._replace(
                #                                     leg_frame = leg_frame 
                #                                                         )

                #debug(leg_frame)
                #leg_frame = sc.doc.Objects.FindGeometry(leg_frame)
                #leg_frame = sc.doc.Objects.Find(leg_frame)

        else:
            output('No legend rectangle dimensions.  ', 'INFO')
            leg_frame = None

    


        debug(leg_frame)

        #def c():
            #return GH_Colour(Color.FromArgb(r(0,255), r(0,255), r(0,255)))
            #return Color.FromArgb(r(0,255), r(0,255), r(0,255))
            #return rs.CreateColor(r(0,255), r(0,255), r(0,255))
        #tags=['Tag1', 'Tag2', 'Tag3', 'Tag4', 'Tag5']
        #colours = [c(), c(), c(), c(), c()]
        #rect = sc.doc.Objects.FindGeometry(leg_frame)
        #for k, v in legend_tags.items():
        #    Legend(Colour.FromArgb(*v), k, leg_frame)
        #Legend( [GH_Colour(Colour.FromArgb(*v)) for v in legend_tags.values()]
        #       ,list(legend_tags.keys()) 
        #       ,leg_frame
        #       )
        gdm = GH_objs_to_recolour
        leg_cols = list(legend_tags.values())
        leg_tags = list(legend_tags.keys())


        sc.doc =  ghdoc # type: ignore
        sc.doc.Views.Redraw()

        retcode = 0

        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    retvals = 'retcode', 'gdm', 'leg_cols', 'leg_tags', 'leg_frame', 'opts'
    show = dict(Input = component_inputs    
               ,Output = ('OK', 'Geom', 'Data') + retvals[1:]
               )
          # To recolour GH Geom with a native Preview component



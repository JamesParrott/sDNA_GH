#! Grasshopper Python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

from email.mime import base
import os
import logging
import subprocess
import itertools
import re
from collections import OrderedDict

from time import asctime
import csv
from numbers import Number
import locale

import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import GhPython
from System.Drawing import Color as Colour #.Net / C# Class
                #System is also available in IronPython, but not System.Drawing
from Grasshopper.GUI.Gradient import GH_Gradient
from Grasshopper.Kernel.Parameters import (Param_Arc
                                          ,Param_Curve
                                          ,Param_Boolean
                                          ,Param_Geometry
                                          ,Param_String
                                          ,Param_FilePath
                                          ,Param_Guid
                                          ,Param_Integer
                                          ,Param_Line
                                          ,Param_Rectangle
                                          ,Param_Colour
                                          ,Param_Number
                                          ,Param_ScriptVariable
                                          ,Param_GenericObject
                                          ,Param_Guid
                                          )

from .helpers.funcs import (make_regex
                           ,splines
                           ,linearly_interpolate
                           ,map_f_to_three_tuples
                           ,three_point_quad_spline
                           )
from .skel.basic.ghdoc import ghdoc
from .skel.tools.helpers.funcs import is_uuid
from .skel.tools.helpers.checkers import (get_OrderedDict
                                         ,get_obj_keys
                                         ,write_obj_val
                                         ,get_sc_doc_of_obj
                                         ,get_sc_doc_of_group
                                         ,get_all_groups
                                         ,get_members_of_a_group
                                         )
from .skel.tools.runner import RunnableTool                                         
from .skel.add_params import ToolWithParams, ParamInfo
from .options_manager import (namedtuple_from_dict
                             ,error_raising_sentinel_factory
                             ,Sentinel
                             ,get_opts_dict
                             )
from .pyshp_wrapper import (get_filename
                           ,get_points_from_obj
                           ,write_iterable_to_shp
                           ,get_fields_recs_and_shapes
                           ,objs_maker_factory
                           ,get_Rhino_objs
                           )
from .logging_wrapper import class_logger_factory
from .gdm_from_GH_Datatree import (make_gdm
                                  ,is_shape
                                  ,override_gdm
                                  )



logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
ClassLogger = class_logger_factory(logger = logger, module_name = __name__)







class sDNA_GH_Tool(RunnableTool, ToolWithParams, ClassLogger):

    factories_dict = dict(go = Param_Boolean
                        #  ,OK = Param_ScriptVariable
                         ,file = Param_FilePath
                        #  ,Geom = Param_ScriptVariable
                        #  ,Data = Param_ScriptVariable
                        #  ,leg_cols = Param_ScriptVariable
                        #  ,leg_tags = Param_ScriptVariable
                        #  ,leg_frame = Param_ScriptVariable
                        #  ,gdm = Param_ScriptVariable
                        #  ,opts = Param_ScriptVariable
                         ,config = Param_FilePath
                        #  ,l_metas = Param_ScriptVariable
                         ,field = Param_String
                        #  ,fields = Param_ScriptVariable
                        #  ,plot_min = Param_ScriptVariable
                        #  ,plot_max = Param_ScriptVariable
                        #  ,class_bounds = Param_ScriptVariable
                        #  ,abbrevs = Param_ScriptVariable
                        #  ,sDNA_fields = Param_ScriptVariable
                        #  ,bbox = Param_ScriptVariable
                         #,Param_GenericObject
                         #,Param_Guid
                         )

    type_hints_dict = dict(Geom = GhPython.Component.GhDocGuidHint())

    access_methods_dict = dict(Data = 'tree')

    @classmethod
    def params_list(cls, names):
        return [ParamInfo(factory = cls.factories_dict.get(name
                                                          ,Param_ScriptVariable
                                                          )
                         ,NickName = name
                         ,Access = 'tree' if name == 'Data' else 'list'
                         ) for name in names                            
               ]

class sDNA_ToolWrapper(sDNA_GH_Tool):
    # In addition to the 
    # other necessary attributes of sDNA_GH_Tool, instances know their own name
    # and nick name, in self.nick_name
    # self.tool_name.  When the instance is called, the version of sDNA
    # is looked up in opts['metas'], from its args.
    # 
    opts = get_opts_dict(metas = dict(sDNA = ('sDNAUISpec', 'runsdnacommand'))
                        ,options = dict(
                            sDNAUISpec = Sentinel('Module not imported yet')
                           ,run_sDNA = Sentinel('Module not imported yet')
                           ,prepped_shp_suffix = "_prepped"
                           ,output_shp_suffix = "_output" 
                           ,dot_shp = '.shp'
                           # file extensions are actually optional in PyShp, 
                           # but just to be safe and future proof
                           ,python_exe = r'C:\Python27\python.exe' 
# Default installation path of Python 2.7.3 release (32 bit ?) 
# http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi copied from sDNA manual:
# https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/installation_usage.html 
                           )
                        )


    def update_tool_opts_and_syntax(self, opts = None):
        if opts is None:
            opts = self.opts
        metas = opts['metas']
        nick_name = self.nick_name

        sDNAUISpec = opts['options'].sDNAUISpec
        sDNA = opts['metas'].sDNA
        self.sDNA = sDNA

        tool_opts = opts.setdefault(nick_name, {})
        if self.tool_name != nick_name:
            tool_opts = opts.setdefault(self.tool_name, {})
        # Note, this is intended to do nothing if nick_name == self.tool_name

        self.logger.debug(tool_opts)
        try:
            sDNA_Tool = getattr(sDNAUISpec, self.tool_name)()
        except:
            msg =   ('No tool called '
                    +self.tool_name
                    +' found in '
                    +sDNAUISpec.__file__
                    +'.  Rename tool_name or change sDNA version.  '
                    )
            self.error(msg)
            raise ValueError(msg)
                            
        self.input_spec = sDNA_Tool.getInputSpec()
        self.get_syntax = sDNA_Tool.getSyntax     

        defaults_dict = { varname : default for (varname
                                                ,displayname
                                                ,datatype
                                                ,filtr
                                                ,default
                                                ,required
                                                ) in self.input_spec  
                        }            
        if sDNA in tool_opts:
            tool_opts_dict = defaults_dict.update( tool_opts[sDNA]._asdict() ) 
        else:
            tool_opts_dict = defaults_dict
        namedtuple_class_name = (nick_name + '_'
                                +(self.tool_name if self.tool_name != nick_name
                                                 else '') + '_'
                                +os.path.basename(sDNAUISpec.__file__).rpartition('.')[0]
                                )
        self.logger.debug(namedtuple_class_name)
        tool_opts[sDNA] = namedtuple_from_dict(tool_opts_dict
                                              ,namedtuple_class_name
                                              ,strict = True
                                              ) 
        self.tool_opts = tool_opts
        self.opts = opts


    def __init__(self, tool_name, nick_name, opts = None):

        if opts is None:
            opts = self.opts  # the class property
        self.debug('Initialising Class.  Creating Class Logger.  ')
        self.tool_name = tool_name
        self.nick_name = nick_name
        self.update_tool_opts_and_syntax(opts)



    
    
    component_inputs = ('file', 'config') 


    def __call__(self # the callable instance / func, not the GH component.
                ,f_name
                ,opts
                ):
        #type(Class, str, dict, namedtuple) -> Boolean, str
        if opts is None:
            opts = self.opts  # the class property

        sDNA = opts['metas'].sDNA
        sDNAUISpec = opts['options'].sDNAUISpec
        run_sDNA = opts['options'].run_sDNA 



        if not hasattr(sDNAUISpec, self.tool_name): 
            raise ValueError(self.tool_name + 'not found in ' + sDNA[0])
        options = opts['options']

        if self.sDNA != opts['metas'].sDNA:
            self.update_tool_opts_and_syntax(opts)

        dot_shp = options.dot_shp

        input_file = self.tool_opts[sDNA].input
        

        #if (not isinstance(input_file, str)) or not isfile(input_file): 
        if (isinstance(f_name, str) and os.path.isfile(f_name)
            and f_name.rpartition('.')[2] in [dot_shp[1:],'dbf','shx']):  
            input_file = f_name

        self.logger.debug(input_file)
         


        output_file = self.tool_opts[sDNA].output
        if output_file == '':
            output_suffix = options.output_shp_suffix
            if self.tool_name == 'sDNAPrepare':
                output_suffix = options.prepped_shp_suffix
            output_file = input_file.rpartition('.')[0] + output_suffix + dot_shp

        output_file = get_filename(output_file, options)

        input_args = self.tool_opts[sDNA]._asdict()
        input_args.update(input = input_file, output = output_file)
        syntax = self.get_syntax(input_args)

        f_name = output_file

        command =   (options.python_exe 
                    + ' -u ' 
                    + '"' 
                    + os.path.join(  os.path.dirname(sDNAUISpec.__file__)
                            ,'bin'
                            ,syntax['command'] + '.py'  
                            ) 
                    + '"'
                    + ' --im ' + run_sDNA.map_to_string( syntax["inputs"] )
                    + ' --om ' + run_sDNA.map_to_string( syntax["outputs"] )
                    + ' ' + syntax["config"]
                    )
        self.logger.info('sDNA command run = ' + command)

        output_lines = subprocess.check_output(command)
        retcode = 0

        self.logger.info(output_lines)


        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    
    retvals = 'retcode', 'f_name'
    component_outputs = ('file',) # retvals[-1])



def get_objs_and_OrderedDicts(all_objs_getter = get_Rhino_objs
                             ,group_getter = get_all_groups
                             ,group_objs_getter = get_members_of_a_group
                             ,OrderedDict_getter = get_OrderedDict()
                             ,obj_type_checker = is_shape
                             ,shp_type = 'POLYLINEZ'
                             ,include_groups = False
                             ):
    #type(function, function, function) -> function
    def generator():
        #type( type[any]) -> list, list
        #
        # Groups first search.  If a special Usertext key on member objects 
        # is used to indicate groups, then an objects first search 
        # is necessary instead, to test every object for membership
        # and track the groups yielded to date, in place of group_getter
        objs_in_any_group = []

        if include_groups:
            groups = group_getter()
            for group in groups:
                objs = group_objs_getter(group)
                if ( objs and
                    any(obj_type_checker(x, shp_type) 
                                                for x in objs) ):                                                 
                    objs_in_any_group += objs
                    d = {}
                    for obj in objs:
                        d.update(OrderedDict_getter(obj))
                    yield group, d

        objs = all_objs_getter(shp_type)
        for obj in objs:
            if ((not include_groups) or 
                 obj not in objs_in_any_group):
                d = OrderedDict_getter(obj)
                yield str(obj), d
                # We take the str of Rhino geom obj reference (its uuid).
                # This is because Grasshopper changes uuids between 
                # connected components, even of 
                # more static Rhino objects, reducing hte usefulness of
                # the original uuid.  
                # Previously was:
                # yield obj, d
        return 

    return generator()


class RhinoObjectsReader(sDNA_GH_Tool):

    opts = get_opts_dict(metas = {}
                        ,options = dict(shape_type = 'POLYLINEZ'
                                       ,merge_subdicts = True
                                       ,include_groups = False
                                       )
                        )

    component_inputs = ('config',) 
    
    def __call__(self, opts = None, gdm = None):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts
        self.debug('Creating Class Logger.  ')

        options = opts['options']


        sc.doc = Rhino.RhinoDoc.ActiveDoc 
        
        #rhino_groups_and_objects = make_gdm(get_objs_and_OrderedDicts(options))
        tmp_gdm = gdm if gdm else OrderedDict()

            
        gdm = make_gdm(get_objs_and_OrderedDicts(get_Rhino_objs
                                                ,get_all_groups
                                                ,get_members_of_a_group
                                                ,lambda *args, **kwargs : {} 
                                                ,is_shape
                                                ,options.shape_type
                                                ,options.include_groups
                                                ) 
                       )
        # lambda : {}, as Usertext is read elsewhere, in read_Usertext



        self.logger.debug('First objects read: \n' 
                         +'\n'.join( str(x) 
                                     for x in gdm.keys()[:3]
                                   )
                         )
        if len(gdm) > 0:
            self.debug('type(gdm[0]) == ' + type(gdm.keys()[0]).__name__ )
        if tmp_gdm:
            gdm = override_gdm(gdm
                              ,tmp_gdm
                              ,options.merge_subdicts
                              )
        self.logger.debug('after override ....Last objects read: \n'
                         +'\n'.join( str(x) 
                                     for x in gdm.keys()[-3:]
                                   )
                         )

        sc.doc = ghdoc 
        self.logger.debug('retvals == ' + str(self.retvals))
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)


    retvals = ('gdm',)
    component_outputs = ('Geom', ) 


class UsertextReader(sDNA_GH_Tool):
    opts = get_opts_dict(metas = {}
                        ,options = {}
                        )
    component_inputs = ('Geom',) 

    def __call__(self, gdm):
        #type(str, dict, dict) -> int, str, dict, list

        self.debug('Starting read_Usertext..  Creating Class logger. ')
        self.debug('type(gdm) == ' + str(type(gdm)))
        self.debug('gdm == ' + str(gdm))


        read_Usertext_as_tuples = get_OrderedDict()
        for obj in gdm:
            gdm[obj].update(read_Usertext_as_tuples(obj))

        # get_OrderedDict() will get Usertext from both the GH and Rhino docs
        # switching the target to RhinoDoc if needed, hence the following line 
        # is important:
        sc.doc = ghdoc  
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)


    retvals = ('gdm',)
    component_outputs = ('Data', ) 



   


class ShapefileWriter(sDNA_GH_Tool):

    opts = get_opts_dict(metas = {}
                        ,options = dict(shape_type = 'POLYLINEZ'
                                       ,input_key_str = 'sDNA input name={name} type={fieldtype} size={size}'
                                       ,dot_shp = '.shp'
                                       ,path = __file__
                                       ,output_shp = os.path.join( os.path.dirname(__file__)
                                                                 ,'tmp.shp'
                                                                 )
                                       )
                        )

    component_inputs = ('file', 'Geom', 'Data', 'config') 

    def __call__(self, f_name, gdm, opts = None):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts
        options = opts['options']
        self.debug('Creating Class Logger.  ')


        shp_type = options.shape_type            


        format_string = options.input_key_str
        pattern = make_regex( format_string )

        def pattern_match_key_names(x):
            #type: (str)-> object #re.MatchObject

            return re.match(pattern, x) 


        def get_list_of_lists_from_tuple(obj):

            target_doc = get_sc_doc_of_obj(obj)    
            if target_doc:
                sc.doc = target_doc
                if is_shape(obj, shp_type):
                    return [get_points_from_obj(obj, shp_type)]
                else:
                    return []      
                #elif is_a_group_in_GH_or_Rhino(obj):
            else:
                target_doc = get_sc_doc_of_group(obj)    
                if target_doc:
                    sc.doc = target_doc                  
                    return [get_points_from_obj(y, shp_type) 
                            for y in get_members_of_a_group(obj)
                            if is_shape(y, shp_type)]
                else:
                    return []

        def shape_IDer(obj):
            return obj #tupl[0].ToString() # uuid

        def find_keys(obj):
            return gdm[obj].keys() #tupl[1].keys() #rs.GetUserText(x,None)

        def get_data_item(obj, key):
            return gdm[obj][key] #tupl[1][key]

        if not f_name:  
            if (options.output_shp and 
                os.path.isdir( os.path.dirname( options.output_shp )
                             ) 
               ):   
                
                f_name = options.output_shp
            else:
                f_name = options.path.rpartition('.')[0]
                f_name += options.dot_shp
                            # file extensions are actually optional in PyShp, 
                            # but just to be safe and future proof we remove
                            # '.3dm'                                        
        self.logger.debug(f_name)

        (retcode
        ,f_name
        ,fields
        ,gdm) = write_iterable_to_shp(
                                 my_iterable = gdm
                                ,shp_file_path = f_name 
                                ,shape_mangler = get_list_of_lists_from_tuple 
                                ,shape_IDer = shape_IDer
                                ,key_finder = find_keys 
                                ,key_matcher = pattern_match_key_names 
                                ,value_demangler = get_data_item 
                                ,shape_code = shp_type 
                                ,options = options
                                ,field_names = None 
                                )
        
        # get_list_of_lists_from_tuple() will 
        # switch the targeted file to RhinoDoc if needed, hence the following line 
        # is important:
        sc.doc = ghdoc  
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = 'retcode', 'f_name', 'gdm'
    component_outputs =  ('file',) 
               


class ShapefileReader(sDNA_GH_Tool):

    opts = get_opts_dict(metas = {}
                        ,options = dict(new_geom = True
                                       ,dot_shp = '.shp'
                                       ,uuid_field = 'Rhino3D_'
                                       ,del_shp = False)
                        )
                        
    component_inputs = ('file', 'Geom') # existing 'Geom', otherwise new 
                                        # objects need to be created

    def __call__(self, f_name, gdm, opts = None):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts
        options = opts['options']
        self.debug('Creating Class Logger.  Reading shapefile... ')

        (shp_fields
        ,recs
        ,shapes
        ,bbox ) = get_fields_recs_and_shapes( f_name )

        self.debug('gdm == ' + str(gdm))

        self.debug('recs[0].as_dict() == ' + str(recs[0].as_dict()))

        if not recs:
            self.logger.warning('No data read from Shapefile ' + f_name + ' ')
            return 1, f_name, gdm, None    
            
        if not shapes:
            self.logger.warning('No shapes in Shapefile ' + f_name + ' ')
            if not gdm:
                self.logger.warning('No Geom objects in Geom Data Mapping.  ')
            return 1, f_name, gdm, None


        if not bbox:
            self.logger.warning('No Bounding Box in Shapefile.  '
                   + f_name 
                   + ' '
                   +'Supply bbox manually or create rectangle to plot legend.'
                   )
            

        fields = [ x[0] for x in shp_fields ]

        self.logger.debug('options.uuid_field in fields == ' 
                         +str(options.uuid_field in fields)
                         )
        self.logger.debug(fields) 



        self.logger.debug('Testing existing geom data map.... ')
        if isinstance(gdm, dict) and len(gdm) == len(recs):
            # an override for different number of overrided geom objects
            # to shapes/recs opens a large a can of worms.  Unsupported.

            self.logger.debug('Geom data map matches shapefile.  ')

            shapes_to_output = list(gdm.keys()) # Dict view in Python 3
        elif options.new_geom:
                    #shapes_to_output = ([shp.points] for shp in shapes )
            
            objs_maker = objs_maker_factory() 
            shapes_to_output = (objs_maker(shp.points) for shp in shapes )
        else:
            # Unsupported until can round trip uuid through sDNA 
            # objs_maker = get_shape_file_rec_ID(options.uuid_field) 
            # # key_val_tuples
            # i.e. if options.uuid_field in fields but also otherwise
            msg =   ('Geom data map and shapefile have unequal'
                    +' lengths len(gdm) == ' + str(len(gdm))
                    +' len(recs) == ' + str(len(recs))
                    +' (or invalid gdm), and new_geom'
                    +' == False'
                    )
            self.logger.error(msg)
            raise ValueError(msg)
   

        shp_file_gen_exp  = itertools.izip(shapes_to_output
                                          ,(rec.as_dict() for rec in recs)
                                          )
      
        sc.doc = Rhino.RhinoDoc.ActiveDoc
        gdm = make_gdm(shp_file_gen_exp)
        sc.doc = ghdoc 
        
        dot_shp = options.dot_shp
        csv_f_name = f_name.rpartition('.')[0] + dot_shp + '.names.csv'
        #sDNA_fields = {}
        if os.path.isfile(csv_f_name):
            f = open(csv_f_name, 'rb')
            f_csv = csv.reader(f)
            #sDNA_fields = [OrderedDict( (line[0], line[1]) for line in f_csv )]
            abbrevs = [line[0] for line in f_csv ]


        self.logger.debug('bbox == ' + str(bbox))

        if options.del_shp and os.path.isfile(f_name):
            os.remove(f_name)  # TODO: Fix, currently Win32 error

        retcode = 0

        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)


    retvals = 'retcode', 'gdm', 'abbrevs', 'fields', 'bbox'
    component_outputs = ('Geom', 'Data') + retvals[1:]
               




class UsertextWriter(sDNA_GH_Tool):

    opts = get_opts_dict(metas = {}
                        ,options = dict(uuid_field = 'Rhino3D_'
                                       ,output_key_str = 'sDNA output={name} run time={datetime}'
                                       ,overwrite_UserText = True
                                       ,max_new_keys = 10
                                       ,dupe_key_suffix = ''
                                       ,suppress_overwrite_warning = False
                                       )
                        )
                        

    component_inputs = ('Geom', 'Data')


    def __call__(self, gdm, opts):
        #type(str, dict, dict) -> int, str, dict, list
        if opts is None:
            opts = self.opts        
        options = opts['options']

        date_time_of_run = asctime()
        self.debug('Creating Class logger at: ' + str(date_time_of_run))


        def write_dict_to_UserText_on_obj(d, rhino_obj):
            #type(dict, str) -> None
            if not isinstance(d, dict):
                return
            
            #if is_an_obj_in_GH_or_Rhino(rhino_obj):
                # Checker switches GH/ Rhino context
            
            target_doc = get_sc_doc_of_obj(rhino_obj)    
            if target_doc:
                sc.doc = target_doc        
                existing_keys = get_obj_keys(rhino_obj)
                if options.uuid_field in d:
                    obj = d.pop( options.uuid_field )
                
                for key in d:

                    s = options.output_key_str
                    UserText_key_name = s.format(name = key
                                                ,datetime = date_time_of_run
                                                )
                    
                    if not options.overwrite_UserText:

                        for i in range(0, options.max_new_keys):
                            tmp = UserText_key_name 
                            tmp += options.dupe_key_suffix.format(i)
                            if tmp not in existing_keys:
                                break
                        UserText_key_name = tmp
                    else:
                        if not options.suppress_overwrite_warning:
                            self.logger.warning( "UserText key == " 
                                        + UserText_key_name 
                                        +" overwritten on object with guid " 
                                        + str(rhino_obj)
                                        )
                    write_obj_val(rhino_obj, UserText_key_name, str( d[key] ))
            else:
                self.logger.info('Object: ' 
                         + key[:10] 
                         + ' is neither a curve nor a group. '
                         )

        for key, val in gdm.items():
            #if is_a_curve_in_GH_or_Rhino(key):
            target_doc = get_sc_doc_of_obj(key)    
            if target_doc:
                sc.doc = target_doc          
                group_members = [key]
            else:
                target_doc = get_sc_doc_of_group(key)    
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

        sc.doc = ghdoc  
        
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)
    
    retvals = ()
    component_outputs = () 
               



class UsertextBaker(sDNA_GH_Tool):

    opts = get_opts_dict(metas = {}
                        ,options = dict()
                        )
                        
    def __init__(self, *args, **kwargs):
        self.debug('Initialising Class.  Creating Class Logger. ')
        self.write_Usertext = UsertextWriter(*args, **kwargs)
    
    component_inputs = ('Geom', 'Data')

    def __call__(self, gdm, opts):
        #type(str, dict, dict) -> int, str, dict, list  

        tmp_gdm = OrderedDict()

        add_to_Rhino = Rhino.RhinoDoc.ActiveDoc.Objects.Add 


        for obj in gdm:
            doc_obj = ghdoc.Objects.Find(obj)
            if doc_obj:
                geometry = doc_obj.Geometry
                attributes = doc_obj.Attributes
                if geometry:
                    # trying to avoid constantly switching sc.doc

                    # The actual bake
                    tmp_gdm[add_to_Rhino(geometry, attributes)] = gdm[obj] 

        
        self.write_Usertext(tmp_gdm, opts)
        gdm = tmp_gdm
        # write_data_to_USertext context switched when checking so will move
        #sc.doc = Rhino.RhinoDoc.ActiveDoc on finding Rhino objects.
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = ('gdm',) #'f_name', 'gdm'
    component_outputs =  ('Geom',) 
               




class DataParser(sDNA_GH_Tool):


    opts = get_opts_dict(metas = {}
                        ,options = dict(field = 'BtEn'
                                       ,plot_min = Sentinel('plot_min is automatically calculated by sDNA_GH unless overridden.  ')
                                       ,plot_max = Sentinel('plot_max is automatically calculated by sDNA_GH unless overridden.  ')
                                       ,re_normaliser = 'linear'
                                       ,sort_data = False
                                       ,number_of_classes = 8
                                       ,class_bounds = [Sentinel('class_bounds is automatically calculated by sDNA_GH unless overridden.  ')]
                                       # e.g. [2000000, 4000000, 6000000, 8000000, 10000000, 12000000]
                                       ,class_spacing = 'equal number of members'
                                       ,base = 10 # for Log and exp
                                       ,colour_as_class = False
                                       ,locale = '' # '' => User's own settings.  Also in DataParser
                                       # e.g. 'fr', 'cn', 'pl'. IETF RFC1766,  ISO 3166 Alpha-2 code
                                       ,num_format = '{:.5n}'
                                       ,first_leg_tag_str = 'below {upper}'
                                       ,gen_leg_tag_str = '{lower} - {upper}'
                                       ,last_leg_tag_str = 'above {lower}'
                                       )
                        )
                        

    def __init__(self):
        self.debug('Initialising Class.  Creating Class Logger. ')
        self.component_inputs = ('Geom', 'Data', 'field', 'plot_max'
                                ,'plot_min', 'class_bounds')
    #
    # Geom is essentially unused in this function, except that the legend tags
    # are appended to it, to colour them in exactly the same way as the 
    # objects.
    #
    def __call__(self, gdm, opts):
        #type(str, dict, dict) -> int, str, dict, list
        # Note!  opts can be mutated.
        if opts is None:
            opts = self.opts
        self.debug('Starting ParseData tool.  ')
        options = opts['options']

        field = options.field

        data = [ val[field] for val in gdm.values()]
        self.logger.debug('data == ' + str(data[:3]) + ' ... ' + str(data[-3:]))
        x_max = max(data) if isinstance(options.plot_max, Sentinel) else options.plot_max
        x_min = min(data) if isinstance(options.plot_min, Sentinel) else options.plot_min
        # bool(0) == False so in case x_min==0 we can't use 
        # if options.plot_min if options.plot_min else min(data) 


        no_manual_classes = (not isinstance(options.class_bounds, list)
                            or not all( isinstance(x, Number) 
                                            for x in options.class_bounds
                                        )
                            )

        print('no_manual_classes == '+ str(no_manual_classes))

        if options.sort_data or (no_manual_classes 
           and options.class_spacing == 'equal number of members'  ):
            # 
            gdm = OrderedDict( sorted(gdm.items()
                                     ,key = lambda tupl : tupl[1][field]
                                     ) 
                            )


        param={}
        param['exponential'] = param['logarithmic'] = options.base

        if no_manual_classes:
            m = options.number_of_classes
            if options.class_spacing == 'equal number of members':
                n = len(gdm)
                objs_per_class = n // m
                # assert gdm is already sorted
                class_bounds = [ val[field] for val in 
                                  gdm.values()[objs_per_class:m*objs_per_class:objs_per_class] 
                                ]  # classes include their lower bound
                self.logger.debug('num class boundaries == ' + str(len(class_bounds)))
                self.logger.debug(options.number_of_classes)
                self.logger.debug(n)
                assert len(class_bounds) + 1 == options.number_of_classes

                msg = 'x_min == ' + str(x_min) + '\n'
                msg += 'class bounds == ' + str(class_bounds) + '\n'
                msg += 'x_max == ' + str(x_max)
                logger.debug(msg)

            else: 
                class_bounds = [
                    splines[options.class_spacing](i
                                                  ,0
                                                  ,param.get(options.class_spacing
                                                            ,'Not used'
                                                            )
                                                  ,m + 1
                                                  ,x_min
                                                  ,x_max
                                                  )     
                    for i in range(1, m + 1) 
                               ]
        else:
            class_bounds = options.class_bounds


        def re_normaliser(x, p = param.get(options.re_normaliser, 'Not used')):
            return splines[options.re_normaliser](x
                                                 ,x_min
                                                 ,p
                                                 ,x_max
                                                 ,x_min
                                                 ,x_max
                                                 )
        
        if not options.colour_as_class:
            classifier = re_normaliser
        elif options.re_normaliser:
            #'linear' # exponential, logarithmic
            def classifier(x): 

                highest_lower_bound = x_min if x < class_bounds[0] else max(y 
                                                for y in class_bounds + [x_min] 
                                                if y <= x                       )
                #Classes include their lower bound
                least_upper_bound = x_max if x >= class_bounds[-1] else min(y for y in class_bounds + [x_max] 
                                        if y > x)

                return re_normaliser (0.5*(least_upper_bound + highest_lower_bound))




        mid_points = [0.5*(x_min + min(class_bounds))]
        mid_points += [0.5*(x + y) for (x,y) in zip(class_bounds[0:-1]
                                                   ,class_bounds[1:]  
                                                   )
                      ]
        mid_points += [ 0.5*(x_max + max(class_bounds))]
        self.logger.debug(mid_points)

        locale.setlocale(locale.LC_ALL,  options.locale)

        x_min_s = options.num_format.format(x_min) 
        upper_s = options.num_format.format(min( class_bounds ))
        mid_pt_s = options.num_format.format( mid_points[0] )

        #e.g. first_leg_tag_str = 'below {upper}'

        legend_tags = [options.first_leg_tag_str.format(lower = x_min_s
                                                       ,upper = upper_s
                                                       ,mid_pt = mid_pt_s
                                                       )
                      ]
        for lower_bound, mid_point, upper_bound in zip(class_bounds[0:-1]
                                                      ,mid_points[1:-1]
                                                      ,class_bounds[1:]  
                                                      ):
            
            lower_s = options.num_format.format(lower_bound)
            upper_s = options.num_format.format(upper_bound)
            mid_pt_s = options.num_format.format(mid_point)
            # e.g. gen_leg_tag_str = '{lower} - {upper}' # also supports {mid}
            legend_tags += [options.gen_leg_tag_str.format(lower = lower_s
                                                          ,upper = upper_s
                                                          ,mid_pt = mid_pt_s 
                                                          )
                            ]

        lower_s = options.num_format.format(max( class_bounds ))
        x_max_s = options.num_format.format(x_max)
        mid_pt_s = options.num_format.format(mid_points[-1])

        # e.g. last_leg_tag_str = 'above {lower}'
        legend_tags += [options.last_leg_tag_str.format(lower = lower_s
                                                       ,upper = x_max_s 
                                                       ,mid_pt = mid_pt_s 
                                                       )        
                        ]                                                       

        assert len(legend_tags) == options.number_of_classes == len(mid_points)

        self.logger.debug(legend_tags)



        gdm = OrderedDict(zip( gdm.keys() + legend_tags 
                            ,(classifier(x) for x in data + mid_points)
                            )
                        )
        plot_min, plot_max = x_min, x_max
        
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = 'plot_min', 'plot_max', 'gdm'
    component_outputs = retvals[:2] + ('Data', 'Geom') + retvals[2:]
               


class ObjectsRecolourer(sDNA_GH_Tool):

    opts = get_opts_dict(metas = {}
                        ,options = dict(field = 'BtEn'
                                       ,Col_Grad = False
                                       ,Col_Grad_num = 5
                                       ,rgb_max = (155, 0, 0) #990000
                                       ,rgb_min = (0, 0, 125) #3333cc
                                       ,rgb_mid = (0, 155, 0) # guessed
                                       ,line_width = 4 # milimetres? 
                                       ,first_leg_tag_str = 'below {upper}'
                                       ,gen_leg_tag_str = '{lower} - {upper}'
                                       ,last_leg_tag_str = 'above {lower}'
                                       ,leg_extent = Sentinel('leg_extent is automatically calculated by sDNA_GH unless overridden.  ')
                                       # [xmin, ymin, xmax, ymax]
                                       ,bbox = Sentinel('bbox is automatically calculated by sDNA_GH unless overridden.  ') 
                                       # [xmin, ymin, xmax, ymax]

                                       )
                        )
                        
    def __init__(self, *args, **kwargs):
        self.debug('Initialising Class.  Creating Class Logger. ')
        self.parse_data = DataParser(*args, **kwargs)
        self.GH_Gradient_preset_names = {0 : 'EarthlyBrown'
                                        ,1 : 'Forest'
                                        ,2 : 'GreyScale'
                                        ,3 : 'Heat'
                                        ,4 : 'SoGay'
                                        ,5 : 'Spectrum'
                                        ,6 : 'Traffic'
                                        ,7 : 'Zebra'
                                        }

    
    component_inputs = ('plot_min', 'plot_max', 'Data', 'Geom', 'bbox', 'field')

    def __call__(self, gdm, opts, plot_min, plot_max, bbox):
        #type(str, dict, dict) -> int, str, dict, list
        # Note!  opts can be mutated.
        if opts is None:
            opts = self.opts
        options = opts['options']
        
        field = options.field
        objs_to_parse = OrderedDict(  (k, v) for k, v in gdm.items()
                                    if isinstance(v, dict) and field in v    
                                    )  # any geom with a normal gdm dict of keys / vals
        if objs_to_parse or plot_min is None or plot_max is None:
            x_min, x_max, gdm_in, opts = self.parse_data(objs_to_parse, opts)
                                                                            
        else:
            self.debug('Skipping parsing')
            gdm_in = {}
            x_min, x_max = plot_min, plot_max

        self.logger.debug('x_min == ' + str(x_min))
        self.logger.debug('x_max == ' + str(x_max))

        objs_to_get_colour = OrderedDict( (k, v) for k, v in gdm.items()
                                                if isinstance(v, Number) 
                                        )
        objs_to_get_colour.update(gdm_in)  # no key clashes possible unless some x
                                        # isinstance(x, dict) 
                                        # and isinstance(x, Number)
        if options.Col_Grad:
            grad = getattr( GH_Gradient()
                        ,self.GH_Gradient_preset_names[options.Col_Grad_num])
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
                rgb_col =  map_f_to_three_tuples( three_point_quad_spline
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

        objs_to_recolour = OrderedDict( (k, v) for k, v in gdm.items()
                                            if isinstance(v, Colour)  
                                    )
            
        objs_to_recolour.update( (key,  get_colour(val))
                                for key, val in objs_to_get_colour.items()
                                )


        legend_tags = OrderedDict()
        legend_first_pattern = make_regex(options.first_leg_tag_str)
        legend_inner_pattern = make_regex(options.gen_leg_tag_str)
        legend_last_pattern = make_regex(options.last_leg_tag_str)

        legend_tag_patterns = (legend_first_pattern
                            ,legend_inner_pattern
                            ,legend_last_pattern
                            )


        GH_objs_to_recolour = OrderedDict()
        objects_to_widen_lines = []


        for obj, new_colour in objs_to_recolour.items():
            #self.logger.debug(obj)
            if is_uuid(obj): 
                target_doc = get_sc_doc_of_obj(obj)    

                if target_doc:
                    sc.doc = target_doc
                    if target_doc == ghdoc:
                        GH_objs_to_recolour[obj] = new_colour 
                    #elif target_doc == Rhino.RhinoDoc.ActiveDoc:
                    else:
                        rs.ObjectColor(obj, new_colour)
                        objects_to_widen_lines.append(obj)

                else:

                    msg =   ('sc.doc == ' + str(sc.doc) 
                            +' i.e. neither Rhinodoc.ActiveDoc '
                            +'nor ghdoc'
                            )
                    self.logger.error(msg)
                    raise ValueError(msg)

            elif any(  bool(re.match(pattern, obj))
                        for pattern in legend_tag_patterns ):
                sc.doc = ghdoc
                legend_tags[obj] = rs.CreateColor(new_colour) # Could glitch if dupe
            else:
                msg = 'Valid colour in Data but no geom obj or legend tag.'
                self.logger.error(msg)
                raise NotImplementedError(msg)

        sc.doc = ghdoc



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




        if (bbox or not isinstance(options.leg_extent, (Sentinel, type(None)))
                 or not isinstance(options.bbox, (Sentinel, type(None)))):
            if not isinstance(options.leg_extent, Sentinel) and options.leg_extent:
                [legend_xmin
                ,legend_ymin
                ,legend_xmax
                ,legend_ymax] = options.leg_extent
                self.logger.debug('legend extent == ' + str(options.leg_extent))
            else: 
                if bbox:
                    self.logger.debug('Using bbox from args')
                    [bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax] = bbox
                elif not isinstance(options.bbox, Sentinel):
                    self.logger.debug('Using options.bbox override. ')
                    bbox = [bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax] = options.bbox

                legend_xmin = bbox_xmin + (1 - 0.4)*(bbox_xmax - bbox_xmin)
                legend_ymin = bbox_ymin + (1 - 0.4)*(bbox_ymax - bbox_ymin)
                legend_xmax, legend_ymax = bbox_xmax, bbox_ymax
                
                self.logger.debug('bbox == ' + str(bbox))


            plane = rs.WorldXYPlane()
            leg_frame = rs.AddRectangle( plane
                                        ,legend_xmax - legend_xmin
                                        ,legend_ymax - legend_ymin 
                                        )

            self.logger.debug('Rectangle width * height == ' 
                                +str(legend_xmax - legend_xmin)
                                +' * '
                                +str(legend_ymax - legend_ymin)
                                )


            rs.MoveObject(leg_frame, [1.07*bbox_xmax, legend_ymin])


        else:
            self.logger.info('No legend rectangle dimensions.  ')
            leg_frame = None

    


        self.logger.debug(leg_frame)


        gdm = GH_objs_to_recolour
        leg_cols = list(legend_tags.values())
        leg_tags = list(legend_tags.keys())


        sc.doc =  ghdoc 
        sc.doc.Views.Redraw()

        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)
    
    retvals = 'gdm', 'leg_cols', 'leg_tags', 'leg_frame', 'opts'
    component_outputs = ('Geom', 'Data') + retvals[1:]
          # To recolour GH Geom with a native Preview component


class sDNA_GeneralDummyTool(sDNA_GH_Tool):
    component_inputs = ('tool',)

    def __call__(self, *args, **kwargs):
        raise NotImplementedError('this function should never run '
                                 +' (there may be a problem with sDNA_General). '
                                 )
    component_outputs = ()

class Load_Config_File(sDNA_GH_Tool):
    component_inputs = ('config',)

    def __call__(self, *args, **kwargs):
        retcode = 0
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)
    retvals = ('retcode',)
    component_outputs = ()
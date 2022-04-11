import sys, logging

from sDNA_GH.sDNA_GH.custom.options_manager import no_name_clashes

if sys.version < '3.3':
    from collections import Hashable, Iterable, MutableMapping
else:
    from collections.abc import Hashable, Iterable, MutableMapping

import GhPython
from System import SizeF, PointF   # .Net Classes, e.g. via Iron Python.

from ..custom.helpers.funcs import (ghdoc
                                   ,no_name_clashes
                                   )
from ..launcher import Output, Debugger
from ..custom.tools import Tool
from ..setup import tools_dict

logger = logging.getLogger('sDNA_GH').addHandler(logging.NullHandler())
#logger = logging.getLogger(__name__)

output = Output(tmp_logs = [], logger = logger)
debug = Debugger(output)

def make_new_component(name
                      ,category
                      ,subcategory
                      ,launcher_code
                      ,this_comp
                      ,position
                      ):
    comp = GhPython.Component.ZuiPythonComponent()
    
    #comp.CopyFrom(this_comp)
    sizeF = SizeF(*position)

    comp.Attributes.Pivot = PointF.Add(comp.Attributes.Pivot, sizeF)
    

    comp.Code = launcher_code
    #comp.NickName = name
    comp.Params.Clear()
    comp.IsAdvancedMode = True
    comp.Category = category
    comp.SubCategory = subcategory

    GH_doc = this_comp.OnPingDocument()
    GH_doc.AddObject(comp, False)



def validate_name_map(name_map, known_tool_names):
    #type(dict, list) -> bool
    if not isinstance(name_map, dict):
        msg = ('Name map is of type: ' + str(type(name_map))
              +'but is required to be a dictionary.  '
              )
        logging.error(msg)
        raise TypeError(msg)
                                                            # No nick names allowed that are 
                                                            # a tool's full / real name.
    nickname_clashes = [name for name in known_tool_names if name in name_map]
    if nickname_clashes:
        msg = ('Nick names in name map clash with known tool names: ' 
              +' '.join(nickname_clashes)
              )
        logging.error(msg)
        raise ValueError(msg)
    else:
        logging.debug('No clashes found in name_map with known tool names.'
                     +' Good job! '
                     )

    
    names_and_nicknames = known_tool_names + list(name_map.keys())
    def points_to_valid_tools(tool_names):
        if not isinstance(tool_names, list):
            tool_names = [tool_names]
        return all(name in names_and_nicknames for name in tool_names)
    invalid_name_map_vals = {key : val for key, val in name_map._asdict().items()
                                        if not points_to_valid_tools(val)}

    if invalid_name_map_vals:
        msg = ('Invalid name_map entries: ' 
              +'\n'.join([k + (v if not isinstance(v, list) else
                               ' '.join([n for n in v if not points_to_valid_tools(n)])
                              )
                          for k, v in invalid_name_map_vals.items()
                         ])
              )
        logging.error(msg)
        raise ValueError(msg)
    else:
        logging.info('Name_map links all point to known names or other name_map links. Cycles not checked. ','INFO')

    return True



class ReturnComponentNames(Tool): # (name, name_map, inst, retvals = None): 

    args = ('opts',)
    component_inputs = ('go',) + args

    def __call__(self, local_opts, **kwargs):
        
        name_map = local_opts['metas'].name_map
        names = list(tools_dict.keys())
        sDNAUISpec = local_opts['options'].sDNAUISpec
        names += [Tool.__name__ for Tool in sDNAUISpec.get_tools()]

        retcode = 0 if validate_name_map(name_map, names) else 1
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]

    retvals = 'retcode', 'names'
    
    show = dict(Input = component_inputs
               ,Output = ('OK',) + retvals[1:]
               )


class Buildcomponents(Tool): 
    args = ('launcher_code', 'plug_in', 'component_names', 'opts', 'd_h', 'w')
    component_inputs = ('go',) + args[1:-2] + ('name_map', 'categories')

    def __call__(self, code, plug_in_name, names, opts_at_call, d_h = None, w = None):
        #type(str, dict) -> None
        # = (kwargs[k] for k in self.args)
        d_h = 175 if d_h is None else d_h
        w = 800 if w is None else w
        
        while (isinstance(code, Iterable) 
               and not isinstance(code, str)):
            code = code[0]

        global module_opts
        module_opts['options']._replace(auto_get_Geom = False
                                ,auto_read_Usertext = False
                                ,auto_write_new_Shp_file = False
                                ,auto_read_Shp = False
                                ,auto_plot_data = False
                                )

        metas = opts_at_call['metas']

        sDNAUISpec = opts_at_call['options'].sDNAUISpec
        categories = {Tool.__name__ : Tool.category for Tool in sDNAUISpec.get_tools()}
        categories.update(metas.categories._asdict())

        name_map = metas.name_map._asdict()

        #retcode, names  = return_component_names(opts_at_call)
        #names now from param input

        nicknameless_names = [name for name in names if name not in name_map.values()]

        for i, name in enumerate(set(list(name_map.keys()) + nicknameless_names)):
            if name_map.get(name, name) not in categories:
                raise ValueError(output('No category for ' + name, 'ERROR'))
            else:
                i *= d_h
                position = [200 + (i % w), 550 + 220*(i // w)]
                comp = GhPython.Component.ZuiPythonComponent()
    
                #comp.CopyFrom(this_comp)
                sizeF = SizeF(*position)

                comp.Attributes.Pivot = PointF.Add(comp.Attributes.Pivot, sizeF)
                

                comp.Code = code
                comp.NickName = name
                comp.Name = name
                comp.Params.Clear()
                comp.IsAdvancedMode = True
                comp.Category = plug_in_name #'sDNA'
                if name_map.get(name, name) in categories:
                    comp.SubCategory = categories[name_map.get(name, name)]

                GH_doc = ghdoc.Component.Attributes.Owner.OnPingDocument()
                GH_doc.AddObject(comp, False)

        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    retvals = ('retcode',)


    show = dict(Input = component_inputs
               ,Output = ('OK',) + retvals[1:]    
               )
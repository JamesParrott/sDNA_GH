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
from ..__main__ import (support_component_names
                       ,special_names
                       ,return_component_names
                       )

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






class ReturnComponentNames(Tool): # (name, name_map, inst, retvals = None): 

    args = ('opts',)
    component_inputs = ('go',) + args

    def __call__(self, local_opts):
        
        sDNAUISpec = local_opts['options'].sDNAUISpec
        name_map = local_opts['metas'].name_map

        sDNA_tool_names = [Tool.__name__ for Tool in sDNAUISpec.get_tools()]
        names_lists = [support_component_names, special_names, sDNA_tool_names]
        names_list = [x for z in names_lists for x in z]
        clash_test_passed = no_name_clashes( name_map,  names_lists )


        if not clash_test_passed:
            output('Component name/abbrev clash.  Rename component or abbreviation. ','WARNING') 
            output('name_map == ' + str(name_map),'INFO') 
            output('names_lists == ' + str(names_lists),'INFO') 
            output('names_list == ' + str(names_list),'INFO') 
        else:
            output('Component name/abbrev test passed. ','INFO') 

        assert clash_test_passed
                                                                # No nick names allowed that are 
                                                                # a tool's full / real name.
        names_and_nicknames = names_list + list(name_map._fields) #name_map.keys()   
        def points_to_valid_tools(tool_names):
            if not isinstance(tool_names, list):
                tool_names = [tool_names]
            return all(name in names_and_nicknames for name in tool_names)
        invalid_name_map_vals = {key : val for key, val in name_map._asdict().items()
                                           if not points_to_valid_tools(val)}
        # TODO.  Lowest priority: Check there are no non-trivial cycles.  this is only devtool validation code - 
        #        not likely a user will expect
        #        correct results if they alter name_map to include a non-trivial cycle.
        if invalid_name_map_vals:
            output('Invalid name_map entries: ' 
                  +'\n'.join([k + (v if not isinstance(v, list) else
                                   ' '.join([n for n in v if not points_to_valid_tools(n)])
                                  )
                              for k, v in invalid_name_map_vals.items()])
                   ,'CRITICAL'
                   )
        else:
            output('Name_map validated successfully.  ','INFO')
        assert not invalid_name_map_vals
        #return special_names + support_component_names + sDNA_tool_names, None, None, None

        names = ([name for name in names_list 
                           if name not in name_map] #.values()] 
                     + list(name_map._fields) #keys())
                    )

        #return 0, None, {}, ret_names, #names_list
        retcode = 0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]

    retvals = 'retcode', 'names'
    
    show = dict(Input = component_inputs
               ,Output = ('OK',) + retvals[1:]
               )


class Buildcomponents(Tool): 
    args = ('launcher_code', 'opts')
    component_inputs = ('go',) + args[1:] + ('name_map', 'categories')

    def __call__(self, code, opts_at_call):
        #type(str, dict) -> None

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

        retcode, names  = return_component_names(opts_at_call)

        nicknameless_names = [name for name in names if name not in name_map.values()]

        for i, name in enumerate(set(list(name_map.keys()) + nicknameless_names)):
            if name_map.get(name, name) not in categories:
                raise ValueError(output('No category for ' + name, 'ERROR'))
            else:
                i *= 175
                w = 800
                #make_new_component(  name
                #                    ,'sDNA'
                #                    ,categories[name_map.get(name, name)]
                #                    ,code
                #                    ,this_comp
                #                    [i % w, i // w]
                #                    )

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
                comp.Category = 'sDNA'
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
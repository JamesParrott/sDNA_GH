#! Grasshopper Python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import logging

from ..custom.skel.tools.name_mapper import validate_name_map
from ..custom.tools import sDNA_GH_Tool
from ..setup import tools_dict
from ..custom.skel.builder import BuildComponents

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
#logger = logging.getLogger(__name__)



class ReturnToolNames(sDNA_GH_Tool): # (name, name_map, inst, retvals = None): 

    def __init__(self):
        self.component_inputs = ()

    def __call__(self, opts):
        
        #logger.debug(opts)
        name_map = opts['metas'].name_map
        names = list(tools_dict.keys())
        sDNAUISpec = opts['options'].sDNAUISpec
        names += [Tool.__name__ for Tool in sDNAUISpec.get_tools()]

        retcode = 0 if validate_name_map(name_map, names) else 1
        logger.debug('Returning from ReturnComponentNames.  ')

        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = 'retcode', 'names'

    component_outputs = retvals[1:]
               


class sDNA_GH_Builder(sDNA_GH_Tool):
    builder = BuildComponents()
    get_names = ReturnToolNames()
    component_inputs = 'launcher_code', 'plug_in_name'

    def __call__(self, launcher_code, plug_in_name, opts):
        
        logger.debug('opts.keys() == ' + str(opts.keys()))

        metas = opts['metas']
        sDNAUISpec = opts['options'].sDNAUISpec

        opts['options'] = opts['options']._replace(
                                                 auto_get_Geom = False
                                                ,auto_read_Usertext = False
                                                ,auto_write_new_Shp_file = False
                                                ,auto_read_Shp = False
                                                ,auto_plot_data = False
                                                )


        categories = {Tool.__name__ : Tool.category for Tool in sDNAUISpec.get_tools()}
        categories.update(metas.categories._asdict())

        name_map = metas.name_map

        retcode, names = self.get_names(opts)

        nicknameless_names = [name for name in names 
                            if all(name != var and name not in var 
                                            for var in name_map.values()
                                    )
                             ]
        component_names = list(name_map.keys()) + nicknameless_names
        logger.debug('list(name_map.keys()) == ' + str(list(name_map.keys())))                           
        logger.debug('nicknameless_names == ' + str(list(nicknameless_names)))                           

        logger.debug('component_names == ' + str(component_names))                           
        logger.debug('type(component_names) == ' + str(type(component_names)))
        unique_component_names = set(component_names)
        logger.debug('unique_component_names == ' + str(unique_component_names))

        logger.debug('names == ' + str(names))


        if retcode == 0:
            retcode, names_built = self.builder(code = launcher_code
                                               ,plug_in_name = plug_in_name
                                               ,names = unique_component_names
                                               ,name_map = name_map
                                               ,categories = categories
                                               ,d_h = None
                                               ,w = None
                                               )
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = ('retcode', 'names_built')
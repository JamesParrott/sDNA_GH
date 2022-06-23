#! /usr/bin/awk NR==3
# -*- coding: utf-8 -*-
# This module requires Grasshopper Python (Rhino3D)

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
__version__ = '0.02'

import logging

from ..custom.skel.tools import name_mapper
from ..custom import tools
from ..custom.skel.tools import runner
from .. import main
from ..custom.skel import builder

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
#logger = logging.getLogger(__name__)



class ToolNamesGetter(tools.sDNA_GH_Tool): # (name, name_map, inst, retvals = None): 

    """ Gets list of Tool Names from tools_dict and sDNA.  """

    def __init__(self):
        self.component_inputs = ()

    def __call__(self, opts):
        
        #logger.debug(opts)
        name_map = opts['metas'].name_map
        
        names = list(runner.tools_dict.keys())
        sDNAUISpec = opts['options'].sDNAUISpec
        names += [Tool.__name__ for Tool in sDNAUISpec.get_tools()]

        retcode = 0 if name_mapper.validate_name_map(name_map, names) else 1
        logger.debug('Returning from ReturnComponentNames.  ')

        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = 'retcode', 'names'

    component_outputs = retvals[1:]
               


class sDNA_GH_Builder(tools.sDNA_GH_Tool):
    builder = builder.ComponentsBuilder()
    get_names = ToolNamesGetter()
    component_inputs = 'launcher_code', 'plug_in_name'

    def __call__(self, launcher_code, plug_in_name, opts):
        
        logger.debug('opts.keys() == %s ' % opts.keys())

        
        tools.import_sDNA(opts)
        sDNAUISpec = opts['options'].sDNAUISpec

        opts['options'] = opts['options']._replace(auto_get_Geom = False
                                                  ,auto_read_Usertext = False
                                                  ,auto_write_Shp = False
                                                  ,auto_read_Shp = False
                                                  ,auto_plot_data = False
                                                  )

        opts['metas'] = opts['metas']._replace(show_all = False)
        
        metas = opts['metas']

        categories = {Tool.__name__ : Tool.category for Tool in sDNAUISpec.get_tools()}
        categories.update(metas.categories)

        name_map = main.default_name_map # metas.name_map

        retcode, names = self.get_names(opts)

        nicknameless_names = [name for name in names 
                            if all(name != var and name not in var 
                                            for var in name_map.values()
                                    )
                             ]
        component_names = list(name_map.keys()) + nicknameless_names
        logger.debug('list(name_map.keys()) == %s ' % list(name_map.keys()))                         
        logger.debug('nicknameless_names == %s ' % list(nicknameless_names))                           

        logger.debug('component_names == %s ' % component_names)                           
        logger.debug('type(component_names) == %s ' % type(component_names))
        unique_component_names = set(component_names)
        logger.debug('unique_component_names == %s ' % unique_component_names)

        logger.debug('names == %s ' % names)


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
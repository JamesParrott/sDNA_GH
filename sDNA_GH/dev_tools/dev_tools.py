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
__version__ = '2.5.1'

import os
import logging

from ..custom.skel.tools import name_mapper
from ..custom import tools
from ..custom.skel.tools import runner
from ..custom.skel.basic.ghdoc import ghdoc
from .. import launcher
from ..custom.skel import builder

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
#logger = logging.getLogger(__name__)

try:
    basestring #type: ignore
except NameError:
    basestring = str


class ToolNamesGetter(tools.sDNA_GH_Tool): # (name, name_map, inst, retvals = None): 

    """ Gets list of Tool Names from tools_dict and sDNA.  """

    def __init__(self, opts):
        super(ToolNamesGetter, self).__init__(opts)
        self.component_inputs = ()

    def __call__(self, opts):
        self.debug('Starting class logger. ')

        #self.logger.debug(opts)
        name_map = opts['metas'].name_map
        
        names = list(runner.tools_dict.keys())
        sDNAUISpec = opts['options'].sDNAUISpec
        names += [Tool.__name__ for Tool in sDNAUISpec.get_tools()]

        retcode = 0 if name_mapper.validate_name_map(name_map, names) else 1
        self.logger.debug('Returning from ReturnComponentNames.  ')

        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = 'retcode', 'names'

    component_outputs = retvals[1:]


plug_in_sub_folder = launcher.PACKAGE_NAME
plug_in_name = launcher.PLUG_IN_NAME

class sDNA_GH_Builder(tools.sDNA_GH_Tool):

    component_inputs = ()

    def __call__(self, opts):
        self.debug('Starting class logger. ')
        self.logger.debug('opts.keys() == %s ' % opts.keys())


        user_objects_location = os.path.join(launcher.REPOSITORY
                                            ,plug_in_sub_folder
                                            ,builder.ghuser_folder
                                            )


        sDNAUISpec, _ = tools.import_sDNA(opts
                                         ,logger = self.logger
                                         ) 

        opts['options'] = opts['options']._replace(auto_get_Geom = False
                                                  ,auto_read_User_Text = False
                                                  ,auto_write_Shp = False
                                                  ,auto_read_Shp = False
                                                  ,auto_plot_data = False
                                                  )

        opts['metas'] = opts['metas']._replace(show_all = False)
        
        metas = opts['metas']

        categories = {Tool.__name__ : Tool.category for Tool in sDNAUISpec.get_tools()}
        categories.update(metas.categories)

        name_map = metas.DEFAULT_NAME_MAP # metas.name_map

        names = list(runner.tools_dict.keys()) # Non sDNA tools.
        self.logger.debug('names == %s ' % names)

        nicknameless_names = [name 
                              for name in names 
                              if name not in name_map.values()
                             ]
        component_names = list(name_map.keys()) + nicknameless_names
        unique_component_names = set(component_names)

        if 'Build_components' in unique_component_names:
            unique_component_names.remove('Build_components')
            # Build components (and any instance of this class) assumes it is 
            # in the project repo, not in a user install.

        self.logger.debug('unique_component_names == %s ' % unique_component_names)

        kwargs = dict(user_objects_location = user_objects_location
                     ,add_to_canvas = False
                     ,move_user_objects = True
                     ,category_abbrevs = metas.category_abbrevs
                     ,plug_in_name = launcher.PLUG_IN_NAME #'sDNA'
                     ,plug_in_sub_folder = plug_in_sub_folder # 'sDNA_GH'
                     )

        names_built = tools.build_sDNA_GH_components(
                                       component_names = unique_component_names
                                      ,name_map = name_map
                                      ,categories = categories
                                      ,overwrite = True
                                      ,**kwargs
                                      )

        sDNA_names_built = tools.build_missing_sDNA_components(opts = opts
                                                              ,**kwargs
                                                              )

        if sDNA_names_built:
            names_built += sDNA_names_built

        retcode = 0

        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = ('retcode', 'names_built')
    component_outputs = ()
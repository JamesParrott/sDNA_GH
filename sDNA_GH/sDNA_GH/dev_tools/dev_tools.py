#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import logging

from ..custom.skel.basic.smart_comp import custom_retvals
from ..custom.skel.tools.name_mapper import validate_name_map
from ..launcher import Output, Debugger
from ..custom.tools import sDNA_GH_Tool
from ..setup import tools_dict
from ..custom.skel.builder import BuildComponents

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
#logger = logging.getLogger(__name__)

output = Output(tmp_logs = [], logger = logger)
debug = Debugger(output)


class ReturnComponentNames(sDNA_GH_Tool): # (name, name_map, inst, retvals = None): 

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

        return custom_retvals(self.retvals
                             ,sources = []
                             ,return_locals = True
                             )


    retvals = 'retcode', 'names'

    component_outputs = retvals[1:]
               


class sDNA_GH_Builder(sDNA_GH_Tool):
    builder = BuildComponents()
    get_names = ReturnComponentNames()
    args = ('launcher_code', 'plug_in', 'component_names', 'opts', 'd_h', 'w')
    component_inputs = ('go',) + args[1:-2] + ('name_map', 'categories')

    def __call__(self, code, plug_in_name, opts_at_call, d_h = None, w = None):
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

        names = self.get_names()

        self.builder(code
                    ,plug_in_name
                    ,names
                    ,name_map
                    ,categories
                    ,d_h = None
                    ,w = None
                    )
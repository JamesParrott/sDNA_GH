#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import logging

from ..custom.skel.basic.smart_comp import custom_retvals
from ..custom.skel.tools.name_mapper import validate_name_map
from ..launcher import Output, Debugger
from ..custom.tools import Tool
from ..setup import tools_dict

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
#logger = logging.getLogger(__name__)

output = Output(tmp_logs = [], logger = logger)
debug = Debugger(output)


class ReturnComponentNames(Tool): # (name, name_map, inst, retvals = None): 

    def __init__(self):
        self.component_inputs = ()

    def __call__(self, opts):
        
        name_map = opts['metas'].name_map
        names = list(tools_dict.keys())
        sDNAUISpec = opts['options'].sDNAUISpec
        names += [Tool.__name__ for Tool in sDNAUISpec.get_tools()]

        retcode = 0 if validate_name_map(name_map, names) else 1
        logger.debug('From ReturnComponentNames : \n\n')

        return custom_retvals(self.retvals
                             ,sources = []
                             ,return_locals = True
                             )


    retvals = 'retcode', 'names'
    @property
    def input_params(self):
        return self.component_inputs
    output_params = retvals[1:]
               



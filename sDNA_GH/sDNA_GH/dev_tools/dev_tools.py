#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import logging
logger = logging.getLogger('sDNA_GH').addHandler(logging.NullHandler())




from ..custom.skel.tools.name_mapper import validate_name_map
from ..launcher import Output, Debugger
from ..custom.tools import Tool
from ..setup import tools_dict

logger = logging.getLogger('sDNA_GH').addHandler(logging.NullHandler())
#logger = logging.getLogger(__name__)

output = Output(tmp_logs = [], logger = logger)
debug = Debugger(output)


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



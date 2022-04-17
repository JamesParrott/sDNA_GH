#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'


import sys
from collections import namedtuple
from abc import abstractmethod
if sys.version < '3.4':
    from abc import ABCMeta
    class ABC:
        __metaclass__ = ABCMeta
else:
    from abc import ABC

from Grasshopper.Kernel.Parameters import Param_ScriptVariable
                                          

from ...basic.smart_comp import get_args_spec
from ...add_params import ParamInfo
   

class ToolABC(ABC):    
                    #Template for tools that can be run by run_tools()
                    # Subclass of this is only enforced if enforceABC == True,
                    # to permit running of regular
                    # functions with attributes via ducktyping check
                    # in quacks_like

    @abstractmethod
    def __call__(self, *args):
        assert len(args) == len(self.args)
        '''  Main tool function'''
        retcode=0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    @property
    @abstractmethod
    def retvals(self): 
        return ('retcode',) 
                 # strings of variable names inside __call__, to be used 
                 # keys in vals_dict.  show['Outputs'] defines the required 
                 # output Param names on the 
                 # GH component

    @property
    @abstractmethod
    def show(self):
        return dict(Inputs = ()   # Input  / Output Params to display.  Extras 
                   ,Outputs = ()  # e.g. to go into **kwargs and thence options
                                  # and ommissions with default values are
                                  # supported
                   )

    anon_pos_args = None    # Names of params that aren't named in the argspec
                            # to put in *args
    anon_kwargs = None      # Names of params that aren't named in the argspec
                            # to put in **kwargs






class Tool(ToolABC):
    @property
    def args(self):
        return tuple(get_args_spec(self).args)


    def __str__(self):
        s = self.tool_name if hasattr(self, 'tool_name') else ''
        s += ' an instance of ' + self.__class__.__name__ +'.  '
        return s

    @property
    def component_inputs(self):
        return self.args

    @property
    def component_outputs(self):
        return self.retvals

    factories_dict = {}

    def params_list(self, names):
        return [ParamInfo(factory = self.factories_dict.get(name
                                                           ,Param_ScriptVariable
                                                           )
                         ,NickName = name
                         ) for name in names
               ]

    @property
    def input_params(self):
        return self.params_list(self.component_inputs)
    
    @property
    def output_params(self):
        return self.params_list(self.component_outputs)

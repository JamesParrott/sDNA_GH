#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys
from abc import abstractmethod
if sys.version < '3.4':
    from abc import ABCMeta
    class ABC:
        __metaclass__ = ABCMeta
else:
    from abc import ABC
   

class ToolABC(ABC):    
                    #Template for tools that can be run by run_tools()
                    # Subclass of this is only enforced if enforceABC == True,
                    # to permit running of regular
                    # functions with attributes via ducktyping check
                    # in quacks_like
    @abstractmethod
    def args(self):
        return ()   # Only the order need correspond to 
                    # __call__'s args. The names can be 
                    # different.  The ones in the args tuple
                    # are used as keys in vals_dict.  
                    # show['Inputs'] defines the
                    # input Param names of the component 

    @abstractmethod
    def __call__(self, *args):
        assert len(args) == len(self.args)
        '''  Main tool function'''
        retcode=0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    @abstractmethod
    def retvals(self): 
        return ('retcode',) 
                 # strings of variable names inside __call__, to be used 
                 # keys in vals_dict.  show['Outputs'] defines the required 
                 # output Param names on the 
                 # GH component

    @abstractmethod
    def show(self):
        return dict(Inputs = ()
                   ,Outputs = ()
                   )

class Tool(ToolABC):
    def __str__(self):
        s = self.tool_name if hasattr(self, 'tool_name') else ''
        s += ' an instance of ' + self.__class__ +'.  '
        return s

#! /usr/bin/awk NR==3
# -*- coding: utf-8 -*-
# This module requires Grasshopper Python (Rhino3D)

# MIT License

# Copyright (c) [2021] [Cardiff University, a body incorporated
# by Royal Charter and a registered charity (number:
# 1136855) whose administrative offices are at 7th floor 30-
# 36 Newport Road, University CF24 0DE, Wales, UK]

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


__authors__ = {'James Parrott', 'Crispin Cooper'}
__version__ = '3.0.0'


import logging
from collections import OrderedDict
import abc


from ..basic import smart_comp
from ..basic.quacks_like import quacks_like


if hasattr(abc, 'ABC'):
    ABC = abc.ABC
else:
    class ABC(object):
        __metaclass__ = abc.ABCMeta
abstractmethod = abc.abstractmethod

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

tools_dict = OrderedDict()


class RunnableTool(ABC):    
    """ Template for tools that can be run by run_tools()
    Subclass of this is only enforced if enforceABC is True,
    to permit running of regular
    functions with attributes via duck-typing check
    in quacks_like
    """

    @abstractmethod
    def __call__(self, *args):
        '''  Main tool function'''
        retcode=0
        locs = locals().copy()
        return [locs[retval] for retval in self.retvals]
    
    @property
    @abstractmethod
    def retvals(self): 
        return ('retcode',) 
    # strings of variable names inside __call__, will be used 
    # keys in vals_dict.  ToolwithParamsABC.output_params
    # defines the corresponding 
    # output Param names on the 
    # GH component (not necessarily the same, e.g. file is a 
    # reserved name, so we use it as an alias for f_name)




def run_tools(tools
             ,args_dict
             ,enforceABC = False):  
    #type(list[Tool], dict)-> dict

    if not isinstance(tools, list):
        tools = list(tools)
    invalid_tools = [tool for tool in tools 
                          if not ( isinstance(tool, RunnableTool) 
                                   or ((not enforceABC) and
                                   quacks_like(RunnableTool, tool))
                                 )
                    ]
    if invalid_tools:
        msg = 'Invalid tool(s) == %s ' % invalid_tools
        logger.error(msg)
        raise ValueError(msg)



    vals_dict = args_dict

    


    logger.debug(tools)                            
    for tool in tools:
        logger.debug(tool)



        anon_pos_args = getattr(tool, 'anon_pos_args', [])
        anon_kwargs = getattr(tool, 'anon_kwargs', [])
        logger.debug('vals_dict.keys() == %s ' % vals_dict.keys())

        pos_args, input_kw_args = smart_comp.prepare_args(
                                     function = tool
                                    ,params_dict = vals_dict
                                    ,anon_pos_args = anon_pos_args
                                    ,anon_kwargs = anon_kwargs
                                    ,prioritise_kwargs = True
                                    ,add_unrecognised_names_to_pos_args = False
                                    )
        
        retvals = tool(*pos_args, **input_kw_args)


        vals_dict.update( zip(tool.retvals, retvals) )
        retcode = vals_dict.get('retcode', 0)

        logger.debug(' return code == %s ' % retcode)
        if retcode != 0:
            msg = ('Tool ' + tool.__class__.__name__
                  +' exited with status code %s ' % retcode
                  )
            logger.error(msg)
            raise Exception(msg)

    return vals_dict     
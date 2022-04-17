#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import logging
from collections import OrderedDict

from .helpers.classes import ToolABC
from ..basic.smart_comp import prepare_args
from ..basic.quacks_like import quacks_like
from .helpers.funcs import tool_name

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

tools_dict = OrderedDict()

def run_tools(tools
             ,args_dict
             ,enforceABC = False):  
    #type(list[Tool], dict)-> dict

    if not isinstance(tools, list):
        tools = list(tools)
    invalid_tools = [tool for tool in tools 
                          if not ( isinstance(tool, ToolABC) 
                                   or ((not enforceABC) and
                                   quacks_like(ToolABC, tool))
                                 )
                    ]
    if invalid_tools:
        msg = 'Invalid tool(s) == ' + str(invalid_tools)
        logger.error(msg)
        raise ValueError(msg)
    
    opts = args_dict['opts']
    metas = opts['metas']
    name_map = metas.name_map #._asdict()



    vals_dict = args_dict 


    logger.debug(tools)                            
    for tool in tools:
        logger.debug(tool)


        #inputs = [vals_dict.get(input, None) for input in tool.args]
        #retvals = tool( *inputs)



        # inputs = {input : vals_dict[input] for input in tool.args 
        #                                    if input in vals_dict
        #          }

        anon_pos_args = getattr(tool, 'anon_pos_args', None)
        anon_kwargs = getattr(tool, 'anon_kwargs', None)

        pos_args, input_kw_args = prepare_args(function = tool
                                              ,params_dict = vals_dict
                                              ,anon_pos_args = anon_pos_args
                                              ,anon_kwargs = anon_kwargs
                                              ,prioritise_kwargs = True
                                              )
        
        retvals = tool(*pos_args, **input_kw_args)

        vals_dict.update( zip(tool.retvals, retvals) )
        vals_dict.setdefault( 'file'
                            , vals_dict.get('f_name')
                            )
        vals_dict['OK'] = (vals_dict.get('retcode', 0) == 0)

        retcode = vals_dict['retcode']
        logger.debug(' return code == ' + str(retcode))
        if retcode != 0:
            msg = ('Tool ' + tool_name(tool) 
                  +' exited with status code ' + str(retcode))
            logger.error(msg)
            raise Exception(msg)

    return vals_dict     
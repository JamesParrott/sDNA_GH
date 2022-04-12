#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import logging
from collections import OrderedDict

from .helpers.classes import ToolABC
from .helpers.quacks_like import quacks_like
from .helpers.funcs import tool_name

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())



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
    name_map = metas.name_map._asdict()



    vals_dict = args_dict 


    logger.debug(tools)                            
    for tool in tools:
        logger.debug(tool)


        #inputs = [vals_dict.get(input, None) for input in tool.args]
        #retvals = tool( *inputs)
        inputs = {input : vals_dict[input] for input in tool.args 
                                           if input in vals_dict
                 }
        
        retvals = tool(**inputs)

        vals_dict.update( OrderedDict(zip(tool.retvals, retvals)) )
        vals_dict.setdefault( 'file'
                            , vals_dict.get('f_name')
                            )
        vals_dict['OK'] = (vals_dict['retcode'] == 0)

        retcode = vals_dict['retcode']
        logger.debug(' return code == ' + str(retcode))
        if retcode != 0:
            msg = ('Tool ' + tool_name(tool) 
                  +' exited with status code ' + str(retcode))
            logger.error(msg)
            raise Exception(msg)

    return vals_dict     
#! Grasshopper Python (Rhino3D)
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'


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
                    #Template for tools that can be run by run_tools()
                    # Subclass of this is only enforced if enforceABC is True,
                    # to permit running of regular
                    # functions with attributes via ducktyping check
                    # in quacks_like

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
                 # strings of variable names inside __call__, to be used 
                 # keys in vals_dict.  show['Outputs'] defines the required 
                 # output Param names on the 
                 # GH component




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


        #inputs = [vals_dict.get(input, None) for input in tool.args]
        #retvals = tool( *inputs)



        # inputs = {input : vals_dict[input] for input in tool.args 
        #                                    if input in vals_dict
        #          }

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
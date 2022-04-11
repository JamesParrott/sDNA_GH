import sys, logging
from collections import OrderedDict
from abc import abstractmethod
if sys.version < '3.4':
    from abc import ABCMeta
    class ABC:
        __metaclass__ = ABCMeta
else:
    from abc import ABC

import sys
from .quacks_like import quacks_like


logger = logging.getLogger(__name__)



   

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


def tool_name(tool):
    #type(type[any] / function)->str
    if hasattr(tool, 'tool_name'):
        return tool.tool_name
    elif hasattr(tool, 'name'):
        return tool.name
    elif hasattr(tool,'__name__'):
        return tool.__name__  
    elif hasattr(tool,'func_name'):
        return tool.func_name
    elif hasattr(tool,'__qualname__'):
        return tool.__qualname__  
    else:
        return tool.__class__.__name__


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
#! Grasshopper Python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys
import logging
from abc import abstractmethod
if sys.version < '3.4':
    from abc import ABCMeta
    class ABC(object):
        __metaclass__ = ABCMeta
else:
    from abc import ABC

import GhPython
import Grasshopper.Kernel 
from Grasshopper.Kernel.Parameters import Param_ScriptVariable

from . import update_params


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class ParamInfoABC(ABC):
    @abstractmethod
    def make(self):
        """Makes instance of a type in Grasshopper.Kernel.Parameters """


class ParamInfo(dict, ParamInfoABC):
    access_methods = ('item', 'list', 'tree')
    def __init__(self
                ,NickName
                ,factory = None 
                ,Name = None
                ,Description = None
                ,Access = 'list'
                ,Optional = True
                ,TypeHint = None 
                ,**kwargs
                ):
        if isinstance(factory, str):
            if not factory.startswith('Param_'):
                factory = 'Param_' + factory
            factory = getattr(Grasshopper.Kernel.Parameters, factory, None)
        if factory is None:
            factory = Param_ScriptVariable
            logger.debug('Using factory Param_ScriptVariable for param : ' + NickName)
        self.factory = factory
        if TypeHint is None and factory == Param_ScriptVariable:
            TypeHint = GhPython.Component.GhDocGuidHint()
        self.TypeHint = TypeHint

        if Name is None:
            Name = NickName
        if Description is None:
            Description = NickName
        if Access in self.access_methods:
            Access = getattr(Grasshopper.Kernel.GH_ParamAccess, Access)
        elif Access not in [getattr(Grasshopper.Kernel.GH_ParamAccess, x) 
                            for x in self.access_methods]:
            logger.warning('Unrecognised access method : ' + str(Access))
        super(ParamInfo, self).__init__(NickName = NickName
                                        ,Name = Name
                                        ,Description = Description
                                        ,Access = Access
                                        ,Optional = Optional
                                        ,**kwargs
                                        )
    def make(self):
        Param = self.factory() #**self)
        if self.TypeHint:
            Param.TypeHint = self.TypeHint
        for attr in self: # class inherits from dict
            setattr(Param, attr, self[attr])
        return Param


class ToolwithParamsABC(ABC):

    @abstractmethod
    def input_params(self):
        """ List of input ParamInfo instances """

    @abstractmethod
    def output_params(self):
        """ List of output ParamInfo instances """

def param_info_list_maker(param_names
                         ,factories = {}
                         ,TypeHints = {}
                         ,access_methods = {}
                         ):
    if isinstance(param_names, str):
        param_names = [param_names]
    return [ParamInfo(NickName = name
                     ,factory = factories.get(name
                                             ,Param_ScriptVariable
                                             )
                     ,TypeHint = TypeHints.get(name
                                              ,None
                                              )
                     ,Access = access_methods.get(name, 'list')
                     ) for name in param_names                            
           ]

class ToolWithParams(ToolwithParamsABC):

    factories_dict = {}

    type_hints_dict = {}

    access_methods_dict = {}

    def params_list(self, names):
        return param_info_list_maker(param_names = names
                                    ,factories = self.factories_dict
                                    ,TypeHints = self.type_hints_dict
                                    ,access_methods = self.access_methods_dict
                                    )


    component_inputs = ()

    component_outputs = ()

    def input_params(self):
        return self.params_list(self.component_inputs)
    
    def output_params(self):
        return self.params_list(self.component_outputs)


def add_Params(Input_or_Output
              ,do_not_add
              ,do_not_remove
              ,Params
              ,params_needed
              ):
    #type(str, list, list, type[any], list, list[Param], list[ParamInfo]) -> None   


    if Input_or_Output not in ['Input', 'Output']:
        raise ValueError("Input_or_Output must be in ['Input', 'Output'], "
                        +"instead of: " + str(Input_or_Output)
                        )

    do_not_add = do_not_add[:]
    do_not_remove = do_not_remove[:]

    params_current = getattr(Params, Input_or_Output)[:]

    logger.debug('params_current NickNames == '
                +' '.join(str(param.NickName) for param in params_current)
                )

    needed_NickNames = [str(param['NickName']) for param in params_needed]

    logger.debug('params_needed NickNames == '
                +' '.join(needed_NickNames)
                )

    registers = dict(Input  = 'RegisterInputParam'
                    ,Output = 'RegisterOutputParam'
                    )

    for param in params_current:  
        if param.NickName in needed_NickNames:
            logger.debug('Param already there, appending to do_not_add == '
                        +str(param.NickName)
                        )
            do_not_add += [param.NickName]
        elif (param.NickName not in do_not_remove and
            len(getattr(param, 'Recipients', [])) == 0 and  
            len(getattr(param, 'Sources',    [])) == 0     ):
            logger.debug(    'Param ' 
                        + str(param.NickName) 
                        + ' not needed, and can be removed.  '
                        )
        else:
            logger.debug('Leaving param alone.  User added output? == ' 
                + str(param.NickName))
            do_not_add += [param.NickName]

    for param in params_needed:
        param_name = param['NickName']
        if param_name not in do_not_add: 
            logger.debug('Adding param == ' + param_name)
            
            # update_params.add_param(Params
            #                        ,update_params.make_new_param(param_name)
            #                        ,Input_or_Output
            #                        )

            getattr(Params, registers[Input_or_Output])(param.make()) 
            Params.OnParametersChanged()


            do_not_add += [param_name] # Not used again but just in case we
                                       # decide not to take a copy of it

        else:
            logger.debug('Param in self.do_not_add == ' + param_name)


def add_tool_params(Params
                   ,tools
                   ,do_not_add
                   ,do_not_remove
                   ,wrapper = None
                   ):
    #type(type[any], list[ToolwithParamsABC], list, list, function) -> type[any]
    
    ParamsSyncObj = Params.EmitSyncObject()

    needed_output_params = [ output for tool in reversed(tools)
                             for output in tool.output_params() ]
                           
    needed_input_params = [ input for tool in tools 
                            for input in tool.input_params() ]
                          
    if wrapper:
        needed_output_params = wrapper.output_params() + needed_output_params
        needed_input_params = wrapper.input_params() + needed_input_params

    update_params.add_params(Params
                            ,'Output'
                            ,[param['NickName'] 
                              for param in needed_output_params]
                            ,do_not_remove
                            )

    update_params.add_params(Params
                            ,'Input'
                            ,[param['NickName'] 
                              for param in needed_input_params]
                            ,do_not_remove
                            )

    # add_Params('Output'
    #           ,do_not_add
    #           ,do_not_remove
    #           ,Params
    #           ,needed_output_params
    #           )
    # add_Params('Input'
    #           ,do_not_add
    #           ,do_not_remove
    #           ,Params
    #           ,needed_input_params
    #           )

    Params.Sync(ParamsSyncObj)
    Params.RepairParamAssociations()
    return Params


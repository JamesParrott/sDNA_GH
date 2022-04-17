#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import logging

import Grasshopper.Kernel
import Grasshopper.Kernel.Parameters

from ..skel.basic.smart_comp import get_args_spec

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ParamInfo(dict):
    access_methods = ('item', 'list', 'tree')
    def __init__(self
                ,NickName
                ,factory = None 
                ,Name = None
                ,Description = None
                ,Access = 'list'
                ,Optional = True
                ,**kwargs
                ):
        if isinstance(factory, str):
            if not factory.startswith('Param_'):
                factory = 'Param_' + factory
            factory = getattr(Grasshopper.Kernel.Parameters, factory, None)
        if factory is None:
            factory = Grasshopper.Kernel.Parameters.Param_ScriptVariable
            logger.debug('Using factory Param_ScriptVariable for param : ' + NickName)
        self.factory = factory

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
        return self.factory(**self)


def update_Input_or_Output_Params(Input_or_Output
                                 ,do_not_add
                                 ,do_not_remove
                                 ,Params
                                 ,params_current
                                 ,params_needed
                                 ):
    #type(str, list, list, type[any], list, list, list[ParamInfo]) -> None   


    assert Input_or_Output in ['Input', 'Output']

    do_not_add = do_not_add[:]
    do_not_remove = do_not_remove[:]

    logger.debug(   'params_current NickNames == '
                    + ' '.join(str(param.NickName) for param in params_current)
                )

    names_needed = [param['NickName'] for param in params_needed]

    registers = dict(Input  = 'RegisterInputParam'
                    ,Output = 'RegisterOutputParam'
                    )

    for param in params_current:  
        if param.NickName in params_needed:
            logger.debug('Param already there, adding to self.do_not_add == '
                + str(param.NickName))
            do_not_add += [param.NickName]
        elif (param.NickName not in do_not_remove and
            len(getattr(param, 'Recipients', [])) == 0 and  
            len(getattr(param, 'Sources',    [])) == 0     ):
            logger.debug(    'Param ' 
                    + str(param.NickName) 
                    + ' not needed, and can be removed.  ')
        else:
            logger.debug('Leaving param alone.  User added output? == ' 
                + str(param.NickName))

        # else:  Leave alone.  The user added the param, 
        # or the component was supplied that way by ourselves.
            do_not_add += [param.NickName]

    for param in params_needed:
        param_name = param['NickName']
        if param_name not in do_not_add: 
            do_not_add += [param_name]
            logger.debug('Adding param == ' + param_name)


            # #var = Grasshopper.Kernel.Parameters.Param_String(NickName = param_name)
            # if param_name in geom_params:
            #     new_param_type = Grasshopper.Kernel.Parameters.Param_Geometry
            # #elif param_name in ['leg_cols']:
            # else:
            #     #new_param_type = Grasshopper.Kernel.Parameters.Param_GenericObject
            #     new_param_type = Grasshopper.Kernel.Parameters.Param_ScriptVariable
            # #else:
            # #    new_param_type = Grasshopper.Kernel.Parameters.Param_String

            # if param_name == 'Data':
            #     Access = Grasshopper.Kernel.GH_ParamAccess.tree
            # else: 
            #     Access = Grasshopper.Kernel.GH_ParamAccess.list

            # var = new_param_type(NickName = param_name
            #                     ,Name = param_name
            #                     ,Description = param_name
            #                     ,Access = Access
            #                     ,Optional = True
            #                     )

            #var.NickName = param_name
            #var.Name = param_name
            #var.Description = param_name
            #if param_name == 'Data':
            #    var.Access = Grasshopper.Kernel.GH_ParamAccess.tree
            #else: 
            #    var.Access = Grasshopper.Kernel.GH_ParamAccess.list

            #var.Optional = True

            #index = getattr(Params, Input_or_Output).Count


            #getattr(Params, registers[Input_or_Output])(var) #, index)
            getattr(Params, registers[Input_or_Output])(param.make()) #, index)
            #Params.Output.Count +=1
            Params.OnParametersChanged()

        else:
            logger.debug('Param in self.do_not_add == ' + param_name)


def add_tool_params(Params
                   ,tools
                   ,do_not_add
                   ,do_not_remove
                   ,wrapper = None
                   ):
    #type(type[any], list, list, list) -> type[any]
    
    ParamsSyncObj = Params.EmitSyncObject()

    current_output_params = getattr(Params, 'Output')[:]
    current_input_params = getattr(Params, 'Input')[:]

    last_tool = tools[-1]
    needed_output_params = last_tool.output_params
    needed_input_params = [ input for tool in tools 
                            for input in tool.input_params 
                          ]
    if wrapper:
        needed_output_params = wrapper.output_params + needed_output_params
        needed_input_params = wrapper.input_params + needed_input_params

    
    update_Input_or_Output_Params('Output'
                                 ,do_not_add
                                 ,do_not_remove
                                 ,Params
                                 ,current_output_params
                                 ,needed_output_params
                                 )
    update_Input_or_Output_Params('Input'
                                 ,do_not_add
                                 ,do_not_remove
                                 ,Params
                                 ,current_input_params
                                 ,needed_input_params
                                 )

    Params.Sync(ParamsSyncObj)
    Params.RepairParamAssociations()
    return Params


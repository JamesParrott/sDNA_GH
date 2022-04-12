#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import logging

import Grasshopper.Kernel
import Grasshopper.Kernel.Parameters

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def update_Input_or_Output_Params(Input_or_Output
                                 ,do_not_add
                                 ,do_not_remove
                                 ,Params
                                 ,tools
                                 ,params_current
                                 ,params_needed
                                 ,geom_params = []
                                 ):
    #type(str, list, list) -> None   


    assert Input_or_Output in ['Input', 'Output']

    do_not_add = do_not_add[:]
    do_not_remove = do_not_remove[:]

    logger.debug(   'params_current NickNames =='
                    + ' '.join(str(param.NickName) for param in params_current)
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

    for param_name in params_needed:
        if param_name not in do_not_add: 
            do_not_add += [param_name]
            logger.debug('Adding param == ' + param_name)

            #var = Grasshopper.Kernel.Parameters.Param_String(NickName = param_name)
            if param_name in geom_params:
                new_param_type = Grasshopper.Kernel.Parameters.Param_Geometry
            #elif param_name in ['leg_cols']:
            else:
                new_param_type = Grasshopper.Kernel.Parameters.Param_GenericObject
            #else:
            #    new_param_type = Grasshopper.Kernel.Parameters.Param_String

            if param_name == 'Data':
                Access = Grasshopper.Kernel.GH_ParamAccess.tree
            else: 
                Access = Grasshopper.Kernel.GH_ParamAccess.list

            var = new_param_type(NickName = param_name
                                ,Name = param_name
                                ,Description = param_name
                                ,Access = Access
                                ,Optional = True
                                )

            #var.NickName = param_name
            #var.Name = param_name
            #var.Description = param_name
            #if param_name == 'Data':
            #    var.Access = Grasshopper.Kernel.GH_ParamAccess.tree
            #else: 
            #    var.Access = Grasshopper.Kernel.GH_ParamAccess.list

            #var.Optional = True

            #index = getattr(Params, Input_or_Output).Count

            registers = dict(Input  = 'RegisterInputParam'
                            ,Output = 'RegisterOutputParam'
                            )
            getattr(Params, registers[Input_or_Output])(var) #, index)
            #Params.Output.Count +=1
            Params.OnParametersChanged()

        else:
            logger.debug('Param in self.do_not_add == ' + param_name)


def add_tool_params(Params
                   ,tools
                   ,do_not_add
                   ,do_not_remove
                   ,geom_params
                   ):
    #type(type[any], list, list, list) -> type[any]
    
    ParamsSyncObj = Params.EmitSyncObject()

    current_output_params = getattr(Params, 'Output')[:]
    current_input_params = getattr(Params, 'Input')[:]

    last_tool = tools[-1]
    needed_output_params = list(last_tool.show['Output'])
    needed_input_params = [ input for tool in tools 
                            for input in tool.show['Input'] ]

    
    update_Input_or_Output_Params('Output'
                                 ,do_not_add
                                 ,do_not_remove
                                 ,Params
                                 ,tools
                                 ,current_output_params
                                 ,needed_output_params
                                 ,geom_params
                                 )
    update_Input_or_Output_Params('Input'
                                 ,do_not_add
                                 ,do_not_remove
                                 ,Params
                                 ,tools
                                 ,current_input_params
                                 ,needed_input_params
                                 ,geom_params
                                 )

    Params.Sync(ParamsSyncObj)
    Params.RepairParamAssociations()
    return Params


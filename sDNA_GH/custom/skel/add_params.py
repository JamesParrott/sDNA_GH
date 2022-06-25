#! /usr/bin/awk NR==3
# -*- coding: utf-8 -*-
# This module requires Grasshopper Python (Rhino3D)

# MIT License

# Copyright (c) [2021] [Cardiff University, a body incorporated
# by Royal Charter and a registered charity (number:
# 1136855) whose administrative offices are at 7th floor 30-
# 36 Newport Road, UniversityCF24 0DE, Wales, UK]

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


__author__ = 'James Parrott'
__version__ = '0.02'

import logging
import abc

import GhPython
import Grasshopper.Kernel 
from Grasshopper.Kernel.Parameters import Param_ScriptVariable

if hasattr(abc, 'ABC'):
    ABC = abc.ABC
else:
    class ABC(object):
        __metaclass__ = abc.ABCMeta
abstractmethod = abc.abstractmethod


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
            logger.warning('Unrecognised access method : %s ' % Access)
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

def check_IO(IO):
    #type(str) -> None
    if IO not in ['Input', 'Output']:
        raise ValueError("IO must be in ['Input', 'Output'], "
                        +"instead of: " + str(IO)
                        )

def current_param_names(params, IO):
    #type(type[any], str) -> list[str]
    check_IO(IO)
    return [param.NickName for param in getattr(params, IO)]
#            for param in getattr(ghenv.Component.Params,IO)]


def add_Params(IO
              ,do_not_add
              ,do_not_remove
              ,Params
              ,params_needed
              ):
    #type(str, list, list, type[any], list, list[Param], list[ParamInfo]) -> None   

    check_IO(IO)



    do_not_add = do_not_add[:]
    do_not_remove = do_not_remove[:]

    params_current = getattr(Params, IO)[:]

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

            getattr(Params, registers[IO])(param.make()) 
            Params.OnParametersChanged()


            do_not_add += [param_name] # Not used again but just in case we
                                       # decide not to take a copy of it

        else:
            logger.debug('Param in do_not_add == ' + param_name)

class ParamsToolAdder(object):

    def __init__(self, Params):
        self.Params = Params

    @property
    def current_outputs(self):
        return current_param_names(self.Params, 'Output')

    @property
    def current_inputs(self):
        return current_param_names(self.Params, 'Input')

    @property
    def user_inputs(self):
        return [input for input in self.current_inputs
                if input not in getattr(self, 'needed_inputs', [])
               ]

    @property
    def user_outputs(self):
        return [output for output in self.current_outputs
                if output not in getattr(self, 'needed_outputs', [])
               ] 

    def add_tool_params(self
                       ,Params
                       ,tools
                       ,do_not_add
                       ,do_not_remove
                       ,wrapper = None
                       ):
        #type(type[any], list[ToolwithParamsABC], list, list, function) -> type[any]
        
        logger.debug('self.current_outputs == %s ' % self.current_outputs)
        
        logger.debug('self.current_inputs == %s ' % self.current_inputs)

        output_tools = list(reversed(tools[:]))
        input_tools = tools[:]

        if wrapper:
            output_tools = [wrapper] + output_tools
            input_tools = [wrapper] + input_tools

        self.needed_outputs = [output['NickName'] 
                               for tool in output_tools
                               for output in tool.output_params() 
                              ]
        self.needed_inputs = [input['NickName'] 
                              for tool in input_tools 
                              for input in tool.input_params() 
                             ]



        missing_output_params = [ output for tool in reversed(output_tools)
                                 for output in tool.output_params() 
                                 if output['NickName'] not in self.current_outputs]

        missing_input_params = [ input for tool in input_tools 
                                for input in tool.input_params() 
                                if input['NickName'] not in self.current_inputs ]
                            
        # if wrapper:
        #     for output in reversed(wrapper.output_params()):
        #         if output['NickName'] not in self.current_outputs:
        #             missing_output_params = [output] + missing_output_params
        #     for input in reversed(wrapper.input_params()):
        #         if input['NickName'] not in self.current_inputs:
        #             missing_input_params = [input] + missing_input_params



        if not missing_output_params and not missing_input_params:
            msg = 'No extra Params required. '
            logger.debug(msg)
            return msg
        else:
            logger.debug('needed_output_params == %s ' % missing_output_params)
            logger.debug('needed_input_params == %s ' % missing_input_params)


        ParamsSyncObj = Params.EmitSyncObject()

        if missing_output_params:
            add_Params('Output'
                    ,do_not_add
                    ,do_not_remove
                    ,Params
                    ,missing_output_params
                    )

        if missing_input_params:
            add_Params('Input'
                    ,do_not_add
                    ,do_not_remove
                    ,Params
                    ,missing_input_params
                    )

        Params.Sync(ParamsSyncObj)
        Params.RepairParamAssociations()

        logger.debug('tools == %s' % tools)


        return 'Tried to add extra Params. '


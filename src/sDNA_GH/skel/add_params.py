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

from collections import OrderedDict
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

try:
    basestring #type: ignore
except NameError:
    basestring = str

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class ParamInfoABC(ABC):
    @abstractmethod
    def make(self):
        """Makes instance of a type in Grasshopper.Kernel.Parameters """


class ParamInfo(dict, ParamInfoABC):
    """ Enables lazy loading of a Grasshopper.Kernel.Parameters.Param_ 
        Class, and collects together both its calling args and the attrs 
        to be set on the instance afterwards, simplifying construction.
        
        The actual Param is initialised by calling .make, e.g. by add_Params.
        
        Initialisation of Params might slow Grasshopper for the user, so this
        Class guarantees we build Params only when they are actually
        needed by a component, and collects all the properties conveniently as 
        function args in the dict, instead of having to set them on the instance
        afterwards.  
    """
    __getattr__ = dict.__getitem__
    valid_access_methods = ('item', 'list', 'tree')
    def __init__(self
                ,NickName = None
                ,param_Class = None 
                ,Name = None
                ,Description = None
                ,Access = 'list'
                ,Optional = True
                ,TypeHint = None 
                ,**kwargs
                ):
        if isinstance(param_Class, basestring):
            if not param_Class.startswith('Param_'):
                param_Class = 'Param_' + param_Class
            param_Class = getattr(Grasshopper.Kernel.Parameters, param_Class, None)
        if param_Class is None:
            param_Class = Param_ScriptVariable
            msg = 'Using Param_ScriptVariable'
            if NickName:
                msg += 'for param_Class: %s' % NickName
            else:
                msg +='for as yet unnamed Param'
            logger.debug(msg)
        self.param_Class = param_Class
        if TypeHint is None and param_Class == Param_ScriptVariable:
            TypeHint = GhPython.Component.GhDocGuidHint()
            
        self.TypeHint = TypeHint  # TypeHint is None handled in .make() below
        if Description is None:
            Description = NickName
        if Access in self.valid_access_methods:
            Access = getattr(Grasshopper.Kernel.GH_ParamAccess, Access)
        elif Access not in [getattr(Grasshopper.Kernel.GH_ParamAccess, x) 
                            for x in self.valid_access_methods]:
            logger.warning('Unrecognised access method : %s ' % Access)
        super(ParamInfo, self).__init__(NickName = NickName
                                       ,Name = Name
                                       ,Description = Description
                                       ,Access = Access
                                       ,Optional = Optional
                                       ,**kwargs
                                       )
    def make(self, **kwargs):
        
        self.update(kwargs)

        if self['NickName'] is None:
            raise ValueError('Param: %s is missing a name' % self.param_Class.__name__)
        
        if self['Name'] is None:
            self['Name'] = self['NickName']

        
        Param = self.param_Class() #**self)

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
                         ,param_classes = {}
                         ,TypeHints = {}
                         ,access_methods = {}
                         ,descriptions = {}
                         ):
    #type(Iterable, dict, dict, dict, dict) -> List[Grasshopper.Kernel.GH_Param]
    if isinstance(param_names, basestring):
        param_names = [param_names]

    param_classes = OrderedDict(param_classes)    # If they do not throw an 
    TypeHints = OrderedDict(TypeHints)            # error, dict and OrderedDict   
    access_methods = OrderedDict(access_methods)  # are idempotent.
    descriptions = OrderedDict(descriptions)

    return [ParamInfo(NickName = name
                     ,param_Class = param_classes.get(name
                                                     ,Param_ScriptVariable
                                                     )
                     ,TypeHint = TypeHints.get(name
                                              ,None
                                              )
                     ,Access = access_methods.get(name, 'list')
                     ,Description = descriptions.get(name#.lower()
                                                         #.replace(' ','') # .strip misses middle
                                                         #.replace('_','')
                                                    ,''
                                                    )
                     ) 
            for name in param_names                            
           ]

class ToolWithParams(ToolwithParamsABC):

    # Tuples are immutable, so subclasses of this class can safely simply append to 
    # these inherited variables.  
    # If we used dicts, we would have to be careful to
    # .copy() to avoid .updating these base class variables too.  
    # This is a little more syntax, but much simpler than meta-classes also.

    param_classes = () # Tuple of tuple of key/value pairs
                       # key: Param name (str), val: Grasshopper.Kernel.Parameters.Param_...

    type_hints = () # Tuple of tuple of key/value pairs
                    # key: Param name (str), val: GhPython.Component.GhDocGuidHint()
                    # Best to leave to the correct Param type above.

    access_methods = () # Tuple of tuple of key/value pairs
                        # key: Param name (str), val in ('item', 'list', 'tree')

    descriptions = () # Tuple of tuple of key/value pairs
                      # key: Param name (str), val: description text

    def params_list(self, names):
        return param_info_list_maker(param_names = names
                                    ,param_classes = self.param_classes
                                    ,TypeHints = self.type_hints
                                    ,access_methods = self.access_methods
                                    ,descriptions = self.descriptions
                                    )


    component_inputs = ()   # tuple of strings of input Param names

    component_outputs = ()  # tuple of strings of input Param names

    def input_params(self, *args):
        return self.params_list(self.component_inputs)
    
    def output_params(self, *args):
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
    #type(str, list, list, type[any], list) -> None   

    check_IO(IO)



    do_not_add = do_not_add[:]
    do_not_remove = do_not_remove[:]

    params_current = getattr(Params, IO)[:]

    logger.debug('params_current NickNames == '
                +' '.join(str(param.NickName) for param in params_current)
                )

    needed_NickNames = [param.NickName for param in params_needed]

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
            logger.debug( 'Param ' 
                        + str(param.NickName) 
                        + ' not needed, and can be removed.  '
                        )
        else:
            logger.debug('Leaving param alone.  User added output? == ' 
                + str(param.NickName))
            do_not_add += [param.NickName]

    for param in params_needed:
        param_name = param.NickName
        if param_name not in do_not_add: 
            logger.debug('Adding param == ' + param_name)
            
            # update_params.add_param(Params
            #                        ,update_params.make_new_param(param_name)
            #                        ,Input_or_Output
            #                        )
            made_param = param
            if isinstance(made_param, ParamInfoABC):
                made_param = made_param.make()
            getattr(Params, registers[IO])(made_param) 
            Params.OnParametersChanged()


            do_not_add += [param_name] # Not used again but just in case we
                                       # decide not to take a copy of it

        else:
            logger.debug('Param in do_not_add == ' + param_name)


def delete_Param(Params, name, IO):
    #type(type[Any], str, str) -> None
    """ Deletes a Param from a GH component.  
    
        WARNING.  Glitches and crashes are likely when calling this function
        from a component, on its own Params (e.g. that will cause it to run
        again).  

        It is used in builder.py, on code-generated components' params, from 
        the builder component (to remove the default GhPython params). 
    """
    check_IO(IO)
    Params_to_delete = [P for P in getattr(Params, IO) if P.NickName == name]
    for Param in Params_to_delete:
        {'Input' : Params.UnregisterInputParameter
        ,'Output' : Params.UnregisterOutputParameter
        }.get(IO)(Param)
    

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
                       ,interpolations = None
                       ):
        #type(type[any], list[ToolwithParamsABC], list, list, function) -> type[any]
        
        if interpolations is None:
            interpolations = {}

        logger.debug('self.current_outputs == %s ' % self.current_outputs)
        
        logger.debug('self.current_inputs == %s ' % self.current_inputs)

        output_tools = list(reversed(tools[:]))
        input_tools = tools[:]

        if wrapper:
            output_tools += [wrapper]
            input_tools = [wrapper] + input_tools

        self.needed_outputs = [output.NickName
                               for tool in output_tools
                               for output in tool.output_params(interpolations)
                              ]
        self.needed_inputs = [input.NickName
                              for tool in input_tools 
                              for input in tool.input_params(interpolations)
                             ]
        # Used later, e.g. by sDNA tools when constructing advanced,
        # to deduce any Params not in here are User Params
        #
        # .NickName searches output['NickName'] for ParamInfo instances as
        # ParamInfo.__getattr__ is dict.__getitem__

        missing_output_params = [output for tool in reversed(output_tools)
                                 for output in tool.output_params(interpolations)
                                 if output.NickName not in self.current_outputs]


        missing_input_params = [input for tool in input_tools 
                                for input in tool.input_params(interpolations)
                                if input.NickName not in self.current_inputs ]
                            
        # if wrapper:
        #     for output in reversed(wrapper.output_params()):
        #         if output['NickName'] not in self.current_outputs:
        #             missing_output_params = [output] + missing_output_params
        #     for input in reversed(wrapper.input_params()):
        #         if input['NickName'] not in self.current_inputs:
        #             missing_input_params = [input] + missing_input_params



        if not missing_output_params and not missing_input_params:
            msg = 'Zero extra Params required. '
            logger.debug(msg)
            return False # params_updated == False
        else:
            logger.debug('missing_output_params == %s ' % missing_output_params)
            logger.debug('missing_input_params == %s ' % missing_input_params)


        ParamsSyncObj = Params.EmitSyncObject()

        for IO, params_list in zip(('Output', 'Input')
                                  ,(missing_output_params, missing_input_params)
                                  ):
            if params_list:
                add_Params(IO
                          ,do_not_add
                          ,do_not_remove
                          ,Params
                          ,params_needed = params_list
                          )


        Params.Sync(ParamsSyncObj)
        Params.RepairParamAssociations()

        logger.debug('tools == %s' % tools)


        return True # params_updated == True


#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'


import logging
import sys
from collections import OrderedDict
from inspect import currentframe
if sys.version < '3.3':
    from collections import Iterable 
else:
    from collections.abc import Iterable
from abc import abstractmethod
if sys.version < '3.4':
    from abc import ABCMeta
    class ABC:
        __metaclass__ = ABCMeta
else:
    from abc import ABC

from ghpythonlib.componentbase import executingcomponent as component

from ..tools.helper.funcs import get_args, quacks_like


logger = logging.getLogger('sDNA_GH').addHandler(logging.NullHandler())


def get_val(key, sources):
    #type(str, list) -> type[any]
    for source in sources:
        if isinstance(source, dict) and key in source:
            return source[key]
        elif hasattr(source, key):
            return getattr(source, key)
    return 'No variable or field: ' + key + ' found. '


def custom_retvals(arg_names, sources = [], return_locals = False, frames_back = 1):
    #type(list[str], list, bool) -> tuple(type[any])
    """ To get inspect.currentframe to target the correct scope,
        if you wrap this function in n functions, that are called from the target
        call it with frames_back = n"""
    if return_locals:
        calling_frame = currentframe()
        for _ in range(frames_back):
            calling_frame = calling_frame.f_back
        sources += [ calling_frame.f_locals.copy() ]
    return tuple(get_val(arg, sources) for arg in arg_names)


def custom_retvals_from_component_Outputs(self, sources):
    
    return custom_retvals([param.NickName for param in self.Params.Output]
                         ,sources
                         ,return_locals = True
                         ,frames_back = 2
                         )
#    assert hasattr(BaseComponent, 'Params')

#    assert hasattr(BaseComponent.Params, 'Output')
#    assert isinstance(BaseComponent.Params.Output, Iterable)


    # if arg_names is None:
    #     arg_names = [param.NickName for param in self.Params.Output]
    # if go:
    #     ret_vals = tuple(get_val(arg, sources) for arg in arg_names)
    #     return ret_vals
    # else:   
    #     return (False, ) + tuple(repeat(None, len(self.Params.Output) - 1))    


def custom_inputs_class_deco(BaseComponent
                            ,anon_pos_arg_names = None
                            ,anon_kwargs = None
                            ,prioritise_kwargs = True
                            ):
    
    assert hasattr(BaseComponent, 'Params')
    assert hasattr(BaseComponent.Params, 'Input')
    assert hasattr(BaseComponent, 'RunScript')
    assert isinstance(BaseComponent.Params.Input, Iterable)


    class Decorated(BaseComponent):
    
        main = BaseComponent.RunScript
        #type(function) -> function
        if anon_pos_arg_names == None:
            if hasattr(main, 'pos_args'):
                anon_pos_arg_names = main.pos_args
            else:
                anon_pos_arg_names = []
        if anon_kwargs == None:
            if hasattr(main, 'kwargs'):
                anon_kwargs = main.kwargs
            else:
                anon_kwargs = []


        def RunScript(self, *param_vals):
            args_dict = {}
            pos_args = OrderedDict()
            param_names = (param.Name for param in self.Params.Input)

            argspec = get_args(self.main)
            req_pos_args = argspec.args[:-len(argspec.defaults)]
            missing_req_pos_args = ()
            
            params_dict = OrderedDict( zip(param_names, param_vals))
            logger.debug(params_dict)

            for param_name in req_pos_args:  # Try to fill required positional
                                                # args with names in Params.
                if param_name in params_dict:
                    pos_args[param_name] += (params_dict.pop(param_name),)
                else:
                    missing_req_pos_args += (param_name)

            
            for param_name in params_dict:   # Try to fill other named args
                                                # with names in Params.
                if param_name in argspec.args: 
                    assert param_name not in req_pos_args # has a default value
                    args_dict[param_name] = params_dict.pop(param_name)
                elif prioritise_kwargs:
                    if param_name in anon_kwargs:
                        args_dict[param_name] = params_dict.pop(param_name)
                    elif param_name in anon_pos_arg_names:
                        anon_pos_args += (params_dict.pop(param_name))
                        # Should really prioritise missing_req_pos_args and
                        # this could put the positional args out of order, but 
                        # as we always have a param name, if it matches a given
                        # anon_pos_arg name, and the user wanted it to go to a 
                        # named positional argument instead, 
                        # what was the point in using this at all?
                        # GH components already support *args, so it's just 
                        # an edge case we will ignore - this smart component 
                        # will never be foolproof!  We can't fix bad naming,
                        # and this tool was intended for different usage.
                elif not prioritise_kwargs:
                    if param_name in anon_pos_arg_names:
                        anon_pos_args += (params_dict.pop(param_name))
                    elif param_name in anon_kwargs:
                        args_dict[param_name] = params_dict.pop(param_name)

            assert all(name not in (argspec.args + anon_kwargs + anon_pos_arg_names)
                        for name in params_dict
                        )
            
            #Try to assign params whose names could not be found to
            # missing required positional args (before ones with defaults).
            for param_name in params_dict:
                if missing_req_pos_args:
                    pos_args[param_name] = params_dict.pop(param_name)
                    missing_req_pos_args = missing_req_pos_args[1:]
                else:
                    break
            
            if missing_req_pos_args:
                msg = 'Missing named positional argument'
                logger.warning(msg)
                raise TypeError(msg)
            
            assert len(pos_args) == len(argspec.args), 'Missing named positional argument?'

            if prioritise_kwargs:
                args_dict.update(params_dict)
            else:
                anon_pos_args += tuple(params_dict.values())

            anon_pos_args = tuple(pos_args.values()) + anon_pos_args

            return BaseComponent.RunScript(*anon_pos_arg_names, **args_dict)
            # BaseClass.RunScript needs to call:
            # custom_retvals_from_component_Outputs(on its retvals) itself
    return Decorated

class MyComponentWithMainABC(component, ABC):
    """Framework for a 'smart' grasshopper component, supporting kwargs type 
       inputs from user-customisable Input Params, default values,
       and returning suitable
       outputs based on the user specified Output Params.  """
    @abstractmethod
    def main(self, *args, **kwargs):
        """ Specify the main script / method here instead of RunScript. 
            In an instance of CustomInputsComponentABC or in a class produced
            by the custom_inputs_class_deco decorator, RunScript now inspects 
            the call signature of this method, then parses the components 
            input Param's matching them up accordingly, then calls this method.

            To also use Custom Outputs in your own code, you need to add the 
            method custom_retvals_from_component_Outputs to the component, in 
            your own code end each exit point of main with
            'return self.custom_retvals_from_component_Outputs(sources)' with 
            sources as a list of whichever dicts or namedtuples whose contents 
            you wish to make available on the Output params.
            
            By default the locals in the scope of main are added to sources so
            sources can be omitted.  
            
            Returning primitives is not supported - 
            create a local variable in the function body with the same name as
            the Output Param you want it on, and assign the primitive to it."""
        return kwargs

    @abstractmethod
    def RunScript(self, *args, **kwargs): #go, Data, Geom, f_name, *args):
        pass
    # type (bool, str, Rhino Geometry, datatree, tuple(namedtuple,namedtuple), *dict)->bool, str, Rhino_Geom, datatree, str

CustomInputsComponentABC = custom_inputs_class_deco(MyComponentWithMainABC)

SmartComponent = custom_inputs_class_deco(MyComponentWithMainABC)
SmartComponent.custom_retvals_from_component_Outputs = custom_retvals_from_component_Outputs

def old_smart_RunScript(self, *args):
    args_dict = {key.Name : val for key, val in zip(self.Params.Input, args) } # .Input[4:] type: ignore
    logger.debug(args)
    ret_vals_dict = self.main(**args_dict)
    go = args_dict.get('go', False)

    tool_opts = self.opts
    nick_name = self.local_metas.nick_name
    sDNA = self.opts['metas'].sDNA
    if nick_name in self.opts:
        tool_opts = self.opts[nick_name]
        if isinstance(tool_opts, dict):
            tmp = {}
            for tool_name in tool_opts:
                tmp.update(tool_opts[tool_name]._asdict())
            tool_opts = tmp
    locs = locals().copy

    sources = [ret_vals_dict
                ,locs
                ,self.opts['metas']
                ,self.opts['options']
                ,self.local_metas
                ,tool_opts
                ]
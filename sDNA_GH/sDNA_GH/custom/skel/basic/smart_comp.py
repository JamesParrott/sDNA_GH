#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'


import logging
import sys
from collections import OrderedDict
from itertools import repeat
from inspect import getargspec
from abc import abstractmethod
if sys.version < '3.4':
    from abc import ABCMeta
    class ABC:
        __metaclass__ = ABCMeta
else:
    from abc import ABC

from ghpythonlib.componentbase import executingcomponent as component


logger = logging.getLogger('sDNA_GH').addHandler(logging.NullHandler())


class SmartComponent(component, ABC):
    """Framework for a 'smart' grasshopper component, supporting kwargs type 
       inputs from user-customisable Input Params, default values,
       and returning suitable
       outputs based on the user specified Output Params.  """
    @abstractmethod
    def main(self, **kwargs):
        """ The main script / Routine now goes in here instead of RunScript, 
            which now makes **kwargs from the user supplied inputs, calls this 
            method with them, then returns the retvals requested by the user 
            specified output Params"""
        return kwargs
    
    def RunScript(self, *args): #go, Data, Geom, f_name, *args):
    # type (bool, str, Rhino Geometry, datatree, tuple(namedtuple,namedtuple), *dict)->bool, str, Rhino_Geom, datatree, str

        args_dict = {key.Name : val for key, val in zip(self.Params.Input, args) } # .Input[4:] type: ignore
        logger.debug(args)
        ret_vals_dict = self.main(**args_dict)
        go = args_dict.get('go', False)

        tool_opts = {}
        nick_name = self.local_metas.nick_name
        sDNA = self.opts['metas'].sDNA
        if nick_name in tool_opts:
            tool_opts = tool_opts[nick_name]
        if isinstance(tool_opts, dict) and sDNA in tool_opts:
            tool_opts = tool_opts[sDNA]
        locs = locals().copy

        sources = [ret_vals_dict
                  ,locs
                  ,self.opts['metas']
                  ,self.opts['options']
                  ,self.local_metas
                  ,tool_opts
                  ]
        def get_val(key, sources):
            #type(str, list) -> type[any]
            for source in sources:
                if isinstance(source, dict) and key in source:
                    return source[key]
                elif hasattr(source, key):
                    return getattr(source, key)
            return 'No variable or field: ' + key + ' found. '

        if go:
            ret_vals = tuple(get_val(param.NickName, sources) for param in self.Params.Output)
            return ret_vals
        else:   
            return (False, ) + tuple(repeat(None, len(self.Params.Output) - 1))        

def smart_RunScript_decorator(base_tool
                             ,anon_pos_arg_names = None
                             ,anon_kwargs = None
                             ,prioritise_kwargs = True
                             ):
    #type(function) -> function
    if anon_pos_arg_names == None:
        if hasattr(base_tool, 'pos_args'):
            anon_pos_arg_names = base_tool.pos_args
        else:
            anon_pos_arg_names = []
    if anon_kwargs == None:
        if hasattr(base_tool, 'kwargs'):
            anon_kwargs = base_tool.kwargs
        else:
            anon_kwargs = []


    def RunScript(self, *param_vals):
        args_dict = {}
        pos_args = OrderedDict()
        param_names = (param.Name for param in self.Params.Input)

        argspec = getargspec(base_tool)
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



                


        retvals = base_tool(*anon_pos_arg_names, **args_dict)
        return retvals
    return RunScript
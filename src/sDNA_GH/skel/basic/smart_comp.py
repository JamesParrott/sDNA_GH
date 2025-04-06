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



""" A framework to build 'Smart' Components for Grasshopper.

    Smart Components are uncompiled GhPython components that 
    support a user or code specified dynamic variable number 
    of Input and Output Params.  
    
    Input Params and their names
    can e.g. be passed as kwargs to Python functions.  Arbitrary
    positional arguments and named ordinary positional arguments are
    supported too, using function introspection via 
    inspect.getargspec, and some customisable priority hints.  
    
    Output Params can have
    the values passed to them automatically that e.g. correspond
    to local Python variables of the same name.  This currently
    requires a couple of lines of boiler plate at each return 
    statement in the function until a bug with 
    inspect.currentframe in GhPython is fixed.  
"""

__authors__ = {'James Parrott', 'Crispin Cooper'}
__version__ = '3.0.4'

import logging
import inspect
import collections
from numbers import Number
if hasattr(collections, 'Sequence'):
    Sequence, Callable = collections.Sequence, collections.Callable
else:
    import collections.abc  
    Sequence, Callable = collections.abc.Sequence, collections.abc.Callable


OrderedDict = collections.OrderedDict

try:
    basestring #type: ignore
except NameError:
    basestring = str

from ghpythonlib.componentbase import executingcomponent as component

from .ghdoc import ghdoc


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def remove_whitespace(strng):
    #type(str) -> str
    return ''.join([char for char in strng if not char.isspace()])


def first_item_if_seq(l, null_container = {}):
    #type(type[any], type[any])-> dict
    """A function to strip out unnecessary wrapping containers, e.g. 
       first_item_if_seq([[1,2,3,4,5]]) == [1,2,3,4,5] without breaking 
       up strings.  
       
       Returns the second argument if the first argument is null.
       Returns the first item of a Sequence, otherwise returns the 
       not-a-Sequence first argument.  
    """
    if not l:
        return null_container        

    if isinstance(l, Sequence) and not isinstance(l, basestring):
        l = l[0]
    
    return l



def get_args_spec(callable):
    if not isinstance(callable, Callable):
        raise TypeError('Argument is not callable, therefore has no args')
    # assert hasattr(callable, '__call__')
    try:
        arg_spec = inspect.getargspec(callable)
    except TypeError:
        try:
            arg_spec = inspect.getargspec(callable.__call__)
        except TypeError:
            raise Exception("Could not get argspec for " + str(callable))
    
    if arg_spec.args[0] in ('self', 'cls'):
        arg_spec = arg_spec._replace(args = arg_spec.args[1:])
    return arg_spec



    # if (type(callable).__name__ == 'function' or
    #     callable.__class__.__name__ == ('function','instancemethod') or
    #     quacks_like(basic_function, callable)):
    #     return inspect.getargspec(callable)
    # elif hasattr(callable, '__call__'):

def get_val(key, sources, case_sensitive = False, support_whitespace = False):
    #type(str, list) -> type[any]
    if key.lower() == 'out':
        return None
        # Standard output parameter of a GhPython component that takes sys.err etc.
        # https://developer.rhino3d.com/guides/rhinopython/ghpython-component/#out-parameter

    for source in sources:
        #logger.debug('Fetching : '+ str(key))
        if isinstance(source, dict) and key in source:
            logger.debug('Fetching %s : %s ' % (key, source[key]))

            return source[key]
        elif hasattr(source, key):
            logger.debug('Fetching %s : %s ' % (key, getattr(source, key)))

            return getattr(source, key)
    if case_sensitive or key.islower():
        logger.debug('No variable or field: ' + key + ' found. ')
        return 'No variable or field: %s found' % key
    else:
        key = key.lower()
        if support_whitespace:
            key = remove_whitespace(key)
        return get_val(key, sources, case_sensitive = True)

    # Whitespace is not stripped as valid python names, namedtuple fields
    # and class attributes cannot contain whitespace.  So dict keys with whitespace
    # will not be returned.

def custom_retvals(retval_names
                  ,sources
                  ,return_locals = True
                  ,frames_back = 2 
                  ):
    #type(list[str], list) -> tuple(type[any])
    return tuple(get_val(retval_name, sources) for retval_name in retval_names)

##############################################################################
#
# Python 3 ish only
#
# def custom_retvals(retval_names
#                   ,sources = None
#                   ,return_locals = False
#                   ,frames_back = 1
#                   ):
#     #type(list[str], list, bool, int) -> tuple(type[any])
#     """ To get inspect.currentframe to target the correct scope,
#         if you wrap this function in n functions, that are called from 
#         the target call it with frames_back = n"""
#     if sources is None:
#         sources = []
#     if return_locals:
#         calling_frame = inspect.currentframe()
#         for _ in range(frames_back):
#             calling_frame = calling_frame.f_back
#         sources += [ calling_frame.f_locals.copy() ]
#     return tuple(get_val(retval_name, sources) for retval_name in retval_names)
#
#
##############################################################################

def component_Outputs(self, sources):
    names = [param.NickName for param in self.Params.Output]
    return custom_retvals(names
                         ,sources
                         ,return_locals = True
                         ,frames_back = 2
                         )



def prepare_args(function
                ,params_dict
                ,anon_pos_args = []
                ,anon_kwargs = []
                ,prioritise_kwargs = True
                ,add_unrecognised_names_to_pos_args = False
                ):
    #type(function, dict, list, list, bool, bool) -> tuple, dict
    argspec = get_args_spec(function)
    logger.debug('argspec(function) == %s ' % argspec)

    params_dict = params_dict.copy()  #We'll be popping keys out later

    args_dict = {}
    pos_args = {} # positional arguments
    unnamed_pos_args = ()
    req_pos_args = argspec.args

    if argspec.defaults:
        req_pos_args = req_pos_args[:-len(argspec.defaults)]
        # required positional arguments (i.e. before those with default values)

    logger.debug('required positional arguments == %s ' % req_pos_args)
    
    missing_req_pos_args = []
    
    for param_name in req_pos_args:  # Try to fill required positional
                                     # args with names in Params.
        if param_name in params_dict:
            pos_args[param_name] = params_dict.pop(param_name)
        else:
            missing_req_pos_args += [param_name]

    #logger.debug('pos_args == %s ' % pos_args))

    for param_name in params_dict.copy():   # Try to fill other named args
                                            # with names in Params.
        if param_name in argspec.args: 
            assert param_name not in req_pos_args   # i.e., it has a 
                                                    # default value
                                                    # so occurs after
                                                    # req_pos_args
            args_dict[param_name] = params_dict.pop(param_name)
        elif prioritise_kwargs and argspec.keywords:
            if param_name in anon_kwargs:
                args_dict[param_name] = params_dict.pop(param_name)
            elif param_name in anon_pos_args and argspec.varargs:
                unnamed_pos_args += (params_dict.pop(param_name),)
            #else:  unnamed_pos_args == anon_kwargs == [] etc. 
            #       handled later
                
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
            if param_name in anon_pos_args and argspec.varargs:
                unnamed_pos_args += (params_dict.pop(param_name))
            elif param_name in anon_kwargs and argspec.keywords:
                args_dict[param_name] = params_dict.pop(param_name)
            #else:  unnamed_pos_args == anon_kwargs == [] etc. 
            #       handled later

    assert all(name not in (argspec.args + anon_kwargs + anon_pos_args)
                for name in params_dict
                )
    
    #Try to assign params whose names could not be found to
    # missing required positional args (before ones with defaults).
    if add_unrecognised_names_to_pos_args:
        for req_pos_arg, param_name in zip(missing_req_pos_args[:], params_dict.copy()):
            if missing_req_pos_args:
                pos_args[req_pos_arg] = params_dict.pop(param_name)
                missing_req_pos_args.remove(req_pos_arg)
            else:
                break

    if missing_req_pos_args:
        msg = 'Missing named positional argument'
        logger.debug('missing_req_pos_args == %s ' % missing_req_pos_args)
        logger.debug('pos_args keys == %s ' % pos_args.keys())
        logger.debug('args_dict keys == %s ' % args_dict.keys())

        logger.error(msg)
        raise TypeError(msg)
    
    if params_dict:
        if prioritise_kwargs and argspec.keywords:
            logger.debug('Adding all remaining Input Params to args_dict')
            args_dict.update(params_dict)
        elif argspec.varargs:
            unnamed_pos_args += tuple(params_dict.values())
            logger.debug('Adding all remaining Input Params to unnamed_pos_args')
        else:
            logger.debug('Unallocated param keys: %s ' % params_dict.keys())


    pos_args_tupl = (tuple(pos_args[arg] 
                           for arg in argspec.args 
                           if arg in pos_args
                          ) 
                    +unnamed_pos_args
                    )

    #logger.debug('pos_args == %s ' % pos_args_tupl))
    #logger.debug('args_dict == %s ' % args_dict))

    return pos_args_tupl, args_dict


def delistify(l):
    if isinstance(l, list) and len(l) == 1:
        return l[0]
    elif hasattr(l, '__len__') and len(l) == 0:
        return None
    else:
        return l # because then it wasn't a trivial list.

def custom_inputs_class_deco(BaseComponent
                            ,anon_pos_args = []
                            ,anon_kwargs = []
                            ,prioritise_kwargs = True
                            ,case_sensitive = True
                            ,leave_whitespace = True
                            ):
    #type(type[any], list, list, bool) -> type[any]

    class Decorated(BaseComponent):
    
        script = BaseComponent.RunScript

        def RunScript(self, *param_vals):
            params_dict = OrderedDict( (param.NickName, delistify(param_val))
                                       for param, param_val 
                                          in zip(self.Params.Input, param_vals)
                                     )
            if not case_sensitive or not leave_whitespace: # Add in extra keys 
                                                           # to make case insensitive
                for key, val in params_dict.copy().items():   
                    if not case_sensitive:
                        key = key.lower() 
                    if not leave_whitespace:
                        key = remove_whitespace(key)
                        key = key.replace('_', '')
                    params_dict.setdefault(key, val)
        # If tools accept **kwargs or *args
        # duped kwargs or args could be a problem here. ymmv.

            logger.debug('\n'.join('%s : %s' %(key, value) if isinstance(value, (str, Number, bool)) else key 
                                   for key, value in params_dict.items())
                        )

            pos_args, args_dict = prepare_args(self.script
                                              ,params_dict = params_dict
                                              ,anon_pos_args = anon_pos_args
                                              ,anon_kwargs = anon_kwargs
                                              ,prioritise_kwargs = prioritise_kwargs   
                                              )

 

            return self.script(*pos_args, **args_dict)
            # BaseClass.RunScript needs to call:
            # component_Outputs(on its retvals) itself
    return Decorated


class NonObsoleteGHPythonComponent(component):
    def __init__(self, *args, **kwargs):
        super(NonObsoleteGHPythonComponent, self).__init__(*args, **kwargs)
        try:
            ghdoc.Component.ToggleObsolete(False)
        except AttributeError:
            pass

class MyComponentWithMain(NonObsoleteGHPythonComponent):


    def __init__(self, *args, **kwargs):
        super(MyComponentWithMain, self).__init__(*args, **kwargs)


    """Framework for a 'smart' grasshopper component, supporting kwargs type 
       inputs from user-customisable Input Params, default values,
       and returning suitable
       outputs based on the user specified Output Params.  """
    def script(self, *args, **kwargs):
        """ Specify the main script / method here instead of RunScript. 
            In an instance of CustomInputsComponent or in a class produced
            by the custom_inputs_class_deco decorator, RunScript now inspects 
            the call signature of this method, then parses the components 
            input Param's matching them up accordingly, then calls this method.

            To also use Custom Outputs in your own code, you need to add the 
            method component_Outputs to the component, in 
            your own code end each exit point of script with
            'return self.component_Outputs(sources)' with 
            sources as a list of whichever dicts or namedtuples whose contents 
            you wish to make available on the Output params.
            
            By default the locals in the scope of script are added to sources so
            sources can be omitted.  
            
            Returning primitives is not supported - 
            create a local variable in the function body with the same name as
            the Output Param you want it on, and assign the primitive to it."""
        return kwargs

    def RunScript(self, *args):
        """The normal method called by Grasshopper when Param Inputs update 
           etc.  A normal component RunScript method can be renamed and saved, 
           then overridden using the custom_inputs_class_deco decorator on the 
           class, in order to use allow the normal RunScript Method to adjust 
           its args according to custom Param inputs, and utilise them akin 
           to **kwargs"""
    # type (bool, str, Rhino Geometry, datatree, tuple(namedtuple,namedtuple), *dict)->bool, str, Rhino_Geom, datatree, str

CustomInputsComponent = custom_inputs_class_deco(MyComponentWithMain)

SmartComponent = custom_inputs_class_deco(MyComponentWithMain)
# Avoid yet another level of inheritance.
SmartComponent.component_Outputs = component_Outputs



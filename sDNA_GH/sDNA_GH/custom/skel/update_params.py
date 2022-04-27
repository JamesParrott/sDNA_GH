#! Grasshopper Python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import itertools

from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper
import scriptcontext as sc


def check_IO(IO):
    if IO not in ('Output', 'Input'):
        raise ValueError("IO needs to be in ('Output', 'Input')")    

def param_names(params, IO):
    check_IO(IO)
    return [param.NickName for param in getattr(params, IO)]
#            for param in getattr(ghenv.Component.Params,IO)]

def remove_param(params, param, IO, protected):
    check_IO(IO)
    registers = dict(Input  = 'UnregisterInputParameter'
                    ,Output = 'UnregisterOutputParameter'
                    )
    index_registers = dict(Input  = 'IndexOfInputParam'
                          ,Output = 'IndexOfOutputParam'
                          )
    if param in getattr(params, IO) and (
       param.NickName not in protected or
       IO == 'Output'):
        
        #index, param = [(i, x) 
        #               for i, x in enumerate(getattr(params, IO)) 
        #               if x.NickName == name
        #               ][0]
        index = getattr(params, index_registers[IO])(str(param))
        getattr(params, registers[IO])(param, index)
        #Params.Input.Remove(param)
        params.OnParametersChanged()

def make_new_param(name):
        param = Grasshopper.Kernel.Parameters.Param_ScriptVariable()
        # param = Grasshopper.Kernel.Parameters.Param_Point()
        param.NickName = name
        param.Name = name
        param.Description = name
        param.Access = Grasshopper.Kernel.GH_ParamAccess.list
        param.Optional = True

        return param

def add_param(params, param, IO):
    check_IO(IO)

    if param.NickName not in param_names(params, IO):

        #index = getattr(params, IO).Count
        registers = dict(Input  = 'RegisterInputParam'
                        ,Output = 'RegisterOutputParam'
                        )
        getattr(params,registers[IO])(param)#, index)
        #ghenv.Component.Params.RepairParamAssociations()
        params.OnParametersChanged()


def add_params(params, IO, param_names, protected):
    check_IO(IO)
    #for param in getattr(params, IO)[:]:
    #    if param.NickName not in param_names:
    #        remove_param(params, param, IO, protected)
    
    for param_name in param_names:
        if param_name not in getattr(params, IO):
            add_param(params, make_new_param(param_name), IO)


def remove_params(params, IO, param_names, protected):
    check_IO(IO)
    for param in getattr(params, IO)[:]:
       if param.NickName not in param_names:
           remove_param(params, param, IO, protected)
    
def add_remove_params(params, IO, param_names, protected):
    check_IO(IO)
    add_params(params, IO, param_names, protected)
    remove_params(params, IO, param_names, protected)

def update_params(params, inputs, outputs, protected):
    
    ParamsSyncObj = params.EmitSyncObject()
    add_remove_params(params, 'Output', outputs, protected)
    add_remove_params(params, 'Input', inputs, protected)
    params.Sync(ParamsSyncObj)
    params.RepairParamAssociations()

class MyComponent(component):
    
    # Before __init__ has run,
    # use ghenv.Component for self
    
    protected = ('x','y','z')
    
    def __init__(self, *args):
        component.__init__(self, *args)

        # self.Params doesn't work in __init__ yet
        # Use ghenv.Component instead
        
    def RunScript(self, *args):

        x = args[0] if args else False
        y = args[1] if len(args) >= 2 else ''
        z = args[2] if len(args) >= 3 else False
        
        outputs = list('womble')
        inputs = ['remember',"you're",'a']
        if sc.sticky.get('no inputs', False):
            inputs = ()        
        if sc.sticky.get('no outputs', False):
            outputs = ()
        if len(self.Params.Output)==0 and len(self.Params.Input)==0 :
           update_params(params = self.Params
                        ,inputs = inputs
                        ,outputs = outputs
                        ,protected = self.protected
                        )
        
        #print ghenv.Component.Params
        
        # return outputs if you have them; here I try it for you:
        return tuple(itertools.repeat(None, len(self.Params.Output)))
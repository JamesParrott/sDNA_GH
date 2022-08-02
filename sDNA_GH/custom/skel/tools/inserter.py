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


__author__ = 'James Parrott'
__version__ = '0.07'

import logging
import collections
if hasattr(collections, 'Iterable'):
    Iterable = collections.Iterable 
else:
    import collections.abc
    Iterable = collections.abc.Iterable

import GhPython



logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def nick_names_that_map_to(names, name_map):
    #type(list, dict) -> list
    if isinstance(names, str):
        names = [names]
    #nick_names = [nick_name for nick_name, mapped_names in name_map._asdict().items()
    #              if (nick_name not in names and 
    #                  any((name == mapped_names or name in mapped_names) for name in names))]
    #nick_names += nick_names_that_map_to(nick_names, name_map)
    #nick_names += names

    nick_names = [nick_name for nick_name in name_map if name_map[nick_name] in names
                                                         and nick_name not in names
                 ] 
    if nick_names == []:
        return names
    else:
        return nick_names_that_map_to(nick_names + names, name_map)


def are_GhPython_components_in_GH(component, names):
    #type(str)->bool
    doc = component.Attributes.Owner.OnPingDocument() 
    return any( type(GH_component) is GhPython.Component.ZuiPythonComponent 
                and GH_component.NickName in names
                for GH_component in doc.Objects
              )



def connected_components(up_or_downstream, Params):
    #type(str, type[any]) -> bool

    IO = {'upstream':'Input', 'downstream':'Output'}
    connected = {'upstream':'Sources', 'downstream':'Recipients'}
    if up_or_downstream not in IO.keys():
        msg = 'Value: %s not in %s ' % (up_or_downstream. IO.keys())
        logger.error(msg)
        raise ValueError(msg)


    comps= [comp.Attributes.GetTopLevel.DocObject
            for param in getattr(Params
                                ,IO[up_or_downstream]
                                ) 
            for comp in getattr(param
                                ,connected[up_or_downstream]
                                )
            ]
    logging.debug(comps)
    return comps

def downstream_components(Params):
    return [recipient.Attributes.GetTopLevel.DocObject
            for param in Params.Output 
            for recipient in param.Recipients
            ]

def are_any_GhPython_comps(up_or_downstream, names, Params):
    #type(str, list, type[any])-> bool
    comps = connected_components(up_or_downstream, Params) #compnt, Params)
    GhPython_compnt_NickNames = [ comp.NickName for comp in comps
                                  if type( comp.Attributes.GetTopLevel.DocObject ) 
                                  is GhPython.Component.ZuiPythonComponent
                                ]
    logger.debug('GhPython comp nicknames = %s ' % GhPython_compnt_NickNames)

    return ( any(name in GhPython_compnt_NickNames 
                for name in names
                )
            or
            any(are_any_GhPython_comps(up_or_downstream, names, comp.Params) 
                for comp in comps
                if hasattr(comp, 'Params') 
                ) 
            )
            
def are_GhPython_downstream(names, Params):
    comps = downstream_components(Params) #component, Params)
    GhPython_compnt_NickNames = [ comp.NickName for comp in comps
                                  if type( comp.Attributes.GetTopLevel.DocObject ) 
                                     is GhPython.Component.ZuiPythonComponent
                                ]
    return ( any(name in GhPython_compnt_NickNames 
                 for name in names
                 )
             or
             any(are_GhPython_downstream(names, comp.Params) 
                 for comp in comps
                 if hasattr(comp, 'Params') 
                 ) 
            )

up_or_downstream_dict = dict(before = 'upstream'
                            ,after =  'downstream'
                            )



def already_inserted(up_or_downstream
                    ,tool_to_insert
                    ,tools_dict
                    ,name_map
                    ,Params
                    ):
    #type(str, type[any], dict, dict, type[any]) -> bool
    logger.debug('Checking if tool ' 
                +str(tool_to_insert) 
                +' already inserted... '
                )
    already_have_tool = [name for name, tools in tools_dict.items() 
                              if tool_to_insert is tools or 
                                 ( isinstance(tools, Iterable) and 
                                 tool_to_insert in tools )  
                        ]
                    # tools_dict is keyed on all present nick names 
                    # as well as names of tools defined in this module
    logger.debug('already_have_tool == %s ' % already_have_tool)


    return are_any_GhPython_comps(up_or_downstream
                                 ,already_have_tool
                                 ,Params
                                 )

def insert_tool(before_or_after
               ,tools # mutated, by the inserted tool
               ,Params
               ,tool_to_insert
               ,is_target
               ,not_a_target
               ,tools_dict
               ,name_map
               ,already_inserted = already_inserted
               ):
    #type(type[any], str, list, type[any], class, function, list) -> list
    assert before_or_after in ('before', 'after')
    up_or_downstream = up_or_downstream_dict[before_or_after]
    offset = 1 if before_or_after == 'after' else 0

    possible_targets = [tool for tool in tools if tool not in not_a_target]
    logger.debug("Possible targets == %s " % possible_targets)

    if not possible_targets:  
        return None
        # Not just last tool.  Else no point checking more
        # than one downstream component?  The user may 
        # wish to do other stuff after the tool.

    if  not already_inserted(up_or_downstream
                            ,tool_to_insert
                            ,tools_dict
                            ,name_map
                            ,Params
                            ): 
                            # check tool not already there in another 
                            # component that will be executed next.
                            # TODO: None in entire canvas is too strict?
        for i, tool in enumerate(tools):
            logger.debug('is_target(tool) : %s ' % is_target(tool))
            logger.debug('tool : %s ' % tool)
            if before_or_after == 'after':
                tools_run_anyway = tools[i:] 
            else:
                tools_run_anyway = tools[:i] 

            if is_target(tool) and tool_to_insert not in tools_run_anyway:
                        # check tool not already inserted 
                        # in tools after specials
                logger.info('Inserting tool : %s ' % tool_to_insert)
                tools.insert(i + offset, tool_to_insert)

    

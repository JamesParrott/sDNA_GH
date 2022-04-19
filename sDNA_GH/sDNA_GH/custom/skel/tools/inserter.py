#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys, logging
if sys.version < '3.3':
    from collections import Iterable
else:
    from collections.abc import Iterable

import GhPython

from .helpers.funcs import tool_name


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


def are_GhPython_components_in_GH(compnt, names):
    #type(str)->bool
    doc = compnt.Attributes.Owner.OnPingDocument() 
    return any( type(GH_component) is GhPython.Component.ZuiPythonComponent 
                and GH_component.NickName in names
                for GH_component in doc.Objects
              )



def connected_components(up_or_downstream, Params):
    #type(str, type[any]) -> bool

    IO = {'upstream':'Input', 'downstream':'Output'}
    connected = {'upstream':'Sources', 'downstream':'Recipients'}
    if up_or_downstream not in IO.keys():
        msg = 'Value : ' + str(up_or_downstream) + ' not in ' + str(IO.keys())
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
    logger.debug('GhPython comp nicknames = ' + str(GhPython_compnt_NickNames))

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
    comps = downstream_components(Params) #compnt, Params)
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
    logger.debug('already_have_tool == ' + str(already_have_tool))
    #logger.debug(tools_dict)
    #if (  not are_GhPython_components_in_GH(compnt, already_have_tool) and

    #logger.debug(name_map)
    #logger.debug(tool_name(tool_to_insert))

    #nick_names = nick_names_that_map_to(tool_name(tool_to_insert), name_map)
    #nick_names += already_have_tool
    #logger.debug('nick_names == '+ str(nick_names))



    # tool_in_other_components = 

    # logger.debug('tool_in_other_components == ' 
    #         + str(not tool_in_other_components) 
    #         )

    return are_any_GhPython_comps(up_or_downstream
                                 ,already_have_tool
                                 ,Params
                                 )

def insert_tool(before_or_after
               ,tools
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

    possible_targets = any(tool not in not_a_target 
                                           for tool in tools
                          )
    logger.debug("Possible targets == " + str(possible_targets))

    if possible_targets:  
                    # Not just last tool.  Else no point checking more
                    # than one downstream component?  The user may 
                    # wish to do other stuff after the tool

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
                logger.debug('is_target(tool) : ' + str(is_target(tool)))
                logger.debug('tool : ' + str(tool))
                if before_or_after == 'after':
                    tools_run_anyway = tools[i:] 
                else:
                    tools_run_anyway = tools[:i] 

                if is_target(tool) and tool_to_insert not in tools_run_anyway:
                         # check tool not already inserted 
                         # in tools after specials
                    logger.info('Inserting tool : ' + str(tool_to_insert))
                    tools.insert(i + offset, tool_to_insert)
    return tools

    
def remove_component_output(self, name):
    """Very buggy and glitchy.  But this is how you can do it... """
    for param in self.Params.Output:
        if param.NickName == name:
            self.Params.UnregisterOutputParam(param)
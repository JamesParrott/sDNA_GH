#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

import GhPython

from .helpers.funcs import tool_name


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
#
#
class Connected_Components():
    IO = {'upstream':'Input', 'downstream':'Output'}
    connected = {'upstream':'Sources', 'downstream':'Recipients'}
                    
    def __call__(self, up_or_downstream, Params):
        #type(str, type[any]) -> bool
        assert up_or_downstream in self.keys
        return [comp.Attributes.GetTopLevel.DocObject
                for param in getattr(Params
                                    ,self.IO[up_or_downstream]
                                    ) 
                for comp in getattr(param
                                   ,self.connected[up_or_downstream]
                                   )
                ]
connected_components = Connected_Components()

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
    already_have_tool = [name for name, tool_list in tools_dict.items() 
                        if tool_to_insert in tool_list]
                    # tools_dict is keyed on all present nick names 
                    # as well as names of tools defined in this module
    logging.debug(already_have_tool)
    logging.debug(tools_dict)
    #if (  not are_GhPython_components_in_GH(compnt, already_have_tool) and

    logging.debug(name_map)

    nick_names = nick_names_that_map_to(tool_name(tool_to_insert), name_map)
    nick_names += already_have_tool
    logging.debug(nick_names)



    # tool_in_other_components = 

    # logging.debug('tool_in_other_components == ' 
    #         + str(not tool_in_other_components) 
    #         )

    return are_any_GhPython_comps(up_or_downstream
                                 ,nick_names
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
               ,tool_insert_check = already_inserted
               ):
    #type(type[any], str, list, type[any], class, function, list) -> list
    assert before_or_after in ('before', 'after')
    up_or_downstream = up_or_downstream_dict[before_or_after]
    offset = 1 if before_or_after == 'after' else 0

    possible_targets = any(tool_name(tool) not in not_a_target 
                                           for tool in tools
                          )
    if possible_targets:  
                    # Not just last tool.  Else no point checking more
                    # than one downstream component?  The user may 
                    # wish to do other stuff after the tool
                    # and name_map is now a meta option too.

        if  tool_insert_check(up_or_downstream
                             ,tool_to_insert
                             ,tools_dict
                             ,name_map
                             ,Params
                             ): 
                             # check tool not already there in another 
                             # component that will be executed next.
                             # TODO: None in entire canvas is too strict?
            for i, tool in enumerate(tools):
                logging.debug('is_target(tool) : ' + str(is_target(tool)))
                logging.debug('tool : ' + str(tool))
                if before_or_after == 'after':
                    tools_run_anyway = tools[i:] 
                else:
                    tools_run_anyway = tools[:i] 

                if is_target(tool) and tool_to_insert not in tools_run_anyway:
                         # check tool not already inserted 
                         # in tools after specials
                    logging.info('Inserting tool : ' + str(tool_to_insert), 'INFO')
                    tools.insert(i + offset, tool_to_insert)
    return tools
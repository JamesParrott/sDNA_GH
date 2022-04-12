#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'

import sys, logging
if sys.version < '3.3':
    from collections import Hashable
else:
    from collections.abc import Hashable


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def validate_name_map(name_map, known_tool_names):
    #type(dict, list) -> bool
    if not isinstance(name_map, dict):
        msg = ('Name map is of type: ' + str(type(name_map))
              +'but is required to be a dictionary.  '
              )
        logger.error(msg)
        raise TypeError(msg)
                                                            # No nick names allowed that are 
                                                            # a tool's full / real name.
    nickname_clashes = [name for name in known_tool_names if name in name_map]
    if nickname_clashes:
        msg = ('Nick names in name map clash with known tool names: ' 
              +' '.join(nickname_clashes)
              )
        logger.error(msg)
        raise ValueError(msg)
    else:
        logger.debug('No clashes found in name_map with known tool names.'
                     +' Good job! '
                     )

    
    names_and_nicknames = known_tool_names + list(name_map.keys())
    def points_to_valid_tools(tool_names):
        if not isinstance(tool_names, list):
            tool_names = [tool_names]
        return all(name in names_and_nicknames for name in tool_names)
    invalid_name_map_vals = {key : val for key, val in name_map._asdict().items()
                                        if not points_to_valid_tools(val)}

    if invalid_name_map_vals:
        msg = ('Invalid name_map entries: ' 
              +'\n'.join([k + (v if not isinstance(v, list) else
                               ' '.join([n for n in v if not points_to_valid_tools(n)])
                              )
                          for k, v in invalid_name_map_vals.items()
                         ])
              )
        logger.error(msg)
        raise ValueError(msg)
    else:
        logger.info('Name_map links all point to known names or other name_map links. Cycles not checked. ','INFO')

    return True


def tool_not_found_error(mapped_name
                        ,name_map
                        ,tools_dict
                        ):
    raise ValueError('Tool: ' + mapped_name + ' not found')


def tool_factory(nick_name
                ,name_map
                ,tools_dict
                ,tool_not_found = tool_not_found_error 
                ):  
    #type( str, dict, dict, function ) -> list

    if not isinstance(nick_name, Hashable):
        msg = 'Non-hashable variable given for key' + str(nick_name)
        logging.error(msg)
        raise TypeError(msg)

    if nick_name not in tools_dict:   
        map_result = getattr(name_map, nick_name, nick_name)  
        # in case nick_name is a tool_name
        
        if not isinstance(map_result, str):
            logging.debug('Processing list of tools found for ' + nick_name)
            tools =[]
            #nick_name_opts = {}
            for mapped_name in map_result:
                tools.append(tool_factory(mapped_name
                                         ,name_map 
                                         ,tools_dict
                                         ,tool_not_found
                                         )
                            )

            if len(tools) == 1:
                tools = tools[0]
            tools_dict.setdefault(nick_name, tools )
        else:
            mapped_name = map_result
            logging.debug(nick_name + ' maps to ' + mapped_name)
            if mapped_name in tools_dict:
                logging.debug('Tool: ' + mapped_name + ' already in tools_dict')
            else:
                tool_not_found(mapped_name
                              ,name_map
                              ,tools_dict
                              )


    logging.debug('tools_dict[' + nick_name + '] == ' + str(tools_dict[nick_name]) )
    return tools_dict[nick_name] 
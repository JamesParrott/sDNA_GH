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
__version__ = '3.0.1'

import os
import shutil
import logging
import collections
if hasattr(collections, 'Iterable'):
    Iterable = collections.Iterable 
else:
    import collections.abc
    Iterable = collections.abc.Iterable
import re

import Grasshopper
import GhPython
import System.Drawing  # .Net / C# Classes, System is in Iron Python.  But 
                       # System.Drawing is not.  Needs Iron pip?
from .basic.ghdoc import ghdoc
from .tools import runner
from . import add_params


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


try:
    basestring #type: ignore
except NameError:
    basestring = str




def update_compnt_and_make_user_obj(component
                                   ,name
                                   ,tool_name
                                   ,subcategory
                                   ,description
                                   ,position
                                   ,plug_in_name
                                   ,dest
                                   ,icons_path = None
                                   ,icon = None
                                   ,locked = False
                                   ,overwrite = False
                                   ,add_to_canvas = True
                                   ,move_user_object = False
                                   ,update = False
                                   ):
    # type(type[any], str, str, str, str, list, str, str, str, str, bool, bool, bool, bool, bool) -> type[any]



    user_object = Grasshopper.Kernel.GH_UserObject()

    sizeF = System.Drawing.SizeF(*position)

    component.Attributes.Pivot = System.Drawing.PointF.Add(component.Attributes.Pivot, sizeF)

    if icon is None:
        if (isinstance(icons_path, basestring) and 
            isinstance(tool_name, basestring)):
            #
            icon = os.path.join(icons_path, tool_name + '.png')

    if icon is not None:
        logger.debug('Adding icon: %s to user_object: %s' % (icon, name))
        user_object.Icon = System.Drawing.Bitmap(icon)

    user_object.BaseGuid = component.ComponentGuid
    component.Description = user_object.Description.Description = description
    
    component.SubCategory = user_object.Description.SubCategory = subcategory 
    component.Category = user_object.Description.Category = plug_in_name
    user_object.Exposure = component.Exposure.primary

    component.Locked = locked 

    component.NickName = user_object.Description.NickName = name
    component.Name = user_object.Description.Name = name   

    #user_object.Description.Name = tool_name if isinstance(tool_name, basestring) else name
    # this determines the .ghuser filename

    if add_to_canvas:
        GH_doc = ghdoc.Component.Attributes.Owner.OnPingDocument()
        GH_doc.AddObject(docObject = component, update = update)

    
    user_object.SetDataFromObject(component)
    user_object.CreateDefaultPath(True)
    user_object.SaveToFile()
 
    if move_user_object:
        if not dest:
            raise ValueError('No destination specified to move user objects to. ')
        if not os.path.isdir(dest):
            os.makedirs(dest)
        elif overwrite:
            # Avoid OSError on Windows, in shutil.move below
            dest_file = os.path.join(dest
                                    ,os.path.basename(user_object.Path)
                                    )
            if os.path.isfile(dest_file):
                os.remove(dest_file)

        logger.debug('Moving user object %s to %s' % (user_object.Description.Name, dest))

        # "If the destination already exists but is not a directory, it may 
        # be overwritten depending on os.rename() semantics."
        # https://docs.python.org/2.7/library/shutil.html#shutil.move
        # "On Windows, if dst already exists, 
        # OSError will be raised even if it is a file "
        # https://docs.python.org/2.7/library/os.html#os.rename

        path = os.path.join(dest, os.path.basename(user_object.Path))

        shutil.move(user_object.Path, dest)

    else:
        path = user_object.Path
        logger.debug('Not moving user object %s ' % user_object.Description.Name)


    return user_object, path

def text_file_to_str(file, extra_new_line_char = '', encoding = 'utf-8', **kwargs):
    #type(str, str) -> str
    """ A simple text file reader.  """
    if file is None or not isinstance(file, basestring):
        msg = 'file == %s is not a string' % file
        logger.error(msg)
        raise TypeError(msg)
    elif not os.path.isfile(file):
        msg = 'file == %s is not a file path' % file
        logger.error(msg)
        raise ValueError(msg)
    else:
        with open(file, 'rb') as f:
            file_contents = extra_new_line_char.join(line.decode(encoding)
                                                     for line in f
                                                    )
    return file_contents


class DocStringParser(object):
    
    doc_string_summary_line_pattern = re.compile(r'"""(.*?)"""'
                                                ,flags = re.DOTALL
                                                ) # so . will match \n
    def __call__(self, code):
        #type(str)-> str, str
        doc_string_match = self.doc_string_summary_line_pattern.search( code )

        if not doc_string_match:
            msg = 'No regex match found for docstring in launcher code.'
            logger.error(msg)
            raise ValueError(msg)

        doc_string_content = doc_string_match.groups()[0]

        doc_string = doc_string_match.group()

        return doc_string_content, doc_string


def build_comps_with_docstring_from_readme(default_path
                                          ,component_names
                                          ,name_map
                                          ,categories
                                          ,category_abbrevs
                                          ,icons_path
                                          ,move_user_objects = False                              
                                          ,path_dict = {}                                          
                                          ,readme_path = None
                                          ,row_height = None
                                          ,row_width = None
                                          ,**kwargs
                                          ):
    # = (kwargs[k] for k in self.args)
    if isinstance(component_names, basestring):
        component_names = [component_names]

    logger.debug('categories.keys() == %s' % categories.keys())
    logger.debug('name_map.keys() == %s' % name_map.keys())
    


    row_height = row_height or 175
    row_width = row_width or 800

    
    while (isinstance(default_path, Iterable) 
            and not isinstance(default_path, basestring)):
        default_path = default_path[0]


    readme = text_file_to_str(readme_path)

    logger.debug('readme[:20] == %s' % readme[:20])

    logger.info('User objects (.ghuser files) dest: %s' % kwargs['dest'])

    user_obj_paths = []

    get_doc_string = DocStringParser()

    for i, nick_name in enumerate(component_names):
        tool_name = name_map.get(nick_name, nick_name)
        logger.debug('%s is a nick name for the tool %s' % (nick_name, tool_name))
        tool_code_path = path_dict.get(tool_name, default_path)
        tool_code = text_file_to_str(tool_code_path, **kwargs)

        doc_string_content, _ = get_doc_string(tool_code)

        if tool_name not in categories:
            msg =  'No category for ' + nick_name
            logger.error(msg)
            raise ValueError(msg)

        subcategory = categories[tool_name]
        subcategory = category_abbrevs.get(subcategory, subcategory)
        logger.debug('Placing tool: %s in category: %s.' % (tool_name, subcategory))

        logger.debug('Building tool with (nick)name = %s' % nick_name)
        if readme:
            logger.debug('Looking in readme for tool with name = %s' % tool_name)


            # Match everything in readme following tool_name and a newline, up to two blank lines.
            tool_summary_pattern = re.compile(r'\(%s\)\r?\n(.*?\r?\n)(\r?\n){2}' % tool_name
                                                ,flags = re.DOTALL # so . will match \n
                                                )
            logger.debug('tool_summary_pattern == %s' % tool_summary_pattern.pattern)

            summary_match = tool_summary_pattern.search( readme )
            if summary_match:
                summary = summary_match.groups()[0]
                tool_code = tool_code.replace(doc_string_content, summary)
                logger.debug('updating tool_code with summary')
            else:
                logger.debug('No summary found for tool: %s.  Tool_code unchanged.' % tool_name)
                summary = doc_string_content

        h = i * row_height
        x = 200 + (h % row_width)
        y = 550 + 220 * (h // row_width)
        position = [x, y]

        gh_python_comp = GhPython.Component.ZuiPythonComponent()
        gh_python_comp.Code = tool_code
        gh_python_comp.IsAdvancedMode = True

        for name, IO in zip(('a', 'x', 'y'), ('Output', 'Input', 'Input')):
            add_params.delete_Param(gh_python_comp.Params, name, IO)
        #gh_python_comp.Params.Clear()


        user_obj, path = update_compnt_and_make_user_obj(
                                         component = gh_python_comp
                                        ,name = nick_name
                                        ,tool_name = tool_name
                                        ,subcategory = subcategory
                                        ,description = summary
                                        ,position = position
                                        ,icons_path = icons_path  
                                        ,locked = False  # all new compnts run
                                        ,move_user_object = move_user_objects
                                        ,**kwargs
                                        )

        logger.info('Successfully created User Object: %s' % user_obj.Description.NickName)

        if path:
            user_obj_paths.append(path)

    logger.info('User objects located at: %s' % set(os.path.dirname(path) 
                                                    for path in user_obj_paths
                                                   )
               )

    return user_obj_paths







class ComponentsBuilder(add_params.ToolWithParams, runner.RunnableTool): 
    component_inputs = ('default_path'
                       ,'path_dict'
                       ,'plug_in_name'
                       ,'component_names'
                       ,'name_map'
                       ,'categories'
                       ,'category_abbrevs'
                       ,'readme_path'
                       ,'add_to_canvas'
                       ,'row_height'
                       ,'row_width'
                       )

    def __call__(self, *args, **kwargs):

        names_built = build_comps_with_docstring_from_readme(*args, **kwargs)

        retcode = 0
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)
    
    retvals = ('retcode', 'names_built')



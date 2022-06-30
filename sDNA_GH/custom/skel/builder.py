#! /usr/bin/awk NR==3
# -*- coding: utf-8 -*-
# This module requires Grasshopper Python (Rhino3D)

# MIT License

# Copyright (c) [2021] [Cardiff University, a body incorporated
# by Royal Charter and a registered charity (number:
# 1136855) whose administrative offices are at 7th floor 30-
# 36 Newport Road, UniversityCF24 0DE, Wales, UK]

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
__version__ = '0.04'

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

ghuser_folder = os.path.join('components', 'automatically_built')


def update_compnt_and_make_user_obj(component
                                   ,name
                                   ,tool_name
                                   ,plug_in_name
                                   ,subcategory
                                   ,description
                                   ,position
                                   ,plug_in_sub_folder = None
                                   ,user_objects_location = None
                                   ,icons_path = None
                                   ,locked = True
                                   ,add_to_canvas = True
                                   ,overwrite = False
                                   ,update = False
                                   ):
    # type(type[any], str, str, str, str, str, list, str, str, bool, bool) -> int

    if plug_in_sub_folder is None:
        plug_in_sub_folder = plug_in_name

    if user_objects_location is None:
        user_objects_location = os.path.join(Grasshopper.Folders.DefaultUserObjectFolder
                                            ,plug_in_sub_folder
                                            ,ghuser_folder
                                            )
    
    if not os.path.isdir(user_objects_location):
        os.mkdir(user_objects_location)


    user_object = Grasshopper.Kernel.GH_UserObject()

    sizeF = System.Drawing.SizeF(*position)

    component.Attributes.Pivot = System.Drawing.PointF.Add(component.Attributes.Pivot, sizeF)

    if icons_path is None:
        icons_path = os.path.join(os.path.dirname(user_objects_location), 'icons')

    if isinstance(tool_name, basestring) and isinstance(icons_path, basestring):
        icon_path = os.path.join(icons_path, tool_name + '.png')
        if os.path.isfile(icon_path):
            user_object.Icon = System.Drawing.Bitmap(icon_path)

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
        success = GH_doc.AddObject(docObject = component, update = update)
    else:
        success = True  # could improve this.
    
    user_object.SetDataFromObject(component)
    user_object.CreateDefaultPath(True)
    user_object.SaveToFile()
    
    if not os.path.isdir(user_objects_location):
        os.mkdir(user_objects_location)
    elif overwrite:
        dest_file = os.path.join(user_objects_location
                                ,os.path.basename(user_object.Path)
                                )
        if os.path.isfile(dest_file):
            os.remove(dest_file)


    shutil.move(user_object.Path, user_objects_location)


    return success

def text_file_to_str(file, extra_new_line_char = '', encoding = 'utf-8'):
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
                                                )
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
                                          ,path_dict = {}                                          
                                          ,readme_path = None
                                          ,row_height = None
                                          ,row_width = None
                                          ,**kwargs
                                          ):
    #type(str, dict, str, list, dict, dict, dict, str, int, int) -> int, list
    # = (kwargs[k] for k in self.args)
    row_height = 175 if row_height is None else row_height
    row_width = 800 if row_width is None else row_width

    
    while (isinstance(default_path, Iterable) 
            and not isinstance(default_path, str)):
        default_path = default_path[0]



    readme = text_file_to_str(readme_path)

    logger.debug('readme[:20] == %s' % readme[:20])



    names_built = []

    get_doc_string = DocStringParser()

    for i, nick_name in enumerate(component_names):
        tool_name = name_map.get(nick_name, nick_name)
        tool_code_path = path_dict.get(tool_name, default_path)
        tool_code = text_file_to_str(tool_code_path)

        doc_string_content, _ = get_doc_string(tool_code)

        if tool_name not in categories:
            msg =  'No category for ' + nick_name
            logging.error(msg)
            raise ValueError(msg)
        else:



            subcategory = categories[tool_name]
            subcategory = category_abbrevs.get(subcategory, subcategory)

            logger.debug('Building tool with (nick)name = %s' % nick_name)
            if readme:
                logger.debug('Looking in readme for tool with name = %s' % tool_name)

                tool_summary_pattern = re.compile(r'\(%s\)\r?\n(.*?\r?\n)(\r?\n){2}' % tool_name
                                                    ,flags = re.DOTALL
                                                    )
                logger.debug('tool_summary_pattern == %s' % tool_summary_pattern.pattern)

                summary_match = tool_summary_pattern.search( readme )
                if summary_match:
                    summary = summary_match.groups()[0]
                    tool_code = tool_code.replace(doc_string_content, summary)
                    logger.debug('updating tool_code with summary')
                else:
                    logger.debug('tool_code unchanged.')
                    summary = doc_string_content

            l = i * row_height
            x = 200 + (l % row_width)
            y = 550 + 220 * (l // row_width)
            position = [x, y]

            gh_python_comp = GhPython.Component.ZuiPythonComponent()
            gh_python_comp.Code = tool_code
            gh_python_comp.IsAdvancedMode = True

            for name, IO in zip(('a','x','y'),('Output','Input','Input')):
                add_params.delete_Param(gh_python_comp.Params, name, IO)
            #gh_python_comp.Params.Clear()


            success = update_compnt_and_make_user_obj(
                                             component = gh_python_comp
                                            ,name = nick_name
                                            ,tool_name = tool_name
                                            ,subcategory = subcategory
                                            ,description = summary
                                            ,position = position
                                            ,locked = False  # all new compnts run
                                            ,**kwargs
                                            )
            if success:
                names_built += [nick_name]

    # CRASHES GRASSHOPPER!!
    # readme_ghuser_file = 'Readme.txt.ghuser'  

    # if not os.path.isfile( os.path.join(user_objects_location, readme_ghuser_file)):
    #     readme_component = Grasshopper.Kernel.Special.GH_Panel()
    #     readme_component.SetUserText(readme)
    #     success = update_compnt_and_make_user_obj(
    #                              component = readme_component
    #                             ,name = readme_ghuser_file.rpartition('.')[0]
    #                             ,tool_name = readme_ghuser_file.rpartition('.')[0]
    #                             ,plug_in_name = plug_in_name
    #                             ,subcategory = 'Extra'
    #                             ,description = 'Usage and installation info for %s. ' % plug_in_name
    #                             ,position = [position[0] + row_width, position[1]]
    #                             ,locked = False  # all new compnts run
    #                             ,**kwargs
    #                             )
    return names_built




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



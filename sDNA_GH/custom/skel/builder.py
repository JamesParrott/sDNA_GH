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
__version__ = '0.02'

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


def make_comp_and_user_obj(name
                          ,tool_name
                          ,plug_in_name
                          ,subcategory
                          ,launcher_code
                          ,description
                          ,position
                          ,user_objects_location = None
                          ,icons_path = None
                          ,locked = True
                          ,SDK_not_script = True
                          ,add_to_canvas = True
                          ,ComponentClass = None
                          ):
    # type(str, str, str, str, str, str, list, str, str, bool, bool, bool, type[any]) -> int

    if user_objects_location is None:
        user_objects_location = os.path.join(os.path.dirname(os.path.dirname(ghdoc.Path))
                                       ,plug_in_name
                                       ,'components'
                                       )
    
    if not os.path.isdir(user_objects_location):
        os.mkdir(user_objects_location)

    if ComponentClass is None:
        ComponentClass = GhPython.Component.ZuiPythonComponent 

    new_comp = ComponentClass()
    user_object = Grasshopper.Kernel.GH_UserObject()

    sizeF = System.Drawing.SizeF(*position)

    new_comp.Attributes.Pivot = System.Drawing.PointF.Add(new_comp.Attributes.Pivot, sizeF)
    new_comp.Params.Clear()

    if icons_path is None:
        icons_path = os.path.join(user_objects_location, 'icons')

    if isinstance(tool_name, basestring):
        icon_path = os.path.join(icons_path, tool_name + '.png')
        if os.path.isfile(icon_path):
            user_object.Icon = System.Drawing.Bitmap(icon_path)

    user_object.BaseGuid = new_comp.ComponentGuid
    new_comp.Code = launcher_code
    new_comp.Description = user_object.Description.Description = description
    
    new_comp.IsAdvancedMode = SDK_not_script
    new_comp.SubCategory = user_object.Description.SubCategory = subcategory 
    new_comp.Category = user_object.Description.Category = plug_in_name
    user_object.Exposure = new_comp.Exposure.primary

    new_comp.Locked = locked 

    new_comp.NickName = user_object.Description.NickName = name
    new_comp.Name = name   

    user_object.Description.Name = tool_name if isinstance(tool_name, basestring) else name
    # this determines the .ghuser filename

    if add_to_canvas:
        GH_doc = ghdoc.Component.Attributes.Owner.OnPingDocument()
        success = GH_doc.AddObject(docObject = new_comp, update = True)
    
    user_object.SetDataFromObject(new_comp)
    user_object.CreateDefaultPath()
    user_object.SaveToFile()
    
    if not os.path.isdir(user_objects_location):
        os.mkdir(user_objects_location)
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
        logger.debug('doc_string_content == %s' % doc_string_content)

        doc_string = doc_string_match.group()
        logger.debug('doc_string_match == %s' % doc_string)

        return doc_string_content, doc_string


def build_comps_with_docstring_from_readme(default_path
                                          ,path_dict
                                          ,plug_in_name
                                          ,component_names
                                          ,name_map
                                          ,categories
                                          ,category_abbrevs
                                          ,add_to_canvas = True
                                          ,readme_path = None
                                          ,user_objects_location = None
                                          ,row_height = None
                                          ,row_width = None
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
                    logger.debug('summary == %s' % summary)
                    tool_code = tool_code.replace(doc_string_content, summary)
                    logger.debug('tool_code[:2400] == %s' % tool_code[:2400])
                else:
                    logger.debug('tool_code unchanged.')
                    summary = doc_string_content

            l = i * row_height
            x = 200 + (l % row_width)
            y = 550 + 220 * (l // row_width)
            position = [x, y]

            success = make_comp_and_user_obj(name = nick_name
                                            ,tool_name = tool_name
                                            ,plug_in_name = plug_in_name
                                            ,subcategory = subcategory
                                            ,launcher_code = tool_code
                                            ,description = summary
                                            ,position = position
                                            ,user_objects_location = user_objects_location
                                            ,locked = False  # all new compnts run
                                            ,SDK_not_script = True
                                            ,add_to_canvas = add_to_canvas
                                            ,ComponentClass = None # GhPython
                                            )
            if success:
                names_built += [nick_name]
    
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



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
__version__ = '3.0.5'


import Rhino
import GhPython
import scriptcontext as sc


def possible_ghdoc_types():

    try: 
        import RhinoCodePlatform.Rhino3D.Languages.GH1.Legacy
    except ImportError:
        pass
    else:
        yield RhinoCodePlatform.Rhino3D.Languages.GH1.Legacy.ProxyDocument
        return

    try:
        yield GhPython.DocReplacement.GrasshopperDocument
    except AttributeError:
        pass
    else:
        return


if 'ghdoc' not in globals():
    if sc.doc == Rhino.RhinoDoc.ActiveDoc:
        raise ValueError('sc.doc == Rhino.RhinoDoc.ActiveDoc. '
                        +'Switch sc.doc = ghdoc and re-import module. '
                        )
    
    # TODO:  Fix in a CPython3 components, in which
    # type(sc.doc)=<class 'RhinoCodePlatform.Rhino3D.Languages.GH1.Legacy.ProxyDocument'>

    ghdoc_type = next(possible_ghdoc_types())
    if isinstance(sc.doc, ghdoc_type):

        ghdoc = sc.doc  # Normally a terrible idea!  But the check conditions
                        # are strong, and we need to get the `magic variable'
                        # ghdoc in this 
                        # namespace as a global, from launcher and GH.
    else:
        raise TypeError(('sc.doc is not of type: %s ' % ghdoc_type.__name__)
                       +'Ensure sc.doc == ghdoc and re-import module.'
                       )


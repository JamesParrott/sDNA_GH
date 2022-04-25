#! Grasshopper Python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'


import Rhino
import GhPython
import scriptcontext as sc


if 'ghdoc' not in globals():
    if sc.doc == Rhino.RhinoDoc.ActiveDoc:
        raise ValueError('sc.doc == Rhino.RhinoDoc.ActiveDoc. '
                        +'Switch sc.doc = ghdoc and re-import module. '
                        )
    if isinstance(sc.doc, GhPython.DocReplacement.GrasshopperDocument):
        ghdoc = sc.doc  # Normally a terrible idea!  But the check conditions
                        # are strong, and we need to get the `magic variable'
                        # ghdoc in this 
                        # namespace as a global, from launcher and GH.
    else:
        raise TypeError('sc.doc is not of type: '
                       +'GhPython.DocReplacement.GrasshopperDocument '
                       +'Ensure sc.doc == ghdoc and re-import module.'
                       )


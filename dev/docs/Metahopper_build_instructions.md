## Dependencies.
#### Metahopper 
Metahopper provides programmatic automated building of the GH components suite, but this is only a convenience - the components can always be built manually too.

### Build instructions.
#### Build Prototype GHPython launcher / namer component
1. Install the add-on Metahopper to your Rhino 7 / Grasshopper (GH) application, e.g. from food4rhino.  
2. Open the builder GH definition [sDNA_GH_builder.gh](devtools/sDNA_GH_builder.gh)
3. Create a new GHPython component if needed.
4. Ensure there are enough input variables and output variables on the GHPython component. It must contain the superset of all inputs and all outputs for all the tools.  Names must be correct and are case-sensitive.  Mandatory inputs are: go, Data, Geom and f_name, as per required arguments of the RunScript() method in the launcher.  Other optional ones (accessed via *args) are: gdm, opts and l_metas.  The required outputs are: OK, Data, Geom and f_name, and also a, gdm, opts and l_metas.
5. Ensure all input variables on the GHPython component are set to *List Access* except Data which should be set to *Tree Access*.  *Item access* should be avoided for expensive processes, as repeated execution is possible, once per item of a list.  This is likely to crash sDNA_GH on accidental connection of large data sets (hover the cursor over them and right click). 
6. Change the GHPython component to *GH_Component SDK Mode*
7.  Make the GHPython component contain the code from [sDNA_GH_launcher.py](sDNA_GH_launcher.py) (largely the same as the 
code that will be in the sDNA_GH GHPython components in the example Grasshopper definition [sDNA_GH.gh](sDNA_GH.gh) ) by 
**EITHER**:
    -a) Turning on *Show "code" input parameter* and ensuring *Input is path* is off.
    -b) Connecting the code input parameter to the output of the Read File Parameter
    -c) Using the File Path Parameter to select [sDNA_GH_launcher.py](sDNA_GH_launcher.py) in your local repo (ensure the Read File component is set to *Total File*)
    -d) Right clicking the code input parameter and selecting *Internalise Data* (in doing so, automatically breaking the connection from this to the Read File component)
**OR**:
    - a) Copy and pasting via the clipboard, e.g. Ctrl+C + Ctrl+V.
    - b) Ensuring the connection  (if any) from the code input parameter to the Read File component is broken
8. Toggle off *Show "code" input parameter* on the GHPython component.
9.  This GHPython component will be used as the template/ prototype Launcher component.  In its source code, check the list of sDNA_GH-only support tools is complete, containing each support tool to be built into a component from the main package's eponymous module [sDNA_GH/sDNA_GH.py].
10. Check the hardcoded dictionary of pseudonyms (i.e. shorter names), for the sDNA tools and the support tools.  These pseudonyms will actually be displayed to Grasshopper users if they switch a component from *Always Draw Icon* to *Always Draw Name*.    
11. Change the template / prototype launcher component to *Always Draw Name* to the renaming process below. below can quickly be checked (i.e. without hovering the mouse cursor over every component's icon).

#### Build and name all sDNA_GH GHPython launcher components
12. Ensure there are enough new copies of the template / prototype sDNA_GH-Launcher GHPython component.  One for each of the tools in the sDNA_GH collection, both sDNA tools and support tools (i.e. at least 16 of them currently).  They must all contain the launcher code from [sDNA_GH_launcher.py](sDNA_GH_launcher.py) and all be in *GH_Component SDK Mode*.  If this has not been done already:
   -a) Create identical copies of the sDNA_GH Launcher component, e.g. by copy and pasting (e.g. selecting the component and pressing Ctrl+C, Ctrl+V).  At least 15 more (at least 16  in total) are required.  Each of the sDNA_GH support tools plus each sDNA class in sDNAUISpec.py for the sDNA version being wrapped (e.g. sDNAIntegral, sDNASkim, sDNAIntegralFromOD, sDNAGeodesics, sDNAHulls, sDNANetRadii, sDNAAccessibilityMap,sDNAPrepare, sDNALineMeasures, sDNALearn, sDNAPredict) along with the sDNA_General 'swiss army knife' needs its own sDNA_GH launcher component for the user to be able to use them as individual components for each tool.  
13. In the file path parameter component, check the path to the sDNAUISpec.py file is correct for the sDNA version being wrapped.
14. Make sure the list of names being output from the original Template GHPython component is correct in the text panel, and if so that it is connected to the Metahopper *Rename Object* component.
15. Select all the copies of the GHPython components, for both the sDNA tools and support tools.
16. Click Select on the Metahopper *Rename Object* component.  The GHPython components should now be renamed.
17. Select each component manually (compile it if so wished and place a compiled version on the canvas, then select that one instead)
18. Click File-> Create User object.  Allocate it to the sDNA_GH category and any subcategories you want.
#### Bundling
19. Save each resulting .GHPY file in the highest parent level of the sDNA_GH folder containing the files to be zipped (in the same sDNA_GH folder, as the other sDNA_GH folder containing a copy of the sDNA_GH Python package for this build).
20. Zip the folder to sDNA_GH.zip.
#### Installation
21. To install, copy sDNA_GH.zip to the user's Grasshopper special Components folder (e.g. %appdata%\Grasshopper\Libraries) and unzip there.
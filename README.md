# GHsDNA

sDNA is a world leading tool for Spatial Design Network Analysis.  GHsDNA is a plug-in for Grasshopper providing components that run the tools from a local [sDNA](https://sdna.cardiff.ac.uk/sdna/) installation, on Rhino and Grasshopper geometry and data.  

## sDNA
sDNA is able to calculate Betweenness, Closeness, Angular distance, and many other quantities including custom hybrid metrics, and is able to perform many other advanced functions as well.  Please note, for results of a network analysis to be meaningful, it must be ensured that the network is first properly [prepared](https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/network_preparation.html).

## GHsDNA functionality
GHsDNA: 
  - Reads a network's polyline Geometry and user specified Data from Rhino. <!-- TODO or reads a network from Geometry and Data created in Grasshopper, the Data Tree being in our required format -->
  - Writes the network links (formed by one or more polylines) and user Data to a Shapefile.  
  - Initiates an sDNA tool that processes that shapefile, and e.g. carries out a network preparation or an analysis.
  - Reads the shapefile produced by the sDNA tool.
  - Displays the results from sDNA by colouring a new layer of new polylines or the original ones

## User manual.  

### Installation.
1. Install [sDNA](https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/installation_usage.html) if you have not already done so.
2. Download GHsDNA.zip from [food4Rhino](https://www.food4rhino.com) or the [GHsDNA releases page on Github](https://www.example.com).
3. Open Rhino and Grasshopper.
4. In Grasshopper click File -> Special folders -> User Objects Folder.  In Rhino 7 this is probably %appdata%\Grasshopper\Libraries  .  

### System Requirements. 
#### Software
1. Windows 10 or 8.1 (not tested in Windows 11) 
2. A Python installation that can launch sDNA correctly (e.g. Python 2.7)
3. sDNA (sDNA itself may require the 64 bit VS2008 redistributable, available [here] (https://docs.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-studio-2008-vc-90-sp1-no-longer-supported) or [here](https://download.microsoft.com/download/5/D/8/5D8C65CB-C849-4025-8E95-C3966CAFD8AE/vcredist_x64.exe ) ).
4. Rhino and Grasshopper (tested in Rhino 7)
#### Hardware
1. 64-bit Intel or AMD processor (Not ARM) 
2. No more than 63 CPU Cores. 
3. 8 GB memory (RAM) or more is recommended. 
4. 1.2 GB disk space. 


### Usage.  

### License.
See [license.md](license.md)

### Copyright.

Cardiff University 2022

## Contact.  
grasshopper.sdna@gmail.com

## Developer manual.  

### Dependencies.
#### Metahopper 
Metahopper provides programmatic automated building of the GH components suite, but this is only a convenience - the components can always be built manually too.

### Build instructions.
#### Build Prototype GHPython launcher / namer component
1. Install the Metahopper add on to your Rhino 7 / Grasshopper (GH) application.  
2. Open the builder GH definition [GHsDNA_builder.gh](devtools/GHsDNA_builder.gh)
3. Create a new GHPython component if needed.
4. Ensure there are enough input variables and output variables on the GHPython component. It must contain the superset of all inputs and all outputs for all the tools, including: file path in, Geom in, Data in, bool in, opts in, file path out, Geom Out, Data Out and bool out.
5. Ensure all input variables on the GHPython component are set to *List Access* (hover the cursor over them and right click). <!-- Set data input and output variables to tree access? -->
6. Change the GHPython component to *GH_Component SDK Mode*
7.  Make the GHPython component contain the code from [GHsDNA_launcher.py](GHsDNA_launcher.py) (largely the same as the 
code that will be in the GHsDNA GHPython components in the example Grasshopper definition [GHsDNA.gh](GHsDNA.gh) ) by 
**EITHER**:
    -a) Turning on *Show "code" input parameter* and ensuring *Input is path* is off.
    -b) Connecting the code input parameter to the output of the Read File Parameter
    -c) Using the File Path Parameter to select [GHsDNA_launcher.py](GHsDNA_launcher.py) in your local repo (ensure the Read File component is set to *Total File*)
    -d) Right clicking the code input parameter and selecting *Internalise Data* (in doing so, automatically breaking the connection from this to the Read File component)
**OR**:
    - a) Copy and pasting via the clipboard, e.g. Ctrl+C + Ctrl+V.
    - b) Ensuring the connection  (if any) from the code input parameter to the Read File component is broken
8. Toggle off *Show "code" input parameter* on tnhe GHPython component.
9.  This GHPython component will be used as the template/ prototype Launcher component.  In its source code, check the list of GHsDNA-only support tools is complete, containing each support tool to be built into a component from the main package's eponymous module [GHsDNA/GHsDNA.py].
10. Check the hardcoded dictionary of pseudonyms (i.e. shorter names), for the sDNA tools and the support tools.  These pseudonyms will actually be displayed to Grasshopper users if they switch a component from *Always Draw Icon* to *Always Draw Name*.    
11. Change the template / prototype launcher component to *Always Draw Name* to the renaming process below. below can quickly be checked (i.e. without hovering the mouse cursor over every component's icon).

#### Build and name all GHsDNA GHPython launcher components
12. Ensure there are enough new copies of the template / prototype GHsDNA-Launcher GHPython component.  One for each of the tools in the GHsDNA collection, both sDNA tools and support tools (i.e. at least 16 of them currently).  They must all contain the launcher code from [GHsDNA_launcher.py](GHsDNA_launcher.py) and all be in *GH_Component SDK Mode*.  If this has not been done already:
   -a) Create identical copies of the GHsDNA Launcher component, e.g. by copy and pasting (e.g. selecting the component and pressing Ctrl+C, Ctrl+V).  At least 15 more (at least 16  in total) are required.  Each of the GHsDNA support tools (e.g. writeSHPpolylinez, checkPrepErrorFree, readSHPpolylinez and addResults), plus each sDNA class in sDNAUISpec.py for the sDNA version being wrapped (e.g. sDNAIntegral, sDNASkim, sDNAIntegralFromOD, sDNAGeodesics, sDNAHulls, sDNANetRadii, sDNAAccessibilityMap,sDNAPrepare, sDNALineMeasures, sDNALearn, sDNAPredict) along with the sDNA_General 'swiss army knife' needs its own GHsDNA launcher component for the user to be able to use them as individual components for each tool.  
13. In the file path parameter component, check the path to the sDNAUISpec.py file is correct for the sDNA version being wrapped.
14. Make sure the list of names being output from the original Template GHPython component is correct in the text panel, and if so that it is connected to the Metahopper *Rename Object* component.
15. Select all the copies of the GHPython components, for both the sDNA tools and support tools.
16. Click Select on the Metahopper *Rename Object* component.  The GHPython components should now be renamed.
17. Select each component manually (compile it if so wished and place a compiled version on the canvas, then select that one instead)
18. Click File-> Create User object.  Allocate it to the GhsDNA category and any subcategories you want.
#### Bundling
19. Save each resulting .GHPY file in the highest parent level of the GHsDNA folder containing the files to be zipped (in the same GHsDNA folder, as the other GHsDNA folder containing a copy of the GHsDNA Python package for this build).
20. Zip the folder to GHsDNA.zip.
#### Installation
21. To install, copy GHsDNA.zip to the user's Grasshopper special Components folder (e.g. %appdata%\Grasshopper\Libraries) and unzip there.
  

### Misc
To compile C# code to a grasshopper assembly (.gha file):
Install Visual Studio 2017 community edition with VB / C# / .Net workflow https://developer.rhino3d.com/guides/grasshopper/installing-tools-windows/#fnref:3
Install Rhino & templates [ as above] https://developercommunity.visualstudio.com/t/net-framework-48-sdk-and-targeting-pack-in-visual/580235
Install .Net v4.8 https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48
Change .csproj target to v4.8 https://stackoverflow.com/questions/58000123/visual-studio-cant-target-net-framework-4-8

GHPython for .ghuser:
Select GHPython component.   Optionally compile to .ghpy.  File -> Create User Object




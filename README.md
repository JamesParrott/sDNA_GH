# sDNA_GH

sDNA is a world leading tool for Spatial Design Network Analysis.  sDNA_GH is a plug-in for Grasshopper providing components that run the tools from a local [sDNA](https://sdna.cardiff.ac.uk/sdna/) installation, on Rhino and Grasshopper geometry and data.  

## sDNA
sDNA is able to calculate Betweenness, Closeness, Angular distance, and many other quantities including custom hybrid metrics, and is able to perform many other advanced functions as well.  Please note, for results of a network analysis to be meaningful, it must be ensured that the network is first properly [prepared](https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/network_preparation.html).

## sDNA_GH functionality
sDNA_GH: 
  - Reads a network's polyline Geometry and user specified Data from Rhino. <!-- TODO or reads a network from Geometry and Data created in Grasshopper, the Data Tree being in our required format -->
  - Writes the network links (formed by one or more polylines) and user Data to a Shapefile.  
  - Initiates an sDNA tool that processes that shapefile, and e.g. carries out a network preparation or an analysis.
  - Reads the shapefile produced by the sDNA tool.
  - Displays the results from sDNA by colouring a new layer of new polylines or the original ones

## User manual.  

### Installation.
1. Install [sDNA](https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/installation_usage.html) if you have not already done so.
2. Download sDNA_GH.zip from [food4Rhino](https://www.food4rhino.com) or the [sDNA_GH releases page on Github](https://www.example.com).
3. Open Rhino and Grasshopper.
4. In Grasshopper click File -> Special folders -> User Objects Folder.  The default in Rhino 7 is %appdata%\Grasshopper\UserObjects .
5. Copy in sDNA_GH.zip to this folder (its path should be %appdata%\Grasshopper\UserObjects\sDNA_GH.zip).
6. Unzip sDNA_GH.zip here (e.g. in Windows 10 right click sDNA_GH.zip and select Extract All ..., then click Extract to use the suggested location)
7. Unblock all the files.  For easy bulk unblocking, a Powershell script is provided in the zip file: \sDNA_GH\dev_tools\batch_files\unblock_all_files_powershell.bat (run as admin in Powershell). 
8. Restart Rhino and Grasshopper.
9. The sDNA_GH plug in components should now be available under a new "sDNA_GH" tab in the ribbon tabs amongst any other plug-ins installed (right of "Mesh", "Intersect", "Transform" and "Display" etc.)


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
#### Tools.
##### Support tools
###### Read_From_Rhino (get_Geom)
Read in references to Rhino geometry (polylines) to provide them in the required form for subsequent sDNA_GH tools.  Can be merged and override with other supplied geometry and data.
###### Write_Shp (write_shapefile)
Writes the provided data and geometry (polylines) to a shapefile.  If not specified, a file name based on the Rhino doc or Grasshopper doc name is used.  Can overwrite existing files, or create new unique files.  If no Data is supplied it will first call read_Usertext (unless auto_read_Usertext = False).
###### Read_Shp (read_shapefile)
Read in the polylines and data from the specified shapefile.  Output the shapes as new Grasshopper Geometry (uness a list of existing corresponding geometry is provided).  The bounding box is provided to calculate a legend frame with.  The abbreviations and field names from an sDNA results field are also read in, and supplied so that a dropdown ist may be created, for easy selection of the data field for subsequent parsing and plotting.  If no separate Parse_Data Component is detected connected to its outputs downstream (unless auto_parse_data = False), Parse_Data is called afterwards.  
###### Parse_Data (parse_data)
Parse the data in a data tree or GDM (Geometry and Data Mapping), from a specified field, for subsequent colouring and plotting.  Use this component separately from Recolour_Objects to calculate colours with a visible Grasshoper Colour Gradient component  wARNING!  Data outputted may be false - rescaled and renormalised, especially if objects are coloured according only to the bin / class they are in.  Max and Min bounds can be overridden, else they are calculated on the whole data range.  If no separate Recolour_objects Component is detected connected to its outputs downstream (unless auto_plot_data = False), Parse_Data is called afterwards.   
###### Recolour_objects
Recolour objects (and legend tags) based on pre parsed and renormalised data, or already calculated colours (RGB).  Custom colour calculation is possible, as is the Grasshopper Colour Gradient internally via Node In Code.  Create a legend by connecting the outputs to a Grasshopper Legend component and the outputs provided.  Custom legend tag templates and class boundaries are supported.  Recolouring unbaked Grasshopper geometry instead of Rhino Geometry requires the outputs to be connected to a Custom Preview component.
If unparsed data is input, Parse_Data is first called.
##### Usertext tools    

###### Read_Usertext
Reads Usertext from Rhino and Grasshopper Geometry whose keys fit a customisable pattern.  If no Geometry is provided, Read_From_Rhino is first called (unless auto_get_Geom = False)
###### Write_Usertext
Write_Usertext to Rhino and Grasshopper geometric objects using a customisable pattern for the keys.
###### bake_Usertext
Transfers Usertext stored on Grasshopper objects to Usertext on the Baked Rhino objects (same keys).  A normal `custom' bake is carried out, but reading the Usertext too into a dictionary.  Then Write_Usertext is called on the resulting Rhino objects with the Usertext data.

##### Analysis tools
###### sDNAIntegral
sDNA Integral wrapper.  This, and all sDNA wrapper components below, will automatically call other support commponents (unless     auto_write_new_Shp_file = False, ,  and )
If no input shape file is specified, Write_Shp is first called (this itself may call Read_Usertext, which in turn may first call Read_From_Rhino).  The component attempts to check if any Read_Usertext components are already connected to its outputs (downstream).  Otherwise after running sDNA (unless auto_read_Shp = False) it will afterwards call Read_Usertext.  Similarly this also may trigger Parse_Data or Recolour_objects afterwards.   Therefore any sDNA component on its own can handle an entire process, from reading in Rhino Geometry, reading Usertext (e.g. for user weights), writing a shapefile, right through to reading in the sDNA output shapefiles, parsing it and recolouring it back in Rhino (writing data back to user text and baking still need to be done additionally).
###### sDNASkim
sDNA Skim wrapper
###### sDNAIntFromOD
sDNA Integral from Origin Destination matrix wrapper
###### sDNAAccessMap
sDNA Accessibility Map wrapper
##### Preparation tools
###### sDNAPrepare
sDNA Prepare wrapper
###### sDNALineMeasures
sDNA line measures wrapper
##### Geometric analysis tools
###### sDNAGeodesics
sDNA Geodesics tool wrapper
###### sDNAHulls
sDNA Convex Hulls tool wrapper
###### sDNANetRadii
sDNA Network Radii wrapper
##### Calibration tools
###### sDNALearn
sDNA Learn wrapper
###### sDNAPredict
sDNA Predict wrapper
##### Dev tools
###### sDNA_general
Run any other component by feeding the name of it into the "tool" input param. A "Swiss army knife" component.
###### Python
Output the names of all the sDNA tool classes for the sDNA installation provided in opts, as well as all the sDNA_GH support tool names.  
###### Self_test
###### Build_components 
Easily build all the other components for the sDNA installation provided.  User Objects still need to be built manually, but components are all the same launcher code in a Gh_Python component, but with different names.  Functionality is provided by tools.py in the sDNA_GH Python package, so new components are only needed to be built for tools sDNA_GH doesn't know about yet.

### Example Grasshopper definitions

### License.
See [license.md](license.md)

### Copyright.

Cardiff University 2022

## Contact.  
grasshopper.sdna@gmail.com

## Developer manual.  

### Dependencies.
####
Powershell is required to be installed, to avoid unblocking every file manually: https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell.  Otherwise no additional dependencies are required to be installed.  sDNA_GH is shipped with files from the following python packages included:
PyShp (MIT License)  "version: 2.2.0" https://github.com/GeospatialPython/pyshp/blob/master/shapefile.py
Toml (MIT License) https://github.com/uiri/toml/blob/master/toml/decoder.py  Latest commit 230f0c9 on 30 Oct 2020 


### Build instructions.
1. Open \dev_tools\sDNA_build_components.gh in Grasshopper. 
2. Right click the Path Component and ensure it points to \sDNA_GH\sDNA_GH\sDNA_GH_launcher.py
3. Ensure the File Reader Component (that the Path Component is connected to) is also connected to the launcher_code input param on
the Build_components GhPython component.
4. In the main Grasshopper Display pull down menu, ensure Draw Icons is turned off.
5. Change the Boolean toggle to True connected to the go input param of Build_components.
6. A slight delay may occur as sDNA_GH/tools.py is imported, and the 20 or so components are created.
7. Turn the Boolean toggle to False (connected to the go input param of Build_components).  This both ensures no further components are created (unnecessary duplicates), and causes an update that makes each component ask Grasshopper what its name is, connect to tools.py, and update its own Input and Output params.
8. Click through all the warnings (as we cleared all Params from each component).  There are about 20 pop ups!
9. The red error on read shp and write shp can be cleared by adding and removing a parm (or building them from components that already have an 'OK' param and a 'go' input param (set to list acess) )
10. Select each component one at a time, and go to the main Grasshopper File pull down menu, and select Create User Object ...
11. Ensure the main category is sDNA_GH or sDNA.  Look up the sub category in the tools.py meta option categories.  Description text
can be used from the tool's description in this readme file itself (above).
12. From %appdata%\Grasshopper\UserObjects or the Grasshopper User objects folder, copy (or move) all the .ghuser files just created into \sDNA_GH in the main repo, next to config.toml
13. Run create_release_sDNA_GH_zip.bat to create the zip file for release.
14. Note:  The components are only GhPython launchers with different names, so the above steps 1 - 12 (in particular, the laborious step 10.) only need to be repeated if the code in \sDNA_GH\sDNA_GH\sDNA_GH_launcher.py has been changed, or if new components e.g. for new tools need to be built.  As much code as possible has been shifted into tools.py and the other sDNA_GH Python package files.  If no changes to the launcher code have been made and no new components/tools are requires, a new release can reuse the .ghuser files from an old release, and the new release's zip files can be created simply by running create_release_sDNA_GH_zip.bat
  

### Misc
To compile C# code to a grasshopper assembly (.gha file):
Install Visual Studio 2017 community edition with VB / C# / .Net workflow https://developer.rhino3d.com/guides/grasshopper/installing-tools-windows/#fnref:3
Install Rhino & templates [ as above] https://developercommunity.visualstudio.com/t/net-framework-48-sdk-and-targeting-pack-in-visual/580235
Install .Net v4.8 https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48
Change .csproj target to v4.8 https://stackoverflow.com/questions/58000123/visual-studio-cant-target-net-framework-4-8

GHPython for .ghuser:
Select GHPython component.   Optionally compile to .ghpy.  File -> Create User Object




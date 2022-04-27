# sDNA_GH
sDNA is a world leading tool for Spatial Design Network Analysis.  sDNA_GH is a plug-in for Grasshopper providing components that run the tools from a local [sDNA](https://sdna.cardiff.ac.uk/sdna/) installation, on Rhino and Grasshopper geometry and data.  

## sDNA
sDNA is able to calculate Betweenness, Closeness, Angular distance, and many other quantities including custom hybrid metrics, and is able to perform many other advanced functions as well.  Please note, for results of a network analysis to be meaningful, it must be ensured that the network is first properly [prepared](https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/network_preparation.html).

## sDNA_GH functionality
sDNA_GH: 
  - Reads a network's polyline Geometry from Rhino or Grashopper, and Data from any Usertext on it. 
  - Writes the network polylines (formed by one or more polylines) and user Data to a Shapefile.  
  - Initiates an sDNA tool that processes that shapefile, and e.g. carries out a network preparation or an analysis.
  - Reads the shapefile produced by the sDNA tool.
  - Displays the results from sDNA by colouring a new layer of new polylines or the original ones

## User manual.  
### Installation.
1. Ensure you have an installation of [Rhino 3D](https://www.rhino3d.com/download/) including Grasshopper (versions 6 and 7 are supported).
2. Ensure you have an installation of [Python 2.7](http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi) [^0]  Iron Python is only supported by sDNA_GH within Grasshopper. 
3. Ensure you have an installation of [sDNA](https://sdna.cardiff.ac.uk/sdna/wp-content/downloads/documentation/manual/sDNA_manual_v4_1_0/installation_usage.html).
4. Download `sDNA_GH.zip` from [food4Rhino](https://www.food4rhino.com) or the [sDNA_GH releases page on Github](https://www.example.com).
5. Ensure `sDNA_GH.zip` is unblocked: Open File Explorer and go to your Downloads folder (or whichever folder you saved it in).  Right click it and select _Properties_ from the bottom of the menu.  Then click on the _Unblock_ check box at the bottom (right of _Security_), then click _OK_ or _Apply_.  The check box and _Security_ section should disappear.  This should unblock all the files the zip archive.  If any files still need to be unblocked,  a [Powershell](https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell) script is provided in the zip file: `\sDNA_GH\dev_tools\batch_files\unblock_all_files_powershell.bat`[^2]  This script is largely code from Ed Wilson of Microsoft's [Dev Blog](https://devblogs.microsoft.com/scripting/easily-unblock-all-files-in-a-directory-using-powershell/) or try this [alternative method](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/unblock-file?view=powershell-7.2))  Please note, you should not automatically trust and unblock all software downloaded from anywhere on the internet [^1].  
6. Open Rhino and Grasshopper.
7. In Grasshopper's pull down menus (above the tabs ribbon at the top) click _File_ -> _Special folders_ -> _User Objects Folder_.  The default in Rhino 7 is `%appdata%\Grasshopper\UserObjects`.  Note, this is not the Components Folder used by many other plug-ins (i.e. not `%appdata%\Grasshopper\Libraries`).
8. Copy in sDNA_GH.zip to this folder (e.g. it should be at `%appdata%\Grasshopper\UserObjects\sDNA_GH.zip`).
9. Unzip `sDNA_GH.zip` to this location (e.g. in Windows 10 right click `sDNA_GH.zip` and select _Extract All ..._, then click _Extract_ to use the suggested location).
10. Ensure sDNA_GH can find sDNA and Python 2.7.  Open the folder `sDNA_GH` (just created by the unzip in the previous step), and inside it, using any text-file editor (e.g. Notepad), open the sDNA_GH user installation options configuration file, `config.toml`.  In the `[metas]` section, look for the option: 
```
sDNA_search_paths = ['C:\Program Files (x86)\sDNA',
                     'C:\Program Files\sDNA',
                     '%appdata%\sDNA',
                     ]
```
Select and _Copy_ the first file path (e.g. `C:\Program Files (x86)\sDNA`).  This is the default sDNA installation directory (if this option is not within `config.toml`, copy and paste it from here into there).  
Open a new _File Explorer_ window. _Paste_ the default sDNA installation directory into the browser bar, and press Enter.  Scroll down and check the folder contains two files, called `sDNAUISpec.py`  (i.e. `C:\Program Files (x86)\sDNA\sDNAUISpec.py`) and `runsdnacommand.py`.

Similarly, scroll down to the `[options]` section of `config.toml`, and find the `python_exe = 'C:\Python27\python.exe'` option (or paste it in there).  Select and copy the file path `C:\Python27\python.exe` and paste this into the browser bar of Windows File Explorer.   Press Enter, and Python 2.7 should start (you may close this - press _Ctrl + Z_ and hit _Enter_)[^3].  

OPTIONAL: If you want to run sDNA from a different version of Python, or if you have installed Python 2.7 somewhere other than its default folder, or if you are using sDNA Open from elsewhere than its default directory, you must alter the values of the above options in `config.toml` to equal the correct sDNA installation folder and Python executable's location respectively, in order for sDNA_GH to find the programs you want.[^4] 

These options may also be specified in a project specific config.toml file, or in an input Parameter to an sDNA_GH component.  But then they need to be entered in each Grasshopper definition (.gh file) using sDNA_GH.  Setting the installation wide options is a one off procedure (unless the Python or sDNA folders are subsequently moved!).  

11. Restart Rhino and Grasshopper.
12. The sDNA_GH plug in components should now be available under a new "sDNA_GH" tab in the ribbon tabs amongst any other plug-ins installed (right of _Mesh_, _Intersect_, _Transform_ and _Display_ etc.)
13. For a first test of sDNA_GH, open  `\sDNA_GH\sDNA_GH\tests\5x18_random_grid_network.3dm' (in the folder from the unzip, in the User Objects folder), place an sDNA_Integral component and connect a True boolean toggle to its _go_.  

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
Read in references to Rhino geometry (polylines) to provide them in the required form for subsequent sDNA_GH tools.  Can be merged and override with other supplied geometry and data.  The UUIDs of the Rhino objects are converted to strings to preserve the reference to them.
###### Write_Shp (write_shapefile)
Writes the provided data and geometry (polylines) to a shapefile.  If not specified, a file name based on the Rhino doc or Grasshopper doc name is used (unless `auto_update_Rhino_doc_path = False`).  Can overwrite existing files, or create new unique files.  If no Data is supplied it will first call read_Usertext (unless auto_read_Usertext = False).
###### Read_Shp (read_shapefile)
Read in the polylines and data from the specified shapefile.  Output the shapes as new Grasshopper Geometry (uness a list of existing corresponding geometry is provided).  The bounding box is provided to create a legend frame with in Recolour_Objects.  The abbreviations and field names from an sDNA results field are also read in, and supplied so that a dropdown list may be created, for easy selection of the data field for subsequent parsing and plotting.  If no separate Parse_Data Component is detected connected to the component's outputs downstream (unless auto_parse_data = False), Parse_Data is called afterwards.  
###### Parse_Data (parse_data)
Parse the data in a data tree or GDM (Geometry and Data Mapping), from a specified field, for subsequent colouring and plotting.  Use this component separately from Recolour_Objects to calculate colours with a visible Grasshoper Colour Gradient component.  
Max and Min bounds can be overridden, else they are calculated on the whole data range.  If no separate Recolour_Objects Component is detected connected to its outputs downstream (unless auto_plot_data = False), Recolour_Objects is called afterwards.     WARNING!  The inputted Data is not changed, but the Data outputted may be changed, and in fact probably is false.  After parsing the data, the legend tags are the definitive reference for what each colour means, not the outputted data values.  The user can rescale, renormalise, and both exponentially and logarithmically re map the data to the (`plot_min`, `plot_max`) domain however they wish, e.g. in order to produce the desired result in Recolour_Objects.  If objects are coloured according only to the midpoint of the bin / class they are in, the parsed data will take far fewer distinct values than the number of polylines in a large network.  
###### Recolour_Objects
Recolour objects (and legend tags) based on pre-parsed and pre-normalised data, or already calculated colours (RGB).  Custom colour calculation is possible, as is the Grasshopper Colour Gradient internally via Node In Code.  Create a legend by connecting leg_cols, leg_tags and leg_frame to a Grasshopper Legend component.  Custom legend tag templates and class boundaries are supported via three format strings.  Recolouring unbaked Grasshopper geometry instead of Rhino Geometry requires Data and Geometry outputs to be connected to a Grasshopper Custom Preview component.  If unparsed data is input, Parse_Data is first called.
##### Usertext tools    

###### Read_Usertext
Reads Usertext from Rhino and Grasshopper Geometry whose keys fit a customisable pattern.  If no Geometry is provided, Read_From_Rhino is first called (unless `auto_get_Geom` = False)
###### Write_Usertext
Write_Usertext to Rhino and Grasshopper geometric objects using a customisable pattern for the keys.
###### Bake_Usertext
Transfers Usertext stored on Grasshopper objects to Usertext on the Baked Rhino objects (under the same keys).  A normal `custom' bake is carried out, but reading the Usertext too into a dictionary.  Afterwards, Write_Usertext is called on the resulting Rhino objects with the Usertext data.

##### Analysis tools
###### sDNA_Integral
sDNA Integral wrapper.  This, and all sDNA wrapper components below, will automatically call other support commponents (unless     `auto_write_new_Shp_file` = False, ,  and )
If no input shape file is specified, Write_Shp is first called (this itself may call Read_Usertext, which in turn may first call Read_From_Rhino).  The component attempts to check if any Read_Usertext components are already connected to its outputs (downstream).  Otherwise after running sDNA (unless `auto_read_Shp` = False) Read_Usertext will be added to the end of the tools list, to be run afterwards.  Similarly this also may trigger Parse_Data or Recolour_Objects to be added to the list and run afterwards.   Therefore any sDNA component on its own can handle an entire typical process, from reading in Rhino Geometry, reading Usertext (e.g. for user weights), writing a shapefile, right through to reading in the sDNA output shapefiles, parsing it and recolouring it back in Rhino. Writing data back to user text and baking still need to be done additionally.
###### sDNA_Skim
sDNA Skim wrapper
###### sDNA_Int_From_OD
sDNA Integral from Origin Destination matrix wrapper
###### sDNA_Access_Map
sDNA Accessibility Map wrapper
##### Preparation tools
###### sDNA_Prepare
sDNA Prepare wrapper
###### sDNA_Line_Measures
sDNA line measures wrapper
##### Geometric analysis tools
###### sDNA_Geodesics
sDNA Geodesics tool wrapper
###### sDNA_Hulls
sDNA Convex Hulls tool wrapper
###### sDNA_Net_Radii
sDNA Network Radii wrapper
##### Calibration tools
###### sDNA_Learn
sDNA Learn wrapper
###### sDNA_Predict
sDNA Predict wrapper
##### Dev tools
###### sDNA_general
Run any other component by feeding the name of it into the "tool" input param. A "Swiss army knife" component.
###### Unload_sDNA_GH
Unload the sDNA_GH Python package, by removing all its keys from sys.modules.  sDNA_GH components will then reload the package and installation-wide options file (config.toml) without having to restart Rhino.
###### Python
Output the names of all the sDNA tool classes for the sDNA installation provided in opts, as well as all the sDNA_GH support tool names.  
###### Self_test
Not a tool in the same sense as the others (this has no tool function in sDNA).  The name `Self_test` (and variations to case and spacing) are recognised by the launcher code, not the main package tools factory.  In a component named "Self_test", the launcher will
cache it, then replace the normal RunScript method in a Grasshopper component class entirely, with a function (`unit_tests_sDNA_GH.run_launcher_tests`) that runs all the package's unit tests (using the Python unittest module).  Unit tests to the functions in the launcher, can also be added to the launcher code.
###### Build_components 
Easily build all the other components for the sDNA installation provided.  User Objects still need to be built manually, but components are all the same launcher code in a Gh_Python component, but with different names.  Functionality is provided by setup.py in the sDNA_GH Python package, so new components are only needed to be built for tools sDNA_GH doesn't know about yet.


#### Options.  
sDNA_GH is customisable.  This is controlled by setting options.  Any option in a component can be read by adding an Output Param and renaming it to the name of the option.  Similarly, any option in a component can be changed by adding an Input Param and renaming it to the name of the option, and connecting it to the new value.  Entire options data structures (`opts`) may be passed in from other components as well, via Grasshopper connections.  
##### Meta options.
###### Primary meta (options file)
Some options are particularly important as they may change other options, change how they are read, or add new parts to the whole options data structure (`opts`).  These are called _meta options_. All options can be set on the Input Params of a GH_sDNA component (zoom in, add a new Input Param, and rename it to the desired option name.  This is case sensitive).  The most important of all the  _meta options_, is the `config` (the "primary meta").  This may be 
set to a file path of a project specific options file.  To create one, copy and paste `config.toml` and edit its values (to the right of the equals signs) in a text editor (the keys (to the left of the equals signs) must be left unchanged else their values will be ignored, or cause a name clash).  The file can be renamed, but should still end in `.toml`.  It may contain other meta options, tool options and local metas, but not another primary meta.  Tool options in the file may refer to any named tool or nick named component, not necessarily the tools of the component that reads the file.  This is intended to enable cleaner Grasshopper definitions, with fewer required connections, by storing the values of options that do not need to be changed away in a separate file.  Options that are used only when a component is first placed, e.g. to set a logging file or logging levels, before any input params may have even been set up, must be configured in the installation wide `config.toml`.
##### Module wide options.
It is tempting to conclude that Input parameter options are the most important, followed by the project specific options file (primary meta), and in turn by an external component's options.  This is largely true, but not necessarily the case on startup.  For efficiency, the sDNA_GH design forces all of its components in the same Grasshopper instance to share the same Python package, which is only imported once by the first component to run (subsequent ones refer to it directly in sys.modules).  This import occurs, before the main method of the Grasshopper Python component class runs.  This method (RunScript) is responsible for reading in the component's input Params.  Therefore any setup code that runs before this method cannot possibly know about the values of the Input Params, the primary meta, nor any other component's options.  At this early stage, the component can only refer to the installation wide options (plus a few necessary hard coded settings in the launcher).  

##### Logging options
Not only is the sDNA_GH component class definition defined in the shared package, the root logger is set up there too when the module is first imported, for all components to subsequently refer to.  So in particular, the advance loading of the default options and installation wide options, mean logging options (e.g. custom logging levels for verbose or quiet output, and the name of the actual log file) have to be set up there, i.e. in the installation wide options file (e.g. `%appdata%\Grasshopper\UserObjects\sDNA_GH\config.toml`).  The same goes for any other options that control code that runs on component setup and module import, before Grasshopper calls RunScript and reads in the component's inputs.  Ordinarily, the higher priority options would override the lower priority ones.  But for code that must run before this override process happens at all, (especially on setup) it is simply too late for some options defined there to have any affect. 

<!-- TODO.  Put such options into their own section of "setup options" -->

 
###### Options override priority order
The component input param options override options in the primary meta.  The primary meta overrides options from another Grasshopper component.  Other component's options override the installation wide options file (e.g. `%appdata%\Grasshopper\UserObjects\sDNA_GH\config.toml`).  Finally this file overrides the hard coded default options in setup.py
###### Name map (abbreviations, nick names and work flows)
After `config`, the next most important meta option is `name_map`, in which custom nick names for user-created sDNA_components (and entire work sequences of tools) may be defined. 
##### Component NickName.
The particular tool or tools a module runs is controlled by its NickName (accessible in the local meta option NickName), but which can be changed by simply renaming the component.  The component then looks up in the meta option name_map to see which (if any)
tool or tools (including other NickNames) its NickName corresponds to, then retrieves these tools from the cache (building them if they do not exist already).  sDNA tools automatically add their own default options and syntax in their initialiser (and add new ones if their nick name or the version of sDNA subsequently changes).  
##### Tool options.
Each nick name in name map creates a new set of options.  These contain options for each tool (real name) in the list of tools used under that nick name.  Each of these has a set of options for each version of sDNA encountered by the component so far.  Primarily this is where the settings for sDNA wrapper tools are stored (apart from a couple of helper overrides, like `file`).  Support tools and sDNA_GH tools use options and meta options in the common name root space (which is the same for all sDNA versions sDNA_GH has found).  
##### Local meta options.
By default all sDNA_GH components share (and may change) the same global dictionary of options (module options, tool options, and meta options, together in opts) in the setup.py module.  If only one of each tool is needed (and there is only one version of sDNA) that will suffice for most users.  Each component with a given nickname in name_map also has its own set of tool options (one for each version of sDNA).  However for one support component to have a different set of options to another, one of them must no longer update the global options dictionary - it must desynchronise from them.  This syncing and desyncing is controlled by each component's individual local meta-options, (in local_metas) sync_to_module_opts, read_from_shared_global_opts.  By default these booleans are both equal to True.  More than one "primary meta" is then possible - just create a new project specific options file (`config.toml`) for each, and specify it's name on the `config` input of the desired components.  just like other optionsm local metas can be set in Input Params, shared between components via Grasshopper connections in the same way as opts, can be set by project config files(`config.toml`) and set in the installation wide config file (e.g. `%appdata%\Grasshopper\UserObjects\sDNA_GH\config.toml`).  But uniquely, they are not updated automatically by syncing to the main module options (as this would defeat their entire purpose, of stopping other options from doing this).

  

### Example Grasshopper definitions.
#### Running sDNA Integral on a random grid read from Rhino.
##### Selecting and specifying an sDNA Results field.
##### Reading shapefile data with existing geometry.
##### Using a Grasshopper Colour gradient component.
##### Adding a legend with a Legend component.
##### Customising legend class boundaries and tag names.

#### Running sDNA Integral on a random grid of Grasshopper geometry (colouring with the Custom Preview component).
#### Running sDNA Integral on a network of polylines, approximating a network of arcs from intersecting circles. 
##### Recolouring the arcs instead of polylines.
#### Writing polylines and data to shapefiles.
#### Reading in polylines and data from shapefiles.
#### Writing Usertext.
#### Reading Usertext for sDNA (e.g. User weights).
#### Baking (saving Grasshopper objects to a Rhino document) with Usertext.


### License.
See [license.md](license.md)

### Copyright.
Cardiff University 2022

## Contact.  
grasshopper.sdna@gmail.com

## Developer manual.  

### Dependencies.
####
 To bulk unblock files, to avoid unblocking every file manually it is necessary to install (Powershell)[https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell].  Otherwise no additional dependencies are required.  sDNA_GH is shipped with files from the following python packages included:
PyShp (MIT License)  "version: 2.2.0" https://github.com/GeospatialPython/pyshp/blob/master/shapefile.py
Toml (MIT License) https://github.com/uiri/toml/blob/master/toml/decoder.py  Latest commit 230f0c9 on 30 Oct 2020 


### Build instructions.
1. Open \dev_tools\sDNA_build_components.gh in Grasshopper. 
2. Right click the Path Component and ensure it points to \sDNA_GH\sDNA_GH\sDNA_GH_launcher.py
3. Ensure the File Reader Component (that the Path Component is connected to) is set to read the whole file, and also is connected to the _launcher code_ input param on the Build_components GhPython component.  Set the plug-in name on _plug in name_.
4. In the main Grasshopper Display pull down menu, ensure Draw Icons is turned off (this displays comoponent names instead).
5. Change the Boolean toggle to True, and connect it to the _go_ input param of Build_components.
6. A slight delay may occur as sDNA_GH/setup.py is imported, and the 23 or so components are created.
7. Turn the Boolean toggle to False (connected to the go input param of Build_components).  This ensures no further components are created (unnecessary duplicates).  The components are disabled, otherwise the next update will makes each one ask Grasshopper what its name is, connect to sDNA_GH.setup.py, and update its own Input and Output params.
8. Click the pull down menu *Solution* and select *Disable Solver*.  
9. Right click each new component (on its name not its Params) and select Enable. 
<!-- Click through all the warnings (as we cleared all Params from each component).  
9. The red error on read shp and write shp can be toggling _Show output "out"_ parameter (or building them from components that already have an 'OK' param and a 'go' input param (set to list acess) ) -->
10. Select each component one at a time, and go to the main Grasshopper File pull down menu, and select _Create User Object ..._
11. Ensure the main category is sDNA_GH or sDNA.  Look up the sub category in the setup.py meta option categories.  Description text
can be used from the tool's description in this readme file itself (above).
12. From %appdata%\Grasshopper\UserObjects or the Grasshopper User objects folder, copy (or move) all the .ghuser files just created into \sDNA_GH in the main repo, next to config.toml
13. Run create_release_sDNA_GH_zip.bat to create the zip file for release.
14. Note:  The components are only GhPython launchers with different names, so steps 1 - 12 above (in particular, the most laborious step, number 10.) only need to be repeated if the code in \sDNA_GH\sDNA_GH\sDNA_GH_launcher.py has been changed, or if new components need to be built e.g. for new tools .  As much code as possible has been shifted into the python package and the other sDNA_GH Python package files.  If no changes to the launcher code have been made and no new components/tools are required, a new release can simply reuse the .ghuser files from an old release, and the new release's zip files can be created simply by re running create_release_sDNA_GH_zip.bat
  

### Misc
To compile C# code to a grasshopper assembly (.gha file):
Install Visual Studio 2017 community edition with VB / C# / .Net workflow [https://developer.rhino3d.com/guides/grasshopper/installing-tools-windows/#fnref:3]
Install Rhino & templates as above [https://developercommunity.visualstudio.com/t/net-framework-48-sdk-and-targeting-pack-in-visual/580235]
Install .Net v4.8 [https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48]
Change .csproj target to v4.8 [https://stackoverflow.com/questions/58000123/visual-studio-cant-target-net-framework-4-8]

GHPython for .ghuser:
Select GHPython component.   Optionally compile to .ghpy.  File -> Create User Object

[^0] The Python 2.7 download can be verified using this [certificate](https://www.python.org/ftp/python/2.7.3/python-2.7.3.msi.asc) and [Gpg4win](https://gpg4win.org/download.html).

[^1] The entire source code for sDNA_GH is visible on [Github](http:\\www.github.com).  All the source code is also visible in the download itself as the component launcher and Python package is visible, except the .ghuser files which each contain the launcher code under a different name, and are compiled.  It is a little repetitive, but see the Build Instructions above to build them for yourself from the source code.   

[^2]  This script is largely code from Ed Wilson of Microsoft's [Dev Blog](https://devblogs.microsoft.com/scripting/easily-unblock-all-files-in-a-directory-using-powershell/) or try this [alternative method](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/unblock-file?view=powershell-7.2)) 

[^3] These checks can also be performed by copy and pasting directly from this document.  However that would only prove the correctness of README.md (this is a good thing, but sDNA_GH does not refer to this file).  For example, if in future a breaking 
change (even an entirely inadvertant one) causes this document to be incorrect (and it has not been updated), `config.toml` still needs to be checked to ensure sDNA_GH will find Python 2.7 and sDNA correctly.

[^4] In the absence of configuration options, sDNA_GH will search certain default directories (C:\, C:\Program Files (x86), %appdata%, and the system path) for sDNA and Python27, so if sDNA and Python 2.7 are installed in a 'normal' place, the sDNA_search_paths option can also be deleted from `config.toml`.  However if a new Python 2.7 version or new sDNA version is installed in future, the behaviour of sDNA_GH may suddenly change if it finds a new version instead, possibly no longer 
working at all (e.g. if it finds Iron Python 2.7).


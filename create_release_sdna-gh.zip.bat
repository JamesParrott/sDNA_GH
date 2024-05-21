@ECHO OFF

set repo_path=%~dp0
set cwd=%CD%
set zip_name=sdna-gh
set target=%cwd%\%zip_name%

mkdir %target%
@REM pip will also install the deps into the target 
@REM that've now been refactored own repos, 
@REM and are now distributed via PyPi (no more static linking):
@REM IronPyShp, toml_tools, Mapclassif-Iron, Cheetah_GH and Anteater_GH
python -m pip install --target=%target% -e .

@REM Zipping up the 'venv' (any directory pip installed into with --target)
@REM is not a recommended distribution technique for Python libraries.
@REM It is not even common (yet?) for Rhino plug-ins.  But more normal
@REM installs from the wheel are also possible via: 
@REM pip install --target=%app_data%\Grasshopper\UserObjects\ %repo_path%\dist\sdna_gh-*-py2.py3-none-any.whl
@REM and a zip file allows: 
@REM i) shipping known versions of the deps, 
@REM ii) giving Rhino users a zip file like many other plug-ins, 
@REM (they are familiar with unblocking and unzipping),
@REM iii) backwards compatibility with the sDNA_GH v1 & v2 installation process 
@REM iv) while also allowing sDNA_GH to be installable and runnable (at
@REM least in code) from Rhino 8 CPython 3 components, simply using the new auto magical syntax:  
@REM #r: sDNA_GH
cd %target%
tar -caf %cwd%\%zip_name%.zip *

@REM Clean up tmp build artefacts.
cd %cwd%
rmdir /s /q %target%

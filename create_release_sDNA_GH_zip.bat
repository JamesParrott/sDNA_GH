@ECHO OFF
REM set source_sDNA_GH_package=%~dp0..\..\sDNA_GH
REM set source_sDNA_GH_package=..\..\sDNA_GH\*
REM cd sDNA_GH
tar -caf sDNA_GH.zip sDNA_GH\* dev_tools\batch_files\unblock_all_files_powershell.bat
REM cd ..
REM tar -uf sDNA_GH.zip dev_tools\batch_files\unblock_all_files_powershell.bat
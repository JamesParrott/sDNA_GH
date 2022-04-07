@ECHO OFF
REM set source_sDNA_GH_package=%~dp0..\..\sDNA_GH
REM set source_sDNA_GH_package=..\..\sDNA_GH\*
REM cd sDNA_GH  dev_tools\files_to_ship_in_each_release.txt

rem https://stackhowto.com/batch-file-to-read-text-file-line-by-line-into-a-variable/
setlocal enabledelayedexpansion
set count=0
for /f "tokens=*" %%x in (dev_tools\files_to_ship_in_each_release.txt) do (
    set /a count+=1
    set fileset[!count!]=%%x
)
dir %fileset%
set fileset=sDNA_GH\* dev_tools\batch_files\unblock_all_files_powershell.bat README.md license.md
tar -caf sDNA_GH.zip %fileset% 
REM sDNA_GH\* dev_tools\batch_files\unblock_all_files_powershell.bat
REM cd ..
REM tar -uf sDNA_GH.zip dev_tools\batch_files\unblock_all_files_powershell.bat
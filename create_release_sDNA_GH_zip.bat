@ECHO OFF
REM set source_sDNA_GH_package=%~dp0..\..\sDNA_GH
REM set source_sDNA_GH_package=..\..\sDNA_GH\*
REM cd sDNA_GH  dev_tools\files_to_ship_in_each_release.txt

rem https://stackhowto.com/batch-file-to-read-text-file-line-by-line-into-a-variable/
rem setlocal enabledelayedexpansion
rem set count=0
rem for /f "tokens=*" %%x in (dev_tools\files_to_ship_in_each_release.txt) do (
rem     set /a count+=1
rem     set fileset[!count!]=%%x
rem )
rem dir %fileset%

rem start " " build_components.bat

copy README.md sDNA_GH
copy README.pdf sDNA_GH
copy license.md sDNA_GH
cd sDNA_GH
rem set fileset= * ..\README.md ..\license.md
tar -caf ..\sDNA_GH.zip *
del README.md
del README.pdf
del license.md


REM sDNA_GH\* dev_tools\batch_files\unblock_all_files_powershell.bat
REM cd ..
REM tar -uf sDNA_GH.zip dev_tools\batch_files\unblock_all_files_powershell.bat
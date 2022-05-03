@ECHO OFF
REM https://devblogs.microsoft.com/scripting/easily-unblock-all-files-in-a-directory-using-powershell/
set destination_GH_libraries_sDNA_GH_package=%appdata%\Grasshopper\UserObjects\sDNA_GH
gci %destination_GH_libraries_sDNA_GH_package% | Unblock-File
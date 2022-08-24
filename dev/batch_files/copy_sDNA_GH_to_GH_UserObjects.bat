@ECHO OFF
set source_sDNA_GH_package=%~dp0..\..\sDNA_GH
REM https://stackoverflow.com/questions/14936625/relative-path-in-bat-script
set destination_GH_libraries_sDNA_GH_package=%appdata%\Grasshopper\UserObjects\sDNA_GH
xcopy %source_sDNA_GH_package% %destination_GH_libraries_sDNA_GH_package% /I /S /E /Y
copy %source_sDNA_GH_package%\..\README.md %destination_GH_libraries_sDNA_GH_package%
copy %source_sDNA_GH_package%\..\license.md %destination_GH_libraries_sDNA_GH_package%

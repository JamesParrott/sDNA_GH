
set THIS_BAT_FILES_DIR=%~dp0
call "C:\Program Files\Rhino 8\System\Rhino.exe" /nosplash /runscript="-_grasshopper _editor _load _document _open %THIS_BAT_FILES_DIR%\exit_Rhino.gh _enterend"
echo %ERRORLEVEL%
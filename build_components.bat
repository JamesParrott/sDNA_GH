@ECHO OFF
cd dev
set REPO_PATH=%~dp0
start " " "C:\Program Files\Rhino 8\System\Rhino.exe" /nosplash /runscript="-_grasshopper _editor _load _document _open %REPO_PATH%\dev\sDNA_build_components.gh _enter _exit _enterend"
cd ..

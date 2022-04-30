@ECHO OFF
call copy_sDNA_GH_to_GH_Libraries.bat

"C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="_Grasshopper _enter"


REM "C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="-Grasshopper editor _enter" 
REM "C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="-Grasshopper editor load document open test_rhino_gh_bat.gh _enter save _enter exit _enter" "C:\Users\James\Documents\Rhino\Grasshopper\test_rhino_gh_bat.3dm"
REM cd "C:\Users\James\Documents\Rhino\Grasshopper\"
REM "C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="-_ReadCommandFile test_rhino_gh.txt" "C:\Users\James\Documents\Rhino\Grasshopper\test_rhino_gh_bat.3dm"

@ECHO OFF
cd dev
REM "-grasshopper editor load document open test_rhino_gh_bat.gh _enter
REM C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.01\dev\sDNA_build_components.gh
start " " "C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="-grasshopper editor load document open C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.01\dev\sDNA_build_components.gh _enter _exit _enterend"
cd ..
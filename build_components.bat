@ECHO OFF
cd dev
start " " "C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="-_grasshopper _editor _load _document _open C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.01\dev\sDNA_build_components.gh _enter _exit _enterend"
cd ..

rem https://www.grasshopper3d.com/forum/topics/parallel-computation-run-iterations-on-multiple-computers
rem http://docs.mcneel.com/rhino/7/help/en-us/information/rhinoscripting.htm

rem ECHO "After Grasshopper builds the components, please check Task Manager for Rhino processes that didn't close properly."
rem TaskMgr 
rem pause
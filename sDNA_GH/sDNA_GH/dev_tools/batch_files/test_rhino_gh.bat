@ECHO OFF
cd "C:\Users\James\Documents\Rhino\Grasshopper\"

"C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="-_ReadCommandFile test_rhino_gh_rhino_commands.txt" "C:\Users\James\Documents\Rhino\Grasshopper\test_rhino_gh_bat.3dm"
REM "C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="_PrintDisplay _State=_On Color=Display Thickness=4 _Enter -_GrasshopperPlayer test_rhino_gh_bat.gh _enter -_save _enter _exit _enterend" "C:\Users\James\Documents\Rhino\Grasshopper\test_rhino_gh_bat.3dm"
REM "C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="_Grasshopper _Document _Open test_rhino_gh_bat.gh _Save _Exit _EnterEnd" "C:\Users\James\Documents\Rhino\Grasshopper\test_rhino_gh_bat.3dm"

REM "C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="-Grasshopper editor load document open test_rhino_gh_bat.gh _enter save _enter exit _enter" "C:\Users\James\Documents\Rhino\Grasshopper\test_rhino_gh_bat.3dm"
REM "C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="-GrasshopperPlayer test_rhino_gh_bat.gh _enter save _enter exit _enter" "C:\Users\James\Documents\Rhino\Grasshopper\test_rhino_gh_bat.3dm"
REM Rhino 5 or 6 only?  Credit to Andrew Heumann https://www.grasshopper3d.com/forum/topics/parallel-computation-run-iterations-on-multiple-computers
REM Example from James Ramsden here:  https://www.grasshopper3d.com/forum/topics/parallel-computation-run-iterations-on-multiple-computers
REM "C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="-grasshopper editor load document open test_rhino_gh_bat.gh _enter save _enter exit _enter" "C:\Users\James\Documents\Rhino\Grasshopper\test_rhino_gh_bat.3dm"
@ECHO OFF

copy README.md sDNA_GH
copy README.pdf sDNA_GH
copy license.md sDNA_GH
cd sDNA_GH
tar -caf ..\sDNA_GH.zip *
del README.md
del README.pdf
del license.md


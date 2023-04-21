@ECHO OFF

set zip_name=sdna-gh
set package_name=sDNA_GH

mkdir %zip_name%
copy README.md %zip_name%
copy README.pdf %zip_name%
copy license.md %zip_name%
xcopy %package_name% %zip_name%\%package_name% /I /S /E /Y
cd %zip_name%
tar -caf ..\%zip_name%.zip *
cd ..
rmdir /s /q %zip_name%
rem del README.md
rem del README.pdf
rem del license.md


@ECHO OFF

set user_objects_dir=C:\Users\James\AppData\Roaming\Grasshopper\UserObjects\

copy /Y sdna-gh.zip %user_objects_dir%
cd %user_objects_dir%
rmdir /S /Q sdna-gh
mkdir sdna-gh
cd sdna-gh
tar -xf ..\sdna-gh.zip

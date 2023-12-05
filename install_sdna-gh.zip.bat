@ECHO OFF

set user_objects_dir=%appdata%\Grasshopper\UserObjects\

@REM copy /Y - overwrites dest if necessary
copy /Y sdna-gh.zip %user_objects_dir%
cd %user_objects_dir%
@REM rem /S - recursive, /Q - Quietly, i.e. deletes without Y/N prompt
rmdir /S /Q sdna-gh
mkdir sdna-gh
cd sdna-gh
tar -xf ..\sdna-gh.zip

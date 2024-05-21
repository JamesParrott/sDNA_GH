@ECHO OFF

set cwd=%CD%
set user_objects_dir=%appdata%\Grasshopper\UserObjects\

@REM copy /Y - overwrites dest if necessary
copy /Y sdna-gh.zip %user_objects_dir%
cd %user_objects_dir%
@REM rem /S - recursive, /Q - Quietly, i.e. deletes without Y/N prompt
rmdir /S /Q sdna-gh
mkdir sdna-gh
@REM I don't know why unzipping in the parent directory is necessary
@REM but it's tricky to get it to work properly
cd sdna-gh
tar -xf ..\sdna-gh.zip
cd %cwd%
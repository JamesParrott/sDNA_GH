@ECHO OFF
set repo_path=%~dp0
cd %repo_path%
@REM PyPA's Build must be installed in the default Python environment.
@REM https://build.pypa.io/en/stable/installation.html
@REM
@REM outdir = {SRC_DIR}\dist is the default.  
@REM It is specified for the avoidance of doubt
@REM for compatibility with create_release_sdna-gh.zip.bat
python -m build --wheel --outdir=%repo_path%\dist .
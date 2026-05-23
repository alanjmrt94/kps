@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
cd /d "%ROOT%"

call "scripts\install.bat"
if errorlevel 1 exit /b 1

".venv\Scripts\python.exe" "kps.py" %*
exit /b %ERRORLEVEL%

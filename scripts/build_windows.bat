@echo off
REM Empaqueta kps.exe con PyInstaller (Windows).
setlocal
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" (
    echo [kps] Ejecuta install.bat o run.bat primero.
    exit /b 1
)
.venv\Scripts\pip install pyinstaller
.venv\Scripts\pyinstaller scripts\kps.spec --noconfirm
echo [kps] Ejecutable: dist\kps.exe
endlocal

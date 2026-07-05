@echo off
REM Empaqueta kps.exe con PyInstaller (Windows, sin dependencias externas).
setlocal EnableExtensions
cd /d "%~dp0\.."

echo [kps build] Directorio: %CD%

if not exist ".venv\Scripts\python.exe" (
    echo [kps build] ERROR: No hay .venv. Ejecuta install.bat o run.bat primero.
    exit /b 1
)

echo [kps build] Instalando PyInstaller y dependencias...
.venv\Scripts\python.exe -m pip install -q --upgrade pip wheel setuptools
.venv\Scripts\python.exe -m pip install -q pyinstaller
.venv\Scripts\python.exe -m pip install -q -r scripts\requirements-windows.txt
if errorlevel 1 exit /b 1

echo [kps build] Iconos: coloca assets\icons\kps.ico (ver assets\icons\README.md)

echo [kps build] Compilando kps.exe...
.venv\Scripts\pyinstaller scripts\kps.spec --noconfirm --clean
if errorlevel 1 exit /b 1

echo [kps build] Listo: dist\kps.exe
echo [kps build] Ejecutar: dist\kps.exe -h
endlocal

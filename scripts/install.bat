@echo off
setlocal EnableExtensions

set "ROOT=%~dp0.."
cd /d "%ROOT%"

echo [kps install] Directorio del proyecto: %CD%

where python >nul 2>&1
if errorlevel 1 (
    echo [kps install] ERROR: Python no encontrado. Instala Python 3 desde https://www.python.org/
    exit /b 1
)

if not exist ".venv" (
    echo [kps install] Creando entorno virtual en .venv...
    python -m venv .venv
    if errorlevel 1 exit /b 1
) else (
    echo [kps install] Usando entorno virtual existente en .venv.
)

echo [kps install] Activando entorno virtual...
call ".venv\Scripts\activate.bat"
if errorlevel 1 exit /b 1

echo [kps install] Actualizando pip...
python -m pip install --upgrade pip wheel setuptools
if errorlevel 1 exit /b 1

echo [kps install] Instalando dependencias desde scripts\requirements-windows.txt (PyPI)...
python -m pip install -r "scripts\requirements-windows.txt"
if errorlevel 1 exit /b 1

echo [kps install] Verificando imports principales...
python -c "import pyautogui; print('OK: pyautogui')"
if errorlevel 1 exit /b 1

echo [kps install] Instalacion completada.
echo [kps install] Ejecuta: .venv\Scripts\python.exe kps.py
echo [kps install] O usa: run.bat
exit /b 0

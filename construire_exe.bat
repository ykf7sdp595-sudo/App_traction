@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Environnement absent. Executez installer.bat avant de construire.
    pause
    exit /b 1
)
python -m pip --python .venv/Scripts/python.exe install -r requirements-build.txt
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m PyInstaller --noconfirm App_traction.spec
if errorlevel 1 exit /b 1
echo Executable cree : %CD%\dist\App_traction.exe
pause

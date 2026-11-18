@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Environnement absent. Executer installer.bat ou suivre README.md.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -c "import streamlit, plotly"
if errorlevel 1 (
    echo Dependances absentes ou environnement invalide. Executer installer.bat.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" launcher.py
if errorlevel 1 pause


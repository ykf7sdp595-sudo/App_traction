@echo off
cd /d "%~dp0"
python --version
if errorlevel 1 (
    echo Python est introuvable. Installer Python puis rouvrir ce fichier.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 (
        echo La creation de l'environnement a echoue. Voir README.md.
        pause
        exit /b 1
    )
)
python -m pip --python .venv/Scripts/python.exe install -r requirements.txt
if errorlevel 1 (
    echo Installation incomplete. Verifier la connexion et la version de Python.
    pause
    exit /b 1
)
echo Installation terminee. Utiliser lancer.bat.
pause

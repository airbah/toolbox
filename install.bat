@echo off
title Installation File Toolbox
cd /d "%~dp0"

echo ========================================
echo   Installation de File Toolbox
echo ========================================
echo.

REM Verifier si l'environnement virtuel existe
if not exist ".venv" (
    echo Creation de l'environnement virtuel...
    python -m venv .venv
)

REM Activer l'environnement virtuel
call .venv\Scripts\activate.bat

REM Installer les dependances
echo.
echo Installation des dependances...
pip install -r requirements.txt

echo.
echo ========================================
echo   Installation terminee !
echo   Lance run.bat pour demarrer l'app
echo ========================================
pause




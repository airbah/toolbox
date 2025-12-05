@echo off
title File Toolbox
cd /d "%~dp0"

REM Activer l'environnement virtuel
call .venv\Scripts\activate.bat

REM Lancer l'application
python main.py

REM Pause en cas d'erreur pour voir le message
if errorlevel 1 pause




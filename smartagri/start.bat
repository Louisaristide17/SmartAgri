@echo off
title SmartAgri

echo.
echo  ============================================
echo    SmartAgri - Demarrage local
echo  ============================================
echo.

:: Chemin absolu vers le dossier backend
set "BACKEND=%~dp0backend"
set "VENV_PY=%BACKEND%\venv\Scripts\python.exe"
set "VENV_PIP=%BACKEND%\venv\Scripts\pip.exe"

:: Aller dans le backend
cd /d "%BACKEND%"
if errorlevel 1 (
    echo ERREUR : dossier backend introuvable.
    pause
    exit /b 1
)

:: Verifier Python
where python >nul 2>&1
if errorlevel 1 (
    echo ERREUR : Python introuvable dans le PATH.
    echo Installez Python depuis https://www.python.org
    echo Cochez "Add Python to PATH" lors de l'installation.
    pause
    exit /b 1
)

echo  Python trouve.

:: Creer le fichier .env si absent
if not exist "%BACKEND%\.env" (
    if exist "%BACKEND%\.env.example" (
        copy "%BACKEND%\.env.example" "%BACKEND%\.env" >nul
        echo  Fichier .env cree.
    )
)

:: Creer le venv si absent
if not exist "%VENV_PY%" (
    echo  Creation du virtualenv Python...
    python -m venv "%BACKEND%\venv"
    if errorlevel 1 (
        echo ERREUR : impossible de creer le venv.
        pause
        exit /b 1
    )
    echo  Virtualenv cree.
)

:: Installer les dependances si fastapi est absent
"%VENV_PY%" -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo  Installation des dependances (patience, 1-3 min)...
    "%VENV_PIP%" install fastapi "uvicorn[standard]" sqlalchemy "python-jose[cryptography]" bcrypt python-dotenv "pydantic[email]" httpx aiofiles --quiet
    if errorlevel 1 (
        echo.
        echo ERREUR : installation des packages echouee.
        echo Verifiez votre connexion internet et reessayez.
        pause
        exit /b 1
    )
    echo  Packages installes.
)

:: Installer aiofiles si absent (pour les fichiers statiques)
"%VENV_PY%" -c "import aiofiles" >nul 2>&1
if errorlevel 1 (
    "%VENV_PIP%" install aiofiles --quiet
)

echo.
echo  ============================================
echo   Serveur demarre sur : http://localhost:8000
echo.
echo   Le site s'ouvre automatiquement.
echo   Compte demo : demo@smartagri.com
echo   Mot de passe : Demo1234!
echo.
echo   Appuyez sur CTRL+C pour arreter.
echo  ============================================
echo.

:: Ouvrir le navigateur apres 2 secondes
start /b cmd /c "timeout /t 2 >nul && start http://localhost:8000"

:: Lancer le backend
"%VENV_PY%" -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

echo.
echo  Serveur arrete.
pause

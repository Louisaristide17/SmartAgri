@echo off
title SmartAgri - Backend

echo.
echo  =============================================
echo    SmartAgri - Demarrage du backend FastAPI
echo  =============================================
echo.

:: ── Aller dans le dossier backend ──────────────────────────────
cd /d "%~dp0backend"
if errorlevel 1 (
    echo [ERREUR] Impossible d'acceder au dossier backend.
    echo Verifiez que le dossier "backend" existe dans le meme dossier que ce fichier.
    pause
    exit /b 1
)

echo  Dossier : %CD%
echo.

:: ── Verifier Python ────────────────────────────────────────────
python --version 2>nul
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    echo Telechargez Python sur : https://www.python.org/downloads/
    echo Cochez "Add Python to PATH" lors de l'installation.
    pause
    exit /b 1
)

:: ── Creer .env si absent ───────────────────────────────────────
if not exist ".env" (
    echo  Creation du fichier .env...
    copy ".env.example" ".env" >nul 2>&1
    echo  Fichier .env cree.
)

:: ── Installer les dependances ──────────────────────────────────
echo  Installation des dependances (patience)...
python -m pip install fastapi "uvicorn[standard]" sqlalchemy "python-jose[cryptography]" bcrypt python-dotenv "pydantic[email]" httpx --quiet --no-warn-script-location 2>nul
echo  Dependances OK.
echo.

:: ── Demarrer le serveur ────────────────────────────────────────
echo  -----------------------------------------------
echo   Serveur       : http://127.0.0.1:8000
echo   Documentation : http://127.0.0.1:8000/docs
echo   Login demo    : demo@smartagri.com
echo   Mot de passe  : Demo1234!
echo  -----------------------------------------------
echo.
echo  Ouvrez le fichier suivant dans votre navigateur :
echo  %~dp0frontend\login\index.html
echo.
echo  Appuyez sur CTRL+C pour arreter le serveur.
echo.

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

if errorlevel 1 (
    echo.
    echo [ERREUR] Le serveur a rencontre un probleme.
    echo Verifiez les messages ci-dessus pour plus de details.
)

echo.
pause

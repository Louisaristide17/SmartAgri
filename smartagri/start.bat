@echo off
chcp 65001 >nul
title SmartAgri - Lancement local

echo.
echo  =============================================
echo    SmartAgri - Demarrage local complet
echo  =============================================
echo.

:: ── Dossier backend ──────────────────────────────────────────
cd /d "%~dp0backend"
if errorlevel 1 (
    echo [ERREUR] Impossible d'acceder au dossier backend.
    pause & exit /b 1
)

:: ── Verifier Python ──────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python introuvable. Installez Python 3.11+ depuis python.org
    echo Cochez "Add Python to PATH" lors de l'installation.
    pause & exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  Python detecte : %PY_VER%

:: ── Creer .env si absent ─────────────────────────────────────
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo  Fichier .env cree depuis .env.example
    )
)

:: ── Creer ou recrér le venv si les packages manquent ─────────
set VENV_PY=venv\Scripts\python.exe
set VENV_PIP=venv\Scripts\pip.exe

if not exist "%VENV_PY%" (
    echo  Creation du virtualenv...
    python -m venv venv
)

:: Verifier que fastapi est installe dans le venv
%VENV_PY% -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo  Installation des dependances (1-2 minutes la premiere fois)...
    %VENV_PIP% install --upgrade pip --quiet
    %VENV_PIP% install ^
        fastapi ^
        "uvicorn[standard]" ^
        sqlalchemy ^
        "python-jose[cryptography]" ^
        "bcrypt" ^
        python-dotenv ^
        "pydantic[email]" ^
        httpx ^
        --quiet --no-warn-script-location
    if errorlevel 1 (
        echo [ERREUR] Installation echouee. Verifiez votre connexion internet.
        pause & exit /b 1
    )
    echo  Dependances installees.
)

echo.
echo  -----------------------------------------------
echo   API Backend   : http://localhost:8000
echo   Documentation : http://localhost:8000/docs
echo.
echo   >> Ouvrez CE lien dans votre navigateur <<
echo   http://localhost:8000/static/../../../frontend/login/index.html
echo.
echo   Ou ouvrez directement ce fichier :
echo   %~dp0frontend\login\index.html
echo.
echo   Compte demo : demo@smartagri.com / Demo1234!
echo  -----------------------------------------------
echo.
echo  Appuyez sur CTRL+C pour arreter.
echo.

:: ── Demarrer uvicorn avec le venv ────────────────────────────
%VENV_PY% -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

echo.
echo  Serveur arrete.
pause

@echo off
title SmartAgri

echo ============================================
echo   SmartAgri - Demarrage local
echo ============================================
echo.

cd /d "%~dp0backend"

echo Python trouve.
echo.
echo Installation des packages (1-3 min la 1ere fois)...
echo.

python -m pip install fastapi "uvicorn[standard]" sqlalchemy "python-jose[cryptography]" bcrypt python-dotenv "pydantic[email]" httpx aiofiles --quiet --no-warn-script-location

echo.
echo Packages OK.
echo.

if not exist ".env" (
    if exist ".env.example" copy ".env.example" ".env" >nul
)

echo ============================================
echo  Site disponible sur : http://localhost:8000
echo  Compte demo : demo@smartagri.com
echo  Mot de passe : Demo1234!
echo.
echo  Appuyez sur CTRL+C pour arreter.
echo ============================================
echo.

start /b cmd /c "timeout /t 3 >nul && start http://localhost:8000"

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

echo.
pause

@echo off
title appli.

echo.
echo   appli.  —  React + FastAPI
echo.
echo   Backend  ^> http://localhost:8000
echo   Frontend ^> http://localhost:3000
echo.

cd /d "%~dp0"

:: Backend en ventana separada
start "appli. — Backend" cmd /k "python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload"

:: Instalar node_modules si no existen
if not exist "frontend\node_modules\" (
    echo   Instalando dependencias npm...
    cd frontend
    npm install
    cd ..
)

:: Frontend en ventana separada
start "appli. — Frontend" cmd /k "cd frontend && npm run dev"

echo   Abriendo http://localhost:3000 ...
timeout /t 3 /nobreak > nul
start http://localhost:3000

echo.
echo   Cierra las dos ventanas negras para parar.
pause

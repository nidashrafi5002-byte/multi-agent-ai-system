@echo off
title Multi-Agent AI System Launcher
echo ===================================================
echo     Starting Multi-Agent AI System (Backend + Frontend)
echo ===================================================
echo.

:: 1. Launch FastAPI Backend in its own window
start "MAIA Backend (Port 8000)" cmd /k "call .\venv\Scripts\activate.bat && python backend\main.py"

:: 2. Launch React Frontend in its own window
start "MAIA Frontend (Port 3000)" cmd /k "cd frontend && npm start"

echo Both services have been launched!
echo.
echo - Frontend UI:  http://localhost:3000 (Use this link in your browser)
echo - Backend API:  http://localhost:8000 (API & Docs at /docs)
echo.
echo You can minimize this window.
pause

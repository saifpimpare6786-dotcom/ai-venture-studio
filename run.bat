@echo off
title Apex Venture Studio Launcher
echo ===================================================
echo   Apex Venture Studio - Autonomous Launch Script
echo ===================================================
echo.

REM 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.10+.
    pause
    exit /b 1
)

REM 2. Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH. Please install Node.js 18+.
    pause
    exit /b 1
)

echo [1/3] Starting FastAPI Backend on http://localhost:8000 ...
start "Apex Backend" cmd /k "cd backend && python main.py"

timeout /t 2 /nobreak >nul

echo [2/3] Starting Vite Frontend on http://localhost:5173 ...
start "Apex Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo [3/3] Opening Dashboard in browser ...
start http://localhost:5173

echo.
echo ===================================================
echo   Venture Studio is running!
echo   Dashboard: http://localhost:5173
echo   API Docs:  http://localhost:8000/docs
echo ===================================================
echo.

@echo off
REM Locus Copilot - Startup Script for Windows

echo.
echo ================================================================================
echo    LOCUS COPILOT - Location Intelligence System for Chennai
echo ================================================================================
echo.

set PROJECT_DIR=%~dp0
set VENV=%PROJECT_DIR%.venv\Scripts\python.exe
"%VENV%" --version >nul 2>&1
if errorlevel 1 (
    set VENV=python
)
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo [1/3] Starting Backend API (port 8000)...
start /B cmd /c "cd %PROJECT_DIR%backend && %VENV% -m uvicorn main:app --host 0.0.0.0 --port 8000"
timeout /t 2 /nobreak

echo [2/3] Starting Frontend Server (port 8080)...
start /B cmd /c "cd %PROJECT_DIR%frontend && %VENV% -m http.server 8080"
timeout /t 2 /nobreak

echo [3/3] Opening Browser...
start http://localhost:8080

echo.
echo ================================================================================
echo All services started!
echo.
echo   Frontend:  http://localhost:8080
echo   API Docs:  http://localhost:8000/docs
echo   Health:    http://localhost:8000/health
echo.
echo Instructions:
echo   1. Select a locality from the dropdown
echo   2. Choose a profile or adjust weights
echo   3. Click "Analyze" to see ranked locations
echo   4. Click on a result to zoom map to that location
echo.
echo To stop services: Close the terminal windows or use Task Manager
echo ================================================================================
echo.

@echo off
echo Starting Imagyn MCP Server...
echo.

REM Check if virtual environment exists
if not exist "imagyn_venv\Scripts\python.exe" (
    echo Error: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Check if config exists
if not exist "config.json" (
    echo Warning: config.json not found, using defaults
    echo.
)

REM Start the server
echo Starting server... Press Ctrl+C to stop
imagyn_venv\Scripts\python src\imagyn\server.py

pause

@echo off
chcp 65001 >nul
title HTML to DWIN BMP Converter - Setup

echo ==========================================
echo HTML to DWIN BMP Converter - Setup
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found:
python --version

:: Create virtual environment
echo.
echo Creating virtual environment...
if exist ".venv" (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

:: Install dependencies
echo.
echo Installing dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

:: Check Chrome
echo.
echo Checking Chrome installation...
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo [OK] Chrome found
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    echo [OK] Chrome found
) else (
    echo [WARNING] Chrome not found in standard locations
    echo Please install Chrome from https://google.com/chrome
)

echo.
echo ==========================================
echo Setup completed successfully!
echo ==========================================
echo.
echo To run the converter:
echo   - Double-click convert.bat, or
echo   - Run: .venv\Scripts\activate ^&^& python html_to_dwin.py
echo.
pause

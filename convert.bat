@echo off
chcp 65001 >nul
title DWIN HMI Converter

echo ==========================================
echo DWIN HMI Converter
echo ==========================================
echo.

:: Check for virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Create the environment:
    echo   python -m venv .venv
    echo.
    echo Install dependencies:
    echo   .venv\Scripts\activate
    echo   pip install selenium Pillow
    echo.
    pause
    exit /b 1
)

:: Check for Python script
if not exist "scripts\convert.py" (
    echo [ERROR] Script scripts\convert.py not found!
    pause
    exit /b 1
)

:: Activate environment
call .venv\Scripts\activate.bat

:: Run conversion
echo Starting conversion...
echo.
python scripts\convert.py %*

:: Check result
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo [SUCCESS] Conversion complete!
    echo ==========================================
    echo.
    echo Output locations:
    echo   - output\pages\    : Page screenshots
    echo   - output\elements\ : UI elements
    echo   - output\dgus\DWIN_SET\ : DGUS project files
    echo   - output\dgus\ICON\     : Icon groups
    echo   - output\dgus\templates\: Template images with element outlines
    echo ==========================================
    echo.
    echo Press any key to open output folder...
    pause >nul
    start explorer "output"
) else (
    echo.
    echo ==========================================
    echo [ERROR] Conversion failed!
    echo ==========================================
    echo.
    pause
)

:: Deactivate environment
call .venv\Scripts\deactivate.bat

#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup script for HTML to DWIN BMP Converter
.DESCRIPTION
    Creates Python virtual environment and installs dependencies
.NOTES
    Run this script in PowerShell: .\setup.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "HTML to DWIN BMP Converter - Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/4] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "      Found: $pythonVersion"
} catch {
    Write-Host "      ERROR: Python not found!" -ForegroundColor Red
    Write-Host "      Please install Python 3.10 or higher from https://python.org"
    exit 1
}

# Check if venv exists
Write-Host "[2/4] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "      Virtual environment already exists, skipping creation"
} else {
    python -m venv .venv
    Write-Host "      Created: .venv" -ForegroundColor Green
}

# Activate and install dependencies
Write-Host "[3/4] Installing dependencies..." -ForegroundColor Yellow
$pipPath = ".venv\Scripts\pip.exe"
& $pipPath install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "      ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "      Dependencies installed successfully" -ForegroundColor Green

# Verify Chrome installation
Write-Host "[4/4] Checking Chrome installation..." -ForegroundColor Yellow
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$chromePathX86 = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

if (Test-Path $chromePath) {
    Write-Host "      Found: $chromePath" -ForegroundColor Green
} elseif (Test-Path $chromePathX86) {
    Write-Host "      Found: $chromePathX86" -ForegroundColor Green
} else {
    Write-Host "      WARNING: Chrome not found in standard locations" -ForegroundColor Yellow
    Write-Host "      Please install Google Chrome from https://google.com/chrome"
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To run the converter:"
Write-Host "  1. Activate environment: .venv\Scripts\activate"
Write-Host "  2. Run converter: python html_to_dwin.py"
Write-Host "  3. Or simply double-click: convert.bat"
Write-Host ""
Write-Host "For DGUS preparation:"
Write-Host "  python prepare_for_dgus.py"
Write-Host ""

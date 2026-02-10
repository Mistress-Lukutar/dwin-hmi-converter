@echo off
:: Launcher for convert.py from scripts directory
:: This batch file forwards to the main convert.bat in the project root

cd /d "%~dp0\.."
call convert.bat %*

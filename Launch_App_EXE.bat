@echo off
:: Launches the compiled TG Contact Extractor standalone executable
title Launching TG Contact Extractor...
cd /d "%~dp0"

if not exist "dist\TGContactExtractor\TGContactExtractor.exe" (
    echo [ERROR] Compiled executable not found!
    echo Please run build.bat first to build the executable.
    echo.
    pause
    exit /b 1
)

start "" "%~dp0dist\TGContactExtractor\TGContactExtractor.exe"
exit

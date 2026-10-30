@echo off
:: ============================================================
::  TG Contact Extractor - Application Launcher
:: ============================================================
title TG Contact Extractor

echo ============================================================
echo   TG Contact Extractor Launcher
echo ============================================================
echo.

:: Ensure working directory is the script's directory
cd /d "%~dp0"

:: Detect Python
set PYTHON_CMD=
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
) else (
    py --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=py
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python is not found on your system PATH!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo and ensure "Add Python to PATH" is checked during installation.
    echo.
    pause
    exit /b 1
)

:: Verify dependencies
echo [1/2] Verifying dependencies...
%PYTHON_CMD% -c "import customtkinter, telethon, openpyxl, PIL" >nul 2>&1
if errorlevel 1 (
    echo Dependencies missing. Installing from requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)
echo       Dependencies OK.

:: Launch Application
echo [2/2] Starting TG Contact Extractor...
echo.
%PYTHON_CMD% main.py

if errorlevel 1 (
    echo.
    echo [NOTICE] Application exited with error code: %errorlevel%
    pause
)

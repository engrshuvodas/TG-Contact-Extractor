@echo off
:: TG Contact Extractor - Windows Build Script
:: Requires: Python 3.11+, PyInstaller, all dependencies installed

echo =============================================
echo  TG Contact Extractor - Windows Build Script
echo =============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not on PATH.
    pause
    exit /b 1
)

:: Install dependencies
echo [1/4] Installing dependencies...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo       Done.

:: Clean previous build
echo [2/4] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist TGContactExtractor.spec del /f /q TGContactExtractor.spec
echo       Done.

:: Build executable
echo [3/4] Building executable with PyInstaller...
pyinstaller ^
    --name "TGContactExtractor" ^
    --onedir ^
    --windowed ^
    --icon "assets\icons\app.ico" ^
    --add-data "assets;assets" ^
    --add-data "config.py;." ^
    --hidden-import "customtkinter" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "telethon" ^
    --hidden-import "openpyxl" ^
    --hidden-import "sqlite3" ^
    --collect-data "customtkinter" ^
    --noconfirm ^
    main.py

if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)
echo       Done.

:: Post-build: copy assets and create required folders
echo [4/4] Finalising build...
if not exist "dist\TGContactExtractor\assets" mkdir "dist\TGContactExtractor\assets"
xcopy /e /i /y "assets" "dist\TGContactExtractor\assets" >nul 2>&1

for %%d in (data sessions exports logs) do (
    if not exist "dist\TGContactExtractor\%%d" mkdir "dist\TGContactExtractor\%%d"
)

:: Clean temporary build files to avoid opening intermediate files
if exist build rmdir /s /q build
if exist TGContactExtractor.spec del /f /q TGContactExtractor.spec

echo.
echo =============================================
echo  Build Complete!
echo  Executable: dist\TGContactExtractor\TGContactExtractor.exe
echo =============================================
pause

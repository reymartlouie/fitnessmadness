@echo off
title FitnessMadness Kiosk

:: Change to the project directory (wherever this .bat file lives)
cd /d %~dp0

:: Activate virtual environment
call venv\Scripts\activate

:: Initialize database if it doesn't exist yet
if not exist database\fitnessmadness.db (
    python database\init_db.py
)

:: Back up the database on every startup (keeps last 7 copies in database\backups\)
python database\backup.py

:: Copy latest backup to USB flash drive if one is plugged in
python database\flashdrive_backup.py

:: Copy latest backup to Google Drive if installed
python database\gdrive_backup.py

:: Apply any schema updates (safe to run repeatedly)
python database\migrate.py

:: Start Flask in the background
start /B python app.py

:: Wait 3 seconds for Flask to start
timeout /t 3 /nobreak >nul

:: Open kiosk in Chrome, fall back to Edge if Chrome is not installed
set BROWSER=
if exist "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe" set BROWSER=%PROGRAMFILES%\Google\Chrome\Application\chrome.exe
if exist "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe" set BROWSER=%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set BROWSER=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe

if "%BROWSER%"=="" if exist "%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe" set BROWSER=%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe
if "%BROWSER%"=="" if exist "%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe" set BROWSER=%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe

if "%BROWSER%"=="" (
    echo [WARN] Chrome and Edge not found. Open http://localhost:5000 manually in your browser.
) else (
    start "" "%BROWSER%" --kiosk --app=http://localhost:5000
)

echo FitnessMadness is running.

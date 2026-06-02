@echo off
title FitnessMadness Kiosk

:: Change to the project directory (update this path to match the gym PC)
cd /d C:\fitnessmadness

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

:: Apply any schema updates (safe to run repeatedly)
python database\migrate.py

:: Start Flask in the background
start /B python app.py

:: Wait 3 seconds for Flask to start
timeout /t 3 /nobreak >nul

:: Open Chrome in kiosk mode
start chrome --kiosk --app=http://localhost:5000

echo FitnessMadness is running.

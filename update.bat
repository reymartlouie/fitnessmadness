@echo off
title FitnessMadness Update
cd /d C:\fitnessmadness

echo Stopping the kiosk...
taskkill /F /IM chrome.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo Backing up database...
call venv\Scripts\activate
python database\backup.py

echo Pulling latest code from git...
git pull

echo Installing any new dependencies...
pip install -r requirements.txt -q

echo Restarting kiosk...
call start.bat

echo Update complete.

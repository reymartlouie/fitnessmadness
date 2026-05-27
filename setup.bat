@echo off
title FitnessMadness Setup
cd /d %~dp0

echo ============================================
echo   FitnessMadness Gym System - First Setup
echo ============================================
echo.

:: ── Step 1: Check Python ─────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please download and install Python 3.10+ from https://www.python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
echo [OK] Python found.

:: ── Step 2: Check Git ────────────────────────────────────────────────
git --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] Git is not installed. Updates via update.bat will not work.
    echo You can install Git from https://git-scm.com if needed.
) else (
    echo [OK] Git found.
)

:: ── Step 3: Create virtual environment ───────────────────────────────
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists.
)

:: ── Step 4: Install dependencies ─────────────────────────────────────
echo Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.

:: ── Step 5: Set up .env if missing ───────────────────────────────────
if not exist .env (
    echo.
    echo Setting up your gym configuration...
    set /p GYM_NAME="Enter your gym name (e.g. Iron Gym): "
    if "%GYM_NAME%"=="" set GYM_NAME=My Gym

    python -c "import secrets; print(secrets.token_hex(32))" > _key.tmp
    set /p SECRET_KEY=<_key.tmp
    del _key.tmp

    (
        echo SECRET_KEY=%SECRET_KEY%
        echo DATABASE_URL=sqlite:///database/fitnessmadness.db
        echo GYM_NAME=%GYM_NAME%
    ) > .env
    echo [OK] Configuration saved to .env
) else (
    echo [OK] .env already exists.
)

:: ── Step 6: Initialize database ──────────────────────────────────────
if not exist database\fitnessmadness.db (
    echo Initializing database...
    python database\init_db.py
    echo [OK] Database created.
) else (
    echo [OK] Database already exists.
)

:: ── Step 7: Run migrations ────────────────────────────────────────────
echo Applying schema updates...
python database\migrate.py

:: ── Step 8: Create admin account ─────────────────────────────────────
echo.
echo Creating admin account...
python database\create_admin.py

:: ── Step 9: Register auto-start with Windows Task Scheduler ──────────
echo.
echo Registering kiosk to start automatically on Windows login...
set TASK_NAME=FitnessMadness Kiosk
set BAT_PATH=%~dp0start.bat

schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if errorlevel 1 (
    schtasks /create /tn "%TASK_NAME%" /tr "\"%BAT_PATH%\"" /sc onlogon /rl highest /f >nul
    if errorlevel 1 (
        echo [WARN] Could not register auto-start. Run setup.bat as Administrator to enable this.
    ) else (
        echo [OK] Auto-start registered. Kiosk will launch automatically on Windows login.
    )
) else (
    echo [OK] Auto-start already registered.
)

:: ── Done ──────────────────────────────────────────────────────────────
echo.
echo ============================================
echo   Setup complete! Launching kiosk now...
echo ============================================
echo.
call start.bat

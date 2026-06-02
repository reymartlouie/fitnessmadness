# FitnessMadness — Gym Attendance Management System

FitnessMadness is a lightweight gym management system that runs on a local Windows PC. It features a member-facing kiosk for check-in and check-out, and an admin dashboard for managing members, tracking attendance, recording payments, and exporting data to CSV. No internet required. Auto-starts on Windows login.

---

## First-Time Setup (do this once)

### 1. Install Python
- Download from https://python.org
- During install, tick **"Add Python to PATH"**

### 2. Copy project to the gym PC
- Recommended location: `C:\fitnessmadness`

### 3. Open Command Prompt in the project folder
```
cd C:\fitnessmadness
```

### 4. Create virtual environment and install packages
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Set up the database
```
python database\init_db.py
python database\create_admin.py
```

### 6. (Optional) Add sample members
```
python database\seed_data.py
```

### 7. Test run
```
python app.py
```
Open `http://localhost:5000` in Chrome.

---

## Auto-Start on Windows Boot

1. Press `Win + R` → type `shell:startup` → press Enter
2. A folder opens — create a **shortcut** to `start.bat` inside it
3. Restart the PC — the app will launch automatically

### To exit kiosk mode (Chrome fullscreen)
Press `Alt + F4` or `Ctrl + W`

---

## Daily Use

| Task | How |
|---|---|
| Start the system | Double-click `start.bat` |
| Stop the system | Close the terminal window |
| Admin dashboard | Click "Admin Access" on kiosk screen |
| Admin login | Username and password set during setup |

---

## Membership Prices
| Type | Monthly Fee |
|---|---|
| Regular | ₱850.00 |
| Student | ₱650.00 |
| Senior | ₱650.00 |

To change prices: edit `models/member.py` → `MEMBERSHIP_PRICES`

---

## Backup

The system runs three layers of backup automatically on every kiosk start:

**1. Local backup (always on)**
Saves a timestamped copy to `database/backups/` and keeps the last 7.

**2. USB flash drive backup (automatic)**
If a flash drive is plugged in, the latest backup is copied to a `FitnessMadness_Backup/` folder on the drive. No setup needed.

**3. Google Drive backup (optional)**
Install [Google Drive for Desktop](https://drive.google.com/drive/download) and sign in with your Google account. The system auto-detects the sync folder and copies the latest backup there on startup.

If the auto-detection fails, add this line to `.env`:
```
GOOGLE_DRIVE_PATH=C:\Users\YourName\Google Drive
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| App won't start | Make sure Python is installed and venv is activated |
| Port 5000 in use | Restart the PC |
| Forgot admin password | Run `python database\create_admin.py` with a new username |
| Database error | Run `python database\init_db.py` again |

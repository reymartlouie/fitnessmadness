# FitnessMadness — Gym Attendance Management System

A local kiosk-based gym attendance system. Runs entirely on one PC.
No internet required. No monthly fees.

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

The entire database is one file:
```
database/fitnessmadness.db
```
Copy this file to a USB drive regularly to back up all member and attendance data.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| App won't start | Make sure Python is installed and venv is activated |
| Port 5000 in use | Restart the PC |
| Forgot admin password | Run `python database\create_admin.py` with a new username |
| Database error | Run `python database\init_db.py` again |

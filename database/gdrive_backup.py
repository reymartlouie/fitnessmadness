"""
Google Drive backup — copies the latest backup into the local Google Drive
sync folder. Google Drive for Desktop handles the actual cloud upload.
Requires Google Drive for Desktop to be installed and signed in.

Path detection order:
  1. GOOGLE_DRIVE_PATH in .env (manual override)
  2. Common default locations (~/Google Drive, ~/My Drive, etc.)
  3. Windows registry (DriveFS sync root)
"""
import os
import sys
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')
GDRIVE_FOLDER_NAME = 'FitnessMadness_Backup'

COMMON_PATHS = [
    os.path.expanduser('~/Google Drive'),
    os.path.expanduser('~/My Drive'),
    os.path.expanduser('~/Google Drive My Drive'),
    os.path.expanduser('~/GoogleDrive'),
]


def find_gdrive_path():
    # 1. Manual override from .env
    env_path = os.environ.get('GOOGLE_DRIVE_PATH', '').strip()
    if env_path and os.path.isdir(env_path):
        return env_path

    # 2. Common default locations
    for path in COMMON_PATHS:
        if os.path.isdir(path):
            return path

    # 3. Windows registry (Google Drive for Desktop / DriveFS)
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Google\DriveFS\Share'
        )
        path, _ = winreg.QueryValueEx(key, 'PerAccountPreferences')
        winreg.CloseKey(key)
        if path and os.path.isdir(path):
            return path
    except Exception:
        pass

    return None


def get_latest_backup():
    if not os.path.exists(BACKUP_DIR):
        return None
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')],
        reverse=True
    )
    return os.path.join(BACKUP_DIR, backups[0]) if backups else None


def run_gdrive_backup():
    gdrive_path = find_gdrive_path()

    if not gdrive_path:
        print(
            "Google Drive backup: Drive folder not found.\n"
            "  Fix: Add GOOGLE_DRIVE_PATH=C:\\Users\\You\\Google Drive to .env\n"
            "  Or install Google Drive for Desktop: https://drive.google.com/drive/download"
        )
        return

    latest = get_latest_backup()
    if not latest:
        print("Google Drive backup: No backup file found. Skipping.")
        return

    filename = os.path.basename(latest)
    dest_dir = os.path.join(gdrive_path, GDRIVE_FOLDER_NAME)
    dest_file = os.path.join(dest_dir, filename)

    try:
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(latest, dest_file)
        print(f"Google Drive backup: Copied {filename} → {dest_dir}")
    except Exception as e:
        print(f"Google Drive backup: Failed — {e}")


if __name__ == '__main__':
    run_gdrive_backup()

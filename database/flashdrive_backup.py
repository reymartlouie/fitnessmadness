"""
Flash drive backup — copies the latest backup to any removable USB drive found.
Runs automatically on kiosk start via start.bat.
"""
import os
import sys
import shutil
import string

BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')
FLASH_FOLDER_NAME = 'FitnessMadness_Backup'


def get_removable_drives():
    try:
        import ctypes
        drives = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive = f"{letter}:\\"
                if ctypes.windll.kernel32.GetDriveType(drive) == 2:  # DRIVE_REMOVABLE
                    drives.append(drive)
            bitmask >>= 1
        return drives
    except Exception:
        return []


def get_latest_backup():
    if not os.path.exists(BACKUP_DIR):
        return None
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')],
        reverse=True
    )
    return os.path.join(BACKUP_DIR, backups[0]) if backups else None


def run_flashdrive_backup():
    drives = get_removable_drives()

    if not drives:
        print("Flash drive backup: No USB drive detected. Skipping.")
        return

    latest = get_latest_backup()
    if not latest:
        print("Flash drive backup: No backup file found. Skipping.")
        return

    filename = os.path.basename(latest)
    copied = []

    for drive in drives:
        dest_dir = os.path.join(drive, FLASH_FOLDER_NAME)
        dest_file = os.path.join(dest_dir, filename)
        try:
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(latest, dest_file)
            copied.append(drive)
        except Exception as e:
            print(f"Flash drive backup: Failed to copy to {drive} — {e}")

    if copied:
        drives_str = ', '.join(copied)
        print(f"Flash drive backup: Copied {filename} to {drives_str}")
    else:
        print("Flash drive backup: Copy failed on all detected drives.")


if __name__ == '__main__':
    run_flashdrive_backup()

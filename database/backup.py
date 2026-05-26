"""
Daily database backup — keeps the last 7 backups in database/backups/.
Run manually or schedule via Windows Task Scheduler / cron.
"""
import sys
import os
import shutil
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DB_PATH = os.path.join(os.path.dirname(__file__), 'fitnessmadness.db')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')
KEEP_LAST = 7


def run_backup():
    if not os.path.exists(DB_PATH):
        print("ERROR: Database file not found. Nothing to back up.")
        sys.exit(1)

    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    dest = os.path.join(BACKUP_DIR, f'fitnessmadness_{timestamp}.db')

    shutil.copy2(DB_PATH, dest)
    print(f"Backup saved: {dest}")

    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')],
        reverse=True
    )
    for old in backups[KEEP_LAST:]:
        os.remove(os.path.join(BACKUP_DIR, old))
        print(f"Removed old backup: {old}")


if __name__ == '__main__':
    run_backup()

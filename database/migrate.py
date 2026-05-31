"""
Schema migration — safe to run multiple times.
Adds new columns to existing tables without touching data.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db


MIGRATIONS = [
    ("members", "phone",  "ALTER TABLE members ADD COLUMN phone VARCHAR(20)"),
    ("members", "email",  "ALTER TABLE members ADD COLUMN email VARCHAR(120)"),
    ("admins",  "email",  "ALTER TABLE admins ADD COLUMN email VARCHAR(120)"),
    ("admins",  "phone",  "ALTER TABLE admins ADD COLUMN phone VARCHAR(20)"),
]

CREATE_TABLES = [
    """CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER NOT NULL REFERENCES members(id),
        amount REAL NOT NULL,
        payment_date DATE NOT NULL,
        recorded_at DATETIME NOT NULL,
        notes VARCHAR(200)
    )""",
]


def run_migrations():
    app = create_app()
    with app.app_context():
        conn = db.engine.raw_connection()
        cursor = conn.cursor()

        for table, column, sql in MIGRATIONS:
            # Check if column already exists before adding
            cursor.execute(f"PRAGMA table_info({table})")
            existing = [row[1] for row in cursor.fetchall()]
            if column not in existing:
                cursor.execute(sql)
                print(f"  Added column: {table}.{column}")
            else:
                print(f"  Already exists: {table}.{column}")

        for sql in CREATE_TABLES:
            cursor.execute(sql)

        conn.commit()
        conn.close()
        print("Migration complete.")


if __name__ == '__main__':
    run_migrations()

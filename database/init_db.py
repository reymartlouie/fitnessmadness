import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from models.admin import Admin
from models.member import Member
from models.attendance import Attendance

def init_database():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")
        print("Tables:", db.engine.table_names() if hasattr(db.engine, 'table_names') else "admins, members, attendance")

if __name__ == '__main__':
    init_database()

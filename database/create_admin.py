import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from models.admin import Admin


def create_admin(username, password):
    app = create_app()
    with app.app_context():
        existing = Admin.query.filter_by(username=username).first()
        if existing:
            print(f"Admin '{username}' already exists.")
            return

        admin = Admin(username=username)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin '{username}' created successfully.")


if __name__ == '__main__':
    print("=== Create Admin Account ===")
    username = input("Enter admin username: ").strip()
    password = input("Enter admin password: ").strip()

    if not username or not password:
        print("Username and password cannot be empty.")
        sys.exit(1)

    create_admin(username, password)

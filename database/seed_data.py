import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from models.member import Member, MembershipType
from datetime import date
from dateutil.relativedelta import relativedelta


SAMPLE_MEMBERS = [
    {'membership_id': 'GM001', 'full_name': 'Juan dela Cruz',     'membership_type': MembershipType.REGULAR},
    {'membership_id': 'GM002', 'full_name': 'Maria Santos',       'membership_type': MembershipType.STUDENT},
    {'membership_id': 'GM003', 'full_name': 'Roberto Reyes',      'membership_type': MembershipType.SENIOR},
    {'membership_id': 'GM004', 'full_name': 'Ana Gonzales',       'membership_type': MembershipType.REGULAR},
    {'membership_id': 'GM005', 'full_name': 'Carlos Mendoza',     'membership_type': MembershipType.STUDENT},
]


def seed():
    app = create_app()
    with app.app_context():
        added = 0
        for data in SAMPLE_MEMBERS:
            existing = Member.query.filter_by(membership_id=data['membership_id']).first()
            if existing:
                print(f"Skipping {data['membership_id']} — already exists.")
                continue

            member = Member(
                membership_id=data['membership_id'],
                full_name=data['full_name'],
                membership_type=data['membership_type'],
                membership_start=date.today(),
                membership_end=date.today() + relativedelta(months=1),
                is_active=True
            )
            db.session.add(member)
            added += 1

        db.session.commit()
        print(f"{added} sample members added.")


if __name__ == '__main__':
    seed()

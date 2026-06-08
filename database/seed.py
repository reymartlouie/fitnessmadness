"""
Seed script — wipes members, attendance, and payments, then inserts fresh dummy data.
Safe to run multiple times (always starts clean).
"""
import sys
import os
import random
from datetime import datetime, date, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models.member import Member, MembershipType, MEMBERSHIP_PRICES
from models.attendance import Attendance
from models.payment import Payment
from dateutil.relativedelta import relativedelta

FIRST_NAMES = [
    'Juan', 'Maria', 'Jose', 'Ana', 'Carlo', 'Liza', 'Miguel', 'Rosa',
    'Ramon', 'Cristina', 'Mark', 'Jasmine', 'Kevin', 'Maricel', 'Patrick',
    'Sheila', 'Bryan', 'Lovely', 'Dennis', 'Vanessa', 'Ronel', 'Marites',
    'Christian', 'Grace', 'Jerome', 'Rhodora', 'Adrian', 'Precious', 'Rex',
    'Jenilyn',
]

LAST_NAMES = [
    'Santos', 'Reyes', 'Cruz', 'Bautista', 'Ocampo', 'Garcia', 'Mendoza',
    'Torres', 'Castillo', 'Villanueva', 'Gonzales', 'Flores', 'Ramos',
    'Aquino', 'dela Cruz', 'Aguilar', 'Morales', 'Diaz', 'Padilla', 'Lim',
]

TYPES = MembershipType.ALL  # 5 types, no senior

def random_ph_phone():
    return f'09{random.randint(100000000, 999999999)}'

def make_membership_id(index):
    return f'FM-{str(index).zfill(4)}'

def seed():
    app = create_app()
    with app.app_context():
        # ── Wipe existing data ────────────────────────────────────────
        Attendance.query.delete()
        Payment.query.delete()
        Member.query.delete()
        db.session.execute(db.text("DELETE FROM sqlite_sequence WHERE name IN ('members','attendance','payments')"))
        db.session.commit()
        print('Cleared members, attendance, payments.')

        # ── Build dummy members ───────────────────────────────────────
        today = date.today()
        members = []

        random.seed(42)
        used_names = set()

        for i in range(1, 31):
            while True:
                name = f'{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}'
                if name not in used_names:
                    used_names.add(name)
                    break

            mtype = TYPES[(i - 1) % len(TYPES)]

            # spread: active, expiring soon, expired, just renewed
            if i <= 20:
                # active — ends 5 to 28 days from now
                end = today + timedelta(days=random.randint(5, 28))
            elif i <= 25:
                # expiring within 7 days
                end = today + timedelta(days=random.randint(1, 6))
            else:
                # expired (within or past grace)
                end = today - timedelta(days=random.randint(1, 20))

            start = end - relativedelta(months=1)
            is_active = end >= today

            phone = random_ph_phone() if random.random() > 0.3 else None
            email = f'{name.lower().replace(" ", ".").replace("dela.", "dela")}@gmail.com' if random.random() > 0.5 else None

            # waiver for all members (required since feature was built)
            waiver_signed_at = datetime.combine(start, datetime.min.time()) + timedelta(hours=random.randint(8, 17))

            m = Member(
                membership_id=make_membership_id(i),
                full_name=name,
                phone=phone,
                email=email,
                membership_type=mtype,
                membership_start=start,
                membership_end=end,
                is_active=is_active,
                created_at=datetime.combine(start, datetime.min.time()),
                waiver_signed_at=waiver_signed_at,
                waiver_name=name,
                waiver_fb_username=None,
            )
            db.session.add(m)
            members.append(m)

        db.session.commit()
        print(f'Inserted {len(members)} members.')

        # ── Attendance — last 30 days ─────────────────────────────────
        att_count = 0
        for m in members:
            if not m.is_active:
                continue
            days_back = random.randint(3, 15)
            for _ in range(days_back):
                att_date = today - timedelta(days=random.randint(0, 29))
                check_in = datetime.combine(att_date, datetime.min.time()) + timedelta(hours=random.randint(6, 18), minutes=random.randint(0, 59))
                check_out = check_in + timedelta(hours=random.randint(1, 2), minutes=random.randint(0, 59))
                duration = int((check_out - check_in).total_seconds() / 60)
                db.session.add(Attendance(
                    member_id=m.id,
                    attendance_date=att_date,
                    check_in_time=check_in,
                    check_out_time=check_out,
                    duration_minutes=duration,
                ))
                att_count += 1

        db.session.commit()
        print(f'Inserted {att_count} attendance records.')

        # ── Payments — one per active member ─────────────────────────
        pay_count = 0
        for m in members:
            if not m.is_active:
                continue
            amount = MEMBERSHIP_PRICES.get(m.membership_type, 950.00)
            db.session.add(Payment(
                member_id=m.id,
                amount=amount,
                payment_date=m.membership_start,
                recorded_at=datetime.combine(m.membership_start, datetime.min.time()) + timedelta(hours=9),
                notes=None,
            ))
            pay_count += 1

        db.session.commit()
        print(f'Inserted {pay_count} payment records.')
        print('Done.')

if __name__ == '__main__':
    seed()

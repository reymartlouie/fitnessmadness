"""
Demo seed script — creates realistic gym data for client demonstrations.
Run once on a fresh database: python database/demo_seed.py

Creates:
  - 500 members (mix of active, expired, expiring soon)
  - Attendance history over the past 6 months
  - Payment records for members who renewed
  - Live check-ins today for demo realism
"""
import sys
import os
import random
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from models.member import Member, MembershipType
from models.attendance import Attendance
from models.payment import Payment

FIRST_NAMES = [
    'Juan', 'Maria', 'Jose', 'Ana', 'Carlos', 'Rosa', 'Miguel', 'Elena',
    'Roberto', 'Linda', 'Antonio', 'Carmen', 'Eduardo', 'Gloria', 'Ricardo',
    'Teresa', 'Fernando', 'Maricel', 'Rodrigo', 'Cristina', 'Mark', 'Liza',
    'Angelo', 'Sheila', 'Dennis', 'Karen', 'Ryan', 'Janine', 'Kevin', 'Aileen',
    'Patrick', 'Honey', 'Rodel', 'Marites', 'Nonoy', 'Nena', 'Boyet', 'Cynthia',
    'Raffy', 'Gina', 'Dodong', 'Rowena', 'Ariel', 'Peachy', 'Erwin', 'Joana',
    'Renz', 'Lyn', 'Jerome', 'Lovely',
]

LAST_NAMES = [
    'dela Cruz', 'Santos', 'Reyes', 'Gonzales', 'Mendoza', 'Garcia', 'Torres',
    'Flores', 'Lopez', 'Ramos', 'Bautista', 'Aquino', 'Castro', 'Villanueva',
    'Dela Rosa', 'Soriano', 'Diaz', 'Hernandez', 'Navarro', 'Morales',
    'Castillo', 'Domingo', 'Pascual', 'Guerrero', 'Aguilar', 'Miranda',
    'Ortega', 'Salazar', 'Tolentino', 'Velasco',
]

MEMBERSHIP_FEES = {
    MembershipType.REGULAR: 850,
    MembershipType.STUDENT: 650,
    MembershipType.SENIOR: 850,
}


def clear_demo_data(app):
    with app.app_context():
        members = Member.query.filter(Member.membership_id.like('DEMO%')).all()
        if not members:
            return
        ids = [m.id for m in members]
        Attendance.query.filter(Attendance.member_id.in_(ids)).delete(synchronize_session=False)
        Payment.query.filter(Payment.member_id.in_(ids)).delete(synchronize_session=False)
        Member.query.filter(Member.membership_id.like('DEMO%')).delete(synchronize_session=False)
        db.session.commit()
        print(f"[OK] Cleared {len(members)} existing demo members.")


def seed_demo(app):
    today = date.today()

    with app.app_context():
        added = 0

        for i in range(1, 276):
            mid = f'DEMO{i:04d}'
            if Member.query.filter_by(membership_id=mid).first():
                continue

            name = f'{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}'
            mtype = random.choices(
                [MembershipType.REGULAR, MembershipType.STUDENT, MembershipType.SENIOR],
                weights=[60, 30, 10]
            )[0]
            phone = f'09{random.randint(100000000, 999999999)}'
            email = f'member{i}@demo.ph'

            # ── Assign member category ─────────────────────────────────
            # 55% active (paying regularly)
            # 15% expiring within 7 days (show alert)
            # 20% expired — never renewed
            # 10% renewed at least once

            roll = random.random()

            if roll < 0.55:
                # Active — started 1-11 months ago, still valid
                category = 'active'
                months_ago = random.randint(1, 11)
                start = today - relativedelta(months=months_ago)
                end = start + relativedelta(months=1)
                while end < today:
                    end += relativedelta(months=1)
                is_active = True

            elif roll < 0.70:
                # Expiring soon — ends within 7 days
                category = 'expiring'
                start = today - relativedelta(months=1) + timedelta(days=random.randint(0, 6))
                end = today + timedelta(days=random.randint(1, 7))
                is_active = True

            elif roll < 0.90:
                # Expired — lapsed 1-6 months ago, never renewed
                category = 'expired'
                start = today - relativedelta(months=random.randint(2, 8))
                end = start + relativedelta(months=1)
                is_active = False

            else:
                # Renewed — has payment history
                category = 'renewed'
                start = today - relativedelta(months=random.randint(2, 6))
                end = start + relativedelta(months=1)
                while end < today:
                    end += relativedelta(months=1)
                is_active = True

            member = Member(
                membership_id=mid,
                full_name=name,
                membership_type=mtype,
                membership_start=start,
                membership_end=end,
                is_active=is_active,
                phone=phone,
                email=email,
            )
            db.session.add(member)
            db.session.flush()

            # ── Attendance records ─────────────────────────────────────
            if category == 'expired':
                # Attended only while membership was valid
                visit_days = random.randint(3, 15)
                visit_range_end = min(end, today)
            elif category == 'expiring':
                visit_days = random.randint(10, 25)
                visit_range_end = today
            else:
                visit_days = random.randint(15, 60)
                visit_range_end = today

            visit_range_start = start
            span = (visit_range_end - visit_range_start).days
            if span > 0:
                sampled_days = random.sample(range(span), min(visit_days, span))
                for day_offset in sampled_days:
                    att_date = visit_range_start + timedelta(days=day_offset)
                    hour = random.randint(5, 20)
                    minute = random.randint(0, 59)
                    check_in = datetime.combine(att_date, datetime.min.time()).replace(hour=hour, minute=minute)
                    duration = random.randint(20, 120)
                    check_out = check_in + timedelta(minutes=duration)
                    att = Attendance(
                        member_id=member.id,
                        attendance_date=att_date,
                        check_in_time=check_in,
                        check_out_time=check_out,
                        duration_minutes=duration,
                    )
                    db.session.add(att)

            # ── Live check-in today (first 20 active members) ──────────
            if added < 20 and is_active:
                check_in = datetime.now() - timedelta(minutes=random.randint(5, 90))
                att = Attendance(
                    member_id=member.id,
                    attendance_date=today,
                    check_in_time=check_in,
                    check_out_time=None,
                )
                db.session.add(att)

            # ── Payment records for renewed members ────────────────────
            if category == 'renewed':
                renewal_count = random.randint(1, 4)
                payment_date = start + relativedelta(months=1)
                for _ in range(renewal_count):
                    if payment_date > today:
                        break
                    payment = Payment(
                        member_id=member.id,
                        amount=MEMBERSHIP_FEES[mtype],
                        payment_date=payment_date,
                        recorded_at=datetime.combine(payment_date, datetime.min.time()),
                        notes=f'{mtype.capitalize()} membership renewal',
                    )
                    db.session.add(payment)
                    payment_date += relativedelta(months=1)

            added += 1

        db.session.commit()

        # ── Summary ────────────────────────────────────────────────────
        total = Member.query.count()
        active = Member.query.filter_by(is_active=True).count()
        expired = Member.query.filter_by(is_active=False).count()
        expiring = Member.query.filter(
            Member.is_active == True,
            Member.membership_end >= today,
            Member.membership_end <= today + timedelta(days=7)
        ).count()
        att_total = Attendance.query.count()
        open_today = Attendance.query.filter_by(attendance_date=today, check_out_time=None).count()
        pay_total = Payment.query.count()

        print(f"\n── Demo data created ─────────────────────────────────")
        print(f"Members added:         {added}")
        print(f"Total members:         {total}")
        print(f"  Active:              {active}")
        print(f"  Expiring this week:  {expiring}")
        print(f"  Expired:             {expired}")
        print(f"Attendance records:    {att_total}")
        print(f"Checked in right now:  {open_today}")
        print(f"Payment records:       {pay_total}")
        print(f"\nReady for demo. Run start.bat to launch the kiosk.")


if __name__ == '__main__':
    app = create_app()
    clear_demo_data(app)
    seed_demo(app)

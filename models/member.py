from extensions import db
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class MembershipType:
    PERSONAL_TRAINER    = 'personal_trainer'
    SUPERVISED_STANDARD = 'supervised_standard'
    SUPERVISED_STUDENT  = 'supervised_student'
    REGULAR             = 'regular'
    STUDENT             = 'student'

    ALL = [
        'personal_trainer',
        'supervised_standard',
        'supervised_student',
        'regular',
        'student',
    ]

    LABELS = {
        'personal_trainer':    'Personal Trainer (1-on-1)',
        'supervised_standard': 'With Supervision – Standard',
        'supervised_student':  'With Supervision – Student',
        'regular':             'No Supervision – Standard',
        'student':             'No Supervision – Student',
    }


MEMBERSHIP_PRICES = {
    MembershipType.PERSONAL_TRAINER:    3800.00,
    MembershipType.SUPERVISED_STANDARD: 1650.00,
    MembershipType.SUPERVISED_STUDENT:  1350.00,
    MembershipType.REGULAR:              950.00,
    MembershipType.STUDENT:              650.00,
}


class Member(db.Model):
    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)
    membership_id = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    membership_type = db.Column(db.String(20), nullable=False, default=MembershipType.REGULAR)
    membership_start = db.Column(db.Date, nullable=False, default=date.today)
    membership_end = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    waiver_signed_at = db.Column(db.DateTime, nullable=True)
    waiver_name = db.Column(db.String(120), nullable=True)
    waiver_fb_username = db.Column(db.String(100), nullable=True)

    attendance_records = db.relationship('Attendance', backref='member', lazy=True)

    def get_monthly_fee(self):
        return MEMBERSHIP_PRICES.get(self.membership_type, MEMBERSHIP_PRICES[MembershipType.REGULAR])

    def get_type_label(self):
        return MembershipType.LABELS.get(self.membership_type, self.membership_type.replace('_', ' ').capitalize())

    GRACE_DAYS = 7

    def is_within_grace(self):
        """True if expired but still within the 7-day grace period."""
        today = date.today()
        return self.membership_end < today <= self.membership_end + relativedelta(days=self.GRACE_DAYS)

    def renew(self, from_today=False, keep_billing_day=False):
        """
        Renew membership by 1 month.

        - Active or within grace → extend from current end date.
        - Past grace, keep_billing_day=True → preserve billing day, next occurrence after today.
          e.g. expired Feb 28, today is May 29 → new end = June 28.
        - Past grace, from_today=True → start fresh from today.
        """
        today = date.today()
        if keep_billing_day:
            billing_day = self.membership_end.day
            try:
                candidate = today.replace(day=billing_day)
            except ValueError:
                candidate = (today + relativedelta(months=1)).replace(day=1)
            if candidate <= today:
                candidate += relativedelta(months=1)
            self.membership_end = candidate
        elif from_today:
            self.membership_end = today + relativedelta(months=1)
        else:
            base = self.membership_end if self.membership_end and self.membership_end >= today else today
            self.membership_end = base + relativedelta(months=1)
        self.membership_start = today
        self.is_active = True

    def check_expiry(self):
        """Mark membership inactive if expiry date has passed."""
        if self.membership_end and self.membership_end < date.today():
            self.is_active = False

    def days_remaining(self):
        if self.membership_end:
            delta = self.membership_end - date.today()
            return max(delta.days, 0)
        return 0

    def __repr__(self):
        return f'<Member {self.membership_id} - {self.full_name} ({self.membership_type})>'

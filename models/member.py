from extensions import db
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class MembershipType:
    REGULAR = 'regular'
    STUDENT = 'student'
    SENIOR = 'senior'

    ALL = [REGULAR, STUDENT, SENIOR]


MEMBERSHIP_PRICES = {
    MembershipType.REGULAR: 850.00,
    MembershipType.STUDENT: 650.00,
    MembershipType.SENIOR: 650.00,    # same as student rate
}


class Member(db.Model):
    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)
    membership_id = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    membership_type = db.Column(db.String(20), nullable=False, default=MembershipType.REGULAR)
    membership_start = db.Column(db.Date, nullable=False, default=date.today)
    membership_end = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendance_records = db.relationship('Attendance', backref='member', lazy=True)

    def get_monthly_fee(self):
        return MEMBERSHIP_PRICES.get(self.membership_type, MEMBERSHIP_PRICES[MembershipType.REGULAR])

    def renew(self):
        """Extend membership by 1 month from today or from current end date if still valid."""
        base = self.membership_end if self.membership_end and self.membership_end >= date.today() else date.today()
        self.membership_end = base + relativedelta(months=1)
        self.membership_start = date.today()
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

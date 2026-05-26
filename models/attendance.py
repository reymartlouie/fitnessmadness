from extensions import db
from datetime import datetime, date


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    check_out_time = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    attendance_date = db.Column(db.Date, nullable=False, default=date.today)

    def calculate_duration(self):
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            self.duration_minutes = int(delta.total_seconds() / 60)

    def is_active(self):
        return self.check_out_time is None

    def __repr__(self):
        return f'<Attendance member_id={self.member_id} date={self.attendance_date}>'

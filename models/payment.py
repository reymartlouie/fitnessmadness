from extensions import db
from datetime import datetime, date


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    recorded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.String(200), nullable=True)

    member = db.relationship('Member', backref='payments')

    def __repr__(self):
        return f'<Payment member_id={self.member_id} amount={self.amount} date={self.payment_date}>'

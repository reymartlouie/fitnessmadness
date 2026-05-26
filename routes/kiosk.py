from flask import Blueprint, render_template, request, flash, redirect, url_for
from extensions import db
from models.member import Member
from models.attendance import Attendance
from datetime import datetime, date

kiosk_bp = Blueprint('kiosk', __name__)


@kiosk_bp.route('/')
def index():
    return render_template('kiosk/index.html', member_records=None, looked_up_member=None)


@kiosk_bp.route('/my-records', methods=['POST'])
def my_records():
    membership_id = request.form.get('membership_id', '').strip()

    if not membership_id:
        flash('Please enter your membership ID.', 'danger')
        return render_template('kiosk/index.html', member_records=None, looked_up_member=None, active_tab='records')

    member = Member.query.filter_by(membership_id=membership_id).first()

    if not member:
        flash('Membership ID not found. Please see the front desk.', 'danger')
        return render_template('kiosk/index.html', member_records=None, looked_up_member=None, active_tab='records')

    records = Attendance.query.filter_by(
        member_id=member.id
    ).order_by(Attendance.check_in_time.desc()).limit(20).all()

    return render_template('kiosk/index.html',
        member_records=records,
        looked_up_member=member,
        active_tab='records'
    )


@kiosk_bp.route('/checkin', methods=['POST'])
def checkin():
    membership_id = request.form.get('membership_id', '').strip()
    full_name = request.form.get('full_name', '').strip()

    if not membership_id or not full_name:
        flash('Please enter both your name and membership ID.', 'danger')
        return redirect(url_for('kiosk.index'))

    member = Member.query.filter_by(membership_id=membership_id).first()

    if not member:
        flash('Membership ID not found. Please see the front desk.', 'danger')
        return redirect(url_for('kiosk.index'))

    if member.full_name.lower() != full_name.lower():
        flash('Name does not match our records. Please see the front desk.', 'danger')
        return redirect(url_for('kiosk.index'))

    member.check_expiry()
    db.session.commit()

    if not member.is_active:
        flash(f'Your membership has expired. Please renew at the front desk.', 'warning')
        return redirect(url_for('kiosk.index'))

    active_session = Attendance.query.filter_by(
        member_id=member.id,
        attendance_date=date.today()
    ).filter(Attendance.check_out_time == None).first()

    if active_session:
        flash(f'You are already checked in, {member.full_name}!', 'warning')
        return redirect(url_for('kiosk.index'))

    attendance = Attendance(
        member_id=member.id,
        check_in_time=datetime.now(),
        attendance_date=date.today()
    )
    db.session.add(attendance)
    db.session.commit()

    flash(f'Welcome, {member.full_name}! Check-in successful.', 'success')
    return redirect(url_for('kiosk.index'))


@kiosk_bp.route('/checkout', methods=['POST'])
def checkout():
    membership_id = request.form.get('membership_id', '').strip()

    if not membership_id:
        flash('Please enter your membership ID.', 'danger')
        return redirect(url_for('kiosk.index'))

    member = Member.query.filter_by(membership_id=membership_id).first()

    if not member:
        flash('Membership ID not found. Please see the front desk.', 'danger')
        return redirect(url_for('kiosk.index'))

    active_session = Attendance.query.filter_by(
        member_id=member.id,
        attendance_date=date.today()
    ).filter(Attendance.check_out_time == None).first()

    if not active_session:
        flash(f'No active check-in found for {member.full_name}.', 'warning')
        return redirect(url_for('kiosk.index'))

    active_session.check_out_time = datetime.now()
    active_session.calculate_duration()
    db.session.commit()

    duration = active_session.duration_minutes
    hours = duration // 60
    minutes = duration % 60

    if hours > 0:
        time_str = f'{hours}h {minutes}m'
    else:
        time_str = f'{minutes} minutes'

    flash(f'Goodbye, {member.full_name}! You trained for {time_str}. Great work!', 'success')
    return redirect(url_for('kiosk.index'))

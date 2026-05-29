import csv
import io
from flask import Blueprint, render_template, request, Response, redirect, url_for, flash
from flask_login import login_required
from models.member import Member, MembershipType, MEMBERSHIP_PRICES
from models.attendance import Attendance
from models.payment import Payment
from extensions import db
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    today = date.today()

    # Sync is_active for any member whose end date has passed but flag wasn't updated
    # (check_expiry only runs when a member tries to check in, so this catches the rest)
    stale_members = Member.query.filter(
        Member.membership_end < today,
        Member.is_active == True
    ).all()
    if stale_members:
        for m in stale_members:
            m.is_active = False
        db.session.commit()

    # Auto-close sessions from previous days that never got a check-out
    # (member left without using the kiosk). Close at 23:59 of that day.
    stale_sessions = Attendance.query.filter(
        Attendance.attendance_date < today,
        Attendance.check_out_time == None
    ).all()
    if stale_sessions:
        for s in stale_sessions:
            s.check_out_time = datetime.combine(s.attendance_date, time(23, 59, 0))
            s.calculate_duration()
        db.session.commit()

    total_checkins_today = Attendance.query.filter_by(attendance_date=today).count()

    active_members = Attendance.query.filter_by(
        attendance_date=today
    ).filter(Attendance.check_out_time == None).count()

    total_members = Member.query.count()
    expired_members = Member.query.filter_by(is_active=False).count()

    from datetime import timedelta
    alert_window = today + timedelta(days=7)
    expiring_soon = Member.query.filter(
        Member.is_active == True,
        Member.membership_end >= today,
        Member.membership_end <= alert_window
    ).order_by(Member.membership_end.asc()).all()

    recent_logs = Attendance.query.order_by(
        Attendance.check_in_time.desc()
    ).limit(10).all()

    return render_template('admin/dashboard.html',
        total_checkins_today=total_checkins_today,
        active_members=active_members,
        total_members=total_members,
        expired_members=expired_members,
        expiring_soon=expiring_soon,
        recent_logs=recent_logs,
        today=today
    )


@admin_bp.route('/members/export')
@login_required
def export_members_csv():
    search = request.args.get('search', '').strip()
    filter_type = request.args.get('type', '').strip()
    filter_status = request.args.get('status', '').strip()

    query = Member.query
    if search:
        query = query.filter(
            (Member.full_name.ilike(f'%{search}%')) |
            (Member.membership_id.ilike(f'%{search}%'))
        )
    if filter_type and filter_type in MembershipType.ALL:
        query = query.filter_by(membership_type=filter_type)
    if filter_status == 'active':
        query = query.filter_by(is_active=True)
    elif filter_status == 'expired':
        query = query.filter_by(is_active=False)

    all_members = query.order_by(Member.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Membership ID', 'Full Name', 'Phone', 'Email',
        'Type', 'Monthly Fee', 'Start Date', 'Expiry Date',
        'Days Remaining', 'Status'
    ])
    for m in all_members:
        writer.writerow([
            m.membership_id,
            m.full_name,
            m.phone or '',
            m.email or '',
            m.membership_type.capitalize(),
            f'{m.get_monthly_fee():.2f}',
            m.membership_start.strftime('%Y-%m-%d'),
            m.membership_end.strftime('%Y-%m-%d'),
            m.days_remaining(),
            'Active' if m.is_active else 'Expired',
        ])

    output.seek(0)
    filename = f"members_{date.today().strftime('%Y-%m-%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@admin_bp.route('/attendance')
@login_required
def attendance():
    search_name = request.args.get('name', '').strip()
    search_id = request.args.get('membership_id', '').strip()
    filter_date = request.args.get('date', '').strip()

    query = Attendance.query.join(Member)

    if search_name:
        query = query.filter(Member.full_name.ilike(f'%{search_name}%'))
    if search_id:
        query = query.filter(Member.membership_id.ilike(f'%{search_id}%'))
    if filter_date:
        try:
            parsed_date = datetime.strptime(filter_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.attendance_date == parsed_date)
        except ValueError:
            pass

    logs = query.order_by(Attendance.check_in_time.desc()).all()

    return render_template('admin/attendance.html',
        logs=logs,
        search_name=search_name,
        search_id=search_id,
        filter_date=filter_date
    )


@admin_bp.route('/attendance/export')
@login_required
def export_csv():
    search_name = request.args.get('name', '').strip()
    search_id = request.args.get('membership_id', '').strip()
    filter_date = request.args.get('date', '').strip()

    query = Attendance.query.join(Member)

    if search_name:
        query = query.filter(Member.full_name.ilike(f'%{search_name}%'))
    if search_id:
        query = query.filter(Member.membership_id.ilike(f'%{search_id}%'))
    if filter_date:
        try:
            parsed_date = datetime.strptime(filter_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.attendance_date == parsed_date)
        except ValueError:
            pass

    logs = query.order_by(Attendance.check_in_time.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Member Name', 'Membership ID', 'Date', 'Check In', 'Check Out', 'Duration (mins)'])

    for log in logs:
        writer.writerow([
            log.member.full_name,
            log.member.membership_id,
            log.attendance_date.strftime('%Y-%m-%d'),
            log.check_in_time.strftime('%I:%M %p'),
            log.check_out_time.strftime('%I:%M %p') if log.check_out_time else '',
            log.duration_minutes if log.duration_minutes else ''
        ])

    output.seek(0)
    filename = f"attendance_{date.today().strftime('%Y-%m-%d')}.csv"

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@admin_bp.route('/members')
@login_required
def members():
    search = request.args.get('search', '').strip()
    filter_type = request.args.get('type', '').strip()
    filter_status = request.args.get('status', '').strip()

    query = Member.query

    if search:
        query = query.filter(
            (Member.full_name.ilike(f'%{search}%')) |
            (Member.membership_id.ilike(f'%{search}%'))
        )
    if filter_type and filter_type in MembershipType.ALL:
        query = query.filter_by(membership_type=filter_type)
    if filter_status == 'active':
        query = query.filter_by(is_active=True)
    elif filter_status == 'expired':
        query = query.filter_by(is_active=False)

    all_members = query.order_by(Member.created_at.desc()).all()

    return render_template('admin/members.html',
        members=all_members,
        search=search,
        filter_type=filter_type,
        filter_status=filter_status,
        membership_types=MembershipType.ALL,
        prices=MEMBERSHIP_PRICES
    )


@admin_bp.route('/members/add', methods=['GET', 'POST'])
@login_required
def add_member():
    if request.method == 'POST':
        membership_id = request.form.get('membership_id', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        membership_type = request.form.get('membership_type', MembershipType.REGULAR)

        if not membership_id or not full_name:
            flash('Membership ID and full name are required.', 'danger')
            return render_template('admin/member_form.html',
                action='add', membership_types=MembershipType.ALL, prices=MEMBERSHIP_PRICES)

        if Member.query.filter_by(membership_id=membership_id).first():
            flash(f'Membership ID "{membership_id}" is already taken.', 'danger')
            return render_template('admin/member_form.html',
                action='add', membership_types=MembershipType.ALL, prices=MEMBERSHIP_PRICES)

        member = Member(
            membership_id=membership_id,
            full_name=full_name,
            phone=phone or None,
            email=email or None,
            membership_type=membership_type,
            membership_start=date.today(),
            membership_end=date.today() + relativedelta(months=1),
            is_active=True
        )
        db.session.add(member)
        db.session.commit()
        flash(f'Member "{full_name}" added successfully.', 'success')
        return redirect(url_for('admin.members'))

    return render_template('admin/member_form.html',
        action='add', membership_types=MembershipType.ALL, prices=MEMBERSHIP_PRICES)


@admin_bp.route('/members/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_member(member_id):
    member = Member.query.get_or_404(member_id)

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        membership_type = request.form.get('membership_type', member.membership_type)

        if not full_name:
            flash('Full name is required.', 'danger')
            return render_template('admin/member_form.html',
                action='edit', member=member,
                membership_types=MembershipType.ALL, prices=MEMBERSHIP_PRICES)

        member.full_name = full_name
        member.phone = phone or None
        member.email = email or None
        member.membership_type = membership_type
        db.session.commit()
        flash(f'Member "{full_name}" updated successfully.', 'success')
        return redirect(url_for('admin.members'))

    return render_template('admin/member_form.html',
        action='edit', member=member,
        membership_types=MembershipType.ALL, prices=MEMBERSHIP_PRICES)


@admin_bp.route('/members/<int:member_id>/renew', methods=['GET', 'POST'])
@login_required
def renew_member(member_id):
    member = Member.query.get_or_404(member_id)
    today = date.today()
    past_grace = member.membership_end < today - relativedelta(days=member.GRACE_DAYS)

    if past_grace and 'from_today' not in request.form:
        # Calculate next billing date (keeps billing day, next occurrence after today)
        billing_day = member.membership_end.day
        try:
            next_billing = today.replace(day=billing_day)
        except ValueError:
            next_billing = (today + relativedelta(months=1)).replace(day=1)
        if next_billing <= today:
            next_billing += relativedelta(months=1)
        return render_template('admin/renew_confirm.html', member=member,
                               today=today, next_billing=next_billing,
                               relativedelta=relativedelta)

    from_today = request.form.get('from_today') == '1'
    keep_billing_day = past_grace and not from_today
    amount = member.get_monthly_fee()
    member.renew(from_today=from_today, keep_billing_day=keep_billing_day)
    payment = Payment(
        member_id=member.id,
        amount=amount,
        payment_date=today,
        recorded_at=datetime.now(),
        notes=f'{member.membership_type.capitalize()} membership renewal'
    )
    db.session.add(payment)
    db.session.commit()
    flash(
        f'Membership for "{member.full_name}" renewed until '
        f'{member.membership_end.strftime("%B %d, %Y")}. '
        f'Payment of ₱{amount:,.2f} recorded.',
        'success'
    )
    return redirect(url_for('admin.members'))


@admin_bp.route('/payments')
@login_required
def payments():
    search = request.args.get('search', '').strip()
    filter_date = request.args.get('date', '').strip()

    query = Payment.query.join(Member)
    if search:
        query = query.filter(
            (Member.full_name.ilike(f'%{search}%')) |
            (Member.membership_id.ilike(f'%{search}%'))
        )
    if filter_date:
        try:
            parsed = datetime.strptime(filter_date, '%Y-%m-%d').date()
            query = query.filter(Payment.payment_date == parsed)
        except ValueError:
            pass

    logs = query.order_by(Payment.recorded_at.desc()).all()
    total = sum(p.amount for p in logs)

    return render_template('admin/payments.html',
        logs=logs, total=total,
        search=search, filter_date=filter_date)


@admin_bp.route('/payments/export')
@login_required
def export_payments_csv():
    logs = Payment.query.join(Member).order_by(Payment.recorded_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Member Name', 'Membership ID', 'Type', 'Amount (PHP)', 'Notes'])
    for p in logs:
        writer.writerow([
            p.payment_date.strftime('%Y-%m-%d'),
            p.member.full_name,
            p.member.membership_id,
            p.member.membership_type.capitalize(),
            f'{p.amount:.2f}',
            p.notes or '',
        ])

    output.seek(0)
    filename = f"payments_{date.today().strftime('%Y-%m-%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@admin_bp.route('/members/<int:member_id>/delete-confirm', methods=['GET'])
@login_required
def delete_member_confirm(member_id):
    member = Member.query.get_or_404(member_id)
    return render_template('admin/delete_confirm.html', member=member)


@admin_bp.route('/members/<int:member_id>/delete', methods=['POST'])
@login_required
def delete_member(member_id):
    member = Member.query.get_or_404(member_id)
    confirm_id = request.form.get('confirm_id', '').strip()

    if confirm_id != member.membership_id:
        flash('Membership ID did not match. Deletion cancelled.', 'danger')
        return redirect(url_for('admin.delete_member_confirm', member_id=member_id))

    name = member.full_name
    Attendance.query.filter_by(member_id=member.id).delete()
    Payment.query.filter_by(member_id=member.id).delete()
    db.session.delete(member)
    db.session.commit()
    flash(f'Member "{name}" and all their attendance records have been permanently deleted.', 'warning')
    return redirect(url_for('admin.members'))

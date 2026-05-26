import csv
import io
from flask import Blueprint, render_template, request, Response, redirect, url_for, flash
from flask_login import login_required
from models.member import Member, MembershipType, MEMBERSHIP_PRICES
from models.attendance import Attendance
from extensions import db
from datetime import date, datetime
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

    total_checkins_today = Attendance.query.filter_by(attendance_date=today).count()

    active_members = Attendance.query.filter_by(
        attendance_date=today
    ).filter(Attendance.check_out_time == None).count()

    total_members = Member.query.count()
    expired_members = Member.query.filter_by(is_active=False).count()

    recent_logs = Attendance.query.order_by(
        Attendance.check_in_time.desc()
    ).limit(10).all()

    return render_template('admin/dashboard.html',
        total_checkins_today=total_checkins_today,
        active_members=active_members,
        total_members=total_members,
        expired_members=expired_members,
        recent_logs=recent_logs,
        today=today
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
        membership_type = request.form.get('membership_type', member.membership_type)

        if not full_name:
            flash('Full name is required.', 'danger')
            return render_template('admin/member_form.html',
                action='edit', member=member,
                membership_types=MembershipType.ALL, prices=MEMBERSHIP_PRICES)

        member.full_name = full_name
        member.membership_type = membership_type
        db.session.commit()
        flash(f'Member "{full_name}" updated successfully.', 'success')
        return redirect(url_for('admin.members'))

    return render_template('admin/member_form.html',
        action='edit', member=member,
        membership_types=MembershipType.ALL, prices=MEMBERSHIP_PRICES)


@admin_bp.route('/members/<int:member_id>/renew', methods=['POST'])
@login_required
def renew_member(member_id):
    member = Member.query.get_or_404(member_id)
    member.renew()
    db.session.commit()
    flash(f'Membership for "{member.full_name}" renewed until {member.membership_end.strftime("%B %d, %Y")}.', 'success')
    return redirect(url_for('admin.members'))


@admin_bp.route('/members/<int:member_id>/delete', methods=['POST'])
@login_required
def delete_member(member_id):
    member = Member.query.get_or_404(member_id)
    name = member.full_name
    Attendance.query.filter_by(member_id=member.id).delete()
    db.session.delete(member)
    db.session.commit()
    flash(f'Member "{name}" and all their attendance records have been deleted.', 'warning')
    return redirect(url_for('admin.members'))

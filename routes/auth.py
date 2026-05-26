from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models.admin import Admin
from extensions import limiter

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('admin/login.html')

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            login_user(admin)
            session.permanent = True
            next_page = request.args.get('next')
            if next_page and not next_page.startswith('/'):
                next_page = None
            flash(f'Welcome back, {admin.username}!', 'success')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('admin/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

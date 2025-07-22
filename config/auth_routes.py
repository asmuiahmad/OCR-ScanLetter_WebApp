"""
Authentication routes
Handles login, logout, registration, and user management
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from config.extensions import db
from config.models import User
from config.forms import LoginForm, RegistrationForm
from config.route_utils import log_user_login, log_user_logout

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and form.password.data and check_password_hash(user.password, form.password.data):
            if not user.is_approved:
                flash('Your account is pending approval by an administrator.', 'warning')
                # Log failed login attempt due to unapproved account
                log_user_login(user.id, user.email, 'blocked', request)
                return render_template('auth/login.html', form=form)
            
            user.last_login = datetime.now()
            if user.login_count is None:
                user.login_count = 0
            user.login_count += 1
            db.session.commit()
            login_user(user)
            
            # Log successful login
            log_user_login(user.id, user.email, 'success', request)
            
            return redirect(url_for('dashboard.dashboard'))
        else:
            # Log failed login attempt
            if user:
                log_user_login(user.id, form.email.data, 'failed', request)
            else:
                log_user_login(None, form.email.data, 'failed', request)
            flash('Invalid email or password', 'error')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    # Log the logout
    user_id = current_user.id if current_user.is_authenticated else None
    if user_id:
        log_user_logout(user_id)
    
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email already registered. Please use a different email or login.', 'error')
                return render_template('auth/register.html', form=form)
            
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            new_user = User(
                email=form.email.data, 
                password=hashed_password,
                role=form.role.data,
                is_approved=False
            )
            
            if form.role.data == 'admin':
                new_user.is_admin = True
            
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Your account is pending approval by an administrator.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error: {str(e)}')
            flash(f'An error occurred during registration. Please try again.', 'error')
    elif form.errors:
        current_app.logger.warning(f'Registration form validation errors: {form.errors}')
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return render_template('auth/register.html', form=form)
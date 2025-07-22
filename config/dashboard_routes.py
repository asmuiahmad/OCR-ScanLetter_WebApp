"""
Dashboard routes
Main dashboard and overview functionality
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, g, current_app
from flask_login import login_required, current_user
from sqlalchemy import extract

from config.extensions import db
from config.models import User, SuratKeluar, SuratMasuk
from config.route_utils import role_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.before_app_request
def set_pending_surat_counts():
    """Set pending surat counts for navigation"""
    g.pending_surat_masuk_count = 0
    
    try:
        if current_user.is_authenticated:
            if current_user.role in ['pimpinan', 'admin']:
                g.pending_surat_masuk_count = SuratMasuk.query.filter_by(status_suratMasuk='pending').count()
                current_app.logger.debug(f"Pending count for {current_user.email}: {g.pending_surat_masuk_count}")
    except Exception as e:
        current_app.logger.warning(f"Error in set_pending_surat_counts: {str(e)}")
        g.pending_surat_masuk_count = 0


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    suratKeluar_count = SuratKeluar.query.count()
    suratMasuk_count = SuratMasuk.query.count()

    today = datetime.now()
    year = today.year
    month = today.month
    week_start = today - timedelta(days=today.weekday())

    suratKeluar_this_year = SuratKeluar.query.filter(
        extract('year', SuratKeluar.tanggal_suratKeluar) == year
    ).count()
    suratMasuk_this_year = SuratMasuk.query.filter(
        extract('year', SuratMasuk.tanggal_suratMasuk) == year
    ).count()

    suratKeluar_this_month = SuratKeluar.query.filter(
        extract('year', SuratKeluar.tanggal_suratKeluar) == year,
        extract('month', SuratKeluar.tanggal_suratKeluar) == month
    ).count()
    suratMasuk_this_month = SuratMasuk.query.filter(
        extract('year', SuratMasuk.tanggal_suratMasuk) == year,
        extract('month', SuratMasuk.tanggal_suratMasuk) == month
    ).count()

    suratKeluar_this_week = SuratKeluar.query.filter(
        SuratKeluar.tanggal_suratKeluar >= week_start
    ).count()
    suratMasuk_this_week = SuratMasuk.query.filter(
        SuratMasuk.tanggal_suratMasuk >= week_start
    ).count()

    recent_surat_keluar = SuratKeluar.query.order_by(SuratKeluar.tanggal_suratKeluar.desc()).limit(5).all()
    recent_surat_masuk = SuratMasuk.query.order_by(SuratMasuk.tanggal_suratMasuk.desc()).limit(5).all()

    users = User.query.order_by(User.last_login.desc()).limit(5).all()

    return render_template(
        'dashboard/index.html', 
        suratKeluar_count=suratKeluar_count,
        suratMasuk_count=suratMasuk_count,
        suratKeluar_this_year=suratKeluar_this_year,
        suratMasuk_this_year=suratMasuk_this_year,
        suratKeluar_this_month=suratKeluar_this_month,
        suratMasuk_this_month=suratMasuk_this_month,
        suratKeluar_this_week=suratKeluar_this_week,
        suratMasuk_this_week=suratMasuk_this_week,
        recent_surat_keluar=recent_surat_keluar,
        recent_surat_masuk=recent_surat_masuk,
        users=users
    )


@dashboard_bp.route('/users', methods=['GET'])
@login_required
def user_list():
    """List all users"""
    users = User.query.all()
    return render_template('auth/user_list.html', users=users)


@dashboard_bp.route('/last-logins', methods=['GET'])
def last_logins():
    """Get last login information"""
    users = User.query.order_by(User.last_login.desc()).limit(10).all()
    result = [{"username": user.email, "last_login": user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'} for user in users]
    return jsonify(result)
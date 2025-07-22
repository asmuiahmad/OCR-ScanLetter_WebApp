"""
Main routes file
Imports and registers all route blueprints
"""

from flask import Blueprint
from flask import render_template, redirect, url_for
from flask_login import current_user

# Import all blueprints
from config.auth_routes import auth_bp
from config.dashboard_routes import dashboard_bp
from config.api_routes import api_bp
from config.surat_routes import surat_bp
from config.surat_masuk_routes import surat_masuk_bp
from config.surat_keluar_routes import surat_keluar_bp
from config.pegawai_routes import pegawai_bp
from config.user_routes import user_bp
from config.cuti_routes import cuti_bp
from config.ocr_routes import ocr_routes_bp
from config.laporan_routes import laporan_bp

# Create main blueprint
main_bp = Blueprint('main', __name__)

# Register all blueprints with the main blueprint
def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(auth_bp)  # Register auth first
    app.register_blueprint(dashboard_bp)  # Register dashboard second
    app.register_blueprint(main_bp)  # Register main third
    app.register_blueprint(api_bp)
    app.register_blueprint(surat_bp)
    app.register_blueprint(surat_masuk_bp)
    app.register_blueprint(surat_keluar_bp)
    app.register_blueprint(pegawai_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(cuti_bp)
    app.register_blueprint(ocr_routes_bp)
    app.register_blueprint(laporan_bp)
    
    # Import remaining routes that haven't been moved yet
    from config.remaining_routes import remaining_bp
    app.register_blueprint(remaining_bp)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    else:
        return redirect(url_for('auth.login'))
from flask import Flask, render_template, request
from config.extensions import db, login_manager
from flask_migrate import Migrate
from datetime import timedelta
from config.models import User
from config.ocr import ocr_bp
from config.ocr_surat_masuk import ocr_surat_masuk_bp 
from config.ocr_surat_keluar import ocr_surat_keluar_bp
from config.breadcrumbs import generate_breadcrumbs
import os

# Konfigurasi direktori instance
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)

app = Flask(__name__, instance_path=instance_path)

# Konfigurasi database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Ganti dengan kunci rahasia yang kuat
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Initialize Extensions
db.init_app(app)
migrate = Migrate(app, db)

login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Register Blueprints
app.register_blueprint(ocr_bp, url_prefix='/ocr')
app.register_blueprint(ocr_surat_masuk_bp, url_prefix='/ocr_surat_masuk')
app.register_blueprint(ocr_surat_keluar_bp, url_prefix='/ocr_surat_keluar')

# Import the auth blueprint
from config.routes import auth_bp

# Register the auth blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')

# User Loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add breadcrumb context processor
@app.context_processor
def inject_breadcrumbs():
    """Inject breadcrumbs into all templates"""
    endpoint = request.endpoint
    view_args = request.view_args or {}
    breadcrumbs = generate_breadcrumbs(endpoint, **view_args)
    return dict(breadcrumbs=breadcrumbs)

# Add utilities to Jinja2
app.jinja_env.globals['zip'] = zip
app.jinja_env.globals.update(max=max, min=min)

# Pastikan direktori instance ada
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Buat database jika belum ada
with app.app_context():
    db.create_all()

from config.routes import *

if __name__ == '__main__':
    app.run(debug=True)

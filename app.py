from flask import Flask, render_template
from config.extensions import db, login_manager
from flask_migrate import Migrate
from datetime import timedelta
from config.models import User
from config.ocr import ocr_bp  # Import the OCR Blueprint
from config.ocr_surat_masuk import ocr_surat_masuk_bp  # Import the Surat Masuk OCR Blueprint
from config.ocr_surat_keluar import ocr_surat_keluar_bp  # Import the 

app = Flask(__name__)

# App Configuration
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Initialize Extensions
db.init_app(app)
migrate = Migrate(app, db)

login_manager.init_app(app)
login_manager.login_view = 'login'

# Register Blueprints
app.register_blueprint(ocr_bp, url_prefix='/ocr')
app.register_blueprint(ocr_surat_masuk_bp, url_prefix='/ocr_surat_masuk')
app.register_blueprint(ocr_surat_keluar_bp, url_prefix='/ocr_surat_keluar')

# User Loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add utilities to Jinja2
app.jinja_env.globals['zip'] = zip
app.jinja_env.globals.update(max=max, min=min)

from config.routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

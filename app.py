from flask import Flask
from config.extensions import db, login_manager
from flask_migrate import Migrate
from datetime import timedelta
from config.models import User, SuratMasuk, SuratKeluar
from config.forms import RegistrationForm, LoginForm
from jinja2 import Environment, select_autoescape
from config.ocr import ocr_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

db.init_app(app)
migrate = Migrate(app, db)

login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.jinja_env.globals.update(max=max, min=min)

from config.routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

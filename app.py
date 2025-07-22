from flask import Flask, render_template, request, session
from config.extensions import db, login_manager, csrf
from flask_migrate import Migrate
from datetime import timedelta
from config.models import User, UserLoginLog
import os
from flask_wtf.csrf import generate_csrf
from werkzeug.exceptions import HTTPException
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)
def create_app():
    app = Flask(__name__, instance_path=instance_path)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
    app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

    db.init_app(app)
    
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    from config.ocr import ocr_bp
    from config.ocr_surat_keluar import ocr_surat_keluar_bp
    from config.ocr_surat_masuk import ocr_surat_masuk_bp
    from config.ocr_cuti import ocr_cuti_bp
    from config.routes_user_login_logs import user_login_logs_bp
    from config.routes_main import register_blueprints
    
    # Register OCR blueprints
    app.register_blueprint(ocr_bp, url_prefix='/ocr')
    app.register_blueprint(ocr_cuti_bp, url_prefix='/cuti')
    app.register_blueprint(ocr_surat_masuk_bp, url_prefix='/surat-masuk')
    app.register_blueprint(ocr_surat_keluar_bp, url_prefix='/surat-keluar')
    app.register_blueprint(user_login_logs_bp)
    
    # Register all other blueprints
    register_blueprints(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.after_request
    def inject_csrf_token(response):
        if 'text/html' in response.headers.get('Content-Type', ''):
            csrf_token = generate_csrf()
            response.set_cookie('csrf_token', csrf_token)
            logger.debug(f"Generated CSRF Token: {csrf_token}")
        return response

    @app.errorhandler(400)
    def handle_bad_request(e):
        logger.error(f"Bad Request Error: {str(e)}")
        if 'csrf_token' in str(e):
            return render_template('error.html', error_message='CSRF token is missing or invalid. Please refresh the page and try again.'), 400
        return render_template('error.html', error_message='Bad Request'), 400

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {str(e)}")
        if isinstance(e, HTTPException):
            if e.code == 400 and 'csrf_token' in str(e):
                return render_template('error.html', error_message='CSRF token is missing or invalid. Please refresh the page and try again.'), 400
            return render_template('error.html', error_message=f'Error {e.code}: {e.name} - {e.description}'), e.code
        return render_template('error.html', error_message='An unexpected error occurred. Please try again later.'), 500

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        try:
            from config.extensions import db
            db.session.rollback()
        except Exception:
            pass
        return render_template('500.html'), 500

    with app.app_context():
        db.create_all()

        from config.breadcrumbs import register_breadcrumbs
        register_breadcrumbs(app)

    return app
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5001)

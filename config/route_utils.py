"""
Route utilities and decorators
Common functions used across different route modules
"""

import math
from functools import wraps
from datetime import datetime, timezone, timedelta

from flask import jsonify, request
from flask_login import current_user

from config.extensions import db
from config.models import UserLoginLog


def role_required(*roles):
    """Decorator to require specific roles for route access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                return jsonify({"error": "Unauthorized"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_user_login(user_id, user_email, status='success', request=None):
    """Log user login activity"""
    try:
        log_data = {
            'user_id': user_id,
            'user_email': user_email,
            'status': status,
            'login_time': datetime.utcnow()
        }
        
        if request:
            log_data['ip_address'] = request.remote_addr
            log_data['user_agent'] = request.headers.get('User-Agent', '')
            
            # Simple user agent parsing
            ua = request.headers.get('User-Agent', '')
            if 'Mobile' in ua or 'Android' in ua or 'iPhone' in ua:
                log_data['device_type'] = 'mobile'
            elif 'Tablet' in ua or 'iPad' in ua:
                log_data['device_type'] = 'tablet'
            else:
                log_data['device_type'] = 'desktop'
                
            if 'Chrome' in ua:
                log_data['browser_info'] = 'Chrome'
            elif 'Firefox' in ua:
                log_data['browser_info'] = 'Firefox'
            elif 'Safari' in ua:
                log_data['browser_info'] = 'Safari'
            else:
                log_data['browser_info'] = 'Other'
        
        login_log = UserLoginLog(**log_data)
        db.session.add(login_log)
        db.session.commit()
        return login_log
    except Exception as e:
        print(f"Error logging login: {str(e)}")
        db.session.rollback()
        return None


def log_user_logout(user_id):
    """Log user logout activity"""
    try:
        # Find most recent login without logout
        recent_login = UserLoginLog.query.filter_by(
            user_id=user_id,
            status='success'
        ).filter(
            UserLoginLog.logout_time.is_(None)
        ).order_by(
            UserLoginLog.login_time.desc()
        ).first()
        
        if recent_login:
            logout_time = datetime.utcnow()
            recent_login.logout_time = logout_time
            # Calculate session duration
            if recent_login.login_time:
                duration = (logout_time - recent_login.login_time).total_seconds()
                recent_login.session_duration = int(duration)
            db.session.commit()
            return recent_login
    except Exception as e:
        print(f"Error logging logout: {str(e)}")
        db.session.rollback()
        return None
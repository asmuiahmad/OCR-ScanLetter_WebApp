"""
Route utilities and decorators
Common functions used across different route modules
"""

import math
from datetime import datetime, timedelta, timezone
import threading
from functools import wraps

from flask import jsonify, request
from flask_login import current_user

from config.extensions import db
from config.models import UserLoginLog


def role_required(*roles):
    """Decorator to require specific roles for route access (case-insensitive)

    This decorator normalizes both the allowed roles and the current user's role
    to lowercase before comparison so role strings like 'Pimpinan' or 'pimpinan'
    are treated equivalently.

    Behavior change:
    - If the request looks like an AJAX/SPA request (Accept includes JSON or
      X-Requested-With == XMLHttpRequest or request.is_json), return a JSON
      403 response so the client-side SPA can handle it gracefully.
    - Otherwise (regular browser navigation), perform a flash + redirect to the
      login page to preserve the standard UX for interactive pages.
    """
    # Normalize allowed roles to lowercase for case-insensitive comparison
    allowed_roles = {r.lower() for r in roles}

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = getattr(current_user, "role", None)

            # If not authenticated or role absent/mismatch -> deny
            if (
                not current_user.is_authenticated
                or not user_role
                or user_role.lower() not in allowed_roles
            ):
                # Heuristics to detect AJAX/SPA/JSON requests:
                accept = request.headers.get("Accept", "") or ""
                xreq = request.headers.get("X-Requested-With", "") or ""
                wants_json = (
                    xreq == "XMLHttpRequest"
                    or "application/json" in accept.lower()
                    or request.is_json
                )

                if wants_json:
                    # Return JSON so SPA/fetch clients receive a proper 403 response
                    return jsonify(
                        {"error": "Unauthorized", "reason": "role_mismatch"}
                    ), 403
                else:
                    # Browser navigation: redirect to login (or show forbidden)
                    from flask import flash, redirect, url_for

                    flash(
                        "Anda tidak memiliki izin untuk mengakses halaman ini.", "error"
                    )
                    # Redirect to login to allow re-auth or proper messaging
                    return redirect(url_for("auth.login"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def log_user_login(user_id, user_email, status="success", request_obj=None):
    """Log user login activity (synchronous with error handling)"""
    try:
        log_data = {
            "user_id": user_id,
            "user_email": user_email,
            "status": status,
            "login_time": datetime.utcnow(),
        }

        if request_obj:
            log_data["ip_address"] = request_obj.remote_addr
            log_data["user_agent"] = request_obj.headers.get("User-Agent", "")

            # Simple user agent parsing
            ua = request_obj.headers.get("User-Agent", "")
            if "Mobile" in ua or "Android" in ua or "iPhone" in ua:
                log_data["device_type"] = "mobile"
            elif "Tablet" in ua or "iPad" in ua:
                log_data["device_type"] = "tablet"
            else:
                log_data["device_type"] = "desktop"

            if "Chrome" in ua:
                log_data["browser_info"] = "Chrome"
            elif "Firefox" in ua:
                log_data["browser_info"] = "Firefox"
            elif "Safari" in ua:
                log_data["browser_info"] = "Safari"
            else:
                log_data["browser_info"] = "Other"

        login_log = UserLoginLog(**log_data)
        db.session.add(login_log)
        db.session.commit()
        return login_log
    except Exception as e:
        print(f"Error logging login: {str(e)}")
        db.session.rollback()
        # Don't raise exception, just log it
        return None


def _log_user_login_async(user_id, user_email, status="success", request_obj=None):
    """Async logging function (runs in background thread) - DEPRECATED"""
    # This function is deprecated and replaced with synchronous logging
    pass


def log_user_logout(user_id):
    """Log user logout activity"""
    try:
        # Find most recent login without logout
        recent_login = (
            UserLoginLog.query.filter_by(user_id=user_id, status="success")
            .filter(UserLoginLog.logout_time.is_(None))
            .order_by(UserLoginLog.login_time.desc())
            .first()
        )

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

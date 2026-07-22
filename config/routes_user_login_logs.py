# Flask Routes for User Login Logs API
# Add these routes to your main Flask application

from flask import request, jsonify, Blueprint
from datetime import datetime, timedelta
import math
from config.extensions import db
from config.models import UserLoginLog

# Create a blueprint for user login logs
user_login_logs_bp = Blueprint('user_login_logs', __name__)

# Hapus atau ubah route '/' agar tidak menangani root path
# @user_login_logs_bp.route('/', methods=['GET'])
@user_login_logs_bp.route('/user-login-logs', methods=['GET'])
def get_user_login_logs():
    """
    Get user login logs with pagination and filtering
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    - date: Filter by date (YYYY-MM-DD format)
    - user: Filter by user email (partial match)
    - status: Filter by status (success, failed, blocked)
    - user_id: Filter by specific user ID
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        date_filter = request.args.get('date')
        user_filter = request.args.get('user')
        status_filter = request.args.get('status')
        user_id_filter = request.args.get('user_id', type=int)
        
        # Build query
        query = UserLoginLog.query
        
        # Apply filters
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter(db.func.date(UserLoginLog.login_time) == filter_date)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
        
        if user_filter:
            query = query.filter(UserLoginLog.user_email.ilike(f'%{user_filter}%'))
        
        if status_filter:
            query = query.filter(UserLoginLog.status == status_filter)
        
        if user_id_filter:
            query = query.filter(UserLoginLog.user_id == user_id_filter)
        
        # Order by most recent first
        query = query.order_by(UserLoginLog.login_time.desc())
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        logs = query.offset(offset).limit(per_page).all()
        
        # Format logs for frontend
        logs_data = [log.to_dict() for log in logs]
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
        
        pagination_info = {
            'current_page': page,
            'total_pages': total_pages,
            'total': total_count,
            'showing': len(logs_data),
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'per_page': per_page
        }
        
        return jsonify({
            'success': True,
            'logs': logs_data,
            'pagination': pagination_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading login logs: {str(e)}'
        }), 500
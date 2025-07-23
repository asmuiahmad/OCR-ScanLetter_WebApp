from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from config.extensions import db
from config.models import User
from config.route_utils import role_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin and current_user.id != user_id:
        flash('You do not have permission to edit this user.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.email = request.form['email']
        new_password = request.form['password']
        if new_password:
            user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('User updated successfully!')
        return redirect(url_for('main.index'))

    return render_template('auth/edit_users.html', users=[user], single_user=True)

@user_bp.route('/edit-user', methods=['GET', 'POST'])
@login_required
def edit_user_view():
    try:
        if not current_user.is_admin:
            flash('You do not have permission to edit users.', 'error')
            return redirect(url_for('main.index'))
        
        users = User.query.all()

        if request.method == 'POST':
            user_id = request.form.get('user_id')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role')
            is_approved = 'is_approved' in request.form

            if not user_id:
                flash('Please select a user to edit.', 'error')
                return redirect(url_for('user.edit_user_view'))

            user = User.query.get(user_id)
            if user:
                user.email = email
                user.role = role
                user.is_approved = is_approved
                
                user.is_admin = (role == 'admin')
                
                if password:
                    user.set_password(password)
                
                db.session.commit()
                current_app.logger.info(f"User {user.email} updated by {current_user.email}")
                flash('User updated successfully!', 'success')
            else:
                flash('User not found.', 'error')

            return redirect(url_for('user.edit_user_view'))

        return render_template('auth/edit_users.html', users=users)
    except Exception as e:
        current_app.logger.error(f"Error in edit_user_view: {str(e)}")
        flash('An error occurred while loading the user management page.', 'error')
        return redirect(url_for('main.index'))

@user_bp.route('/get-user-data/<int:user_id>')
@login_required
def get_user_data(user_id):
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    user = User.query.get(user_id)
    if user:
        return jsonify({
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "is_approved": user.is_approved
            }
        })
    else:
        return jsonify({"success": False}), 404

@user_bp.route('/approve-user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    try:
        user = User.query.get(user_id)
        if user:
            user.is_approved = True
            db.session.commit()
            current_app.logger.info(f"User {user.email} approved by {current_user.email}")
            return jsonify({"success": True, "message": f"User {user.email} has been approved"})
        else:
            return jsonify({"success": False, "message": "User not found"}), 404
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving user {user_id}: {str(e)}")
        return jsonify({"success": False, "message": f"Error approving user: {str(e)}"}), 500

@user_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete user account"""
    if not current_user.is_admin:
        flash('You do not have permission to delete users.', 'error')
        return redirect(url_for('main.index'))
    
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('user.edit_user_view'))
    
    try:
        user = User.query.get(user_id)
        if user:
            user_email = user.email
            db.session.delete(user)
            db.session.commit()
            current_app.logger.info(f"User {user_email} deleted by {current_user.email}")
            flash(f'User {user_email} has been deleted successfully.', 'success')
        else:
            flash('User not found.', 'error')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user {user_id}: {str(e)}")
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('user.edit_user_view'))

@user_bp.route('/user-activity-log')
@login_required
def user_activity_log():
    """Get user activity log with pagination"""
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
                
        from datetime import datetime, timedelta
        import json
        
        mock_logs = [
            {
                'id': 1,
                'activity_type': 'user_created',
                'target_user_email': 'john.doe@example.com',
                'performed_by_email': 'admin@example.com',
                'changes': None,
                'created_at': (datetime.now() - timedelta(minutes=30)).isoformat()
            },
            {
                'id': 2,
                'activity_type': 'role_changed',
                'target_user_email': 'jane.smith@example.com',
                'performed_by_email': 'admin@example.com',
                'changes': json.dumps({
                    'role': {'old': 'karyawan', 'new': 'pimpinan'}
                }),
                'created_at': (datetime.now() - timedelta(hours=2)).isoformat()
            },
            {
                'id': 3,
                'activity_type': 'password_changed',
                'target_user_email': 'user@example.com',
                'performed_by_email': 'user@example.com',
                'changes': json.dumps({
                    'password': {'old': '••••••••', 'new': '••••••••'}
                }),
                'created_at': (datetime.now() - timedelta(days=1)).isoformat()
            },
            {
                'id': 4,
                'activity_type': 'user_approved',
                'target_user_email': 'newuser@example.com',
                'performed_by_email': 'admin@example.com',
                'changes': None,
                'created_at': (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                'id': 5,
                'activity_type': 'email_changed',
                'target_user_email': 'updated@example.com',
                'performed_by_email': 'admin@example.com',
                'changes': json.dumps({
                    'email': {'old': 'old@example.com', 'new': 'updated@example.com'}
                }),
                'created_at': (datetime.now() - timedelta(days=3)).isoformat()
            },
            {
                'id': 6,
                'activity_type': 'user_deleted',
                'target_user_email': 'deleted@example.com',
                'performed_by_email': 'admin@example.com',
                'changes': None,
                'created_at': (datetime.now() - timedelta(days=7)).isoformat()
            }
        ]
        
        total_logs = len(mock_logs)
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_logs = mock_logs[start_index:end_index]
        
        total_pages = (total_logs + per_page - 1) // per_page
        
        pagination_info = {
            'current_page': page,
            'total_pages': total_pages,
            'total': total_logs,
            'showing': len(paginated_logs),
            'has_prev': page > 1,
            'has_next': page < total_pages
        }
        
        return jsonify({
            'success': True,
            'logs': paginated_logs,
            'pagination': pagination_info
        })
        
    except Exception as e:
        current_app.logger.error(f"Error loading activity log: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error loading activity log: {str(e)}'
        }), 500
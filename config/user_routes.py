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
    # Check permissions
    if not current_user.is_admin and current_user.id != user_id:
        flash('Anda tidak memiliki izin untuk mengedit user ini.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        try:
            # Update basic info
            user.email = request.form.get('email', user.email)
            
            # Only admin can change role and approval status
            if current_user.is_admin:
                user.role = request.form.get('role', user.role)
                user.is_approved = 'is_approved' in request.form
                user.is_admin = (user.role == 'admin')
            
            # Handle password change
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password:
                # Validate password confirmation
                if new_password != confirm_password:
                    flash('Password baru dan konfirmasi password tidak cocok!', 'error')
                    return render_template('auth/edit_user_profile.html', user=user)
                
                # Check current password if not admin editing other user
                if not current_user.is_admin or current_user.id == user_id:
                    if not current_password:
                        flash('Password lama harus diisi untuk mengubah password!', 'error')
                        return render_template('auth/edit_user_profile.html', user=user)
                    
                    if not user.check_password(current_password):
                        flash('Password lama tidak benar!', 'error')
                        return render_template('auth/edit_user_profile.html', user=user)
                
                # Validate new password strength
                if len(new_password) < 8:
                    flash('Password baru harus minimal 8 karakter!', 'error')
                    return render_template('auth/edit_user_profile.html', user=user)
                
                # Set new password
                user.set_password(new_password)
            
            db.session.commit()
            current_app.logger.info(f"User {user.email} updated by {current_user.email}")
            flash('Profile berhasil diperbarui!', 'success')
            
            # Redirect based on user role
            if current_user.is_admin and current_user.id != user_id:
                return redirect(url_for('user.edit_user_view'))
            else:
                return redirect(url_for('main.index'))
                
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user {user_id}: {str(e)}")
            flash(f'Error memperbarui profile: {str(e)}', 'error')

    return render_template('auth/edit_user_profile.html', user=user)

@user_bp.route('/edit-user', methods=['GET', 'POST'])
@login_required
def edit_user_view():
    try:
        if not current_user.is_admin:
            flash('Anda tidak memiliki izin untuk mengelola pegawai.', 'error')
            return redirect(url_for('main.index'))
        
        users = User.query.all()

        if request.method == 'POST':
            user_id = request.form.get('user_id')
            email = request.form.get('email')
            role = request.form.get('role')
            is_approved = 'is_approved' in request.form
            
            # Password fields
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')

            if not user_id:
                flash('Silakan pilih pegawai yang akan diedit.', 'error')
                return redirect(url_for('user.edit_user_view'))

            user = User.query.get(user_id)
            if user:
                # Update basic info
                user.email = email
                user.role = role
                user.is_approved = is_approved
                user.is_admin = (role == 'admin')
                
                # Handle password change if provided
                if new_password:
                    # Validate password confirmation
                    if new_password != confirm_new_password:
                        flash('Password baru dan konfirmasi password tidak cocok!', 'error')
                        return redirect(url_for('user.edit_user_view'))
                    
                    # Validate password strength
                    if len(new_password) < 8:
                        flash('Password baru harus minimal 8 karakter!', 'error')
                        return redirect(url_for('user.edit_user_view'))
                    
                    # For admin editing other users, current password is optional
                    # For users editing themselves, current password is required
                    if current_user.id == user.id and current_password:
                        if not user.check_password(current_password):
                            flash('Password lama tidak benar!', 'error')
                            return redirect(url_for('user.edit_user_view'))
                    
                    user.set_password(new_password)
                
                db.session.commit()
                current_app.logger.info(f"User {user.email} updated by {current_user.email}")
                flash('Data pegawai berhasil diperbarui!', 'success')
            else:
                flash('Data pegawai tidak ditemukan.', 'error')

            return redirect(url_for('user.edit_user_view'))

        return render_template('auth/edit_users.html', users=users)
    except Exception as e:
        current_app.logger.error(f"Error in edit_user_view: {str(e)}")
        flash('Terjadi kesalahan saat memuat halaman kelola pegawai.', 'error')
        return redirect(url_for('main.index'))

@user_bp.route('/get-user-data/<int:user_id>')
@login_required
def get_user_data(user_id):
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Tidak memiliki izin akses"}), 403
    
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
        return jsonify({"success": False, "message": "Tidak memiliki izin untuk menyetujui pegawai"}), 403
    
    try:
        user = User.query.get(user_id)
        if user:
            user.is_approved = True
            db.session.commit()
            current_app.logger.info(f"User {user.email} approved by {current_user.email}")
            return jsonify({"success": True, "message": f"Pegawai {user.email} berhasil disetujui"})
        else:
            return jsonify({"success": False, "message": "Data pegawai tidak ditemukan"}), 404
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving user {user_id}: {str(e)}")
        return jsonify({"success": False, "message": f"Gagal menyetujui pegawai: {str(e)}"}), 500

@user_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete user account"""
    if not current_user.is_admin:
        flash('Anda tidak memiliki izin untuk menghapus pegawai.', 'error')
        return redirect(url_for('main.index'))
    
    if user_id == current_user.id:
        flash('Anda tidak dapat menghapus akun Anda sendiri.', 'error')
        return redirect(url_for('user.edit_user_view'))
    
    try:
        user = User.query.get(user_id)
        if user:
            user_email = user.email
            db.session.delete(user)
            db.session.commit()
            current_app.logger.info(f"User {user_email} deleted by {current_user.email}")
            flash(f'Pegawai {user_email} berhasil dihapus.', 'success')
        else:
            flash('Data pegawai tidak ditemukan.', 'error')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user {user_id}: {str(e)}")
        flash(f'Gagal menghapus pegawai: {str(e)}', 'error')
    
    return redirect(url_for('user.edit_user_view'))

@user_bp.route('/user-activity-log')
@login_required
def user_activity_log():
    """Get user activity log with pagination"""
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Tidak memiliki izin untuk melihat log aktivitas"}), 403
    
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
            'message': f'Gagal memuat log aktivitas: {str(e)}'
        }), 500

@user_bp.route('/profile')
@login_required
def profile():
    """View current user profile"""
    return render_template('auth/edit_user_profile.html', user=current_user)

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit current user profile"""
    return edit_user(current_user.id)

@user_bp.route('/my-profile')
@login_required
def my_profile():
    """Quick access to current user profile"""
    return redirect(url_for('user.edit_user', user_id=current_user.id))
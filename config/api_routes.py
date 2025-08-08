import math
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user

from config.extensions import db
from config.models import SuratMasuk, UserLoginLog
from config.route_utils import role_required

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/notifications/count', methods=['GET'])
@login_required
def get_notification_count():
    """Get notification count for current user"""
    try:
        if current_user.role in ['pimpinan', 'admin']:
            pending_count = SuratMasuk.query.filter_by(status_suratMasuk='pending').count()
            return jsonify({
                'success': True,
                'pending_count': pending_count
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
    except Exception as e:
        current_app.logger.error(f"Error getting notification count: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@api_bp.route('/test', methods=['GET'])
@login_required
def test_api():
    """Test API endpoint"""
    return jsonify({
        'success': True,
        'message': 'API berfungsi dengan baik',
        'user': current_user.email,
        'role': current_user.role
    })


@api_bp.route('/surat-keluar/detail/<int:surat_id>', methods=['GET'])
@login_required
@role_required('pimpinan')
def get_surat_masuk_detail(surat_id):
    """Get surat masuk detail"""
    try:
        surat = SuratMasuk.query.get(surat_id)
        if not surat:
            return jsonify({
                'success': False,
                'message': f'Surat dengan ID {surat_id} tidak ditemukan'
            }), 404
        
        try:
            tanggal_str = surat.tanggal_suratMasuk.strftime('%d/%m/%Y') if surat.tanggal_suratMasuk else ''
        except Exception as e:
            current_app.logger.error(f"Error formatting date: {str(e)}")
            tanggal_str = ''
        
        try:
            created_at_str = surat.created_at.strftime('%Y-%m-%d %H:%M') if surat.created_at else ''
        except Exception as e:
            current_app.logger.error(f"Error formatting created_at: {str(e)}")
            created_at_str = ''
        
        surat_data = {
            'id_suratMasuk': surat.id_suratMasuk,
            'nomor_suratMasuk': str(surat.nomor_suratMasuk) if surat.nomor_suratMasuk else '',
            'tanggal_suratMasuk': tanggal_str,
            'pengirim_suratMasuk': str(surat.pengirim_suratMasuk) if surat.pengirim_suratMasuk else '',
            'penerima_suratMasuk': str(surat.penerima_suratMasuk) if surat.penerima_suratMasuk else '',
            'isi_suratMasuk': str(surat.isi_suratMasuk) if surat.isi_suratMasuk else '',
            'status_suratMasuk': str(surat.status_suratMasuk) if surat.status_suratMasuk else 'pending',
            'file_suratMasuk': bool(surat.file_suratMasuk),
            'has_gambar': bool(surat.gambar_suratMasuk),
            'created_at': created_at_str
        }
        
        current_app.logger.info(f"Successfully retrieved surat data for ID {surat_id}")
        
        return jsonify({
            'success': True,
            'surat': surat_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting surat keluar detail for ID {surat_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Gagal memuat detail surat: {str(e)}'
        }), 500


@api_bp.route('/chart-data')
@login_required
def chart_data():
    """Get chart data for dashboard"""
    try:
        # Get monthly data for the current year
        from datetime import datetime
        from sqlalchemy import extract, func
        
        current_year = datetime.now().year
        
        monthly_data = db.session.query(
            extract('month', SuratMasuk.tanggal_suratMasuk).label('month'),
            func.count(SuratMasuk.id_suratMasuk).label('count')
        ).filter(
            extract('year', SuratMasuk.tanggal_suratMasuk) == current_year
        ).group_by(
            extract('month', SuratMasuk.tanggal_suratMasuk)
        ).all()
        
        data = {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            'datasets': [{
                'label': 'Surat Masuk',
                'data': [0] * 12,
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1
            }]
        }
        
        for month, count in monthly_data:
            if month:
                data['datasets'][0]['data'][int(month) - 1] = count
        
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error getting chart data: {str(e)}")
        return jsonify({'error': 'Failed to load chart data'}), 500


@api_bp.route('/debug/surat/<int:surat_id>', methods=['GET'])
@login_required
@role_required('pimpinan')
def debug_surat(surat_id):
    """Debug surat information"""
    try:
        surat = SuratMasuk.query.get(surat_id)
        if not surat:
            return jsonify({'error': 'Surat not found'}), 404
        
        debug_info = {
            'id': surat.id_suratMasuk,
            'nomor': surat.nomor_suratMasuk,
            'pengirim': surat.pengirim_suratMasuk,
            'penerima': surat.penerima_suratMasuk,
            'isi': surat.isi_suratMasuk,
            'status': surat.status_suratMasuk,
            'created_at': surat.created_at.isoformat() if surat.created_at else None,
            'has_file': bool(surat.file_suratMasuk),
            'has_image': bool(surat.gambar_suratMasuk)
        }
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/user-login-logs')
@login_required
def get_user_login_logs():
    """Get user login logs with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        date_filter = request.args.get('date')
        user_filter = request.args.get('user')
        status_filter = request.args.get('status')
        user_id_filter = request.args.get('user_id', type=int)
        
        query = UserLoginLog.query
        
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
        
        query = query.order_by(UserLoginLog.login_time.desc())
        
        total_count = query.count()
        
        offset = (page - 1) * per_page
        logs = query.offset(offset).limit(per_page).all()
        
        logs_data = [log.to_dict() for log in logs]
        
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


@api_bp.route('/update-ocr-accuracy/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'pimpinan')
def update_ocr_accuracy(id):
    """Update OCR accuracy for a specific document"""
    try:
        surat_type = request.form.get('type')  # 'masuk' or 'keluar'
        
        if surat_type == 'masuk':
            surat = SuratKeluar.query.get_or_404(id)
            try:
                from config.ocr_utils import calculate_overall_ocr_accuracy
                surat.ocr_accuracy_suratKeluar = calculate_overall_ocr_accuracy(surat, 'suratKeluar')
                accuracy = surat.ocr_accuracy_suratKeluar
            except ImportError:
                # Fallback if ocr_utils is not available
                accuracy = 0
        elif surat_type == 'keluar':
            surat = SuratMasuk.query.get_or_404(id)
            try:
                from config.ocr_utils import calculate_overall_ocr_accuracy
                surat.ocr_accuracy_suratMasuk = calculate_overall_ocr_accuracy(surat, 'suratMasuk')
                accuracy = surat.ocr_accuracy_suratMasuk
            except ImportError:
                accuracy = 0
        else:
            return jsonify({"success": False, "error": "Invalid surat type"})
        
        db.session.commit()
        return jsonify({"success": True, "accuracy": accuracy})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating OCR accuracy: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
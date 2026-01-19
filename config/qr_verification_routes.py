"""
QR Code Verification Routes
============================
Routes untuk verifikasi QR code surat cuti
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from config.qr_code_generator import QRCodeGenerator
from config.models import Cuti, db
import json

qr_verify_bp = Blueprint('qr_verify', __name__, url_prefix='/verify-cuti')

@qr_verify_bp.route('/<signature_hash>')
def verify_qr_code(signature_hash):
    """Public route untuk verifikasi QR code"""
    try:
        qr_generator = QRCodeGenerator()
        result = qr_generator.verify_qr_code(signature_hash)
        
        return render_template(
            'cuti/verify_qr_code.html',
            result=result,
            signature_hash=signature_hash
        )
        
    except Exception as e:
        return render_template(
            'cuti/verify_qr_code.html',
            result={
                'valid': False,
                'message': f'Error: {str(e)}',
                'data': None
            },
            signature_hash=signature_hash
        )

@qr_verify_bp.route('/api/<signature_hash>')
def verify_qr_code_api(signature_hash):
    """API endpoint untuk verifikasi QR code"""
    try:
        qr_generator = QRCodeGenerator()
        result = qr_generator.verify_qr_code(signature_hash)
        
        return jsonify(result), 200 if result['valid'] else 404
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'message': f'Error: {str(e)}',
            'data': None
        }), 500

@qr_verify_bp.route('/preview/<int:cuti_id>')
@login_required
def preview_qr_code(cuti_id):
    """Preview QR code untuk surat cuti tertentu"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)
        
        # Generate QR code if not exists
        if not cuti.qr_code:
            qr_generator = QRCodeGenerator()
            approver_info = {
                'name': current_user.username,
                'nip': getattr(current_user, 'nip', '-')
            }
            
            qr_result = qr_generator.generate_qr_code_with_text(cuti, approver_info)
            
            if qr_result:
                cuti.qr_code = qr_result['signature_hash']
                db.session.commit()
                
                return render_template(
                    'cuti/preview_qr_code.html',
                    cuti=cuti,
                    qr_result=qr_result
                )
        else:
            # Load existing QR code
            qr_generator = QRCodeGenerator()
            qr_data, _ = qr_generator.create_qr_data(cuti)
            
            return render_template(
                'cuti/preview_qr_code.html',
                cuti=cuti,
                qr_result={
                    'signature_hash': cuti.qr_code,
                    'qr_data': qr_data,
                    'verification_url': qr_generator.create_verification_url(cuti.qr_code)
                }
            )
            
    except Exception as e:
        flash(f'Error preview QR code: {str(e)}', 'error')
        return redirect(url_for('cuti.list_cuti'))

@qr_verify_bp.route('/regenerate/<int:cuti_id>', methods=['POST'])
@login_required
def regenerate_qr_code(cuti_id):
    """Regenerate QR code untuk surat cuti"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)
        
        qr_generator = QRCodeGenerator()
        approver_info = {
            'name': current_user.username,
            'nip': getattr(current_user, 'nip', '-')
        }
        
        # Get style from request
        style = request.form.get('style', 'with_text')
        
        if style == 'basic':
            qr_result = qr_generator.generate_qr_code_basic(cuti, approver_info)
        elif style == 'styled':
            qr_result = qr_generator.generate_qr_code_styled(cuti, approver_info)
        elif style == 'with_logo':
            qr_result = qr_generator.generate_qr_code_with_logo(cuti, approver_info)
        else:  # with_text
            qr_result = qr_generator.generate_qr_code_with_text(cuti, approver_info)
        
        if qr_result:
            cuti.qr_code = qr_result['signature_hash']
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'QR code berhasil di-generate ulang',
                'qr_base64': qr_result['qr_base64'],
                'signature_hash': qr_result['signature_hash'],
                'verification_url': qr_result['verification_url']
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Gagal generate QR code'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@qr_verify_bp.route('/scan')
def scan_qr_code():
    """Halaman untuk scan QR code menggunakan kamera"""
    return render_template('cuti/scan_qr_code.html')

@qr_verify_bp.route('/batch-verify', methods=['POST'])
@login_required
def batch_verify_qr_codes():
    """Verifikasi multiple QR codes sekaligus"""
    try:
        data = request.get_json()
        signature_hashes = data.get('signature_hashes', [])
        
        if not signature_hashes:
            return jsonify({
                'success': False,
                'message': 'Tidak ada signature hash yang diberikan'
            }), 400
        
        qr_generator = QRCodeGenerator()
        results = []
        
        for signature_hash in signature_hashes:
            result = qr_generator.verify_qr_code(signature_hash)
            results.append({
                'signature_hash': signature_hash,
                'valid': result['valid'],
                'message': result['message'],
                'data': result['data']
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results),
            'valid_count': sum(1 for r in results if r['valid'])
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

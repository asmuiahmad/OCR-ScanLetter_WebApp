"""
Pegawai routes
Employee management functionality
"""

from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required

from config.extensions import db
from config.models import Pegawai
from config.route_utils import role_required

pegawai_bp = Blueprint('pegawai', __name__)


@pegawai_bp.route('/pegawai', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def pegawai():
    """Add new pegawai"""
    if request.method == 'POST':
        try:
            # Get form data
            nama = request.form.get('nama')
            nip = request.form.get('nip')
            tanggal_lahir_str = request.form.get('tanggal_lahir')
            jenis_kelamin = request.form.get('jenis_kelamin')
            agama = request.form.get('agama')
            jabatan = request.form.get('jabatan')
            golongan = request.form.get('golongan')
            nomor_telpon = request.form.get('nomor_telpon')
            riwayat_pendidikan = request.form.get('riwayat_pendidikan')
            riwayat_pekerjaan = request.form.get('riwayat_pekerjaan')
            
            # Validate required fields
            if not all([nama, nip, tanggal_lahir_str, jenis_kelamin]):
                return jsonify({
                    "success": False, 
                    "message": "Nama, NIP, tanggal lahir, dan jenis kelamin wajib diisi"
                }), 400
            
            # Check if NIP already exists
            existing_pegawai = Pegawai.query.filter_by(nip=nip).first()
            if existing_pegawai:
                return jsonify({
                    "success": False, 
                    "message": f"NIP {nip} sudah terdaftar"
                }), 400
            
            # Parse date
            try:
                tanggal_lahir = datetime.strptime(tanggal_lahir_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    "success": False, 
                    "message": "Format tanggal lahir tidak valid"
                }), 400
            
            # Create new pegawai
            new_pegawai = Pegawai(
                nama=nama,
                nip=nip,
                tanggal_lahir=tanggal_lahir,
                jenis_kelamin=jenis_kelamin,
                agama=agama,
                jabatan=jabatan,
                golongan=golongan,
                nomor_telpon=nomor_telpon,
                riwayat_pendidikan=riwayat_pendidikan,
                riwayat_pekerjaan=riwayat_pekerjaan
            )
            
            db.session.add(new_pegawai)
            db.session.commit()
            
            current_app.logger.info(f"Pegawai baru ditambahkan: {nama} (NIP: {nip})")
            
            return jsonify({
                "success": True, 
                "message": f"Pegawai {nama} berhasil ditambahkan"
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding pegawai: {str(e)}")
            return jsonify({
                "success": False, 
                "message": f"Gagal menambahkan pegawai: {str(e)}"
            }), 500
    
    return render_template('pegawai/pegawai.html')


@pegawai_bp.route('/pegawai/list', methods=['GET'])
@login_required
@role_required('admin', 'pimpinan')
def pegawai_list():
    """List all pegawai"""
    try:
        daftar_pegawai = Pegawai.query.all()
        current_app.logger.info(f"Found {len(daftar_pegawai)} pegawai records")
        return render_template('pegawai/list_pegawai_simple.html', daftar_pegawai=daftar_pegawai)
    except Exception as e:
        current_app.logger.error(f"Error in pegawai_list: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500


@pegawai_bp.route('/pegawai/edit/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'pimpinan')
def edit_pegawai(id):
    """Edit pegawai"""
    try:
        pegawai = Pegawai.query.get(id)
        if not pegawai:
            return jsonify({"success": False, "message": "Pegawai tidak ditemukan"}), 404
        
        # Get form data
        nama = request.form.get('nama')
        nip = request.form.get('nip')
        tanggal_lahir_str = request.form.get('tanggal_lahir')
        jenis_kelamin = request.form.get('jenis_kelamin')
        agama = request.form.get('agama')
        jabatan = request.form.get('jabatan')
        golongan = request.form.get('golongan')
        nomor_telpon = request.form.get('nomor_telpon')
        riwayat_pendidikan = request.form.get('riwayat_pendidikan')
        riwayat_pekerjaan = request.form.get('riwayat_pekerjaan')
        
        # Validate required fields
        if not all([nama, nip, tanggal_lahir_str, jenis_kelamin]):
            return jsonify({
                "success": False, 
                "message": "Nama, NIP, tanggal lahir, dan jenis kelamin wajib diisi"
            }), 400
        
        # Check if NIP already exists (excluding current pegawai)
        existing_pegawai = Pegawai.query.filter(
            Pegawai.nip == nip, 
            Pegawai.id != id
        ).first()
        if existing_pegawai:
            return jsonify({
                "success": False, 
                "message": f"NIP {nip} sudah digunakan oleh pegawai lain"
            }), 400
        
        # Parse date
        try:
            tanggal_lahir = datetime.strptime(tanggal_lahir_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                "success": False, 
                "message": "Format tanggal lahir tidak valid"
            }), 400
        
        # Update pegawai data
        pegawai.nama = nama
        pegawai.nip = nip
        pegawai.tanggal_lahir = tanggal_lahir
        pegawai.jenis_kelamin = jenis_kelamin
        pegawai.agama = agama
        pegawai.jabatan = jabatan
        pegawai.golongan = golongan
        pegawai.nomor_telpon = nomor_telpon
        pegawai.riwayat_pendidikan = riwayat_pendidikan
        pegawai.riwayat_pekerjaan = riwayat_pekerjaan
        
        db.session.commit()
        
        current_app.logger.info(f"Pegawai diupdate: {nama} (ID: {id})")
        
        return jsonify({
            "success": True, 
            "message": f"Data pegawai {nama} berhasil diperbarui"
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating pegawai {id}: {str(e)}")
        return jsonify({"success": False, "message": f"Gagal mengupdate pegawai: {str(e)}"}), 500


@pegawai_bp.route('/add', methods=['POST'])
@login_required
@role_required('admin', 'pimpinan')
def add_pegawai():
    """Add new pegawai via JSON API"""
    try:
        data = request.get_json()
        
        # Validate required fields based on actual model
        required_fields = ['nama', 'nip', 'tanggal_lahir', 'jenis_kelamin']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Field {field} wajib diisi'
                }), 400
        
        # Check if NIP already exists
        existing_pegawai = Pegawai.query.filter_by(nip=data['nip']).first()
        if existing_pegawai:
            return jsonify({
                'success': False,
                'message': f'NIP {data["nip"]} sudah terdaftar'
            }), 400
        
        # Parse date
        try:
            tanggal_lahir = datetime.strptime(data['tanggal_lahir'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Format tanggal lahir tidak valid (gunakan YYYY-MM-DD)'
            }), 400
        
        # Create new pegawai
        pegawai = Pegawai(
            nama=data['nama'],
            nip=data['nip'],
            tanggal_lahir=tanggal_lahir,
            jenis_kelamin=data['jenis_kelamin'],
            jabatan=data.get('jabatan'),
            golongan=data.get('golongan'),
            agama=data.get('agama'),
            nomor_telpon=data.get('nomor_telpon'),
            riwayat_pendidikan=data.get('riwayat_pendidikan'),
            riwayat_pekerjaan=data.get('riwayat_pekerjaan')
        )
        
        db.session.add(pegawai)
        db.session.commit()
        
        current_app.logger.info(f"Pegawai baru ditambahkan via API: {pegawai.nama} (NIP: {pegawai.nip})")
        
        return jsonify({
            'success': True,
            'message': f'Pegawai {pegawai.nama} berhasil ditambahkan',
            'data': {
                'id': pegawai.id,
                'nama': pegawai.nama,
                'nip': pegawai.nip,
                'tanggal_lahir': pegawai.tanggal_lahir.isoformat(),
                'jenis_kelamin': pegawai.jenis_kelamin,
                'jabatan': pegawai.jabatan,
                'golongan': pegawai.golongan,
                'agama': pegawai.agama,
                'nomor_telpon': pegawai.nomor_telpon,
                'riwayat_pendidikan': pegawai.riwayat_pendidikan,
                'riwayat_pekerjaan': pegawai.riwayat_pekerjaan
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding pegawai via API: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat menambahkan pegawai'
        }), 500


@pegawai_bp.route('/pegawai/hapus/<int:id>', methods=['POST'])
@login_required
@role_required('admin')
def hapus_pegawai(id):
    """Delete pegawai"""
    try:
        pegawai = Pegawai.query.get(id)
        if not pegawai:
            return jsonify({"success": False, "message": "Pegawai tidak ditemukan"}), 404
        
        nama_pegawai = pegawai.nama
        nip_pegawai = pegawai.nip
        
        # Check if pegawai is referenced in other tables
        # Add checks here if needed for referential integrity
        
        db.session.delete(pegawai)
        db.session.commit()
        
        current_app.logger.info(f"Pegawai dihapus: {nama_pegawai} (NIP: {nip_pegawai})")
        
        return jsonify({
            "success": True, 
            "message": f"Pegawai {nama_pegawai} berhasil dihapus"
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting pegawai {id}: {str(e)}")
        return jsonify({"success": False, "message": f"Gagal menghapus pegawai: {str(e)}"}), 500
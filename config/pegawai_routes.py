"""
Pegawai routes
Employee management functionality
"""

from datetime import datetime

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import login_required

from config.extensions import db
from config.models import Pegawai
from config.route_utils import role_required

pegawai_bp = Blueprint("pegawai", __name__)


@pegawai_bp.route("/pegawai", methods=["GET", "POST"])
@login_required
@role_required("admin", "pimpinan")
def pegawai():
    """Add new pegawai"""
    if request.method == "POST":
        try:
            current_app.logger.info("=== POST /pegawai called ===")
            current_app.logger.info(f"Request method: {request.method}")
            current_app.logger.info(f"Content-Type: {request.content_type}")
            current_app.logger.info(
                f"Is AJAX: {request.headers.get('X-Requested-With')}"
            )
            current_app.logger.info(f"Form data keys: {list(request.form.keys())}")

            # Get form data
            nama = request.form.get("nama")
            nip = request.form.get("nip")
            tanggal_lahir_str = request.form.get("tanggal_lahir")
            jenis_kelamin = request.form.get("jenis_kelamin")
            agama = request.form.get("agama")
            jabatan = request.form.get("jabatan")
            golongan = request.form.get("golongan")
            nomor_telpon = request.form.get("nomor_telpon")
            riwayat_pendidikan = request.form.get("riwayat_pendidikan")
            riwayat_pekerjaan = request.form.get("riwayat_pekerjaan")

            current_app.logger.info(
                f"Received data - nama: {nama}, nip: {nip}, tanggal_lahir: {tanggal_lahir_str}, jenis_kelamin: {jenis_kelamin}"
            )

            # Validate required fields
            if not all([nama, nip, tanggal_lahir_str, jenis_kelamin]):
                current_app.logger.warning("Validation failed: missing required fields")
                return jsonify(
                    {
                        "success": False,
                        "message": "Nama, NIP, tanggal lahir, dan jenis kelamin wajib diisi",
                    }
                ), 400

            # Check if NIP already exists
            existing_pegawai = Pegawai.query.filter_by(nip=nip).first()
            if existing_pegawai:
                current_app.logger.warning(f"NIP {nip} already exists")
                return jsonify(
                    {"success": False, "message": f"NIP {nip} sudah terdaftar"}
                ), 400

            # Parse date
            try:
                if tanggal_lahir_str:
                    tanggal_lahir = datetime.strptime(
                        tanggal_lahir_str, "%Y-%m-%d"
                    ).date()
                else:
                    return jsonify(
                        {"success": False, "message": "Tanggal lahir wajib diisi"}
                    ), 400
            except ValueError:
                return jsonify(
                    {"success": False, "message": "Format tanggal lahir tidak valid"}
                ), 400

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
                riwayat_pekerjaan=riwayat_pekerjaan,
            )

            db.session.add(new_pegawai)
            db.session.commit()

            current_app.logger.info(f"Pegawai baru ditambahkan: {nama} (NIP: {nip})")
            current_app.logger.info(f"Returning success response")

            return jsonify(
                {"success": True, "message": f"Pegawai {nama} berhasil ditambahkan"}
            ), 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding pegawai: {str(e)}")
            current_app.logger.error(f"Error type: {type(e).__name__}")
            import traceback

            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify(
                {"success": False, "message": f"Gagal menambahkan pegawai: {str(e)}"}
            ), 500

    return render_template("pegawai/pegawai.html")


@pegawai_bp.route("/pegawai/list", methods=["GET"])
@login_required
@role_required("admin", "pimpinan")
def pegawai_list():
    """List all pegawai"""
    try:
        daftar_pegawai = Pegawai.query.all()
        current_app.logger.info(f"Found {len(daftar_pegawai)} pegawai records")
        return render_template(
            "pegawai/list_pegawai_simple.html", daftar_pegawai=daftar_pegawai
        )
    except Exception as e:
        current_app.logger.error(f"Error in pegawai_list: {str(e)}")
        return jsonify(
            {"success": False, "message": f"Terjadi kesalahan: {str(e)}"}
        ), 500


@pegawai_bp.route("/pegawai/edit/<int:id>", methods=["POST"])
@login_required
@role_required("admin", "pimpinan")
def edit_pegawai(id):
    """Edit pegawai"""
    try:
        pegawai = Pegawai.query.get(id)
        if not pegawai:
            return jsonify(
                {"success": False, "message": "Pegawai tidak ditemukan"}
            ), 404

        # Get form data
        nama = request.form.get("nama")
        nip = request.form.get("nip")
        tanggal_lahir_str = request.form.get("tanggal_lahir")
        jenis_kelamin = request.form.get("jenis_kelamin")
        agama = request.form.get("agama")
        jabatan = request.form.get("jabatan")
        golongan = request.form.get("golongan")
        nomor_telpon = request.form.get("nomor_telpon")
        riwayat_pendidikan = request.form.get("riwayat_pendidikan")
        riwayat_pekerjaan = request.form.get("riwayat_pekerjaan")

        # Validate required fields
        if not all([nama, nip, tanggal_lahir_str, jenis_kelamin]):
            return jsonify(
                {
                    "success": False,
                    "message": "Nama, NIP, tanggal lahir, dan jenis kelamin wajib diisi",
                }
            ), 400

        # Check if NIP already exists (excluding current pegawai)
        existing_pegawai = Pegawai.query.filter(
            Pegawai.nip == nip, Pegawai.id != id
        ).first()
        if existing_pegawai:
            return jsonify(
                {
                    "success": False,
                    "message": f"NIP {nip} sudah digunakan oleh pegawai lain",
                }
            ), 400

        # Parse date
        try:
            if tanggal_lahir_str:
                tanggal_lahir = datetime.strptime(tanggal_lahir_str, "%Y-%m-%d").date()
            else:
                return jsonify(
                    {"success": False, "message": "Tanggal lahir wajib diisi"}
                ), 400
        except ValueError:
            return jsonify(
                {"success": False, "message": "Format tanggal lahir tidak valid"}
            ), 400

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

        return jsonify(
            {"success": True, "message": f"Data pegawai {nama} berhasil diperbarui"}
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating pegawai {id}: {str(e)}")
        return jsonify(
            {"success": False, "message": f"Gagal mengupdate pegawai: {str(e)}"}
        ), 500


@pegawai_bp.route("/add", methods=["POST"])
@login_required
@role_required("admin", "pimpinan")
def add_pegawai():
    """Add new pegawai via JSON API"""
    try:
        data = request.get_json()

        # Validate required fields based on actual model
        required_fields = ["nama", "nip", "tanggal_lahir", "jenis_kelamin"]
        for field in required_fields:
            if not data.get(field):
                return jsonify(
                    {"success": False, "message": f"Field {field} wajib diisi"}
                ), 400

        # Check if NIP already exists
        existing_pegawai = Pegawai.query.filter_by(nip=data["nip"]).first()
        if existing_pegawai:
            return jsonify(
                {"success": False, "message": f"NIP {data['nip']} sudah terdaftar"}
            ), 400

        # Parse date
        try:
            tanggal_lahir_str = data.get("tanggal_lahir")
            if tanggal_lahir_str:
                tanggal_lahir = datetime.strptime(tanggal_lahir_str, "%Y-%m-%d").date()
            else:
                return jsonify(
                    {"success": False, "message": "Tanggal lahir wajib diisi"}
                ), 400
        except ValueError:
            return jsonify(
                {
                    "success": False,
                    "message": "Format tanggal lahir tidak valid (gunakan YYYY-MM-DD)",
                }
            ), 400

        # Create new pegawai
        pegawai = Pegawai(
            nama=data["nama"],
            nip=data["nip"],
            tanggal_lahir=tanggal_lahir,
            jenis_kelamin=data["jenis_kelamin"],
            jabatan=data.get("jabatan"),
            golongan=data.get("golongan"),
            agama=data.get("agama"),
            nomor_telpon=data.get("nomor_telpon"),
            riwayat_pendidikan=data.get("riwayat_pendidikan"),
            riwayat_pekerjaan=data.get("riwayat_pekerjaan"),
        )

        db.session.add(pegawai)
        db.session.commit()

        current_app.logger.info(
            f"Pegawai baru ditambahkan via API: {pegawai.nama} (NIP: {pegawai.nip})"
        )

        return jsonify(
            {
                "success": True,
                "message": f"Pegawai {pegawai.nama} berhasil ditambahkan",
                "data": {
                    "id": pegawai.id,
                    "nama": pegawai.nama,
                    "nip": pegawai.nip,
                    "tanggal_lahir": pegawai.tanggal_lahir.isoformat(),
                    "jenis_kelamin": pegawai.jenis_kelamin,
                    "jabatan": pegawai.jabatan,
                    "golongan": pegawai.golongan,
                    "agama": pegawai.agama,
                    "nomor_telpon": pegawai.nomor_telpon,
                    "riwayat_pendidikan": pegawai.riwayat_pendidikan,
                    "riwayat_pekerjaan": pegawai.riwayat_pekerjaan,
                },
            }
        ), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding pegawai via API: {str(e)}")
        return jsonify(
            {"success": False, "message": "Terjadi kesalahan saat menambahkan pegawai"}
        ), 500


@pegawai_bp.route("/pegawai/hapus/<int:id>", methods=["POST"])
@login_required
@role_required("admin")
def hapus_pegawai(id):
    """Delete pegawai"""
    try:
        pegawai = Pegawai.query.get(id)
        if not pegawai:
            return jsonify(
                {"success": False, "message": "Pegawai tidak ditemukan"}
            ), 404

        nama_pegawai = pegawai.nama
        nip_pegawai = pegawai.nip

        # Check if pegawai is referenced in other tables
        # Add checks here if needed for referential integrity

        db.session.delete(pegawai)
        db.session.commit()

        current_app.logger.info(f"Pegawai dihapus: {nama_pegawai} (NIP: {nip_pegawai})")

        return jsonify(
            {"success": True, "message": f"Pegawai {nama_pegawai} berhasil dihapus"}
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting pegawai {id}: {str(e)}")
        return jsonify(
            {"success": False, "message": f"Gagal menghapus pegawai: {str(e)}"}
        ), 500


@pegawai_bp.route("/pegawai/debug", methods=["GET", "POST"])
@login_required
@role_required("admin", "pimpinan")
def pegawai_debug():
    """Debug endpoint untuk test form pegawai - returns detailed error info"""
    if request.method == "POST":
        try:
            current_app.logger.info("=== DEBUG POST /pegawai/debug called ===")

            # Log all request data
            current_app.logger.info(f"Request method: {request.method}")
            current_app.logger.info(f"Content-Type: {request.content_type}")
            current_app.logger.info(f"Headers: {dict(request.headers)}")
            current_app.logger.info(f"Form data: {dict(request.form)}")
            current_app.logger.info(f"Files: {dict(request.files)}")

            # Get form data
            nama = request.form.get("nama")
            nip = request.form.get("nip")
            tanggal_lahir_str = request.form.get("tanggal_lahir")
            jenis_kelamin = request.form.get("jenis_kelamin")

            debug_info = {
                "request_received": True,
                "method": request.method,
                "content_type": request.content_type,
                "form_keys": list(request.form.keys()),
                "form_data": {
                    "nama": nama,
                    "nip": nip,
                    "tanggal_lahir": tanggal_lahir_str,
                    "jenis_kelamin": jenis_kelamin,
                },
                "has_csrf_token": "csrf_token" in request.form,
                "is_ajax": request.headers.get("X-Requested-With") == "XMLHttpRequest",
            }

            current_app.logger.info(f"Debug info: {debug_info}")

            # Validate required fields
            if not all([nama, nip, tanggal_lahir_str, jenis_kelamin]):
                missing = []
                if not nama:
                    missing.append("nama")
                if not nip:
                    missing.append("nip")
                if not tanggal_lahir_str:
                    missing.append("tanggal_lahir")
                if not jenis_kelamin:
                    missing.append("jenis_kelamin")

                return jsonify(
                    {
                        "success": False,
                        "message": f"Field wajib kosong: {', '.join(missing)}",
                        "debug": debug_info,
                        "missing_fields": missing,
                    }
                ), 400

            # Try to parse date
            try:
                tanggal_lahir = datetime.strptime(tanggal_lahir_str, "%Y-%m-%d").date()
            except ValueError as e:
                return jsonify(
                    {
                        "success": False,
                        "message": f"Format tanggal tidak valid: {str(e)}",
                        "debug": debug_info,
                    }
                ), 400

            # Check NIP exists
            existing = Pegawai.query.filter_by(nip=nip).first()
            if existing:
                return jsonify(
                    {
                        "success": False,
                        "message": f"NIP {nip} sudah terdaftar",
                        "debug": debug_info,
                    }
                ), 400

            # All validation passed
            return jsonify(
                {
                    "success": True,
                    "message": "Validasi berhasil! (Debug mode - data tidak disimpan)",
                    "debug": debug_info,
                    "would_save": {
                        "nama": nama,
                        "nip": nip,
                        "tanggal_lahir": tanggal_lahir_str,
                        "jenis_kelamin": jenis_kelamin,
                    },
                }
            ), 200

        except Exception as e:
            current_app.logger.error(f"Debug error: {str(e)}")
            import traceback

            return jsonify(
                {
                    "success": False,
                    "message": f"Error: {str(e)}",
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                }
            ), 500

    # GET request - show debug form
    return render_template("pegawai/pegawai_debug.html")

"""
Pegawai routes
Employee management functionality
"""

from datetime import datetime

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import login_required
from sqlalchemy import or_

from config.extensions import db
from config.models import Pegawai
from config.route_utils import role_required

pegawai_bp = Blueprint("pegawai", __name__)


@pegawai_bp.route("/pegawai", methods=["GET", "POST"])
@login_required
@role_required("admin")
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
            batas_cuti_str = request.form.get("batas_cuti", "12")

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

            # Parse batas_cuti
            try:
                batas_cuti = int(batas_cuti_str) if batas_cuti_str else 12
                if batas_cuti < 0 or batas_cuti > 30:
                    return jsonify(
                        {"success": False, "message": "Batas cuti harus antara 0-30 hari"}
                    ), 400
            except ValueError:
                return jsonify(
                    {"success": False, "message": "Batas cuti harus berupa angka"}
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
                batas_cuti=batas_cuti,
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
            "pegawai/list_pegawai.html", daftar_pegawai=daftar_pegawai
        )
    except Exception as e:
        current_app.logger.error(f"Error in pegawai_list: {str(e)}")
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(
                {"success": False, "message": f"Terjadi kesalahan: {str(e)}"}
            ), 500
        else:
            # For regular browser requests, render error page
            from flask import flash, redirect, url_for
            flash(f"Terjadi kesalahan saat memuat daftar pegawai: {str(e)}", "error")
            return redirect(url_for("dashboard.dashboard"))


@pegawai_bp.route("/pegawai/edit/<int:id>", methods=["POST"])
@login_required
@role_required("admin")
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
        batas_cuti_str = request.form.get("batas_cuti", "12")

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

        # Parse batas_cuti
        try:
            batas_cuti = int(batas_cuti_str) if batas_cuti_str else 12
            if batas_cuti < 0 or batas_cuti > 30:
                return jsonify(
                    {"success": False, "message": "Batas cuti harus antara 0-30 hari"}
                ), 400
        except ValueError:
            return jsonify(
                {"success": False, "message": "Batas cuti harus berupa angka"}
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
        pegawai.batas_cuti = batas_cuti

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
@role_required("admin")
def add_pegawai():
    """Add new pegawai via JSON API or Form"""
    try:
        # Check if it's JSON or form data
        if request.is_json:
            data = request.get_json()
        else:
            # Handle form data
            data = request.form.to_dict()

        # Validate required fields based on actual model
        required_fields = ["nama", "nip", "tanggal_lahir", "jenis_kelamin"]
        for field in required_fields:
            if not data.get(field):
                if request.is_json:
                    return jsonify(
                        {"success": False, "message": f"Field {field} wajib diisi"}
                    ), 400
                else:
                    from flask import flash, redirect, url_for
                    flash(f"Field {field} wajib diisi", "error")
                    return redirect(url_for("pegawai.pegawai_list"))

        # Check if NIP already exists
        existing_pegawai = Pegawai.query.filter_by(nip=data["nip"]).first()
        if existing_pegawai:
            if request.is_json:
                return jsonify(
                    {"success": False, "message": f"NIP {data['nip']} sudah terdaftar"}
                ), 400
            else:
                from flask import flash, redirect, url_for
                flash(f"NIP {data['nip']} sudah terdaftar", "error")
                return redirect(url_for("pegawai.pegawai_list"))

        # Parse date
        try:
            tanggal_lahir_str = data.get("tanggal_lahir")
            if tanggal_lahir_str:
                tanggal_lahir = datetime.strptime(tanggal_lahir_str, "%Y-%m-%d").date()
            else:
                if request.is_json:
                    return jsonify(
                        {"success": False, "message": "Tanggal lahir wajib diisi"}
                    ), 400
                else:
                    from flask import flash, redirect, url_for
                    flash("Tanggal lahir wajib diisi", "error")
                    return redirect(url_for("pegawai.pegawai_list"))
        except ValueError:
            if request.is_json:
                return jsonify(
                    {
                        "success": False,
                        "message": "Format tanggal lahir tidak valid (gunakan YYYY-MM-DD)",
                    }
                ), 400
            else:
                from flask import flash, redirect, url_for
                flash("Format tanggal lahir tidak valid", "error")
                return redirect(url_for("pegawai.pegawai_list"))

        # Parse batas_cuti
        batas_cuti = 12  # Default value
        if data.get("batas_cuti"):
            try:
                batas_cuti = int(data.get("batas_cuti"))
                if batas_cuti < 0 or batas_cuti > 30:
                    if request.is_json:
                        return jsonify(
                            {"success": False, "message": "Batas cuti harus antara 0-30 hari"}
                        ), 400
                    else:
                        from flask import flash, redirect, url_for
                        flash("Batas cuti harus antara 0-30 hari", "error")
                        return redirect(url_for("pegawai.pegawai_list"))
            except ValueError:
                if request.is_json:
                    return jsonify(
                        {"success": False, "message": "Batas cuti harus berupa angka"}
                    ), 400
                else:
                    from flask import flash, redirect, url_for
                    flash("Batas cuti harus berupa angka", "error")
                    return redirect(url_for("pegawai.pegawai_list"))

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
            batas_cuti=batas_cuti,
        )

        db.session.add(pegawai)
        db.session.commit()

        current_app.logger.info(
            f"Pegawai baru ditambahkan: {pegawai.nama} (NIP: {pegawai.nip})"
        )

        if request.is_json:
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
                        "batas_cuti": pegawai.batas_cuti,
                    },
                }
            ), 200
        else:
            from flask import flash, redirect, url_for
            flash(f"Pegawai {pegawai.nama} berhasil ditambahkan", "success")
            return redirect(url_for("pegawai.pegawai_list"))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding pegawai: {str(e)}")
        
        if request.is_json:
            return jsonify(
                {"success": False, "message": "Terjadi kesalahan saat menambahkan pegawai"}
            ), 500
        else:
            from flask import flash, redirect, url_for
            flash("Terjadi kesalahan saat menambahkan pegawai", "error")
            return redirect(url_for("pegawai.pegawai_list"))


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



# API Endpoints for Cuti Form
@pegawai_bp.route("/api/pegawai/search", methods=["GET"])
@login_required
def search_pegawai():
    """Search pegawai by name or NIP for autocomplete"""
    try:
        query = request.args.get("q", "").strip()
        
        if not query:
            return jsonify({
                "success": True,
                "pegawai": [],
                "message": "Query kosong"
            })
        
        if len(query) < 2:
            return jsonify({
                "success": True,
                "pegawai": [],
                "message": "Minimal 2 karakter untuk pencarian"
            })
        
        # Search by name or NIP
        like_pattern = f"%{query}%"
        pegawai_list = Pegawai.query.filter(
            or_(
                Pegawai.nama.ilike(like_pattern),
                Pegawai.nip.ilike(like_pattern)
            )
        ).limit(10).all()
        
        results = []
        for p in pegawai_list:
            results.append({
                "id": p.id,
                "nama": p.nama,
                "nip": p.nip,
                "jabatan": p.jabatan or "-",
                "golongan": p.golongan or "-",
                "batas_cuti": p.batas_cuti if p.batas_cuti is not None else 12,
                "unit_kerja": p.unit_kerja or "-",
                "masa_kerja": p.masa_kerja or "-",
                "nomor_telpon": p.nomor_telpon or ""
            })
        
        return jsonify({
            "success": True,
            "pegawai": results,
            "count": len(results),
            "message": f"Ditemukan {len(results)} pegawai"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error searching pegawai: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Terjadi kesalahan: {str(e)}"
        }), 500


@pegawai_bp.route("/api/pegawai/<int:pegawai_id>", methods=["GET"])
@login_required
def get_pegawai_detail(pegawai_id):
    """Get pegawai detail by ID"""
    try:
        pegawai = Pegawai.query.get(pegawai_id)
        
        if not pegawai:
            return jsonify({
                "success": False,
                "message": "Pegawai tidak ditemukan"
            }), 404
        
        return jsonify({
            "success": True,
            "pegawai": {
                "id": pegawai.id,
                "nama": pegawai.nama,
                "nip": pegawai.nip,
                "jabatan": pegawai.jabatan or "",
                "golongan": pegawai.golongan or "",
                "batas_cuti": pegawai.batas_cuti if pegawai.batas_cuti is not None else 12,
                "unit_kerja": pegawai.unit_kerja or "",
                "masa_kerja": pegawai.masa_kerja or "",
                "nomor_telpon": pegawai.nomor_telpon or "",
                "tanggal_lahir": pegawai.tanggal_lahir.strftime("%Y-%m-%d") if pegawai.tanggal_lahir else "",
                "jenis_kelamin": pegawai.jenis_kelamin or "",
                "agama": pegawai.agama or ""
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting pegawai detail: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Terjadi kesalahan: {str(e)}"
        }), 500


@pegawai_bp.route("/api/pegawai/quota/<nip>", methods=["GET"])
@login_required
def get_pegawai_quota(nip):
    """Get pegawai cuti quota by NIP"""
    try:
        pegawai = Pegawai.query.filter_by(nip=nip).first()
        
        if not pegawai:
            return jsonify({
                "success": False,
                "message": "Pegawai dengan NIP tersebut tidak ditemukan"
            }), 404
        
        return jsonify({
            "success": True,
            "batas_cuti": pegawai.batas_cuti if pegawai.batas_cuti is not None else 12,
            "nama": pegawai.nama,
            "nip": pegawai.nip
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting pegawai quota: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Terjadi kesalahan: {str(e)}"
        }), 500


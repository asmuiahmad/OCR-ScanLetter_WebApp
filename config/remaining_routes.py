"""
Remaining routes
Routes that haven't been categorized yet or are miscellaneous
TODO: Move these routes to appropriate modules
"""

import io
import os
import subprocess
import tempfile
from calendar import monthrange
from collections import defaultdict
from datetime import datetime

import pytesseract
from docx import Document
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required
from mailmerge import MailMerge
from sqlalchemy import asc, desc, extract, func, or_
from werkzeug.utils import secure_filename

from config.extensions import db
from config.models import Pegawai, SuratKeluar, SuratMasuk
from config.ocr_utils import hitung_field_not_found
from config.route_utils import role_required

remaining_bp = Blueprint("remaining", __name__)


# laporan-statistik route moved to config/laporan_routes.py

# generate_cuti route moved to config/cuti_routes.py


@remaining_bp.route("/surat_keluar")
@login_required
def surat_keluar():
    """Surat keluar list"""
    daftar_surat = SuratKeluar.query.all()
    return render_template("surat_keluar/surat_keluar.html", daftar_surat=daftar_surat)


@remaining_bp.route("/test_surat_keluar", methods=["GET"])
def test_surat_keluar():
    """Test surat keluar"""
    try:
        surat_keluar_entries = SuratKeluar.query.paginate(page=1, per_page=20)
        return render_template(
            "surat_keluar/show_surat_keluar.html",
            entries=surat_keluar_entries,
            sort="tanggal_suratKeluar",
            order="asc",
            search="",
        )
    except Exception as e:
        return f"Error: {str(e)}", 500


@remaining_bp.route("/surat-keluar/list", methods=["GET"])
@login_required
@role_required("pimpinan", "admin")
def list_surat_keluar():
    """List surat keluar for approval"""
    try:
        pending_surat_masuk = SuratMasuk.query.filter_by(
            status_suratMasuk="pending"
        ).all()
        pending_surat_masuk_count = len(pending_surat_masuk)

        return render_template(
            "surat_keluar/list_surat_keluar.html",
            pending_surat_masuk=pending_surat_masuk,
            pending_surat_masuk_count=pending_surat_masuk_count,
        )
    except Exception as e:
        current_app.logger.error(f"Error in list_surat_keluar: {str(e)}")
        flash("Terjadi kesalahan saat memuat daftar surat.", "error")
        return redirect(url_for("main.index"))


@remaining_bp.route("/surat-keluar/approve/<int:surat_id>", methods=["POST"])
@login_required
@role_required("pimpinan")
def approve_surat(surat_id):
    """Approve surat"""
    try:
        surat = SuratMasuk.query.get(surat_id)
        if surat:
            surat.status_suratMasuk = "approved"
            db.session.commit()
            return jsonify({"success": True, "message": "Surat berhasil disetujui"})
        else:
            return jsonify({"success": False, "error": "Surat tidak ditemukan"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@remaining_bp.route("/surat-keluar/reject/<int:surat_id>", methods=["POST"])
@login_required
@role_required("pimpinan")
def reject_surat(surat_id):
    """Reject surat"""
    try:
        surat = SuratMasuk.query.get(surat_id)
        if surat:
            surat.status_suratMasuk = "rejected"
            db.session.commit()
            return jsonify({"success": True, "message": "Surat berhasil ditolak"})
        else:
            return jsonify({"success": False, "error": "Surat tidak ditemukan"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@remaining_bp.route("/list-pending-surat-masuk")
@login_required
@role_required("pimpinan")
def list_pending_surat_masuk():
    """List pending surat masuk"""
    try:
        pending_surat_masuk = SuratMasuk.query.filter_by(
            status_suratMasuk="pending"
        ).all()
        return render_template(
            "surat_masuk/list_pending_surat_masuk.html",
            pending_surat_masuk=pending_surat_masuk,
        )
    except Exception as e:
        current_app.logger.error(f"Error in list_pending_surat_masuk: {str(e)}")
        flash("Terjadi kesalahan saat memuat daftar surat pending.", "error")
        return redirect(url_for("main.index"))


@remaining_bp.route("/ocr-test", methods=["GET", "POST"])
@login_required
def ocr_test():
    """OCR test functionality"""
    extracted_text = ""

    if request.method == "POST":
        try:
            if "file" not in request.files:
                flash("No file selected", "error")
                return render_template(
                    "ocr/ocr_test.html",
                    extracted_text=extracted_text,
                    has_error=True,
                    has_success=False,
                )

            file = request.files["file"]
            if file.filename == "":
                flash("No file selected", "error")
                return render_template(
                    "ocr/ocr_test.html",
                    extracted_text=extracted_text,
                    has_error=True,
                    has_success=False,
                )

            if file and file.filename.lower().endswith(
                (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff")
            ):
                try:
                    # Save uploaded file temporarily
                    filename = secure_filename(file.filename)
                    temp_path = os.path.join(tempfile.gettempdir(), filename)
                    file.save(temp_path)

                    # Perform OCR
                    extracted_text = pytesseract.image_to_string(
                        temp_path, lang="ind+eng"
                    )

                    # Clean up
                    os.remove(temp_path)

                    if extracted_text.strip():
                        flash("OCR extraction successful!", "success")
                        return render_template(
                            "ocr/ocr_test.html",
                            extracted_text=extracted_text,
                            has_error=False,
                            has_success=True,
                        )
                    else:
                        flash("No text could be extracted from the image", "warning")
                        return render_template(
                            "ocr/ocr_test.html",
                            extracted_text="No text found",
                            has_error=False,
                            has_success=False,
                        )

                except Exception as ocr_error:
                    current_app.logger.error(f"OCR processing error: {str(ocr_error)}")
                    flash(f"Error processing image: {str(ocr_error)}", "error")
                    return render_template(
                        "ocr/ocr_test.html",
                        extracted_text=extracted_text,
                        has_error=True,
                        has_success=False,
                    )
            else:
                flash(
                    "Please upload a valid image file (PNG, JPG, JPEG, GIF, BMP, TIFF)",
                    "error",
                )
                return render_template(
                    "ocr/ocr_test.html",
                    extracted_text=extracted_text,
                    has_error=True,
                    has_success=False,
                )

        except Exception as e:
            current_app.logger.error(f"OCR test error: {str(e)}")
            flash(f"An error occurred: {str(e)}", "error")
            return render_template(
                "ocr/ocr_test.html",
                extracted_text=extracted_text,
                has_error=True,
                has_success=False,
            )

    return render_template(
        "ocr/ocr_test.html",
        extracted_text=extracted_text,
        has_error=False,
        has_success=False,
    )


@remaining_bp.route("/favicon.ico")
def favicon():
    """Serve favicon"""
    return send_from_directory(
        os.path.join(current_app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )

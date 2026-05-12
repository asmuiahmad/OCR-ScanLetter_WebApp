"""
Cuti routes
Leave/vacation management functionality
"""

import os
import tempfile
from datetime import datetime
from io import BytesIO

import qrcode
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
    url_for,
)
from flask_login import current_user, login_required
from mailmerge import MailMerge

from config.extensions import db
from config.forms import CutiForm, InputCutiForm
from config.models import AuditLog, Cuti, Pegawai, User
from config.pdf_form_generator import CutiFormPDFGenerator
from config.route_utils import role_required

cuti_bp = Blueprint("cuti", __name__)


def _overlap_days(start_a, end_a, start_b, end_b):
    """Return inclusive overlap days between two date ranges."""
    overlap_start = max(start_a, start_b)
    overlap_end = min(end_a, end_b)
    if overlap_start > overlap_end:
        return 0
    return (overlap_end - overlap_start).days + 1


def _used_cuti_days_for_year(nip, year):
    """
    Count used leave days for a NIP in a given year.
    Rejected leaves are excluded.
    """
    year_start = datetime(year, 1, 1).date()
    year_end = datetime(year, 12, 31).date()

    cuti_entries = (
        Cuti.query.filter(
            Cuti.nip == nip,
            Cuti.status_cuti != "rejected",
            Cuti.tanggal_cuti <= year_end,
            Cuti.sampai_cuti >= year_start,
        )
        .all()
    )

    total_days = 0
    for entry in cuti_entries:
        total_days += _overlap_days(
            entry.tanggal_cuti,
            entry.sampai_cuti,
            year_start,
            year_end,
        )
    return total_days


def _validate_yearly_cuti_quota(nip, start_date, end_date, batas_cuti):
    """
    Validate yearly quota across all years touched by requested range.
    Returns list of violations per year.
    """
    violations = []
    for year in range(start_date.year, end_date.year + 1):
        year_start = datetime(year, 1, 1).date()
        year_end = datetime(year, 12, 31).date()

        requested_days_in_year = _overlap_days(start_date, end_date, year_start, year_end)
        if requested_days_in_year <= 0:
            continue

        used_days = _used_cuti_days_for_year(nip, year)
        projected_total = used_days + requested_days_in_year

        if projected_total > batas_cuti:
            violations.append(
                {
                    "year": year,
                    "used_days": used_days,
                    "requested_days": requested_days_in_year,
                    "quota": batas_cuti,
                    "projected_total": projected_total,
                }
            )

    return violations


def create_download_response(file_path, filename, mimetype="application/pdf"):
    """
    Create a proper download response that forces download to Downloads folder
    """
    try:
        # Ensure file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Create response with proper headers for forced download
        response = send_file(
            file_path, as_attachment=True, download_name=filename, mimetype=mimetype
        )

        # Enhanced headers to force download to Downloads folder
        response.headers["Content-Type"] = mimetype
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # Additional headers to ensure proper download behavior
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Transfer-Encoding"] = "binary"

        return response

    except Exception as e:
        current_app.logger.error(f"Error creating download response: {str(e)}")
        raise


def generate_cuti_filename(nama, tanggal_dibuat, file_type="surat_cuti"):
    """
    Generate standardized filename for cuti documents
    Format: surat_cuti_[nama]_[YYYY-MM-DD].pdf

    Args:
        nama (str): Employee name
        tanggal_dibuat (datetime/date): Date when the document was created
        file_type (str): Type of document (default: "surat_cuti")

    Returns:
        str: Formatted filename
    """
    try:
        # Clean the name - remove spaces, special characters, and convert to lowercase
        clean_nama = (
            nama.replace(" ", "_").replace("-", "_").replace(".", "").replace(",", "")
        )
        clean_nama = "".join(c for c in clean_nama if c.isalnum() or c == "_").lower()

        # Format date as YYYY-MM-DD
        if hasattr(tanggal_dibuat, "strftime"):
            date_str = tanggal_dibuat.strftime("%Y-%m-%d")
        else:
            # If it's already a string, try to parse it
            date_str = str(tanggal_dibuat)

        # Generate filename
        filename = f"{file_type}_{clean_nama}_{date_str}.pdf"

        return filename

    except Exception as e:
        # Fallback to simple format if there's an error
        clean_nama = str(nama).replace(" ", "_")
        return f"{file_type}_{clean_nama}.pdf"


@cuti_bp.route("/generate-cuti-direct", methods=["GET", "POST"])
@login_required
def generate_cuti_direct():
    """Generate cuti form directly using HTML template - primary method"""
    form = CutiForm()

    if form.validate_on_submit():
        try:
            # Calculate lama_cuti automatically
            tanggal_mulai = form.tanggal_cuti.data
            tanggal_selesai = form.sampai_cuti.data
            # Guard against None values and unexpected types
            if tanggal_mulai and tanggal_selesai:
                try:
                    lama_cuti_days = (tanggal_selesai - tanggal_mulai).days + 1
                    lama_cuti_str = f"{lama_cuti_days} hari"
                except Exception:
                    # Fallback if subtraction fails
                    lama_cuti_str = ""
            else:
                lama_cuti_str = ""

            # Check yearly leave quota for the employee (quota per year)
            pegawai = Pegawai.query.filter_by(nip=form.nip.data).first()
            batas_cuti = pegawai.batas_cuti if pegawai else 12
            quota_violations = _validate_yearly_cuti_quota(
                form.nip.data,
                tanggal_mulai,
                tanggal_selesai,
                batas_cuti,
            )

            if quota_violations:
                first_violation = quota_violations[0]
                flash(
                    (
                        f"Kuota cuti tahun {first_violation['year']} terlampaui. "
                        f"Kuota: {first_violation['quota']} hari, "
                        f"sudah terpakai: {first_violation['used_days']} hari, "
                        f"permintaan baru: {first_violation['requested_days']} hari "
                        f"(total jadi {first_violation['projected_total']} hari)."
                    ),
                    "error",
                )
                return render_template("cuti/generate_cuti_form.html", form=form)

            # Create new cuti record
            new_cuti = Cuti(
                nama=form.nama.data,
                nip=form.nip.data,
                jabatan=form.jabatan.data,
                gol_ruang=form.gol_ruang.data,
                unit_kerja=form.unit_kerja.data,
                masa_kerja=form.masa_kerja.data,
                alamat=form.alamat.data,
                no_suratmasuk=form.no_suratmasuk.data,
                tgl_ajuan_cuti=form.tgl_ajuan_cuti.data,
                tanggal_cuti=form.tanggal_cuti.data,
                sampai_cuti=form.sampai_cuti.data,
                telp=form.telp.data,
                jenis_cuti=form.jenis_cuti.data,
                alasan_cuti=form.alasan_cuti.data,
                lama_cuti=lama_cuti_str,
                status_cuti="pending",  # Pending approval from pimpinan
            )

            db.session.add(new_cuti)
            db.session.commit()

            # Generate PDF using HTML template (primary method)
            from config.html_template_handler import HtmlTemplateHandler

            template_handler = HtmlTemplateHandler()

            # Generate PDF from HTML template
            result = template_handler.fill_template_and_generate_pdf(new_cuti)

            if result["success"]:
                # Update cuti record with generated files info
                new_cuti.qr_code = result["signature_hash"]
                new_cuti.pdf_path = result["pdf_path"]
                db.session.commit()

                # Return PDF file for download
                return send_file(
                    result["pdf_path"],
                    as_attachment=True,
                    download_name=f"surat_cuti_{new_cuti.nama.replace(' ', '_')}_{new_cuti.id_cuti}.pdf",
                    mimetype="application/pdf",
                )
            else:
                flash(
                    f"Error: Tidak dapat menghasilkan PDF - {result['error']}", "error"
                )
                current_app.logger.error(
                    f"PDF generation failed for cuti ID: {new_cuti.id_cuti} - {result['error']}"
                )

                # Still commit the cuti record but redirect to list
                db.session.commit()
                flash(
                    "Data cuti berhasil disimpan, namun terjadi error saat generate PDF",
                    "warning",
                )
                return redirect(url_for("cuti.list_cuti"))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating cuti: {str(e)}")
            flash(f"Error creating cuti form: {str(e)}", "error")

    return render_template("cuti/generate_cuti_form.html", form=form)


@cuti_bp.route("/generate-cuti-html", methods=["GET", "POST"])
@login_required
def generate_cuti_html():
    """Generate cuti form using HTML template and PDF"""
    form = CutiForm()

    if form.validate_on_submit():
        try:
            # Calculate lama_cuti automatically
            tanggal_mulai = form.tanggal_cuti.data
            tanggal_selesai = form.sampai_cuti.data
            # Guard against None values and unexpected types
            if tanggal_mulai and tanggal_selesai:
                try:
                    lama_cuti_days = (tanggal_selesai - tanggal_mulai).days + 1
                    lama_cuti_str = f"{lama_cuti_days} hari"
                except Exception:
                    # Fallback if subtraction fails
                    lama_cuti_str = ""
            else:
                lama_cuti_str = ""

            # Check yearly leave quota for the employee (quota per year)
            pegawai = Pegawai.query.filter_by(nip=form.nip.data).first()
            batas_cuti = pegawai.batas_cuti if pegawai else 12
            quota_violations = _validate_yearly_cuti_quota(
                form.nip.data,
                tanggal_mulai,
                tanggal_selesai,
                batas_cuti,
            )

            if quota_violations:
                first_violation = quota_violations[0]
                flash(
                    (
                        f"Kuota cuti tahun {first_violation['year']} terlampaui. "
                        f"Kuota: {first_violation['quota']} hari, "
                        f"sudah terpakai: {first_violation['used_days']} hari, "
                        f"permintaan baru: {first_violation['requested_days']} hari "
                        f"(total jadi {first_violation['projected_total']} hari)."
                    ),
                    "error",
                )
                return render_template("cuti/generate_cuti_form.html", form=form)

            # Create new cuti record
            new_cuti = Cuti(
                nama=form.nama.data,
                nip=form.nip.data,
                jabatan=form.jabatan.data,
                gol_ruang=form.gol_ruang.data,
                unit_kerja=form.unit_kerja.data,
                masa_kerja=form.masa_kerja.data,
                alamat=form.alamat.data,
                no_suratmasuk=form.no_suratmasuk.data,
                tgl_ajuan_cuti=form.tgl_ajuan_cuti.data,
                tanggal_cuti=form.tanggal_cuti.data,
                sampai_cuti=form.sampai_cuti.data,
                telp=form.telp.data,
                jenis_cuti=form.jenis_cuti.data,
                alasan_cuti=form.alasan_cuti.data,
                lama_cuti=lama_cuti_str,
                status_cuti="pending",  # Pending approval from pimpinan
            )

            db.session.add(new_cuti)
            db.session.commit()

            # Generate PDF using HTML template
            from config.html_template_handler import HtmlTemplateHandler

            template_handler = HtmlTemplateHandler()

            # Generate PDF from HTML template
            result = template_handler.fill_template_and_generate_pdf(new_cuti)

            if result["success"]:
                # Update cuti record with generated files info
                new_cuti.qr_code = result["signature_hash"]
                new_cuti.pdf_path = result["pdf_path"]
                db.session.commit()

                # Return PDF file for download
                return send_file(
                    result["pdf_path"],
                    as_attachment=True,
                    download_name=f"surat_cuti_{new_cuti.nama.replace(' ', '_')}_{new_cuti.id_cuti}.pdf",
                    mimetype="application/pdf",
                )
            else:
                flash(
                    f"Error: Tidak dapat menghasilkan PDF - {result['error']}", "error"
                )
                current_app.logger.error(
                    f"PDF generation failed for cuti ID: {new_cuti.id_cuti} - {result['error']}"
                )

                # Still commit the cuti record but redirect to list
                db.session.commit()
                flash(
                    "Data cuti berhasil disimpan, namun terjadi error saat generate PDF",
                    "warning",
                )
                return redirect(url_for("cuti.list_cuti"))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating cuti: {str(e)}")
            flash(f"Error creating cuti form: {str(e)}", "error")

    return render_template("cuti/generate_cuti_form.html", form=form)


@cuti_bp.route("/generate-cuti", methods=["GET", "POST"])
@login_required
def generate_cuti():
    """Generate cuti form and PDF"""
    form = CutiForm()

    # Handle POST request - let Flask-WTF handle CSRF automatically
    if request.method == "POST":
        # Check if form is valid (this includes CSRF validation)
        if not form.validate():
            # Log validation errors for debugging
            current_app.logger.warning(f"Form validation failed: {form.errors}")
            
            # Check if it's a CSRF error
            if "csrf_token" in form.errors:
                flash(
                    "Token keamanan tidak valid atau telah kedaluwarsa. Silakan refresh halaman dan coba lagi.",
                    "error",
                )
            else:
                # Handle other validation errors with more user-friendly messages
                error_messages = []
                for field, errors in form.errors.items():
                    field_name = {
                        'nama': 'Nama',
                        'nip': 'NIP', 
                        'jabatan': 'Jabatan',
                        'gol_ruang': 'Golongan/Ruang',
                        'unit_kerja': 'Unit Kerja',
                        'masa_kerja': 'Masa Kerja',
                        'alamat': 'Alamat',
                        'no_suratmasuk': 'Nomor Surat Masuk',
                        'tgl_ajuan_cuti': 'Tanggal Ajuan Cuti',
                        'tanggal_cuti': 'Tanggal Mulai Cuti',
                        'sampai_cuti': 'Tanggal Selesai Cuti',
                        'telp': 'Nomor Telepon',
                        'jenis_cuti': 'Jenis Cuti',
                        'alasan_cuti': 'Alasan Cuti'
                    }.get(field, field)
                    
                    for error in errors:
                        if error == "This field is required.":
                            error_messages.append(f"{field_name} harus diisi")
                        else:
                            error_messages.append(f"{field_name}: {error}")
                
                # Flash all error messages
                for msg in error_messages:
                    flash(msg, "error")
                    
            return render_template("cuti/generate_cuti_form.html", form=form)

    if form.validate_on_submit():
        try:
            # Calculate lama_cuti automatically
            tanggal_mulai = form.tanggal_cuti.data
            tanggal_selesai = form.sampai_cuti.data
            # Guard against None values and unexpected types
            if tanggal_mulai and tanggal_selesai:
                try:
                    lama_cuti_days = (tanggal_selesai - tanggal_mulai).days + 1
                    lama_cuti_str = f"{lama_cuti_days} hari"
                except Exception:
                    # Fallback if subtraction fails
                    lama_cuti_str = ""
            else:
                lama_cuti_str = ""

            # Check yearly leave quota for the employee (quota per year)
            pegawai = Pegawai.query.filter_by(nip=form.nip.data).first()
            batas_cuti = pegawai.batas_cuti if pegawai else 12
            quota_violations = _validate_yearly_cuti_quota(
                form.nip.data,
                tanggal_mulai,
                tanggal_selesai,
                batas_cuti,
            )

            if quota_violations:
                first_violation = quota_violations[0]
                flash(
                    (
                        f"Kuota cuti tahun {first_violation['year']} terlampaui. "
                        f"Kuota: {first_violation['quota']} hari, "
                        f"sudah terpakai: {first_violation['used_days']} hari, "
                        f"permintaan baru: {first_violation['requested_days']} hari "
                        f"(total jadi {first_violation['projected_total']} hari)."
                    ),
                    "error",
                )
                return render_template("cuti/generate_cuti_form.html", form=form)

            # Create new cuti record
            new_cuti = Cuti(
                nama=form.nama.data,
                nip=form.nip.data,
                jabatan=form.jabatan.data,
                gol_ruang=form.gol_ruang.data,
                unit_kerja=form.unit_kerja.data,
                masa_kerja=form.masa_kerja.data,
                alamat=form.alamat.data,
                no_suratmasuk=form.no_suratmasuk.data,
                tgl_ajuan_cuti=form.tgl_ajuan_cuti.data,
                tanggal_cuti=form.tanggal_cuti.data,
                sampai_cuti=form.sampai_cuti.data,
                telp=form.telp.data,
                jenis_cuti=form.jenis_cuti.data,
                alasan_cuti=form.alasan_cuti.data,
                lama_cuti=lama_cuti_str,
                status_cuti="pending",  # Pending approval from pimpinan
            )

            db.session.add(new_cuti)
            db.session.commit()

            # Prioritize HTML template first (most reliable for PDF generation)
            result = None

            # Method 1: HTML Template (primary - always produces a PDF)
            try:
                from config.html_template_handler import HtmlTemplateHandler

                template_handler = HtmlTemplateHandler()
                current_app.logger.info(
                    f"Attempting PDF generation for cuti ID: {new_cuti.id_cuti}"
                )
                result = template_handler.fill_template_and_generate_pdf(new_cuti)
                if result and result.get("success"):
                    current_app.logger.info(
                        f"✅ HTML template successful - PDF at: {result.get('pdf_path')}"
                    )
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                    current_app.logger.warning(
                        f"HTML template returned failure: {error_msg}"
                    )
            except Exception as html_error:
                current_app.logger.error(f"HTML template failed: {str(html_error)}")
                import traceback
                current_app.logger.error(traceback.format_exc())

            # Method 2: Advanced DOCX Template (fallback - only if PDF conversion succeeds)
            if not result or not result.get("success"):
                try:
                    from config.docx_template_advanced import (
                        AdvancedDocxTemplateHandler,
                    )

                    template_handler = AdvancedDocxTemplateHandler()
                    result = template_handler.fill_template_and_generate_pdf(new_cuti)
                    if result and result.get("success"):
                        # Verify that the result is actually a PDF file
                        pdf_path = result.get("pdf_path", "")
                        if (
                            pdf_path
                            and pdf_path.endswith(".pdf")
                            and os.path.exists(pdf_path)
                        ):
                            current_app.logger.info("✅ Advanced DOCX template successful")
                        else:
                            # If not PDF, mark as failed and try next method
                            result = None
                            current_app.logger.warning("Advanced DOCX template returned non-PDF file")
                except Exception as advanced_error:
                    current_app.logger.error(f"Advanced DOCX template failed: {str(advanced_error)}")
                    import traceback
                    current_app.logger.error(traceback.format_exc())

            # Method 3: Basic DOCX Template (last resort - only if PDF conversion succeeds)
            if not result or not result.get("success"):
                try:
                    from config.docx_template_handler import DocxTemplateHandler

                    template_handler = DocxTemplateHandler()
                    result = template_handler.fill_template_and_generate_pdf(new_cuti)
                    if result and result.get("success"):
                        # Verify that the result is actually a PDF file
                        pdf_path = result.get("pdf_path", "")
                        if (
                            pdf_path
                            and pdf_path.endswith(".pdf")
                            and os.path.exists(pdf_path)
                        ):
                            current_app.logger.info("✅ Basic DOCX template successful")
                        else:
                            result = {
                                "success": False,
                                "error": "PDF conversion failed",
                            }
                            current_app.logger.warning("Basic DOCX template returned non-PDF file")
                except Exception as docx_error:
                    current_app.logger.error(f"Basic DOCX template failed: {str(docx_error)}")
                    import traceback
                    current_app.logger.error(traceback.format_exc())
                    result = {"success": False, "error": "All template methods failed"}

            if result and result.get("success"):
                pdf_path = result.get("pdf_path", "")

                # Verify file is actually a PDF
                if not pdf_path or not pdf_path.endswith(".pdf"):
                    flash("Error: File yang dihasilkan bukan PDF", "error")
                    current_app.logger.error(f"Generated file is not PDF: {pdf_path}")
                    db.session.commit()
                    return redirect(url_for("cuti.list_cuti"))

                if not os.path.exists(pdf_path):
                    flash("Error: File PDF tidak ditemukan", "error")
                    current_app.logger.error(f"PDF file not found: {pdf_path}")
                    db.session.commit()
                    return redirect(url_for("cuti.list_cuti"))

                # Update cuti record with generated files info
                new_cuti.qr_code = result.get("signature_hash", "")
                new_cuti.pdf_path = pdf_path
                db.session.commit()

                # Convert to absolute path for send_file
                if not os.path.isabs(pdf_path):
                    # Try relative to app root first
                    abs_path1 = os.path.join(current_app.root_path, pdf_path)
                    # Try relative to project root
                    abs_path2 = os.path.abspath(pdf_path)
                    # Use whichever exists
                    if os.path.exists(abs_path1):
                        pdf_path = abs_path1
                    elif os.path.exists(abs_path2):
                        pdf_path = abs_path2
                    else:
                        # Fallback to absolute path
                        pdf_path = os.path.abspath(pdf_path)

                # Return PDF file for download with enhanced headers
                try:
                    current_app.logger.info(f"Sending PDF file: {pdf_path}")
                    filename = generate_cuti_filename(
                        new_cuti.nama, new_cuti.tgl_ajuan_cuti
                    )
                    return create_download_response(pdf_path, filename)
                except Exception as send_error:
                    current_app.logger.error(
                        f"Error sending PDF file: {str(send_error)}"
                    )
                    import traceback

                    current_app.logger.error(traceback.format_exc())
                    flash("Error: Gagal mengirim file PDF", "error")
                    return redirect(url_for("cuti.list_cuti"))
            else:
                error_msg = (
                    result.get("error", "Unknown error")
                    if result
                    else "PDF generation failed - no result returned"
                )
                current_app.logger.error(
                    f"PDF generation failed for cuti ID: {new_cuti.id_cuti} - {error_msg}"
                )
                
                # Flash detailed error message to user
                flash(f"Gagal membuat PDF: {error_msg}", "error")

                # Still commit the cuti record but redirect to list
                db.session.commit()
                flash(
                    "Data cuti berhasil disimpan, namun terjadi error saat generate PDF. Silakan coba download dari daftar cuti.",
                    "warning",
                )
                return redirect(url_for("cuti.list_cuti"))

        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            current_app.logger.error(f"Error creating cuti: {error_msg}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            
            # Provide more specific error messages
            if "IntegrityError" in error_msg:
                flash("Terjadi kesalahan: Data yang sama sudah ada dalam sistem", "error")
            elif "OperationalError" in error_msg:
                flash("Terjadi kesalahan koneksi database. Silakan coba lagi dalam beberapa saat", "error")
            elif "DataError" in error_msg:
                flash("Terjadi kesalahan: Format data tidak valid", "error")
            else:
                flash(f"Terjadi kesalahan saat menyimpan data: {error_msg}", "error")
                
            return render_template("cuti/generate_cuti_form.html", form=form)

    return render_template("cuti/generate_cuti_form.html", form=form)


@cuti_bp.route("/input-cuti", methods=["GET", "POST"])
@login_required
@role_required("admin")
def input_cuti():
    """Input cuti form"""
    form = InputCutiForm()

    if form.validate_on_submit():
        try:
            # Calculate lama_cuti automatically
            tanggal_mulai = form.tanggal_cuti.data
            tanggal_selesai = form.sampai_cuti.data
            # Guard against None values and unexpected types
            if tanggal_mulai and tanggal_selesai:
                try:
                    lama_cuti_days = (tanggal_selesai - tanggal_mulai).days + 1
                    lama_cuti_str = f"{lama_cuti_days} hari"
                except Exception:
                    # Fallback if subtraction fails
                    lama_cuti_str = ""
            else:
                lama_cuti_str = ""

            pegawai = Pegawai.query.filter_by(nip=form.nip.data).first()
            batas_cuti = pegawai.batas_cuti if pegawai else 12
            quota_violations = _validate_yearly_cuti_quota(
                form.nip.data,
                tanggal_mulai,
                tanggal_selesai,
                batas_cuti,
            )

            if quota_violations:
                first_violation = quota_violations[0]
                flash(
                    (
                        f"Kuota cuti tahun {first_violation['year']} terlampaui. "
                        f"Kuota: {first_violation['quota']} hari, "
                        f"sudah terpakai: {first_violation['used_days']} hari, "
                        f"permintaan baru: {first_violation['requested_days']} hari "
                        f"(total jadi {first_violation['projected_total']} hari)."
                    ),
                    "error",
                )
                return render_template("cuti/input_cuti.html", form=form)

            new_cuti = Cuti(
                nama=form.nama.data,
                nip=form.nip.data,
                jabatan=form.jabatan.data,
                gol_ruang=form.gol_ruang.data,
                unit_kerja=form.unit_kerja.data,
                masa_kerja=form.masa_kerja.data,
                alamat=form.alamat.data,
                no_suratmasuk=form.no_suratmasuk.data,
                tgl_ajuan_cuti=form.tgl_ajuan_cuti.data,
                tanggal_cuti=form.tanggal_cuti.data,
                sampai_cuti=form.sampai_cuti.data,
                telp=form.telp.data,
                jenis_cuti=form.jenis_cuti.data,
                alasan_cuti=form.alasan_cuti.data,
                lama_cuti=lama_cuti_str,
                status_cuti="pending",
            )

            db.session.add(new_cuti)
            db.session.commit()

            flash("Data cuti berhasil disimpan!", "success")
            return redirect(url_for("cuti.list_cuti"))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving cuti: {str(e)}")
            flash(f"Error saving cuti: {str(e)}", "error")

    return render_template("cuti/input_cuti.html", form=form)


@cuti_bp.route("/list-cuti")
@login_required
@role_required("admin", "pimpinan")
def list_cuti():
    """List all cuti applications with pagination and search"""
    try:
        # Get page number and search query from query parameters
        page = request.args.get("page", 1, type=int)
        search_query = request.args.get("search", "", type=str).strip()
        per_page = 20
        
        # Build base query
        query = Cuti.query
        
        # Apply search filter if provided
        if search_query:
            search_filter = f"%{search_query}%"
            query = query.filter(
                (Cuti.nama.ilike(search_filter)) |
                (Cuti.nip.ilike(search_filter)) |
                (Cuti.jenis_cuti.ilike(search_filter))
            )
        
        # Query with pagination
        entries = query.order_by(Cuti.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Annotate each cuti with an `approved_role` attribute so templates/JS can
        # clearly display whether approval came from a 'pimpinan' or 'admin'.
        # We attach the attribute directly to the model instances (safe for read-only use).
        for c in entries.items:
            c.approved_role = None
            if c.approved_by:
                try:
                    approver = User.query.filter_by(email=c.approved_by).first()
                    if approver and getattr(approver, "role", None):
                        c.approved_role = approver.role
                except Exception:
                    # Defensive: if lookup fails, leave approved_role as None
                    c.approved_role = None

        return render_template("cuti/list_cuti.html", entries=entries, search_query=search_query)
    except Exception as e:
        # Log full exception with traceback for debugging
        current_app.logger.error(f"Error loading cuti list: {str(e)}", exc_info=True)

        # Detect AJAX/SPA/JSON requests and return JSON so SPA can display an error
        accept = request.headers.get("Accept", "") or ""
        xreq = request.headers.get("X-Requested-With", "") or ""
        wants_json = (
            xreq == "XMLHttpRequest"
            or "application/json" in accept.lower()
            or request.is_json
        )

        if wants_json:
            return jsonify(
                {
                    "success": False,
                    "message": "Gagal memuat daftar cuti",
                    "error": str(e),
                }
            ), 500

        # Fallback for normal browser navigation: flash and redirect to main index
        flash("Error loading cuti list", "error")
        return redirect(url_for("main.index"))


@cuti_bp.route("/audit-logs")
@login_required
@role_required("admin", "pimpinan")
def audit_logs():
    """Admin view: return recent audit logs (JSON) for verification"""
    try:
        # Return the most recent 200 audit entries for quick verification in UI or API clients
        logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
        logs_data = [log.to_dict() for log in logs]
        return jsonify({"success": True, "logs": logs_data}), 200
    except Exception as e:
        current_app.logger.error(f"Error loading audit logs: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Gagal memuat audit logs"}), 500


@cuti_bp.route("/approve-cuti/<int:cuti_id>", methods=["POST"])
@login_required
@role_required("admin", "pimpinan")
def approve_cuti(cuti_id):
    """Approve cuti application (accepts JSON/form and returns JSON for AJAX)"""
    try:
        # Debug logging to help trace permission/session issues
        current_app.logger.debug(
            f"approve_cuti called: user={getattr(current_user, 'email', None)} role={getattr(current_user, 'role', None)} cuti_id={cuti_id}"
        )

        cuti = Cuti.query.get_or_404(cuti_id)

        # Accept JSON body or form data
        data = request.get_json(silent=True) or request.form
        current_app.logger.debug(f"approve_cuti payload: {data}")
        notes = data.get("notes") if hasattr(data, "get") else None

        cuti.status_cuti = "approved"
        cuti.approved_by = current_user.email
        cuti.approved_at = datetime.utcnow()
        if notes:
            cuti.notes = notes
        # Reset cached PDF so it gets regenerated with approval info
        cuti.pdf_path = None

        db.session.commit()

        # Create an AuditLog entry using the SQLAlchemy model (clean, transactional)
        try:
            from config.models import AuditLog

            audit = AuditLog(
                entity_type="cuti",
                entity_id=cuti.id_cuti,
                action="approve",
                performed_by=getattr(current_user, "email", None),
                notes=notes or None,
            )
            db.session.add(audit)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Failed to write audit log for approve: {e}", exc_info=True
            )

        return jsonify(
            {
                "success": True,
                "message": f"Cuti untuk {cuti.nama} telah disetujui",
                "cuti_id": cuti.id_cuti,
                "status": cuti.status_cuti,
            }
        ), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error approving cuti {cuti_id}: {str(e)}", exc_info=True
        )
        return jsonify(
            {"success": False, "message": "Error approving cuti", "error": str(e)}
        ), 500


@cuti_bp.route("/reject-cuti/<int:cuti_id>", methods=["POST"])
@login_required
@role_required("admin", "pimpinan")
def reject_cuti(cuti_id):
    """Reject cuti application (accepts JSON/form and returns JSON for AJAX)"""
    try:
        # Debug logging to help trace permission/session issues
        current_app.logger.debug(
            f"reject_cuti called: user={getattr(current_user, 'email', None)} role={getattr(current_user, 'role', None)} cuti_id={cuti_id}"
        )

        cuti = Cuti.query.get_or_404(cuti_id)

        # Accept JSON body or form data
        data = request.get_json(silent=True) or request.form
        current_app.logger.debug(f"reject_cuti payload: {data}")
        notes = data.get("notes", "") if hasattr(data, "get") else ""

        cuti.status_cuti = "rejected"
        cuti.notes = notes
        # Reset cached PDF so it gets regenerated with rejection info
        cuti.pdf_path = None

        db.session.commit()

        # Create an AuditLog entry using the SQLAlchemy model (clean, transactional)
        try:
            from config.models import AuditLog

            audit = AuditLog(
                entity_type="cuti",
                entity_id=cuti.id_cuti,
                action="reject",
                performed_by=getattr(current_user, "email", None),
                notes=notes or None,
            )
            db.session.add(audit)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Failed to write audit log for reject: {e}", exc_info=True
            )

        return jsonify(
            {
                "success": True,
                "message": f"Cuti untuk {cuti.nama} telah ditolak",
                "cuti_id": cuti.id_cuti,
                "status": cuti.status_cuti,
            }
        ), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error rejecting cuti {cuti_id}: {str(e)}", exc_info=True
        )
        return jsonify(
            {"success": False, "message": "Error rejecting cuti", "error": str(e)}
        ), 500


@cuti_bp.route("/delete-cuti/<int:cuti_id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_cuti(cuti_id):
    """Delete cuti application"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)
        nama_cuti = cuti.nama

        # Delete associated files if they exist
        if cuti.pdf_path and os.path.exists(cuti.pdf_path):
            os.remove(cuti.pdf_path)

        db.session.delete(cuti)
        db.session.commit()

        flash(f"Data cuti {nama_cuti} berhasil dihapus", "success")
        return redirect(url_for("cuti.list_cuti"))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting cuti {cuti_id}: {str(e)}")
        flash("Error deleting cuti", "error")
        return redirect(url_for("cuti.list_cuti"))


@cuti_bp.route("/bulk-approve", methods=["POST"])
@login_required
@role_required("admin", "pimpinan")
def bulk_approve_cuti():
    """Bulk approve multiple cuti applications"""
    try:
        # Log raw request data
        current_app.logger.info(f"=== BULK APPROVE REQUEST ===")
        current_app.logger.info(f"User: {current_user.email}, Role: {current_user.role}")
        current_app.logger.info(f"Request method: {request.method}")
        current_app.logger.info(f"Request content type: {request.content_type}")
        
        # Try to get cuti_ids from form array notation first
        cuti_ids = request.form.getlist('cuti_ids[]')
        current_app.logger.info(f"Extracted cuti_ids from form array: {cuti_ids}")
        
        # If not found, try other methods
        if not cuti_ids:
            # Try JSON
            if request.is_json:
                json_data = request.get_json()
                current_app.logger.info(f"JSON data: {json_data}")
                cuti_ids = json_data.get("cuti_ids", []) if json_data else []
            
            # Try form data with JSON string
            if not cuti_ids:
                cuti_ids_str = request.form.get("cuti_ids")
                if cuti_ids_str:
                    try:
                        import json
                        cuti_ids = json.loads(cuti_ids_str)
                        current_app.logger.info(f"Parsed from JSON string: {cuti_ids}")
                    except:
                        pass
        
        current_app.logger.info(f"Final cuti_ids: {cuti_ids} (type: {type(cuti_ids).__name__}, length: {len(cuti_ids)})")
        
        if not cuti_ids or len(cuti_ids) == 0:
            current_app.logger.warning(f"No cuti IDs provided for bulk approve")
            flash("Pilih minimal 1 cuti untuk disetujui", "warning")
            return redirect(url_for("cuti.list_cuti"))
        
        approved_count = 0
        failed_count = 0
        approved_ids = []
        failed_ids = []
        
        for cuti_id in cuti_ids:
            try:
                current_app.logger.info(f"Processing approve for cuti ID: {cuti_id} (type: {type(cuti_id)})")
                
                # Ensure cuti_id is integer
                cuti_id_int = int(cuti_id)
                current_app.logger.info(f"Converted cuti_id to int: {cuti_id_int}")
                
                cuti = Cuti.query.get(cuti_id_int)
                current_app.logger.info(f"Query result for cuti {cuti_id_int}: {cuti}")
                
                if cuti and cuti.status_cuti == "pending":
                    current_app.logger.info(f"Found pending cuti {cuti_id_int}: {cuti.nama}")
                    
                    cuti.status_cuti = "approved"
                    cuti.approved_by = current_user.email
                    cuti.approved_at = datetime.utcnow()
                    
                    # Log the action
                    audit_log = AuditLog(
                        user_email=current_user.email,
                        action="approve_cuti",
                        table_name="cuti",
                        record_id=cuti_id_int,
                        details=f"Bulk approved cuti for {cuti.nama}",
                    )
                    db.session.add(audit_log)
                    approved_count += 1
                    approved_ids.append(cuti_id_int)
                    current_app.logger.info(f"Marked cuti {cuti_id_int} for approval")
                else:
                    if not cuti:
                        current_app.logger.warning(f"Cuti {cuti_id_int} not found in database")
                    else:
                        current_app.logger.warning(f"Cuti {cuti_id_int} status is not pending: {cuti.status_cuti}")
                    failed_count += 1
                    failed_ids.append(cuti_id_int)
                    
            except ValueError as ve:
                current_app.logger.error(f"Error converting cuti_id {cuti_id} to int: {str(ve)}")
                failed_count += 1
                failed_ids.append(cuti_id)
                continue
            except Exception as e:
                current_app.logger.error(f"Error approving cuti {cuti_id}: {str(e)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
                failed_count += 1
                failed_ids.append(cuti_id)
                continue
        
        current_app.logger.info(f"Before commit - approved_count: {approved_count}, failed_count: {failed_count}")
        current_app.logger.info(f"Approved IDs: {approved_ids}, Failed IDs: {failed_ids}")
        
        # Commit all approvals at once
        try:
            db.session.commit()
            current_app.logger.info(f"✓ Bulk approve committed successfully: {approved_count} approved, {failed_count} failed")
            flash(f"✓ {approved_count} permohonan cuti berhasil disetujui", "success")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"✗ Error committing bulk approve: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            flash(f"✗ Error: {str(e)}", "error")
        
        return redirect(url_for("cuti.list_cuti"))
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in bulk_approve_cuti: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("cuti.list_cuti"))


@cuti_bp.route("/bulk-delete", methods=["POST"])
@login_required
@role_required("admin")
def bulk_delete_cuti():
    """Bulk delete multiple cuti applications"""
    try:
        current_app.logger.info(f"=== BULK DELETE REQUEST ===")
        current_app.logger.info(f"User: {current_user.email}, Role: {current_user.role}")
        current_app.logger.info(f"Request method: {request.method}")
        current_app.logger.info(f"Request content type: {request.content_type}")
        current_app.logger.info(f"Request form: {dict(request.form)}")
        current_app.logger.info(f"Request form lists: {request.form.lists()}")
        
        # Get cuti_ids from form array notation
        cuti_ids = request.form.getlist('cuti_ids[]')
        current_app.logger.info(f"Extracted cuti_ids from form array: {cuti_ids}")
        
        # If not found, try other methods
        if not cuti_ids:
            # Try JSON
            if request.is_json:
                json_data = request.get_json()
                current_app.logger.info(f"JSON data: {json_data}")
                cuti_ids = json_data.get("cuti_ids", []) if json_data else []
            
            # Try form data with JSON string
            if not cuti_ids:
                cuti_ids_str = request.form.get("cuti_ids")
                if cuti_ids_str:
                    try:
                        import json
                        cuti_ids = json.loads(cuti_ids_str)
                        current_app.logger.info(f"Parsed from JSON string: {cuti_ids}")
                    except:
                        pass
        
        current_app.logger.info(f"Final cuti_ids: {cuti_ids} (type: {type(cuti_ids).__name__}, length: {len(cuti_ids)})")
        
        if not cuti_ids or len(cuti_ids) == 0:
            current_app.logger.warning(f"No cuti IDs provided for bulk delete")
            flash("Pilih minimal 1 cuti untuk dihapus", "warning")
            return redirect(url_for("cuti.list_cuti"))
        
        deleted_count = 0
        failed_count = 0
        deleted_ids = []
        failed_ids = []
        
        for cuti_id in cuti_ids:
            try:
                current_app.logger.info(f"Processing delete for cuti ID: {cuti_id} (type: {type(cuti_id)})")
                
                # Ensure cuti_id is integer
                cuti_id_int = int(cuti_id)
                current_app.logger.info(f"Converted cuti_id to int: {cuti_id_int}")
                
                cuti = Cuti.query.get(cuti_id_int)
                current_app.logger.info(f"Query result for cuti {cuti_id_int}: {cuti}")
                
                if cuti:
                    current_app.logger.info(f"Found cuti {cuti_id_int}: {cuti.nama}")
                    
                    # Log the action before deletion
                    audit_log = AuditLog(
                        user_email=current_user.email,
                        action="delete_cuti",
                        table_name="cuti",
                        record_id=cuti_id_int,
                        details=f"Bulk deleted cuti for {cuti.nama}",
                    )
                    db.session.add(audit_log)
                    
                    # Delete associated PDF file if exists
                    if cuti.pdf_path and os.path.exists(cuti.pdf_path):
                        try:
                            os.remove(cuti.pdf_path)
                            current_app.logger.info(f"Deleted PDF file: {cuti.pdf_path}")
                        except Exception as e:
                            current_app.logger.warning(f"Could not delete PDF file: {str(e)}")
                    
                    db.session.delete(cuti)
                    deleted_count += 1
                    deleted_ids.append(cuti_id_int)
                    current_app.logger.info(f"Marked cuti {cuti_id_int} for deletion")
                else:
                    current_app.logger.warning(f"Cuti {cuti_id_int} not found in database")
                    failed_count += 1
                    failed_ids.append(cuti_id_int)
                    
            except ValueError as ve:
                current_app.logger.error(f"Error converting cuti_id {cuti_id} to int: {str(ve)}")
                failed_count += 1
                failed_ids.append(cuti_id)
                continue
            except Exception as e:
                current_app.logger.error(f"Error deleting cuti {cuti_id}: {str(e)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
                failed_count += 1
                failed_ids.append(cuti_id)
                continue
        
        current_app.logger.info(f"Before commit - deleted_count: {deleted_count}, failed_count: {failed_count}")
        current_app.logger.info(f"Deleted IDs: {deleted_ids}, Failed IDs: {failed_ids}")
        
        # Commit all deletions at once
        try:
            db.session.commit()
            current_app.logger.info(f"✓ Bulk delete committed successfully: {deleted_count} deleted, {failed_count} failed")
            flash(f"✓ {deleted_count} permohonan cuti berhasil dihapus", "success")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"✗ Error committing bulk delete: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            flash(f"✗ Error: {str(e)}", "error")
        
        return redirect(url_for("cuti.list_cuti"))
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in bulk_delete_cuti: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("cuti.list_cuti"))


@cuti_bp.route("/detail/<int:cuti_id>")
@login_required
def detail_cuti(cuti_id):
    """Get cuti detail as JSON"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)

        # Resolve approver role if an approver email exists
        approved_role = None
        if cuti.approved_by:
            approver = User.query.filter_by(email=cuti.approved_by).first()
            if approver:
                approved_role = approver.role

        cuti_data = {
            "id_cuti": cuti.id_cuti,
            "nama": cuti.nama,
            "nip": cuti.nip,
            "jabatan": cuti.jabatan,
            "gol_ruang": cuti.gol_ruang,
            "unit_kerja": cuti.unit_kerja,
            "masa_kerja": cuti.masa_kerja,
            "alamat": cuti.alamat,
            "telp": cuti.telp,
            "jenis_cuti": cuti.jenis_cuti,
            "alasan_cuti": cuti.alasan_cuti,
            "lama_cuti": cuti.lama_cuti,
            "tanggal_cuti": cuti.tanggal_cuti.strftime("%d/%m/%Y"),
            "sampai_cuti": cuti.sampai_cuti.strftime("%d/%m/%Y"),
            "tgl_ajuan_cuti": cuti.tgl_ajuan_cuti.strftime("%d/%m/%Y"),
            "status_cuti": cuti.status_cuti,
            "approved_by": cuti.approved_by,
            "approved_role": approved_role,
            "approved_at": cuti.approved_at.strftime("%d/%m/%Y %H:%M")
            if cuti.approved_at
            else None,
            "notes": cuti.notes,
        }

        return {"success": True, "cuti": cuti_data}

    except Exception as e:
        current_app.logger.error(f"Error getting cuti detail {cuti_id}: {str(e)}")
        return {"success": False, "message": str(e)}


@cuti_bp.route("/preview-cuti-html/<int:cuti_id>")
@login_required
def preview_cuti_html(cuti_id):
    """Preview HTML template with filled data"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)

        from config.html_template_handler import HtmlTemplateHandler

        template_handler = HtmlTemplateHandler()

        # Check if template exists
        if not os.path.exists(template_handler.template_path):
            flash("Template HTML tidak ditemukan", "error")
            return redirect(url_for("cuti.list_cuti"))

        # Generate signature hash for preview
        signature_hash = template_handler.generate_signature_hash(cuti)

        # Read HTML template
        with open(template_handler.template_path, "r", encoding="utf-8") as file:
            html_content = file.read()

        # Replace placeholders
        html_content = template_handler.replace_placeholders_in_html(
            html_content, cuti, signature_hash
        )

        # Add preview notice
        preview_notice = """
        <div style="position: fixed; top: 0; left: 0; right: 0; background: #ff9800; color: white; padding: 10px; text-align: center; z-index: 1000;">
            <strong>PREVIEW MODE</strong> - Ini adalah preview template HTML.
            <a href="javascript:window.close()" style="color: white; text-decoration: underline;">Tutup</a>
        </div>
        <div style="margin-top: 50px;">
        """
        html_content = html_content.replace("<body>", f"<body>{preview_notice}")
        html_content = html_content.replace("</body>", "</div></body>")

        # Replace QR code placeholder with text for preview
        html_content = html_content.replace(
            "{{QR_CODE}}",
            '<div style="border: 1px dashed #ccc; width: 100px; height: 100px; display: flex; align-items: center; justify-content: center; font-size: 10px;">QR CODE</div>',
        )

        # Return HTML content with proper content type for preview
        from flask import Response

        return Response(html_content, mimetype="text/html")

    except Exception as e:
        current_app.logger.error(f"Error previewing HTML for cuti {cuti_id}: {str(e)}")
        flash("Error loading preview", "error")
        return redirect(url_for("cuti.list_cuti"))


@cuti_bp.route("/download-cuti-pdf/<int:cuti_id>")
@login_required
def download_cuti_pdf(cuti_id):
    """Download PDF for existing cuti application"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)

        # Check if PDF already exists
        # Force regenerate if status is approved/rejected so approval info is reflected
        if cuti.pdf_path and os.path.exists(cuti.pdf_path) and cuti.status_cuti == 'pending':
            pdf_path = cuti.pdf_path
            # Convert to absolute path for send_file
            if not os.path.isabs(pdf_path):
                pdf_path = os.path.join(current_app.root_path, "..", pdf_path)
                pdf_path = os.path.abspath(pdf_path)

            try:
                filename = generate_cuti_filename(cuti.nama, cuti.tgl_ajuan_cuti)
                return create_download_response(pdf_path, filename)
            except Exception as send_error:
                current_app.logger.error(
                    f"Error sending existing PDF file: {str(send_error)}"
                )
                # If sending fails, regenerate PDF
                pass

        # If PDF doesn't exist, generate it using multiple template methods
        result = None

        # Method 1: HTML Template (primary - always produces a PDF)
        try:
            from config.html_template_handler import HtmlTemplateHandler

            template_handler = HtmlTemplateHandler()
            current_app.logger.info("Attempting HTML template for download...")
            result = template_handler.fill_template_and_generate_pdf(cuti)
            if result and result.get("success"):
                current_app.logger.info(f"✅ HTML template successful for download - PDF: {result.get('pdf_path')}")
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result'
                current_app.logger.warning(f"HTML template failed: {error_msg}")
        except Exception as html_error:
            current_app.logger.error(f"HTML template exception: {str(html_error)}")
            import traceback
            current_app.logger.error(traceback.format_exc())

        # Method 2: Advanced DOCX Template (fallback - only if PDF conversion succeeds)
        if not result or not result.get("success"):
            try:
                from config.docx_template_advanced import AdvancedDocxTemplateHandler

                template_handler = AdvancedDocxTemplateHandler()
                current_app.logger.info("Attempting Advanced DOCX template for download...")
                result = template_handler.fill_template_and_generate_pdf(cuti)
                if result and result.get("success"):
                    # Verify that the result is actually a PDF file
                    pdf_path = result.get("pdf_path", "")
                    if (
                        pdf_path
                        and pdf_path.endswith(".pdf")
                        and os.path.exists(pdf_path)
                    ):
                        current_app.logger.info("✅ Advanced DOCX template successful for download")
                    else:
                        result = None
                        current_app.logger.warning("Advanced DOCX template returned non-PDF file")
            except Exception as advanced_error:
                current_app.logger.error(f"Advanced DOCX template exception: {str(advanced_error)}")
                import traceback
                current_app.logger.error(traceback.format_exc())

        # Method 3: Basic DOCX Template (last resort - only if PDF conversion succeeds)
        if not result or not result.get("success"):
            try:
                from config.docx_template_handler import DocxTemplateHandler

                template_handler = DocxTemplateHandler()
                current_app.logger.info("Attempting Basic DOCX template for download...")
                result = template_handler.fill_template_and_generate_pdf(cuti)
                if result and result.get("success"):
                    # Verify that the result is actually a PDF file
                    pdf_path = result.get("pdf_path", "")
                    if (
                        pdf_path
                        and pdf_path.endswith(".pdf")
                        and os.path.exists(pdf_path)
                    ):
                        current_app.logger.info("✅ Basic DOCX template successful for download")
                    else:
                        result = {"success": False, "error": "PDF conversion failed"}
                        current_app.logger.warning("Basic DOCX template returned non-PDF file")
            except Exception as docx_error:
                current_app.logger.error(f"Basic DOCX template exception: {str(docx_error)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
                result = {"success": False, "error": "All template methods failed"}

        if result and result.get("success"):
            pdf_path = result.get("pdf_path", "")

            # Verify file is actually a PDF
            if not pdf_path or not pdf_path.endswith(".pdf"):
                current_app.logger.error(f"Generated file is not PDF: {pdf_path}")
                flash("Error: File yang dihasilkan bukan PDF", "error")
                return redirect(url_for("cuti.list_cuti"))

            if not os.path.exists(pdf_path):
                current_app.logger.error(f"PDF file not found: {pdf_path}")
                flash("Error: File PDF tidak ditemukan", "error")
                return redirect(url_for("cuti.list_cuti"))

            # Convert to absolute path for send_file
            if not os.path.isabs(pdf_path):
                pdf_path = os.path.join(current_app.root_path, "..", pdf_path)
                pdf_path = os.path.abspath(pdf_path)

            # Update cuti record with generated files info
            cuti.qr_code = result.get("signature_hash", "")
            cuti.pdf_path = pdf_path
            db.session.commit()

            try:
                current_app.logger.info(f"Sending PDF file: {pdf_path}")
                filename = generate_cuti_filename(cuti.nama, cuti.tgl_ajuan_cuti)
                return create_download_response(pdf_path, filename)
            except Exception as send_error:
                current_app.logger.error(f"Error sending PDF file: {str(send_error)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
                flash("Error: Gagal mengirim file PDF", "error")
                return redirect(url_for("cuti.list_cuti"))

        error_msg = (
            result.get("error", "Unknown error")
            if result
            else "PDF generation failed - no result returned"
        )
        current_app.logger.error(
            f"PDF generation failed for cuti ID: {cuti_id} - {error_msg}"
        )
        flash(f"Gagal membuat PDF: {error_msg}", "error")
        return redirect(url_for("cuti.list_cuti"))

    except Exception as e:
        current_app.logger.error(f"Error downloading PDF for cuti {cuti_id}: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash("Error downloading PDF", "error")
        return redirect(url_for("cuti.list_cuti"))


@cuti_bp.route("/generate-form-pdf/<int:cuti_id>")
@login_required
def generate_form_pdf(cuti_id):
    """Generate PDF formulir cuti dengan format resmi Mahkamah Agung"""
    try:
        # Get cuti data
        cuti = Cuti.query.get_or_404(cuti_id)
        current_app.logger.info(f"Generating form PDF for cuti ID: {cuti_id}")

        # Generate PDF
        pdf_generator = CutiFormPDFGenerator()
        pdf_path = pdf_generator.create_cuti_form_from_model(cuti)

        # Verify PDF was created
        if not pdf_path or not os.path.exists(pdf_path):
            raise Exception(f"PDF generation failed - file not found: {pdf_path}")

        current_app.logger.info(f"Form PDF generated successfully: {pdf_path}")

        # Return PDF file with enhanced download headers
        filename = generate_cuti_filename(
            cuti.nama, cuti.tgl_ajuan_cuti, "formulir_cuti"
        )
        return create_download_response(pdf_path, filename)

    except Exception as e:
        current_app.logger.error(
            f"Error generating PDF form for cuti {cuti_id}: {str(e)}"
        )
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f"Error generating PDF form: {str(e)}", "error")
        return redirect(url_for("cuti.list_cuti"))


@cuti_bp.route("/preview-form-pdf/<int:cuti_id>")
@login_required
def preview_form_pdf(cuti_id):
    """Preview formulir cuti sebelum generate PDF"""
    try:
        # Get cuti data
        cuti = Cuti.query.get_or_404(cuti_id)

        return render_template("cuti/preview_form_pdf.html", cuti=cuti)

    except Exception as e:
        current_app.logger.error(
            f"Error previewing PDF form for cuti {cuti_id}: {str(e)}"
        )
        flash(f"Error loading preview: {str(e)}", "error")
        return redirect(url_for("cuti.list_cuti"))

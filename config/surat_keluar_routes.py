"""
Surat Keluar routes
Outgoing document management functionality
"""

from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required
from sqlalchemy import asc, desc, func

from config.extensions import db
from config.forms import SuratKeluarForm
from config.models import SuratKeluar
from config.route_utils import role_required

surat_keluar_bp = Blueprint("surat_keluar", __name__)


@surat_keluar_bp.route("/show_surat_keluar", methods=["GET"])
@login_required
def show_surat_keluar():
    """Show surat keluar list"""
    try:
        sort = request.args.get("sort", "tanggal_suratKeluar")
        order = request.args.get("order", "desc")
        page = request.args.get("page", 1, type=int)
        search = request.args.get("search", "").strip()

        sort_options = {
            "tanggal_suratKeluar": SuratKeluar.tanggal_suratKeluar,
            "pengirim_suratKeluar": SuratKeluar.pengirim_suratKeluar,
            "penerima_suratKeluar": SuratKeluar.penerima_suratKeluar,
            "nomor_suratKeluar": SuratKeluar.nomor_suratKeluar,
            "isi_suratKeluar": SuratKeluar.isi_suratKeluar,
            "created_at": SuratKeluar.created_at,
            "status_suratKeluar": SuratKeluar.status_suratKeluar,
        }

        sort_column = sort_options.get(sort, SuratKeluar.tanggal_suratKeluar)
        order_by = asc(sort_column) if order == "asc" else desc(sort_column)

        query = SuratKeluar.query

        if search:
            like_pattern = f"%{search}%"
            query = query.filter(
                (SuratKeluar.pengirim_suratKeluar.ilike(like_pattern))
                | (SuratKeluar.penerima_suratKeluar.ilike(like_pattern))
                | (SuratKeluar.nomor_suratKeluar.ilike(like_pattern))
                | (SuratKeluar.isi_suratKeluar.ilike(like_pattern))
            )

        surat_keluar_entries = query.order_by(order_by).paginate(page=page, per_page=20)

        return render_template(
            "surat_keluar/show_surat_keluar.html",
            entries=surat_keluar_entries,
            sort=sort,
            order=order,
            search=search,
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("main.index"))


@surat_keluar_bp.route("/input_surat_keluar", methods=["GET", "POST"])
@login_required
@role_required("admin")
def input_surat_keluar():
    """Input new surat keluar"""
    form = SuratKeluarForm()

    # Debug logging
    if request.method == "POST":
        current_app.logger.info("=== POST REQUEST DEBUG (SURAT KELUAR) ===")
        current_app.logger.info(f"Form data keys: {list(request.form.keys())}")
        current_app.logger.info(f"Files in request: {list(request.files.keys())}")

        if "image" in request.files:
            uploaded_file = request.files["image"]
            current_app.logger.info(f"File detected: {uploaded_file.filename}")
            current_app.logger.info(f"File content type: {uploaded_file.content_type}")
        else:
            current_app.logger.warning("No file found in request.files")

    if form.validate_on_submit():
        try:
            # Handle file upload
            image_data = None
            if form.image.data:
                file = form.image.data
                current_app.logger.info(f"Processing image: {file.filename}")

                # Validate file extension
                allowed_extensions = {"jpg", "jpeg", "png"}
                file_ext = (
                    file.filename.rsplit(".", 1)[1].lower()
                    if "." in file.filename
                    else ""
                )

                if file_ext not in allowed_extensions:
                    flash(
                        f"Format file tidak didukung. Hanya menerima: {', '.join(sorted(allowed_extensions))}",
                        "warning",
                    )
                    current_app.logger.warning(f"Invalid file extension: {file_ext}")
                else:
                    image_data = file.read()
                    if len(image_data) == 0:
                        current_app.logger.warning("File is empty (0 bytes)")
                        image_data = None
                    else:
                        current_app.logger.info(
                            f"Image uploaded successfully: {file.filename}, size: {len(image_data)} bytes"
                        )
            else:
                current_app.logger.info("No image uploaded (optional field)")

            new_surat_keluar = SuratKeluar(
                tanggal_suratKeluar=form.tanggal_suratKeluar.data,
                pengirim_suratKeluar=form.pengirim_suratKeluar.data,
                penerima_suratKeluar=form.penerima_suratKeluar.data,
                nomor_suratKeluar=form.nomor_suratKeluar.data,
                kode_suratKeluar=form.kode_suratKeluar.data,
                jenis_suratKeluar=form.jenis_suratKeluar.data,
                isi_suratKeluar=form.isi_suratKeluar.data,
                gambar_suratKeluar=image_data,
                status_suratKeluar="pending",
                created_at=datetime.utcnow(),
            )
            db.session.add(new_surat_keluar)
            db.session.commit()

            current_app.logger.info(
                f"Surat Keluar saved with ID: {new_surat_keluar.id_suratKeluar}"
            )
            current_app.logger.info(f"Image saved to DB: {image_data is not None}")

            # Verify file was saved
            db.session.refresh(new_surat_keluar)
            if new_surat_keluar.gambar_suratKeluar:
                image_size_kb = len(new_surat_keluar.gambar_suratKeluar) / 1024
                current_app.logger.info(
                    f"Verified: Image saved in DB ({image_size_kb:.2f} KB)"
                )
                flash(
                    f"Surat Keluar berhasil ditambahkan dengan lampiran ({image_size_kb:.2f} KB)!",
                    "success",
                )
            else:
                current_app.logger.info("Verified: No image in DB")
                flash("Surat Keluar berhasil ditambahkan (tanpa lampiran)!", "success")

            return redirect(url_for("surat_keluar.show_surat_keluar"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Error adding Surat Keluar: {str(e)}", exc_info=True
            )
            flash(f"Gagal menambahkan Surat Keluar: {str(e)}", "danger")
            return render_template("surat_keluar/input_surat_keluar.html", form=form)
    elif request.method == "POST":
        # If form is invalid, show detailed errors
        current_app.logger.error(f"Form validation errors: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error pada {field}: {error}", "danger")
    return render_template("surat_keluar/input_surat_keluar.html", form=form)


@surat_keluar_bp.route(
    "/edit_surat_keluar/<int:id_suratKeluar>", methods=["GET", "POST"]
)
@login_required
@role_required("admin")
def edit_surat_keluar(id_suratKeluar):
    """Edit surat keluar"""
    surat_keluar = SuratKeluar.query.get_or_404(id_suratKeluar)

    if request.method == "POST":
        try:
            # Update surat keluar fields
            surat_keluar.nomor_suratKeluar = request.form.get(
                "nomor_suratKeluar", surat_keluar.nomor_suratKeluar
            )
            surat_keluar.pengirim_suratKeluar = request.form.get(
                "pengirim_suratKeluar", surat_keluar.pengirim_suratKeluar
            )
            surat_keluar.penerima_suratKeluar = request.form.get(
                "penerima_suratKeluar", surat_keluar.penerima_suratKeluar
            )
            surat_keluar.isi_suratKeluar = request.form.get(
                "isi_suratKeluar", surat_keluar.isi_suratKeluar
            )

            from config.ocr_utils import calculate_overall_ocr_accuracy

            surat_keluar.ocr_accuracy_suratKeluar = calculate_overall_ocr_accuracy(
                surat_keluar, "suratKeluar"
            )

            if "gambar_suratKeluar" in request.files:
                file = request.files["gambar_suratKeluar"]
                if file and file.filename != "":
                    # Handle file upload if needed
                    pass

            db.session.commit()
            flash("Surat keluar berhasil diperbarui.", "success")
            return redirect(url_for("surat_keluar.show_surat_keluar"))
        except Exception as e:
            db.session.rollback()
            flash(f"Gagal memperbarui surat keluar: {str(e)}", "error")

    return render_template("surat_keluar/edit_surat_keluar.html", surat=surat_keluar)


@surat_keluar_bp.route("/delete_surat_keluar/<int:id_suratKeluar>", methods=["POST"])
@login_required
@role_required("admin")
def delete_surat_keluar(id_suratKeluar):
    """Delete surat keluar"""
    surat_keluar = SuratKeluar.query.get_or_404(id_suratKeluar)

    try:
        db.session.delete(surat_keluar)
        db.session.commit()
        flash("Surat keluar berhasil dihapus.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal menghapus surat keluar: {str(e)}", "error")

    return redirect(url_for("surat_keluar.show_surat_keluar"))


@surat_keluar_bp.route("/surat_keluar")
@login_required
def surat_keluar():
    """Surat keluar list (legacy route)"""
    daftar_surat = SuratKeluar.query.all()
    return render_template("surat_keluar/surat_keluar.html", daftar_surat=daftar_surat)


# Additional chart-data from routes_old.py
@surat_keluar_bp.route("/chart-data")
@login_required
def chart_data():
    masuk = (
        db.session.query(
            func.date(SuratKeluar.tanggal_suratKeluar).label("tanggal"),
            func.count().label("jumlah"),
        )
        .group_by(func.date(SuratKeluar.tanggal_suratKeluar))
        .all()
    )

    keluar = (
        db.session.query(
            func.date(SuratKeluar.tanggal_suratKeluar).label("tanggal"),
            func.count().label("jumlah"),
        )
        .group_by(func.date(SuratKeluar.tanggal_suratKeluar))
        .all()
    )

    tanggal_set = set([m[0] for m in masuk] + [k[0] for k in keluar])
    tanggal_sorted = sorted(tanggal_set)

    data_masuk_dict = {m[0]: m[1] for m in masuk}
    data_keluar_dict = {k[0]: k[1] for k in keluar}

    data = {
        "labels": tanggal_sorted,
        "surat_keluar": [data_masuk_dict.get(t, 0) for t in tanggal_sorted],
        "surat_masuk": [data_keluar_dict.get(t, 0) for t in tanggal_sorted],
    }
    return jsonify(data)


@surat_keluar_bp.route("/approve-surat/<int:surat_id>", methods=["POST"])
@login_required
@role_required("pimpinan", "admin")
def approve_surat_keluar(surat_id):
    """Approve surat keluar - only pimpinan or admin can approve"""
    try:
        surat = SuratKeluar.query.get(surat_id)
        if not surat:
            return jsonify({"success": False, "message": "Surat tidak ditemukan"}), 404

        if surat.status_suratKeluar != "pending":
            return jsonify(
                {
                    "success": False,
                    "message": f"Surat sudah {surat.status_suratKeluar}. Tidak dapat diubah lagi.",
                }
            ), 400

        # Update status
        surat.status_suratKeluar = "approved"

        db.session.commit()

        current_app.logger.info(
            f"Surat Keluar ID {surat_id} disetujui oleh {current_user.email}"
        )

        return jsonify(
            {
                "success": True,
                "message": f"Surat dari {surat.pengirim_suratKeluar} berhasil disetujui",
                "surat_info": {
                    "nomor": surat.nomor_suratKeluar,
                    "pengirim": surat.pengirim_suratKeluar,
                    "status": surat.status_suratKeluar,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving surat keluar {surat_id}: {str(e)}")
        return jsonify(
            {"success": False, "message": "Terjadi kesalahan saat menyetujui surat"}
        ), 500


@surat_keluar_bp.route("/reject-surat/<int:surat_id>", methods=["POST"])
@login_required
@role_required("pimpinan", "admin")
def reject_surat_keluar(surat_id):
    """Reject surat keluar - only pimpinan or admin can reject"""
    try:
        surat = SuratKeluar.query.get(surat_id)
        if not surat:
            return jsonify({"success": False, "message": "Surat tidak ditemukan"}), 404

        if surat.status_suratKeluar != "pending":
            return jsonify(
                {
                    "success": False,
                    "message": f"Surat sudah {surat.status_suratKeluar}. Tidak dapat diubah lagi.",
                }
            ), 400

        # Update status
        surat.status_suratKeluar = "rejected"

        db.session.commit()

        current_app.logger.info(
            f"Surat Keluar ID {surat_id} ditolak oleh {current_user.email}"
        )

        return jsonify(
            {
                "success": True,
                "message": f"Surat dari {surat.pengirim_suratKeluar} berhasil ditolak",
                "surat_info": {
                    "nomor": surat.nomor_suratKeluar,
                    "pengirim": surat.pengirim_suratKeluar,
                    "status": surat.status_suratKeluar,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting surat keluar {surat_id}: {str(e)}")
        return jsonify(
            {"success": False, "message": "Terjadi kesalahan saat menolak surat"}
        ), 500


@surat_keluar_bp.route("/template-surat", methods=["GET", "POST"])
@login_required
@role_required("admin", "staff")
def template_surat():
    """Create surat keluar from template and directly download as PDF"""
    if request.method == "POST":
        import io
        import traceback
        from flask import make_response
        
        try:
            # Generate nomor surat otomatis
            year = datetime.now().year
            month = datetime.now().month
            
            # Count existing letters this month
            count = SuratKeluar.query.filter(
                func.extract('year', SuratKeluar.tanggal_suratKeluar) == year,
                func.extract('month', SuratKeluar.tanggal_suratKeluar) == month
            ).count() + 1
            
            # Format: W10-A/XXX/HK.05/MM/YYYY
            nomor_surat = f"W10-A/{count:03d}/HK.05/{month:02d}/{year}"
            
            # Get form data
            penerima = request.form.get('penerima_suratKeluar')
            pengirim = request.form.get('pengirim_suratKeluar')
            perihal = request.form.get('perihal')
            isi_surat = request.form.get('isi_suratKeluar')
            tanggal = request.form.get('tanggal_suratKeluar')
            
            # Validate required fields
            if not all([penerima, pengirim, perihal, isi_surat, tanggal]):
                flash('Semua field harus diisi!', 'error')
                return redirect(url_for('surat_keluar.template_surat'))
            
            # Create new surat keluar
            new_surat = SuratKeluar(
                nomor_suratKeluar=nomor_surat,
                tanggal_suratKeluar=datetime.strptime(tanggal, '%Y-%m-%d') if tanggal else datetime.now(),
                pengirim_suratKeluar=pengirim,
                penerima_suratKeluar=penerima,
                isi_suratKeluar=isi_surat,
                jenis_suratKeluar=perihal,
                kode_suratKeluar='W10-A',
                status_suratKeluar='pending',
                created_at=datetime.utcnow()
            )
            
            db.session.add(new_surat)
            db.session.commit()
            
            current_app.logger.info(f'✅ Surat keluar berhasil dibuat: {nomor_surat} (ID: {new_surat.id_suratKeluar})')
            
            # Generate PDF langsung di sini (tidak redirect)
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import cm
                from reportlab.lib import colors
                from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
                
                # Generate safe filename
                safe_filename = f"Surat_Keluar_{nomor_surat.replace('/', '_').replace(' ', '_')}.pdf"
                
                # Create PDF buffer
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(
                    buffer, 
                    pagesize=A4,
                    topMargin=2.5*cm, 
                    bottomMargin=2*cm,
                    leftMargin=2*cm, 
                    rightMargin=2*cm
                )
                
                # Build PDF content
                story = []
                styles = getSampleStyleSheet()
                
                # Custom styles
                body_style = ParagraphStyle(
                    'Body',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.black,
                    alignment=TA_JUSTIFY,
                    spaceAfter=12,
                    leading=24,
                    firstLineIndent=2.5*cm
                )
                
                normal_style = ParagraphStyle(
                    'Normal',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.black,
                    alignment=TA_JUSTIFY,
                    spaceAfter=12,
                    leading=24
                )
                
                # Custom styles untuk kop surat
                kop_title_style = ParagraphStyle(
                    'KopTitle',
                    parent=styles['Heading1'],
                    fontSize=13,
                    textColor=colors.black,
                    spaceAfter=2,
                    alignment=TA_CENTER,
                    fontName='Helvetica-Bold',
                    leading=14
                )
                
                kop_address_style = ParagraphStyle(
                    'KopAddress',
                    parent=styles['Normal'],
                    fontSize=8.5,
                    textColor=colors.black,
                    alignment=TA_CENTER,
                    spaceAfter=6,
                    leading=10
                )
                
                # Kop Surat dengan Logo
                # Use actual logo image with proper aspect ratio
                from reportlab.platypus import Image as RLImage
                import os
                
                logo_path = os.path.join(current_app.root_path, 'static', 'assets', 'images', 'logo_pa_original.png')
                
                if os.path.exists(logo_path):
                    try:
                        # Use preserveAspectRatio to prevent stretching
                        logo_element = RLImage(
                            logo_path, 
                            width=2*cm, 
                            height=2*cm,
                            kind='proportional'  # Maintain aspect ratio
                        )
                        current_app.logger.info(f"✅ Logo loaded from: {logo_path}")
                    except Exception as img_error:
                        current_app.logger.error(f"Error loading logo image: {str(img_error)}")
                        # Fallback to empty space
                        logo_element = Paragraph("", styles['Normal'])
                else:
                    current_app.logger.warning(f"Logo file not found: {logo_path}")
                    # Fallback to empty space
                    logo_element = Paragraph("", styles['Normal'])
                
                kop_text = Paragraph(
                    "<b>MAHKAMAH AGUNG REPUBLIK INDONESIA</b><br/>"
                    "<b>DIREKTORAT JENDERAL BADAN PERADILAN AGAMA</b><br/>"
                    "<b>PENGADILAN TINGGI AGAMA BANJARMASIN</b><br/>"
                    "<b>PENGADILAN AGAMA BANJARBARU</b><br/>"
                    "<font size='8.5'>Jalan Trikora Nomor 4, Kelurahan Kemuning, Kecamatan Banjarbaru Selatan<br/>"
                    "Kota Banjarbaru, Kalimantan Selatan 70714, www.pa-banjarbaru.go.id, "
                    "<font color='blue'><u>pa.banjarbaru@gmail.com</u></font></font>",
                    kop_title_style
                )
                
                kop_table = Table([[logo_element, kop_text]], colWidths=[2.5*cm, doc.width-2.5*cm])
                kop_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ]))
                story.append(kop_table)
                
                # Line separator
                story.append(Spacer(1, 0.2*cm))
                line_data = [['', '']]
                line_table = Table(line_data, colWidths=[doc.width])
                line_table.setStyle(TableStyle([
                    ('LINEABOVE', (0, 0), (-1, 0), 2.5, colors.black),
                ]))
                story.append(line_table)
                story.append(Spacer(1, 0.4*cm))
                
                # Nomor, Lampiran, Perihal
                info_data = [
                    ['Nomor', ':', nomor_surat],
                    ['Lampiran', ':', '-'],
                    ['Perihal', ':', perihal]
                ]
                info_table = Table(info_data, colWidths=[3*cm, 0.5*cm, doc.width-3.5*cm])
                info_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (2, 0), (2, 0), 'Courier-Bold'),
                    ('FONTNAME', (2, 2), (2, 2), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(info_table)
                story.append(Spacer(1, 0.8*cm))
                
                # Kepada
                kepada_style = ParagraphStyle(
                    'Kepada', 
                    parent=styles['Normal'], 
                    fontSize=11, 
                    spaceAfter=4,
                    leading=18
                )
                story.append(Paragraph("<b>Kepada Yth.</b>", kepada_style))
                story.append(Paragraph(f"<b>{penerima}</b>", kepada_style))
                story.append(Paragraph("di-", kepada_style))
                story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Tempat</b>", kepada_style))
                story.append(Spacer(1, 0.8*cm))
                
                # Pembuka
                story.append(Paragraph("Dengan hormat,", normal_style))
                
                # Isi Surat
                if isi_surat:
                    isi_paragraphs = isi_surat.split('\n')
                    for para in isi_paragraphs:
                        if para.strip():
                            para_clean = para.strip().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            story.append(Paragraph(para_clean, body_style))
                
                # Penutup
                story.append(Paragraph(
                    "Demikian surat ini kami sampaikan. Atas perhatian dan kerjasamanya, kami ucapkan terima kasih.", 
                    body_style
                ))
                story.append(Spacer(1, 1.5*cm))
                
                # Tanda Tangan
                tanggal_obj = datetime.strptime(tanggal, '%Y-%m-%d') if tanggal else datetime.now()
                tanggal_str = tanggal_obj.strftime('%d %B %Y')
                nama_ttd = pengirim.split(',')[0] if ',' in pengirim else pengirim
                
                # Style untuk nama dengan underline
                nama_ttd_style = ParagraphStyle(
                    'NamaTTD',
                    parent=styles['Normal'],
                    fontSize=11,
                    fontName='Helvetica-Bold',
                    textColor=colors.black,
                    alignment=TA_LEFT,
                    underlineWidth=1,
                    underlineOffset=-2
                )
                
                ttd_data = [
                    ['', f'Banjarbaru, {tanggal_str}'],
                    ['', pengirim],
                    ['', ''],
                    ['', ''],
                    ['', ''],
                    ['', Paragraph(f'<u>{nama_ttd}</u>', nama_ttd_style)]
                ]
                ttd_table = Table(ttd_data, colWidths=[doc.width/2, doc.width/2])
                ttd_table.setStyle(TableStyle([
                    ('FONTSIZE', (1, 0), (1, -1), 11),
                    ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 5), (1, 5), 'Helvetica-Bold'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (1, 0), (1, -1), 'TOP'),
                ]))
                story.append(ttd_table)
                
                # Build PDF
                doc.build(story)
                
                # Get PDF data
                pdf_data = buffer.getvalue()
                buffer.close()
                
                current_app.logger.info(f"✅ PDF generated: {len(pdf_data)} bytes")
                
                # Create response
                response = make_response(pdf_data)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
                response.headers['Content-Length'] = len(pdf_data)
                
                return response
                
            except Exception as pdf_error:
                current_app.logger.error(f"❌ PDF generation error: {str(pdf_error)}")
                current_app.logger.error(traceback.format_exc())
                flash(f'Surat berhasil dibuat, tapi gagal generate PDF: {str(pdf_error)}', 'warning')
                return redirect(url_for('surat_keluar.show_surat_keluar'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"❌ Error creating template surat: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            flash(f'Gagal membuat surat: {str(e)}', 'error')
            return redirect(url_for('surat_keluar.template_surat'))
    
    # Generate preview nomor surat
    year = datetime.now().year
    month = datetime.now().month
    count = SuratKeluar.query.filter(
        func.extract('year', SuratKeluar.tanggal_suratKeluar) == year,
        func.extract('month', SuratKeluar.tanggal_suratKeluar) == month
    ).count() + 1
    preview_nomor = f"W10-A/{count:03d}/HK.05/{month:02d}/{year}"
    
    return render_template('surat_keluar/template_surat.html', preview_nomor=preview_nomor)


@surat_keluar_bp.route("/preview-template/<int:id_suratKeluar>")
@login_required
def preview_template_surat(id_suratKeluar):
    """Preview template surat with official letterhead"""
    surat = SuratKeluar.query.get_or_404(id_suratKeluar)
    return render_template('surat_keluar/preview_template.html', surat=surat)


@surat_keluar_bp.route("/download-pdf/<int:id_suratKeluar>")
@login_required
def download_pdf_surat(id_suratKeluar):
    """Download surat keluar as PDF file"""
    import io
    import traceback
    from flask import make_response
    
    try:
        surat = SuratKeluar.query.get_or_404(id_suratKeluar)
        current_app.logger.info(f"Starting PDF generation for surat ID: {id_suratKeluar}")
        
        # Generate safe filename
        safe_filename = f"Surat_Keluar_{surat.nomor_suratKeluar.replace('/', '_').replace(' ', '_')}.pdf"
        current_app.logger.info(f"PDF filename: {safe_filename}")
        
        # Method 1: Try ReportLab (more reliable)
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            
            current_app.logger.info("Using ReportLab for PDF generation")
            
            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=A4,
                topMargin=2.5*cm, 
                bottomMargin=2*cm,
                leftMargin=2*cm, 
                rightMargin=2*cm
            )
            
            # Build PDF content
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=13,
                textColor=colors.black,
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=18,
                textColor=colors.black,
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            address_style = ParagraphStyle(
                'Address',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=12
            )
            
            body_style = ParagraphStyle(
                'Body',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.black,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                leading=24,
                firstLineIndent=2.5*cm
            )
            
            normal_style = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.black,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                leading=24
            )
            
            # Custom styles untuk kop surat
            kop_title_style = ParagraphStyle(
                'KopTitle',
                parent=styles['Heading1'],
                fontSize=13,
                textColor=colors.black,
                spaceAfter=2,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                leading=14
            )
            
            kop_subtitle_style = ParagraphStyle(
                'KopSubtitle',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.black,
                spaceAfter=2,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                leading=13
            )
            
            kop_address_style = ParagraphStyle(
                'KopAddress',
                parent=styles['Normal'],
                fontSize=8.5,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=6,
                leading=10
            )
            
            # Kop Surat dengan Logo - sesuai format resmi PA Banjarbaru
            # Logo PA (placeholder - bisa diganti dengan logo asli)
            from reportlab.lib.utils import ImageReader
            from reportlab.platypus import Image as RLImage
            
            # Buat table untuk logo + kop surat
            kop_content = []
            
            # Row 1: Logo + Kop Surat
            # Use actual logo image with proper aspect ratio
            from reportlab.platypus import Image as RLImage
            import os
            
            logo_path = os.path.join(current_app.root_path, 'static', 'assets', 'images', 'logo_pa_original.png')
            
            if os.path.exists(logo_path):
                try:
                    logo_element = RLImage(
                        logo_path, 
                        width=2*cm, 
                        height=2*cm,
                        kind='proportional'  # Maintain aspect ratio
                    )
                    current_app.logger.info(f"✅ Logo loaded from: {logo_path}")
                except Exception as img_error:
                    current_app.logger.error(f"Error loading logo: {str(img_error)}")
                    logo_element = Paragraph("", styles['Normal'])
            else:
                current_app.logger.warning(f"Logo not found: {logo_path}")
                logo_element = Paragraph("", styles['Normal'])
            
            kop_text = Paragraph(
                "<b>MAHKAMAH AGUNG REPUBLIK INDONESIA</b><br/>"
                "<b>DIREKTORAT JENDERAL BADAN PERADILAN AGAMA</b><br/>"
                "<b>PENGADILAN TINGGI AGAMA BANJARMASIN</b><br/>"
                "<b>PENGADILAN AGAMA BANJARBARU</b><br/>"
                "<font size='8.5'>Jalan Trikora Nomor 4, Kelurahan Kemuning, Kecamatan Banjarbaru Selatan<br/>"
                "Kota Banjarbaru, Kalimantan Selatan 70714, www.pa-banjarbaru.go.id, "
                "<font color='blue'><u>pa.banjarbaru@gmail.com</u></font></font>",
                kop_title_style
            )
            
            kop_table = Table([[logo_element, kop_text]], colWidths=[2.5*cm, doc.width-2.5*cm])
            kop_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ]))
            story.append(kop_table)
            
            # Line separator (single thick line)
            story.append(Spacer(1, 0.2*cm))
            line_data = [['', '']]
            line_table = Table(line_data, colWidths=[doc.width])
            line_table.setStyle(TableStyle([
                ('LINEABOVE', (0, 0), (-1, 0), 2.5, colors.black),
            ]))
            story.append(line_table)
            story.append(Spacer(1, 0.4*cm))
            
            # Nomor, Lampiran, Perihal
            info_data = [
                ['Nomor', ':', surat.nomor_suratKeluar or '-'],
                ['Lampiran', ':', '-'],
                ['Perihal', ':', surat.jenis_suratKeluar or '-']
            ]
            info_table = Table(info_data, colWidths=[3*cm, 0.5*cm, doc.width-3.5*cm])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, 0), 'Courier-Bold'),
                ('FONTNAME', (2, 2), (2, 2), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 0.8*cm))
            
            # Kepada
            kepada_style = ParagraphStyle(
                'Kepada', 
                parent=styles['Normal'], 
                fontSize=11, 
                spaceAfter=4,
                leading=18
            )
            story.append(Paragraph("<b>Kepada Yth.</b>", kepada_style))
            story.append(Paragraph(f"<b>{surat.penerima_suratKeluar or '-'}</b>", kepada_style))
            story.append(Paragraph("di-", kepada_style))
            story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Tempat</b>", kepada_style))
            story.append(Spacer(1, 0.8*cm))
            
            # Pembuka
            story.append(Paragraph("Dengan hormat,", normal_style))
            
            # Isi Surat
            if surat.isi_suratKeluar:
                isi_paragraphs = surat.isi_suratKeluar.split('\n')
                for para in isi_paragraphs:
                    if para.strip():
                        # Escape HTML special characters
                        para_clean = para.strip().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        story.append(Paragraph(para_clean, body_style))
            
            # Penutup
            story.append(Paragraph(
                "Demikian surat ini kami sampaikan. Atas perhatian dan kerjasamanya, kami ucapkan terima kasih.", 
                body_style
            ))
            story.append(Spacer(1, 1.5*cm))
            
            # Tanda Tangan
            tanggal_str = surat.tanggal_suratKeluar.strftime('%d %B %Y') if surat.tanggal_suratKeluar else ''
            nama_ttd = surat.pengirim_suratKeluar.split(',')[0] if ',' in surat.pengirim_suratKeluar else surat.pengirim_suratKeluar
            
            # Style untuk nama dengan underline
            nama_ttd_style = ParagraphStyle(
                'NamaTTD',
                parent=styles['Normal'],
                fontSize=11,
                fontName='Helvetica-Bold',
                textColor=colors.black,
                alignment=TA_LEFT,
                underlineWidth=1,
                underlineOffset=-2
            )
            
            ttd_data = [
                ['', f'Banjarbaru, {tanggal_str}'],
                ['', surat.pengirim_suratKeluar or '-'],
                ['', ''],
                ['', ''],
                ['', ''],
                ['', Paragraph(f'<u>{nama_ttd}</u>', nama_ttd_style)]
            ]
            ttd_table = Table(ttd_data, colWidths=[doc.width/2, doc.width/2])
            ttd_table.setStyle(TableStyle([
                ('FONTSIZE', (1, 0), (1, -1), 11),
                ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 5), (1, 5), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (1, 0), (1, -1), 'TOP'),
            ]))
            story.append(ttd_table)
            
            # Build PDF
            doc.build(story)
            current_app.logger.info("PDF built successfully with ReportLab")
            
            # Get PDF data
            pdf_data = buffer.getvalue()
            buffer.close()
            
            current_app.logger.info(f"PDF size: {len(pdf_data)} bytes")
            
            # Create response
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
            response.headers['Content-Length'] = len(pdf_data)
            
            current_app.logger.info(f"✅ PDF generated successfully for surat {id_suratKeluar}")
            return response
            
        except Exception as reportlab_error:
            current_app.logger.error(f"ReportLab error: {str(reportlab_error)}")
            current_app.logger.error(traceback.format_exc())
            
            # Method 2: Try WeasyPrint as fallback
            try:
                from weasyprint import HTML, CSS
                from weasyprint.text.fonts import FontConfiguration
                
                current_app.logger.info("Trying WeasyPrint as fallback")
                
                # Render HTML template
                html_content = render_template('surat_keluar/pdf_template.html', surat=surat)
                
                # Create font configuration
                font_config = FontConfiguration()
                
                # Generate PDF from HTML
                pdf_file = HTML(string=html_content, base_url=request.url_root).write_pdf(
                    font_config=font_config
                )
                
                current_app.logger.info(f"PDF size: {len(pdf_file)} bytes")
                
                # Create response
                response = make_response(pdf_file)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
                response.headers['Content-Length'] = len(pdf_file)
                
                current_app.logger.info(f"✅ PDF generated successfully with WeasyPrint for surat {id_suratKeluar}")
                return response
                
            except Exception as weasy_error:
                current_app.logger.error(f"WeasyPrint error: {str(weasy_error)}")
                current_app.logger.error(traceback.format_exc())
                raise Exception(f"Both PDF engines failed. ReportLab: {str(reportlab_error)}, WeasyPrint: {str(weasy_error)}")
            
    except Exception as e:
        current_app.logger.error(f"❌ Error generating PDF for surat {id_suratKeluar}: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        flash(f'Gagal membuat PDF: {str(e)}. Silakan hubungi administrator.', 'error')
        return redirect(url_for('surat_keluar.preview_template_surat', id_suratKeluar=id_suratKeluar))

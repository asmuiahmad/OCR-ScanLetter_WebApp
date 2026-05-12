"""
Laporan routes
Statistical reports and analytics functionality
"""

from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func, or_

from config.extensions import db
from config.models import (
    AuditLog, Cuti, DisposisiSurat, Pegawai,
    SuratKeluar, SuratMasuk, User, UserLoginLog,
)
from config.route_utils import role_required

laporan_bp = Blueprint("laporan", __name__)


@laporan_bp.route("/laporan-statistik")
@login_required
@role_required("admin", "pimpinan")
def laporan_statistik():
    """Statistical reports"""
    semua_surat_masuk = SuratMasuk.query.all()
    semua_surat_keluar = SuratKeluar.query.all()

    total_masuk = len(semua_surat_masuk)
    total_keluar = len(semua_surat_keluar)

    # Count successful extractions - check all required fields
    berhasil_masuk = len(
        [
            s
            for s in semua_surat_masuk
            if (
                not hasattr(s, "initial_nomor_suratMasuk")
                or s.initial_nomor_suratMasuk != "Not found"
            )
            and (
                not hasattr(s, "initial_pengirim_suratMasuk")
                or s.initial_pengirim_suratMasuk != "Not found"
            )
            and (
                not hasattr(s, "initial_penerima_suratMasuk")
                or s.initial_penerima_suratMasuk != "Not found"
            )
            and (
                not hasattr(s, "initial_isi_suratMasuk")
                or s.initial_isi_suratMasuk != "Not found"
            )
        ]
    )

    berhasil_keluar = len(
        [
            s
            for s in semua_surat_keluar
            if (
                not hasattr(s, "initial_nomor_suratKeluar")
                or s.initial_nomor_suratKeluar != "Not found"
            )
            and (
                not hasattr(s, "initial_pengirim_suratKeluar")
                or s.initial_pengirim_suratKeluar != "Not found"
            )
            and (
                not hasattr(s, "initial_penerima_suratKeluar")
                or s.initial_penerima_suratKeluar != "Not found"
            )
            and (
                not hasattr(s, "initial_isi_suratKeluar")
                or s.initial_isi_suratKeluar != "Not found"
            )
        ]
    )

    persentase_berhasil_masuk = (
        round((berhasil_masuk / total_masuk * 100), 2) if total_masuk else 0
    )
    persentase_berhasil_keluar = (
        round((berhasil_keluar / total_keluar * 100), 2) if total_keluar else 0
    )

    field_stats_masuk = {
        "nomor_suratMasuk": 0,
        "pengirim_suratMasuk": 0,
        "penerima_suratMasuk": 0,
        "isi_suratMasuk": 0,
    }

    for surat in semua_surat_masuk:
        if (
            hasattr(surat, "initial_nomor_suratMasuk")
            and surat.initial_nomor_suratMasuk == "Not found"
        ):
            field_stats_masuk["nomor_suratMasuk"] += 1
        if (
            hasattr(surat, "initial_pengirim_suratMasuk")
            and surat.initial_pengirim_suratMasuk == "Not found"
        ):
            field_stats_masuk["pengirim_suratMasuk"] += 1
        if (
            hasattr(surat, "initial_penerima_suratMasuk")
            and surat.initial_penerima_suratMasuk == "Not found"
        ):
            field_stats_masuk["penerima_suratMasuk"] += 1
        if (
            hasattr(surat, "initial_isi_suratMasuk")
            and surat.initial_isi_suratMasuk == "Not found"
        ):
            field_stats_masuk["isi_suratMasuk"] += 1

    field_stats_keluar = {
        "nomor_suratKeluar": 0,
        "pengirim_suratKeluar": 0,
        "penerima_suratKeluar": 0,
        "isi_suratKeluar": 0,
    }

    for surat in semua_surat_keluar:
        if (
            hasattr(surat, "initial_nomor_suratKeluar")
            and surat.initial_nomor_suratKeluar == "Not found"
        ):
            field_stats_keluar["nomor_suratKeluar"] += 1
        if (
            hasattr(surat, "initial_pengirim_suratKeluar")
            and surat.initial_pengirim_suratKeluar == "Not found"
        ):
            field_stats_keluar["pengirim_suratKeluar"] += 1
        if (
            hasattr(surat, "initial_penerima_suratKeluar")
            and surat.initial_penerima_suratKeluar == "Not found"
        ):
            field_stats_keluar["penerima_suratKeluar"] += 1
        if (
            hasattr(surat, "initial_isi_suratKeluar")
            and surat.initial_isi_suratKeluar == "Not found"
        ):
            field_stats_keluar["isi_suratKeluar"] += 1

    full_letter_components_masuk = ["initial_nomor_suratMasuk"]
    full_letter_components_keluar = ["initial_nomor_suratKeluar"]

    full_letter_not_found_masuk = sum(
        sum(
            1
            for surat in semua_surat_masuk
            if hasattr(surat, field) and getattr(surat, field) == "Not found"
        )
        for field in full_letter_components_masuk
    )
    full_letter_not_found_keluar = sum(
        sum(
            1
            for surat in semua_surat_keluar
            if hasattr(surat, field) and getattr(surat, field) == "Not found"
        )
        for field in full_letter_components_keluar
    )

    field_stats_masuk["full_letter_number_not_found"] = full_letter_not_found_masuk
    field_stats_keluar["full_letter_number_not_found"] = full_letter_not_found_keluar

    akurasi_masuk = [
        s.ocr_accuracy_suratMasuk
        for s in semua_surat_masuk
        if s.ocr_accuracy_suratMasuk is not None
    ]
    akurasi_keluar = [
        s.ocr_accuracy_suratKeluar
        for s in semua_surat_keluar
        if s.ocr_accuracy_suratKeluar is not None
    ]

    rata2_akurasi_masuk = (
        round(sum(akurasi_masuk) / len(akurasi_masuk), 2) if akurasi_masuk else 0
    )
    rata2_akurasi_keluar = (
        round(sum(akurasi_keluar) / len(akurasi_keluar), 2) if akurasi_keluar else 0
    )

    akurasi_tinggi_masuk = len([a for a in akurasi_masuk if a >= 90])
    akurasi_sedang_masuk = len([a for a in akurasi_masuk if 70 <= a < 90])
    akurasi_rendah_masuk = len([a for a in akurasi_masuk if a < 70])

    akurasi_tinggi_keluar = len([a for a in akurasi_keluar if a >= 90])
    akurasi_sedang_keluar = len([a for a in akurasi_keluar if 70 <= a < 90])
    akurasi_rendah_keluar = len([a for a in akurasi_keluar if a < 70])

    # Get failed extractions for Surat Masuk
    gagal_ekstraksi_suratMasuk = SuratMasuk.query.filter(
        or_(
            SuratMasuk.initial_nomor_suratMasuk == "Not found",
            SuratMasuk.initial_pengirim_suratMasuk == "Not found",
            SuratMasuk.initial_penerima_suratMasuk == "Not found",
            SuratMasuk.initial_isi_suratMasuk == "Not found",
        )
    ).all()

    # Get failed extractions for Surat Keluar
    gagal_ekstraksi_suratKeluar = SuratKeluar.query.filter(
        or_(
            SuratKeluar.initial_nomor_suratKeluar == "Not found",
            SuratKeluar.initial_pengirim_suratKeluar == "Not found",
            SuratKeluar.initial_penerima_suratKeluar == "Not found",
            SuratKeluar.initial_isi_suratKeluar == "Not found",
        )
    ).all()

    keyword = request.args.get("keyword", "")
    surat_keyword = []
    if keyword:
        surat_keyword = SuratMasuk.query.filter(
            SuratMasuk.isi_suratMasuk.ilike(f"%{keyword}%")
        ).all()

    # ── Data tambahan untuk laporan cetak ──────────────────────────────
    # Surat Masuk per status
    masuk_pending   = SuratMasuk.query.filter_by(status_suratMasuk="pending").count()
    masuk_approved  = SuratMasuk.query.filter_by(status_suratMasuk="approved").count()
    masuk_rejected  = SuratMasuk.query.filter_by(status_suratMasuk="rejected").count()

    # Surat Keluar per status
    keluar_pending  = SuratKeluar.query.filter_by(status_suratKeluar="pending").count()
    keluar_approved = SuratKeluar.query.filter_by(status_suratKeluar="approved").count()
    keluar_rejected = SuratKeluar.query.filter_by(status_suratKeluar="rejected").count()

    # Cuti
    semua_cuti = Cuti.query.order_by(Cuti.tgl_ajuan_cuti.desc()).all()
    total_cuti          = len(semua_cuti)
    cuti_pending        = sum(1 for c in semua_cuti if c.status_cuti == "pending")
    cuti_approved       = sum(1 for c in semua_cuti if c.status_cuti == "approved")
    cuti_rejected       = sum(1 for c in semua_cuti if c.status_cuti == "rejected")

    # Pegawai
    semua_pegawai = Pegawai.query.order_by(Pegawai.nama).all()
    total_pegawai = len(semua_pegawai)

    # Disposisi
    semua_disposisi = DisposisiSurat.query.order_by(DisposisiSurat.tanggal_disposisi.desc()).all()
    total_disposisi     = len(semua_disposisi)
    disposisi_draft     = sum(1 for d in semua_disposisi if d.status == "draft")
    disposisi_dikirim   = sum(1 for d in semua_disposisi if d.status == "dikirim")
    disposisi_selesai   = sum(1 for d in semua_disposisi if d.status == "selesai")

    # Tanggal cetak
    tanggal_cetak = datetime.now().strftime("%d %B %Y, %H:%M")

    return render_template(
        "statistik/laporan_statistik.html",
        persentase_berhasil_masuk=persentase_berhasil_masuk,
        persentase_berhasil_keluar=persentase_berhasil_keluar,
        gagal_ekstraksi_suratKeluar=gagal_ekstraksi_suratKeluar,
        gagal_ekstraksi_suratMasuk=gagal_ekstraksi_suratMasuk,
        keyword=keyword,
        surat_keyword=surat_keyword,
        rata2_akurasi_masuk=rata2_akurasi_masuk,
        rata2_akurasi_keluar=rata2_akurasi_keluar,
        field_stats_keluar=field_stats_keluar,
        field_stats_masuk=field_stats_masuk,
        total_masuk=total_masuk,
        total_keluar=total_keluar,
        akurasi_tinggi_masuk=akurasi_tinggi_masuk,
        akurasi_sedang_masuk=akurasi_sedang_masuk,
        akurasi_rendah_masuk=akurasi_rendah_masuk,
        akurasi_tinggi_keluar=akurasi_tinggi_keluar,
        akurasi_sedang_keluar=akurasi_sedang_keluar,
        akurasi_rendah_keluar=akurasi_rendah_keluar,
        # Data laporan cetak
        masuk_pending=masuk_pending,
        masuk_approved=masuk_approved,
        masuk_rejected=masuk_rejected,
        keluar_pending=keluar_pending,
        keluar_approved=keluar_approved,
        keluar_rejected=keluar_rejected,
        semua_cuti=semua_cuti,
        total_cuti=total_cuti,
        cuti_pending=cuti_pending,
        cuti_approved=cuti_approved,
        cuti_rejected=cuti_rejected,
        semua_pegawai=semua_pegawai,
        total_pegawai=total_pegawai,
        semua_disposisi=semua_disposisi,
        total_disposisi=total_disposisi,
        disposisi_draft=disposisi_draft,
        disposisi_dikirim=disposisi_dikirim,
        disposisi_selesai=disposisi_selesai,
        semua_surat_masuk=semua_surat_masuk,
        semua_surat_keluar=semua_surat_keluar,
        tanggal_cetak=tanggal_cetak,
        current_user=current_user,
    )



@laporan_bp.route("/chart-data")
@login_required
def chart_data():
    """Get chart data for daily statistics with real data"""
    try:
        # Get data for the last 7 days
        today = datetime.now().date()
        seven_days_ago = today - timedelta(days=6)

        # Query surat masuk and keluar for the last 7 days
        surat_masuk_data = (
            db.session.query(
                func.date(SuratMasuk.created_at).label("date"),
                func.count(SuratMasuk.id_suratMasuk).label("count"),
            )
            .filter(func.date(SuratMasuk.created_at) >= seven_days_ago)
            .group_by(func.date(SuratMasuk.created_at))
            .all()
        )

        surat_keluar_data = (
            db.session.query(
                func.date(SuratKeluar.created_at).label("date"),
                func.count(SuratKeluar.id_suratKeluar).label("count"),
            )
            .filter(func.date(SuratKeluar.created_at) >= seven_days_ago)
            .group_by(func.date(SuratKeluar.created_at))
            .all()
        )

        # Create dictionaries for easy lookup
        masuk_dict = {str(item.date): item.count for item in surat_masuk_data}
        keluar_dict = {str(item.date): item.count for item in surat_keluar_data}

        # Generate labels and data for all 7 days
        labels = []
        surat_masuk_counts = []
        surat_keluar_counts = []

        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            date_str = str(date)
            labels.append(date.strftime("%d/%m"))
            surat_masuk_counts.append(masuk_dict.get(date_str, 0))
            surat_keluar_counts.append(keluar_dict.get(date_str, 0))

        return jsonify(
            {
                "labels": labels,
                "surat_masuk": surat_masuk_counts,
                "surat_keluar": surat_keluar_counts,
                "status": "success",
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error generating chart data: {str(e)}")
        # Return dummy data as fallback
        return jsonify(
            {
                "labels": [
                    "20/01",
                    "21/01",
                    "22/01",
                    "23/01",
                    "24/01",
                    "25/01",
                    "26/01",
                ],
                "surat_masuk": [0, 0, 0, 0, 0, 0, 0],
                "surat_keluar": [0, 0, 0, 0, 0, 0, 0],
                "status": "error",
                "message": str(e),
            }
        )


@laporan_bp.route("/laporan/cetak")
@login_required
@role_required("admin", "pimpinan")
def laporan_cetak():
    """Halaman laporan cetak — 8 laporan siap print"""
    now = datetime.now()
    tanggal_cetak = now.strftime("%d %B %Y, %H:%M")

    # 1. Surat Masuk
    semua_surat_masuk = SuratMasuk.query.order_by(
        SuratMasuk.tanggal_suratMasuk.desc()
    ).all()
    masuk_pending  = sum(1 for s in semua_surat_masuk if s.status_suratMasuk == "pending")
    masuk_approved = sum(1 for s in semua_surat_masuk if s.status_suratMasuk == "approved")
    masuk_rejected = sum(1 for s in semua_surat_masuk if s.status_suratMasuk == "rejected")

    # 2. Surat Keluar
    semua_surat_keluar = SuratKeluar.query.order_by(
        SuratKeluar.tanggal_suratKeluar.desc()
    ).all()
    keluar_pending  = sum(1 for s in semua_surat_keluar if s.status_suratKeluar == "pending")
    keluar_approved = sum(1 for s in semua_surat_keluar if s.status_suratKeluar == "approved")
    keluar_rejected = sum(1 for s in semua_surat_keluar if s.status_suratKeluar == "rejected")

    # 3. Cuti
    semua_cuti = Cuti.query.order_by(Cuti.tgl_ajuan_cuti.desc()).all()
    cuti_pending  = sum(1 for c in semua_cuti if c.status_cuti == "pending")
    cuti_approved = sum(1 for c in semua_cuti if c.status_cuti == "approved")
    cuti_rejected = sum(1 for c in semua_cuti if c.status_cuti == "rejected")

    # 4. Pegawai
    semua_pegawai = Pegawai.query.order_by(Pegawai.nama).all()

    # 5. Disposisi
    semua_disposisi = DisposisiSurat.query.order_by(
        DisposisiSurat.tanggal_disposisi.desc()
    ).all()
    disposisi_draft   = sum(1 for d in semua_disposisi if d.status == "draft")
    disposisi_dikirim = sum(1 for d in semua_disposisi if d.status == "dikirim")
    disposisi_selesai = sum(1 for d in semua_disposisi if d.status == "selesai")

    # 6. Approval History (dari AuditLog)
    semua_audit = AuditLog.query.order_by(AuditLog.created_at.desc()).all()
    audit_approved = sum(1 for a in semua_audit if a.action == "approved")
    audit_rejected = sum(1 for a in semua_audit if a.action == "rejected")

    # 7. Login Logs
    semua_login = UserLoginLog.query.order_by(
        UserLoginLog.login_time.desc()
    ).limit(500).all()
    login_success = sum(1 for l in semua_login if l.status == "success")
    login_failed  = sum(1 for l in semua_login if l.status != "success")

    # 8. OCR Stats
    akurasi_masuk  = [s.ocr_accuracy_suratMasuk  for s in semua_surat_masuk  if s.ocr_accuracy_suratMasuk  is not None]
    akurasi_keluar = [s.ocr_accuracy_suratKeluar for s in semua_surat_keluar if s.ocr_accuracy_suratKeluar is not None]
    rata2_ocr_masuk  = round(sum(akurasi_masuk)  / len(akurasi_masuk),  2) if akurasi_masuk  else 0
    rata2_ocr_keluar = round(sum(akurasi_keluar) / len(akurasi_keluar), 2) if akurasi_keluar else 0

    # Ringkasan umum
    ringkasan = [
        {"label": "Surat Masuk",  "total": len(semua_surat_masuk),  "pending": masuk_pending,  "approved": masuk_approved,  "rejected": masuk_rejected},
        {"label": "Surat Keluar", "total": len(semua_surat_keluar), "pending": keluar_pending, "approved": keluar_approved, "rejected": keluar_rejected},
        {"label": "Cuti",         "total": len(semua_cuti),         "pending": cuti_pending,   "approved": cuti_approved,   "rejected": cuti_rejected},
        {"label": "Disposisi",    "total": len(semua_disposisi),    "pending": disposisi_draft,"approved": disposisi_selesai,"rejected": 0},
        {"label": "Pegawai",      "total": len(semua_pegawai),      "pending": "-",            "approved": "-",             "rejected": "-"},
        {"label": "Audit Log",    "total": len(semua_audit),        "pending": "-",            "approved": audit_approved,  "rejected": audit_rejected},
        {"label": "Login Log",    "total": len(semua_login),        "pending": "-",            "approved": login_success,   "rejected": login_failed},
    ]

    return render_template(
        "laporan/cetak.html",
        tanggal_cetak=tanggal_cetak,
        # Surat Masuk
        semua_surat_masuk=semua_surat_masuk,
        masuk_pending=masuk_pending, masuk_approved=masuk_approved, masuk_rejected=masuk_rejected,
        # Surat Keluar
        semua_surat_keluar=semua_surat_keluar,
        keluar_pending=keluar_pending, keluar_approved=keluar_approved, keluar_rejected=keluar_rejected,
        # Cuti
        semua_cuti=semua_cuti,
        cuti_pending=cuti_pending, cuti_approved=cuti_approved, cuti_rejected=cuti_rejected,
        # Pegawai
        semua_pegawai=semua_pegawai,
        # Disposisi
        semua_disposisi=semua_disposisi,
        disposisi_draft=disposisi_draft, disposisi_dikirim=disposisi_dikirim, disposisi_selesai=disposisi_selesai,
        # Audit / Approval History
        semua_audit=semua_audit,
        audit_approved=audit_approved, audit_rejected=audit_rejected,
        # Login Logs
        semua_login=semua_login,
        login_success=login_success, login_failed=login_failed,
        # OCR Stats
        rata2_ocr_masuk=rata2_ocr_masuk, rata2_ocr_keluar=rata2_ocr_keluar,
        akurasi_masuk=akurasi_masuk, akurasi_keluar=akurasi_keluar,
        # Ringkasan
        ringkasan=ringkasan,
    )

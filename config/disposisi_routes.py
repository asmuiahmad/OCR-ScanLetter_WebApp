from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify, current_app
from flask_login import current_user, login_required
from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import joinedload

from config.extensions import db
from config.models import Disposisi, SuratKeluar, SuratMasuk, User, DisposisiHistory
from config.route_utils import role_required
from config.disposisi_helpers import (
    update_disposisi_status,
    get_disposisi_timeline,
    get_disposisi_stats,
    get_status_badge_class,
    get_status_icon,
    get_prioritas_badge_class,
    get_prioritas_icon
)

disposisi_bp = Blueprint("disposisi", __name__)

VALID_STATUS = ["draft", "dikirim", "diproses", "selesai", "ditolak"]
VALID_PRIORITAS = ["rendah", "normal", "tinggi", "urgent"]
VALID_TIPE = ["masuk", "keluar"]


def _base_query_for_user():
    """Base query with proper joins and user filtering"""
    query = Disposisi.query.options(
        joinedload(Disposisi.surat_masuk),
        joinedload(Disposisi.surat_keluar),
        joinedload(Disposisi.dari_user),
        joinedload(Disposisi.kepada_user),
    )
    if current_user.role in ["admin", "pimpinan"]:
        return query
    return query.filter(
        or_(
            Disposisi.dari_user_id == current_user.id,
            Disposisi.kepada_user_id == current_user.id,
        )
    )


def _can_access(disposisi):
    """Check if current user can access disposisi"""
    if current_user.role in ["admin", "pimpinan"]:
        return True
    return current_user.id in [disposisi.dari_user_id, disposisi.kepada_user_id]


def _can_update(disposisi):
    """Check if current user can update disposisi"""
    if current_user.role in ["admin", "pimpinan"]:
        return True
    return current_user.id == disposisi.kepada_user_id


@disposisi_bp.route("/disposisi", methods=["GET"])
@login_required
def list_disposisi():
    try:
        current_app.logger.info(f"📋 List disposisi accessed by user {current_user.id} ({current_user.email})")
        
        page = request.args.get("page", 1, type=int)
        q = request.args.get("q", "").strip()
        status = request.args.get("status", "").strip().lower()
        tipe = request.args.get("tipe", "").strip().lower()

        current_app.logger.info(f"🔍 Filters - page: {page}, q: '{q}', status: '{status}', tipe: '{tipe}'")

        query = _base_query_for_user()

        if status in VALID_STATUS:
            query = query.filter(Disposisi.status == status)
        else:
            status = ""

        if tipe in VALID_TIPE:
            query = query.filter(Disposisi.surat_tipe == tipe)
        else:
            tipe = ""

        if q:
            like_q = f"%{q}%"
            query = query.outerjoin(
                SuratMasuk, Disposisi.surat_masuk_id == SuratMasuk.id_suratMasuk
            ).outerjoin(
                SuratKeluar, Disposisi.surat_keluar_id == SuratKeluar.id_suratKeluar
            ).filter(
                or_(
                    SuratMasuk.nomor_suratMasuk.ilike(like_q),
                    SuratMasuk.pengirim_suratMasuk.ilike(like_q),
                    SuratKeluar.nomor_suratKeluar.ilike(like_q),
                    SuratKeluar.penerima_suratKeluar.ilike(like_q),
                    Disposisi.perihal.ilike(like_q),
                    Disposisi.instruksi.ilike(like_q),
                )
            )

        pagination = query.order_by(desc(Disposisi.created_at)).paginate(
            page=page, per_page=15, error_out=False
        )

        current_app.logger.info(f"📊 Found {len(pagination.items)} disposisi on page {page}/{pagination.pages}")

        # Use helper function for stats
        stats = get_disposisi_stats(
            user_id=current_user.id,
            role=current_user.role
        )

        current_app.logger.info(f"✅ List disposisi loaded successfully")

        return render_template(
            "disposisi/list_disposisi.html",
            pagination=pagination,
            disposisi_list=pagination.items,
            stats=stats,
            q=q,
            status=status,
            tipe=tipe,
        )
    
    except Exception as e:
        current_app.logger.error(f"❌ Error in list_disposisi: {str(e)}")
        current_app.logger.error(f"💥 Error type: {type(e).__name__}")
        import traceback
        current_app.logger.error(f"📚 Traceback: {traceback.format_exc()}")
        
        flash(f"Terjadi kesalahan saat memuat daftar disposisi: {str(e)}", "error")
        return redirect(url_for("dashboard.dashboard"))


@disposisi_bp.route("/disposisi/buat", methods=["GET", "POST"])
@login_required
@role_required("admin", "pimpinan")
def buat_disposisi():
    pre_tipe = request.args.get("tipe", "").strip().lower()
    pre_surat_id = request.args.get("surat_id", type=int)

    if request.method == "POST":
        surat_tipe = request.form.get("surat_tipe", "").strip().lower()
        surat_id = request.form.get("surat_id", type=int)
        surat_masuk_id_form = request.form.get("surat_masuk_id", type=int)
        surat_keluar_id_form = request.form.get("surat_keluar_id", type=int)
        kepada_user_id = request.form.get("kepada_user_id", type=int)
        perihal = request.form.get("perihal", "").strip()
        instruksi = request.form.get("instruksi", "").strip()
        prioritas = request.form.get("prioritas", "normal").strip().lower()
        batas_waktu_raw = request.form.get("batas_waktu", "").strip()

        if surat_tipe not in VALID_TIPE:
            flash("Tipe surat tidak valid.", "error")
            return redirect(request.url)

        # Fallback: support non-JS submit by reading direct select fields.
        if not surat_id:
            if surat_tipe == "masuk":
                surat_id = surat_masuk_id_form
            elif surat_tipe == "keluar":
                surat_id = surat_keluar_id_form

        if not surat_id:
            flash("Pilih surat yang akan didisposisikan.", "error")
            return redirect(request.url)
        if not kepada_user_id:
            flash("Pilih penerima disposisi.", "error")
            return redirect(request.url)
        if not instruksi:
            flash("Instruksi disposisi wajib diisi.", "error")
            return redirect(request.url)
        if prioritas not in VALID_PRIORITAS:
            prioritas = "normal"
        if kepada_user_id == current_user.id:
            flash("Disposisi tidak bisa ditujukan ke diri sendiri.", "error")
            return redirect(request.url)

        penerima = User.query.get(kepada_user_id)
        if not penerima or not penerima.is_approved:
            flash("Penerima disposisi tidak valid.", "error")
            return redirect(request.url)

        surat_masuk_id = None
        surat_keluar_id = None
        if surat_tipe == "masuk":
            surat = SuratMasuk.query.get(surat_id)
            if not surat:
                flash("Surat masuk tidak ditemukan.", "error")
                return redirect(request.url)
            surat_masuk_id = surat.id_suratMasuk
        else:
            surat = SuratKeluar.query.get(surat_id)
            if not surat:
                flash("Surat keluar tidak ditemukan.", "error")
                return redirect(request.url)
            surat_keluar_id = surat.id_suratKeluar

        batas_waktu = None
        if batas_waktu_raw:
            try:
                batas_waktu = datetime.strptime(batas_waktu_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("Format batas waktu tidak valid.", "error")
                return redirect(request.url)

        existing = Disposisi.query.filter(
            and_(
                Disposisi.surat_tipe == surat_tipe,
                Disposisi.surat_masuk_id == surat_masuk_id,
                Disposisi.surat_keluar_id == surat_keluar_id,
                Disposisi.kepada_user_id == kepada_user_id,
                Disposisi.status.in_(["draft", "dikirim", "diproses"]),
            )
        ).first()
        if existing:
            flash("Sudah ada disposisi aktif untuk surat dan penerima tersebut.", "warning")
            return redirect(request.url)

        disposisi = Disposisi(
            surat_tipe=surat_tipe,
            surat_masuk_id=surat_masuk_id,
            surat_keluar_id=surat_keluar_id,
            dari_user_id=current_user.id,
            kepada_user_id=kepada_user_id,
            perihal=perihal or f"Disposisi surat {surat_tipe}",
            instruksi=instruksi,
            prioritas=prioritas,
            batas_waktu=batas_waktu,
            status="draft",  # Start as draft
        )
        db.session.add(disposisi)
        db.session.flush()  # Get ID before updating status
        
        # Use helper to update status to 'dikirim' (will sync surat status)
        success, message, _ = update_disposisi_status(
            disposisi.id,
            'dikirim',
            catatan=f"Disposisi dibuat oleh {current_user.email}"
        )
        
        if not success:
            db.session.rollback()
            flash(f"Error: {message}", "error")
            return redirect(request.url)
        
        db.session.commit()

        flash("Disposisi berhasil dibuat dan dikirim.", "success")
        return redirect(url_for("disposisi.detail_disposisi", disposisi_id=disposisi.id))

    users = (
        User.query.filter(User.is_approved == True, User.id != current_user.id)
        .order_by(User.email.asc())
        .all()
    )
    surat_masuk = (
        SuratMasuk.query.filter(SuratMasuk.status_suratMasuk == "approved")
        .order_by(desc(SuratMasuk.created_at))
        .limit(100)
        .all()
    )
    surat_keluar = (
        SuratKeluar.query.filter(SuratKeluar.status_suratKeluar == "approved")
        .order_by(desc(SuratKeluar.created_at))
        .limit(100)
        .all()
    )

    return render_template(
        "disposisi/buat_disposisi.html",
        users=users,
        surat_masuk=surat_masuk,
        surat_keluar=surat_keluar,
        pre_tipe=pre_tipe if pre_tipe in VALID_TIPE else "",
        pre_surat_id=pre_surat_id,
    )


@disposisi_bp.route("/disposisi/<int:disposisi_id>/detail", methods=["GET"])
@login_required
def detail_disposisi(disposisi_id):
    disposisi = Disposisi.query.options(
        joinedload(Disposisi.surat_masuk),
        joinedload(Disposisi.surat_keluar),
        joinedload(Disposisi.dari_user),
        joinedload(Disposisi.kepada_user),
    ).get_or_404(disposisi_id)

    if not _can_access(disposisi):
        flash("Anda tidak punya akses ke disposisi ini.", "error")
        return redirect(url_for("disposisi.list_disposisi"))

    # Get timeline for display
    timeline = get_disposisi_timeline(disposisi_id)

    return render_template(
        "disposisi/detail_disposisi.html",
        disposisi=disposisi,
        timeline=timeline,
        get_status_badge_class=get_status_badge_class,
        get_status_icon=get_status_icon,
        get_prioritas_badge_class=get_prioritas_badge_class,
        get_prioritas_icon=get_prioritas_icon
    )





@disposisi_bp.route("/disposisi/<int:disposisi_id>/update", methods=["POST"])
@login_required
def update_status_disposisi(disposisi_id):
    try:
        current_app.logger.info(f"🔄 Starting update for disposisi {disposisi_id} by user {current_user.id}")
        
        # Debug: Log all form data
        current_app.logger.info(f"📝 Form data received:")
        for key, value in request.form.items():
            current_app.logger.info(f"   {key}: {value}")
        
        disposisi = Disposisi.query.get_or_404(disposisi_id)
        current_app.logger.info(f"📋 Found disposisi: {disposisi.id}, current status: {disposisi.status}")

        if not _can_update(disposisi):
            current_app.logger.warning(f"❌ User {current_user.id} cannot update disposisi {disposisi_id}")
            flash("Anda tidak punya hak untuk memperbarui disposisi ini.", "error")
            return redirect(url_for("disposisi.list_disposisi"))

        status_baru = request.form.get("status", "").strip().lower()
        catatan_tindak_lanjut = request.form.get("catatan_tindak_lanjut", "").strip()
        alasan_penolakan = request.form.get("alasan_penolakan", "").strip()
        
        current_app.logger.info(f"📝 Parsed data - Status: '{status_baru}', Catatan: {len(catatan_tindak_lanjut)} chars, Alasan: {len(alasan_penolakan)} chars")
        
        # Validation
        if not status_baru:
            current_app.logger.warning("❌ Status baru tidak dipilih")
            flash("Status baru harus dipilih.", "error")
            return redirect(url_for("disposisi.detail_disposisi", disposisi_id=disposisi.id))
        
        if status_baru not in VALID_STATUS:
            current_app.logger.warning(f"❌ Status tidak valid: '{status_baru}'. Valid statuses: {VALID_STATUS}")
            flash("Status disposisi tidak valid.", "error")
            return redirect(url_for("disposisi.detail_disposisi", disposisi_id=disposisi.id))

        # Special validation for rejection
        if status_baru == "ditolak" and not alasan_penolakan and not catatan_tindak_lanjut:
            current_app.logger.warning("❌ Penolakan tanpa alasan atau catatan")
            flash("Alasan penolakan atau catatan tindak lanjut wajib diisi saat menolak disposisi.", "error")
            return redirect(url_for("disposisi.detail_disposisi", disposisi_id=disposisi.id))

        current_app.logger.info(f"✅ Validation passed, calling update_disposisi_status")
        
        # Use helper function to update status (will sync surat status and add history)
        success, message, updated_disposisi = update_disposisi_status(
            disposisi_id,
            status_baru,
            catatan=catatan_tindak_lanjut,
            alasan_penolakan=alasan_penolakan
        )
        
        current_app.logger.info(f"📊 Update result - Success: {success}, Message: '{message}'")
        
        if success:
            flash("Status disposisi berhasil diperbarui.", "success")
            current_app.logger.info(f"✅ Update successful, redirecting to detail page")
        else:
            flash(f"Gagal memperbarui status: {message}", "error")
            current_app.logger.error(f"❌ Update failed: {message}")
        
        return redirect(url_for("disposisi.detail_disposisi", disposisi_id=disposisi.id))
        
    except Exception as e:
        # Log the error for debugging
        current_app.logger.error(f"💥 CRITICAL ERROR updating disposisi {disposisi_id}: {str(e)}")
        current_app.logger.error(f"💥 Error type: {type(e).__name__}")
        import traceback
        current_app.logger.error(f"📚 Full traceback: {traceback.format_exc()}")
        
        # User-friendly error message
        flash(f"Terjadi kesalahan saat memperbarui disposisi: {str(e)}", "error")
        return redirect(url_for("disposisi.detail_disposisi", disposisi_id=disposisi_id))

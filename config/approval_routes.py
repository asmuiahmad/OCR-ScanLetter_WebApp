"""
Approval Routes Module
Handles approval/rejection of surat masuk and surat keluar by pimpinan (leaders)
"""

import logging
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
from flask_login import current_user, login_required
from sqlalchemy import desc

from config.extensions import db, csrf
from config.models import AuditLog, SuratKeluar, SuratMasuk
from config.route_utils import role_required

logger = logging.getLogger(__name__)
approval_bp = Blueprint("approval", __name__, url_prefix="/approval")


# ==================== SURAT MASUK APPROVAL ====================


@approval_bp.route("/surat-masuk/list", methods=["GET"])
@login_required
@role_required("pimpinan", "admin")
def list_pending_surat_masuk():
    """List semua surat masuk pending untuk persetujuan"""
    try:
        page = request.args.get("page", 1, type=int)
        status = request.args.get("status", "pending", type=str)
        search = request.args.get("search", "", type=str)

        query = SuratMasuk.query

        # Filter by status
        if status == "pending":
            query = query.filter_by(status_suratMasuk="pending")
        elif status == "approved":
            query = query.filter_by(status_suratMasuk="approved")
        elif status == "rejected":
            query = query.filter_by(status_suratMasuk="rejected")
        elif status == "all":
            pass
        else:
            query = query.filter_by(status_suratMasuk="pending")

        # Search filter
        if search:
            query = query.filter(
                (SuratMasuk.nomor_suratMasuk.ilike(f"%{search}%"))
                | (SuratMasuk.pengirim_suratMasuk.ilike(f"%{search}%"))
                | (SuratMasuk.isi_suratMasuk.ilike(f"%{search}%"))
            )

        # Order by tanggal terbaru
        query = query.order_by(desc(SuratMasuk.tanggal_suratMasuk))

        # Pagination
        pagination = query.paginate(page=page, per_page=10)
        surat_list = pagination.items

        pending_count = SuratMasuk.query.filter_by(status_suratMasuk="pending").count()
        approved_count = SuratMasuk.query.filter_by(
            status_suratMasuk="approved"
        ).count()
        rejected_count = SuratMasuk.query.filter_by(
            status_suratMasuk="rejected"
        ).count()

        return render_template(
            "approval/surat_masuk_approval_list.html",
            surat_list=surat_list,
            pagination=pagination,
            status=status,
            search=search,
            pending_count=pending_count,
            approved_count=approved_count,
            rejected_count=rejected_count,
        )

    except Exception as e:
        logger.error(f"Error in list_pending_surat_masuk: {str(e)}")
        flash("Terjadi kesalahan saat memuat daftar surat masuk.", "error")
        return redirect(url_for("main.index"))


@approval_bp.route("/surat-masuk/<int:surat_id>/detail", methods=["GET"])
@login_required
@role_required("pimpinan", "admin")
def surat_masuk_detail(surat_id):
    """Lihat detail surat masuk untuk persetujuan"""
    try:
        surat = SuratMasuk.query.get_or_404(surat_id)

        return render_template(
            "approval/surat_masuk_detail.html",
            surat=surat,
        )

    except Exception as e:
        logger.error(f"Error in surat_masuk_detail: {str(e)}")
        flash("Surat masuk tidak ditemukan.", "error")
        return redirect(url_for("approval.list_pending_surat_masuk"))


@approval_bp.route("/surat-masuk/<int:surat_id>/approve", methods=["POST"])
@login_required
@role_required("pimpinan", "admin")
def approve_surat_masuk(surat_id):
    """Approve surat masuk"""
    try:
        surat = SuratMasuk.query.get_or_404(surat_id)

        notes = request.form.get("approval_notes", "")

        # Update surat status
        surat.status_suratMasuk = "approved"
        surat.approved_by = current_user.email
        surat.approved_at = datetime.utcnow()
        surat.approval_notes = notes

        # Create audit log
        audit = AuditLog(
            entity_type="SuratMasuk",
            entity_id=surat_id,
            action="approved",
            performed_by=current_user.email,
            notes=f"Surat masuk disetujui oleh {current_user.email}. Catatan: {notes}",
        )

        db.session.add(audit)
        db.session.commit()

        logger.info(f"Surat Masuk {surat_id} approved by {current_user.email}")

        flash("Surat masuk berhasil disetujui!", "success")
        return redirect(url_for("approval.list_pending_surat_masuk"))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in approve_surat_masuk: {str(e)}")
        flash("Terjadi kesalahan saat menyetujui surat.", "error")
        return redirect(url_for("approval.surat_masuk_detail", surat_id=surat_id))


@approval_bp.route("/surat-masuk/<int:surat_id>/reject", methods=["POST"])
@login_required
@role_required("pimpinan", "admin")
def reject_surat_masuk(surat_id):
    """Reject surat masuk"""
    try:
        surat = SuratMasuk.query.get_or_404(surat_id)

        reason = request.form.get("rejection_reason", "")
        if not reason:
            flash("Alasan penolakan tidak boleh kosong.", "error")
            return redirect(url_for("approval.surat_masuk_detail", surat_id=surat_id))

        # Update surat status
        surat.status_suratMasuk = "rejected"
        surat.approved_by = current_user.email
        surat.approved_at = datetime.utcnow()
        surat.rejected_reason = reason

        # Create audit log
        audit = AuditLog(
            entity_type="SuratMasuk",
            entity_id=surat_id,
            action="rejected",
            performed_by=current_user.email,
            notes=f"Surat masuk ditolak oleh {current_user.email}. Alasan: {reason}",
        )

        db.session.add(audit)
        db.session.commit()

        logger.info(
            f"Surat Masuk {surat_id} rejected by {current_user.email}: {reason}"
        )

        flash("Surat masuk berhasil ditolak.", "success")
        return redirect(url_for("approval.list_pending_surat_masuk"))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in reject_surat_masuk: {str(e)}")
        flash("Terjadi kesalahan saat menolak surat.", "error")
        return redirect(url_for("approval.surat_masuk_detail", surat_id=surat_id))


@approval_bp.route("/surat-masuk/<int:surat_id>/approve-api", methods=["POST"])
@csrf.exempt
@login_required
@role_required("pimpinan", "admin")
def approve_surat_masuk_api(surat_id):
    """API endpoint untuk approve surat masuk (AJAX)"""
    try:
        surat = SuratMasuk.query.get_or_404(surat_id)

        data = request.get_json() or {}
        notes = data.get("approval_notes", "")

        # Update surat status
        surat.status_suratMasuk = "approved"
        surat.approved_by = current_user.email
        surat.approved_at = datetime.utcnow()
        surat.approval_notes = notes

        # Create audit log
        audit = AuditLog(
            entity_type="SuratMasuk",
            entity_id=surat_id,
            action="approved",
            performed_by=current_user.email,
            notes=f"Surat masuk disetujui. Catatan: {notes}",
        )

        db.session.add(audit)
        db.session.commit()

        logger.info(f"Surat Masuk {surat_id} approved by {current_user.email}")

        return jsonify(
            {
                "success": True,
                "message": "Surat masuk berhasil disetujui",
                "surat_id": surat_id,
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in approve_surat_masuk_api: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@approval_bp.route("/surat-masuk/<int:surat_id>/reject-api", methods=["POST"])
@csrf.exempt
@login_required
@role_required("pimpinan", "admin")
def reject_surat_masuk_api(surat_id):
    """API endpoint untuk reject surat masuk (AJAX)"""
    try:
        surat = SuratMasuk.query.get_or_404(surat_id)

        data = request.get_json() or {}
        reason = data.get("rejection_reason", "")

        if not reason:
            return jsonify(
                {"success": False, "error": "Alasan penolakan diperlukan"}
            ), 400

        # Update surat status
        surat.status_suratMasuk = "rejected"
        surat.approved_by = current_user.email
        surat.approved_at = datetime.utcnow()
        surat.rejected_reason = reason

        # Create audit log
        audit = AuditLog(
            entity_type="SuratMasuk",
            entity_id=surat_id,
            action="rejected",
            performed_by=current_user.email,
            notes=f"Surat masuk ditolak. Alasan: {reason}",
        )

        db.session.add(audit)
        db.session.commit()

        logger.info(f"Surat Masuk {surat_id} rejected by {current_user.email}")

        return jsonify(
            {
                "success": True,
                "message": "Surat masuk berhasil ditolak",
                "surat_id": surat_id,
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in reject_surat_masuk_api: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== SURAT KELUAR APPROVAL ====================


@approval_bp.route("/surat-keluar/list", methods=["GET"])
@login_required
@role_required("pimpinan", "admin")
def list_pending_surat_keluar():
    """List semua surat keluar pending untuk persetujuan"""
    try:
        page = request.args.get("page", 1, type=int)
        status = request.args.get("status", "pending", type=str)
        search = request.args.get("search", "", type=str)

        query = SuratKeluar.query

        # Filter by status
        if status == "pending":
            query = query.filter_by(status_suratKeluar="pending")
        elif status == "approved":
            query = query.filter_by(status_suratKeluar="approved")
        elif status == "rejected":
            query = query.filter_by(status_suratKeluar="rejected")
        elif status == "all":
            pass
        else:
            query = query.filter_by(status_suratKeluar="pending")

        # Search filter
        if search:
            query = query.filter(
                (SuratKeluar.nomor_suratKeluar.ilike(f"%{search}%"))
                | (SuratKeluar.pengirim_suratKeluar.ilike(f"%{search}%"))
                | (SuratKeluar.isi_suratKeluar.ilike(f"%{search}%"))
            )

        # Order by tanggal terbaru
        query = query.order_by(desc(SuratKeluar.tanggal_suratKeluar))

        # Pagination
        pagination = query.paginate(page=page, per_page=10)
        surat_list = pagination.items

        pending_count = SuratKeluar.query.filter_by(
            status_suratKeluar="pending"
        ).count()
        approved_count = SuratKeluar.query.filter_by(
            status_suratKeluar="approved"
        ).count()
        rejected_count = SuratKeluar.query.filter_by(
            status_suratKeluar="rejected"
        ).count()

        return render_template(
            "approval/surat_keluar_approval_list.html",
            surat_list=surat_list,
            pagination=pagination,
            status=status,
            search=search,
            pending_count=pending_count,
            approved_count=approved_count,
            rejected_count=rejected_count,
        )

    except Exception as e:
        logger.error(f"Error in list_pending_surat_keluar: {str(e)}")
        flash("Terjadi kesalahan saat memuat daftar surat keluar.", "error")
        return redirect(url_for("main.index"))


@approval_bp.route("/surat-keluar/<int:surat_id>/detail", methods=["GET"])
@login_required
@role_required("pimpinan", "admin")
def surat_keluar_detail(surat_id):
    """Lihat detail surat keluar untuk persetujuan"""
    try:
        surat = SuratKeluar.query.get_or_404(surat_id)

        return render_template(
            "approval/surat_keluar_detail.html",
            surat=surat,
        )

    except Exception as e:
        logger.error(f"Error in surat_keluar_detail: {str(e)}")
        flash("Surat keluar tidak ditemukan.", "error")
        return redirect(url_for("approval.list_pending_surat_keluar"))


@approval_bp.route("/surat-keluar/<int:surat_id>/approve", methods=["POST"])
@login_required
@role_required("pimpinan", "admin")
def approve_surat_keluar(surat_id):
    """Approve surat keluar"""
    try:
        surat = SuratKeluar.query.get_or_404(surat_id)

        notes = request.form.get("approval_notes", "")

        # Update surat status
        surat.status_suratKeluar = "approved"
        surat.approved_by = current_user.email
        surat.approved_at = datetime.utcnow()
        surat.approval_notes = notes

        # Create audit log
        audit = AuditLog(
            entity_type="SuratKeluar",
            entity_id=surat_id,
            action="approved",
            performed_by=current_user.email,
            notes=f"Surat keluar disetujui oleh {current_user.email}. Catatan: {notes}",
        )

        db.session.add(audit)
        db.session.commit()

        logger.info(f"Surat Keluar {surat_id} approved by {current_user.email}")

        flash("Surat keluar berhasil disetujui!", "success")
        return redirect(url_for("approval.list_pending_surat_keluar"))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in approve_surat_keluar: {str(e)}")
        flash("Terjadi kesalahan saat menyetujui surat.", "error")
        return redirect(url_for("approval.surat_keluar_detail", surat_id=surat_id))


@approval_bp.route("/surat-keluar/<int:surat_id>/reject", methods=["POST"])
@login_required
@role_required("pimpinan", "admin")
def reject_surat_keluar(surat_id):
    """Reject surat keluar"""
    try:
        surat = SuratKeluar.query.get_or_404(surat_id)

        reason = request.form.get("rejection_reason", "")
        if not reason:
            flash("Alasan penolakan tidak boleh kosong.", "error")
            return redirect(url_for("approval.surat_keluar_detail", surat_id=surat_id))

        # Update surat status
        surat.status_suratKeluar = "rejected"
        surat.approved_by = current_user.email
        surat.approved_at = datetime.utcnow()
        surat.rejected_reason = reason

        # Create audit log
        audit = AuditLog(
            entity_type="SuratKeluar",
            entity_id=surat_id,
            action="rejected",
            performed_by=current_user.email,
            notes=f"Surat keluar ditolak oleh {current_user.email}. Alasan: {reason}",
        )

        db.session.add(audit)
        db.session.commit()

        logger.info(
            f"Surat Keluar {surat_id} rejected by {current_user.email}: {reason}"
        )

        flash("Surat keluar berhasil ditolak.", "success")
        return redirect(url_for("approval.list_pending_surat_keluar"))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in reject_surat_keluar: {str(e)}")
        flash("Terjadi kesalahan saat menolak surat.", "error")
        return redirect(url_for("approval.surat_keluar_detail", surat_id=surat_id))


@approval_bp.route("/surat-keluar/<int:surat_id>/approve-api", methods=["POST"])
@csrf.exempt
@login_required
@role_required("pimpinan", "admin")
def approve_surat_keluar_api(surat_id):
    """API endpoint untuk approve surat keluar (AJAX)"""
    try:
        surat = SuratKeluar.query.get_or_404(surat_id)

        data = request.get_json() or {}
        notes = data.get("approval_notes", "")

        # Update surat status
        surat.status_suratKeluar = "approved"
        surat.approved_by = current_user.email
        surat.approved_at = datetime.utcnow()
        surat.approval_notes = notes

        # Create audit log
        audit = AuditLog(
            entity_type="SuratKeluar",
            entity_id=surat_id,
            action="approved",
            performed_by=current_user.email,
            notes=f"Surat keluar disetujui. Catatan: {notes}",
        )

        db.session.add(audit)
        db.session.commit()

        logger.info(f"Surat Keluar {surat_id} approved by {current_user.email}")

        return jsonify(
            {
                "success": True,
                "message": "Surat keluar berhasil disetujui",
                "surat_id": surat_id,
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in approve_surat_keluar_api: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@approval_bp.route("/surat-keluar/<int:surat_id>/reject-api", methods=["POST"])
@csrf.exempt
@login_required
@role_required("pimpinan", "admin")
def reject_surat_keluar_api(surat_id):
    """API endpoint untuk reject surat keluar (AJAX)"""
    try:
        surat = SuratKeluar.query.get_or_404(surat_id)

        data = request.get_json() or {}
        reason = data.get("rejection_reason", "")

        if not reason:
            return jsonify(
                {"success": False, "error": "Alasan penolakan diperlukan"}
            ), 400

        # Update surat status
        surat.status_suratKeluar = "rejected"
        surat.approved_by = current_user.email
        surat.approved_at = datetime.utcnow()
        surat.rejected_reason = reason

        # Create audit log
        audit = AuditLog(
            entity_type="SuratKeluar",
            entity_id=surat_id,
            action="rejected",
            performed_by=current_user.email,
            notes=f"Surat keluar ditolak. Alasan: {reason}",
        )

        db.session.add(audit)
        db.session.commit()

        logger.info(f"Surat Keluar {surat_id} rejected by {current_user.email}")

        return jsonify(
            {
                "success": True,
                "message": "Surat keluar berhasil ditolak",
                "surat_id": surat_id,
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in reject_surat_keluar_api: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== STATS & ANALYTICS ====================


@approval_bp.route("/stats", methods=["GET"])
@login_required
@role_required("pimpinan", "admin")
def approval_stats():
    """Halaman statistik persetujuan"""
    try:
        from sqlalchemy import func

        surat_masuk_pending = SuratMasuk.query.filter_by(status_suratMasuk="pending").count()
        surat_masuk_approved = SuratMasuk.query.filter_by(status_suratMasuk="approved").count()
        surat_masuk_rejected = SuratMasuk.query.filter_by(status_suratMasuk="rejected").count()

        surat_keluar_pending = SuratKeluar.query.filter_by(status_suratKeluar="pending").count()
        surat_keluar_approved = SuratKeluar.query.filter_by(status_suratKeluar="approved").count()
        surat_keluar_rejected = SuratKeluar.query.filter_by(status_suratKeluar="rejected").count()

        # Riwayat persetujuan terbaru (10 terakhir)
        recent_masuk = (
            SuratMasuk.query
            .filter(SuratMasuk.status_suratMasuk.in_(["approved", "rejected"]))
            .filter(SuratMasuk.approved_by.isnot(None))
            .order_by(desc(SuratMasuk.approved_at))
            .limit(10)
            .all()
        )
        recent_keluar = (
            SuratKeluar.query
            .filter(SuratKeluar.status_suratKeluar.in_(["approved", "rejected"]))
            .filter(SuratKeluar.approved_by.isnot(None))
            .order_by(desc(SuratKeluar.approved_at))
            .limit(10)
            .all()
        )

        # Gabung dan urutkan berdasarkan approved_at
        recent_activity = []
        for s in recent_masuk:
            recent_activity.append({
                "type": "masuk",
                "nomor": s.nomor_suratMasuk or "-",
                "pengirim": s.pengirim_suratMasuk or "-",
                "status": s.status_suratMasuk,
                "approved_by": s.approved_by,
                "approved_at": s.approved_at,
                "notes": s.approval_notes or s.rejected_reason or "-",
            })
        for s in recent_keluar:
            recent_activity.append({
                "type": "keluar",
                "nomor": s.nomor_suratKeluar or "-",
                "pengirim": s.pengirim_suratKeluar or "-",
                "status": s.status_suratKeluar,
                "approved_by": s.approved_by,
                "approved_at": s.approved_at,
                "notes": s.approval_notes or s.rejected_reason or "-",
            })
        recent_activity.sort(key=lambda x: x["approved_at"] or datetime.min, reverse=True)
        recent_activity = recent_activity[:10]

        return render_template(
            "approval/stats.html",
            surat_masuk_pending=surat_masuk_pending,
            surat_masuk_approved=surat_masuk_approved,
            surat_masuk_rejected=surat_masuk_rejected,
            surat_keluar_pending=surat_keluar_pending,
            surat_keluar_approved=surat_keluar_approved,
            surat_keluar_rejected=surat_keluar_rejected,
            recent_activity=recent_activity,
        )
    except Exception as e:
        logger.error(f"Error in approval_stats: {str(e)}")
        flash("Terjadi kesalahan saat memuat statistik.", "error")
        return redirect(url_for("main.index"))

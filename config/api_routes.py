import math

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import or_

from config.extensions import db
from config.models import SuratKeluar, SuratMasuk, UserLoginLog
from config.route_utils import role_required

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/notifications/count", methods=["GET"])
@login_required
def get_notification_count():
    """Get notification count for current user - only for admin or pimpinan"""
    try:
        # Only admin or pimpinan can view notification counts
        if current_user.role not in ("pimpinan", "admin"):
            # Return empty but successful payload to avoid exposing details to unauthorized users
            return jsonify(
                {
                    "success": True,
                    "pending_count": 0,
                    "message": "Akses terbatas untuk admin atau pimpinan",
                }
            )

        # Count pending surat masuk and surat keluar
        pending_masuk = SuratMasuk.query.filter_by(status_suratMasuk="pending").count()
        pending_keluar = SuratKeluar.query.filter_by(
            status_suratKeluar="pending"
        ).count()
        total_pending = pending_masuk + pending_keluar

        return jsonify(
            {
                "success": True,
                "pending_count": total_pending,
                "pending_masuk": pending_masuk,
                "pending_keluar": pending_keluar,
                "message": f"{total_pending} surat menunggu persetujuan"
                if total_pending > 0
                else "Tidak ada surat yang menunggu persetujuan",
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error getting notification count: {str(e)}")
        return jsonify(
            {
                "success": False,
                "message": "Terjadi kesalahan saat memuat jumlah notifikasi",
            }
        ), 500


@api_bp.route("/notifications/recent", methods=["GET"])
@login_required
def get_recent_notifications():
    """Get recent pending surat masuk and surat keluar for notifications - only for admin or pimpinan"""
    try:
        # Only admin or pimpinan can view approval notifications
        if current_user.role not in ("pimpinan", "admin"):
            return jsonify(
                {
                    "success": False,
                    "message": "Akses ditolak. Hanya admin atau pimpinan yang dapat melihat notifikasi persetujuan surat.",
                }
            ), 403

        # Fetch pending surat masuk, ordered by creation time (newest first)
        recent_masuk = (
            SuratMasuk.query.filter_by(status_suratMasuk="pending")
            .order_by(SuratMasuk.created_at.desc())
            .limit(10)
            .all()
        )

        # Fetch pending surat keluar, ordered by creation time (newest first)
        recent_keluar = (
            SuratKeluar.query.filter_by(status_suratKeluar="pending")
            .order_by(SuratKeluar.created_at.desc())
            .limit(10)
            .all()
        )

        # Count total pending (separate query for accuracy despite limit=10)
        pending_masuk = SuratMasuk.query.filter_by(status_suratMasuk="pending").count()
        pending_keluar = SuratKeluar.query.filter_by(status_suratKeluar="pending").count()

        surat_list = []

        # Add surat masuk
        for surat in recent_masuk:
            surat_data = {
                "id": surat.id_suratMasuk,
                "type": "masuk",
                "pengirim": surat.pengirim_suratMasuk or "Pengirim tidak diketahui",
                "penerima": surat.penerima_suratMasuk or "Penerima tidak diketahui",
                "nomor": surat.nomor_suratMasuk or "Nomor tidak tersedia",
                "tanggal_display": surat.tanggal_suratMasuk.strftime("%d %b %Y")
                if surat.tanggal_suratMasuk
                else "Tanggal tidak diketahui",
                "created_at_display": surat.created_at.strftime("%d %b %Y %H:%M")
                if surat.created_at
                else "",
                "created_at_sort": surat.created_at.isoformat()
                if surat.created_at
                else "",
                "ringkasan": (surat.isi_suratMasuk[:100] + "...")
                if surat.isi_suratMasuk and len(surat.isi_suratMasuk) > 100
                else (surat.isi_suratMasuk or ""),
            }
            surat_list.append(surat_data)

        # Add surat keluar
        for surat in recent_keluar:
            surat_data = {
                "id": surat.id_suratKeluar,
                "type": "keluar",
                "pengirim": surat.pengirim_suratKeluar or "Pengirim tidak diketahui",
                "penerima": surat.penerima_suratKeluar or "Penerima tidak diketahui",
                "nomor": surat.nomor_suratKeluar or "Nomor tidak tersedia",
                "tanggal_display": surat.tanggal_suratKeluar.strftime("%d %b %Y")
                if surat.tanggal_suratKeluar
                else "Tanggal tidak diketahui",
                "created_at_display": surat.created_at.strftime("%d %b %Y %H:%M")
                if surat.created_at
                else "",
                "created_at_sort": surat.created_at.isoformat()
                if surat.created_at
                else "",
                "ringkasan": (surat.isi_suratKeluar[:100] + "...")
                if surat.isi_suratKeluar and len(surat.isi_suratKeluar) > 100
                else (surat.isi_suratKeluar or ""),
            }
            surat_list.append(surat_data)

        # Sort by created_at (newest first)
        surat_list.sort(key=lambda x: x.get("created_at_sort") or "", reverse=True)

        # Limit total to 15 items
        surat_list = surat_list[:15]

        return jsonify(
            {
                "success": True,
                "surat_list": surat_list,
                "pending_count": len(surat_list),
                "pending_masuk": pending_masuk,
                "pending_keluar": pending_keluar,
                "message": f"Ditemukan {len(surat_list)} surat yang menunggu persetujuan",
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error getting recent notifications: {str(e)}")
        return jsonify(
            {"success": False, "message": "Terjadi kesalahan saat memuat notifikasi"}
        ), 500


@api_bp.route("/surat-keluar/detail/<int:surat_id>", methods=["GET"])
@login_required
@role_required("pimpinan", "admin")
def get_surat_masuk_detail(surat_id):
    """Get surat masuk detail"""
    try:
        surat = SuratMasuk.query.get(surat_id)
        if not surat:
            return jsonify(
                {
                    "success": False,
                    "message": f"Surat dengan ID {surat_id} tidak ditemukan",
                }
            ), 404

        try:
            tanggal_str = (
                surat.tanggal_suratMasuk.strftime("%d/%m/%Y")
                if surat.tanggal_suratMasuk
                else ""
            )
        except Exception as e:
            current_app.logger.error(f"Error formatting date: {str(e)}")
            tanggal_str = ""

        try:
            created_at_str = (
                surat.created_at.strftime("%Y-%m-%d %H:%M") if surat.created_at else ""
            )
        except Exception as e:
            current_app.logger.error(f"Error formatting created_at: {str(e)}")
            created_at_str = ""

        surat_data = {
            "id_suratMasuk": surat.id_suratMasuk,
            "nomor_suratMasuk": str(surat.nomor_suratMasuk)
            if surat.nomor_suratMasuk
            else "",
            "tanggal_suratMasuk": tanggal_str,
            "pengirim_suratMasuk": str(surat.pengirim_suratMasuk)
            if surat.pengirim_suratMasuk
            else "",
            "penerima_suratMasuk": str(surat.penerima_suratMasuk)
            if surat.penerima_suratMasuk
            else "",
            "isi_suratMasuk": str(surat.isi_suratMasuk) if surat.isi_suratMasuk else "",
            "status_suratMasuk": str(surat.status_suratMasuk)
            if surat.status_suratMasuk
            else "pending",
            "file_suratMasuk": bool(surat.file_suratMasuk),
            "has_gambar": bool(surat.gambar_suratMasuk),
            "created_at": created_at_str,
        }

        current_app.logger.info(f"Successfully retrieved surat data for ID {surat_id}")

        return jsonify({"success": True, "surat": surat_data})

    except Exception as e:
        current_app.logger.error(
            f"Error getting surat keluar detail for ID {surat_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify(
            {"success": False, "message": f"Gagal memuat detail surat: {str(e)}"}
        ), 500


@api_bp.route("/chart-data")
@login_required
def chart_data():
    """Get chart data for dashboard"""
    try:
        # Get monthly data for the current year
        from datetime import datetime

        from sqlalchemy import extract, func

        current_year = datetime.now().year

        monthly_data = (
            db.session.query(
                extract("month", SuratMasuk.tanggal_suratMasuk).label("month"),
                func.count(SuratMasuk.id_suratMasuk).label("count"),
            )
            .filter(extract("year", SuratMasuk.tanggal_suratMasuk) == current_year)
            .group_by(extract("month", SuratMasuk.tanggal_suratMasuk))
            .all()
        )

        data = {
            "labels": [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ],
            "datasets": [
                {
                    "label": "Surat Masuk",
                    "data": [0] * 12,
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 1,
                }
            ],
        }

        for month, count in monthly_data:
            if month:
                data["datasets"][0]["data"][int(month) - 1] = count

        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error getting chart data: {str(e)}")
        return jsonify({"error": "Failed to load chart data"}), 500


@api_bp.route("/user-login-logs")
@login_required
def get_user_login_logs():
    """Get user login logs with pagination - Admin only"""
    if not current_user.is_admin:
        return jsonify(
            {"success": False, "message": "Tidak memiliki izin untuk melihat log login"}
        ), 403
    
    try:
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        date_filter = request.args.get("date")
        user_filter = request.args.get("user")
        status_filter = request.args.get("status")
        user_id_filter = request.args.get("user_id", type=int)

        query = UserLoginLog.query

        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                query = query.filter(
                    db.func.date(UserLoginLog.login_time) == filter_date
                )
            except ValueError:
                return jsonify(
                    {"success": False, "message": "Invalid date format. Use YYYY-MM-DD"}
                ), 400

        if user_filter:
            query = query.filter(UserLoginLog.user_email.ilike(f"%{user_filter}%"))

        if status_filter:
            query = query.filter(UserLoginLog.status == status_filter)

        if user_id_filter:
            query = query.filter(UserLoginLog.user_id == user_id_filter)

        query = query.order_by(UserLoginLog.login_time.desc())

        total_count = query.count()

        offset = (page - 1) * per_page
        logs = query.offset(offset).limit(per_page).all()

        logs_data = [log.to_dict() for log in logs]

        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

        pagination_info = {
            "current_page": page,
            "total_pages": total_pages,
            "total": total_count,
            "showing": len(logs_data),
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "per_page": per_page,
        }

        return jsonify(
            {"success": True, "logs": logs_data, "pagination": pagination_info}
        )

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Error loading login logs: {str(e)}"}
        ), 500


@api_bp.route("/update-ocr-accuracy/<int:id>", methods=["POST"])
@login_required
@role_required("admin", "pimpinan")
def update_ocr_accuracy(id):
    """Update OCR accuracy for a specific document"""
    try:
        surat_type = request.form.get("type")  # 'masuk' or 'keluar'

        if surat_type == "masuk":
            surat = SuratKeluar.query.get_or_404(id)
            try:
                from config.ocr_utils import calculate_overall_ocr_accuracy

                surat.ocr_accuracy_suratKeluar = calculate_overall_ocr_accuracy(
                    surat, "suratKeluar"
                )
                accuracy = surat.ocr_accuracy_suratKeluar
            except ImportError:
                # Fallback if ocr_utils is not available
                accuracy = 0
        elif surat_type == "keluar":
            surat = SuratMasuk.query.get_or_404(id)
            try:
                from config.ocr_utils import calculate_overall_ocr_accuracy

                surat.ocr_accuracy_suratMasuk = calculate_overall_ocr_accuracy(
                    surat, "suratMasuk"
                )
                accuracy = surat.ocr_accuracy_suratMasuk
            except ImportError:
                accuracy = 0
        else:
            return jsonify({"success": False, "error": "Invalid surat type"})

        db.session.commit()
        return jsonify({"success": True, "accuracy": accuracy})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating OCR accuracy: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/csrf-token", methods=["GET"])
@login_required
def get_csrf_token():
    """Get fresh CSRF token"""
    try:
        from flask_wtf.csrf import generate_csrf
        token = generate_csrf()
        return jsonify({"success": True, "csrf_token": token})
    except Exception as e:
        current_app.logger.error(f"Error generating CSRF token: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/pegawai/quota/<nip>", methods=["GET"])
@login_required
def get_pegawai_quota(nip):
    """Get leave quota for an employee by NIP"""
    try:
        from config.models import Pegawai

        pegawai = Pegawai.query.filter_by(nip=nip).first()
        if not pegawai:
            return jsonify({"success": False, "message": "Pegawai tidak ditemukan"}), 404

        return jsonify(
            {
                "success": True,
                "nip": pegawai.nip,
                "nama": pegawai.nama,
                "batas_cuti": pegawai.batas_cuti,
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error getting pegawai quota: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/pegawai/search", methods=["GET"])
@login_required
def search_pegawai():
    """Search pegawai by name or NIP"""
    try:
        from config.models import Pegawai

        query = request.args.get("q", "").strip()
        if not query:
            # Return all pegawai if no query
            pegawai_list = Pegawai.query.limit(20).all()
        else:
            # Search by name or NIP
            pegawai_list = (
                Pegawai.query.filter(
                    or_(
                        Pegawai.nama.ilike(f"%{query}%"),
                        Pegawai.nip.ilike(f"%{query}%"),
                    )
                )
                .limit(20)
                .all()
            )
        
        # Format data for frontend
        results = []
        for pegawai in pegawai_list:
            results.append({
                "id": pegawai.id,
                "nama": pegawai.nama,
                "nip": pegawai.nip,
                "jabatan": pegawai.jabatan or "",
                "golongan": pegawai.golongan or "",
                "nomor_telpon": pegawai.nomor_telpon or "",
                "batas_cuti": pegawai.batas_cuti,
                "unit_kerja": getattr(pegawai, 'unit_kerja', None) or pegawai.jabatan or "",
                "masa_kerja": getattr(pegawai, 'masa_kerja', None) or "",
                "alamat": ""
            })
        
        return jsonify({"success": True, "pegawai": results})
    except Exception as e:
        current_app.logger.error(f"Error searching pegawai: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({"success": False, "message": "Terjadi kesalahan saat mencari data pegawai"}), 500


@api_bp.route("/pegawai/<int:pegawai_id>", methods=["GET"])
@login_required
def get_pegawai_detail(pegawai_id):
    """Get detailed pegawai information by ID"""
    try:
        from config.models import Pegawai
        from datetime import date

        pegawai = Pegawai.query.get_or_404(pegawai_id)
        
        # Calculate masa kerja if tanggal_lahir is available
        masa_kerja = getattr(pegawai, 'masa_kerja', None) or ""
        if not masa_kerja and pegawai.tanggal_lahir:
            today = date.today()
            age = today.year - pegawai.tanggal_lahir.year - ((today.month, today.day) < (pegawai.tanggal_lahir.month, pegawai.tanggal_lahir.day))
            masa_kerja = f"{age} tahun"
        
        result = {
            "id": pegawai.id,
            "nama": pegawai.nama,
            "nip": pegawai.nip,
            "jabatan": pegawai.jabatan or "",
            "golongan": pegawai.golongan or "",
            "nomor_telpon": pegawai.nomor_telpon or "",
            "batas_cuti": pegawai.batas_cuti,
            "unit_kerja": getattr(pegawai, 'unit_kerja', None) or pegawai.jabatan or "",
            "masa_kerja": masa_kerja,
            "alamat": "",
            "tanggal_lahir": pegawai.tanggal_lahir.strftime("%Y-%m-%d") if pegawai.tanggal_lahir else "",
            "jenis_kelamin": pegawai.jenis_kelamin or "",
            "agama": pegawai.agama or "",
            "riwayat_pendidikan": pegawai.riwayat_pendidikan or "",
            "riwayat_pekerjaan": pegawai.riwayat_pekerjaan or ""
        }
        
        return jsonify({"success": True, "pegawai": result})
    except Exception as e:
        current_app.logger.error(f"Error getting pegawai detail: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({"success": False, "message": "Terjadi kesalahan saat mengambil data pegawai"}), 500


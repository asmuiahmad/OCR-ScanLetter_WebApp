"""
Helper functions untuk sistem disposisi
Menangani status sync, history tracking, dan notifikasi
"""

from datetime import datetime, date, timedelta
from config.extensions import db
from config.models import Disposisi, DisposisiHistory, SuratMasuk, SuratKeluar
from flask import current_app
from flask_login import current_user
from sqlalchemy import or_


def update_disposisi_status(disposisi_id, new_status, catatan=None, alasan_penolakan=None):
    """
    Update status disposisi dan sync dengan status surat
    
    Args:
        disposisi_id: ID disposisi
        new_status: Status baru (draft, dikirim, diproses, selesai, ditolak)
        catatan: Catatan tambahan
        alasan_penolakan: Alasan jika ditolak
    
    Returns:
        tuple: (success: bool, message: str, disposisi: Disposisi)
    """
    try:
        current_app.logger.info(f"🔧 Helper: Starting update_disposisi_status for ID {disposisi_id}")
        current_app.logger.info(f"🔧 Helper: new_status='{new_status}', catatan={len(catatan) if catatan else 0} chars, alasan={len(alasan_penolakan) if alasan_penolakan else 0} chars")
        
        disposisi = Disposisi.query.get(disposisi_id)
        if not disposisi:
            current_app.logger.error(f"❌ Helper: Disposisi {disposisi_id} not found")
            return False, "Disposisi tidak ditemukan", None
        
        old_status = disposisi.status
        current_app.logger.info(f"🔧 Helper: Found disposisi, old_status='{old_status}', new_status='{new_status}'")
        
        # Validate status transition - make it more flexible
        valid_transitions = {
            'draft': ['dikirim', 'ditolak'],
            'dikirim': ['diproses', 'ditolak', 'dikirim'],  # Allow re-sending
            'diproses': ['selesai', 'ditolak', 'diproses'],  # Allow staying in process
            'selesai': ['selesai'],  # Allow updating notes when finished
            'ditolak': ['draft', 'dikirim']   # Allow restarting after rejection
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            # More flexible validation - allow admin/pimpinan to override
            from flask_login import current_user
            if not (current_user.is_authenticated and current_user.role in ['admin', 'pimpinan']):
                current_app.logger.warning(f"❌ Helper: Invalid transition {old_status} → {new_status} for user role {current_user.role if current_user.is_authenticated else 'anonymous'}")
                return False, f"Transisi dari {old_status} ke {new_status} tidak diizinkan", None
            else:
                current_app.logger.info(f"✅ Helper: Admin override allowed for transition {old_status} → {new_status}")
        
        # Update status
        current_app.logger.info(f"🔧 Helper: Updating status from '{old_status}' to '{new_status}'")
        disposisi.status = new_status
        
        # Update timestamps based on status
        if new_status == 'dikirim' and not disposisi.tanggal_dikirim:
            disposisi.tanggal_dikirim = datetime.now()
            current_app.logger.info(f"🔧 Helper: Set tanggal_dikirim")
        elif new_status == 'diproses' and not disposisi.tanggal_diproses:
            disposisi.tanggal_diproses = datetime.now()
            current_app.logger.info(f"🔧 Helper: Set tanggal_diproses")
        elif new_status == 'selesai':
            # Check if tanggal_selesai column exists
            if hasattr(disposisi, 'tanggal_selesai') and not disposisi.tanggal_selesai:
                disposisi.tanggal_selesai = datetime.now()
                current_app.logger.info(f"🔧 Helper: Set tanggal_selesai")
            elif not hasattr(disposisi, 'tanggal_selesai'):
                current_app.logger.warning(f"⚠️ Helper: tanggal_selesai field not found in model")
        
        # Update catatan if provided
        if catatan:
            disposisi.catatan_tindak_lanjut = catatan
            current_app.logger.info(f"🔧 Helper: Updated catatan_tindak_lanjut")
        
        # Update alasan penolakan if ditolak
        if new_status == 'ditolak' and alasan_penolakan:
            disposisi.alasan_penolakan = alasan_penolakan
            current_app.logger.info(f"🔧 Helper: Updated alasan_penolakan")
        
        # Sync status surat (don't fail if this fails)
        try:
            current_app.logger.info(f"🔧 Helper: Syncing surat status...")
            sync_surat_status(disposisi, new_status)
            current_app.logger.info(f"✅ Helper: Surat status synced successfully")
        except Exception as sync_error:
            current_app.logger.error(f"❌ Helper: Error syncing surat status: {str(sync_error)}")
            # Continue with disposisi update even if surat sync fails
        
        # Add to history (don't fail if this fails)
        try:
            current_app.logger.info(f"🔧 Helper: Adding to history...")
            add_disposisi_history(
                disposisi_id=disposisi_id,
                status_lama=old_status,
                status_baru=new_status,
                catatan=catatan,
                user_id=current_user.id if current_user.is_authenticated else None
            )
            current_app.logger.info(f"✅ Helper: History added successfully")
        except Exception as history_error:
            current_app.logger.error(f"❌ Helper: Error adding disposisi history: {str(history_error)}")
            # Continue with disposisi update even if history fails
        
        # Commit the main disposisi changes
        current_app.logger.info(f"🔧 Helper: Committing database changes...")
        db.session.commit()
        current_app.logger.info(f"✅ Helper: Database committed successfully")
        
        # TODO: Send notification (implement later)
        # send_disposisi_notification(disposisi, new_status)
        
        success_message = f"Status berhasil diupdate dari {old_status} ke {new_status}"
        current_app.logger.info(f"🎉 Helper: {success_message}")
        return True, success_message, disposisi
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"💥 Helper: CRITICAL ERROR in update_disposisi_status: {str(e)}")
        current_app.logger.error(f"💥 Helper: Error type: {type(e).__name__}")
        import traceback
        current_app.logger.error(f"📚 Helper: Full traceback: {traceback.format_exc()}")
        return False, f"Terjadi kesalahan: {str(e)}", None


def sync_surat_status(disposisi, new_disposisi_status):
    """
    Sync status surat dengan status disposisi
    
    Args:
        disposisi: Object Disposisi
        new_disposisi_status: Status baru disposisi
    """
    try:
        # Get surat object
        if disposisi.surat_tipe == 'masuk':
            surat = SuratMasuk.query.get(disposisi.surat_masuk_id)
            if not surat:
                current_app.logger.warning(f"Surat masuk {disposisi.surat_masuk_id} not found for disposisi {disposisi.id}")
                return
            
            # Backup status surat sebelum disposisi (only once)
            if not disposisi.status_surat_sebelum:
                disposisi.status_surat_sebelum = surat.status_suratMasuk
            
            # Update status surat based on disposisi status
            if new_disposisi_status == 'dikirim':
                surat.status_suratMasuk = 'didisposisikan'
            elif new_disposisi_status == 'diproses':
                surat.status_suratMasuk = 'dalam_proses'
            elif new_disposisi_status == 'selesai':
                surat.status_suratMasuk = 'selesai_disposisi'
            elif new_disposisi_status == 'ditolak':
                # Restore previous status
                surat.status_suratMasuk = disposisi.status_surat_sebelum or 'approved'
            # For 'draft' status, don't change surat status
        
        elif disposisi.surat_tipe == 'keluar':
            surat = SuratKeluar.query.get(disposisi.surat_keluar_id)
            if not surat:
                current_app.logger.warning(f"Surat keluar {disposisi.surat_keluar_id} not found for disposisi {disposisi.id}")
                return
            
            # Backup status surat sebelum disposisi (only once)
            if not disposisi.status_surat_sebelum:
                disposisi.status_surat_sebelum = surat.status_suratKeluar
            
            # Update status surat based on disposisi status
            if new_disposisi_status == 'dikirim':
                surat.status_suratKeluar = 'didisposisikan'
            elif new_disposisi_status == 'diproses':
                surat.status_suratKeluar = 'dalam_proses'
            elif new_disposisi_status == 'selesai':
                surat.status_suratKeluar = 'selesai_disposisi'
            elif new_disposisi_status == 'ditolak':
                # Restore previous status
                surat.status_suratKeluar = disposisi.status_surat_sebelum or 'approved'
            # For 'draft' status, don't change surat status
        
        else:
            current_app.logger.warning(f"Unknown surat_tipe: {disposisi.surat_tipe} for disposisi {disposisi.id}")
            return
        
        db.session.flush()
        
    except Exception as e:
        current_app.logger.error(f"Error syncing surat status: {str(e)}")
        # Don't raise exception, just log it so main process continues


def add_disposisi_history(disposisi_id, status_lama, status_baru, catatan=None, user_id=None):
    """
    Add entry to disposisi history
    
    Args:
        disposisi_id: ID disposisi
        status_lama: Status lama
        status_baru: Status baru
        catatan: Catatan perubahan
        user_id: ID user yang melakukan perubahan
    """
    try:
        # Ensure we have a valid user_id
        if not user_id and current_user.is_authenticated:
            user_id = current_user.id
        elif not user_id:
            # Skip history if no user (shouldn't happen in normal flow)
            current_app.logger.warning(f"Skipping history for disposisi {disposisi_id} - no user_id")
            return
        
        history = DisposisiHistory(
            disposisi_id=disposisi_id,
            status_lama=status_lama,
            status_baru=status_baru,
            catatan=catatan,
            user_id=user_id,
            timestamp=datetime.now()
        )
        db.session.add(history)
        db.session.flush()
        
    except Exception as e:
        current_app.logger.error(f"Error adding disposisi history: {str(e)}")
        # Don't raise exception, just log it so main process continues


def get_disposisi_timeline(disposisi_id):
    """
    Get timeline of disposisi status changes
    
    Args:
        disposisi_id: ID disposisi
    
    Returns:
        list: List of history entries with user info
    """
    try:
        history = DisposisiHistory.query.filter_by(
            disposisi_id=disposisi_id
        ).order_by(DisposisiHistory.timestamp.asc()).all()
        
        timeline = []
        for entry in history:
            timeline.append({
                'id': entry.id,
                'status_lama': entry.status_lama,
                'status_baru': entry.status_baru,
                'catatan': entry.catatan,
                'user_email': entry.user.email if entry.user else 'System',
                'user_name': entry.user.email.split('@')[0] if entry.user else 'System',
                'timestamp': entry.timestamp,
                'timestamp_str': entry.timestamp.strftime('%d/%m/%Y %H:%M') if entry.timestamp else ''
            })
        
        return timeline
        
    except Exception as e:
        current_app.logger.error(f"Error getting disposisi timeline: {str(e)}")
        return []


def get_disposisi_stats(user_id=None, role=None):
    """
    Get disposisi statistics
    
    Args:
        user_id: Filter by user (optional)
        role: User role for filtering (optional)
    
    Returns:
        dict: Statistics data
    """
    try:
        query = Disposisi.query
        
        # Filter based on role
        if role not in ['admin', 'pimpinan'] and user_id:
            # Regular user: only see disposisi they're involved in
            query = query.filter(
                or_(
                    Disposisi.dari_user_id == user_id,
                    Disposisi.kepada_user_id == user_id
                )
            )
        
        total = query.count()
        draft = query.filter_by(status='draft').count()
        dikirim = query.filter_by(status='dikirim').count()
        diproses = query.filter_by(status='diproses').count()
        selesai = query.filter_by(status='selesai').count()
        ditolak = query.filter_by(status='ditolak').count()
        
        # Count overdue
        from datetime import date
        overdue = query.filter(
            Disposisi.batas_waktu < date.today(),
            Disposisi.status.in_(['dikirim', 'diproses'])
        ).count()
        
        # Count near deadline (within 2 days)
        from datetime import timedelta
        near_deadline = query.filter(
            Disposisi.batas_waktu <= date.today() + timedelta(days=2),
            Disposisi.batas_waktu >= date.today(),
            Disposisi.status.in_(['dikirim', 'diproses'])
        ).count()
        
        return {
            'total': total,
            'draft': draft,
            'dikirim': dikirim,
            'diproses': diproses,
            'selesai': selesai,
            'ditolak': ditolak,
            'overdue': overdue,
            'near_deadline': near_deadline,
            'active': dikirim + diproses  # Active disposisi
        }
        
    except Exception as e:
        current_app.logger.error(f"Error getting disposisi stats: {str(e)}")
        return {
            'total': 0,
            'draft': 0,
            'dikirim': 0,
            'diproses': 0,
            'selesai': 0,
            'ditolak': 0,
            'overdue': 0,
            'near_deadline': 0,
            'active': 0
        }


def send_disposisi_notification(disposisi, status):
    """
    Send notification for disposisi status change
    TODO: Implement email/in-app notification
    
    Args:
        disposisi: Disposisi object
        status: New status
    """
    # Placeholder for notification system
    # Will be implemented in Phase 2
    pass


def get_status_badge_class(status):
    """
    Get CSS class for status badge
    
    Args:
        status: Status string
    
    Returns:
        str: CSS class
    """
    badges = {
        'draft': 'bg-gray-100 text-gray-800',
        'dikirim': 'bg-blue-100 text-blue-800',
        'diproses': 'bg-yellow-100 text-yellow-800',
        'selesai': 'bg-green-100 text-green-800',
        'ditolak': 'bg-red-100 text-red-800'
    }
    return badges.get(status, 'bg-gray-100 text-gray-800')


def get_status_icon(status):
    """
    Get icon for status
    
    Args:
        status: Status string
    
    Returns:
        str: Icon emoji/class
    """
    icons = {
        'draft': '📝',
        'dikirim': '📤',
        'diproses': '⏳',
        'selesai': '✅',
        'ditolak': '❌'
    }
    return icons.get(status, '📋')


def get_prioritas_badge_class(prioritas):
    """
    Get CSS class for prioritas badge
    
    Args:
        prioritas: Prioritas string
    
    Returns:
        str: CSS class
    """
    badges = {
        'rendah': 'bg-green-100 text-green-800',
        'normal': 'bg-blue-100 text-blue-800',
        'tinggi': 'bg-orange-100 text-orange-800',
        'urgent': 'bg-red-100 text-red-800'
    }
    return badges.get(prioritas, 'bg-gray-100 text-gray-800')


def get_prioritas_icon(prioritas):
    """
    Get icon for prioritas
    
    Args:
        prioritas: Prioritas string
    
    Returns:
        str: Icon emoji
    """
    icons = {
        'rendah': '🟢',
        'normal': '🔵',
        'tinggi': '🟡',
        'urgent': '🔴'
    }
    return icons.get(prioritas, '⚪')

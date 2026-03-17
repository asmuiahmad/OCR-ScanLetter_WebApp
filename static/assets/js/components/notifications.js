/**
 * Notification Bell — Persetujuan Surat
 */

function sanitizeText(text) {
  if (text == null) return '';
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

/* ── Counter badges ─────────────────────────────────────── */
function updateNotificationCounters(pendingMasuk, pendingKeluar) {
  const mv = document.getElementById('notifCountMasukValue');
  const kv = document.getElementById('notifCountKeluarValue');
  if (mv) mv.textContent = pendingMasuk;
  if (kv) kv.textContent = pendingKeluar;

  const total = pendingMasuk + pendingKeluar;
  const bell  = document.querySelector('.notification-bell-btn');
  if (!bell) return;

  let badge = bell.querySelector('.notif-badge');
  if (total > 0) {
    bell.classList.add('has-notifications');
    if (!badge) {
      badge = document.createElement('span');
      badge.className = 'notif-badge absolute bg-red-500 text-white text-xs rounded-full min-w-[20px] h-5 flex items-center justify-center font-bold px-1';
      badge.style.cssText = 'top:-4px;right:-4px;z-index:10;';
      bell.appendChild(badge);
    }
    badge.textContent = total;
  } else {
    bell.classList.remove('has-notifications');
    if (badge) badge.remove();
  }
}

/* ── Render one notification item ───────────────────────── */
function buildNotifItem(surat) {
  const isMasuk     = surat.type === 'masuk';
  const typeLabel   = isMasuk ? 'Surat Masuk' : 'Surat Keluar';
  const typeIcon    = isMasuk ? 'fa-inbox' : 'fa-paper-plane';
  const badgeCls    = isMasuk
    ? 'bg-blue-100 text-blue-700 border border-blue-200'
    : 'bg-purple-100 text-purple-700 border border-purple-200';

  const nomor       = sanitizeText(surat.nomor       || '-');
  const pengirim    = sanitizeText(surat.pengirim     || '-');
  const penerima    = sanitizeText(surat.penerima     || '-');
  const tanggal     = sanitizeText(surat.tanggal_display    || '-');
  const dimasukan   = sanitizeText(surat.created_at_display || '');

  const li = document.createElement('li');
  li.innerHTML = `
    <div class="px-4 py-3 hover:bg-gray-50 transition-colors group">
      <!-- Label + waktu dimasukan -->
      <div class="flex items-center justify-between mb-1.5">
        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${badgeCls}">
          <i class="fas ${typeIcon}"></i> ${typeLabel}
        </span>
        ${dimasukan ? `<span class="text-xs text-gray-400 flex items-center gap-1"><i class="far fa-clock"></i>${dimasukan}</span>` : ''}
      </div>
      <!-- Nomor surat -->
      <div class="text-xs font-bold text-gray-700 flex items-center gap-1 mb-0.5">
        <i class="fas fa-hashtag text-gray-400"></i>${nomor}
      </div>
      <!-- Pengirim → Penerima -->
      <div class="text-xs text-gray-600 flex items-center gap-1 mb-0.5 truncate">
        <i class="fas fa-user text-gray-400 flex-shrink-0"></i>
        <span class="truncate">${pengirim}</span>
        <i class="fas fa-arrow-right text-gray-300 flex-shrink-0 text-[10px]"></i>
        <span class="truncate">${penerima}</span>
      </div>
      <!-- Tanggal surat -->
      <div class="text-xs text-gray-400 flex items-center gap-1 mb-2">
        <i class="far fa-calendar-alt"></i>${tanggal}
      </div>
      <!-- Tombol aksi -->
      <div class="flex gap-2">
        <button onclick="approveSurat(${surat.id}, this, '${surat.type}')"
                class="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-semibold text-white border-none cursor-pointer transition"
                style="background:linear-gradient(135deg,#059669,#10b981);"
                onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'"
                title="Setujui Surat">
          <i class="fas fa-check"></i> Setujui
        </button>
        <button onclick="rejectSurat(${surat.id}, this, '${surat.type}')"
                class="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-semibold text-white border-none cursor-pointer transition"
                style="background:linear-gradient(135deg,#dc2626,#ef4444);"
                onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'"
                title="Tolak Surat">
          <i class="fas fa-times"></i> Tolak
        </button>
      </div>
    </div>
  `;
  return li;
}

/* ── Update dropdown list ───────────────────────────────── */
function updateNotificationDropdownContent(suratList) {
  const dropdown = document.querySelector('.notification-dropdown');
  if (!dropdown) return;

  const listEl   = dropdown.querySelector('.notif-list');
  const emptyEl  = dropdown.querySelector('.notif-empty');
  const loadEl   = dropdown.querySelector('.notif-loading');

  if (loadEl) loadEl.style.display = 'none';

  if (!listEl) return;
  listEl.innerHTML = '';

  if (suratList && suratList.length > 0) {
    suratList.forEach(s => listEl.appendChild(buildNotifItem(s)));
    if (emptyEl) emptyEl.style.display = 'none';
  } else {
    if (emptyEl) emptyEl.style.display = 'block';
  }
}

/* ── Fetch & refresh ────────────────────────────────────── */
function refreshNotificationDropdown() {
  const dropdown = document.querySelector('.notification-dropdown');
  const loadEl   = dropdown?.querySelector('.notif-loading');
  if (loadEl) loadEl.style.display = 'block';

  fetch('/api/notifications/recent')
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(data => {
      if (data.success) {
        updateNotificationDropdownContent(data.surat_list || []);
        updateNotificationCounters(data.pending_masuk || 0, data.pending_keluar || 0);
      } else {
        updateNotificationDropdownContent([]);
      }
    })
    .catch(() => updateNotificationDropdownContent([]));
}

function updateNotificationCount() {
  fetch('/api/notifications/count')
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(data => {
      if (data.success) {
        updateNotificationCounters(data.pending_masuk || 0, data.pending_keluar || 0);
      }
    })
    .catch(() => {});
}

/* ── Approve / Reject ───────────────────────────────────── */
function approveSurat(suratId, btn, suratType) {
  // Stop the click from bubbling to the document (which would close dropdown)
  if (window.event) window.event.stopPropagation();

  btn.disabled = true;
  const originalHtml = btn.innerHTML;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

  const endpoint = suratType === 'masuk'
    ? `/approval/surat-masuk/${suratId}/approve-api`
    : `/approval/surat-keluar/${suratId}/approve-api`;

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

  fetch(endpoint, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'X-CSRFToken': csrfToken,
      'X-CSRF-Token': csrfToken,
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({})
  })
  .then(r => {
    if (!r.ok) return r.text().then(t => { throw new Error(`HTTP ${r.status}: ${t}`); });
    return r.json();
  })
  .then(data => {
    if (data.success) {
      window.toast?.success('Surat berhasil disetujui');
      const li = btn.closest('li');
      if (li) {
        li.style.transition = 'opacity 0.3s,transform 0.3s';
        li.style.opacity = '0';
        li.style.transform = 'translateX(40px)';
        setTimeout(() => { li.remove(); updateNotificationCount(); }, 320);
      }
    } else {
      window.toast?.error(data.message || data.error || 'Gagal menyetujui surat');
      btn.disabled = false;
      btn.innerHTML = originalHtml;
    }
  })
  .catch(err => {
    console.error('approveSurat error:', err);
    window.toast?.error('Terjadi kesalahan: ' + err.message);
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  });
}

function rejectSurat(suratId, btn, suratType) {
  if (window.event) window.event.stopPropagation();

  // Ambil nomor surat dari item notifikasi untuk subtitle modal
  const li = btn.closest('li');
  const nomor = li?.querySelector('.fa-hashtag')?.parentElement?.textContent?.trim() || '';

  openGlobalRejectModal(suratId, suratType, nomor, btn);
}

/* ── Global Reject Modal ────────────────────────────────── */
let _rejectContext = null;

function openGlobalRejectModal(suratId, suratType, nomor, btn) {
  _rejectContext = { suratId, suratType, btn, originalHtml: btn.innerHTML };

  const modal = document.getElementById('globalRejectModal');
  const box   = document.getElementById('globalRejectBox');
  const sub   = document.getElementById('globalRejectSubtitle');
  const ta    = document.getElementById('globalRejectReason');
  const ctr   = document.getElementById('globalRejectCounter');

  sub.textContent  = nomor ? 'Nomor: ' + nomor : '';
  ta.value         = '';
  ctr.textContent  = '0 / 500';

  modal.style.opacity    = '1';
  modal.style.visibility = 'visible';
  box.style.transform    = 'translateY(0) scale(1)';
  document.body.style.overflow = 'hidden';

  setTimeout(() => ta.focus(), 100);
}

function closeGlobalRejectModal() {
  const modal = document.getElementById('globalRejectModal');
  const box   = document.getElementById('globalRejectBox');

  modal.style.opacity    = '0';
  modal.style.visibility = 'hidden';
  box.style.transform    = 'translateY(20px) scale(0.97)';
  document.body.style.overflow = '';

  // Kembalikan tombol jika dibatalkan
  if (_rejectContext?.btn) {
    _rejectContext.btn.disabled = false;
    _rejectContext.btn.innerHTML = _rejectContext.originalHtml;
  }
  _rejectContext = null;
}

function submitGlobalReject() {
  if (!_rejectContext) return;

  const reason = document.getElementById('globalRejectReason').value.trim();
  if (!reason) {
    document.getElementById('globalRejectReason').focus();
    document.getElementById('globalRejectReason').style.borderColor = '#ef4444';
    document.getElementById('globalRejectReason').style.boxShadow = '0 0 0 3px rgba(239,68,68,0.25)';
    return;
  }

  const { suratId, suratType, btn } = _rejectContext;
  const submitBtn = document.getElementById('globalRejectSubmitBtn');

  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Memproses...';

  const endpoint = suratType === 'masuk'
    ? `/approval/surat-masuk/${suratId}/reject-api`
    : `/approval/surat-keluar/${suratId}/reject-api`;

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

  fetch(endpoint, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'X-CSRFToken': csrfToken,
      'X-CSRF-Token': csrfToken,
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({ rejection_reason: reason })
  })
  .then(r => {
    if (!r.ok) return r.text().then(t => { throw new Error(`HTTP ${r.status}: ${t}`); });
    return r.json();
  })
  .then(data => {
    if (data.success) {
      const li = btn.closest('li');
      // Tutup modal dulu
      const modal = document.getElementById('globalRejectModal');
      const box   = document.getElementById('globalRejectBox');
      modal.style.opacity    = '0';
      modal.style.visibility = 'hidden';
      box.style.transform    = 'translateY(20px) scale(0.97)';
      document.body.style.overflow = '';
      _rejectContext = null;

      window.toast?.success('Surat berhasil ditolak');
      if (li) {
        li.style.transition = 'opacity 0.3s,transform 0.3s';
        li.style.opacity = '0';
        li.style.transform = 'translateX(-40px)';
        setTimeout(() => { li.remove(); updateNotificationCount(); }, 320);
      }
    } else {
      window.toast?.error(data.message || data.error || 'Gagal menolak surat');
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="fas fa-times" style="margin-right:0.25rem;"></i> Tolak Surat';
      btn.disabled = false;
      btn.innerHTML = _rejectContext?.originalHtml || '<i class="fas fa-times"></i> Tolak';
    }
  })
  .catch(err => {
    console.error('rejectSurat error:', err);
    window.toast?.error('Terjadi kesalahan: ' + err.message);
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fas fa-times" style="margin-right:0.25rem;"></i> Tolak Surat';
    if (_rejectContext?.btn) {
      _rejectContext.btn.disabled = false;
      _rejectContext.btn.innerHTML = _rejectContext.originalHtml;
    }
  });
}

/* ── Init ───────────────────────────────────────────────── */
function initializeNotifications() {
  updateNotificationCount();

  // Tutup global reject modal saat klik backdrop atau tekan Escape
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      const modal = document.getElementById('globalRejectModal');
      if (modal && modal.style.visibility === 'visible') closeGlobalRejectModal();
    }
  });
  document.getElementById('globalRejectModal')?.addEventListener('click', function(e) {
    if (e.target === this) closeGlobalRejectModal();
  });

  // Use event delegation on document — works even if bell is re-rendered
  document.addEventListener('click', function(e) {
    const bell     = document.querySelector('.notification-bell-btn');
    const dropdown = document.querySelector('.notification-dropdown');
    if (!bell || !dropdown) return;

    // Bell clicked
    if (bell.contains(e.target) || e.target === bell) {
      e.preventDefault();
      e.stopPropagation();
      const isOpen = dropdown.style.display === 'flex';
      if (isOpen) {
        dropdown.style.display = 'none';
      } else {
        dropdown.style.display = 'flex';
        refreshNotificationDropdown();
      }
      return;
    }

    // Click outside — close dropdown
    if (!dropdown.contains(e.target)) {
      dropdown.style.display = 'none';
    }
  });

  // Refresh count every 30s; refresh dropdown content every 60s if open
  setInterval(updateNotificationCount, 30000);
  setInterval(() => {
    const dropdown = document.querySelector('.notification-dropdown');
    if (dropdown && dropdown.style.display === 'flex') refreshNotificationDropdown();
  }, 60000);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeNotifications);
} else {
  initializeNotifications();
}

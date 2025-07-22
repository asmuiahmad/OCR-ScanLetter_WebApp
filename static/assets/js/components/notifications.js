/**
 * Notification System
 * Handles notification bell and notification updates
 */

function updateNotificationCount() {
  const notificationBell = document.querySelector('.notification-bell-btn');
  if (!notificationBell) return;

  fetch('/api/notifications/count')
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        const badge = notificationBell.querySelector('.absolute');
        if (data.pending_count > 0) {
          if (badge) {
            badge.textContent = data.pending_count;
          } else {
            const newBadge = document.createElement('span');
            newBadge.className = 'absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center';
            newBadge.textContent = data.pending_count;
            notificationBell.appendChild(newBadge);
          }
        } else {
          if (badge) {
            badge.remove();
          }
        }
      }
    })
    .catch(error => {
      console.error('Error fetching notification count:', error);
    });
}

function initializeNotifications() {
  const notificationBell = document.querySelector('.notification-bell-btn');
  if (notificationBell) {
    updateNotificationCount();
    
    setInterval(updateNotificationCount, 30000);
  }
}

function approveSurat(suratId, buttonElement) {
  event.stopPropagation();
  fetch(`/surat-keluar/approve/${suratId}`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content,
      'Content-Type': 'application/json'
    }
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      window.toast.success('Surat telah disetujui!');
      const listItem = buttonElement.closest('li');
      listItem.classList.add('fade-out-item');
      setTimeout(() => {
        listItem.remove();
        updateNotificationCount();
      }, 500);
    } else {
      window.toast.error(data.message || 'Gagal menyetujui surat!');
    }
  })
  .catch(() => window.toast.error('Gagal menyetujui surat!'));
}

function rejectSurat(suratId, buttonElement) {
  event.stopPropagation();
  fetch(`/surat-keluar/reject/${suratId}`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content,
      'Content-Type': 'application/json'
    }
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      window.toast.success('Surat telah ditolak!');
      const listItem = buttonElement.closest('li');
      listItem.classList.add('fade-out-item');
      setTimeout(() => {
        listItem.remove();
        updateNotificationCount();
      }, 500);
    } else {
      window.toast.error(data.message || 'Gagal menolak surat!');
    }
  })
  .catch(() => window.toast.error('Gagal menolak surat!'));
}
/**
 * Notification System
 * Handles notification bell and notification updates
 */

function sanitizeText(text) {
  if (text === null || text === undefined) {
    return '';
  }
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function updateNotificationCounters(pendingMasuk, pendingKeluar) {
  const masukValue = document.getElementById('notifCountMasukValue');
  const keluarValue = document.getElementById('notifCountKeluarValue');

  if (masukValue) {
    masukValue.textContent = pendingMasuk;
  }

  if (keluarValue) {
    keluarValue.textContent = pendingKeluar;
  }
}

function updateNotificationCount() {
  const notificationBell = document.querySelector('.notification-bell-btn');
  if (!notificationBell) {
    console.warn('Notification bell button not found');
    return;
  }

  console.log('Updating notification count...');
  
  fetch('/api/notifications/count')
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Notification count data:', data);
      if (data.success) {
        updateNotificationCounters(data.pending_masuk || 0, data.pending_keluar || 0);

        const badge = notificationBell.querySelector('.absolute');
        const pendingCount = data.pending_count || 0;
        
        if (pendingCount > 0) {
          // Add has-notifications class for bell animation
          notificationBell.classList.add('has-notifications');
          
          if (badge) {
            badge.textContent = pendingCount;
            // Ensure badge is visible
            badge.style.display = 'flex';
            badge.style.visibility = 'visible';
          } else {
            const newBadge = document.createElement('span');
            newBadge.className = 'absolute bg-red-500 text-white text-xs rounded-full min-w-[20px] h-5 flex items-center justify-center font-bold px-1';
            newBadge.style.top = '-4px';
            newBadge.style.right = '-4px';
            newBadge.style.zIndex = '10';
            newBadge.style.display = 'flex';
            newBadge.style.visibility = 'visible';
            newBadge.textContent = pendingCount;
            notificationBell.appendChild(newBadge);
            console.log('Created new notification badge:', pendingCount);
          }
        } else {
          // Remove has-notifications class
          notificationBell.classList.remove('has-notifications');
          
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
  const notificationDropdown = document.querySelector('.notification-dropdown');
  
  console.log('Initializing notifications...', { notificationBell, notificationDropdown });
  
  if (notificationBell && notificationDropdown) {
    // Initial count update
    updateNotificationCount();
    
    // Toggle dropdown on bell click and load recent notifications
    notificationBell.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      console.log('Bell clicked, dropdown hidden:', notificationDropdown.classList.contains('hidden'));
      
      const isHidden = notificationDropdown.classList.contains('hidden');
      
      if (isHidden) {
        // Load recent notifications when opening dropdown
        console.log('Loading notifications...');
        refreshNotificationDropdown();
        notificationDropdown.classList.remove('hidden');
      } else {
        notificationDropdown.classList.add('hidden');
      }
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
      if (notificationBell && notificationDropdown && 
          !notificationBell.contains(e.target) && 
          !notificationDropdown.contains(e.target)) {
        notificationDropdown.classList.add('hidden');
      }
    });
    
    // Update notification count every 30 seconds
    setInterval(updateNotificationCount, 30000);
    
    // Refresh dropdown content every 60 seconds if it's open
    setInterval(() => {
      if (notificationDropdown && !notificationDropdown.classList.contains('hidden')) {
        refreshNotificationDropdown();
      }
    }, 60000);
  } else {
    console.warn('Notification bell or dropdown not found:', { notificationBell, notificationDropdown });
  }
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() {
    initializeNotifications();
  });
} else {
  // DOM already loaded
  initializeNotifications();
}

function approveSurat(suratId, buttonElement, suratType = 'masuk') {
  if (event) event.stopPropagation();
  
  // Disable button to prevent double clicks
  buttonElement.disabled = true;
  buttonElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
  
  const endpoint = suratType === 'masuk' 
    ? `/surat-masuk/approve-surat/${suratId}`
    : `/surat-keluar/approve-surat/${suratId}`;
  
  fetch(endpoint, {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || '',
      'Content-Type': 'application/json'
    }
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      window.toast?.success('✅ Surat berhasil disetujui!');
      const listItem = buttonElement.closest('li');
      if (listItem) {
        listItem.style.transition = 'all 0.5s ease-out';
        listItem.style.opacity = '0';
        listItem.style.transform = 'translateX(100%)';
        setTimeout(() => {
          listItem.remove();
          updateNotificationCount();
          refreshNotificationDropdown();
        }, 500);
      }
    } else {
      window.toast?.error(data.message || '❌ Gagal menyetujui surat!');
      // Re-enable button on error
      buttonElement.disabled = false;
      buttonElement.innerHTML = '<i class="fas fa-check"></i>';
    }
  })
  .catch(error => {
    console.error('Error approving surat:', error);
    window.toast?.error('❌ Terjadi kesalahan saat menyetujui surat!');
    // Re-enable button on error
    buttonElement.disabled = false;
    buttonElement.innerHTML = '<i class="fas fa-check"></i>';
  });
}

function rejectSurat(suratId, buttonElement, suratType = 'masuk') {
  if (event) event.stopPropagation();
  
  // Konfirmasi sebelum menolak
  if (!confirm('Apakah Anda yakin ingin menolak surat ini?')) {
    return;
  }
  
  // Disable button to prevent double clicks
  buttonElement.disabled = true;
  buttonElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
  
  const endpoint = suratType === 'masuk' 
    ? `/surat-masuk/reject-surat/${suratId}`
    : `/surat-keluar/reject-surat/${suratId}`;
  
  fetch(endpoint, {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || '',
      'Content-Type': 'application/json'
    }
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      window.toast?.success('🚫 Surat berhasil ditolak!');
      const listItem = buttonElement.closest('li');
      if (listItem) {
        listItem.style.transition = 'all 0.5s ease-out';
        listItem.style.opacity = '0';
        listItem.style.transform = 'translateX(-100%)';
        setTimeout(() => {
          listItem.remove();
          updateNotificationCount();
          refreshNotificationDropdown();
        }, 500);
      }
    } else {
      window.toast?.error(data.message || '❌ Gagal menolak surat!');
      // Re-enable button on error
      buttonElement.disabled = false;
      buttonElement.innerHTML = '<i class="fas fa-times"></i>';
    }
  })
  .catch(error => {
    console.error('Error rejecting surat:', error);
    window.toast?.error('❌ Terjadi kesalahan saat menolak surat!');
    // Re-enable button on error
    buttonElement.disabled = false;
    buttonElement.innerHTML = '<i class="fas fa-times"></i>';
  });
}

function refreshNotificationDropdown() {
  console.log('Refreshing notification dropdown...');
  
  fetch('/api/notifications/recent')
    .then(response => {
      console.log('Notification API response status:', response.status);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Notification API data:', data);
      if (data.success) {
        updateNotificationDropdownContent(data.surat_list || []);
        updateNotificationCounters(data.pending_masuk || 0, data.pending_keluar || 0);
        updateNotificationCount();
      } else {
        console.error('API returned success=false:', data.message);
        updateNotificationDropdownContent([]);
      }
    })
    .catch(error => {
      console.error('Error refreshing notification dropdown:', error);
      // Show error message in dropdown
      const dropdown = document.querySelector('.notification-dropdown');
      if (dropdown) {
        const existingContent = dropdown.querySelector('.notification-content');
        if (existingContent) {
          existingContent.innerHTML = `
            <div class="py-8 px-5 text-center text-red-400">
              <div class="flex flex-col items-center gap-2">
                <i class="fas fa-exclamation-triangle text-2xl"></i>
                <div class="text-sm font-medium">Error memuat notifikasi</div>
                <div class="text-xs">Silakan refresh halaman</div>
              </div>
            </div>
          `;
        }
      }
    });
}

function updateNotificationDropdownContent(suratList) {
  const dropdown = document.querySelector('.notification-dropdown');
  if (!dropdown) {
    console.warn('Notification dropdown not found');
    return;
  }
  
  console.log('Updating dropdown content with', suratList?.length || 0, 'items');
  
  // Find the content area (after header)
  const header = dropdown.querySelector('.p-4.border-b');
  const existingContent = dropdown.querySelector('.notification-content');
  
  // Remove existing content
  if (existingContent) {
    existingContent.remove();
  }
  
  // Create new content container
  const contentContainer = document.createElement('div');
  contentContainer.className = 'notification-content';
  
  if (suratList && suratList.length > 0) {
    console.log('Rendering', suratList.length, 'notifications');
    const listElement = document.createElement('ul');
    listElement.className = 'divide-y divide-gray-100';

    // Add new items
    suratList.forEach(surat => {
      const suratType = surat.type || 'masuk';
      const suratId = surat.id;
      const isMasuk = suratType === 'masuk';
      const typeLabel = isMasuk ? 'Surat Masuk' : 'Surat Keluar';
      const typeIcon = isMasuk ? 'fa-inbox' : 'fa-paper-plane';
      const typeBadgeClass = isMasuk ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800';

      const pengirim = sanitizeText(surat.pengirim || 'Pengirim tidak diketahui');
      const tanggalDisplay = sanitizeText(surat.tanggal_display || 'Tanggal tidak diketahui');
      const nomor = sanitizeText(surat.nomor || 'No. surat tidak diketahui');
      const penerima = sanitizeText(surat.penerima || 'Penerima tidak diketahui');
      const createdAtDisplay = sanitizeText(surat.created_at_display || '');
      const ringkasan = sanitizeText(surat.ringkasan || '');

      const listItem = document.createElement('li');
      listItem.innerHTML = `
        <div class="flex flex-col gap-2 py-4 px-5 hover:bg-blue-50 transition group border-b last:border-b-0 border-gray-100">
          <div class="flex flex-row items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${typeBadgeClass}">
                  <i class="fas ${typeIcon} mr-1"></i>${typeLabel}
                </span>
              </div>
              <div class="font-semibold text-gray-800 group-hover:text-blue-700 truncate">
                ${pengirim}
              </div>
              <div class="text-xs text-gray-500 mt-1 flex items-center gap-2">
                <i class="far fa-calendar-alt"></i>
                ${tanggalDisplay}
              </div>
              <div class="text-xs text-gray-600 truncate mt-1 flex items-center gap-2">
                <i class="fas fa-hashtag"></i>${nomor}
              </div>
              <div class="text-xs text-gray-500 mt-1 flex items-center gap-2">
                <i class="fas fa-user"></i>${penerima}
              </div>
              ${createdAtDisplay ? `
              <div class="text-xs text-gray-400 mt-1 flex items-center gap-2">
                <i class="far fa-clock"></i>${createdAtDisplay}
              </div>` : ''}
              ${ringkasan ? `
              <div class="text-xs text-gray-500 mt-2 leading-snug">
                ${ringkasan}
              </div>` : ''}
            </div>
            <div class="flex flex-col items-end gap-2 ml-2">
              <span class="inline-block text-xs text-white bg-orange-500 px-2 py-1 rounded-full text-center whitespace-nowrap">
                Menunggu Persetujuan
              </span>
              <div class="flex gap-1">
                <button onclick="approveSurat(${suratId}, this, '${suratType}')" 
                        class="approve-btn flex items-center justify-center w-8 h-8 rounded-full bg-green-100 hover:bg-green-200 text-green-700 border border-green-200 transition-all duration-200 hover:scale-105" 
                        title="Setujui Surat">
                  <i class="fas fa-check text-sm"></i>
                </button>
                <button onclick="rejectSurat(${suratId}, this, '${suratType}')" 
                        class="reject-btn flex items-center justify-center w-8 h-8 rounded-full bg-red-100 hover:bg-red-200 text-red-700 border border-red-200 transition-all duration-200 hover:scale-105" 
                        title="Tolak Surat">
                  <i class="fas fa-times text-sm"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
      listElement.appendChild(listItem);
    });

    contentContainer.appendChild(listElement);
  } else {
    const noDataElement = document.createElement('div');
    noDataElement.className = 'py-8 px-5 text-center text-gray-400';
    noDataElement.innerHTML = `
      <div class="flex flex-col items-center gap-2">
        <i class="fas fa-check-circle text-3xl text-green-400"></i>
        <div class="text-sm font-medium">Semua surat sudah diproses</div>
        <div class="text-xs">Tidak ada surat yang menunggu persetujuan</div>
      </div>
    `;
    contentContainer.appendChild(noDataElement);
  }
  
  // Insert content after header
  if (header && header.nextSibling) {
    dropdown.insertBefore(contentContainer, header.nextSibling);
  } else {
    dropdown.appendChild(contentContainer);
  }
}
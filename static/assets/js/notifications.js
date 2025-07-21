/* ===== NOTIFICATION SYSTEM ===== */

// Function to update notification count
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

// Initialize notification system
function initializeNotifications() {
  const notificationBell = document.querySelector('.notification-bell-btn');
  if (notificationBell) {
    // Update count on page load
    updateNotificationCount();
    
    // Auto-refresh every 30 seconds
    setInterval(updateNotificationCount, 30000);
  }
}

// Initialize notifications when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  initializeNotifications();
});

// Export functions for global use
window.updateNotificationCount = updateNotificationCount;
window.initializeNotifications = initializeNotifications;
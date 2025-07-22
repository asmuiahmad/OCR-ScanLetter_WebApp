/**
 * Toast Notification System
 * Provides a simple way to show toast notifications
 */
class ToastNotification {
  constructor() {
    this.container = document.getElementById('toast-container');
  }
  
  show(message, type = 'success', title = null, duration = 5000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = this.getIcon(type);
    const closeIcon = '×';
    
    toast.innerHTML = `
      <div class="toast-content">
        ${title ? `<div class="toast-title">${title}</div>` : ''}
        <div class="toast-message">${message}</div>
      </div>
      <button class="toast-close" onclick="this.parentElement.remove()">${closeIcon}</button>
    `;
    
    this.container.appendChild(toast);
    
    if (duration > 0) {
      setTimeout(() => {
        if (toast.parentElement) {
          toast.classList.add('fade-out');
          setTimeout(() => {
            if (toast.parentElement) {
              toast.remove();
            }
          }, 300);
        }
      }, duration);
    }
    
    return toast;
  }
  
  getIcon(type) {
    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ'
    };
    return icons[type] || icons.info;
  }
  
  success(message, title = null) {
    return this.show(message, 'success', title);
  }
  
  error(message, title = null) {
    return this.show(message, 'error', title);
  }
  
  warning(message, title = null) {
    return this.show(message, 'warning', title);
  }
  
  info(message, title = null) {
    return this.show(message, 'info', title);
  }
}

// Initialize toast notification system
window.toast = new ToastNotification();

document.addEventListener('DOMContentLoaded', function() {
  const flashMessages = document.querySelectorAll('.alert');
  flashMessages.forEach(alert => {
    const message = alert.textContent.trim();
    const category = alert.className.includes('alert-success') ? 'success' :
                    alert.className.includes('alert-danger') ? 'error' :
                    alert.className.includes('alert-warning') ? 'warning' : 'info';
    
    window.toast.show(message, category);
    
    alert.remove();
  });

  initializeNotifications();
});
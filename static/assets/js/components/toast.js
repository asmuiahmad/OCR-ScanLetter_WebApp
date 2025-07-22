/* ===== TOAST NOTIFICATION SYSTEM ===== */

class ToastNotification {
  constructor() {
    this.container = document.getElementById('toast-container');
    if (!this.container) {
      // Create container if it doesn't exist
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.className = 'fixed bottom-4 right-4 z-50 space-y-2';
      document.body.appendChild(this.container);
    }
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
    
    // Auto remove after duration
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

// Initialize global toast instance
window.toast = new ToastNotification();

// Convert flash messages to toasts
document.addEventListener('DOMContentLoaded', function() {
  const flashMessages = document.querySelectorAll('.alert');
  flashMessages.forEach(alert => {
    const message = alert.textContent.trim();
    const category = alert.className.includes('alert-success') ? 'success' :
                    alert.className.includes('alert-danger') ? 'error' :
                    alert.className.includes('alert-warning') ? 'warning' : 'info';
    
    // Show toast
    window.toast.show(message, category);
    
    // Remove original alert
    alert.remove();
  });
});
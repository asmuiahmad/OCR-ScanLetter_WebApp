/**
 * Toast Notification System
 * Unified toast notifications for the entire application
 */

class ToastNotification {
    constructor() {
        this.container = null;
        this.init();
    }
    
    init() {
        // Create toast container if it doesn't exist
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-sm';
            document.body.appendChild(this.container);
        }
    }
    
    show(message, type = 'success', duration = 5000) {
        const toast = this.createToast(message, type);
        this.container.appendChild(toast);
        
        // Trigger animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Auto remove
        setTimeout(() => {
            this.remove(toast);
        }, duration);
        
        return toast;
    }
    
    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} transform translate-x-full transition-all duration-300 ease-in-out`;
        
        const config = this.getTypeConfig(type);
        
        toast.innerHTML = `
            <div class="flex items-center p-4 rounded-lg shadow-lg ${config.bgClass} ${config.textClass} min-w-0">
                <div class="flex-shrink-0">
                    <i class="${config.icon} text-lg"></i>
                </div>
                <div class="ml-3 flex-1 min-w-0">
                    <p class="text-sm font-medium break-words">${message}</p>
                </div>
                <button class="ml-3 flex-shrink-0 toast-close" onclick="window.toast.remove(this.closest('.toast'))">
                    <i class="fas fa-times text-sm opacity-70 hover:opacity-100 transition-opacity"></i>
                </button>
            </div>
        `;
        
        return toast;
    }
    
    getTypeConfig(type) {
        const configs = {
            success: {
                icon: 'fas fa-check-circle',
                bgClass: 'bg-green-600',
                textClass: 'text-white'
            },
            error: {
                icon: 'fas fa-exclamation-circle',
                bgClass: 'bg-red-600',
                textClass: 'text-white'
            },
            warning: {
                icon: 'fas fa-exclamation-triangle',
                bgClass: 'bg-yellow-600',
                textClass: 'text-white'
            },
            info: {
                icon: 'fas fa-info-circle',
                bgClass: 'bg-blue-600',
                textClass: 'text-white'
            }
        };
        
        return configs[type] || configs.info;
    }
    
    remove(toast) {
        if (!toast || !toast.parentNode) return;
        
        toast.classList.remove('show');
        toast.classList.add('translate-x-full');
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
    
    success(message, duration) {
        return this.show(message, 'success', duration);
    }
    
    error(message, duration) {
        return this.show(message, 'error', duration);
    }
    
    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }
    
    info(message, duration) {
        return this.show(message, 'info', duration);
    }
    
    clear() {
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

// Add CSS styles
const toastStyles = `
<style>
.toast.show {
    transform: translateX(0) !important;
}

.toast {
    max-width: 400px;
    word-wrap: break-word;
}

@media (max-width: 640px) {
    #toast-container {
        bottom: 1rem;
        right: 1rem;
        left: 1rem;
        max-width: none;
    }
    
    .toast {
        max-width: none;
    }
}

.toast-close {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    color: inherit;
}

.toast-close:hover {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    padding: 2px;
}
</style>
`;

// Inject styles
if (!document.getElementById('toast-styles')) {
    const styleElement = document.createElement('div');
    styleElement.id = 'toast-styles';
    styleElement.innerHTML = toastStyles;
    document.head.appendChild(styleElement);
}

// Initialize global toast instance
window.toast = new ToastNotification();

// Legacy support - global functions
window.showToast = (message, type, duration) => window.toast.show(message, type, duration);
window.showSuccessToast = (message, duration) => window.toast.success(message, duration);
window.showErrorToast = (message, duration) => window.toast.error(message, duration);
window.showWarningToast = (message, duration) => window.toast.warning(message, duration);
window.showInfoToast = (message, duration) => window.toast.info(message, duration);
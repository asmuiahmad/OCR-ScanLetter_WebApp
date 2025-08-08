/* ===== SPA BACKEND SUPPORT ===== */

// Add CSRF token to all AJAX requests
function setupCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    if (token) {
        // Set default headers for fetch requests
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            if (!options.headers) {
                options.headers = {};
            }
            
            // Add CSRF token for POST, PUT, DELETE requests
            if (options.method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method.toUpperCase())) {
                options.headers['X-CSRFToken'] = token.getAttribute('content');
            }
            
            return originalFetch(url, options);
        };
    }
}

// Handle form submissions via AJAX
function setupAjaxForms() {
    document.addEventListener('submit', async (e) => {
        const form = e.target;
        
        // Skip if form has data-no-ajax attribute
        if (form.hasAttribute('data-no-ajax')) return;
        
        // Skip file upload forms (for now)
        if (form.enctype === 'multipart/form-data') return;
        
        e.preventDefault();
        
        try {
            const formData = new FormData(form);
            const response = await fetch(form.action || window.location.pathname, {
                method: form.method || 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const result = await response.text();
                
                // If response is JSON, handle it
                try {
                    const jsonResult = JSON.parse(result);
                    if (jsonResult.success) {
                        if (jsonResult.redirect) {
                            window.spaNavigation.navigate(jsonResult.redirect);
                        } else if (jsonResult.message) {
                            showToast(jsonResult.message, 'success');
                        }
                    } else {
                        showToast(jsonResult.message || 'Terjadi kesalahan', 'error');
                    }
                } catch {
                    // If not JSON, treat as HTML and update page
                    const pageData = window.spaNavigation.parsePageContent(result);
                    window.spaNavigation.updatePageContent(pageData);
                }
            } else {
                showToast('Terjadi kesalahan saat mengirim data', 'error');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            showToast('Terjadi kesalahan jaringan', 'error');
        }
    });
}

// Setup notification polling for real-time updates
function setupNotificationPolling() {
    if (!window.location.pathname.includes('/dashboard')) return;
    
    setInterval(async () => {
        try {
            const response = await fetch('/api/notifications', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                updateNotificationBadge(data.count);
                updateNotificationDropdown(data.notifications);
            }
        } catch (error) {
            console.error('Notification polling error:', error);
        }
    }, 30000); // Poll every 30 seconds
}

function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-bell-btn .absolute');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    }
}

function updateNotificationDropdown(notifications) {
    const dropdown = document.querySelector('.notification-dropdown ul');
    if (dropdown && notifications) {
        dropdown.innerHTML = notifications.map(notif => `
            <li>
                <div class="flex flex-col gap-1 py-4 px-5 hover:bg-blue-50 transition rounded-xl group border-b last:border-b-0 border-gray-100">
                    <div class="flex flex-row sm:items-center sm:justify-between gap-1">
                        <span class="font-semibold text-gray-800 group-hover:text-blue-700">${notif.title}</span>
                        <span class="inline-block text-xs text-white bg-blue-500 px-3 py-0.5 rounded-full group-hover:bg-blue-700 text-center">${notif.status}</span>
                    </div>
                    <div class="flex items-center text-xs text-gray-500 gap-2 mt-1">
                        <i class="far fa-calendar-alt mr-1"></i>
                        ${notif.date}
                    </div>
                </div>
            </li>
        `).join('');
    }
}

// Initialize all SPA backend support
document.addEventListener('DOMContentLoaded', () => {
    setupCSRFToken();
    setupAjaxForms();
    setupNotificationPolling();
});

// Listen for page content updates to reinitialize
window.addEventListener('pageContentUpdated', () => {
    setupAjaxForms();
});
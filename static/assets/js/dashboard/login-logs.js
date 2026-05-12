/**
 * Login Logs Management
 * Handles loading, displaying, and filtering user login logs
 */

// Login logs variables
let currentPage = 1;
const logsPerPage = 20;

// Load login logs
async function loadLoginLogs(page = 1) {
    try {
        currentPage = page;
        
        console.log('Loading login logs, page:', page);
        
        // Show loading
        document.getElementById('login-logs-content').innerHTML = `
            <div class="p-8 text-center text-gray-500">
                <i class="fas fa-spinner fa-spin mr-2"></i>Memuat log login...
            </div>
        `;

        // Get current filters
        const dateFilter = document.getElementById('date-filter')?.value || '';
        const userFilter = document.getElementById('user-filter')?.value || '';
        
        // Build query parameters
        let queryParams = `page=${page}&per_page=${logsPerPage}`;
        if (dateFilter) queryParams += `&date=${dateFilter}`;
        if (userFilter) queryParams += `&user=${encodeURIComponent(userFilter)}`;

        console.log('Fetching from URL:', `/api/user-login-logs?${queryParams}`);

        // Fetch from backend
        const response = await fetch(`/api/user-login-logs?${queryParams}`);
        
        console.log('Response status:', response.status);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.success) {
            displayLoginLogs(data.logs);
            updatePagination(data.pagination);
            document.getElementById('total-logins').textContent = data.pagination.total;
            
            // Show backend status
            showBackendStatus('Data login real-time berhasil dimuat', 'success');
        } else {
            throw new Error(data.message || 'Failed to load login logs');
        }
        
    } catch (error) {
        console.error('Error loading login logs:', error);
        document.getElementById('login-logs-content').innerHTML = `
            <div class="p-8 text-center text-red-500">
                <i class="fas fa-exclamation-triangle mr-2"></i>Terjadi kesalahan saat memuat log login
                <div class="text-sm mt-2 text-gray-600">Error: ${error.message}</div>
            </div>
        `;
        showBackendStatus('Error memuat data login', 'error');
    }
}

// Display login logs
function displayLoginLogs(logs) {
    const container = document.getElementById('login-logs-content');
    
    if (logs.length === 0) {
        container.innerHTML = `
            <div class="p-8 text-center text-gray-500">
                <i class="fas fa-info-circle mr-2"></i>Tidak ada log login yang ditemukan
            </div>
        `;
        return;
    }

    container.innerHTML = logs.map(log => {
        const statusClass = log.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
        const statusIcon = log.status === 'success' ? 'fas fa-check-circle' : 'fas fa-times-circle';
        
        return `
            <div class="grid grid-cols-4 gap-4 px-4 py-1.5 border-b border-gray-100 hover:bg-gray-50 text-sm">
                <div class="text-gray-900">
                    <div class="font-medium text-xs">${formatDateTime(log.login_time)}</div>
                </div>
                <div class="text-gray-900">
                    <div class="font-medium text-xs truncate">${log.user_email}</div>
                </div>
                <div class="text-gray-600">
                    <div class="font-mono text-xs">${log.ip_address}</div>
                </div>
                <div>
                    <span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium ${statusClass}">
                        <i class="${statusIcon} mr-1"></i>
                        ${log.status === 'success' ? 'Berhasil' : 'Gagal'}
                    </span>
                </div>
            </div>
        `;
    }).join('');
}

// Update pagination
function updatePagination(pagination) {
    document.getElementById('showing-count').textContent = pagination.showing;
    document.getElementById('total-count').textContent = pagination.total;
    document.getElementById('page-info').textContent = `Halaman ${pagination.current_page} dari ${pagination.total_pages}`;
    
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    prevBtn.disabled = !pagination.has_prev;
    nextBtn.disabled = !pagination.has_next;
}

// Clear filters
function clearFilters() {
    document.getElementById('date-filter').value = '';
    document.getElementById('user-filter').value = '';
    loadLoginLogs(1);
}

// Show backend status
function showBackendStatus(message, type) {
    const statusElement = document.getElementById('backend-status');
    if (statusElement) {
        statusElement.textContent = message;
        
        // Add visual indicator based on type
        statusElement.className = 'text-white text-opacity-80 text-sm mt-1';
        if (type === 'warning') {
            statusElement.className += ' text-yellow-200';
        } else if (type === 'error') {
            statusElement.className += ' text-red-200';
        }
    }
}

// Refresh login logs
function refreshLoginLogs() {
    loadLoginLogs(currentPage);
    
    // Show refresh feedback
    const button = event.target.closest('button');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Refreshing...';
    button.disabled = true;
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 1000);
}

// Format date and time
function formatDateTime(dateString) {
    const date = new Date(dateString);
    const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
        timeZone: 'Asia/Jakarta' // Explicitly set to Indonesia timezone
    };
    return date.toLocaleString('id-ID', options);
}

// Add event listeners for filters
document.addEventListener('DOMContentLoaded', function() {
    console.log('Login logs script loaded');
    
    // Load login logs on page load
    loadLoginLogs(1);
    
    // Add filter event listeners
    const dateFilter = document.getElementById('date-filter');
    const userFilter = document.getElementById('user-filter');
    
    if (dateFilter) {
        dateFilter.addEventListener('change', function() {
            loadLoginLogs(1);
        });
    }
    
    if (userFilter) {
        userFilter.addEventListener('input', function() {
            // Debounce the input
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                loadLoginLogs(1);
            }, 500);
        });
    }
    
    // Add test function to window for debugging
    window.testLoginLogs = async function() {
        console.log('=== TESTING LOGIN LOGS ===');
        try {
            const response = await fetch('/api/user-login-logs?page=1&per_page=5');
            console.log('Test response status:', response.status);
            const data = await response.json();
            console.log('Test response data:', data);
            return data;
        } catch (error) {
            console.error('Test error:', error);
            return error;
        }
    };
    
    console.log('You can run testLoginLogs() from console to debug');
});
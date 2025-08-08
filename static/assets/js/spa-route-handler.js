/* ===== SPA ROUTE HANDLER ===== */

// Enhanced route handling for specific pages
class SPARouteHandler {
    constructor() {
        this.routes = new Map();
        this.setupRoutes();
    }

    setupRoutes() {
        // Dashboard routes
        this.routes.set('/dashboard', {
            onLoad: () => this.initDashboard(),
            scripts: ['assets/js/dashboard/login-logs.js']
        });

        // Surat Masuk routes
        this.routes.set('/surat-masuk', {
            onLoad: () => this.initSuratMasuk(),
            scripts: ['assets/js/utils/confirm-delete.js']
        });

        // Surat Keluar routes
        this.routes.set('/surat-keluar', {
            onLoad: () => this.initSuratKeluar(),
            scripts: ['assets/js/utils/confirm-delete.js']
        });

        // OCR routes
        this.routes.set('/ocr/surat-masuk', {
            onLoad: () => this.initOCRSuratMasuk(),
            scripts: []
        });

        this.routes.set('/ocr/surat-keluar', {
            onLoad: () => this.initOCRSuratKeluar(),
            scripts: []
        });

        // Form routes
        this.routes.set('/surat-masuk/input', {
            onLoad: () => this.initInputSuratMasuk(),
            scripts: ['assets/js/forms/input-surat.js']
        });

        this.routes.set('/surat-keluar/input', {
            onLoad: () => this.initInputSuratKeluar(),
            scripts: ['assets/js/forms/input-surat.js']
        });

        // User management
        this.routes.set('/user/edit', {
            onLoad: () => this.initUserManagement(),
            scripts: []
        });

        // Statistics
        this.routes.set('/laporan-statistik', {
            onLoad: () => this.initStatistics(),
            scripts: []
        });
    }

    async handleRoute(url) {
        const route = this.findRoute(url);
        if (route) {
            // Load required scripts
            await this.loadScripts(route.scripts);
            
            // Execute route-specific initialization
            if (route.onLoad) {
                route.onLoad();
            }
        }
    }

    findRoute(url) {
        for (const [pattern, config] of this.routes) {
            if (url.includes(pattern)) {
                return config;
            }
        }
        return null;
    }

    async loadScripts(scripts) {
        for (const script of scripts) {
            await this.loadScript(script);
        }
    }

    loadScript(src) {
        return new Promise((resolve, reject) => {
            // Check if script already loaded
            if (document.querySelector(`script[src*="${src}"]`)) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = `/static/${src}`;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    // Route-specific initialization methods
    initDashboard() {
        // Initialize dashboard-specific functionality
        if (window.loadLoginLogs) {
            window.loadLoginLogs(1);
        }
        
        // Reinitialize charts if present
        if (window.loadChartData) {
            window.loadChartData();
        }
    }

    initSuratMasuk() {
        // Initialize surat masuk table functionality
        this.initTableSearch();
        this.initPagination();
    }

    initSuratKeluar() {
        // Initialize surat keluar table functionality
        this.initTableSearch();
        this.initPagination();
    }

    initOCRSuratMasuk() {
        // Initialize OCR functionality for surat masuk
        this.initFileUpload();
        this.initOCRProcessing();
    }

    initOCRSuratKeluar() {
        // Initialize OCR functionality for surat keluar
        this.initFileUpload();
        this.initOCRProcessing();
    }

    initInputSuratMasuk() {
        // Initialize input form for surat masuk
        this.initFormValidation();
        this.initFileUpload();
    }

    initInputSuratKeluar() {
        // Initialize input form for surat keluar
        this.initFormValidation();
        this.initFileUpload();
    }

    initUserManagement() {
        // Initialize user management functionality
        this.initModals();
        this.initUserForms();
    }

    initStatistics() {
        // Initialize statistics page
        if (window.loadChartData) {
            window.loadChartData();
        }
    }

    // Common initialization methods
    initTableSearch() {
        const searchForm = document.querySelector('.search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                // Handle search via AJAX
                this.handleTableSearch(searchForm);
            });
        }
    }

    initPagination() {
        document.querySelectorAll('.pagination a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                // Handle pagination via AJAX
                this.handlePagination(link.href);
            });
        });
    }

    initFileUpload() {
        // Initialize drag & drop file upload
        const dropAreas = document.querySelectorAll('[id*="drop-area"]');
        dropAreas.forEach(area => {
            this.setupDropArea(area);
        });
    }

    initFormValidation() {
        // Initialize form validation
        document.querySelectorAll('form').forEach(form => {
            this.setupFormValidation(form);
        });
    }

    initModals() {
        // Initialize modal functionality
        document.querySelectorAll('[data-modal]').forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                const modalId = trigger.getAttribute('data-modal');
                this.openModal(modalId);
            });
        });
    }

    initOCRProcessing() {
        // Initialize OCR processing functionality
        const ocrForms = document.querySelectorAll('form[action*="ocr"]');
        ocrForms.forEach(form => {
            form.addEventListener('submit', (e) => {
                this.handleOCRSubmission(e, form);
            });
        });
    }

    initUserForms() {
        // Initialize user management forms
        const userForms = document.querySelectorAll('form[action*="user"]');
        userForms.forEach(form => {
            this.setupUserForm(form);
        });
    }

    // Helper methods
    async handleTableSearch(form) {
        const formData = new FormData(form);
        const params = new URLSearchParams(formData);
        const url = `${form.action}?${params}`;
        
        try {
            const response = await fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            
            if (response.ok) {
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                // Update table content
                const newTable = doc.querySelector('.overflow-x-auto');
                const currentTable = document.querySelector('.overflow-x-auto');
                if (newTable && currentTable) {
                    currentTable.innerHTML = newTable.innerHTML;
                    this.initPagination(); // Reinitialize pagination
                }
            }
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    async handlePagination(url) {
        try {
            const response = await fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            
            if (response.ok) {
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                // Update table and pagination
                const newContent = doc.querySelector('.container');
                const currentContent = document.querySelector('.container');
                if (newContent && currentContent) {
                    currentContent.innerHTML = newContent.innerHTML;
                    this.initTableSearch();
                    this.initPagination();
                }
            }
        } catch (error) {
            console.error('Pagination error:', error);
        }
    }

    setupDropArea(area) {
        const fileInput = area.querySelector('input[type="file"]');
        if (!fileInput) return;

        area.addEventListener('click', () => fileInput.click());
        
        area.addEventListener('dragover', (e) => {
            e.preventDefault();
            area.classList.add('dragover');
        });
        
        area.addEventListener('dragleave', () => {
            area.classList.remove('dragover');
        });
        
        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                this.updateFileName(area, fileInput.files[0].name);
            }
        });
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                this.updateFileName(area, fileInput.files[0].name);
            }
        });
    }

    updateFileName(area, fileName) {
        const nameDisplay = area.querySelector('[id*="file-selected-name"]');
        if (nameDisplay) {
            nameDisplay.textContent = fileName;
        }
    }

    setupFormValidation(form) {
        form.addEventListener('submit', (e) => {
            // Add custom validation logic here
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('border-red-500');
                } else {
                    field.classList.remove('border-red-500');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showToast('Mohon lengkapi semua field yang wajib diisi', 'error');
            }
        });
    }

    handleOCRSubmission(e, form) {
        e.preventDefault();
        
        const fileInput = form.querySelector('input[type="file"]');
        if (!fileInput || !fileInput.files.length) {
            showToast('Mohon pilih file terlebih dahulu', 'error');
            return;
        }
        
        // Show processing indicator
        showToast('Memproses OCR...', 'info');
        
        // Submit form normally for OCR processing
        form.submit();
    }

    setupUserForm(form) {
        // Add user-specific form handling
        const passwordFields = form.querySelectorAll('input[type="password"]');
        passwordFields.forEach(field => {
            this.addPasswordToggle(field);
        });
    }

    addPasswordToggle(field) {
        const container = field.parentElement;
        const toggle = container.querySelector('.password-toggle, .password-toggle-btn');
        
        if (toggle) {
            toggle.addEventListener('click', () => {
                const type = field.type === 'password' ? 'text' : 'password';
                field.type = type;
                
                const icon = toggle.querySelector('i');
                if (icon) {
                    icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
                }
            });
        }
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    }
}

// Initialize route handler
document.addEventListener('DOMContentLoaded', () => {
    window.spaRouteHandler = new SPARouteHandler();
});

// Listen for page content updates
window.addEventListener('pageContentUpdated', () => {
    const currentUrl = window.location.pathname;
    window.spaRouteHandler.handleRoute(currentUrl);
});

window.SPARouteHandler = SPARouteHandler;
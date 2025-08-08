/**
 * OCR Modal - Optimized JavaScript
 * Lazy loading and performance optimized
 */

// Critical functions - loaded immediately
const OCRModal = {
    // Cache DOM elements
    modal: null,
    imagePreview: null,
    form: null,
    
    // Initialize with minimal DOM queries
    init() {
        this.modal = document.getElementById('extractedDataModal');
        if (!this.modal) return;
        
        this.imagePreview = document.getElementById('imagePreview');
        this.form = document.getElementById('extractedDataForm');
        
        // Bind critical events only
        this.bindCriticalEvents();
        
        // Lazy load non-critical features
        this.lazyLoadFeatures();
    },
    
    // Bind only essential events first
    bindCriticalEvents() {
        // Close modal events
        const closeBtn = document.getElementById('closeModalBtn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close(), { passive: true });
        }
        
        // Backdrop click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.close();
        }, { passive: true });
        
        // Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.modal.classList.contains('hidden')) {
                this.close();
            }
        }, { passive: true });
    },
    
    // Lazy load non-critical features
    lazyLoadFeatures() {
        // Use requestIdleCallback for non-critical features
        if ('requestIdleCallback' in window) {
            requestIdleCallback(() => this.loadZoomFeatures());
            requestIdleCallback(() => this.loadNavigationFeatures());
            requestIdleCallback(() => this.loadFormFeatures());
        } else {
            // Fallback for browsers without requestIdleCallback
            setTimeout(() => {
                this.loadZoomFeatures();
                this.loadNavigationFeatures();
                this.loadFormFeatures();
            }, 100);
        }
    },
    
    // Load zoom features when needed
    loadZoomFeatures() {
        const zoomInBtn = document.getElementById('zoomInBtn');
        const zoomOutBtn = document.getElementById('zoomOutBtn');
        const resetZoomBtn = document.getElementById('resetZoomBtn');
        const zoomLevel = document.getElementById('zoomLevel');
        
        if (!zoomInBtn || !this.imagePreview) return;
        
        let currentZoom = 1;
        let isDragging = false;
        let startX, startY, scrollLeft, scrollTop;
        
        // Zoom functions
        const updateZoom = (zoom) => {
            currentZoom = Math.max(0.5, Math.min(3, zoom));
            this.imagePreview.style.transform = `scale(${currentZoom})`;
            if (zoomLevel) zoomLevel.textContent = `${Math.round(currentZoom * 100)}%`;
        };
        
        // Event listeners with passive where possible
        zoomInBtn.addEventListener('click', () => updateZoom(currentZoom + 0.2), { passive: true });
        zoomOutBtn.addEventListener('click', () => updateZoom(currentZoom - 0.2), { passive: true });
        resetZoomBtn?.addEventListener('click', () => updateZoom(1), { passive: true });
        
        // Mouse wheel zoom
        this.imagePreview.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? -0.1 : 0.1;
            updateZoom(currentZoom + delta);
        });
        
        // Pan functionality
        this.imagePreview.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.pageX - this.imagePreview.offsetLeft;
            startY = e.pageY - this.imagePreview.offsetTop;
            this.imagePreview.style.cursor = 'grabbing';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            e.preventDefault();
            const x = e.pageX - startX;
            const y = e.pageY - startY;
            this.imagePreview.style.left = `${x}px`;
            this.imagePreview.style.top = `${y}px`;
        }, { passive: false });
        
        document.addEventListener('mouseup', () => {
            isDragging = false;
            this.imagePreview.style.cursor = 'grab';
        }, { passive: true });
    },
    
    // Load navigation features
    loadNavigationFeatures() {
        const prevBtn = document.getElementById('prevModalBtn');
        const nextBtn = document.getElementById('nextModalBtn');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.navigate(-1), { passive: true });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.navigate(1), { passive: true });
        }
    },
    
    // Load form features
    loadFormFeatures() {
        const saveBtn = document.getElementById('saveExtractedData');
        
        if (saveBtn && this.form) {
            saveBtn.addEventListener('click', () => this.saveData(), { passive: true });
        }
        
        // Form validation
        if (this.form) {
            this.form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveData();
            });
        }
    },
    
    // Modal methods
    show() {
        if (!this.modal) return;
        
        this.modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        // Focus management
        const firstFocusable = this.modal.querySelector('button, input, textarea, select');
        if (firstFocusable) {
            firstFocusable.focus();
        }
    },
    
    close() {
        if (!this.modal) return;
        
        this.modal.classList.add('hidden');
        document.body.style.overflow = '';
    },
    
    navigate(direction) {
        // Navigation logic here
        console.log('Navigate:', direction);
    },
    
    saveData() {
        if (!this.form) return;
        
        // Add loading state
        const saveBtn = document.getElementById('saveExtractedData');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.textContent = 'Menyimpan...';
        }
        
        // Form submission logic here
        const formData = new FormData(this.form);
        
        // Simulate save (replace with actual implementation)
        setTimeout(() => {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '💾 Simpan Data';
            }
            this.close();
        }, 1000);
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => OCRModal.init());
} else {
    OCRModal.init();
}

// Export for global access
window.OCRModal = OCRModal;
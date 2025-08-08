/**
 * OCR Modal Functionality for Surat Masuk
 * Enhanced modal with image zoom, pan, and form handling
 */

class OCRModalSuratMasuk {
    constructor(extractedDataList, imagePaths) {
        this.extractedDataList = extractedDataList || [];
        this.imagePaths = imagePaths || [];
        this.currentIndex = 0;
        this.scale = 1;
        this.panning = false;
        this.pointX = 0;
        this.pointY = 0;
        this.start = { x: 0, y: 0 };
        
        this.init();
    }
    
    init() {
        this.bindElements();
        this.setupEventListeners();
        this.createViewButton();
    }
    
    bindElements() {
        this.modal = document.getElementById('extractedDataModal');
        this.closeBtn = document.getElementById('closeModalBtn');
        this.prevBtn = document.getElementById('prevModalBtn');
        this.nextBtn = document.getElementById('nextModalBtn');
        this.saveBtn = document.getElementById('saveExtractedData');
        this.form = document.getElementById('extractedDataForm');
        this.imagePreview = document.getElementById('imagePreview');
        this.imageContainer = document.getElementById('imagePreviewContainer');
        this.noImageText = document.getElementById('noImageText');
        this.zoomInBtn = document.getElementById('zoomInBtn');
        this.zoomOutBtn = document.getElementById('zoomOutBtn');
        this.resetZoomBtn = document.getElementById('resetZoomBtn');
        this.zoomLevel = document.getElementById('zoomLevel');
    }
    
    setupEventListeners() {
        // Modal controls
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.closeModal());
        }
        
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => this.previousDocument());
        }
        
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => this.nextDocument());
        }
        
        if (this.saveBtn && !this.saveBtn.hasAttribute('data-handler-added')) {
            this.saveBtn.addEventListener('click', () => this.saveData());
            this.saveBtn.setAttribute('data-handler-added', 'true');
        }
        
        // Modal backdrop click
        if (this.modal) {
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.closeModal();
                }
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (!this.modal || this.modal.classList.contains('hidden')) return;
            
            switch(e.key) {
                case 'Escape':
                    this.closeModal();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.previousDocument();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.nextDocument();
                    break;
                case 's':
                case 'S':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.saveData();
                    }
                    break;
            }
        });
        
        // Zoom controls
        if (this.zoomInBtn) {
            this.zoomInBtn.addEventListener('click', () => this.zoomIn());
        }
        
        if (this.zoomOutBtn) {
            this.zoomOutBtn.addEventListener('click', () => this.zoomOut());
        }
        
        if (this.resetZoomBtn) {
            this.resetZoomBtn.addEventListener('click', () => this.resetZoom());
        }
        
        // Image pan and zoom
        this.setupImageInteraction();
    }
    
    setupImageInteraction() {
        if (!this.imageContainer) return;
        
        // Mouse wheel zoom
        this.imageContainer.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? -0.1 : 0.1;
            this.zoom(delta);
        });
        
        // Pan functionality
        this.imageContainer.addEventListener('mousedown', (e) => {
            if (e.target === this.imagePreview) {
                this.panning = true;
                this.start = { 
                    x: e.clientX - this.pointX, 
                    y: e.clientY - this.pointY 
                };
                this.imageContainer.classList.add('grabbing');
            }
        });
        
        this.imageContainer.addEventListener('mousemove', (e) => {
            if (this.panning) {
                this.pointX = e.clientX - this.start.x;
                this.pointY = e.clientY - this.start.y;
                this.updateImageTransform();
            }
        });
        
        this.imageContainer.addEventListener('mouseup', () => {
            this.panning = false;
            this.imageContainer.classList.remove('grabbing');
        });
        
        this.imageContainer.addEventListener('mouseleave', () => {
            this.panning = false;
            this.imageContainer.classList.remove('grabbing');
        });
    }
    
    createViewButton() {
        // Check if button already exists in template
        const existingBtn = document.getElementById('viewExtractedDataBtn');
        if (existingBtn) {
            // Button already exists in template, just add event listener
            existingBtn.addEventListener('click', () => this.openModal());
            return;
        }
        
        // Create button only if it doesn't exist and we have data
        if (!this.extractedDataList || this.extractedDataList.length === 0) return;
        
        const viewDataBtn = document.createElement('button');
        viewDataBtn.id = 'viewExtractedDataBtn';
        viewDataBtn.className = 'mt-4 bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition duration-300 font-medium text-lg shadow-lg w-full';
        viewDataBtn.innerHTML = `
            <i class="fas fa-eye mr-2"></i>
            Lihat Hasil Ekstraksi (${this.extractedDataList.length} dokumen)
        `;
        
        viewDataBtn.addEventListener('click', () => this.openModal());
        
        const uploadForm = document.getElementById('uploadForm');
        if (uploadForm) {
            uploadForm.parentNode.insertBefore(viewDataBtn, uploadForm.nextSibling);
        }
    }
    
    openModal() {
        if (!this.modal) return;
        
        this.modal.classList.remove('hidden');
        this.currentIndex = 0;
        this.fillFormWithData(this.extractedDataList[0]);
        this.updateNavButtons();
        this.resetZoom();
        
        // Focus management
        this.modal.focus();
    }
    
    closeModal() {
        if (!this.modal) return;
        
        this.modal.classList.add('hidden');
        this.resetZoom();
    }
    
    previousDocument() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.fillFormWithData(this.extractedDataList[this.currentIndex]);
            this.updateNavButtons();
            this.resetZoom();
        }
    }
    
    nextDocument() {
        if (this.currentIndex < this.extractedDataList.length - 1) {
            this.currentIndex++;
            this.fillFormWithData(this.extractedDataList[this.currentIndex]);
            this.updateNavButtons();
            this.resetZoom();
        }
    }
    
    updateNavButtons() {
        if (!this.prevBtn || !this.nextBtn) return;
        
        if (this.extractedDataList.length <= 1) {
            this.prevBtn.style.display = 'none';
            this.nextBtn.style.display = 'none';
        } else {
            this.prevBtn.style.display = 'inline-block';
            this.nextBtn.style.display = 'inline-block';
            this.prevBtn.disabled = (this.currentIndex === 0);
            this.nextBtn.disabled = (this.currentIndex === this.extractedDataList.length - 1);
        }
    }
    
    fillFormWithData(data) {
        if (!this.form || !data) return;
        
        // Field mappings
        const fieldMappings = {
            'full_letter_number': data['nomor_surat'] || '',
            'pengirim_suratMasuk': data['pengirim'] || '',
            'penerima_suratMasuk': data['penerima'] || '',
            'isi_suratMasuk': data['isi'] || '',
            'acara_suratMasuk': data['acara'] || '',
            'tempat_suratMasuk': data['tempat'] || '',
            'tanggal': data['tanggal'] || ''
        };
        
        // Fill form fields
        Object.entries(fieldMappings).forEach(([name, value]) => {
            const input = this.form.querySelector(`[name="${name}"]`);
            if (input) {
                input.value = value;
            }
        });
        
        // Handle special date fields
        this.handleDateField('tanggal_acara_suratMasuk', data['tanggal_acara']);
        this.handleTimeField('jam_suratMasuk', data['jam']);
        
        // Update image preview
        this.updateImagePreview(data);
    }
    
    handleDateField(fieldName, dateValue) {
        const input = this.form.querySelector(`[name="${fieldName}"]`);
        if (!input) return;
        
        if (dateValue) {
            const parsedDate = this.parseDate(dateValue);
            input.value = parsedDate || '';
        } else {
            input.value = '';
        }
    }
    
    handleTimeField(fieldName, timeValue) {
        const input = this.form.querySelector(`[name="${fieldName}"]`);
        if (!input) return;
        
        if (timeValue) {
            const parsedTime = this.parseTime(timeValue);
            input.value = parsedTime || '';
        } else {
            input.value = '';
        }
    }
    
    parseDate(dateStr) {
        if (!dateStr) return null;
        
        const formats = [
            /(\d{1,2})\/(\d{1,2})\/(\d{4})/,
            /(\d{1,2})-(\d{1,2})-(\d{4})/,
            /(\d{4})-(\d{1,2})-(\d{1,2})/,
            /(\d{1,2})\/(\d{1,2})\/(\d{2})/,
            /(\d{1,2})-(\d{1,2})-(\d{2})/
        ];
        
        for (let format of formats) {
            const match = dateStr.match(format);
            if (match) {
                let day, month, year;
                if (match[1].length === 4) {
                    year = match[1];
                    month = match[2].padStart(2, '0');
                    day = match[3].padStart(2, '0');
                } else {
                    day = match[1].padStart(2, '0');
                    month = match[2].padStart(2, '0');
                    year = match[3].length === 2 ? '20' + match[3] : match[3];
                }
                return `${year}-${month}-${day}`;
            }
        }
        return null;
    }
    
    parseTime(timeStr) {
        if (!timeStr) return null;
        
        const formats = [
            /(\d{1,2}):(\d{2})/,
            /(\d{1,2})\.(\d{2})/,
            /(\d{1,2})\.(\d{2})\s*(WIB|WITA|WIT)?/,
            /(\d{1,2}):(\d{2})\s*(WIB|WITA|WIT)?/,
            /(\d{1,2})\s*(\d{2})/
        ];
        
        for (let format of formats) {
            const match = timeStr.match(format);
            if (match) {
                const hour = match[1].padStart(2, '0');
                const minute = match[2].padStart(2, '0');
                return `${hour}:${minute}`;
            }
        }
        return null;
    }
    
    updateImagePreview(data) {
        if (!this.imagePreview || !this.noImageText) return;
        
        if (data.filename) {
            const imagePath = `/static/ocr/surat_masuk/${data.filename}`;
            this.imagePreview.src = imagePath;
            this.imagePreview.classList.remove('hidden');
            this.noImageText.classList.add('hidden');
        } else {
            this.imagePreview.classList.add('hidden');
            this.noImageText.classList.remove('hidden');
        }
    }
    
    zoomIn() {
        this.zoom(0.1);
    }
    
    zoomOut() {
        this.zoom(-0.1);
    }
    
    zoom(delta) {
        const newScale = this.scale + delta;
        if (newScale > 0.1 && newScale < 5) {
            this.scale = newScale;
            this.updateImageTransform();
        }
    }
    
    resetZoom() {
        this.scale = 1;
        this.pointX = 0;
        this.pointY = 0;
        this.updateImageTransform();
    }
    
    updateImageTransform() {
        if (this.imagePreview) {
            this.imagePreview.style.transform = `translate(${this.pointX}px, ${this.pointY}px) scale(${this.scale})`;
            if (this.zoomLevel) {
                this.zoomLevel.textContent = Math.round(this.scale * 100) + '%';
            }
        }
    }
    
    async saveData() {
        if (!this.form || !this.saveBtn) return;
        
        const formData = new FormData(this.form);
        const extractedData = [];
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        
        if (!csrfToken) {
            this.showError('CSRF token tidak ditemukan');
            return;
        }
        
        // Show loading state
        const originalText = this.saveBtn.innerHTML;
        this.saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Menyimpan...';
        this.saveBtn.disabled = true;
        
        // Collect form data
        const rowData = {};
        formData.forEach((value, key) => {
            rowData[key] = value;
        });
        extractedData.push(rowData);
        
        try {
            const response = await fetch('/surat-masuk/save_extracted_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin',
                body: JSON.stringify(extractedData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess();
                setTimeout(() => {
                    this.closeModal();
                    window.location.reload();
                }, 1500);
            } else {
                throw new Error(data.error || 'Gagal menyimpan data');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError(error.message);
            
            // Reset button after 3 seconds
            setTimeout(() => {
                this.saveBtn.innerHTML = originalText;
                this.saveBtn.style.backgroundColor = '';
                this.saveBtn.disabled = false;
            }, 3000);
        }
    }
    
    showSuccess() {
        if (!this.saveBtn) return;
        
        this.saveBtn.innerHTML = '<i class="fas fa-check mr-2"></i>Berhasil!';
        this.saveBtn.style.backgroundColor = '#059669';
    }
    
    showError(message) {
        if (!this.saveBtn) return;
        
        this.saveBtn.innerHTML = '<i class="fas fa-exclamation-triangle mr-2"></i>Gagal!';
        this.saveBtn.style.backgroundColor = '#dc2626';
        
        // Show error message
        alert('Terjadi kesalahan saat menyimpan data: ' + message);
    }
}

// Make class available globally
window.OCRModalSuratMasuk = OCRModalSuratMasuk;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get data from template
    const extractedDataList = window.extractedDataList || [];
    const imagePaths = window.imagePaths || [];
    
    // Initialize OCR Modal
    if (extractedDataList.length > 0) {
        new OCRModalSuratMasuk(extractedDataList, imagePaths);
    }
});
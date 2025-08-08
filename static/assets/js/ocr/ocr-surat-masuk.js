/**
 * OCR Surat Masuk JavaScript functionality
 * Handles file upload, drag & drop, image preview, zoom, and form processing
 */

// Global variables
let extractedDataList = [];
let imagePaths = [];
let currentIndex = 0;
let zoomLevel = 1;
let isDragging = false;
let dragStart = { x: 0, y: 0 };
let imagePosition = { x: 0, y: 0 };

/**
 * Initialize OCR functionality when DOM is ready
 */
function initializeOCR() {
    setupFileUpload();
    setupDragAndDrop();
    setupImagePreview();
    setupModalFunctionality();
    setupFormHandling();
    
    console.log('OCR functionality initialized');
}

/**
 * Setup file upload functionality
 */
function setupFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const selectedFilesText = document.getElementById('selectedFiles');
    const filePreview = document.getElementById('filePreview');

    if (!fileInput) return;

    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            const fileNames = Array.from(this.files)
                .map(file => file.name)
                .join(', ');
            
            if (selectedFilesText) {
                selectedFilesText.textContent = `Dipilih: ${fileNames}`;
                selectedFilesText.classList.remove('text-gray-600');
                selectedFilesText.classList.add('text-green-600');
            }
            
            if (filePreview) {
                filePreview.classList.remove('hidden');
            }
        } else {
            if (selectedFilesText) {
                selectedFilesText.textContent = 'Belum ada file dipilih';
                selectedFilesText.classList.remove('text-green-600');
                selectedFilesText.classList.add('text-gray-600');
            }
            
            if (filePreview) {
                filePreview.classList.add('hidden');
            }
        }
    });
}

/**
 * Setup drag and drop functionality
 */
function setupDragAndDrop() {
    const dropZone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');

    if (!dropZone || !fileInput) return;

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        dropZone.classList.add('dragover');
    }

    function unhighlight(e) {
        dropZone.classList.remove('dragover');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        fileInput.files = files;
        
        // Trigger change event
        const event = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(event);
    }
}

/**
 * Setup image preview with zoom and pan functionality
 */
function setupImagePreview() {
    const imagePreview = document.getElementById('imagePreview');
    const imageContainer = document.getElementById('imagePreviewContainer');
    const zoomInBtn = document.getElementById('zoomInBtn');
    const zoomOutBtn = document.getElementById('zoomOutBtn');
    const resetZoomBtn = document.getElementById('resetZoomBtn');
    const zoomLevelDisplay = document.getElementById('zoomLevel');

    if (!imagePreview || !imageContainer) return;

    // Zoom controls
    if (zoomInBtn) {
        zoomInBtn.addEventListener('click', () => zoomImage(1.2));
    }
    
    if (zoomOutBtn) {
        zoomOutBtn.addEventListener('click', () => zoomImage(0.8));
    }
    
    if (resetZoomBtn) {
        resetZoomBtn.addEventListener('click', resetZoom);
    }

    // Mouse wheel zoom
    imageContainer.addEventListener('wheel', function(e) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        zoomImage(delta);
    });

    // Pan functionality
    imagePreview.addEventListener('mousedown', startDrag);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', endDrag);

    function zoomImage(factor) {
        zoomLevel *= factor;
        zoomLevel = Math.max(0.1, Math.min(5, zoomLevel)); // Limit zoom between 10% and 500%
        
        imagePreview.style.transform = `scale(${zoomLevel}) translate(${imagePosition.x}px, ${imagePosition.y}px)`;
        
        if (zoomLevelDisplay) {
            zoomLevelDisplay.textContent = `${Math.round(zoomLevel * 100)}%`;
        }
    }

    function resetZoom() {
        zoomLevel = 1;
        imagePosition = { x: 0, y: 0 };
        imagePreview.style.transform = 'scale(1) translate(0px, 0px)';
        
        if (zoomLevelDisplay) {
            zoomLevelDisplay.textContent = '100%';
        }
    }

    function startDrag(e) {
        if (zoomLevel <= 1) return; // Only allow panning when zoomed in
        
        isDragging = true;
        dragStart.x = e.clientX - imagePosition.x;
        dragStart.y = e.clientY - imagePosition.y;
        imagePreview.style.cursor = 'grabbing';
    }

    function drag(e) {
        if (!isDragging) return;
        
        e.preventDefault();
        imagePosition.x = e.clientX - dragStart.x;
        imagePosition.y = e.clientY - dragStart.y;
        
        imagePreview.style.transform = `scale(${zoomLevel}) translate(${imagePosition.x}px, ${imagePosition.y}px)`;
    }

    function endDrag() {
        isDragging = false;
        imagePreview.style.cursor = 'move';
    }
}

/**
 * Setup modal functionality
 */
function setupModalFunctionality() {
    const modal = document.getElementById('extractedDataModal');
    const closeBtn = document.getElementById('closeModalBtn');
    const prevBtn = document.getElementById('prevModalBtn');
    const nextBtn = document.getElementById('nextModalBtn');

    if (!modal) return;

    // Close modal functionality
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }

    // Close modal when clicking outside
    modal.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Navigation buttons
    if (prevBtn) {
        prevBtn.addEventListener('click', navigatePrevious);
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', navigateNext);
    }

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (!modal.classList.contains('hidden')) {
            switch(e.key) {
                case 'Escape':
                    closeModal();
                    break;
                case 'ArrowLeft':
                    navigatePrevious();
                    break;
                case 'ArrowRight':
                    navigateNext();
                    break;
            }
        }
    });
}

/**
 * Setup form handling
 */
function setupFormHandling() {
    const saveBtn = document.getElementById('saveExtractedData');
    const uploadForm = document.getElementById('uploadForm');

    if (saveBtn) {
        saveBtn.addEventListener('click', saveExtractedData);
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const submitBtn = uploadForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Memproses...';
            }
        });
    }
}

/**
 * Fill form with extracted data
 * @param {Object} data - Extracted data object
 */
function fillFormWithData(data) {
    const form = document.getElementById('extractedDataForm');
    if (!form || !data) return;

    // Field mappings for surat masuk
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
        const input = form.querySelector(`[name="${name}"]`);
        if (input) {
            input.value = value;
        }
    });

    // Handle special date and time fields
    handleSpecialFields(form, data);

    // Update image preview
    updateImagePreview(data);

    // Update navigation buttons
    updateNavigationButtons();
}

/**
 * Handle special date and time fields
 * @param {HTMLElement} form - Form element
 * @param {Object} data - Data object
 */
function handleSpecialFields(form, data) {
    // Handle tanggal acara
    const tanggalAcaraInput = form.querySelector('[name="tanggal_acara_suratMasuk"]');
    if (tanggalAcaraInput && data['tanggal_acara']) {
        const parsedDate = parseTanggalAcara(data['tanggal_acara']);
        tanggalAcaraInput.value = parsedDate || '';
    }

    // Handle jam acara
    const jamAcaraInput = form.querySelector('[name="jam_suratMasuk"]');
    if (jamAcaraInput && data['jam']) {
        const parsedTime = parseJamAcara(data['jam']);
        jamAcaraInput.value = parsedTime || '';
    }
}

/**
 * Parse tanggal acara from various formats
 * @param {string} tanggalStr - Date string
 * @returns {string|null} Formatted date string (YYYY-MM-DD) or null
 */
function parseTanggalAcara(tanggalStr) {
    if (!tanggalStr) return null;

    const formats = [
        /(\d{1,2})\/(\d{1,2})\/(\d{4})/, // DD/MM/YYYY
        /(\d{1,2})-(\d{1,2})-(\d{4})/, // DD-MM-YYYY
        /(\d{4})-(\d{1,2})-(\d{1,2})/, // YYYY-MM-DD
        /(\d{1,2})\/(\d{1,2})\/(\d{2})/, // DD/MM/YY
        /(\d{1,2})-(\d{1,2})-(\d{2})/  // DD-MM-YY
    ];

    for (let format of formats) {
        const match = tanggalStr.match(format);
        if (match) {
            let day, month, year;
            if (match[1].length === 4) {
                // Format YYYY-MM-DD
                year = match[1];
                month = match[2].padStart(2, '0');
                day = match[3].padStart(2, '0');
            } else {
                // Format DD/MM/YYYY or DD-MM-YYYY
                day = match[1].padStart(2, '0');
                month = match[2].padStart(2, '0');
                year = match[3].length === 2 ? '20' + match[3] : match[3];
            }
            return `${year}-${month}-${day}`;
        }
    }
    return null;
}

/**
 * Parse jam acara from various formats
 * @param {string} jamStr - Time string
 * @returns {string|null} Formatted time string (HH:MM) or null
 */
function parseJamAcara(jamStr) {
    if (!jamStr) return null;

    const formats = [
        /(\d{1,2}):(\d{2})/, // HH:MM
        /(\d{1,2})\.(\d{2})/, // HH.MM
        /(\d{1,2})\.(\d{2})\s*(WIB|WITA|WIT)?/, // HH.MM WIB
        /(\d{1,2}):(\d{2})\s*(WIB|WITA|WIT)?/, // HH:MM WIB
        /(\d{1,2})\s*(\d{2})/ // HH MM
    ];

    for (let format of formats) {
        const match = jamStr.match(format);
        if (match) {
            const hour = match[1].padStart(2, '0');
            const minute = match[2].padStart(2, '0');
            return `${hour}:${minute}`;
        }
    }
    return null;
}

/**
 * Update image preview
 * @param {Object} data - Data object containing filename
 */
function updateImagePreview(data) {
    const imagePreview = document.getElementById('imagePreview');
    const noImageText = document.getElementById('noImageText');

    if (!imagePreview || !noImageText) return;

    if (data.filename) {
        const imagePath = `/static/ocr/surat_masuk/${data.filename}`;
        imagePreview.src = imagePath;
        imagePreview.classList.remove('hidden');
        noImageText.classList.add('hidden');
        
        // Reset zoom when changing image
        resetImageZoom();
    } else {
        imagePreview.classList.add('hidden');
        noImageText.classList.remove('hidden');
    }
}

/**
 * Reset image zoom and position
 */
function resetImageZoom() {
    const imagePreview = document.getElementById('imagePreview');
    const zoomLevelDisplay = document.getElementById('zoomLevel');
    
    if (imagePreview) {
        zoomLevel = 1;
        imagePosition = { x: 0, y: 0 };
        imagePreview.style.transform = 'scale(1) translate(0px, 0px)';
    }
    
    if (zoomLevelDisplay) {
        zoomLevelDisplay.textContent = '100%';
    }
}

/**
 * Update navigation buttons state
 */
function updateNavigationButtons() {
    const prevBtn = document.getElementById('prevModalBtn');
    const nextBtn = document.getElementById('nextModalBtn');

    if (!extractedDataList || extractedDataList.length <= 1) {
        if (prevBtn) prevBtn.style.display = 'none';
        if (nextBtn) nextBtn.style.display = 'none';
    } else {
        if (prevBtn) {
            prevBtn.style.display = 'inline-block';
            prevBtn.disabled = (currentIndex === 0);
        }
        if (nextBtn) {
            nextBtn.style.display = 'inline-block';
            nextBtn.disabled = (currentIndex === extractedDataList.length - 1);
        }
    }
}

/**
 * Navigate to previous item
 */
function navigatePrevious() {
    if (currentIndex > 0) {
        currentIndex--;
        fillFormWithData(extractedDataList[currentIndex]);
    }
}

/**
 * Navigate to next item
 */
function navigateNext() {
    if (currentIndex < extractedDataList.length - 1) {
        currentIndex++;
        fillFormWithData(extractedDataList[currentIndex]);
    }
}

/**
 * Close modal
 */
function closeModal() {
    const modal = document.getElementById('extractedDataModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

/**
 * Show modal with extracted data
 */
function showModal() {
    const modal = document.getElementById('extractedDataModal');
    if (modal && extractedDataList.length > 0) {
        modal.classList.remove('hidden');
        currentIndex = 0;
        fillFormWithData(extractedDataList[0]);
    }
}

/**
 * Save extracted data to server
 */
function saveExtractedData() {
    const form = document.getElementById('extractedDataForm');
    const saveBtn = document.getElementById('saveExtractedData');
    
    if (!form) {
        showAlert('Form tidak ditemukan', 'error');
        return;
    }

    // Show loading state
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Menyimpan...';
    }

    const formData = new FormData(form);
    const extractedData = [];
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

    // Collect form data
    const rowData = {};
    formData.forEach((value, key) => {
        rowData[key] = value;
    });
    extractedData.push(rowData);

    // Send data to server
    fetch('/ocr-surat-masuk/save-extracted-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken || ''
        },
        credentials: 'same-origin',
        body: JSON.stringify(extractedData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showAlert('Data berhasil disimpan', 'success');
            closeModal();
            setTimeout(() => window.location.reload(), 1500);
        } else {
            throw new Error(data.error || 'Gagal menyimpan data');
        }
    })
    .catch(error => {
        console.error('Error saving data:', error);
        showAlert(`Terjadi kesalahan: ${error.message}`, 'error');
    })
    .finally(() => {
        // Reset button state
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = 'Simpan';
        }
    });
}

/**
 * Show alert message
 * @param {string} message - Alert message
 * @param {string} type - Alert type (success, error, info, warning)
 */
function showAlert(message, type = 'info') {
    // Try to use existing toast notification system
    if (typeof showToast === 'function') {
        showToast(message, type);
        return;
    }
    
    // Fallback to browser alert
    alert(message);
}

/**
 * Initialize extracted data from server response
 * @param {Array} dataList - List of extracted data
 * @param {Array} imageList - List of image paths
 */
function initializeExtractedData(dataList, imageList) {
    extractedDataList = dataList || [];
    imagePaths = imageList || [];
    
    if (extractedDataList.length > 0) {
        createViewDataButton();
    }
}

/**
 * Create "View Extracted Data" button
 */
function createViewDataButton() {
    const uploadForm = document.getElementById('uploadForm');
    if (!uploadForm || document.getElementById('viewExtractedDataBtn')) return;

    const viewDataBtn = document.createElement('button');
    viewDataBtn.id = 'viewExtractedDataBtn';
    viewDataBtn.type = 'button';
    viewDataBtn.className = 'mt-4 bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition duration-300 font-medium text-lg shadow-lg w-full';
    viewDataBtn.innerHTML = `
        <svg class="w-5 h-5 inline mr-2 align-text-bottom" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
        </svg>
        Lihat Hasil Ekstraksi (${extractedDataList.length} dokumen)
    `;
    
    viewDataBtn.addEventListener('click', showModal);
    
    uploadForm.parentNode.insertBefore(viewDataBtn, uploadForm.nextSibling);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeOCR);

// Export functions for global access
window.ocrSuratMasuk = {
    initializeExtractedData,
    showModal,
    closeModal,
    saveExtractedData
};
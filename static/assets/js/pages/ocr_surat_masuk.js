// Get base URLs from data attributes
const suratMasukImageBaseUrl = document.querySelector('#ocr-form').dataset.suratMasukImageUrl;
const staticImageBaseUrl = document.querySelector('#ocr-form').dataset.staticImageUrl;
const ocrEndpoint = document.querySelector('#ocr-form').dataset.ocrEndpoint;
    let currentIndex = 0;
const extractedDataList = JSON.parse(document.querySelector('#ocr-form').dataset.extractedDataList || '[]');
const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    function openModal(index) {
        if (index < 0 || index >= extractedDataList.length) {
            alert("Indeks di luar batas.");
            return;
        }

        resetZoom();
        currentIndex = index;
        const data = extractedDataList[index];
        
        // Atur sumber gambar
        const imageSrc = data.id_suratMasuk !== null ? 
            suratMasukImageBaseUrl.replace('0', data.id_suratMasuk) : 
            staticImageBaseUrl + data.filename;
        document.getElementById('modal-image').src = imageSrc;

        // Isi nilai awal (hidden)
        document.getElementById('initial_full_letter_number').value = data.full_letter_number || '';
        document.getElementById('initial_pengirim_suratMasuk').value = data.pengirim_suratMasuk || '';
        document.getElementById('initial_penerima_suratMasuk').value = data.penerima_suratMasuk || '';
        document.getElementById('initial_isi_suratMasuk').value = data.isi_suratMasuk || '';

        // Isi form
        document.getElementById('filename').value = data.filename;
        document.getElementById('full_letter_number').value = data.full_letter_number || '';
        document.getElementById('pengirim_suratMasuk').value = data.pengirim_suratMasuk || '';
        document.getElementById('penerima_suratMasuk').value = data.penerima_suratMasuk || '';
        document.getElementById('kodesurat2').value = data.kodesurat2 || '';
        document.getElementById('jenis_surat').value = data.jenis_surat || '';
        document.getElementById('isi_suratMasuk').value = data.isi_suratMasuk || '';

        // Isi opsi tanggal
        const dateSelect = document.getElementById('selected_date');
        dateSelect.innerHTML = '<option value="">Pilih tanggal</option>';
        if (data.dates && data.dates.length > 0) {
            data.dates.forEach((date) => {
                const option = document.createElement('option');
                option.value = date;
                option.textContent = date;
                dateSelect.appendChild(option);
            });
            // Pilih tanggal pertama secara default
            dateSelect.options[1].selected = true;
        }

        $('#dataModal').modal('show');
    }

    function nextModal() {
        if (currentIndex < extractedDataList.length - 1) {
            openModal(currentIndex + 1);
        } else {
            alert("Tidak ada entri lagi untuk diproses.");
        }
    }

    function previousModal() {
        if (currentIndex > 0) {
            openModal(currentIndex - 1);
        } else {
            alert("Sudah di entri pertama.");
        }
    }

    function saveData() {
        const saveButton = document.getElementById('saveButton');
        const originalButtonText = saveButton.innerHTML;
        saveButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';
        saveButton.disabled = true;

        const formData = {
            filename: document.getElementById('filename').value,
            initial_full_letter_number: document.getElementById('initial_full_letter_number').value,
            initial_pengirim_suratMasuk: document.getElementById('initial_pengirim_suratMasuk').value,
            initial_penerima_suratMasuk: document.getElementById('initial_penerima_suratMasuk').value,
            initial_isi_suratMasuk: document.getElementById('initial_isi_suratMasuk').value,
            full_letter_number: document.getElementById('full_letter_number').value.trim(),
            pengirim_suratMasuk: document.getElementById('pengirim_suratMasuk').value.trim(),
            penerima_suratMasuk: document.getElementById('penerima_suratMasuk').value.trim(),
            selected_date: document.getElementById('selected_date').value.trim(),
            kodesurat2: document.getElementById('kodesurat2').value.trim(),
            jenis_surat: document.getElementById('jenis_surat').value.trim(),
            isi_suratMasuk: document.getElementById('isi_suratMasuk').value.trim()
        };

        // Validasi field wajib
        const requiredFields = {
            "Nomor Surat Lengkap": formData.full_letter_number,
            "Pengirim": formData.pengirim_suratMasuk,
            "Penerima": formData.penerima_suratMasuk,
            "Isi": formData.isi_suratMasuk,
            "Tanggal Surat": formData.selected_date
        };
        
        const missingFields = [];
        for (const [fieldName, value] of Object.entries(requiredFields)) {
            if (!value) {
                missingFields.push(fieldName);
            }
        }
        
        if (missingFields.length > 0) {
            alert(`Harap isi semua field wajib:\n- ${missingFields.join('\n- ')}`);
            saveButton.innerHTML = originalButtonText;
            saveButton.disabled = false;
            return;
        }

    fetch(ocrEndpoint, {
            method: "POST",
            headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrfToken
            },
        body: JSON.stringify(formData),
        })
        .then(response => {
            // Tanggapan mungkin bukan JSON (misal: error 500)
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                return response.json();
            } else {
                return response.text().then(text => {
                    // Periksa apakah respons adalah halaman login (session habis)
                    if (text.includes("login")) {
                        return { 
                            success: false, 
                            error: "Sesi Anda telah habis. Silakan login kembali." 
                        };
                    }
                    throw new Error(text || "Respons tidak valid dari server");
                });
            }
        })
        .then(data => {
            console.log("Server response:", data);
            if (data.success) {
                // Auto navigate to next entry
                if (currentIndex < extractedDataList.length - 1) {
                    openModal(currentIndex + 1);
                } else {
                    $('#dataModal').modal('hide');
                    alert('Semua data berhasil disimpan!');
                    // Optional: reload the page to reset the state
                    window.location.reload();
                }
            } else {
                // Tampilkan error spesifik dari server jika ada
                const errorMsg = data.error || "Kesalahan tidak diketahui";
                alert(`Gagal menyimpan data: ${errorMsg}`);
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert(`Terjadi kesalahan: ${error.message || error}`);
        })
        .finally(() => {
            saveButton.innerHTML = originalButtonText;
            saveButton.disabled = false;
        });
    }

    // Fungsi zoom gambar
    let scale = 1;
    let originX = 0;
    let originY = 0;
    let startX, startY;
    let isDragging = false;

    const image = document.getElementById("modal-image");
    const imageContainer = document.querySelector(".image-container");

if (imageContainer) {
    imageContainer.addEventListener("wheel", function (e) {
        e.preventDefault();
        const scaleAmount = 0.1;
        const rect = imageContainer.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        if (e.deltaY < 0) {
            scale += scaleAmount;
        } else {
            scale = Math.max(scale - scaleAmount, 0.1);
        }
        
        // Sesuaikan origin untuk zoom di posisi kursor
        originX = mouseX - (mouseX - originX) * (scale / (scale - scaleAmount));
        originY = mouseY - (mouseY - originY) * (scale / (scale - scaleAmount));
        
        updateTransform();
    });

    imageContainer.addEventListener("mousedown", function (e) {
        isDragging = true;
        startX = e.clientX - originX;
        startY = e.clientY - originY;
        imageContainer.style.cursor = "grabbing";
    });
}

    document.addEventListener("mousemove", function (e) {
        if (isDragging) {
            originX = e.clientX - startX;
            originY = e.clientY - startY;
            updateTransform();
        }
    });

    document.addEventListener("mouseup", function () {
        isDragging = false;
    if (imageContainer) {
        imageContainer.style.cursor = "grab";
    }
    });

    function updateTransform() {
    if (image) {
        image.style.transform = `translate(${originX}px, ${originY}px) scale(${scale})`;
    }
    }

    function resetZoom() {
        scale = 1;
        originX = 0;
        originY = 0;
        updateTransform();
    }

    function zoomIn() {
        scale += 0.2;
        updateTransform();
    }

    function zoomOut() {
        scale = Math.max(scale - 0.2, 0.5);
        updateTransform();
    }

// Comprehensive file upload debugging
function debugFileUpload(event) {
    console.log('=== File Upload Debug ===');
    console.log('Event type:', event.type);
    console.log('Target:', event.target);
    
    const fileInput = document.getElementById('fileInput');
    
    // Detailed input element inspection
    console.log('File Input Details:', {
        id: fileInput.id,
        name: fileInput.name,
        multiple: fileInput.multiple,
        accept: fileInput.accept,
        required: fileInput.required
    });

    // Browser compatibility check
    if (typeof FileList === 'undefined') {
        console.error('FileList not supported in this browser');
        alert('Browser tidak mendukung unggah file. Gunakan browser modern.');
        return;
    }

    // Check file selection methods
    console.log('Direct files access:', fileInput.files);
    
    // Alternative file retrieval
    const files = event.target.files || fileInput.files;
    console.log('Event files:', files);
    console.log('Files length:', files ? files.length : 'No files');

    if (!files || files.length === 0) {
        console.warn('No files selected');
        const selectedFilesText = document.getElementById('selectedFilesText');
        const fileValidationMessage = document.getElementById('fileValidationMessage');
        
        selectedFilesText.textContent = 'Tidak ada file dipilih';
        fileValidationMessage.classList.remove('hidden');
        fileValidationMessage.textContent = 'Harap pilih setidaknya satu file gambar';
        
        // Force file input click to ensure file selection dialog opens
        fileInput.click();
        return;
    }

    // Detailed file information
    Array.from(files).forEach((file, index) => {
        console.log(`File ${index + 1}:`, {
            name: file.name,
            type: file.type,
            size: file.size
        });
    });
}

// Modify existing event listeners to include debugging
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const manualUploadBtn = document.getElementById('manualUploadBtn');
    const selectedFilesText = document.getElementById('selectedFilesText');
    const fileValidationMessage = document.getElementById('fileValidationMessage');
    const ocrForm = document.getElementById('ocr-form');

    // Add debug logging to file input
    fileInput.addEventListener('change', function(event) {
        console.log('File input change event triggered');
        debugFileUpload(event);
        updateFileSelection(event);
    });

    // Manual upload button debugging
    manualUploadBtn.addEventListener('click', function() {
        console.log('Manual upload button clicked');
        fileInput.click();
    });

    // Form submission debugging
    ocrForm.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('Form submission prevented');
        
        const files = fileInput.files;
        console.log('Form submission files:', files);
        
        if (!files || files.length === 0) {
            console.warn('No files selected on form submit');
            selectedFilesText.textContent = 'Tidak ada file dipilih';
            fileValidationMessage.classList.remove('hidden');
            fileValidationMessage.textContent = 'Harap pilih setidaknya satu file gambar';
            fileInput.click(); // Force file selection
            return;
        }

        // Existing form submission logic
        const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
        
        if (imageFiles.length === 0) {
            console.warn('No image files selected');
            selectedFilesText.textContent = 'Tidak ada file gambar dipilih';
            fileValidationMessage.classList.remove('hidden');
            fileValidationMessage.textContent = 'Harap pilih file gambar yang valid';
            fileInput.click(); // Force file selection
            return;
        }

        const formData = new FormData(ocrForm);
        
        // Ensure only image files are sent
        formData.delete('image');
        imageFiles.forEach(file => {
            formData.append('image', file);
            console.log('Appending file:', file.name);
        });

        fetch(ocrForm.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            console.log('Fetch response:', response);
            if (response.redirected) {
                window.location.href = response.url;
                return null;
            } else {
                return response.text();
            }
        })
        .then(data => {
            if (data) {
                console.log('Server response:', data);
                alert(data || 'Berhasil mengunggah file');
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            alert('Terjadi kesalahan saat mengunggah file: ' + error.message);
        });
    });
});

// Function to update file selection
function updateFileSelection(event) {
    console.log('=== File Selection Debug ===');
    console.log('Event:', event);
    
    const fileInput = document.getElementById('fileInput');
    const selectedFilesText = document.getElementById('selectedFilesText');
    const fileValidationMessage = document.getElementById('fileValidationMessage');
    
    console.log('File Input:', fileInput);
    console.log('File Input Properties:', {
        id: fileInput.id,
        name: fileInput.name,
        multiple: fileInput.multiple,
        accept: fileInput.accept,
        files: fileInput.files
    });
    
    // Validate files
    const maxFiles = parseInt(fileInput.dataset.maxFiles || '10', 10);
    const allowedTypes = (fileInput.dataset.allowedTypes || 'image/*').split(',');
    
    const files = fileInput.files;
    console.log('Files:', files);
    
    if (!files || files.length === 0) {
        console.warn('No files selected');
        selectedFilesText.textContent = 'Belum ada file dipilih';
        fileValidationMessage.classList.remove('hidden');
        fileValidationMessage.textContent = 'Harap pilih setidaknya satu file';
        return;
    }
    
    if (files.length > maxFiles) {
        console.warn(`Too many files. Max: ${maxFiles}, Selected: ${files.length}`);
        fileValidationMessage.classList.remove('hidden');
        fileValidationMessage.textContent = `Maksimal ${maxFiles} file yang dapat diunggah`;
        fileInput.value = ''; // Reset file input
        selectedFilesText.textContent = 'Belum ada file dipilih';
        return;
    }
    
    // Filter image files
    const imageFiles = Array.from(files).filter(file => 
        allowedTypes.some(type => 
            type === '*' || file.type.startsWith(type.replace('*', ''))
        )
    );
    
    console.log('Image Files:', imageFiles);
    
    if (imageFiles.length === 0) {
        console.warn('No valid image files');
        selectedFilesText.textContent = 'Belum ada file dipilih';
        fileValidationMessage.classList.remove('hidden');
        fileValidationMessage.textContent = 'Harap pilih file gambar yang valid';
        fileInput.value = ''; // Reset file input
        return;
    }
    
    // Update file input with only valid image files
    const dataTransfer = new DataTransfer();
    imageFiles.forEach(file => dataTransfer.items.add(file));
    fileInput.files = dataTransfer.files;
    
    // Update UI
    const fileNames = imageFiles.map(file => file.name);
    selectedFilesText.textContent = `Dipilih: ${fileNames.join(', ')}`;
    fileValidationMessage.classList.add('hidden');
    
    console.log('File selection complete');
}

document.querySelector('form').addEventListener('submit', function(e) {
    const fileInput = document.getElementById('file-input');
    if (fileInput.files.length === 0) {
        e.preventDefault();
        alert('Please select at least one file');
        return false;
    }
    
    // Additional validation if needed
    return true;
});

// Add this to your JavaScript
console.log("Form submission intercepted");
const formData = new FormData(document.querySelector('form'));
for (let [key, value] of formData.entries()) {
    console.log(key, value);
}

// Comprehensive File Upload Handling
document.addEventListener('DOMContentLoaded', function() {
    console.log('OCR Surat Masuk Page Loaded');

    // Get all relevant elements
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const selectFileBtn = document.getElementById('selectFileBtn');
    const filePreview = document.getElementById('filePreview');
    const selectedFilesText = document.getElementById('selectedFiles');
    const uploadForm = document.getElementById('uploadForm');

    // Debug: Log element existence
    console.log('Dropzone Element:', dropzone ? 'Found' : 'Not Found');
    console.log('File Input Element:', fileInput ? 'Found' : 'Not Found');
    console.log('Select File Button:', selectFileBtn ? 'Found' : 'Not Found');

    // Comprehensive button click handler
    function setupFileSelectionButton() {
        if (!selectFileBtn) {
            console.error('Select File Button not found!');
            return;
        }

        if (!fileInput) {
            console.error('File Input not found!');
            return;
        }

        // Remove any existing event listeners to prevent multiple bindings
        selectFileBtn.removeEventListener('click', fileSelectionHandler);
        selectFileBtn.addEventListener('click', fileSelectionHandler);

        console.log('File Selection Button Event Listener Added');
    }

    function fileSelectionHandler(event) {
        console.log('Select File Button Clicked');
        
        // Prevent default button behavior
        event.preventDefault();
        event.stopPropagation();

        // Trigger file input click
        if (fileInput) {
            console.log('Triggering File Input Click');
            fileInput.click();
        } else {
            console.error('File Input Element Not Found!');
            alert('Terjadi kesalahan: Elemen input file tidak ditemukan');
        }
    }

    // File Input Change Handler
    function fileInputChangeHandler(event) {
        console.log('File Input Changed');
        const files = event.target.files;
        
        console.log(`Number of files selected: ${files.length}`);
        
        if (files.length > 0) {
            const fileNames = Array.from(files).map(file => file.name);
            console.log('Selected Files:', fileNames);
            
            if (selectedFilesText) {
                selectedFilesText.textContent = `Dipilih: ${fileNames.join(', ')}`;
                filePreview.classList.remove('hidden');
            }
        }
    }

    // Setup event listeners
    if (fileInput) {
        fileInput.addEventListener('change', fileInputChangeHandler);
    }

    // Initial setup
    setupFileSelectionButton();

    // Optional: Fallback error handling
    window.addEventListener('error', function(event) {
        console.error('Unhandled Error:', event.error);
        alert('Terjadi kesalahan tidak terduga. Silakan refresh halaman.');
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Debugging function
    function debugLog(message) {
        console.log(`[OCR File Upload Debug] ${message}`);
    }

    // Get all critical elements
    const fileInput = document.getElementById('fileInput');
    const selectFileBtn = document.getElementById('selectFileBtn');
    const filePreview = document.getElementById('filePreview');
    const selectedFilesText = document.getElementById('selectedFiles');

    // Validate critical elements
    if (!fileInput) {
        debugLog('❌ File Input Element Not Found!');
        return;
    }

    if (!selectFileBtn) {
        debugLog('❌ Select File Button Not Found!');
        return;
    }

    // Direct file input click handler
    function triggerFileInput(event) {
        event.preventDefault();
        event.stopPropagation();
        
        debugLog('🔍 Select File Button Clicked');
        fileInput.click();
    }

    // File selection change handler
    function handleFileSelection(event) {
        const files = event.target.files;
        
        debugLog(`📂 Files Selected: ${files.length}`);
        
        if (files.length > 0) {
            const fileNames = Array.from(files)
                .map(file => file.name)
                .join(', ');
            
            debugLog(`📄 Selected Files: ${fileNames}`);
            
            // Update file preview
            if (selectedFilesText) {
                selectedFilesText.textContent = `Dipilih: ${fileNames}`;
                filePreview.classList.remove('hidden');
            }
        }
    }

    // Attach event listeners
    selectFileBtn.addEventListener('click', triggerFileInput);
    fileInput.addEventListener('change', handleFileSelection);

    // Additional debugging
    debugLog('✅ File Upload Script Initialized Successfully');
});

// Safe Element Selection and Error Handling
document.addEventListener('DOMContentLoaded', function() {
    // Debugging and Error Logging Function
    function safeLog(message, type = 'log') {
        const prefix = '[OCR Surat Masuk Debug]';
        console[type](`${prefix} ${message}`);
    }

    // Safe Element Selection
    function $(selector) {
        const element = document.querySelector(selector);
        if (!element) {
            safeLog(`Element not found: ${selector}`, 'warn');
        }
        return element;
    }

    // Safe Data Attribute Retrieval
    function getDataAttribute(selector, attribute, defaultValue = '') {
        const element = $(selector);
        return element ? element.dataset[attribute] || defaultValue : defaultValue;
    }

    // Safe Event Listener Attachment
    function safeAddEventListener(selector, event, handler) {
        const element = $(selector);
        if (element) {
            element.addEventListener(event, handler);
        } else {
            safeLog(`Cannot attach ${event} event to ${selector}`, 'warn');
        }
    }

    // Retrieve Base URLs and Endpoints Safely
    const suratMasukImageBaseUrl = getDataAttribute('#ocr-form', 'suratMasukImageUrl', '');
    const staticImageBaseUrl = getDataAttribute('#ocr-form', 'staticImageUrl', '');
    const ocrEndpoint = getDataAttribute('#ocr-form', 'ocrEndpoint', '');

    // Safe CSRF Token Retrieval
    const csrfToken = $('meta[name="csrf-token"]')?.getAttribute('content') || '';

    // File Upload Debugging and Handling
    function setupFileUpload() {
        const fileInput = $('#fileInput');
        const selectFileBtn = $('#selectFileBtn');
        const filePreview = $('#filePreview');
        const selectedFilesText = $('#selectedFiles');

        if (!fileInput || !selectFileBtn || !filePreview || !selectedFilesText) {
            safeLog('One or more file upload elements are missing', 'error');
            return;
        }

        // File Selection Handler
        function handleFileSelection(event) {
            const files = event.target.files;
            
            if (files.length > 0) {
                const fileNames = Array.from(files)
                    .map(file => file.name)
                    .join(', ');
                
                safeLog(`Files Selected: ${fileNames}`);
                
                selectedFilesText.textContent = `Dipilih: ${fileNames}`;
                filePreview.classList.remove('hidden');
            }
        }

        // Trigger File Input
        function triggerFileInput(event) {
            event.preventDefault();
            fileInput.click();
        }

        // Attach Event Listeners
        selectFileBtn.addEventListener('click', triggerFileInput);
        fileInput.addEventListener('change', handleFileSelection);

        safeLog('File Upload Setup Complete');
    }

    // Initialize File Upload
    setupFileUpload();

    // Prevent Undefined Sidebar Errors
    try {
        // If sidebar exists, do something
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            // Optional: Add sidebar-specific logic
            safeLog('Sidebar found');
        }
    } catch (error) {
        safeLog('Sidebar initialization error', 'error');
    }

    // Optional: Global Error Handling
    window.addEventListener('error', function(event) {
        safeLog(`Unhandled Error: ${event.message}`, 'error');
    });
});

// Modal Close Button Handling
document.addEventListener('DOMContentLoaded', function() {
    // Safe Element Selection Function
    function $(selector) {
        const element = document.querySelector(selector);
        if (!element) {
            console.warn(`[OCR Modal] Element not found: ${selector}`);
        }
        return element;
    }

    // Modal Close Functionality
    function setupModalClose() {
        const closeModalBtn = $('#closeModalBtn');
        const extractedDataModal = $('#extractedDataModal');

        if (!closeModalBtn || !extractedDataModal) {
            console.warn('[OCR Modal] Close button or modal not found');
            return;
        }

        // Close modal when close button is clicked
        closeModalBtn.addEventListener('click', function() {
            console.log('[OCR Modal] Close button clicked');
            extractedDataModal.classList.add('hidden');
        });

        // Optional: Close modal when clicking outside
        extractedDataModal.addEventListener('click', function(event) {
            if (event.target === extractedDataModal) {
                console.log('[OCR Modal] Background clicked, closing modal');
                extractedDataModal.classList.add('hidden');
            }
        });

        // Optional: Close modal with Escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && !extractedDataModal.classList.contains('hidden')) {
                console.log('[OCR Modal] Escape key pressed, closing modal');
                extractedDataModal.classList.add('hidden');
            }
        });
    }

    // Initialize Modal Close Functionality
    setupModalClose();
});
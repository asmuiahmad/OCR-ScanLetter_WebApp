/**
 * Common OCR functionality
 * Shared functions for OCR pages
 */

function updateFileName(input) {
    const file = input.files[0];
    const fileNameDisplay = document.getElementById('file-name');
    if (file && fileNameDisplay) {
        fileNameDisplay.textContent = file.name;
    }
}

// Drag and drop functionality
function initializeDragDrop(dropZoneId) {
    const dropZone = document.getElementById(dropZoneId);
    if (!dropZone) return;

    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const fileInput = dropZone.querySelector('input[type="file"]');
            if (fileInput) {
                fileInput.files = files;
                updateFileName(fileInput);
            }
        }
    });
}
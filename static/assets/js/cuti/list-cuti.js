/**
 * Cuti List Management JavaScript
 * Handles cuti approval, rejection, and detail viewing
 */

let currentCutiId = null;

/**
 * View detail of a specific cuti
 * @param {number} cutiId - The ID of the cuti to view
 */
function viewDetail(cutiId) {
    // Show loading state
    const detailContent = document.getElementById('detailContent');
    if (detailContent) {
        detailContent.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Memuat detail...</div>';
    }
    
    // Show modal immediately
    const detailModal = document.getElementById('detailModal');
    if (detailModal) {
        $(detailModal).modal('show');
    }
    
    // Load detail cuti via AJAX
    fetch(`/cuti/detail/${cutiId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const cuti = data.cuti;
                const content = generateDetailContent(cuti);
                if (detailContent) {
                    detailContent.innerHTML = content;
                }
            } else {
                throw new Error(data.message || 'Failed to load detail');
            }
        })
        .catch(error => {
            console.error('Error loading detail:', error);
            if (detailContent) {
                detailContent.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i> 
                        Terjadi kesalahan saat memuat detail: ${error.message}
                    </div>
                `;
            }
        });
}

/**
 * Generate HTML content for cuti detail
 * @param {Object} cuti - Cuti data object
 * @returns {string} HTML content
 */
function generateDetailContent(cuti) {
    const statusBadgeClass = getStatusBadgeClass(cuti.status_cuti);
    
    return `
        <div class="row">
            <div class="col-md-6">
                <h6><strong>Data Pegawai</strong></h6>
                <table class="table table-sm">
                    <tr><td>Nama</td><td>: ${escapeHtml(cuti.nama || '-')}</td></tr>
                    <tr><td>NIP</td><td>: ${escapeHtml(cuti.nip || '-')}</td></tr>
                    <tr><td>Jabatan</td><td>: ${escapeHtml(cuti.jabatan || '-')}</td></tr>
                    <tr><td>Gol/Ruang</td><td>: ${escapeHtml(cuti.gol_ruang || '-')}</td></tr>
                    <tr><td>Unit Kerja</td><td>: ${escapeHtml(cuti.unit_kerja || '-')}</td></tr>
                    <tr><td>Masa Kerja</td><td>: ${escapeHtml(cuti.masa_kerja || '-')}</td></tr>
                    <tr><td>Alamat</td><td>: ${escapeHtml(cuti.alamat || '-')}</td></tr>
                    <tr><td>Telepon</td><td>: ${escapeHtml(cuti.telp || '-')}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6><strong>Data Cuti</strong></h6>
                <table class="table table-sm">
                    <tr><td>Jenis Cuti</td><td>: ${escapeHtml(cuti.jenis_cuti || '-')}</td></tr>
                    <tr><td>Alasan</td><td>: ${escapeHtml(cuti.alasan_cuti || '-')}</td></tr>
                    <tr><td>Lama Cuti</td><td>: ${escapeHtml(cuti.lama_cuti || '-')}</td></tr>
                    <tr><td>Tanggal Mulai</td><td>: ${escapeHtml(cuti.tanggal_cuti || '-')}</td></tr>
                    <tr><td>Tanggal Selesai</td><td>: ${escapeHtml(cuti.sampai_cuti || '-')}</td></tr>
                    <tr><td>Status</td><td>: <span class="badge ${statusBadgeClass}">${getStatusText(cuti.status_cuti)}</span></td></tr>
                    ${cuti.approved_by ? `<tr><td>Disetujui oleh</td><td>: ${escapeHtml(cuti.approved_by)}</td></tr>` : ''}
                    ${cuti.approved_at ? `<tr><td>Tanggal Persetujuan</td><td>: ${escapeHtml(cuti.approved_at)}</td></tr>` : ''}
                    ${cuti.notes ? `<tr><td>Catatan</td><td>: ${escapeHtml(cuti.notes)}</td></tr>` : ''}
                </table>
            </div>
        </div>
    `;
}

/**
 * Get status badge CSS class
 * @param {string} status - Status value
 * @returns {string} CSS class
 */
function getStatusBadgeClass(status) {
    switch (status) {
        case 'approved': return 'badge-success';
        case 'rejected': return 'badge-danger';
        case 'pending':
        default: return 'badge-warning';
    }
}

/**
 * Get status display text
 * @param {string} status - Status value
 * @returns {string} Display text
 */
function getStatusText(status) {
    switch (status) {
        case 'approved': return 'Disetujui';
        case 'rejected': return 'Ditolak';
        case 'pending': return 'Menunggu Persetujuan';
        default: return status || 'Unknown';
    }
}

/**
 * Approve cuti
 * @param {number} cutiId - The ID of the cuti to approve
 */
function approveCuti(cutiId) {
    currentCutiId = cutiId;
    // Clear previous notes
    const notesField = document.getElementById('notes');
    if (notesField) {
        notesField.value = '';
    }
    $('#approvalModal').modal('show');
}

/**
 * Reject cuti
 * @param {number} cutiId - The ID of the cuti to reject
 */
function rejectCuti(cutiId) {
    currentCutiId = cutiId;
    // Clear previous notes
    const rejectNotesField = document.getElementById('rejectNotes');
    if (rejectNotesField) {
        rejectNotesField.value = '';
    }
    $('#rejectionModal').modal('show');
}

/**
 * Show QR code for digital signature verification
 * @param {string} signatureHash - The signature hash
 */
function showQRCode(signatureHash) {
    const qrHashElement = document.getElementById('qrHash');
    if (qrHashElement) {
        qrHashElement.textContent = signatureHash;
    }
    
    // Generate QR code URL for verification
    const verifyUrl = `${window.location.origin}/cuti/verify/${signatureHash}`;
    
    // Create QR code using a simple QR code generator
    const qrContainer = document.getElementById('qrCodeContainer');
    if (qrContainer) {
        qrContainer.innerHTML = `
            <div class="qr-container">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(verifyUrl)}" 
                     alt="QR Code" class="img-fluid" 
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzM3NDE1MSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkVycm9yIGxvYWRpbmcgUVI8L3RleHQ+PC9zdmc+'">
                <p class="mt-2"><small>URL Verifikasi: <a href="${verifyUrl}" target="_blank">${verifyUrl}</a></small></p>
            </div>
        `;
    }
    
    $('#qrModal').modal('show');
}

/**
 * Handle cuti approval confirmation
 */
function handleApprovalConfirmation() {
    const notesField = document.getElementById('notes');
    const notes = notesField ? notesField.value : '';
    
    if (!currentCutiId) {
        showAlert('Error: ID cuti tidak valid', 'danger');
        return;
    }
    
    // Show loading state
    const confirmButton = document.getElementById('confirmApprove');
    if (confirmButton) {
        confirmButton.disabled = true;
        confirmButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Memproses...';
    }
    
    fetch(`/cuti/approve/${currentCutiId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ notes: notes })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showAlert('Cuti berhasil disetujui dengan tanda tangan digital!', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            throw new Error(data.message || 'Gagal menyetujui cuti');
        }
    })
    .catch(error => {
        console.error('Error approving cuti:', error);
        showAlert(`Terjadi kesalahan: ${error.message}`, 'danger');
    })
    .finally(() => {
        // Reset button state
        if (confirmButton) {
            confirmButton.disabled = false;
            confirmButton.innerHTML = 'Setujui Cuti';
        }
    });
    
    $('#approvalModal').modal('hide');
}

/**
 * Handle cuti rejection confirmation
 */
function handleRejectionConfirmation() {
    const rejectNotesField = document.getElementById('rejectNotes');
    const notes = rejectNotesField ? rejectNotesField.value : '';
    
    if (!notes.trim()) {
        showAlert('Alasan penolakan harus diisi', 'warning');
        return;
    }
    
    if (!currentCutiId) {
        showAlert('Error: ID cuti tidak valid', 'danger');
        return;
    }
    
    // Show loading state
    const confirmButton = document.getElementById('confirmReject');
    if (confirmButton) {
        confirmButton.disabled = true;
        confirmButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Memproses...';
    }
    
    fetch(`/cuti/reject/${currentCutiId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ notes: notes })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showAlert('Cuti berhasil ditolak', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            throw new Error(data.message || 'Gagal menolak cuti');
        }
    })
    .catch(error => {
        console.error('Error rejecting cuti:', error);
        showAlert(`Terjadi kesalahan: ${error.message}`, 'danger');
    })
    .finally(() => {
        // Reset button state
        if (confirmButton) {
            confirmButton.disabled = false;
            confirmButton.innerHTML = 'Tolak Cuti';
        }
    });
    
    $('#rejectionModal').modal('hide');
}

/**
 * Get CSRF token from meta tag
 * @returns {string} CSRF token
 */
function getCsrfToken() {
    const metaTag = document.querySelector('meta[name=csrf-token]');
    return metaTag ? metaTag.getAttribute('content') : '';
}

/**
 * Show alert message
 * @param {string} message - Alert message
 * @param {string} type - Alert type (success, danger, warning, info)
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
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Initialize event listeners when DOM is ready
 */
function initializeCutiList() {
    // Approval confirmation
    const confirmApproveBtn = document.getElementById('confirmApprove');
    if (confirmApproveBtn) {
        confirmApproveBtn.addEventListener('click', handleApprovalConfirmation);
    }
    
    // Rejection confirmation
    const confirmRejectBtn = document.getElementById('confirmReject');
    if (confirmRejectBtn) {
        confirmRejectBtn.addEventListener('click', handleRejectionConfirmation);
    }
    
    console.log('Cuti list functionality initialized');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeCutiList);

// Export functions for global access
window.cutiList = {
    viewDetail,
    approveCuti,
    rejectCuti,
    showQRCode
};
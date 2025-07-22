/**
 * Cuti Management JavaScript
 * Handles cuti approval and management functions
 */

let currentCutiId = null;

function approveCuti(id) {
    if (confirm('Apakah Anda yakin ingin menyetujui cuti ini?')) {
        currentCutiId = id;
        // Add your approval logic here
        fetch(`/cuti/approve/${id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toast.success('Cuti berhasil disetujui!');
                location.reload();
            } else {
                window.toast.error(data.message || 'Gagal menyetujui cuti!');
            }
        })
        .catch(error => {
            window.toast.error('Terjadi kesalahan saat menyetujui cuti!');
        });
    }
}

function rejectCuti(id) {
    if (confirm('Apakah Anda yakin ingin menolak cuti ini?')) {
        currentCutiId = id;
        // Add your rejection logic here
        fetch(`/cuti/reject/${id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toast.success('Cuti berhasil ditolak!');
                location.reload();
            } else {
                window.toast.error(data.message || 'Gagal menolak cuti!');
            }
        })
        .catch(error => {
            window.toast.error('Terjadi kesalahan saat menolak cuti!');
        });
    }
}
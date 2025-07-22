/**
 * Modal Utility Functions
 * Common modal functions used across the application
 */

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
        document.body.style.overflow = 'auto';
    }
}

function openEditModal(userId, userEmail) {
    const modal = document.getElementById('editModal');
    if (modal) {
        // Populate modal with user data
        const userIdInput = modal.querySelector('#edit_user_id');
        const userEmailInput = modal.querySelector('#edit_user_email');
        
        if (userIdInput) userIdInput.value = userId;
        if (userEmailInput) userEmailInput.value = userEmail;
        
        openModal('editModal');
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
        e.target.classList.remove('show');
        document.body.style.overflow = 'auto';
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            modal.style.display = 'none';
            modal.classList.remove('show');
            document.body.style.overflow = 'auto';
        });
    }
});
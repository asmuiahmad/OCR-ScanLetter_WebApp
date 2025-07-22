/**
 * Form Input Surat JavaScript
 * Handles date initialization for surat input forms
 */
document.addEventListener('DOMContentLoaded', function() {
    const today = new Date().toISOString().split('T')[0];
    
    // Set today's date for all empty date inputs
    document.querySelectorAll('input[type="date"]').forEach(input => {
        if (!input.value) {
            input.value = today;
        }
    });
});
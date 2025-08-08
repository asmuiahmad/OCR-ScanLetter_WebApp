/**
 * Authentication JavaScript functionality
 * Handles password visibility toggle and password matching
 */

/**
 * Toggle password visibility
 * @param {string} inputId - ID of the password input field
 * @param {HTMLElement} button - Toggle button element
 */
function togglePassword(inputId, button) {
    const passwordInput = document.getElementById(inputId);
    const eyeIcon = button.querySelector('.eye-icon');
    const eyeOffIcon = button.querySelector('.eye-off-icon');
    
    if (!passwordInput || !eyeIcon || !eyeOffIcon) {
        console.error('Password toggle elements not found');
        return;
    }
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        eyeIcon.style.display = 'none';
        eyeOffIcon.style.display = 'block';
        button.setAttribute('aria-label', 'Hide password');
    } else {
        passwordInput.type = 'password';
        eyeIcon.style.display = 'block';
        eyeOffIcon.style.display = 'none';
        button.setAttribute('aria-label', 'Show password');
    }
}

/**
 * Check if passwords match (for registration form)
 */
function checkPasswordMatch() {
    const password = document.getElementById('registerPassword');
    const confirmPassword = document.getElementById('confirmPassword');
    const registerButton = document.getElementById('registerButton');
    const messageDiv = document.getElementById('passwordMatchMessage');
    
    if (!password || !confirmPassword || !registerButton || !messageDiv) {
        return; // Elements not found, probably not on register page
    }
    
    const passwordValue = password.value;
    const confirmPasswordValue = confirmPassword.value;
    
    // Check if both fields have values
    if (passwordValue === '' && confirmPasswordValue === '') {
        hidePasswordMessage(messageDiv);
        registerButton.disabled = true;
        return;
    }
    
    // Check if confirm password field has value
    if (confirmPasswordValue === '') {
        hidePasswordMessage(messageDiv);
        registerButton.disabled = true;
        return;
    }
    
    // Check password length and if passwords match
    if (passwordValue.length >= 6 && passwordValue === confirmPasswordValue) {
        showPasswordMessage(messageDiv, '✓ Passwords match', 'match');
        registerButton.disabled = false;
        
        // Auto-hide message after 4 seconds
        setTimeout(function() {
            fadeOutMessage(messageDiv);
        }, 4000);
    } else if (passwordValue.length < 6) {
        showPasswordMessage(messageDiv, '⚠ Password must be at least 6 characters', 'no-match');
        registerButton.disabled = true;
    } else {
        showPasswordMessage(messageDiv, '✗ Passwords do not match', 'no-match');
        registerButton.disabled = true;
    }
}

/**
 * Show password match message
 * @param {HTMLElement} messageDiv - Message container element
 * @param {string} message - Message text
 * @param {string} type - Message type ('match' or 'no-match')
 */
function showPasswordMessage(messageDiv, message, type) {
    messageDiv.textContent = message;
    messageDiv.className = `password-match-message ${type}`;
    messageDiv.style.display = 'block';
    messageDiv.style.opacity = '1';
}

/**
 * Hide password match message
 * @param {HTMLElement} messageDiv - Message container element
 */
function hidePasswordMessage(messageDiv) {
    messageDiv.style.display = 'none';
    messageDiv.style.opacity = '1';
}

/**
 * Fade out password message
 * @param {HTMLElement} messageDiv - Message container element
 */
function fadeOutMessage(messageDiv) {
    messageDiv.style.opacity = '0';
    setTimeout(function() {
        messageDiv.style.display = 'none';
        messageDiv.style.opacity = '1';
    }, 300);
}

/**
 * Store current page URL in sessionStorage for redirect after login
 */
function storeCurrentPageForRedirect() {
    // Don't store login/register pages
    if (window.location.pathname.includes('/login') || 
        window.location.pathname.includes('/register') ||
        window.location.pathname.includes('/logout')) {
        return;
    }
    
    // Store current URL for redirect after re-login
    sessionStorage.setItem('redirectAfterLogin', window.location.href);
}

/**
 * Handle session timeout detection and redirect
 */
function handleSessionTimeout() {
    // Check if we're being redirected to login due to timeout
    const urlParams = new URLSearchParams(window.location.search);
    const nextParam = urlParams.get('next');
    
    if (nextParam && window.location.pathname.includes('/login')) {
        // Store the intended destination
        sessionStorage.setItem('redirectAfterLogin', nextParam);
        
        // Show timeout message if not already shown
        const timeoutMessage = document.querySelector('.alert-info');
        if (!timeoutMessage) {
            showTimeoutMessage();
        }
    }
}

/**
 * Show session timeout message
 */
function showTimeoutMessage() {
    const loginContainer = document.querySelector('.login');
    if (!loginContainer) return;
    
    const existingAlert = loginContainer.querySelector('.timeout-alert');
    if (existingAlert) return; // Already shown
    
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning text-center timeout-alert';
    alertDiv.innerHTML = '<i class="fas fa-clock"></i> Sesi Anda telah berakhir. Silakan login kembali untuk melanjutkan.';
    
    const h1 = loginContainer.querySelector('h1');
    if (h1) {
        loginContainer.insertBefore(alertDiv, h1);
    }
}

/**
 * Handle redirect after successful login
 */
function handleLoginRedirect() {
    // Only run on login page
    if (!window.location.pathname.includes('/login')) {
        return;
    }
    
    // Check if we have a stored redirect URL from sessionStorage
    const storedRedirect = sessionStorage.getItem('redirectAfterLogin');
    const urlParams = new URLSearchParams(window.location.search);
    const nextParam = urlParams.get('next');
    
    // If we have a next parameter but no stored redirect, store it
    if (nextParam && !storedRedirect) {
        sessionStorage.setItem('redirectAfterLogin', nextParam);
    }
}

/**
 * Initialize authentication form functionality
 */
function initializeAuthForms() {
    // Add event listeners for password matching on registration form
    const registerPassword = document.getElementById('registerPassword');
    const confirmPassword = document.getElementById('confirmPassword');
    
    if (registerPassword && confirmPassword) {
        registerPassword.addEventListener('input', checkPasswordMatch);
        confirmPassword.addEventListener('input', checkPasswordMatch);
        
        // Initial check
        checkPasswordMatch();
    }
    
    // Add keyboard support for password toggle buttons
    const passwordToggleButtons = document.querySelectorAll('.password-toggle');
    passwordToggleButtons.forEach(button => {
        button.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                button.click();
            }
        });
        
        // Set initial aria-label
        button.setAttribute('aria-label', 'Show password');
    });
    
    // Form validation enhancement
    const authForms = document.querySelectorAll('.auth-form, form[action*="login"], form[action*="register"]');
    authForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = 'Processing...';
                
                // Re-enable button after 5 seconds as fallback
                setTimeout(() => {
                    submitButton.disabled = false;
                    submitButton.textContent = submitButton.dataset.originalText || 'Submit';
                }, 5000);
            }
        });
        
        // Store original button text
        const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitButton) {
            submitButton.dataset.originalText = submitButton.textContent;
        }
    });
    
    // Handle session timeout detection
    handleSessionTimeout();
    
    // Handle redirect after successful login
    handleLoginRedirect();
    
    console.log('Authentication forms initialized');
}

/**
 * Show form validation error
 * @param {string} message - Error message
 * @param {HTMLElement} container - Container to show error in
 */
function showFormError(message, container = null) {
    if (!container) {
        container = document.querySelector('.login-box, .auth-container');
    }
    
    if (!container) {
        alert(message);
        return;
    }
    
    // Remove existing error messages
    const existingErrors = container.querySelectorAll('.form-error');
    existingErrors.forEach(error => error.remove());
    
    // Create new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'form-error alert alert-error';
    errorDiv.textContent = message;
    
    // Insert at the beginning of the container
    container.insertBefore(errorDiv, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 5000);
}

/**
 * Show form success message
 * @param {string} message - Success message
 * @param {HTMLElement} container - Container to show message in
 */
function showFormSuccess(message, container = null) {
    if (!container) {
        container = document.querySelector('.login-box, .auth-container');
    }
    
    if (!container) {
        alert(message);
        return;
    }
    
    // Remove existing messages
    const existingMessages = container.querySelectorAll('.form-success, .form-error');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new success message
    const successDiv = document.createElement('div');
    successDiv.className = 'form-success alert alert-success';
    successDiv.textContent = message;
    
    // Insert at the beginning of the container
    container.insertBefore(successDiv, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (successDiv.parentNode) {
            successDiv.remove();
        }
    }, 5000);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeAuthForms);

// Export functions for global access
window.authUtils = {
    togglePassword,
    checkPasswordMatch,
    showFormError,
    showFormSuccess
};
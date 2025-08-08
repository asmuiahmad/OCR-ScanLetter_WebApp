/**
 * Session Management JavaScript
 * Handles session timeout detection and page redirect after re-login
 */

/**
 * Store current page URL for redirect after login
 */
function storeCurrentPageForRedirect() {
    // Don't store login/register/logout pages
    if (window.location.pathname.includes('/login') || 
        window.location.pathname.includes('/register') ||
        window.location.pathname.includes('/logout')) {
        return;
    }
    
    // Store current URL for redirect after re-login
    sessionStorage.setItem('lastVisitedPage', window.location.href);
    console.log('Stored last visited page:', window.location.href);
}

/**
 * Get stored page URL for redirect after login
 */
function getStoredPageForRedirect() {
    return sessionStorage.getItem('lastVisitedPage');
}

/**
 * Clear stored page URL
 */
function clearStoredPageForRedirect() {
    sessionStorage.removeItem('lastVisitedPage');
}

/**
 * Handle AJAX requests that might encounter session timeout
 */
function setupAjaxSessionHandler() {
    // Override XMLHttpRequest to detect session timeouts
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;
    
    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
        this._url = url;
        return originalOpen.apply(this, arguments);
    };
    
    XMLHttpRequest.prototype.send = function(data) {
        const xhr = this;
        const originalOnReadyStateChange = xhr.onreadystatechange;
        
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                // Check if response indicates session timeout (redirect to login)
                if (xhr.status === 401 || 
                    (xhr.status === 200 && xhr.responseURL && xhr.responseURL.includes('/login'))) {
                    
                    // Store current page before redirecting
                    storeCurrentPageForRedirect();
                    
                    // Redirect to login with next parameter
                    const currentUrl = encodeURIComponent(window.location.href);
                    window.location.href = `/login?next=${currentUrl}`;
                    return;
                }
            }
            
            if (originalOnReadyStateChange) {
                originalOnReadyStateChange.apply(xhr, arguments);
            }
        };
        
        return originalSend.apply(this, arguments);
    };
}

/**
 * Setup fetch API session handler
 */
function setupFetchSessionHandler() {
    const originalFetch = window.fetch;
    
    window.fetch = function(...args) {
        return originalFetch.apply(this, args)
            .then(response => {
                // Check if response indicates session timeout
                if (response.status === 401 || 
                    (response.url && response.url.includes('/login') && !args[0].includes('/login'))) {
                    
                    // Store current page before redirecting
                    storeCurrentPageForRedirect();
                    
                    // Redirect to login with next parameter
                    const currentUrl = encodeURIComponent(window.location.href);
                    window.location.href = `/login?next=${currentUrl}`;
                    return;
                }
                
                return response;
            })
            .catch(error => {
                console.error('Fetch error:', error);
                throw error;
            });
    };
}

/**
 * Setup form submission session handler
 */
function setupFormSessionHandler() {
    // Handle form submissions that might encounter session timeout
    document.addEventListener('submit', function(event) {
        const form = event.target;
        
        // Skip if it's the login form
        if (form.action && form.action.includes('/login')) {
            return;
        }
        
        // Store current page before form submission
        storeCurrentPageForRedirect();
    });
}

/**
 * Initialize session management
 */
function initializeSessionManager() {
    // Store current page on every page load (except auth pages)
    storeCurrentPageForRedirect();
    
    // Setup AJAX and fetch handlers for session timeout detection
    setupAjaxSessionHandler();
    setupFetchSessionHandler();
    setupFormSessionHandler();
    
    // Handle browser back/forward navigation
    window.addEventListener('popstate', function() {
        storeCurrentPageForRedirect();
    });
    
    // Store page before user navigates away
    window.addEventListener('beforeunload', function() {
        storeCurrentPageForRedirect();
    });
    
    console.log('Session manager initialized');
}

/**
 * Check if user should be redirected after successful login
 */
function handlePostLoginRedirect() {
    // Only run this on pages after successful login (not on login page itself)
    if (window.location.pathname.includes('/login')) {
        return;
    }
    
    const storedPage = getStoredPageForRedirect();
    const urlParams = new URLSearchParams(window.location.search);
    const fromLogin = urlParams.get('from_login');
    
    // If we just came from login and have a stored page, redirect there
    if (fromLogin === 'true' && storedPage && storedPage !== window.location.href) {
        console.log('Redirecting to stored page after login:', storedPage);
        clearStoredPageForRedirect();
        
        // Clean the URL by removing the from_login parameter
        const cleanUrl = new URL(window.location);
        cleanUrl.searchParams.delete('from_login');
        
        // Use replace to avoid adding to browser history
        window.history.replaceState({}, '', cleanUrl.toString());
        
        // Redirect to the stored page
        window.location.href = storedPage;
        return;
    }
    
    // Clean up the from_login parameter if present
    if (fromLogin === 'true') {
        const cleanUrl = new URL(window.location);
        cleanUrl.searchParams.delete('from_login');
        window.history.replaceState({}, '', cleanUrl.toString());
    }
    
    // Clear stored page if we're on a different page than expected
    if (storedPage && storedPage === window.location.href) {
        clearStoredPageForRedirect();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeSessionManager();
    handlePostLoginRedirect();
});

// Export functions for global access
window.sessionManager = {
    storeCurrentPageForRedirect,
    getStoredPageForRedirect,
    clearStoredPageForRedirect,
    handlePostLoginRedirect
};
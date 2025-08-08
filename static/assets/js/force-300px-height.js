/**
 * Force 300px Height JavaScript
 * Emergency script to ensure containers have 300px height
 */

function force300pxHeight() {
    // Find all log containers
    const logContainer = document.querySelector('.log-container');
    const loginLogsContainer = document.querySelector('.login-logs-container');
    const loginLogsById = document.getElementById('login-logs-container');
    
    const containers = [logContainer, loginLogsContainer, loginLogsById].filter(Boolean);
    
    containers.forEach((container) => {
        if (container) {
            // Clean force styles via JavaScript
            container.style.height = '300px';
            container.style.maxHeight = '300px';
            container.style.overflowY = 'auto';
            container.style.overflowX = 'hidden';
            
            // Remove any existing debug indicators
            const existingDebug = container.querySelectorAll('[data-debug="300px"]');
            existingDebug.forEach(debug => debug.remove());
        }
    });
}

// Run when DOM is ready
document.addEventListener('DOMContentLoaded', force300pxHeight);

// Run when window loads
window.addEventListener('load', force300pxHeight);

// Export for manual testing
window.force300pxHeight = force300pxHeight;
/**
 * Scrollbar Utilities
 * Enhances scrollable containers with visual indicators
 */

/**
 * Check if an element is scrollable and add appropriate classes
 * @param {HTMLElement} element - The element to check
 */
function checkScrollable(element) {
    if (!element) return;
    
    const isScrollable = element.scrollHeight > element.clientHeight;
    
    if (isScrollable) {
        element.classList.add('scrollable');
    } else {
        element.classList.remove('scrollable');
    }
}

/**
 * Initialize scrollbar utilities for log containers
 */
function initializeScrollbarUtils() {
    // Find all log containers
    const logContainers = [
        document.querySelector('.log-container'),
        document.querySelector('.login-logs-container'),
        document.querySelector('.recent-users-container'),
        document.querySelector('#activity-logs-container')
    ].filter(Boolean);
    
    // Check scrollable state for each container
    logContainers.forEach(container => {
        checkScrollable(container);
        
        // Add scroll event listener to update fade effects
        container.addEventListener('scroll', function() {
            updateScrollFadeEffects(this);
        });
        
        // Use ResizeObserver to detect content changes
        if (window.ResizeObserver) {
            const resizeObserver = new ResizeObserver(() => {
                checkScrollable(container);
            });
            resizeObserver.observe(container);
        }
        
        // Also check when content changes (for dynamic content)
        const mutationObserver = new MutationObserver(() => {
            setTimeout(() => checkScrollable(container), 100);
        });
        
        mutationObserver.observe(container, {
            childList: true,
            subtree: true
        });
    });
    
    console.log('Scrollbar utilities initialized for', logContainers.length, 'containers');
}

/**
 * Update fade effects based on scroll position
 * @param {HTMLElement} container - The scrollable container
 */
function updateScrollFadeEffects(container) {
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;
    const scrollBottom = scrollHeight - scrollTop - clientHeight;
    
    // Add classes based on scroll position
    container.classList.toggle('scrolled-top', scrollTop > 10);
    container.classList.toggle('scrolled-bottom', scrollBottom > 10);
}

/**
 * Smooth scroll to top of container
 * @param {string} containerId - ID of the container to scroll
 */
function scrollToTop(containerId) {
    const container = document.getElementById(containerId) || document.querySelector(containerId);
    if (container) {
        container.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }
}

/**
 * Smooth scroll to bottom of container
 * @param {string} containerId - ID of the container to scroll
 */
function scrollToBottom(containerId) {
    const container = document.getElementById(containerId) || document.querySelector(containerId);
    if (container) {
        container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeScrollbarUtils);

// Re-initialize when content is dynamically loaded
document.addEventListener('contentLoaded', initializeScrollbarUtils);

// Export functions for global access
window.scrollbarUtils = {
    checkScrollable,
    updateScrollFadeEffects,
    scrollToTop,
    scrollToBottom,
    initializeScrollbarUtils
};
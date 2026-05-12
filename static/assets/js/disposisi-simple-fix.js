/* Disposisi Menu - Clean Simple Fix */

console.log('🔧 Loading clean disposisi menu fix...');

// Simple fix - no floating buttons, no complex logic
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Applying clean disposisi fix...');
    
    // Find all disposisi links and make sure they work
    const disposisiLinks = document.querySelectorAll('a[href="/disposisi"], a[href*="disposisi"]');
    
    console.log(`Found ${disposisiLinks.length} disposisi links`);
    
    disposisiLinks.forEach((link, index) => {
        console.log(`Fixing disposisi link ${index + 1}:`, link);
        
        // Ensure it's clickable
        link.style.cursor = 'pointer';
        link.style.pointerEvents = 'auto';

        // Keep handler minimal; avoid forcing inline hover colors.
        link.addEventListener('click', function() {
            console.log('🖱️ Disposisi link clicked:', this.href);
        });
    });
    
    console.log('✅ Clean disposisi fix applied');
});

// Simple test function
window.testDisposisi = function() {
    const links = document.querySelectorAll('a[href="/disposisi"], a[href*="disposisi"]');
    console.log(`Found ${links.length} disposisi links`);
    
    if (links.length > 0) {
        console.log('Clicking first disposisi link...');
        links[0].click();
        return true;
    } else {
        console.error('No disposisi links found');
        return false;
    }
};

console.log('✅ Clean disposisi script loaded');
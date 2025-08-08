/**
 * Performance Monitor
 * Tracks loading times and optimization metrics
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.init();
    }
    
    init() {
        // Wait for page load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.measurePageLoad());
        } else {
            this.measurePageLoad();
        }
        
        // Measure resource loading
        this.measureResources();
        
        // Monitor modal performance
        this.monitorModal();
    }
    
    measurePageLoad() {
        if (!('performance' in window)) return;
        
        const navigation = performance.getEntriesByType('navigation')[0];
        if (!navigation) return;
        
        this.metrics.pageLoad = {
            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
            loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
            totalTime: navigation.loadEventEnd - navigation.navigationStart,
            dnsLookup: navigation.domainLookupEnd - navigation.domainLookupStart,
            tcpConnect: navigation.connectEnd - navigation.connectStart,
            serverResponse: navigation.responseEnd - navigation.requestStart,
            domProcessing: navigation.domComplete - navigation.domLoading
        };
        
        console.log('📊 Page Load Metrics:', this.metrics.pageLoad);
        
        // Log performance to console
        this.logPerformance();
    }
    
    measureResources() {
        if (!('performance' in window)) return;
        
        const resources = performance.getEntriesByType('resource');
        const cssResources = resources.filter(r => r.name.includes('.css'));
        const jsResources = resources.filter(r => r.name.includes('.js'));
        
        this.metrics.resources = {
            css: cssResources.map(r => ({
                name: r.name.split('/').pop(),
                duration: r.duration,
                size: r.transferSize || 0,
                cached: r.transferSize === 0
            })),
            js: jsResources.map(r => ({
                name: r.name.split('/').pop(),
                duration: r.duration,
                size: r.transferSize || 0,
                cached: r.transferSize === 0
            }))
        };
        
        console.log('📦 Resource Loading:', this.metrics.resources);
    }
    
    monitorModal() {
        const modal = document.getElementById('extractedDataModal');
        if (!modal) return;
        
        // Monitor modal show performance
        const originalShow = window.OCRModal?.show;
        if (originalShow) {
            window.OCRModal.show = function() {
                const startTime = performance.now();
                
                originalShow.call(this);
                
                requestAnimationFrame(() => {
                    const endTime = performance.now();
                    console.log(`🎭 Modal show time: ${(endTime - startTime).toFixed(2)}ms`);
                });
            };
        }
        
        // Monitor form submission performance
        const form = document.getElementById('extractedDataForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                const startTime = performance.now();
                
                // Monitor form processing time
                setTimeout(() => {
                    const endTime = performance.now();
                    console.log(`📝 Form processing time: ${(endTime - startTime).toFixed(2)}ms`);
                }, 0);
            });
        }
    }
    
    logPerformance() {
        const { pageLoad } = this.metrics;
        if (!pageLoad) return;
        
        console.group('🚀 Performance Summary');
        console.log(`⏱️ Total Load Time: ${pageLoad.totalTime.toFixed(2)}ms`);
        console.log(`🌐 DNS Lookup: ${pageLoad.dnsLookup.toFixed(2)}ms`);
        console.log(`🔗 TCP Connect: ${pageLoad.tcpConnect.toFixed(2)}ms`);
        console.log(`📡 Server Response: ${pageLoad.serverResponse.toFixed(2)}ms`);
        console.log(`🏗️ DOM Processing: ${pageLoad.domProcessing.toFixed(2)}ms`);
        console.log(`✅ DOM Ready: ${pageLoad.domContentLoaded.toFixed(2)}ms`);
        console.groupEnd();
        
        // Performance recommendations
        this.giveRecommendations();
    }
    
    giveRecommendations() {
        const { pageLoad, resources } = this.metrics;
        if (!pageLoad) return;
        
        console.group('💡 Performance Recommendations');
        
        if (pageLoad.totalTime > 3000) {
            console.warn('⚠️ Page load time is slow (>3s). Consider optimizing resources.');
        }
        
        if (pageLoad.serverResponse > 1000) {
            console.warn('⚠️ Server response is slow (>1s). Consider server optimization.');
        }
        
        if (resources?.css?.length > 5) {
            console.warn('⚠️ Many CSS files detected. Consider bundling.');
        }
        
        if (resources?.js?.length > 5) {
            console.warn('⚠️ Many JS files detected. Consider bundling.');
        }
        
        const uncachedResources = [
            ...(resources?.css || []),
            ...(resources?.js || [])
        ].filter(r => !r.cached);
        
        if (uncachedResources.length > 0) {
            console.log('📦 Uncached resources:', uncachedResources.map(r => r.name));
        }
        
        console.groupEnd();
    }
    
    // Method to get metrics for external use
    getMetrics() {
        return this.metrics;
    }
}

// Initialize performance monitoring
const perfMonitor = new PerformanceMonitor();

// Export for global access
window.PerformanceMonitor = perfMonitor;
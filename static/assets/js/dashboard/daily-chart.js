/**
 * Dashboard Daily Chart functionality
 * Handles the daily chart for Surat Masuk & Keluar
 */

let dailyChart = null;

/**
 * Initialize the daily chart
 */
function initDailyChart() {
    const ctx = document.getElementById('dailyChart');
    if (!ctx) {
        console.error('Daily chart canvas not found');
        return;
    }
    
    const context = ctx.getContext('2d');
    
    dailyChart = new Chart(context, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Surat Masuk',
                data: [],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: 'rgb(59, 130, 246)',
                pointBorderColor: 'rgb(59, 130, 246)',
                pointHoverBackgroundColor: 'rgb(59, 130, 246)',
                pointHoverBorderColor: 'rgb(59, 130, 246)'
            }, {
                label: 'Surat Keluar',
                data: [],
                borderColor: 'rgb(239, 68, 68)',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: 'rgb(239, 68, 68)',
                pointBorderColor: 'rgb(239, 68, 68)',
                pointHoverBackgroundColor: 'rgb(239, 68, 68)',
                pointHoverBorderColor: 'rgb(239, 68, 68)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                },
                title: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Tanggal'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Jumlah Surat'
                    },
                    ticks: {
                        stepSize: 1,
                        callback: function(value) {
                            return Math.floor(value) === value ? value : '';
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

/**
 * Load daily chart data from API
 */
function loadDailyChartData() {
    const loadingElement = document.getElementById('chart-loading');
    
    if (loadingElement) {
        loadingElement.style.display = 'flex';
    }
    
    fetch('/dashboard/api/daily-chart-data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error('Error loading chart data:', data.error);
                showChartError('Gagal memuat data grafik');
                return;
            }
            
            if (!dailyChart) {
                console.error('Daily chart not initialized');
                showChartError('Grafik belum diinisialisasi');
                return;
            }
            
            // Update chart data
            dailyChart.data.labels = data.labels || [];
            dailyChart.data.datasets[0].data = data.surat_masuk || [];
            dailyChart.data.datasets[1].data = data.surat_keluar || [];
            
            // Update chart with animation
            dailyChart.update('active');
            
            // Hide loading indicator
            if (loadingElement) {
                loadingElement.style.display = 'none';
            }
            
            console.log('Chart data loaded successfully');
        })
        .catch(error => {
            console.error('Error loading chart data:', error);
            showChartError('Gagal memuat grafik');
        });
}

/**
 * Show chart error message
 * @param {string} message - Error message to display
 */
function showChartError(message) {
    const loadingElement = document.getElementById('chart-loading');
    if (loadingElement) {
        loadingElement.innerHTML = `
            <div class="text-center">
                <i class="fas fa-exclamation-triangle text-2xl text-red-400 mb-2"></i>
                <p class="text-red-500">${message}</p>
                <button onclick="retryLoadChart()" class="mt-2 px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-sm">
                    <i class="fas fa-redo mr-1"></i>Coba Lagi
                </button>
            </div>
        `;
    }
}

/**
 * Retry loading chart data
 */
function retryLoadChart() {
    console.log('Retrying chart data load...');
    loadDailyChartData();
}

/**
 * Refresh chart data manually
 */
function refreshDailyChart() {
    console.log('Refreshing daily chart...');
    loadDailyChartData();
}

/**
 * Initialize chart when DOM is ready
 */
function initializeDashboardChart() {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded');
        showChartError('Library grafik tidak tersedia');
        return;
    }
    
    // Initialize chart
    initDailyChart();
    
    // Load data
    loadDailyChartData();
    
    console.log('Dashboard chart initialized');
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboardChart();
});

// Export functions for global access
window.dashboardChart = {
    init: initializeDashboardChart,
    refresh: refreshDailyChart,
    retry: retryLoadChart
};
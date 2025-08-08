/* ===== ERROR PAGES JAVASCRIPT ===== */

// Initialize error page functionality
document.addEventListener("DOMContentLoaded", function () {
  initErrorPage();
});

function initErrorPage() {
  // Add simple animations
  addPageAnimations();

  // Initialize auto-refresh for maintenance page only
  if (window.location.pathname.includes("maintenance")) {
    initMaintenanceMode();
  }

  // Add essential keyboard shortcuts only
  addKeyboardShortcuts();
}

// Add simple entrance animations
function addPageAnimations() {
  const errorContainer = document.querySelector(".max-w-4xl");

  if (errorContainer) {
    errorContainer.style.opacity = "0";

    setTimeout(() => {
      errorContainer.style.transition = "opacity 0.3s ease-out";
      errorContainer.style.opacity = "1";
    }, 50);
  }
}

// Initialize maintenance mode functionality
function initMaintenanceMode() {
  let progress = 65;
  const progressBar = document.getElementById("progress-bar");
  const progressText = document.getElementById("progress-text");

  // Simulate progress updates
  function updateProgress() {
    if (progress < 100) {
      progress += Math.random() * 2;
      if (progress > 100) progress = 100;

      if (progressBar) {
        progressBar.style.width = progress + "%";
      }
      if (progressText) {
        progressText.textContent = Math.round(progress) + "%";
      }

      // Show completion message when done
      if (progress >= 100) {
        showMaintenanceComplete();
      }
    }
  }

  // Update progress every 30 seconds
  setInterval(updateProgress, 30000);

  // Auto refresh every 5 minutes
  setTimeout(() => {
    location.reload();
  }, 300000);
}

// Show maintenance completion
function showMaintenanceComplete() {
  const progressContainer = document.querySelector(".progress-container");
  if (progressContainer) {
    progressContainer.innerHTML = `
            <div class="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
                <i class="fas fa-check-circle text-green-500 text-2xl mb-2"></i>
                <p class="text-green-800 font-medium">Maintenance Complete!</p>
                <p class="text-green-600 text-sm">Redirecting in 3 seconds...</p>
            </div>
        `;

    setTimeout(() => {
      window.location.href = "/";
    }, 3000);
  }
}

// Add essential keyboard shortcuts
function addKeyboardShortcuts() {
  document.addEventListener("keydown", function (e) {
    // ESC key - go back
    if (e.key === "Escape") {
      history.back();
    }

    // Enter key - go to dashboard
    if (e.key === "Enter") {
      window.location.href = "/";
    }
  });
}

// Get current error type
function getErrorType() {
  const path = window.location.pathname;
  if (path.includes("404")) return "404";
  if (path.includes("500")) return "500";
  if (path.includes("403")) return "403";
  if (path.includes("maintenance")) return "maintenance";
  return "general";
}

// Utility functions
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg text-white font-medium transition-all duration-300 transform translate-x-full`;

  // Set toast color based on type
  switch (type) {
    case "success":
      toast.classList.add("bg-green-500");
      break;
    case "error":
      toast.classList.add("bg-red-500");
      break;
    case "warning":
      toast.classList.add("bg-yellow-500");
      break;
    default:
      toast.classList.add("bg-blue-500");
  }

  toast.textContent = message;
  document.body.appendChild(toast);

  // Show toast
  setTimeout(() => {
    toast.classList.remove("translate-x-full");
  }, 100);

  // Hide toast after 3 seconds
  setTimeout(() => {
    toast.classList.add("translate-x-full");
    setTimeout(() => {
      document.body.removeChild(toast);
    }, 300);
  }, 3000);
}

// Check system status
function checkSystemStatus() {
  fetch("/api/status")
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "online") {
        showToast("System is back online!", "success");
        setTimeout(() => {
          window.location.href = "/";
        }, 2000);
      }
    })
    .catch((error) => {
      console.log("Status check failed:", error);
    });
}

// Auto-check system status every 30 seconds for maintenance page only
if (window.location.pathname.includes("maintenance")) {
  setInterval(checkSystemStatus, 30000);
}

// Export essential functions only
window.ErrorPage = {
  showToast,
  checkSystemStatus,
};

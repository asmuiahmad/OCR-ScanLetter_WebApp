/* ===== SPA NAVIGATION SYSTEM ===== */

class SPANavigation {
  constructor() {
    this.currentPage = window.location.pathname;
    this.contentContainer = document.querySelector(".content");
    this.breadcrumbContainer = document.querySelector("nav ol");
    this.isLoading = false;
    this.cache = new Map();

    this.init();
  }

  init() {
    // Intercept all navigation links
    this.interceptLinks();

    // Handle browser back/forward buttons
    window.addEventListener("popstate", (e) => {
      if (e.state && e.state.url) {
        this.loadPage(e.state.url, false);
      }
    });

    // Add initial state to history
    history.replaceState({ url: this.currentPage }, "", this.currentPage);

    // Add loading indicator styles
    this.addLoadingStyles();
  }

  interceptLinks() {
    document.addEventListener("click", (e) => {
      const link = e.target.closest("a[href]");

      if (!link) return;

      const href = link.getAttribute("href");

      // Skip external links, anchors, and special links
      if (this.shouldSkipLink(href, link)) return;

      e.preventDefault();
      this.navigateTo(href);
    });
  }

  shouldSkipLink(href, link) {
    return (
      !href ||
      href.startsWith("#") ||
      href.startsWith("mailto:") ||
      href.startsWith("tel:") ||
      href.includes("logout") ||
      href.includes("download") ||
      link.hasAttribute("download") ||
      link.target === "_blank" ||
      href.startsWith("http") ||
      href.includes("static/")
    );
  }

  async navigateTo(url) {
    if (this.isLoading || url === this.currentPage) return;

    // Update active sidebar item
    this.updateSidebarActive(url);

    // Load page content
    await this.loadPage(url, true);
  }

  async loadPage(url, addToHistory = true) {
    if (this.isLoading) return;

    this.isLoading = true;
    this.showLoading();

    try {
      let content;

      // Check cache first
      if (this.cache.has(url)) {
        content = this.cache.get(url);
      } else {
        content = await this.fetchPageContent(url);
        // Cache the content (limit cache size)
        if (this.cache.size > 10) {
          const firstKey = this.cache.keys().next().value;
          this.cache.delete(firstKey);
        }
        this.cache.set(url, content);
      }

      // Update page content
      this.updatePageContent(content);

      // Update URL and history
      if (addToHistory) {
        history.pushState({ url }, "", url);
      }

      this.currentPage = url;

      // Update page title
      if (content.title) {
        document.title = content.title;
      }
    } catch (error) {
      console.error("Failed to load page:", error);
      this.showError("Gagal memuat halaman. Silakan coba lagi.");
    } finally {
      this.isLoading = false;
      this.hideLoading();
    }
  }

  async fetchPageContent(url) {
    const response = await fetch(url, {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        Accept: "application/json, text/html",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const html = await response.text();
    return this.parsePageContent(html);
  }

  parsePageContent(html) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    // Extract main content
    const content = doc.querySelector(".content");
    const breadcrumb = doc.querySelector("nav ol");
    const title = doc.querySelector("title");

    return {
      content: content ? content.innerHTML : html,
      breadcrumb: breadcrumb ? breadcrumb.innerHTML : "",
      title: title ? title.textContent : "",
    };
  }

  updatePageContent(pageData) {
    // Update main content with fade effect
    this.contentContainer.style.opacity = "0";

    setTimeout(() => {
      this.contentContainer.innerHTML = pageData.content;

      // Update breadcrumb
      if (pageData.breadcrumb && this.breadcrumbContainer) {
        this.breadcrumbContainer.innerHTML = pageData.breadcrumb;
      }

      // Re-initialize any JavaScript components
      this.reinitializeComponents();

      // Fade in new content
      this.contentContainer.style.opacity = "1";

      // Scroll to top
      this.contentContainer.scrollTop = 0;
    }, 150);
  }

  updateSidebarActive(url) {
    // Remove active class from all sidebar links
    document.querySelectorAll(".nav-links a").forEach((link) => {
      link.classList.remove("active");
    });

    // Don't add active class - keep sidebar clean and simple
    // Just expand parent dropdown if needed for navigation context
    const activeLink = document.querySelector(`.nav-links a[href="${url}"]`);
    if (activeLink) {
      const dropdown = activeLink.closest(".dropdown");
      if (dropdown) {
        dropdown.style.display = "block";
        dropdown.classList.add("show");
        const parentLink = dropdown.previousElementSibling;
        if (parentLink) {
          const chevron = parentLink.querySelector(".fa-chevron-down");
          if (chevron) {
            chevron.style.transform = "rotate(180deg)";
          }
        }
      }
    }
  }

  reinitializeComponents() {
    // Reinitialize common components
    this.reinitializeTooltips();
    this.reinitializeForms();
    this.reinitializeModals();
    this.reinitializeCharts();

    // Fire custom event for other scripts
    window.dispatchEvent(new CustomEvent("pageContentUpdated"));
  }

  reinitializeTooltips() {
    // Reinitialize any tooltip libraries
    if (window.bootstrap && window.bootstrap.Tooltip) {
      document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
        new bootstrap.Tooltip(el);
      });
    }
  }

  reinitializeForms() {
    // Reinitialize form validation and interactions
    document.querySelectorAll("form").forEach((form) => {
      // Add any form-specific initialization here
    });
  }

  reinitializeModals() {
    // Reinitialize modal functionality
    document.querySelectorAll(".modal").forEach((modal) => {
      // Add modal event listeners
    });
  }

  reinitializeCharts() {
    // Reinitialize charts if Chart.js is present
    if (window.Chart && document.querySelector("canvas")) {
      // Chart initialization will be handled by individual page scripts
    }
  }

  showLoading() {
    // Show progress bar
    this.showProgressBar();

    if (!document.querySelector(".spa-loading")) {
      const loading = document.createElement("div");
      loading.className = "spa-loading";
      loading.innerHTML = `
                <div class="spa-loading-spinner" role="status" aria-live="polite">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Memuat...</span>
                </div>
            `;
      document.body.appendChild(loading);
    }
  }

  hideLoading() {
    // Hide progress bar
    this.hideProgressBar();

    const loading = document.querySelector(".spa-loading");
    if (loading) {
      loading.remove();
    }
  }

  showProgressBar() {
    const progressBar = document.getElementById("spaProgressBar");
    if (progressBar) {
      progressBar.style.width = "0%";
      progressBar.style.opacity = "1";

      // Animate to 70% while loading
      setTimeout(() => {
        progressBar.style.width = "70%";
      }, 100);
    }
  }

  hideProgressBar() {
    const progressBar = document.getElementById("spaProgressBar");
    if (progressBar) {
      // Complete the progress bar
      progressBar.style.width = "100%";

      // Hide after completion
      setTimeout(() => {
        progressBar.style.opacity = "0";
        setTimeout(() => {
          progressBar.style.width = "0%";
        }, 300);
      }, 200);
    }
  }

  showError(message) {
    // Show error toast
    if (window.showToast) {
      window.showToast(message, "error");
    } else {
      alert(message);
    }
  }

  addLoadingStyles() {
    if (document.querySelector("#spa-styles")) return;

    const styles = document.createElement("style");
    styles.id = "spa-styles";
    styles.textContent = `
            .content {
                transition: opacity 0.15s ease-out;
            }
            
            .spa-loading {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.1);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                backdrop-filter: blur(1px);
            }
            
            .spa-loading-spinner {
                background: white;
                padding: 1.5rem 2rem;
                border-radius: 0.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                display: flex;
                align-items: center;
                gap: 0.75rem;
                font-weight: 500;
                color: #374151;
            }
            
            .spa-loading-spinner i {
                color: #3b82f6;
                font-size: 1.25rem;
            }
            
            .nav-links a.active {
                background-color: rgba(59, 130, 246, 0.1);
                color: #3b82f6;
                border-right: 3px solid #3b82f6;
            }
            
            .nav-links a {
                transition: all 0.2s ease;
            }
        `;
    document.head.appendChild(styles);
  }

  // Public method to programmatically navigate
  navigate(url) {
    this.navigateTo(url);
  }

  // Public method to refresh current page
  refresh() {
    this.cache.delete(this.currentPage);
    this.loadPage(this.currentPage, false);
  }
}

// Initialize SPA Navigation when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.spaNavigation = new SPANavigation();
});

// Export for use in other scripts
window.SPANavigation = SPANavigation;

/* ===== SIDEBAR FUNCTIONALITY ===== */

// Dropdown menu toggle for modern sidebar
function toggleMenu(e, id) {
  e.preventDefault();
  e.stopPropagation();
  
  const dropdown = document.getElementById(id);
  const chevron = e.currentTarget.querySelector('.fa-chevron-down');
  const sidebar = document.querySelector('.modern-sidebar');
  
  // Don't open dropdown if sidebar is collapsed
  if (sidebar && sidebar.classList.contains('sidebar-collapsed')) {
    return;
  }
  
  // Close all other dropdowns first
  document.querySelectorAll('.dropdown.show').forEach(otherDropdown => {
    if (otherDropdown.id !== id) {
      otherDropdown.classList.remove('show');
      const otherChevron = document.querySelector(`[onclick*="${otherDropdown.id}"] .fa-chevron-down`);
      if (otherChevron) {
        otherChevron.style.transform = 'rotate(0deg)';
      }
    }
  });
  
  // Toggle current dropdown
  if (dropdown.classList.contains('show')) {
    dropdown.classList.remove('show');
    if (chevron) chevron.style.transform = 'rotate(0deg)';
  } else {
    dropdown.classList.add('show');
    if (chevron) chevron.style.transform = 'rotate(180deg)';
  }
}

// User Profile Menu Toggle
function toggleUserMenu(e) {
  e.preventDefault();
  e.stopPropagation();
  const dropdown = document.getElementById('userDropdown');
  dropdown.classList.toggle('show');
}

// Show User Info Modal
function showUserInfo() {
  const userInfo = `
    <div class="user-info-modal">
      <h4>Informasi User</h4>
      <p><strong>Email:</strong> ${window.currentUser?.email || 'N/A'}</p>
      <p><strong>Role:</strong> ${window.currentUser?.role || 'N/A'}</p>
      <p><strong>Status:</strong> ${window.currentUser?.isApproved ? 'Active' : 'Pending'}</p>
      <p><strong>Last Login:</strong> ${window.currentUser?.lastLogin || 'Never'}</p>
      <p><strong>Login Count:</strong> ${window.currentUser?.loginCount || 0}</p>
    </div>
  `;
  
  // Show toast with user info
  if (window.toast) {
    window.toast.info(userInfo, 'User Information', 8000);
  }
  
  // Close dropdown
  const dropdown = document.getElementById('userDropdown');
  if (dropdown) {
    dropdown.classList.remove('show');
  }
}

// Enhanced Sidebar toggle functionality
document.addEventListener('DOMContentLoaded', function() {
  const sidebar = document.querySelector('.modern-sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  
  // 1. PASTIKAN SIDEBAR COLLAPSE SAAT LOAD
  let isCollapsed = true;
  const savedState = localStorage.getItem('sidebarCollapsed');
  
  if (savedState !== null) {
    isCollapsed = savedState === 'true';
  } else {
    // Default: collapse di desktop dan mobile
    isCollapsed = true;
    localStorage.setItem('sidebarCollapsed', 'true');
  }
  
  // Terapkan state awal
  if (sidebar) {
    if (isCollapsed) {
      sidebar.classList.add('sidebar-collapsed');
    } else {
      sidebar.classList.remove('sidebar-collapsed');
    }
    // Hapus class no-transition setelah inisialisasi
    setTimeout(() => {
      sidebar.classList.remove('no-transition');
    }, 100);
  }

  // 2. TOGGLE FUNCTION DENGAN PERBAIKAN LEBAR
  function toggleSidebar() {
    if (!sidebar) return;
    isCollapsed = !isCollapsed;
    if (isCollapsed) {
      sidebar.classList.add('sidebar-collapsed');
      // Close all dropdowns when collapsing
      document.querySelectorAll('.dropdown.show').forEach(dropdown => {
        dropdown.classList.remove('show');
        const chevron = document.querySelector(`[onclick*="${dropdown.id}"] .fa-chevron-down`);
        if (chevron) {
          chevron.style.transform = 'rotate(0deg)';
        }
        const parentLink = document.querySelector(`[onclick*="${dropdown.id}"]`);
        if (parentLink) {
          parentLink.classList.remove('active');
        }
      });
    } else {
      sidebar.classList.remove('sidebar-collapsed');
    }
    localStorage.setItem('sidebarCollapsed', isCollapsed);
    // Perbaiki tooltip saat toggle
    document.querySelectorAll('.nav-links li a').forEach(link => {
      if (isCollapsed && !link.getAttribute('data-tooltip')) {
        const title = link.querySelector('.links_name')?.textContent || '';
        link.setAttribute('data-tooltip', title);
      }
    });
  }

  // 3. EVENT LISTENER UNTUK TOGGLE
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', toggleSidebar);
  }

  // 4. PERBAIKI TOOLTIP SAAT COLLAPSE
  if (isCollapsed) {
    document.querySelectorAll('.nav-links li a').forEach(link => {
      const title = link.querySelector('.links_name')?.textContent || '';
      link.setAttribute('data-tooltip', title);
    });
  }
  
  // Completely disable any sidebar hover expand functionality
  if (sidebar) {
    // Remove any existing hover event listeners
    sidebar.onmouseenter = null;
    sidebar.onmouseleave = null;
    
    // Ensure sidebar width is controlled only by CSS classes
    sidebar.addEventListener('mouseenter', function(e) {
      e.preventDefault();
      // Do nothing - no hover expand
    });
    
    sidebar.addEventListener('mouseleave', function(e) {
      e.preventDefault();
      // Do nothing - no hover collapse
    });
  }
  
  // Auto-collapse on mobile only
  function handleResize() {
    if (window.innerWidth <= 768) {
      if (!isCollapsed) {
        toggleSidebar();
      }
    }
  }
  
  window.addEventListener('resize', handleResize);
  handleResize(); // Check on initial load

  // Notification bell toggle
  const notificationBell = document.querySelector('.notification-bell-btn');
  const notificationDropdown = document.querySelector('.notification-dropdown');

  if (notificationBell && notificationDropdown) {
    notificationBell.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      notificationDropdown.classList.toggle('hidden');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
      if (!notificationBell.contains(event.target) && !notificationDropdown.contains(event.target)) {
        notificationDropdown.classList.add('hidden');
      }
    });
  }

  // Mobile menu toggle
  const mobileMenuButton = document.querySelector('.mobile-menu-button');
  const mobileMenu = document.querySelector('.mobile-menu');
  if (mobileMenuButton && mobileMenu) {
    mobileMenuButton.addEventListener('click', function() {
      mobileMenu.classList.toggle('hidden');
    });
  }

  // Close dropdowns when clicking outside
  document.addEventListener('click', function(e) {
    const sidebar = document.querySelector('.modern-sidebar');
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');
    const userDropdown = document.getElementById('userDropdown');
    const userMenuBtn = document.querySelector('.user-menu-btn');
    
    // Close all sidebar dropdowns if clicking outside sidebar
    if (sidebar && !sidebar.contains(e.target)) {
      document.querySelectorAll('.dropdown.show').forEach(dropdown => {
        dropdown.classList.remove('show');
        const chevron = document.querySelector(`[onclick*="${dropdown.id}"] .fa-chevron-down`);
        if (chevron) {
          chevron.style.transform = 'rotate(0deg)';
        }
        const parentLink = document.querySelector(`[onclick*="${dropdown.id}"]`);
        if (parentLink) {
          parentLink.classList.remove('active');
        }
      });
    }
    
    // Close mobile sidebar
    if (sidebar && mobileMenuButton && !sidebar.contains(e.target) && !mobileMenuButton.contains(e.target)) {
      sidebar.classList.remove('mobile-open');
      if (mobileMenu) {
        mobileMenu.classList.add('hidden');
      }
    }
    
    // Close user dropdown
    if (userDropdown && userMenuBtn && !userMenuBtn.contains(e.target) && !userDropdown.contains(e.target)) {
      userDropdown.classList.remove('show');
    }
  });
  
  // Add tooltip data to user avatar for collapsed state
  const userAvatar = document.querySelector('.user-avatar');
  if (userAvatar && window.currentUser) {
    const username = window.currentUser.email ? window.currentUser.email.split('@')[0] : 'User';
    const role = window.currentUser.role ? window.currentUser.role.charAt(0).toUpperCase() + window.currentUser.role.slice(1) : 'User';
    userAvatar.setAttribute('data-tooltip', `${username} (${role})`);
  }

  // Remove sidebar expand on hover (desktop only)
  // (No code for mouseenter/mouseleave on sidebar)
});

// Export functions for global use
window.toggleMenu = toggleMenu;
window.toggleUserMenu = toggleUserMenu;
window.showUserInfo = showUserInfo;
// Common utility functions for YouTube Movie Picker

/**
 * Show a notification to the user
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, error, info, warning)
 * @param {number} duration - Duration in milliseconds (optional)
 */
function showNotification(message, type = 'info', duration = null) {
  const notification = document.createElement('div');
  const defaultDuration = type === 'info' ? 6000 : 3000;
  const finalDuration = duration || defaultDuration;
  
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.opacity = '0';
    setTimeout(() => {
      if (document.body.contains(notification)) {
        document.body.removeChild(notification);
      }
    }, 300);
  }, finalDuration);
}

/**
 * Format a date for display
 * @param {string|Date} date - The date to format
 * @param {boolean} includeTime - Whether to include time
 * @returns {string} Formatted date string
 */
function formatDate(date, includeTime = false) {
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    if (includeTime) {
      return dateObj.toLocaleString();
    } else {
      return dateObj.toLocaleDateString();
    }
  } catch (error) {
    return 'Invalid date';
  }
}

/**
 * Extract video ID from YouTube URL
 * @param {string} url - YouTube URL
 * @returns {string|null} Video ID or null if invalid
 */
function extractVideoId(url) {
  try {
    if (url.includes('youtube.com')) {
      const urlParams = new URLSearchParams(new URL(url).search);
      return urlParams.get('v');
    } else if (url.includes('youtu.be')) {
      return url.split('/').pop().split('?')[0];
    }
    return null;
  } catch (error) {
    return null;
  }
}

/**
 * Get YouTube thumbnail URL
 * @param {string} videoId - YouTube video ID
 * @param {string} quality - Thumbnail quality (default, hqdefault, maxresdefault)
 * @returns {string} Thumbnail URL
 */
function getYouTubeThumbnail(videoId, quality = 'hqdefault') {
  return `https://img.youtube.com/vi/${videoId}/${quality}.jpg`;
}

/**
 * Debounce function to limit rapid function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Simple loading state manager
 */
const LoadingManager = {
  show: function(elementId, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (element) {
      element.innerHTML = `
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <p class="loading-text">${message}</p>
        </div>
      `;
    }
  },
  
  hide: function(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
      element.innerHTML = '';
    }
  }
};

/**
 * Simple error state manager
 */
const ErrorManager = {
  show: function(elementId, message, subMessage = null) {
    const element = document.getElementById(elementId);
    if (element) {
      element.innerHTML = `
        <div class="error-container">
          <p class="error-text">${message}</p>
          ${subMessage ? `<p class="error-subtext">${subMessage}</p>` : ''}
        </div>
      `;
    }
  }
};

/**
 * Mobile dropdown/hamburger menu manager
 */
const MobileMenuManager = {
  init: function(buttonId, containerId) {
    const button = document.getElementById(buttonId);
    const container = document.getElementById(containerId);
    
    if (!button || !container) return;
    
    // Toggle menu on button click
    button.addEventListener('click', () => {
      container.classList.toggle('show');
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!container.contains(e.target) && !button.contains(e.target)) {
        container.classList.remove('show');
      }
    });
    
    return {
      show: () => container.classList.add('show'),
      hide: () => container.classList.remove('show'),
      toggle: () => container.classList.toggle('show')
    };
  }
};

/**
 * Form validation utilities
 */
const FormValidator = {
  validateRequired: function(value, fieldName) {
    if (!value || value.trim() === '') {
      return `${fieldName} is required`;
    }
    return null;
  },
  
  validateUrl: function(url, fieldName = 'URL') {
    if (!url || url.trim() === '') {
      return `${fieldName} is required`;
    }
    
    try {
      new URL(url);
      if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
        return 'Please enter a valid YouTube URL';
      }
      return null;
    } catch (error) {
      return 'Please enter a valid URL';
    }
  },
  
  showFieldError: function(fieldId, message) {
    const field = document.getElementById(fieldId);
    if (field) {
      field.classList.add('error');
      
      // Remove existing error message
      const existingError = field.parentNode.querySelector('.field-error');
      if (existingError) {
        existingError.remove();
      }
      
      // Add error message
      const errorDiv = document.createElement('div');
      errorDiv.className = 'field-error';
      errorDiv.style.color = '#ef4444';
      errorDiv.style.fontSize = '0.875rem';
      errorDiv.style.marginTop = '0.25rem';
      errorDiv.textContent = message;
      field.parentNode.appendChild(errorDiv);
    }
  },
  
  clearFieldError: function(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
      field.classList.remove('error');
      const errorDiv = field.parentNode.querySelector('.field-error');
      if (errorDiv) {
        errorDiv.remove();
      }
    }
  }
};

/**
 * Local storage utilities
 */
const StorageUtil = {
  set: function(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.warn('Failed to save to localStorage:', error);
      return false;
    }
  },
  
  get: function(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.warn('Failed to read from localStorage:', error);
      return defaultValue;
    }
  },
  
  remove: function(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.warn('Failed to remove from localStorage:', error);
      return false;
    }
  }
};

/**
 * Toggle visibility of collapsible sections (forms, menus, etc.)
 * @param {string} sectionId - ID of the section to toggle
 * @param {boolean} scrollIntoView - Whether to scroll to the section when shown
 */
function toggleSection(sectionId, scrollIntoView = true) {
  const section = document.getElementById(sectionId);
  if (!section) return;
  
  const isHidden = section.classList.contains('hidden');
  
  if (isHidden) {
    section.classList.remove('hidden');
    if (scrollIntoView) {
      section.scrollIntoView({ behavior: 'smooth' });
    }
  } else {
    section.classList.add('hidden');
  }
  
  return !isHidden; // Return new visibility state (true = visible)
}

/**
 * Close a collapsible section
 * @param {string} sectionId - ID of the section to close
 */
function closeSection(sectionId) {
  const section = document.getElementById(sectionId);
  if (section) {
    section.classList.add('hidden');
  }
}

/**
 * Show a section
 * @param {string} sectionId - ID of the section to show
 * @param {boolean} scrollIntoView - Whether to scroll to the section
 */
function showSection(sectionId, scrollIntoView = true) {
  const section = document.getElementById(sectionId);
  if (section) {
    section.classList.remove('hidden');
    if (scrollIntoView) {
      section.scrollIntoView({ behavior: 'smooth' });
    }
  }
}

/**
 * Create a movie card element
 * @param {Object} movie - Movie object with id, title, url, verified, etc.
 * @param {Object} options - Options for card creation
 * @returns {HTMLElement} Movie card element
 */
function createMovieCard(movie, options = {}) {
  const {
    showDeleteButton = true,
    cardClass = 'movie-card',
    imageHeight = 'h-48',
    linkPrefix = '/movie/'
  } = options;

  const videoId = extractVideoId(movie.url);
  const thumbnail = `https://img.youtube.com/vi/${videoId}/0.jpg`;

  // Format last verified date
  let lastVerifiedText = '';
  if (movie.last_verified) {
    lastVerifiedText = `Last verified: ${formatDate(movie.last_verified, true)}`;
  } else {
    lastVerifiedText = 'Not verified';
  }

  const card = document.createElement('div');
  card.className = `${cardClass} mobile-movie-card relative rounded overflow-hidden shadow hover:shadow-lg transform hover:-translate-y-1 transition bg-gray-800 hover:bg-gray-700`;
  card.innerHTML = `
    <a href="${linkPrefix}${movie.id}" class="block">
      <div class="relative">
        <img src="${thumbnail}" alt="${escapeHtml(movie.title)}" class="w-full ${imageHeight} sm:${imageHeight} object-cover">
        <!-- Verified badge: upper-left -->
        ${movie.verified ? '<div class="status-badge status-badge-verified absolute top-1 left-1 z-10">✅</div>' : ''}
        <!-- IMDb rating badge: upper-right -->
        ${(movie.imdb_rating && movie.imdb_rating !== 'N/A') ? `<div class="rating-badge absolute top-1 right-1 z-10">⭐ ${movie.imdb_rating}</div>` : ''}
        <!-- Age restriction badge: lower-left -->
        ${movie.age_restricted ? '<div class="status-badge status-badge-age-restricted absolute bottom-1 left-1 z-10">🔞</div>' : ''}
      </div>
      <div class="p-3">
        <h3 class="font-semibold text-white mb-1 line-clamp-2">${escapeHtml(movie.title)}</h3>
        <p class="text-xs text-gray-400">${lastVerifiedText}</p>
        ${movie.age_restricted ? '<p class="text-xs text-red-400 mt-1">⚠️ Age-restricted content</p>' : ''}
      </div>
    </a>
    ${(showDeleteButton && linkPrefix !== '/movie/') ? `
      <button onclick="deleteMovie(${movie.id}, event)" 
              class="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white text-xs px-2 py-1 rounded opacity-75 hover:opacity-100 transition-opacity"
              title="Delete movie">
        🗑️
      </button>
    ` : ''}
  `;

  return card;
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Setup hamburger menu functionality
 * @param {string} toggleButtonId - ID of the hamburger toggle button
 * @param {string} dropdownId - ID of the dropdown container
 * @param {string} currentTextId - ID of element showing current selection (optional)
 */
function setupHamburgerMenu(toggleButtonId, dropdownId, currentTextId = null) {
  const toggleButton = document.getElementById(toggleButtonId);
  const dropdown = document.getElementById(dropdownId);
  
  if (!toggleButton || !dropdown) {
    console.warn(`Hamburger menu setup failed: missing elements ${toggleButtonId} or ${dropdownId}`);
    return;
  }
  
  toggleButton.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropdown.classList.toggle('show');
  });
  
  // Close on click outside
  document.addEventListener('click', (e) => {
    if (!toggleButton.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.remove('show');
    }
  });
  
  // Handle option selection in dropdown
  dropdown.addEventListener('click', (e) => {
    const option = e.target.closest('[data-value]');
    if (option) {
      const value = option.getAttribute('data-value');
      const text = option.textContent.trim();
      
      // Update current text if element exists
      if (currentTextId) {
        const currentTextElement = document.getElementById(currentTextId);
        if (currentTextElement) {
          currentTextElement.textContent = text;
        }
      }
      
      // Close dropdown
      dropdown.classList.remove('show');
      
      // Dispatch custom event for handling selection
      const event = new CustomEvent('hamburgerSelect', {
        detail: { value, text, option }
      });
      dropdown.dispatchEvent(event);
    }
  });
}

/**
 * Setup form toggle functionality
 * @param {string} toggleButtonId - ID of button that opens the form
 * @param {string} sectionId - ID of the form section
 * @param {string} closeButtonId - ID of button that closes the form
 */
function setupFormToggle(toggleButtonId, sectionId, closeButtonId) {
  const toggleButton = document.getElementById(toggleButtonId);
  const closeButton = document.getElementById(closeButtonId);
  
  if (toggleButton) {
    toggleButton.addEventListener('click', () => {
      showSection(sectionId);
    });
  }
  
  if (closeButton) {
    closeButton.addEventListener('click', () => {
      closeSection(sectionId);
    });
  }
}

/**
 * Initialize common page features
 */
function initCommonFeatures() {
  // Add click-to-copy functionality to any element with data-copy attribute
  document.querySelectorAll('[data-copy]').forEach(element => {
    element.style.cursor = 'pointer';
    element.addEventListener('click', () => {
      const textToCopy = element.getAttribute('data-copy') || element.textContent;
      navigator.clipboard.writeText(textToCopy).then(() => {
        showNotification('Copied to clipboard!', 'success', 2000);
      }).catch(() => {
        showNotification('Failed to copy to clipboard', 'error');
      });
    });
  });
  
  // Add loading states to forms
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', (e) => {
      const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
      if (submitButton) {
        submitButton.disabled = true;
        const originalText = submitButton.textContent;
        submitButton.textContent = 'Loading...';
        
        // Re-enable after 10 seconds as fallback
        setTimeout(() => {
          submitButton.disabled = false;
          submitButton.textContent = originalText;
        }, 10000);
      }
    });
  });
}

// Initialize common features when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initCommonFeatures);
} else {
  initCommonFeatures();
}

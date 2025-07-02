// API utilities for YouTube Movie Picker

/**
 * Base API class for making HTTP requests
 */
class APIClient {
  constructor(baseURL = '') {
    this.baseURL = baseURL;
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    try {
      const response = await fetch(url, mergedOptions);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      
      return data;
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }
  
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }
  
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
  
  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }
  
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

// Global API client instance
const api = new APIClient('/api');

/**
 * Movie-related API functions
 */
const MovieAPI = {
  // Get all movies with pagination
  async getMovies(limit = null, offset = 0) {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit);
    if (offset) params.append('offset', offset);
    
    const endpoint = `/movies${params.toString() ? '?' + params.toString() : ''}`;
    return api.get(endpoint);
  },
  
  // Get a single movie by ID
  async getMovie(id) {
    return api.get(`/movies/${id}`);
  },
  
  // Create a new movie
  async createMovie(title, url, verified = false) {
    return api.post('/movies', { title, url, verified });
  },
  
  // Update an existing movie
  async updateMovie(id, title, url, verified = false) {
    return api.put(`/movies/${id}`, { title, url, verified });
  },
  
  // Delete a movie
  async deleteMovie(id) {
    return api.delete(`/movies/${id}`);
  },
  
  // Get a random movie
  async getRandomMovie() {
    return api.get('/random-movie');
  },
  
  // Get movie info (OMDb data)
  async getMovieInfo(id) {
    return api.get(`/movie-info/${id}`);
  },
  
  // Get movies by genre
  async getMoviesByGenre(genreName, sortBy = 'title', order = 'asc') {
    const params = new URLSearchParams({
      sort_by: sortBy,
      order: order
    });
    return api.get(`/movies-by-genre/${encodeURIComponent(genreName)}?${params}`);
  },
  
  // Get movies with genre information
  async getMoviesWithGenres() {
    return api.get('/movies-with-genres');
  },
  
  // Verify a movie URL
  async verifyMovie(id) {
    return api.post(`/movie/${id}/verify`);
  },
  
  // Check movie age restrictions
  async checkAgeRestrictions(id) {
    return api.post(`/check-age-restrictions/${id}`);
  },
  
  // Clear movie info cache
  async clearCache(id) {
    return api.post(`/clear-cache/${id}`);
  }
};

/**
 * Search and import API functions
 */
const SearchAPI = {
  // Search YouTube for movies
  async searchYouTube(query, maxResults = 10, useAPI = false) {
    return api.post('/search-youtube', {
      query,
      max_results: maxResults,
      use_api: useAPI
    });
  },
  
  // Import a movie from search results
  async importFromSearch(url, title = null, autoVerify = true, fetchMetadata = true) {
    const data = { url, auto_verify: autoVerify, fetch_metadata: fetchMetadata };
    if (title) data.title = title;
    return api.post('/import-from-search', data);
  }
};

/**
 * Utility API functions
 */
const UtilityAPI = {
  // Fetch YouTube video title
  async fetchTitle(url) {
    return api.post('/fetch-title', { url });
  },
  
  // Validate a URL
  async validateUrl(url) {
    return api.post('/validate-url', { url });
  },
  
  // Test all URLs in background
  async testAllUrls() {
    return api.post('/test-urls');
  }
};

/**
 * Admin API functions
 */
const AdminAPI = {
  // Get admin statistics
  async getStats() {
    return api.get('/admin/stats');
  },
  
  // Bulk operations
  async bulkVerify() {
    return api.post('/admin/bulk-verify');
  },
  
  async bulkCheckAge() {
    return api.post('/admin/bulk-check-age');
  },
  
  async bulkFetchInfo() {
    return api.post('/admin/bulk-fetch-info');
  }
};

/**
 * Higher-level API operations with error handling and loading states
 */
const MovieManager = {
  // Load movies with pagination and loading states
  async loadMovies(containerId, limit = 8, offset = 0, append = false) {
    const container = document.getElementById(containerId);
    if (!container) throw new Error(`Container ${containerId} not found`);
    
    if (!append) {
      LoadingManager.show(containerId, 'Loading movies...');
    }
    
    try {
      const data = await MovieAPI.getMovies(limit, offset);
      
      if (!append) {
        container.innerHTML = '';
      }
      
      if (data.movies && data.movies.length > 0) {
        data.movies.forEach(movie => {
          const movieCard = this.createMovieCard(movie);
          container.appendChild(movieCard);
        });
      } else if (!append) {
        ErrorManager.show(containerId, 'No movies found', 'Try adding some movies to get started');
      }
      
      return data;
    } catch (error) {
      if (!append) {
        ErrorManager.show(containerId, 'Failed to load movies', error.message);
      }
      throw error;
    }
  },
  
  // Create a movie card element
  createMovieCard(movie) {
    const videoId = extractVideoId(movie.url);
    const thumbnail = videoId ? getYouTubeThumbnail(videoId) : '';
    
    const card = document.createElement('a');
    card.href = `/movie/${movie.id}`;
    card.className = 'movie-card';
    
    // Status badges
    let badges = '';
    if (movie.verified) {
      badges += '<div class="status-badge status-badge-verified">✅</div>';
    }
    if (movie.age_restricted) {
      badges += '<div class="status-badge status-badge-age-restricted">🔞</div>';
    }
    if (movie.age_checked_at && !movie.age_restricted) {
      badges += '<div class="status-badge status-badge-age-checked">👍</div>';
    }
    
    // Rating badge
    let ratingBadge = '';
    if (movie.imdb_rating && movie.imdb_rating !== 'N/A') {
      ratingBadge = `<div class="rating-badge">★ ${movie.imdb_rating}</div>`;
    }
    
    card.innerHTML = `
      <div style="position: relative;">
        ${thumbnail ? `<img src="${thumbnail}" alt="${movie.title}" class="video-thumbnail" onerror="this.src='${getYouTubeThumbnail(videoId, 'hqdefault')}'">` : ''}
        <div class="status-badges">${badges}</div>
        ${ratingBadge}
      </div>
      <div class="card-content">
        <h4 class="card-title line-clamp-2">${movie.title}</h4>
        ${movie.year && movie.year !== 'N/A' ? `<p class="text-xs text-gray-400">${movie.year}</p>` : ''}
        ${movie.last_verified ? `<p class="text-xs text-gray-500">Verified: ${formatDate(movie.last_verified)}</p>` : ''}
        ${movie.age_restricted ? '<p class="text-xs text-red-400 mt-1">⚠️ Age-restricted</p>' : ''}
      </div>
    `;
    
    return card;
  },
  
  // Add a new movie with validation and feedback
  async addMovie(title, url, verified = false, showNotifications = true) {
    try {
      // Validate inputs
      const titleError = FormValidator.validateRequired(title, 'Title');
      if (titleError) {
        if (showNotifications) showNotification(titleError, 'error');
        return null;
      }
      
      const urlError = FormValidator.validateUrl(url);
      if (urlError) {
        if (showNotifications) showNotification(urlError, 'error');
        return null;
      }
      
      const result = await MovieAPI.createMovie(title, url, verified);
      
      if (showNotifications) {
        showNotification('Movie added successfully! 🎬', 'success');
      }
      
      return result;
    } catch (error) {
      if (showNotifications) {
        showNotification(`Failed to add movie: ${error.message}`, 'error');
      }
      throw error;
    }
  }
};

/**
 * Auto-completion and search utilities
 */
const SearchManager = {
  // Initialize search functionality with debouncing
  init(inputId, resultsId, onSelect) {
    const input = document.getElementById(inputId);
    const results = document.getElementById(resultsId);
    
    if (!input || !results) return;
    
    const debouncedSearch = debounce(async (query) => {
      if (query.length < 3) {
        results.innerHTML = '';
        return;
      }
      
      try {
        LoadingManager.show(resultsId, 'Searching...');
        const data = await SearchAPI.searchYouTube(query, 5);
        
        results.innerHTML = '';
        if (data.results && data.results.length > 0) {
          data.results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'search-result-item';
            item.innerHTML = `
              <img src="${result.thumbnail}" alt="${result.title}" style="width: 80px; height: 45px; object-fit: cover; border-radius: 4px;">
              <div>
                <h4>${result.title}</h4>
                <p>${result.duration || 'Unknown duration'}</p>
              </div>
            `;
            item.addEventListener('click', () => onSelect(result));
            results.appendChild(item);
          });
        } else {
          ErrorManager.show(resultsId, 'No results found', 'Try a different search term');
        }
      } catch (error) {
        ErrorManager.show(resultsId, 'Search failed', error.message);
      }
    }, 500);
    
    input.addEventListener('input', (e) => {
      debouncedSearch(e.target.value.trim());
    });
  }
};

/**
 * Delete a movie with confirmation
 * @param {number} movieId - ID of the movie to delete
 * @param {Event} event - Click event (to prevent bubbling)
 * @param {Function} onSuccess - Callback function on successful deletion
 */
async function deleteMovie(movieId, event, onSuccess = null) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  
  if (!confirm('Are you sure you want to delete this movie? This action cannot be undone.')) {
    return;
  }
  
  try {
    const response = await fetch(`/api/movies/${movieId}`, {
      method: 'DELETE'
    });
    
    const result = await response.json();
    
    if (result.success) {
      showNotification('Movie deleted successfully', 'success');
      if (onSuccess) {
        onSuccess(movieId);
      }
    } else {
      showNotification('Failed to delete movie: ' + (result.error || 'Unknown error'), 'error');
    }
  } catch (error) {
    console.error('Error deleting movie:', error);
    showNotification('Failed to delete movie. Please try again.', 'error');
  }
}

/**
 * Fetch title from YouTube URL
 * @param {string} url - YouTube URL
 * @returns {Promise<Object>} Result object with success and title/error
 */
async function fetchYouTubeTitle(url) {
  try {
    const response = await fetch('/api/fetch-title', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url })
    });
    
    return await response.json();
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Validate YouTube URL
 * @param {string} url - YouTube URL to validate
 * @returns {Promise<Object>} Result object with success and valid/message
 */
async function validateYouTubeUrl(url) {
  try {
    const response = await fetch('/api/validate-url', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url })
    });
    
    return await response.json();
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Add a new movie
 * @param {string} title - Movie title
 * @param {string} url - YouTube URL
 * @param {boolean} verified - Whether URL is verified
 * @returns {Promise<Object>} Result object
 */
async function addMovie(title, url, verified = false) {
  try {
    // First validate the URL
    const validation = await validateYouTubeUrl(url);
    const isVerified = validation.success && validation.valid;
    
    const response = await fetch('/api/movies', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title, url, verified: verified || isVerified })
    });
    
    const result = await response.json();
    if (result.success) {
      result.verified = isVerified;
      result.validationMessage = validation.message;
    }
    return result;
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Search YouTube for movies
 * @param {string} query - Search query
 * @param {Object} options - Search options
 * @returns {Promise<Object>} Search results
 */
async function searchYouTube(query, options = {}) {
  const { maxResults = 10, useApi = false } = options;
  
  try {
    const response = await fetch('/api/search-youtube', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        query, 
        max_results: maxResults, 
        use_api: useApi 
      })
    });
    
    return await response.json();
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Import a movie from search results
 * @param {string} title - Movie title
 * @param {string} url - YouTube URL
 * @param {Object} options - Import options
 * @returns {Promise<Object>} Import result
 */
async function importMovieFromSearch(title, url, options = {}) {
  const { autoVerify = true, fetchMetadata = true } = options;
  
  try {
    const response = await fetch('/api/import-from-search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        title, 
        url, 
        auto_verify: autoVerify, 
        fetch_metadata: fetchMetadata 
      })
    });
    
    return await response.json();
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Load movies with pagination
 * @param {Object} options - Load options
 * @returns {Promise<Object>} Movies data
 */
async function loadMovies(options = {}) {
  const { limit = null, offset = 0 } = options;
  
  try {
    let url = `/api/movies?offset=${offset}`;
    if (limit) {
      url += `&limit=${limit}`;
    }
    
    const response = await fetch(url);
    return await response.json();
  } catch (error) {
    console.error('Error loading movies:', error);
    return { movies: [], total_count: 0, has_more: false };
  }
}
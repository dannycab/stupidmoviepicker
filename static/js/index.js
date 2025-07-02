// Index page specific JavaScript
// Handles movie grid, form interactions, and search functionality

class MovieGridManager {
  constructor() {
    this.currentOffset = 0;
    this.pageSize = 8;
    this.totalMovies = 0;
    this.init();
  }
  
  init() {
    this.setupEventListeners();
    this.loadMovies();
  }
  
  setupEventListeners() {
    // Form toggles
    setupFormToggle('addMovieToggle', 'addMovieSection', 'closeAddForm');
    setupFormToggle('searchMovieToggle', 'searchMovieSection', 'closeSearchForm');
    
    // Load more button
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
      loadMoreBtn.addEventListener('click', () => {
        this.loadMovies(true);
      });
    }
    
    // Add movie form
    const addMovieForm = document.getElementById('addMovieForm');
    if (addMovieForm) {
      addMovieForm.addEventListener('submit', (e) => this.handleAddMovie(e));
    }
    
    // Search form
    const searchForm = document.getElementById('searchMovieForm');
    if (searchForm) {
      searchForm.addEventListener('submit', (e) => this.handleSearch(e));
    }
    
    // Auto-fetch title when URL is entered
    const urlInput = document.getElementById('movieUrl');
    if (urlInput) {
      this.setupAutoTitleFetch(urlInput);
    }
  }
  
  async loadMovies(append = false) {
    try {
      const data = await loadMovies({
        limit: this.pageSize,
        offset: this.currentOffset
      });
      
      const grid = document.getElementById('movieGrid');
      if (!grid) return;
      
      if (!append) {
        grid.innerHTML = '';
        this.currentOffset = 0;
      }
      
      this.totalMovies = data.total_count;
      
      data.movies.forEach(movie => {
        const card = createMovieCard(movie, {
          showDeleteButton: true,
          imageHeight: 'h-48'
        });
        grid.appendChild(card);
      });

      // Update load more button
      const loadMoreBtn = document.getElementById('loadMoreBtn');
      if (loadMoreBtn) {
        if (data.has_more) {
          loadMoreBtn.classList.remove('hidden');
          loadMoreBtn.textContent = `Load More (${data.movies.length + this.currentOffset} of ${this.totalMovies})`;
        } else {
          loadMoreBtn.classList.add('hidden');
        }
      }

      if (append) {
        this.currentOffset += data.movies.length;
      } else {
        this.currentOffset = data.movies.length;
      }
    } catch (error) {
      console.error('Error loading movies:', error);
      showNotification('Error loading movies', 'error');
    }
  }
  
  setupAutoTitleFetch(urlInput) {
    let titleFetchTimeout;
    
    urlInput.addEventListener('input', async (e) => {
      const url = e.target.value.trim();
      const titleInput = document.getElementById('movieTitle');
      
      if (!titleInput) return;
      
      // Clear previous timeout
      if (titleFetchTimeout) {
        clearTimeout(titleFetchTimeout);
      }
      
      if (!url) {
        titleInput.value = '';
        titleInput.placeholder = 'Title will be fetched automatically...';
        titleInput.readOnly = true;
        return;
      }
      
      // Basic YouTube URL validation
      if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
        titleInput.value = '';
        titleInput.placeholder = 'Enter a valid YouTube URL first';
        titleInput.readOnly = true;
        return;
      }
      
      // Debounce the API call
      titleFetchTimeout = setTimeout(async () => {
        titleInput.placeholder = 'Fetching title...';
        titleInput.value = '';
        
        const result = await fetchYouTubeTitle(url);
        
        if (result.success && result.title) {
          titleInput.value = result.title;
          titleInput.readOnly = false;
          titleInput.placeholder = 'Edit title if needed';
        } else {
          titleInput.value = '';
          titleInput.placeholder = `Error: ${result.error || 'Could not fetch title'}`;
          titleInput.readOnly = false;
        }
      }, 1000); // Wait 1 second after user stops typing
    });
  }
  
  async handleAddMovie(e) {
    e.preventDefault();
    
    const title = document.getElementById('movieTitle').value.trim();
    const url = document.getElementById('movieUrl').value.trim();
    
    if (!title || !url) {
      showNotification('Please fill in both title and URL', 'error');
      return;
    }
    
    // Basic YouTube URL validation
    if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
      showNotification('Please enter a valid YouTube URL', 'error');
      return;
    }
    
    const result = await addMovie(title, url);
    
    if (result.success) {
      let message = 'Movie added successfully! 🎬 Fetching genre info and checking age restrictions...';
      if (result.verified) {
        message += ' ✅ URL verified and working.';
      } else if (result.validationMessage) {
        message += ` ⚠️ URL issue: ${result.validationMessage}`;
      }
      showNotification(message, 'success');
      
      document.getElementById('addMovieForm').reset();
      closeSection('addMovieSection');
      this.currentOffset = 0; // Reset pagination
      this.loadMovies(); // Refresh the movie grid
    } else {
      showNotification(`Error: ${result.error}`, 'error');
    }
  }
  
  async handleSearch(e) {
    e.preventDefault();
    
    const query = document.getElementById('searchQuery').value.trim();
    const searchResultsDiv = document.getElementById('searchResults');
    const searchResultsGrid = document.getElementById('searchResultsGrid');
    
    if (!query) return;
    
    // Hide results and show loading
    if (searchResultsDiv) searchResultsDiv.classList.add('hidden');
    if (searchResultsGrid) searchResultsGrid.innerHTML = '';
    
    showNotification('Searching YouTube...', 'info');
    
    try {
      const data = await searchYouTube(query);
      
      if (!data.success || !data.results || data.results.length === 0) {
        showNotification('No results found.', 'warning');
        return;
      }
      
      if (searchResultsDiv) searchResultsDiv.classList.remove('hidden');
      
      data.results.forEach(result => {
        const card = this.createSearchResultCard(result);
        if (searchResultsGrid) searchResultsGrid.appendChild(card);
      });
      
      showNotification(`Found ${data.results.length} results`, 'success');
    } catch (err) {
      showNotification('Error searching YouTube.', 'error');
    }
  }
  
  createSearchResultCard(result) {
    const card = document.createElement('div');
    card.className = 'bg-gray-700 rounded-lg shadow p-3 flex flex-col';
    card.innerHTML = `
      <img src="${result.thumbnail}" alt="${escapeHtml(result.title)}" class="w-full h-40 object-cover rounded mb-2">
      <h4 class="font-semibold text-white mb-1 line-clamp-2">${escapeHtml(result.title)}</h4>
      <a href="${result.url}" target="_blank" class="text-blue-400 text-xs mb-2">View on YouTube</a>
      <button class="import-btn bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 transition text-sm mt-auto" 
              data-title="${encodeURIComponent(result.title)}" 
              data-url="${encodeURIComponent(result.url)}">
        Import
      </button>
    `;
    
    // Add import button listener
    const importBtn = card.querySelector('.import-btn');
    importBtn.addEventListener('click', async () => {
      const title = decodeURIComponent(importBtn.getAttribute('data-title'));
      const url = decodeURIComponent(importBtn.getAttribute('data-url'));
      
      importBtn.disabled = true;
      importBtn.textContent = 'Importing...';
      
      const resp = await importMovieFromSearch(title, url);
      
      if (resp.success) {
        importBtn.textContent = 'Imported!';
        importBtn.classList.remove('bg-green-600');
        importBtn.classList.add('bg-blue-600');
        this.loadMovies(); // Refresh movie grid
        showNotification('Movie imported successfully!', 'success');
      } else {
        importBtn.textContent = 'Error';
        showNotification(resp.error || 'Import failed.', 'error');
      }
      
      setTimeout(() => {
        importBtn.disabled = false;
        importBtn.textContent = 'Import';
        importBtn.classList.remove('bg-blue-600');
        importBtn.classList.add('bg-green-600');
      }, 2000);
    });
    
    return card;
  }
  
  // Public method to refresh the grid (called from deleteMovie)
  refresh() {
    this.loadMovies();
  }
}

// Global function for delete movie (called from movie cards)
async function deleteMovie(movieId, event) {
  await window.movieGridManager.deleteMovieFromGrid(movieId, event);
}

// Extend the MovieGridManager with delete functionality
MovieGridManager.prototype.deleteMovieFromGrid = async function(movieId, event) {
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
      this.loadMovies(); // Refresh the grid
      showNotification('Movie deleted successfully', 'success');
    } else {
      showNotification('Failed to delete movie: ' + (result.error || 'Unknown error'), 'error');
    }
  } catch (error) {
    console.error('Error deleting movie:', error);
    showNotification('Failed to delete movie. Please try again.', 'error');
  }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.movieGridManager = new MovieGridManager();
});

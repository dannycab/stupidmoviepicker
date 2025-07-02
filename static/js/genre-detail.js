// Genre detail page specific JavaScript
// Handles movie display for a specific genre with sorting and pagination

class GenreDetailManager {
  constructor(genreName) {
    this.genreName = genreName;
    this.currentSort = 'title';
    this.currentOrder = 'asc';
    this.currentOffset = 0;
    this.pageSize = 12;
    this.totalMovies = 0;
    this.allMovies = [];
    this.init();
  }
  
  init() {
    this.setupEventListeners();
    this.loadMovies();
  }
  
  setupEventListeners() {
    // Setup hamburger menu for mobile sort controls
    setupHamburgerMenu('mobileSortToggle', 'mobileSortContainer', 'currentSortText');
    
    // Listen for hamburger selections
    const mobileSortContainer = document.getElementById('mobileSortContainer');
    if (mobileSortContainer) {
      mobileSortContainer.addEventListener('hamburgerSelect', (e) => {
        this.setSort(e.detail.value);
      });
    }
    
    // Desktop sort buttons
    const desktopSortButtons = document.querySelectorAll('#desktopSortControls .sort-option');
    desktopSortButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        this.setSort(btn.getAttribute('data-sort'));
      });
    });

    // Desktop order toggle
    const orderBtn = document.getElementById('toggleOrder');
    if (orderBtn) {
      orderBtn.addEventListener('click', () => {
        this.toggleOrder();
      });
    }

    // Mobile order toggle
    const mobileOrderBtn = document.getElementById('mobileToggleOrder');
    if (mobileOrderBtn) {
      mobileOrderBtn.addEventListener('click', () => {
        this.toggleOrder();
      });
    }

    // Load more button
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
      loadMoreBtn.addEventListener('click', () => {
        this.loadMoreMovies();
      });
    }
  }
  
  async loadMovies() {
    try {
      // Optionally, show a subtle loading indicator (not a notification)
      const params = new URLSearchParams({
        sort_by: this.currentSort,
        order: this.currentOrder
      });
      const response = await fetch(`/api/movies-by-genre/${encodeURIComponent(this.genreName)}?${params.toString()}`);
      const data = await response.json();
      
      if (data.success) {
        this.allMovies = data.movies;
        this.totalMovies = data.movies.length;
        this.currentOffset = 0;
        this.displayMovies();
        // Optionally, show a success notification (or remove for less noise)
        // showNotification(`Loaded ${this.totalMovies} movies`, 'success');
      } else {
        this.showError(data.error || 'Failed to load movies for this genre');
      }
    } catch (error) {
      this.showError('Error loading movies: ' + error.message);
    }
  }
  
  setSort(sortBy) {
    if (this.currentSort === sortBy) return;
    this.currentSort = sortBy;
    // Update active state for desktop buttons
    const desktopButtons = document.querySelectorAll('#desktopSortControls .sort-option');
    desktopButtons.forEach(btn => {
      if (btn.getAttribute('data-sort') === sortBy) {
        btn.classList.remove('bg-gray-600');
        btn.classList.add('bg-blue-600', 'active');
      } else {
        btn.classList.remove('bg-blue-600', 'active');
        btn.classList.add('bg-gray-600');
      }
    });
    // Update active state for mobile buttons
    const mobileButtons = document.querySelectorAll('#mobileSortContainer .sort-option');
    mobileButtons.forEach(btn => {
      if (btn.getAttribute('data-sort') === sortBy || btn.getAttribute('data-value') === sortBy) {
        btn.classList.remove('bg-gray-600');
        btn.classList.add('bg-blue-600', 'active');
      } else {
        btn.classList.remove('bg-blue-600', 'active');
        btn.classList.add('bg-gray-600');
      }
    });
    this.loadMovies(); // Reload with new sort
  }

  toggleOrder() {
    this.currentOrder = this.currentOrder === 'asc' ? 'desc' : 'asc';
    // Update order text/icons
    const orderText = document.getElementById('orderText');
    if (orderText) orderText.textContent = this.currentOrder === 'asc' ? 'Ascending' : 'Descending';
    const mobileOrderText = document.getElementById('mobileOrderText');
    if (mobileOrderText) mobileOrderText.textContent = this.currentOrder === 'asc' ? 'Ascending' : 'Descending';
    // Optionally update icons here
    this.loadMovies();
  }
  
  displayMovies() {
    const movieGrid = document.getElementById('movieGrid');
    if (!movieGrid) return;
    
    // Clear existing movies
    movieGrid.innerHTML = '';
    
    if (this.allMovies.length === 0) {
      this.showNoMovies();
      return;
    }
    
    // Show first page of movies
    const moviesToShow = this.allMovies.slice(0, this.pageSize);
    this.currentOffset = moviesToShow.length;
    
    moviesToShow.forEach(movie => {
      const card = createMovieCard(movie, {
        showDeleteButton: false,
        imageHeight: 'h-48'
      });
      movieGrid.appendChild(card);
    });
    
    this.updateLoadMoreButton();
    this.updateMovieCount();
  }
  
  loadMoreMovies() {
    const movieGrid = document.getElementById('movieGrid');
    if (!movieGrid) return;
    
    const nextMovies = this.allMovies.slice(this.currentOffset, this.currentOffset + this.pageSize);
    
    nextMovies.forEach(movie => {
      const card = createMovieCard(movie, {
        showDeleteButton: false,
        imageHeight: 'h-48'
      });
      movieGrid.appendChild(card);
    });
    
    this.currentOffset += nextMovies.length;
    this.updateLoadMoreButton();
    this.updateMovieCount();
  }
  
  updateLoadMoreButton() {
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (!loadMoreBtn) return;
    
    if (this.currentOffset < this.allMovies.length) {
      loadMoreBtn.classList.remove('hidden');
      const remaining = this.allMovies.length - this.currentOffset;
      loadMoreBtn.textContent = `Load More (${remaining} remaining)`;
    } else {
      loadMoreBtn.classList.add('hidden');
    }
  }
  
  updateMovieCount() {
    const movieCount = document.getElementById('movieCount');
    if (movieCount) {
      movieCount.textContent = `Showing ${Math.min(this.currentOffset, this.allMovies.length)} of ${this.allMovies.length} movies`;
    }
  }
  
  showNoMovies() {
    const movieGrid = document.getElementById('movieGrid');
    if (movieGrid) {
      movieGrid.innerHTML = `
        <div class="col-span-full text-center py-8">
          <div class="text-6xl mb-4">🎭</div>
          <h3 class="text-xl font-semibold text-white mb-2">No movies found</h3>
          <p class="text-gray-400">No movies available in the "${this.genreName}" genre.</p>
          <a href="/genres" class="inline-block mt-4 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition duration-200">
            Browse Other Genres
          </a>
        </div>
      `;
    }
    
    // Hide load more button
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
      loadMoreBtn.classList.add('hidden');
    }
  }
  
  showError(message) {
    const movieGrid = document.getElementById('movieGrid');
    if (movieGrid) {
      movieGrid.innerHTML = `
        <div class="col-span-full text-center py-8">
          <div class="text-6xl mb-4">❌</div>
          <h3 class="text-xl font-semibold text-white mb-2">Error</h3>
          <p class="text-gray-400">${message}</p>
          <button onclick="location.reload()" class="inline-block mt-4 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition duration-200">
            Try Again
          </button>
        </div>
      `;
    }
    
    showNotification(message, 'error');
  }
}

// Helper function to get the genre name from the page
function getGenreFromPage() {
  // Try to get from page title or URL
  const titleElement = document.querySelector('h1');
  if (titleElement) {
    const match = titleElement.textContent.match(/Movies in "([^"]+)"/);
    if (match) {
      return match[1];
    }
  }
  
  // Fallback to URL path
  const pathParts = window.location.pathname.split('/');
  if (pathParts[1] === 'genre' && pathParts[2]) {
    return decodeURIComponent(pathParts[2]);
  }
  
  return 'Unknown';
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  const genreName = getGenreFromPage();
  new GenreDetailManager(genreName);
});

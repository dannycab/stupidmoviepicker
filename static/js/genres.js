// Genres page specific JavaScript
// Handles genre filtering and movie display by genre

class GenreManager {
  constructor() {
    this.allMoviesWithGenres = [];
    this.currentGenre = 'all';
    this.init();
  }
  
  init() {
    this.setupEventListeners();
    this.loadMoviesWithGenres();
  }
  
  setupEventListeners() {
    // Setup hamburger menu for mobile genre filters
    setupHamburgerMenu('mobileGenreToggle', 'mobileGenreFilters', 'currentGenreText');
    
    // Listen for hamburger selections
    const mobileGenreFilters = document.getElementById('mobileGenreFilters');
    if (mobileGenreFilters) {
      mobileGenreFilters.addEventListener('hamburgerSelect', (e) => {
        this.setGenre(e.detail.value);
      });
    }
  }
  
  async loadMoviesWithGenres() {
    try {
      const response = await fetch('/api/movies-with-genres');
      const data = await response.json();
      
      if (data.success) {
        this.allMoviesWithGenres = data.movies;
        this.populateGenreFilters();
        this.displayMoviesByGenre();
      } else {
        this.showError('Failed to load movies with genre information');
      }
    } catch (error) {
      this.showError('Error loading movies: ' + error.message);
    }
  }
  
  populateGenreFilters() {
    const genreSet = new Set();
    
    this.allMoviesWithGenres.forEach(movie => {
      if (movie.genre && movie.genre !== 'N/A') {
        // Split multiple genres and add each one
        movie.genre.split(/[,;|]/).forEach(genre => {
          const trimmedGenre = genre.trim();
          if (trimmedGenre && trimmedGenre.toLowerCase() !== 'n/a') {
            genreSet.add(trimmedGenre);
          }
        });
      }
    });
    
    const sortedGenres = Array.from(genreSet).sort();
    
    // Populate desktop filters
    const desktopFilters = document.getElementById('desktopGenreFilters');
    if (desktopFilters) {
      this.populateGenreButtons(desktopFilters, sortedGenres, false);
    }
    
    // Populate mobile filters
    const mobileFilters = document.querySelector('#mobileGenreFilters .mobile-genre-filters');
    if (mobileFilters) {
      this.populateGenreButtons(mobileFilters, sortedGenres, true);
    }
  }
  
  populateGenreButtons(container, genres, isMobile) {
    // Keep the "All Genres" button and clear others
    const allButton = container.querySelector('[data-genre="all"]');
    const existingButtons = container.querySelectorAll('.genre-filter:not([data-genre="all"])');
    existingButtons.forEach(btn => btn.remove());
    
    genres.forEach(genre => {
      const button = document.createElement('button');
      button.className = 'genre-filter bg-gray-600 text-white px-3 py-2 rounded-md hover:bg-gray-500 transition duration-200';
      button.setAttribute('data-genre', genre);
      button.textContent = genre;
      
      if (!isMobile) {
        button.addEventListener('click', () => this.setGenre(genre));
      } else {
        button.setAttribute('data-value', genre);
      }
      
      container.appendChild(button);
    });
  }
  
  setGenre(genre) {
    this.currentGenre = genre;
    
    // Update active state for desktop buttons
    const desktopButtons = document.querySelectorAll('#desktopGenreFilters .genre-filter');
    desktopButtons.forEach(btn => {
      if (btn.getAttribute('data-genre') === genre) {
        btn.classList.remove('bg-gray-600');
        btn.classList.add('bg-blue-600', 'active');
      } else {
        btn.classList.remove('bg-blue-600', 'active');
        btn.classList.add('bg-gray-600');
      }
    });
    
    // Update active state for mobile buttons
    const mobileButtons = document.querySelectorAll('#mobileGenreFilters .genre-filter');
    mobileButtons.forEach(btn => {
      if (btn.getAttribute('data-genre') === genre || btn.getAttribute('data-value') === genre) {
        btn.classList.remove('bg-gray-600');
        btn.classList.add('bg-blue-600', 'active');
      } else {
        btn.classList.remove('bg-blue-600', 'active');
        btn.classList.add('bg-gray-600');
      }
    });
    
    this.displayMoviesByGenre();
  }
  
  displayMoviesByGenre() {
    const genreContent = document.getElementById('genreContent');
    if (!genreContent) return;
    
    let filteredMovies;
    
    if (this.currentGenre === 'all') {
      filteredMovies = this.allMoviesWithGenres;
    } else {
      filteredMovies = this.allMoviesWithGenres.filter(movie => {
        if (!movie.genre || movie.genre === 'N/A') return false;
        
        // Check if the movie's genre contains the selected genre
        const movieGenres = movie.genre.split(/[,;|]/).map(g => g.trim().toLowerCase());
        return movieGenres.includes(this.currentGenre.toLowerCase());
      });
    }
    
    if (filteredMovies.length === 0) {
      genreContent.innerHTML = `
        <div class="text-center py-8">
          <div class="text-6xl mb-4">🎭</div>
          <h3 class="text-xl font-semibold text-white mb-2">No movies found</h3>
          <p class="text-gray-400">
            ${this.currentGenre === 'all' 
              ? 'No movies with genre information available.' 
              : `No movies found in the "${this.currentGenre}" genre.`}
          </p>
        </div>
      `;
      return;
    }
    
    // Group movies by genre for display
    const genreGroups = this.groupMoviesByGenre(filteredMovies);
    
    genreContent.innerHTML = '';
    
    if (this.currentGenre === 'all') {
      // Show all genres with their movies
      Object.entries(genreGroups).forEach(([genre, movies]) => {
        this.createGenreSection(genreContent, genre, movies);
      });
    } else {
      // Show only the selected genre
      this.createGenreSection(genreContent, this.currentGenre, filteredMovies, true);
    }
  }
  
  groupMoviesByGenre(movies) {
    const groups = {};
    
    movies.forEach(movie => {
      if (!movie.genre || movie.genre === 'N/A') {
        if (!groups['Unknown']) groups['Unknown'] = [];
        groups['Unknown'].push(movie);
        return;
      }
      
      // Split multiple genres
      const genres = movie.genre.split(/[,;|]/).map(g => g.trim());
      genres.forEach(genre => {
        if (genre && genre.toLowerCase() !== 'n/a') {
          if (!groups[genre]) groups[genre] = [];
          groups[genre].push(movie);
        }
      });
    });
    
    return groups;
  }
  
  createGenreSection(container, genre, movies, isFiltered = false) {
    const section = document.createElement('div');
    section.className = 'mb-8';

    const header = document.createElement('div');
    header.className = 'flex items-center justify-between mb-4';
    header.innerHTML = `
      <h2 class="text-2xl font-bold text-white">${genre} (${movies.length})</h2>
      ${isFiltered ? `
        <a href="/genre/${encodeURIComponent(genre)}" class="btn btn-gray ml-2">View All</a>
      ` : `
        <a href="/genre/${encodeURIComponent(genre)}" 
           class="mobile-btn bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition duration-200 text-sm">
          View All →
        </a>
      `}
    `;

    const grid = document.createElement('div');
    grid.className = 'mobile-movie-grid grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6';

    // Show up to 8 movies per genre when showing all, or all movies when filtered
    const moviesToShow = isFiltered ? movies : movies.slice(0, 8);

    moviesToShow.forEach(movie => {
      const card = createMovieCard(movie, {
        showDeleteButton: false,
        imageHeight: 'h-48'
      });
      grid.appendChild(card);
    });

    section.appendChild(header);
    section.appendChild(grid);

    if (!isFiltered && movies.length > 8) {
      const seeMore = document.createElement('div');
      seeMore.className = 'text-center mt-4';
      seeMore.innerHTML = `
        <a href="/genre/${encodeURIComponent(genre)}" 
           class="text-blue-400 hover:text-blue-300 text-sm">
          See all ${movies.length} movies in ${genre} →
        </a>
      `;
      section.appendChild(seeMore);
    }

    container.appendChild(section);
  }
  
  showError(message) {
    const genreContent = document.getElementById('genreContent');
    if (genreContent) {
      genreContent.innerHTML = `
        <div class="text-center py-8">
          <div class="text-6xl mb-4">❌</div>
          <h3 class="text-xl font-semibold text-white mb-2">Error</h3>
          <p class="text-gray-400">${message}</p>
        </div>
      `;
    }
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new GenreManager();
});

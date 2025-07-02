"""
Test suite for YouTube Movie Picker API endpoints.

Run tests with: pytest tests/
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

# Import the Flask app
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, get_db_connection


@pytest.fixture
def client():
    """Create a test client."""
    # Create a temporary database
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            # Initialize test database
            conn = get_db_connection()
            conn.execute('''
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    verified INTEGER DEFAULT 0,
                    last_verified TEXT,
                    age_restricted INTEGER DEFAULT 0,
                    age_checked_at TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS movie_info_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    movie_id INTEGER UNIQUE,
                    plot TEXT,
                    year TEXT,
                    director TEXT,
                    actors TEXT,
                    genre TEXT,
                    runtime TEXT,
                    imdb_rating TEXT,
                    poster TEXT,
                    found_with TEXT,
                    cached_at TEXT,
                    FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE
                )
            ''')
            conn.commit()
            conn.close()
        yield client
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


class TestMovieAPI:
    """Test movie-related API endpoints."""
    
    def test_get_movies_empty(self, client):
        """Test getting movies from empty database."""
        response = client.get('/api/movies')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'movies' in data
        assert data['movies'] == []
        assert data['total_count'] == 0
        assert data['has_more'] is False
    
    @patch('app.fetch_movie_info')
    @patch('app.check_age_restriction')
    def test_add_movie(self, mock_age_check, mock_movie_info, client):
        """Test adding a new movie."""
        # Mock external API calls
        mock_movie_info.return_value = (True, {'genre': 'Action', 'year': '2010'})
        mock_age_check.return_value = (False, 'No restrictions')
        
        movie_data = {
            'title': 'Test Movie',
            'url': 'https://youtube.com/watch?v=test123',
            'verified': False
        }
        
        response = client.post('/api/movies', 
                             data=json.dumps(movie_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'id' in data
        assert 'Movie added successfully' in data['message']
    
    def test_add_movie_missing_data(self, client):
        """Test adding movie with missing data."""
        movie_data = {'title': 'Test Movie'}  # Missing URL
        
        response = client.post('/api/movies',
                             data=json.dumps(movie_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing title or url' in data['error']
    
    def test_get_movies_with_pagination(self, client):
        """Test movie pagination."""
        # Add test movies first
        movies = [
            {'title': f'Movie {i}', 'url': f'https://youtube.com/watch?v=test{i}'}
            for i in range(5)
        ]
        
        for movie in movies:
            client.post('/api/movies',
                       data=json.dumps(movie),
                       content_type='application/json')
        
        # Test pagination
        response = client.get('/api/movies?limit=2&offset=0')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['movies']) == 2
        assert data['total_count'] == 5
        assert data['has_more'] is True
    
    def test_delete_movie(self, client):
        """Test deleting a movie."""
        # Add a movie first
        movie_data = {
            'title': 'Movie to Delete',
            'url': 'https://youtube.com/watch?v=delete123'
        }
        
        add_response = client.post('/api/movies',
                                 data=json.dumps(movie_data),
                                 content_type='application/json')
        movie_id = json.loads(add_response.data)['id']
        
        # Delete the movie
        response = client.delete(f'/api/movies/{movie_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert f'Movie {movie_id} deleted' in data['message']


class TestUtilityAPI:
    """Test utility API endpoints."""
    
    @patch('app.fetch_youtube_title')
    def test_fetch_title_success(self, mock_fetch, client):
        """Test successful title fetching."""
        mock_fetch.return_value = (True, 'Test Video Title')
        
        url_data = {'url': 'https://youtube.com/watch?v=test123'}
        response = client.post('/api/fetch-title',
                             data=json.dumps(url_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['title'] == 'Test Video Title'
    
    @patch('app.fetch_youtube_title')
    def test_fetch_title_failure(self, mock_fetch, client):
        """Test failed title fetching."""
        mock_fetch.return_value = (False, 'Could not extract title')
        
        url_data = {'url': 'https://youtube.com/watch?v=invalid'}
        response = client.post('/api/fetch-title',
                             data=json.dumps(url_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'Could not extract title'
    
    @patch('app.validate_url')
    def test_validate_url(self, mock_validate, client):
        """Test URL validation."""
        mock_validate.return_value = (True, 'OK')
        
        url_data = {'url': 'https://youtube.com/watch?v=valid123'}
        response = client.post('/api/validate-url',
                             data=json.dumps(url_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['valid'] is True
        assert data['message'] == 'OK'
    
    def test_random_movie_empty_db(self, client):
        """Test random movie from empty database."""
        response = client.get('/api/random-movie')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'No movies available' in data['error']


class TestAdminAPI:
    """Test admin API endpoints."""
    
    def test_admin_stats(self, client):
        """Test admin statistics endpoint."""
        response = client.get('/api/admin/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        
        stats = data['data']
        expected_keys = [
            'total_movies', 'verified_movies', 'unverified_movies',
            'age_restricted_movies', 'cache_entries'
        ]
        for key in expected_keys:
            assert key in stats
    
    def test_verify_all_movies(self, client):
        """Test bulk movie verification."""
        response = client.post('/api/verify-all-movies')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'background' in data['message']
    
    def test_clear_all_cache(self, client):
        """Test clearing all cache."""
        response = client.post('/api/admin/clear-all-cache')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'cleared successfully' in data['message']


class TestMovieInfo:
    """Test movie information endpoints."""
    
    def test_movie_info_not_found(self, client):
        """Test movie info for non-existent movie."""
        response = client.get('/api/movie-info/999')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Movie not found' in data['error']
    
    def test_clear_cache_success(self, client):
        """Test clearing cache for specific movie."""
        # Add a movie first
        movie_data = {
            'title': 'Cache Test Movie',
            'url': 'https://youtube.com/watch?v=cache123'
        }
        
        add_response = client.post('/api/movies',
                                 data=json.dumps(movie_data),
                                 content_type='application/json')
        movie_id = json.loads(add_response.data)['id']
        
        # Clear cache
        response = client.post(f'/api/clear-cache/{movie_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert f'Cache cleared for movie {movie_id}' in data['message']


class TestErrorHandling:
    """Test error handling."""
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post('/api/movies',
                             data='invalid json',
                             content_type='application/json')
        
        # Should handle gracefully (exact response depends on implementation)
        assert response.status_code in [400, 500]
    
    def test_missing_content_type(self, client):
        """Test handling of missing content type."""
        movie_data = {'title': 'Test', 'url': 'https://youtube.com/watch?v=test'}
        
        response = client.post('/api/movies',
                             data=json.dumps(movie_data))
        
        # Should handle gracefully
        assert response.status_code in [200, 400]


if __name__ == '__main__':
    pytest.main([__file__])

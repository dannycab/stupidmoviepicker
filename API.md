# 📡 API Documentation

Complete REST API documentation for YouTube Movie Picker. The API provides programmatic access to all movie management and discovery features.

## 🔗 Base URL

```
http://localhost:5000
```

## 📋 Interactive Documentation

Visit `/api/docs/` for interactive Swagger documentation with live testing capabilities.

## 🔐 Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## 📊 Response Format

All API responses follow this standard format:

### Success Response
```json
{
  "success": true,
  "data": { ... },          // Response data (varies by endpoint)
  "message": "Optional message"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "code": 400               // HTTP status code
}
```


## 🎬 Movies API

### Search YouTube for Movies
Search YouTube for movies using web scraping or the official API.

**Endpoint:** `POST /api/search-youtube`

**Request Body:**
```json
{
  "query": "The Matrix 1999",
  "max_results": 10,      // Optional, default 10
  "use_api": false        // Optional, default false
}
```

**Example Response:**
```json
{
  "success": true,
  "results": [
    {
      "video_id": "vKQi3bBA1y8",
      "title": "The Matrix (1999) - Full Movie",
      "url": "https://www.youtube.com/watch?v=vKQi3bBA1y8",
      "duration": "2:16:00",
      "thumbnail": "https://img.youtube.com/vi/vKQi3bBA1y8/0.jpg",
      "channel": "Movie Channel",
      "has_full_movie": true
    }
  ],
  "search_method": "scraping",
  "total_found": 1,
  "query": "The Matrix 1999"
}
```

### Import Movie from YouTube Search
Add a movie to the library from YouTube search results with automatic title extraction and validation.

**Endpoint:** `POST /api/import-from-search`

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=vKQi3bBA1y8",
  "title": "The Matrix (1999)",      // Optional
  "auto_verify": true,              // Optional, default true
  "fetch_metadata": true            // Optional, default true
}
```

**Example Response:**
```json
{
  "success": true,
  "movie_id": 44,
  "title": "The Matrix (1999)",
  "url": "https://www.youtube.com/watch?v=vKQi3bBA1y8",
  "title_extracted": true,
  "extracted_title": "The Matrix (1999)",
  "verified": true,
  "age_restricted": false,
  "message": "Movie imported successfully! OMDb metadata is being fetched in background.",
  "warnings": []
}
```

### Get All Movies
Retrieve a paginated list of all movies.

**Endpoint:** `GET /api/movies`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | all | Number of movies to return |
| `offset` | integer | No | 0 | Number of movies to skip |

**Example Request:**
```bash
curl "http://localhost:5000/api/movies?limit=10&offset=0"
```

**Example Response:**
```json
{
  "movies": [
    {
      "id": 1,
      "title": "The Matrix (1999)",
      "url": "https://www.youtube.com/watch?v=vKQi3bBA1y8",
      "verified": 1,
      "last_verified": "2025-01-15T10:30:00",
      "age_restricted": 0,
      "age_checked_at": "2025-01-15T10:30:00"
    }
  ],
  "total_count": 42,
  "has_more": true
}
```

### Add New Movie
Create a new movie entry.

**Endpoint:** `POST /api/movies`

**Request Body:**
```json
{
  "title": "Movie Title",
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "verified": false          // Optional, defaults to false
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/movies" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Inception (2010)",
    "url": "https://www.youtube.com/watch?v=YoHD9XEInc0"
  }'
```

**Example Response:**
```json
{
  "success": true,
  "id": 43,
  "message": "Movie added successfully! OMDb info and age restrictions are being checked in the background."
}
```

### Update Movie
Update an existing movie's information.

**Endpoint:** `PUT /api/movies/{movie_id}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `movie_id` | integer | Yes | Unique movie identifier |

**Request Body:**
```json
{
  "title": "Updated Movie Title",
  "url": "https://www.youtube.com/watch?v=NEW_VIDEO_ID",
  "verified": true
}
```

**Example Request:**
```bash
curl -X PUT "http://localhost:5000/api/movies/43" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Inception - Directors Cut (2010)",
    "url": "https://www.youtube.com/watch?v=YoHD9XEInc0",
    "verified": true
  }'
```

**Example Response:**
```json
{
  "success": true,
  "message": "Movie 43 updated. Data refresh started in background.",
  "data_refresh_triggered": true
}
```

### Delete Movie
Remove a movie from the database.

**Endpoint:** `DELETE /api/movies/{movie_id}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `movie_id` | integer | Yes | Unique movie identifier |

**Example Request:**
```bash
curl -X DELETE "http://localhost:5000/api/movies/43"
```

**Example Response:**
```json
{
  "success": true,
  "message": "Movie 43 deleted"
}
```

### Get Random Movie
Retrieve a random movie from the database.

**Endpoint:** `GET /api/random-movie`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `verified_only` | string | No | false | If 'true', only return verified movies |

**Example Request:**
```bash
curl "http://localhost:5000/api/random-movie?verified_only=true"
```

**Example Response:**
```json
{
  "success": true,
  "id": 15,
  "title": "The Dark Knight (2008)",
  "url": "https://www.youtube.com/watch?v=EXeTwQWrcwY"
}
```

### Get Movie Information
Retrieve detailed information about a specific movie from OMDb API.

**Endpoint:** `GET /api/movie-info/{movie_id}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `movie_id` | integer | Yes | Unique movie identifier |

**Example Request:**
```bash
curl "http://localhost:5000/api/movie-info/15"
```

**Example Response:**
```json
{
  "success": true,
  "info": {
    "plot": "When the menace known as the Joker wreaks havoc...",
    "year": "2008",
    "director": "Christopher Nolan",
    "actors": "Christian Bale, Heath Ledger, Aaron Eckhart",
    "genre": "Action, Crime, Drama",
    "runtime": "152 min",
    "imdb_rating": "9.0",
    "poster": "https://m.media-amazon.com/images/...",
    "found_with": "The Dark Knight",
    "from_cache": true
  },
  "from_cache": true,
  "searched_title": "The Dark Knight",
  "original_title": "The Dark Knight (2008)"
}
```

### Clear Movie Cache
Remove cached OMDb information for a specific movie.

**Endpoint:** `POST /api/clear-cache/{movie_id}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `movie_id` | integer | Yes | Unique movie identifier |

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/clear-cache/15"
```

**Example Response:**
```json
{
  "success": true,
  "message": "Cache cleared for movie 15"
}
```


## 🎭 Genre API

### Get Movies by Genre
Retrieve movies by genre from cached OMDb data.

**Endpoint:** `GET /api/movies-by-genre/{genre_name}`

**Query Parameters:**
- `sort_by` (string, optional): `title`, `year`, `rating`, `add_date` (default: `title`)
- `order` (string, optional): `asc`, `desc` (default: `asc`)

**Example Request:**
```bash
curl "http://localhost:5000/api/movies-by-genre/Action?sort_by=rating&order=desc"
```

**Example Response:**
```json
{
  "success": true,
  "genre": "Action",
  "movies": [
    {
      "id": 1,
      "title": "The Matrix (1999)",
      "url": "https://www.youtube.com/watch?v=vKQi3bBA1y8",
      "verified": true,
      "last_verified": "2025-01-15T10:30:00",
      "age_restricted": false,
      "age_checked_at": "2025-01-15T10:30:00",
      "genre": "Action, Sci-Fi",
      "year": "1999",
      "imdb_rating": "8.7",
      "poster": "https://m.media-amazon.com/images/..."
    }
  ],
  "total_count": 1
}
```

### Get Movies with Genre Information
Retrieve all movies with their cached genre and metadata information.

**Endpoint:** `GET /api/movies-with-genres`

**Example Request:**
```bash
curl "http://localhost:5000/api/movies-with-genres"
```

**Example Response:**
```json
{
  "success": true,
  "movies": [
    {
      "id": 1,
      "title": "The Matrix (1999)",
      "url": "https://www.youtube.com/watch?v=vKQi3bBA1y8",
      "verified": 1,
      "last_verified": "2025-01-15T10:30:00",
      "age_restricted": 0,
      "age_checked_at": "2025-01-15T10:30:00",
      "genre": "Action, Sci-Fi",
      "year": "1999",
      "imdb_rating": "8.7",
      "director": "Lana Wachowski, Lilly Wachowski",
      "actors": "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss",
      "runtime": "136 min",
      "plot": "A computer programmer is led to fight...",
      "poster": "https://m.media-amazon.com/images/..."
    }
  ]
}
```

## 🛠️ Utility API

### Validate YouTube URL
Check if a YouTube URL is valid and accessible.

**Endpoint:** `POST /api/validate-url`

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/validate-url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=vKQi3bBA1y8"
  }'
```

**Example Response:**
```json
{
  "success": true,
  "valid": true,
  "message": "OK"
}
```

### Fetch YouTube Video Title
Extract the title from a YouTube URL.

**Endpoint:** `POST /api/fetch-title`

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/fetch-title" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=vKQi3bBA1y8"
  }'
```

**Example Response:**
```json
{
  "success": true,
  "title": "The Matrix (1999) - Official Trailer"
}
```

### Verify All Movies
Start background verification of all movie URLs.

**Endpoint:** `POST /api/verify-all-movies`

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/verify-all-movies"
```

**Example Response:**
```json
{
  "success": true,
  "message": "Verification of all movies started in background"
}
```

### Check Age Restrictions
Start background check for age-restricted content on all movies.

**Endpoint:** `POST /api/check-age-restrictions`

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/check-age-restrictions"
```

**Example Response:**
```json
{
  "success": true,
  "message": "Age restriction check started in background",
  "results": []
}
```

## 👨‍💼 Admin API

### Get Admin Statistics
Retrieve comprehensive statistics about the movie database.

**Endpoint:** `GET /api/admin/stats`

**Example Request:**
```bash
curl "http://localhost:5000/api/admin/stats"
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "total_movies": 150,
    "verified_movies": 142,
    "unverified_movies": 8,
    "age_restricted_movies": 5,
    "cache_entries": 135,
    "oldest_cache": "2025-01-10T15:22:00",
    "last_verification": "2025-01-15T10:30:00",
    "last_age_check": "2025-01-15T09:15:00"
  }
}
```

### Clear All Cache
Remove all cached OMDb information from the database.

**Endpoint:** `POST /api/admin/clear-all-cache`

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/admin/clear-all-cache"
```

**Example Response:**
```json
{
  "success": true,
  "message": "All cache cleared successfully"
}
```

### Refresh All Cache
Start background refresh of all cached movie information.

**Endpoint:** `POST /api/admin/refresh-all-cache`

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/admin/refresh-all-cache"
```

**Example Response:**
```json
{
  "success": true,
  "message": "Cache refresh started in background"
}
```

## 📄 Web Routes

### Main Application Routes
These routes serve HTML pages for the web interface:

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Main movie grid page |
| `/movie/{movie_id}` | GET | Individual movie detail page |
| `/admin` | GET | Admin dashboard |
| `/genres` | GET | Genre browsing page |
| `/random` | GET | Redirect to random movie page |
| `/docs` | GET | Redirect to API documentation |
| `/api/docs/` | GET | Interactive Swagger API documentation |

### Movie Actions
| Route | Method | Description |
|-------|--------|-------------|
| `/movie/{movie_id}/verify` | POST | Mark movie as manually verified |

## ❌ Error Codes

| HTTP Code | Description |
|-----------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters or missing required fields |
| 404 | Not Found - Movie or resource doesn't exist |
| 500 | Internal Server Error - Server-side error occurred |

## 📝 Data Models

### Movie Object
```json
{
  "id": 1,                                    // Unique identifier
  "title": "Movie Title",                     // Movie title
  "url": "https://youtube.com/watch?v=...",  // YouTube URL
  "verified": 1,                             // 0 or 1, URL verification status
  "last_verified": "2025-01-15T10:30:00",   // ISO timestamp or null
  "age_restricted": 0,                       // 0 or 1, age restriction status
  "age_checked_at": "2025-01-15T10:30:00"   // ISO timestamp or null
}
```

### Movie Info Object (OMDb Data)
```json
{
  "plot": "Movie plot description",
  "year": "2008",
  "director": "Director Name",
  "actors": "Actor 1, Actor 2, Actor 3",
  "genre": "Action, Drama",
  "runtime": "152 min",
  "imdb_rating": "8.5",
  "poster": "https://image-url.com/poster.jpg",
  "found_with": "Search term used",
  "cached_at": "2025-01-15T10:30:00",
  "from_cache": true
}
```

## 🔄 Rate Limiting

The API implements intelligent rate limiting for external service calls:

- **YouTube API calls**: 0.1 second delay between requests
- **OMDb API calls**: 1 second delay between requests for batch operations
- **Background operations**: Automatic throttling to prevent service overload

## 🎯 Usage Examples

### JavaScript/Node.js
```javascript
// Add a new movie
const response = await fetch('http://localhost:5000/api/movies', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    title: 'Inception (2010)',
    url: 'https://www.youtube.com/watch?v=YoHD9XEInc0'
  })
});

const result = await response.json();
console.log(result);
```

### Python
```python
import requests

# Get random movie
response = requests.get('http://localhost:5000/api/random-movie')
movie = response.json()

if movie['success']:
    print(f"Random movie: {movie['title']}")
    print(f"Watch at: {movie['url']}")
```

### Bash/Shell
```bash
#!/bin/bash

# Get admin statistics
curl -s "http://localhost:5000/api/admin/stats" | jq '.data'

# Add multiple movies from a list
while IFS=',' read -r title url; do
  curl -X POST "http://localhost:5000/api/movies" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"$title\",\"url\":\"$url\"}"
  sleep 1
done < movies.csv
```

## 🔍 Testing the API

### Using curl
```bash
# Test basic connectivity
curl "http://localhost:5000/api/admin/stats"

# Test adding a movie
curl -X POST "http://localhost:5000/api/movies" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Movie","url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Using the Web Interface
1. Visit `http://localhost:5000/api/docs/` for interactive testing
2. Use the "Try it out" buttons to test endpoints
3. View request/response examples

## 📞 Support

For API questions or issues:

1. Check the interactive documentation at `/api/docs/`
2. Review this documentation for examples
3. Check [GitHub Issues](https://github.com/your-username/YTMoviePicker/issues)
4. Create a new issue with API-specific details

---

This API documentation is automatically kept in sync with the application. For the most up-to-date interactive documentation, always refer to `/api/docs/` when the application is running.

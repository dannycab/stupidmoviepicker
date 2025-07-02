from dotenv import load_dotenv
load_dotenv()

import re
import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import sqlite3
import random
import threading
import requests
from urllib.parse import urlparse, quote_plus
from datetime import datetime
import time
from flasgger import Swagger, swag_from
import json

# Authentication imports
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from auth import User, UserManager
from forms import LoginForm, RegistrationForm, ProfileForm, ChangePasswordForm


# Database file path - unified logic for Docker and local development
def get_db_path():
    """Get the appropriate database path"""
    # Check for Docker environment first
    if os.path.exists('/app/data'):
        data_dir = '/app/data'
        print(f"🐳 Docker environment detected - using {data_dir}")
    elif os.path.exists('./data'):
        data_dir = './data'
        print(f"📁 Local data directory found - using {data_dir}")
    else:
        data_dir = '.'
        print(f"📂 Using current directory for database - {data_dir}")
    
    db_path = os.path.join(data_dir, 'movies.db')
    print(f"🗄️ Database path: {db_path}")
    return db_path


# One-time migration: add last_verified column if not exists
def migrate_db():
    # Use the unified database path
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if movies table exists first
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
    if not cursor.fetchone():
        print("Movies table doesn't exist. Database needs to be initialized first.")
        conn.close()
        return
    
    # Check and add last_verified column
    cursor.execute("PRAGMA table_info(movies)")
    columns = [col[1] for col in cursor.fetchall()]
    if "last_verified" not in columns:
        cursor.execute("ALTER TABLE movies ADD COLUMN last_verified TEXT")
        conn.commit()
        
        # For existing movies without last_verified, run a quick verification
        print("Running initial verification for existing movies...")
        movies = cursor.execute('SELECT id, url FROM movies WHERE last_verified IS NULL').fetchall()
        for movie in movies:
            is_valid, _ = validate_url(movie[1])
            if is_valid:
                last_verified = datetime.now().isoformat()
                cursor.execute('UPDATE movies SET verified = 1, last_verified = ? WHERE id = ?', 
                             (last_verified, movie[0]))
        conn.commit()
        print(f"✅ Verified {len(movies)} existing movies")
    
    # Check and add age_restricted column
    if "age_restricted" not in columns:
        cursor.execute("ALTER TABLE movies ADD COLUMN age_restricted INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE movies ADD COLUMN age_checked_at TEXT")
        conn.commit()
        print("✅ Added age restriction tracking columns")
    
    # Create movie_info cache table
    cursor.execute('''
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
    print("✅ Movie info cache table ready")
    
    conn.close()

# Initialize database if it doesn't exist
def init_db_if_needed():
    """Initialize the database if it doesn't exist"""
    # Use the unified database path
    db_path = get_db_path()
    data_dir = os.path.dirname(db_path)
    
    # Ensure data directory exists and is writable
    if not os.path.exists(data_dir) and data_dir != '.':
        try:
            os.makedirs(data_dir, exist_ok=True)
            print(f"Created data directory: {data_dir}")
        except PermissionError:
            print(f"❌ Permission denied creating {data_dir}, falling back to current directory")
            db_path = 'movies.db'
    
    # Check if database file exists and has tables
    if not os.path.exists(db_path):
        print(f"Database doesn't exist at {db_path}. Initializing...")
        try:
            # Set the DB_PATH environment variable for init_db.py
            os.environ['DB_PATH'] = db_path
            exec(open('init_db.py').read())
            print(f"✅ Database initialized successfully at {db_path}")
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            raise
    else:
        # Check if movies table exists
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
            if not cursor.fetchone():
                print("Database exists but movies table is missing. Reinitializing...")
                conn.close()
                os.environ['DB_PATH'] = db_path
                exec(open('init_db.py').read())
                print(f"✅ Database reinitialized successfully at {db_path}")
            else:
                conn.close()
                print(f"✅ Database already exists at {db_path}")
        except Exception as e:
            print(f"❌ Error checking database: {e}")
            raise

# Initialize database first
init_db_if_needed()

# Run migrations
migrate_db()


app = Flask(__name__, template_folder="templates")

# Initialize Swagger for API documentation
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "YouTube Movie Picker API",
        "description": "API for managing and discovering YouTube movies",
        "version": "1.0.0",
        "contact": {
            "name": "YouTube Movie Picker",
            "url": "https://github.com/your-repo/YTMoviePicker"
        }
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": ["http", "https"],
    "tags": [
        {
            "name": "movies",
            "description": "Movie management operations"
        },
        {
            "name": "admin",
            "description": "Administrative operations"
        },
        {
            "name": "utility",
            "description": "Utility operations"
        }
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Flask app configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['WTF_CSRF_ENABLED'] = True

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.get(user_id)

# Database connection
def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

# Fetch all movies (user-scoped)
def fetch_all_movies(user_id=None):
    conn = get_db_connection()
    if user_id:
        movies = conn.execute('SELECT * FROM movies WHERE user_id = ?', (user_id,)).fetchall()
    else:
        # For admin or when no user specified, get all movies
        movies = conn.execute('SELECT * FROM movies').fetchall()
    conn.close()
    return [dict(movie) for movie in movies]

# Add a new movie (user-scoped)
def add_movie(title, url, verified=False, user_id=None):
    conn = get_db_connection()
    cur = conn.cursor()
    last_verified = datetime.now().isoformat() if verified else None
    cur.execute('INSERT INTO movies (title, url, verified, last_verified, user_id) VALUES (?, ?, ?, ?, ?)', 
                (title, url, int(verified), last_verified, user_id))
    conn.commit()
    movie_id = cur.lastrowid
    conn.close()
    return movie_id

# Update a movie
def update_movie(movie_id, title, url, verified):
    conn = get_db_connection()
    last_verified = datetime.now().isoformat() if verified else None
    conn.execute('UPDATE movies SET title = ?, url = ?, verified = ?, last_verified = ? WHERE id = ?', 
                 (title, url, int(verified), last_verified, movie_id))
    conn.commit()
    conn.close()

# Cache movie information
def save_movie_info_cache(movie_id, movie_info):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete existing cache for this movie
        cursor.execute('DELETE FROM movie_info_cache WHERE movie_id = ?', (movie_id,))
        
        # Insert new cache
        cursor.execute('''
            INSERT INTO movie_info_cache 
            (movie_id, plot, year, director, actors, genre, runtime, imdb_rating, poster, found_with, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            movie_id,
            movie_info.get('plot', ''),
            movie_info.get('year', ''),
            movie_info.get('director', ''),
            movie_info.get('actors', ''),
            movie_info.get('genre', ''),
            movie_info.get('runtime', ''),
            movie_info.get('imdb_rating', ''),
            movie_info.get('poster', ''),
            movie_info.get('found_with', ''),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        print(f"💾 Cached movie info for movie ID {movie_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to cache movie info: {e}")
        return False

# Retrieve cached movie information
def get_movie_info_cache(movie_id, max_age_hours=24):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT plot, year, director, actors, genre, runtime, imdb_rating, poster, found_with, cached_at
            FROM movie_info_cache 
            WHERE movie_id = ?
        ''', (movie_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        # Check if cache is still fresh
        cached_at = datetime.fromisoformat(row[9])
        age_hours = (datetime.now() - cached_at).total_seconds() / 3600
        
        if age_hours > max_age_hours:
            print(f"🕒 Cache expired for movie ID {movie_id} (age: {age_hours:.1f} hours)")
            return None
            
        print(f"💾 Using cached info for movie ID {movie_id} (age: {age_hours:.1f} hours)")
        return {
            'plot': row[0],
            'year': row[1],
            'director': row[2],
            'actors': row[3],
            'genre': row[4],
            'runtime': row[5],
            'imdb_rating': row[6],
            'poster': row[7],
            'found_with': row[8],
            'cached_at': row[9],
            'from_cache': True
        }
    except Exception as e:
        print(f"❌ Failed to retrieve cached info: {e}")
        return None

# Update age restriction status
def update_age_restriction_status(movie_id, is_age_restricted):
    """Update the age restriction status for a movie"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        age_checked_at = datetime.now().isoformat()
        cursor.execute(
            'UPDATE movies SET age_restricted = ?, age_checked_at = ? WHERE id = ?',
            (int(is_age_restricted), age_checked_at, movie_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to update age restriction status: {e}")
        return False

# Delete a movie
def delete_movie(movie_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM movies WHERE id = ?', (movie_id,))
    conn.commit()
    conn.close()

# Fetch movie information from OMDb API (IMDb data)
def fetch_movie_info(title, timeout=10):
    debug_info = {
        'search_attempts': [],
        'api_key_present': bool(os.getenv('OMDB_API_KEY')),
        'original_title': title
    }
    
    try:
        # Get API key from environment variable
        api_key = os.getenv('OMDB_API_KEY')
        
        print(f"🔍 Searching for movie: '{title}'")
        print(f"🔑 API Key present: {'Yes' if api_key else 'No'}")
        
        # Try multiple search strategies
        search_titles = [
            title,  # Original title
            title.strip(),  # Remove whitespace
            re.sub(r'\s+', ' ', title),  # Normalize whitespace
            title.replace('&', 'and'),  # Replace & with 'and'
        ]
        
        # Also try without common words that might interfere
        cleaned_title = re.sub(r'\b(movie|film|full|hd|4k|trailer|official)\b', '', title, flags=re.IGNORECASE).strip()
        if cleaned_title and cleaned_title not in search_titles:
            search_titles.append(cleaned_title)
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        for i, search_title in enumerate(search_titles):
            if not search_title.strip():
                continue
                
            attempt_info = {
                'attempt_number': i + 1,
                'search_term': search_title,
                'url': '',
                'status_code': None,
                'response_headers': {},
                'response_data': {},
                'error': None
            }
            
            if api_key:
                api_url = f"http://www.omdbapi.com/?t={search_title}&type=movie&apikey={api_key}"
            else:
                api_url = f"http://www.omdbapi.com/?t={search_title}&type=movie"
            
            attempt_info['url'] = api_url
            print(f"🌐 API Call #{i+1}: {api_url}")
            
            try:
                response = requests.get(api_url, headers=headers, timeout=timeout)
                attempt_info['status_code'] = response.status_code
                attempt_info['response_headers'] = dict(response.headers)
                
                print(f"📡 Response Status: {response.status_code}")
                print(f"📋 Response Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        attempt_info['response_data'] = data
                        print(f"📝 Response Data: {data}")
                        
                        if data.get('Response') == 'True':
                            print(f"✅ Found movie with search term: '{search_title}'")
                            debug_info['search_attempts'].append(attempt_info)
                            return True, {
                                'plot': data.get('Plot', 'No plot available'),
                                'year': data.get('Year', 'Unknown'),
                                'director': data.get('Director', 'Unknown'),
                                'actors': data.get('Actors', 'Unknown'),
                                'genre': data.get('Genre', 'Unknown'),
                                'runtime': data.get('Runtime', 'Unknown'),
                                'imdb_rating': data.get('imdbRating', 'N/A'),
                                'poster': data.get('Poster', ''),
                                'found_with': search_title,
                                'debug_info': debug_info
                            }
                        else:
                            error_msg = data.get('Error', 'Unknown error')
                            attempt_info['error'] = error_msg
                            print(f"❌ Search #{i+1} failed: {error_msg}")
                            
                            # Check for specific error types
                            if 'Invalid API key' in error_msg:
                                debug_info['search_attempts'].append(attempt_info)
                                return False, "Invalid API key. Please check your OMDB_API_KEY environment variable."
                            elif 'Request limit reached' in error_msg:
                                print("🚫 Rate limit reached!")
                                attempt_info['error'] = f"Rate limit reached: {error_msg}"
                            elif 'Too many requests' in error_msg:
                                print("🚫 Too many requests!")
                                attempt_info['error'] = f"Too many requests: {error_msg}"
                            
                    except ValueError as json_error:
                        attempt_info['error'] = f"Invalid JSON response: {json_error}"
                        attempt_info['response_data'] = response.text[:500]  # First 500 chars
                        print(f"❌ Invalid JSON response: {json_error}")
                        print(f"📄 Raw response: {response.text[:200]}")
                        
                elif response.status_code == 401:
                    attempt_info['error'] = "Unauthorized - Invalid API key"
                    print(f"🔐 Unauthorized (401) - Invalid API key")
                    # If we get 401, try without API key as fallback
                    if api_key:
                        print(f"🔄 Trying without API key as fallback...")
                        fallback_url = f"http://www.omdbapi.com/?t={search_title}&type=movie"
                        try:
                            fallback_response = requests.get(fallback_url, headers=headers, timeout=timeout)
                            if fallback_response.status_code == 200:
                                fallback_data = fallback_response.json()
                                if fallback_data.get('Response') == 'True':
                                    print(f"✅ Found movie with fallback (no API key): '{search_title}'")
                                    return True, {
                                        'plot': fallback_data.get('Plot', 'No plot available'),
                                        'year': fallback_data.get('Year', 'Unknown'),
                                        'director': fallback_data.get('Director', 'Unknown'),
                                        'actors': fallback_data.get('Actors', 'Unknown'),
                                        'genre': fallback_data.get('Genre', 'Unknown'),
                                        'runtime': fallback_data.get('Runtime', 'Unknown'),
                                        'imdb_rating': fallback_data.get('imdbRating', 'N/A'),
                                        'poster': fallback_data.get('Poster', ''),
                                        'found_with': f"{search_title} (fallback)",
                                        'debug_info': debug_info,
                                        'note': 'Found using free tier after API key failed'
                                    }
                        except Exception as fallback_error:
                            print(f"❌ Fallback also failed: {fallback_error}")
                elif response.status_code == 429:
                    attempt_info['error'] = "Rate limited (429)"
                    print(f"🚫 Rate limited (429)")
                elif response.status_code >= 500:
                    attempt_info['error'] = f"Server error ({response.status_code})"
                    print(f"💥 Server error ({response.status_code})")
                else:
                    attempt_info['error'] = f"HTTP {response.status_code}: {response.text[:200]}"
                    print(f"❌ HTTP Error {response.status_code}: {response.text[:200]}")
                    
            except requests.exceptions.RequestException as req_error:
                attempt_info['error'] = f"Request exception: {req_error}"
                print(f"🔌 Request error: {req_error}")
                
            debug_info['search_attempts'].append(attempt_info)
            
            # Small delay between requests to be respectful
            time.sleep(0.1)
        
        # Check if all attempts failed due to invalid API key
        invalid_key_attempts = [attempt for attempt in debug_info['search_attempts'] 
                              if attempt.get('status_code') == 401]
        
        if len(invalid_key_attempts) > 0 and api_key:
            print("🔑 API key appears to be invalid or expired")
            return False, f"Invalid or expired API key. Please get a new key from http://www.omdbapi.com/ or remove the OMDB_API_KEY environment variable to use the free tier. Debug info: {debug_info}"
        
        # If no API key, show helpful message
        if not api_key:
            print("⚠️ No API key found - using free tier")
            return False, f"Movie not found. Consider getting a free API key from http://www.omdbapi.com/ for better search results. Debug info: {debug_info}"
        
        print("❌ All search variations failed")
        return False, f"Movie not found after trying {len(search_titles)} search variations. Debug info: {debug_info}"
            
    except requests.exceptions.Timeout:
        print("⏰ Request timeout")
        return False, f"Request timeout. Debug info: {debug_info}"
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error")
        return False, f"Connection error. Debug info: {debug_info}"
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        return False, f"Error: {str(e)}. Debug info: {debug_info}"

# Fetch YouTube video title
def fetch_youtube_title(url, timeout=10):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=timeout)
        
        if response.status_code == 200:
            html = response.text
            
            # Try multiple extraction methods
            patterns = [
                # Standard title tag
                r'<title>(.+?) - YouTube</title>',
                # JSON-LD structured data
                r'"name":"([^"]+)".*?"@type":"VideoObject"',
                # Video title in meta property
                r'<meta property="og:title" content="([^"]+)"',
                # Alternative JSON pattern
                r'"videoDetails":{"videoId":"[^"]+","title":"([^"]+)"',
                # Another JSON pattern
                r'"title":{"runs":\[{"text":"([^"]+)"}',
                # Simpler JSON title pattern
                r'"title":"([^"]+)".*?"lengthSeconds"',
                # YouTube's current structure
                r'<meta name="title" content="([^"]+)"',
            ]
            
            for pattern in patterns:
                title_match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if title_match:
                    title = title_match.group(1)
                    
                    # Clean up HTML entities and unicode escapes
                    title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
                    title = title.replace('\\u0026', '&').replace('\\u003c', '<').replace('\\u003e', '>')
                    
                    # Remove common suffixes that might indicate it's not the actual title
                    if not any(suffix in title.lower() for suffix in ['comments', 'subscribers', 'views', 'likes']):
                        print(f"✅ Extracted title using pattern: {pattern}")
                        print(f"📝 Title: {title}")
                        return True, title
                    else:
                        print(f"⚠️ Skipped suspicious title: {title}")
            
            return False, "Could not extract video title from any pattern"
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except Exception as e:
        return False, f"Error: {str(e)}"

# Check for YouTube age restrictions
def check_age_restriction(url, timeout=10):
    """
    Check if a YouTube video is age-restricted.
    Returns: (is_age_restricted: bool, message: str)
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=timeout)
        
        if response.status_code != 200:
            return False, f"Could not check age restriction (HTTP {response.status_code})"
        
        content = response.text.lower()
        
        # Check for various age restriction indicators
        age_indicators = [
            'this video may be inappropriate for some users',
            'sign in to confirm your age',
            'this video is not available',
            'age-restricted',
            'content warning',
            'age_gated',
            'confirm your age',
            'restricted content',
            'content_age_gate'
        ]
        
        for indicator in age_indicators:
            if indicator in content:
                return True, "Age-restricted content detected"
        
        # Check for embed restrictions (another indicator)
        if 'video is not available' in content or 'private video' in content:
            return True, "Content not publicly available"
            
        return False, "No age restrictions detected"
        
    except requests.exceptions.Timeout:
        return False, "Timeout while checking age restriction"
    except requests.exceptions.ConnectionError:
        return False, "Connection error while checking age restriction"
    except Exception as e:
        return False, f"Error checking age restriction: {str(e)}"

def validate_url(url, timeout=10):
    try:
        parsed = urlparse(url)
        if not parsed.netloc or ('youtube.com' not in parsed.netloc and 'youtu.be' not in parsed.netloc):
            return False, "Invalid YouTube URL format"

        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)

        if response.status_code == 200:
            return True, "OK"
        elif response.status_code == 404:
            return False, "Video not found (404)"
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except Exception as e:
        return False, f"Error: {str(e)}"

# Background URL testing
def test_urls_background():
    conn = get_db_connection()
    movies = conn.execute('SELECT * FROM movies').fetchall()
    for movie in movies:
        is_valid, _ = validate_url(movie['url'])
        last_verified = datetime.now().isoformat()
        conn.execute('UPDATE movies SET verified = ?, last_verified = ? WHERE id = ?', 
                     (int(is_valid), last_verified, movie['id']))
        time.sleep(0.5)
    conn.commit()
    conn.close()

# YouTube Search Functions
def search_youtube_videos(query, max_results=10, timeout=10):
    """
    Search YouTube for videos using web scraping (no API key required)
    Returns: (success: bool, results: list or error_message: str)
    """
    try:
        print(f"🔍 Searching YouTube for: '{query}'")
        
        # Encode the search query for URL
        encoded_query = quote_plus(query + " full movie")
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=timeout)
        
        if response.status_code != 200:
            return False, f"Failed to search YouTube (HTTP {response.status_code})"
        
        html = response.text
        
        # Extract video data from the page
        results = []
        
        # Pattern to match video data in the YouTube search results
        # YouTube embeds video data in JSON within script tags
        video_pattern = r'"videoId":"([^"]+)".*?"title":{"runs":\[{"text":"([^"]+)"}.*?"lengthText":{"simpleText":"([^"]*)"}'
        
        # Alternative patterns for different YouTube layouts
        patterns = [
            # Standard pattern
            r'"videoId":"([^"]+)".*?"title":{"runs":\[{"text":"([^"]+)"}.*?"lengthText":{"simpleText":"([^"]+)"}',
            # Alternative pattern
            r'"videoId":"([^"]+)".*?"title":{"simpleText":"([^"]+)"}.*?"lengthText":{"simpleText":"([^"]+)"}',
            # More flexible pattern
            r'"videoId":"([^"]+)"[^}]*"title":\{"[^}]*"text":"([^"]+)"[^}]*\}[^}]*"lengthText":\{"simpleText":"([^"]+)"',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            if matches:
                print(f"✅ Found {len(matches)} videos using pattern")
                break
        
        if not matches:
            # Try a simpler approach - look for video IDs and titles separately
            video_ids = re.findall(r'"videoId":"([^"]+)"', html)
            titles = re.findall(r'"title":{"runs":\[{"text":"([^"]+)"}', html)
            
            if video_ids and titles:
                matches = list(zip(video_ids, titles, ['Unknown'] * len(video_ids)))
                print(f"✅ Found {len(matches)} videos using fallback method")
            else:
                return False, "Could not extract video information from YouTube search results"
        
        # Process the matches
        seen_video_ids = set()
        for match in matches[:max_results * 2]:  # Get more than needed to filter duplicates
            if len(results) >= max_results:
                break
                
            video_id = match[0]
            title = match[1]
            duration = match[2] if len(match) > 2 else "Unknown"
            
            # Skip duplicates
            if video_id in seen_video_ids:
                continue
            seen_video_ids.add(video_id)
            
            # Skip shorts (typically under 60 seconds)
            if duration and ':' in duration:
                time_parts = duration.split(':')
                if len(time_parts) == 2:  # MM:SS format
                    try:
                        minutes = int(time_parts[0])
                        seconds = int(time_parts[1])
                        total_seconds = minutes * 60 + seconds
                        if total_seconds < 300:  # Skip videos under 5 minutes
                            continue
                    except ValueError:
                        pass
            
            # Clean up title
            title = title.replace('\\u0026', '&').replace('\\u003c', '<').replace('\\u003e', '>')
            title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
            
            # Skip obvious non-movie content
            skip_keywords = ['trailer', 'teaser', 'clip', 'scene', 'behind the scenes', 'review', 'reaction']
            if any(keyword in title.lower() for keyword in skip_keywords):
                continue
            
            # Prefer results with "full movie" in title
            has_full_movie = 'full movie' in title.lower()
            
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            results.append({
                'video_id': video_id,
                'title': title,
                'url': url,
                'duration': duration,
                'thumbnail': f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                'has_full_movie': has_full_movie
            })
        
        # Sort results to prioritize "full movie" titles
        results.sort(key=lambda x: (x['has_full_movie'], x['title']), reverse=True)
        
        print(f"✅ Successfully found {len(results)} video results")
        return True, results
        
    except requests.exceptions.Timeout:
        return False, "Search request timed out"
    except requests.exceptions.ConnectionError:
        return False, "Connection error while searching"
    except Exception as e:
        print(f"❌ YouTube search error: {e}")
        return False, f"Search error: {str(e)}"

def search_youtube_with_api(query, max_results=10):
    """
    Search YouTube using the official API (requires API key)
    Returns: (success: bool, results: list or error_message: str)
    """
    try:
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            return False, "YouTube API key not found. Set YOUTUBE_API_KEY environment variable."
        
        print(f"🔍 Searching YouTube API for: '{query}'")
        
        # YouTube Data API v3 search endpoint
        search_url = "https://www.googleapis.com/youtube/v3/search"
        
        params = {
            'part': 'snippet',
            'q': query + ' full movie',
            'type': 'video',
            'maxResults': max_results,
            'order': 'relevance',
            'videoDuration': 'long',  # Prefer longer videos (likely full movies)
            'key': api_key
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code != 200:
            return False, f"YouTube API error (HTTP {response.status_code})"
        
        data = response.json()
        
        if 'items' not in data:
            return False, "No results found"
        
        results = []
        for item in data['items']:
            video_id = item['id']['videoId']
            title = item['snippet']['title']
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            results.append({
                'video_id': video_id,
                'title': title,
                'url': url,
                'duration': 'Unknown',
                'thumbnail': item['snippet']['thumbnails']['high']['url'],
                'channel': item['snippet']['channelTitle'],
                'published': item['snippet']['publishedAt'],
                'description': item['snippet']['description'][:200] + '...' if len(item['snippet']['description']) > 200 else item['snippet']['description']
            })
        
        print(f"✅ YouTube API found {len(results)} results")
        return True, results
        
    except Exception as e:
        print(f"❌ YouTube API search error: {e}")
        return False, f"API search error: {str(e)}"

# YouTube Search and Import API Endpoints

@app.route('/api/search-youtube', methods=['POST'])
@swag_from({
    'tags': ['movies'],
    'summary': 'Search for movies on YouTube',
    'description': 'Search YouTube for movies using either web scraping or official API',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['query'],
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Movie title or search query',
                    'example': 'The Matrix 1999'
                },
                'max_results': {
                    'type': 'integer',
                    'description': 'Maximum number of results to return',
                    'default': 10,
                    'example': 10
                },
                'use_api': {
                    'type': 'boolean',
                    'description': 'Use YouTube API instead of web scraping (requires YOUTUBE_API_KEY)',
                    'default': False
                }
            }
        }
    }],
    'responses': {
        200: {
            'description': 'Search results',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'video_id': {'type': 'string'},
                                'title': {'type': 'string'},
                                'url': {'type': 'string'},
                                'duration': {'type': 'string'},
                                'thumbnail': {'type': 'string'},
                                'channel': {'type': 'string'},
                                'has_full_movie': {'type': 'boolean'}
                            }
                        }
                    },
                    'search_method': {'type': 'string'},
                    'total_found': {'type': 'integer'}
                }
            }
        },
        400: {
            'description': 'Bad request',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def search_youtube_endpoint():
    """Search for movies on YouTube and return results"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'success': False, 'error': 'Missing query parameter'}), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({'success': False, 'error': 'Query cannot be empty'}), 400
        
        max_results = data.get('max_results', 10)
        use_api = data.get('use_api', False)
        
        print(f"🔍 Searching YouTube for: '{query}' (max_results: {max_results}, use_api: {use_api})")
        
        # Try API first if requested and available
        if use_api:
            success, results = search_youtube_with_api(query, max_results)
            search_method = "YouTube Data API v3"
        else:
            success, results = search_youtube_videos(query, max_results)
            search_method = "Web Scraping"
        
        # If API failed and use_api was True, fall back to scraping
        if not success and use_api:
            print(f"⚠️ API search failed: {results}. Falling back to web scraping...")
            success, results = search_youtube_videos(query, max_results)
            search_method = "Web Scraping (API fallback)"
        
        if not success:
            return jsonify({
                'success': False,
                'error': results,  # results contains error message when success=False
                'search_method': search_method
            }), 400
        
        return jsonify({
            'success': True,
            'results': results,
            'search_method': search_method,
            'total_found': len(results),
            'query': query
        })
        
    except Exception as e:
        print(f"❌ YouTube search endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': f"Search error: {str(e)}"
        }), 500

@app.route('/api/import-from-search', methods=['POST'])
@swag_from({
    'tags': ['movies'],
    'summary': 'Import a movie from YouTube search results',
    'description': 'Add a movie to the library from YouTube search results with automatic title extraction and validation',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['url'],
            'properties': {
                'url': {
                    'type': 'string',
                    'description': 'YouTube URL to import',
                    'example': 'https://www.youtube.com/watch?v=vKQi3bBA1y8'
                },
                'title': {
                    'type': 'string',
                    'description': 'Custom title (optional - will auto-extract if not provided)',
                    'example': 'The Matrix (1999)'
                },
                'auto_verify': {
                    'type': 'boolean',
                    'description': 'Automatically verify the URL before adding',
                    'default': True
                },
                'fetch_metadata': {
                    'type': 'boolean',
                    'description': 'Automatically fetch OMDb metadata in background',
                    'default': True
                }
            }
        }
    }],
    'responses': {
        200: {
            'description': 'Movie imported successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'movie_id': {'type': 'integer'},
                    'title': {'type': 'string'},
                    'url': {'type': 'string'},
                    'title_extracted': {'type': 'boolean'},
                    'verified': {'type': 'boolean'},
                    'age_restricted': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'warnings': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    }
                }
            }
        },
        400: {
            'description': 'Bad request or validation failed',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'error': {'type': 'string'},
                    'details': {'type': 'object'}
                }
            }
        }
    }
})
def import_from_search():
    """Import a movie from YouTube search results into the library"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': 'Missing url parameter'}), 400
        
        url = data['url'].strip()
        if not url:
            return jsonify({'success': False, 'error': 'URL cannot be empty'}), 400
        
        custom_title = data.get('title', '').strip()
        auto_verify = data.get('auto_verify', True)
        fetch_metadata = data.get('fetch_metadata', True)
        
        warnings = []
        extracted_title = None
        
        print(f"🎬 Importing movie from URL: {url}")
        
        # Validate URL format first
        parsed = urlparse(url)
        if not parsed.netloc or ('youtube.com' not in parsed.netloc and 'youtu.be' not in parsed.netloc):
            return jsonify({
                'success': False,
                'error': 'Invalid YouTube URL format',
                'details': {'url': url, 'parsed_netloc': parsed.netloc}
            }), 400
        
        # Extract title if not provided
        title_extracted = False
        if custom_title:
            final_title = custom_title
            print(f"📝 Using custom title: {final_title}")
        else:
            print("🔍 Extracting title from YouTube...")
            title_success, title_result = fetch_youtube_title(url)
            if title_success:
                extracted_title = title_result
                final_title = extracted_title
                title_extracted = True
                print(f"✅ Extracted title: {final_title}")
            else:
                warnings.append(f"Could not extract title: {title_result}")
                # Use a fallback title based on video ID
                if 'youtube.com' in url and 'v=' in url:
                    video_id = url.split('v=')[1].split('&')[0]
                elif 'youtu.be' in url:
                    video_id = url.split('/')[-1].split('?')[0]
                else:
                    video_id = 'unknown'
                final_title = f"YouTube Video {video_id}"
                print(f"⚠️ Using fallback title: {final_title}")
        
        # Verify URL if requested
        verified = False
        if auto_verify:
            print("🔍 Verifying URL...")
            is_valid, validation_message = validate_url(url)
            if is_valid:
                verified = True
                print(f"✅ URL verified: {validation_message}")
            else:
                warnings.append(f"URL validation failed: {validation_message}")
                print(f"⚠️ URL validation failed: {validation_message}")
        
        # Check for age restrictions
        print("🔍 Checking age restrictions...")
        is_age_restricted, age_message = check_age_restriction(url)
        if is_age_restricted:
            warnings.append(f"Age-restricted content: {age_message}")
            print(f"🔞 Age restriction detected: {age_message}")
        else:
            print(f"👍 No age restrictions: {age_message}")
        
        # Check for duplicates
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM movies WHERE url = ?", (url,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Movie with this URL already exists in the library',
                'details': {
                    'existing_id': existing[0],
                    'existing_title': existing[1],
                    'url': url
                }
            }), 400
        
        # Add movie to database
        movie_id = add_movie(final_title, url, verified)
        
        # Update age restriction info
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE movies 
            SET age_restricted = ?, age_checked_at = ? 
            WHERE id = ?
        ''', (int(is_age_restricted), datetime.now().isoformat(), movie_id))
        conn.commit()
        conn.close()
        
        print(f"✅ Movie added with ID: {movie_id}")
        
        # Fetch metadata in background if requested
        if fetch_metadata:
            def fetch_metadata_background():
                try:
                    print(f"🎭 Fetching OMDb metadata for: {final_title}")
                    success, info = fetch_movie_info(final_title)
                    if success and isinstance(info, dict):
                        save_movie_info_cache(movie_id, info)
                        print(f"✅ Cached OMDb info for movie ID {movie_id}")
                    else:
                        print(f"❌ Failed to fetch OMDb info: {info}")
                except Exception as e:
                    print(f"❌ Error fetching metadata: {e}")
            
            thread = threading.Thread(target=fetch_metadata_background)
            thread.daemon = True
            thread.start()
        
        return jsonify({
            'success': True,
            'movie_id': movie_id,
            'title': final_title,
            'url': url,
            'title_extracted': title_extracted,
            'extracted_title': extracted_title,
            'verified': verified,
            'age_restricted': is_age_restricted,
            'message': 'Movie imported successfully!' + (' OMDb metadata is being fetched in background.' if fetch_metadata else ''),
            'warnings': warnings
        })
        
    except Exception as e:
        print(f"❌ Import endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': f"Import error: {str(e)}",
            'details': {'exception_type': type(e).__name__}
        }), 500

# Missing Flask App Routes - need to be added after the existing code

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.verify_password(form.username.data, form.password.data)
        if user:
            login_user(user, remember=form.remember_me.data)
            user.update_last_login()
            flash(f'Welcome back, {user.display_name}!', 'success')
            
            # Redirect to next page or index
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html', title='Sign In', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user, message = User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        
        if user:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(f'Registration failed: {message}', 'error')
    
    return render_template('auth/register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', title='Profile')

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    form = ProfileForm(current_user.email)
    if form.validate_on_submit():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET first_name = ?, last_name = ?, email = ?
            WHERE id = ?
        ''', (form.first_name.data, form.last_name.data, form.email.data, current_user.id))
        conn.commit()
        conn.close()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email.data = current_user.email
    
    return render_template('auth/edit_profile.html', title='Edit Profile', form=form)

@app.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        # Verify current password
        if not check_password_hash(current_user.password_hash, form.current_password.data):
            flash('Current password is incorrect', 'error')
        else:
            # Update password
            new_hash = generate_password_hash(form.new_password.data)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                         (new_hash, current_user.id))
            conn.commit()
            conn.close()
            
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))
    
    return render_template('auth/change_password.html', title='Change Password', form=form)

# Routes
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/docs')
def docs():
    """Redirect to API documentation"""
    return redirect('/api/docs/')

@app.route('/api/movies', methods=['GET'])
def get_movies():
    """Get all movies with pagination
    ---
    tags:
      - movies
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
        description: Number of movies to return (if not specified, returns all)
      - name: offset
        in: query
        type: integer
        default: 0
        description: Number of movies to skip for pagination
    responses:
      200:
        description: List of movies
        schema:
          type: object
          properties:
            movies:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: Unique movie ID
                  title:
                    type: string
                    description: Movie title
                  url:
                    type: string
                    description: YouTube URL
                  verified:
                    type: integer
                    description: Whether the URL has been verified (0 or 1)
                  last_verified:
                    type: string
                    description: ISO timestamp of last verification
                  age_restricted:
                    type: integer
                    description: Whether the content is age-restricted (0 or 1)
                  age_checked_at:
                    type: string
                    description: ISO timestamp of last age restriction check
            total_count:
              type: integer
              description: Total number of movies in database
            has_more:
              type: boolean
              description: Whether there are more movies available
    """
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int, default=0)
    
    conn = get_db_connection()
    if limit:
        movies = conn.execute('SELECT * FROM movies ORDER BY id DESC LIMIT ? OFFSET ?', (limit, offset)).fetchall()
    else:
        # When no limit is specified, use a very large limit to get all remaining records
        movies = conn.execute('SELECT * FROM movies ORDER BY id DESC LIMIT -1 OFFSET ?', (offset,)).fetchall()
    
    # Get total count for pagination info
    total_count = conn.execute('SELECT COUNT(*) FROM movies').fetchone()[0]
    conn.close()
    
    return jsonify({
        'movies': [dict(movie) for movie in movies],
        'total_count': total_count,
        'has_more': (offset + len(movies)) < total_count
    })

@app.route('/api/movies', methods=['POST'])
def create_movie():
    """Add a new movie
    ---
    tags:
      - movies
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
            - url
          properties:
            title:
              type: string
              description: Movie title
              example: "The Matrix (1999)"
            url:
              type: string
              description: YouTube URL
              example: "https://www.youtube.com/watch?v=vKQi3bBA1y8"
            verified:
              type: boolean
              description: Whether the URL has been manually verified
              default: false
    responses:
      200:
        description: Movie added successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            id:
              type: integer
              description: ID of the newly created movie
            message:
              type: string
              example: "Movie added successfully! OMDb info and age restrictions are being checked in the background."
      400:
        description: Bad request - missing required fields
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Missing title or url"
    """
    data = request.get_json()
    title = data.get('title')
    url = data.get('url')
    verified = data.get('verified', False)
    if not title or not url:
        return jsonify({'success': False, 'error': 'Missing title or url'}), 400
    
    # Create the movie first
    movie_id = add_movie(title, url, verified)
    
    # Immediately fetch OMDb info and check age restrictions in background
    def fetch_movie_data_background():
        try:
            print(f"🎬 Fetching movie data for new movie: {title}")
            
            # Fetch OMDb info
            success, info = fetch_movie_info(title)
            if success and isinstance(info, dict):
                save_movie_info_cache(movie_id, info)
                print(f"✅ Cached OMDb info for: {title}")
            else:
                print(f"❌ Failed to fetch OMDb info for: {title}")
            
            # Check age restrictions
            is_age_restricted, message = check_age_restriction(url)
            
            # Update movie with age restriction info
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE movies 
                SET age_restricted = ?, age_checked_at = ? 
                WHERE id = ?
            ''', (int(is_age_restricted), datetime.now().isoformat(), movie_id))
            conn.commit()
            conn.close()
            
            print(f"{'🔞' if is_age_restricted else '👍'} Age restriction check for {title}: {message}")
            
        except Exception as e:
            print(f"❌ Error fetching movie data for {title}: {e}")
    
    # Start background task
    thread = threading.Thread(target=fetch_movie_data_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True, 
        'id': movie_id,
        'message': 'Movie added successfully! OMDb info and age restrictions are being checked in the background.'
    })

@app.route('/api/movies/<int:movie_id>', methods=['PUT'])
def edit_movie(movie_id):
    """Update an existing movie
    ---
    tags:
      - movies
    parameters:
      - name: movie_id
        in: path
        type: integer
        required: true
        description: Unique movie identifier
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
            - url
          properties:
            title:
              type: string
              description: Updated movie title
              example: "The Matrix Reloaded (2003)"
            url:
              type: string
              description: Updated YouTube URL
              example: "https://www.youtube.com/watch?v=kYzz0FSgpSU"
            verified:
              type: boolean
              description: Whether the URL has been manually verified
              default: false
    responses:
      200:
        description: Movie updated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Movie 1 updated. Data refresh started in background."
            data_refresh_triggered:
              type: boolean
              description: Whether background data refresh was triggered
      400:
        description: Bad request - missing required fields
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Missing title or url"
      404:
        description: Movie not found
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Movie not found"
    """
    data = request.get_json()
    title = data.get('title')
    url = data.get('url')
    verified = data.get('verified', False)
    if not title or not url:
        return jsonify({'success': False, 'error': 'Missing title or url'}), 400
    
    # Get the current movie data to check what changed
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title, url FROM movies WHERE id = ?", (movie_id,))
    current_movie = cursor.fetchone()
    conn.close()
    
    if not current_movie:
        return jsonify({'success': False, 'error': 'Movie not found'}), 404
    
    current_title, current_url = current_movie
    title_changed = current_title != title
    url_changed = current_url != url
    
    # Update the movie
    update_movie(movie_id, title, url, verified)
    
    # If title or URL changed, refresh all associated data in background
    if title_changed or url_changed:
        def refresh_movie_data_background():
            try:
                print(f"🔄 Refreshing data for updated movie: {title}")
                
                # Clear existing cache if title changed (since we'll search with new title)
                if title_changed:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM movie_info_cache WHERE movie_id = ?', (movie_id,))
                    conn.commit()
                    conn.close()
                    print(f"🗑️ Cleared cache for movie {movie_id} due to title change")
                
                # Re-fetch OMDb info (especially important if title changed)
                success, info = fetch_movie_info(title)
                if success and isinstance(info, dict):
                    save_movie_info_cache(movie_id, info)
                    print(f"✅ Refreshed OMDb info for: {title}")
                else:
                    print(f"❌ Failed to refresh OMDb info for: {title} - {info}")
                
                # Re-verify URL (especially important if URL changed)
                is_valid, message = validate_url(url)
                if is_valid:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('UPDATE movies SET verified = 1, last_verified = ? WHERE id = ?', 
                                 (datetime.now().isoformat(), movie_id))
                    conn.commit()
                    conn.close()
                    print(f"✅ URL re-verified for: {title}")
                else:
                    print(f"❌ URL verification failed for: {title} - {message}")
                
                # Re-check age restrictions
                is_age_restricted, age_message = check_age_restriction(url)
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE movies 
                    SET age_restricted = ?, age_checked_at = ? 
                    WHERE id = ?
                ''', (int(is_age_restricted), datetime.now().isoformat(), movie_id))
                conn.commit()
                conn.close()
                
                print(f"{'🔞' if is_age_restricted else '👍'} Age restriction re-checked for {title}: {age_message}")
                
            except Exception as e:
                print(f"❌ Error refreshing movie data for {title}: {e}")
        
        # Start background refresh
        thread = threading.Thread(target=refresh_movie_data_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': f'Movie {movie_id} updated. Data refresh started in background.',
            'data_refresh_triggered': True
        })
    else:
        return jsonify({
            'success': True, 
            'message': f'Movie {movie_id} updated',
            'data_refresh_triggered': False
        })

@app.route('/api/movies/<int:movie_id>', methods=['DELETE'])
def remove_movie(movie_id):
    """Delete a movie
    ---
    tags:
      - movies
    parameters:
      - name: movie_id
        in: path
        type: integer
        required: true
        description: Unique movie identifier
    responses:
      200:
        description: Movie deleted successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Movie 1 deleted"
    """
    delete_movie(movie_id)
    return jsonify({'success': True, 'message': f'Movie {movie_id} deleted'})

@app.route('/random')
def random_movie_redirect():
    """Redirect to a random movie detail page"""
    try:
        verified_only = request.args.get('verified_only', 'false').lower() == 'true'
        movies = fetch_all_movies()
        if verified_only:
            movies = [m for m in movies if m['verified']]
        if not movies:
            # If no movies available, redirect to home with error message
            return redirect(url_for('index', error='No movies available'))
        
        # Select a random movie and redirect to its detail page
        movie = random.choice(movies)
        return redirect(url_for('movie_detail', movie_id=movie['id']))
    except Exception as e:
        print(f"❌ Error getting random movie: {e}")
        return redirect(url_for('index', error='Error selecting random movie'))

@app.route('/api/random-movie')
def random_movie():
    """Get a random movie
    ---
    tags:
      - movies
    parameters:
      - name: verified_only
        in: query
        type: string
        required: false
        description: If 'true', only return verified movies
        enum: ['true', 'false']
        default: 'false'
    responses:
      200:
        description: Random movie selected
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            title:
              type: string
              description: Movie title
              example: "The Matrix (1999)"
            url:
              type: string
              description: YouTube URL
              example: "https://www.youtube.com/watch?v=vKQi3bBA1y8"
            id:
              type: integer
              description: Movie ID
              example: 42
      404:
        description: No movies available
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "No movies available"
    """
    verified_only = request.args.get('verified_only', 'false').lower() == 'true'
    movies = fetch_all_movies()
    if verified_only:
        movies = [m for m in movies if m['verified']]
    if not movies:
        return jsonify({'success': False, 'error': 'No movies available'}), 404
    movie = random.choice(movies)
    return jsonify({'success': True, 'title': movie['title'], 'url': movie['url'], 'id': movie['id']})

@app.route('/api/movie-info/<int:movie_id>')
def get_movie_info(movie_id):
    """Get detailed movie information from OMDb API
    ---
    tags:
      - movies
    parameters:
      - name: movie_id
        in: path
        type: integer
        required: true
        description: Unique movie identifier
    responses:
      200:
        description: Movie information retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            info:
              type: object
              properties:
                plot:
                  type: string
                  example: "A computer programmer is led to fight an underground war..."
                year:
                  type: string
                  example: "1999"
                director:
                  type: string
                  example: "Lana Wachowski, Lilly Wachowski"
                actors:
                  type: string
                  example: "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss"
                genre:
                  type: string
                  example: "Action, Sci-Fi"
                runtime:
                  type: string
                  example: "136 min"
                imdb_rating:
                  type: string
                  example: "8.7"
                poster:
                  type: string
                  example: "https://m.media-amazon.com/images/..."
                found_with:
                  type: string
                  example: "The Matrix"
                from_cache:
                  type: boolean
                  example: true
            from_cache:
              type: boolean
              description: Whether data was retrieved from cache
            searched_title:
              type: string
              description: Title used for search
            original_title:
              type: string
              description: Original movie title from database
      404:
        description: Movie not found
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Movie not found"
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM movies WHERE id = ?", (movie_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'success': False, 'error': 'Movie not found'}), 404
    
    # Check cache first
    cached_info = get_movie_info_cache(movie_id)
    if cached_info:
        return jsonify({
            'success': True,
            'info': cached_info,
            'from_cache': True,
            'searched_title': 'N/A (cached)',
            'original_title': row[0]
        })
    
    # Clean up title for better search results, but be less aggressive
    title = row[0]
    original_title = title
    
    # Remove common YouTube suffixes that might interfere with search
    title = re.sub(r'\s*-\s*Official Trailer.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*-\s*Trailer.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*-\s*Full Movie.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\[.*?\]\s*$', '', title)  # Remove [anything] at end
    title = re.sub(r'\s*\(.*?trailer.*?\)\s*$', '', title, flags=re.IGNORECASE)  # Remove (trailer) at end
    
    # Only remove year if it's clearly at the end and in parentheses
    title = re.sub(r'\s*\(19\d{2}\)\s*$', '', title)  # 1900s years
    title = re.sub(r'\s*\(20\d{2}\)\s*$', '', title)  # 2000s years
    
    title = title.strip()
    
    print(f"🔍 No cache found, fetching from API for movie ID {movie_id}")
    success, info = fetch_movie_info(title)
    
    # If successful, cache the result
    if success and isinstance(info, dict):
        save_movie_info_cache(movie_id, info)
        info['from_cache'] = False
    
    return jsonify({
        'success': success,
        'info': info if success else None,
        'error': info if not success else None,
        'searched_title': title,
        'original_title': original_title,
        'from_cache': False
    })

@app.route('/api/clear-cache/<int:movie_id>', methods=['POST'])
def clear_movie_cache(movie_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM movie_info_cache WHERE movie_id = ?', (movie_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Cache cleared for movie {movie_id}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/fetch-title', methods=['POST'])
def fetch_title_endpoint():
    """Extract title from YouTube URL
    ---
    tags:
      - utility
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - url
          properties:
            url:
              type: string
              description: YouTube URL to extract title from
              example: "https://www.youtube.com/watch?v=vKQi3bBA1y8"
    responses:
      200:
        description: Title extraction result
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            title:
              type: string
              description: Extracted video title (null if failed)
              example: "The Matrix (1999) - Official Trailer"
            error:
              type: string
              description: Error message (null if successful)
              example: null
      400:
        description: Bad request - missing URL
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Missing url"
    """
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'success': False, 'error': 'Missing url'}), 400
    
    success, title = fetch_youtube_title(url)
    return jsonify({
        'success': success,
        'title': title if success else None,
        'error': title if not success else None
    })

@app.route('/api/validate-url', methods=['POST'])
def validate_url_endpoint():
    """Validate a YouTube URL
    ---
    tags:
      - utility
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - url
          properties:
            url:
              type: string
              description: YouTube URL to validate
              example: "https://www.youtube.com/watch?v=vKQi3bBA1y8"
    responses:
      200:
        description: URL validation result
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            valid:
              type: boolean
              description: Whether the URL is valid and accessible
            message:
              type: string
              description: Validation result message
              example: "OK"
      400:
        description: Bad request - missing URL
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Missing url"
    """
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'success': False, 'error': 'Missing url'}), 400
    
    is_valid, message = validate_url(url)
    return jsonify({
        'success': True, 
        'valid': is_valid, 
        'message': message
    })

@app.route('/api/verify-all-movies', methods=['POST'])
def verify_all_movies():
    """Start background verification of all movie URLs
    ---
    tags:
      - admin
    responses:
      200:
        description: Verification process started successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Verification of all movies started in background"
    """
    thread = threading.Thread(target=test_urls_background)
    thread.daemon = True
    thread.start()
    return jsonify({'success': True, 'message': 'Verification of all movies started in background'})

@app.route('/api/test-urls', methods=['POST'])
def test_urls():
    thread = threading.Thread(target=test_urls_background)
    thread.daemon = True
    thread.start()
    return jsonify({'success': True, 'message': 'URL testing started'})

@app.route("/movie/<int:movie_id>/verify", methods=['POST'])
def verify_movie(movie_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if movie exists
    cursor.execute("SELECT id FROM movies WHERE id = ?", (movie_id,))
    if not cursor.fetchone():
        conn.close()
        return "Movie not found", 404
    
    # Mark as verified with current timestamp
    last_verified = datetime.now().isoformat()
    cursor.execute("UPDATE movies SET verified = 1, last_verified = ? WHERE id = ?", 
                   (last_verified, movie_id))
    conn.commit()
    conn.close()
    
    # Redirect back to the movie detail page
    return redirect(url_for('movie_detail', movie_id=movie_id))

@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, url, verified, last_verified FROM movies WHERE id = ?", (movie_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return "Movie not found", 404
    movie = {
        "id": row[0],
        "title": row[1],
        "url": row[2],
        "verified": bool(row[3]),
        "last_verified": row[4]
    }
    video_id = ""
    if "youtube.com" in movie["url"]:
        from urllib.parse import urlparse, parse_qs
        q = urlparse(movie["url"])
        video_id = parse_qs(q.query).get("v", [""])[0]
    elif "youtu.be" in movie["url"]:
        video_id = movie["url"].split("/")[-1]
    return render_template("movie_detail.html", movie=movie, video_id=video_id)

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/admin/stats', methods=['GET'])  
def get_admin_stats():
    """Get comprehensive database statistics
    ---
    tags:
      - admin
    responses:
      200:
        description: Statistics retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                total_movies:
                  type: integer
                  description: Total number of movies in database
                  example: 150
                verified_movies:
                  type: integer
                  description: Number of verified movies
                  example: 142
                unverified_movies:
                  type: integer
                  description: Number of unverified movies
                  example: 8
                age_restricted_movies:
                  type: integer
                  description: Number of age-restricted movies
                  example: 5
                cache_entries:
                  type: integer
                  description: Number of cached movie info entries
                  example: 135
                oldest_cache:
                  type: string
                  description: Timestamp of oldest cache entry
                  example: "2025-01-10T15:22:00"
                last_verification:
                  type: string
                  description: Timestamp of last verification
                  example: "2025-01-15T10:30:00"
                last_age_check:
                  type: string
                  description: Timestamp of last age restriction check
                  example: "2025-01-15T09:15:00"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Database error"
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get basic movie statistics
        stats = {}
        stats['total_movies'] = cursor.execute('SELECT COUNT(*) FROM movies').fetchone()[0]
        stats['verified_movies'] = cursor.execute('SELECT COUNT(*) FROM movies WHERE verified = 1').fetchone()[0]
        stats['unverified_movies'] = stats['total_movies'] - stats['verified_movies']
        
        # Check if age_restricted column exists
        cursor.execute("PRAGMA table_info(movies)")
        columns = [col[1] for col in cursor.fetchall()]
        if "age_restricted" in columns:
            stats['age_restricted_movies'] = cursor.execute('SELECT COUNT(*) FROM movies WHERE age_restricted = 1').fetchone()[0]
        else:
            stats['age_restricted_movies'] = 0
        
        # Get cache statistics
        stats['cache_entries'] = cursor.execute('SELECT COUNT(*) FROM movie_info_cache').fetchone()[0]
        
        # Get oldest cache entry
        oldest_cache = cursor.execute('SELECT MIN(cached_at) FROM movie_info_cache WHERE cached_at IS NOT NULL').fetchone()[0]
        stats['oldest_cache'] = oldest_cache
        
        # Get last verification date
        last_verified = cursor.execute('SELECT MAX(last_verified) FROM movies WHERE last_verified IS NOT NULL').fetchone()[0]
        stats['last_verification'] = last_verified
        
        # Get last age check date (if column exists)
        if "age_checked_at" in columns:
            last_age_check = cursor.execute('SELECT MAX(age_checked_at) FROM movies WHERE age_checked_at IS NOT NULL').fetchone()[0]
            stats['last_age_check'] = last_age_check
        else:
            stats['last_age_check'] = None
        
        conn.close()
        
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/clear-all-cache', methods=['POST'])
def clear_all_cache():
    """Clear all cached movie information from OMDb API
    ---
    tags:
      - admin
    responses:
      200:
        description: Cache cleared successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "All cache cleared successfully"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Database error"
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM movie_info_cache')
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'All cache cleared successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/refresh-all-cache', methods=['POST'])
def refresh_all_cache():
    """Start background refresh of all cached movie information
    ---
    tags:
      - admin
    responses:
      200:
        description: Cache refresh started successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Cache refresh started in background"
    """
    def refresh_cache_background():
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Clear all existing cache
            cursor.execute('DELETE FROM movie_info_cache')
            conn.commit()
            
            # Get all movies
            movies = cursor.execute('SELECT id, title FROM movies').fetchall()
            conn.close()
            
            print(f"🔄 Starting cache refresh for {len(movies)} movies")
            
            for i, movie in enumerate(movies, 1):
                movie_id, title = movie
                try:
                    print(f"🔍 Refreshing cache {i}/{len(movies)}: {title}")
                    
                    success, info = fetch_movie_info(title)
                    if success and isinstance(info, dict):
                        save_movie_info_cache(movie_id, info)
                        print(f"✅ Cached info for: {title}")
                    else:
                        print(f"❌ Failed to fetch info for: {title}")
                    
                    # Small delay to be respectful to OMDb API
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"❌ Error refreshing {title}: {e}")
            
            print("✅ Cache refresh completed")
            
        except Exception as e:
            print(f"❌ Cache refresh error: {e}")
    
    thread = threading.Thread(target=refresh_cache_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Cache refresh started in background'})

@app.route('/api/check-age-restrictions', methods=['POST'])
def check_age_restrictions():
    """Start background check of age restrictions for all movies
    ---
    tags:
      - admin
    responses:
      200:
        description: Age restriction check started successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Age restriction check started in background"
    """
    def check_age_restrictions_background():
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get all movies
            movies = cursor.execute('SELECT id, title, url FROM movies').fetchall()
            conn.close()
            
            print(f"🔞 Starting age restriction check for {len(movies)} movies")
            
            for i, movie in enumerate(movies, 1):
                movie_id, title, url = movie
                try:
                    print(f"🔍 Checking age restrictions {i}/{len(movies)}: {title}")
                    
                    is_age_restricted, message = check_age_restriction(url)
                    
                    # Update database
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE movies 
                        SET age_restricted = ?, age_checked_at = ? 
                        WHERE id = ?
                    ''', (int(is_age_restricted), datetime.now().isoformat(), movie_id))
                    conn.commit()
                    conn.close()
                    
                    print(f"{'🔞' if is_age_restricted else '👍'} {title}: {message}")
                    
                    # Small delay to be respectful
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ Error checking {title}: {e}")
            
            print("✅ Age restriction check completed")
            
        except Exception as e:
            print(f"❌ Age restriction check error: {e}")
    
    thread = threading.Thread(target=check_age_restrictions_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Age restriction check started in background'})

@app.route('/genres')
def genres():
    return render_template('genres.html')

@app.route('/genre/<genre_name>')
def genre_detail(genre_name):
    return render_template('genre_detail.html', genre=genre_name)

@app.route('/api/movies-by-genre/<genre_name>')
def movies_by_genre(genre_name):
    """Get movies by genre from cached OMDb data
    ---
    tags:
      - movies
    parameters:
      - name: genre_name
        in: path
        type: string
        required: true
        description: Genre name to filter by
      - name: sort_by
        in: query
        type: string
        required: false
        description: Sort field (title, year, rating, add_date)
        default: title
      - name: order
        in: query
        type: string
        required: false
        description: Sort order (asc, desc)
        default: asc
    responses:
      200:
        description: Movies filtered by genre
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            genre:
              type: string
              example: "Action"
            movies:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  title:
                    type: string
                  url:
                    type: string
                  genre:
                    type: string
                  year:
                    type: string
                  imdb_rating:
                    type: string
            total_count:
              type: integer
    """
    try:
        # Get sorting parameters
        sort_by = request.args.get('sort_by', 'title')
        order = request.args.get('order', 'asc')
        
        # Validate sort_by parameter
        valid_sorts = {
            'title': 'm.title',
            'year': 'c.year',
            'rating': 'CASE WHEN c.imdb_rating = "N/A" THEN 0 ELSE CAST(c.imdb_rating AS REAL) END',
            'add_date': 'm.id'  # Using ID as proxy for add date (newer movies have higher IDs)
        }
        
        if sort_by not in valid_sorts:
            sort_by = 'title'
        
        # Validate order parameter
        if order not in ['asc', 'desc']:
            order = 'asc'
        
        sort_column = valid_sorts[sort_by]
        order_clause = f"{sort_column} {'ASC' if order == 'asc' else 'DESC'}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get movies with cached info that match the genre
        query = f'''
            SELECT m.id, m.title, m.url, m.verified, m.last_verified, m.age_restricted, m.age_checked_at,
                   c.genre, c.year, c.imdb_rating, c.poster
            FROM movies m
            JOIN movie_info_cache c ON m.id = c.movie_id
            WHERE c.genre LIKE ?
            ORDER BY {order_clause}
        '''
        cursor.execute(query, (f'%{genre_name}%',))
        rows = cursor.fetchall()
        conn.close()
        movies = []
        for row in rows:
            movies.append({
                'id': row[0],
                'title': row[1],
                'url': row[2],
                'verified': bool(row[3]),
                'last_verified': row[4],
                'age_restricted': bool(row[5]) if row[5] is not None else False,
                'age_checked_at': row[6],
                'genre': row[7],
                'year': row[8],
                'imdb_rating': row[9],
                'poster': row[10]
            })
        return jsonify({
            'success': True,
            'genre': genre_name,
            'movies': movies,
            'total_count': len(movies)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/movies-with-genres')
def movies_with_genres():
    """Get all movies with their cached genre information
    ---
    tags:
      - movies
    responses:
      200:
        description: Movies with genre information
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            movies:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  title:
                    type: string
                  url:
                    type: string
                  verified:
                    type: integer
                  age_restricted:
                    type: integer
                  genre:
                    type: string
                  year:
                    type: string
                  imdb_rating:
                    type: string
                  poster:
                    type: string
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all movies with their cached genre information
        cursor.execute('''
            SELECT m.id, m.title, m.url, m.verified, m.age_restricted, m.age_checked_at,
                   c.genre, c.year, c.imdb_rating, c.poster
            FROM movies m
            LEFT JOIN movie_info_cache c ON m.id = c.movie_id
            ORDER BY m.id DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        movies = []
        for row in rows:
            movies.append({
                'id': row[0],
                'title': row[1],
                'url': row[2],
                'verified': row[3],
                'age_restricted': row[4],
                'age_checked_at': row[5],
                'genre': row[6] or 'N/A',
                'year': row[7] or 'N/A',
                'imdb_rating': row[8] or 'N/A',
                'poster': row[9] or ''
            })
        
        return jsonify({
            'success': True,
            'movies': movies
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🎬 Starting YouTube Movie Picker on {host}:{port}")
    print(f"📡 API Documentation: http://{host}:{port}/api/docs/")
    print(f"🗂️ Database: {get_db_path()}")
    
    app.run(host=host, port=port, debug=debug)

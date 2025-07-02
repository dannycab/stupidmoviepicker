import sqlite3
import os

# Use data directory for Docker compatibility with fallback
def get_db_path():
    """Get the appropriate database path"""
    # Check for environment variable first (set by app.py)
    if 'DB_PATH' in os.environ:
        return os.environ['DB_PATH']
    
    # Fallback logic
    data_dir = '/app/data' if os.path.exists('/app/data') else '.'
    return os.path.join(data_dir, 'movies.db')

DB_PATH = get_db_path()

print(f"Initializing database at: {DB_PATH}")

# Ensure the directory exists
db_dir = os.path.dirname(DB_PATH)
if db_dir and not os.path.exists(db_dir):
    try:
        os.makedirs(db_dir, exist_ok=True)
        print(f"Created directory: {db_dir}")
    except Exception as e:
        print(f"Warning: Could not create directory {db_dir}: {e}")

# Connect to (or create) the database
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print(f"✅ Connected to database: {DB_PATH}")
except Exception as e:
    print(f"❌ Failed to connect to database {DB_PATH}: {e}")
    raise

# Create the movies table with all required columns
cursor.execute('''
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    verified INTEGER DEFAULT 0,
    last_verified TEXT DEFAULT NULL,
    age_restricted INTEGER DEFAULT 0,
    age_checked_at TEXT DEFAULT NULL
)
''')

# Create movie_info_cache table
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
conn.close()
print(f"✅ Database created at {DB_PATH} with all required tables.")

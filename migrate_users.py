"""
Database migration for user authentication system
Adds users table and updates movies table to support multi-user functionality
"""

import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

def get_db_path():
    """Get the appropriate database path"""
    # Check for Docker environment first
    if os.path.exists('/app/data'):
        data_dir = '/app/data'
    elif os.path.exists('./data'):
        data_dir = './data'
    else:
        data_dir = '.'
    
    db_path = os.path.join(data_dir, 'movies.db')
    return db_path

def migrate_users_table():
    """Add users table and user_id to movies table"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔐 Starting user authentication migration...")
    
    # Check if users table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        print("✅ Users table already exists")
        conn.close()
        return
    
    # Create users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            is_admin BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            profile_picture TEXT
        )
    ''')
    
    print("✅ Created users table")
    
    # Check if movies table has user_id column
    cursor.execute("PRAGMA table_info(movies)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "user_id" not in columns:
        # Add user_id column to movies table
        cursor.execute("ALTER TABLE movies ADD COLUMN user_id INTEGER")
        print("✅ Added user_id column to movies table")
        
        # Create a default admin user
        admin_password = "admin123"  # TODO: Make this configurable
        admin_hash = generate_password_hash(admin_password)
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ("admin", "admin@ytmoviepicker.local", admin_hash, "Admin", "User", 1, 1))
        
        admin_id = cursor.lastrowid
        print(f"✅ Created default admin user (ID: {admin_id})")
        print(f"   Username: admin")
        print(f"   Password: {admin_password}")
        print(f"   ⚠️  Change this password immediately!")
        
        # Assign all existing movies to the admin user
        cursor.execute("UPDATE movies SET user_id = ? WHERE user_id IS NULL", (admin_id,))
        existing_count = cursor.rowcount
        print(f"✅ Assigned {existing_count} existing movies to admin user")
        
        # Add foreign key constraint (SQLite doesn't support adding FK constraints to existing tables,
        # so we'll enforce this in the application layer)
        
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_user_id ON movies(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    
    print("✅ Created database indexes")
    
    conn.commit()
    conn.close()
    
    print("🎉 User authentication migration completed successfully!")
    print("\n📝 Next steps:")
    print("1. Install new dependencies: pip install -r requirements.txt")
    print("2. Update Flask app with authentication routes")
    print("3. Add login/register templates")
    print("4. Update existing routes to be user-scoped")

if __name__ == "__main__":
    migrate_users_table()

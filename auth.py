"""
User authentication models and utilities
"""

import sqlite3
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

def get_db_path():
    """Get the appropriate database path"""
    import os
    # Check for Docker environment first
    if os.path.exists('/app/data'):
        data_dir = '/app/data'
    elif os.path.exists('./data'):
        data_dir = './data'
    else:
        data_dir = '.'
    
    db_path = os.path.join(data_dir, 'movies.db')
    return db_path

def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

class User(UserMixin):
    """User model for Flask-Login"""
    
    def __init__(self, id, username, email, first_name, last_name, is_admin, is_active, created_at, last_login, profile_picture=None):
        self.id = id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.is_admin = is_admin
        self.is_active = is_active
        self.created_at = created_at
        self.last_login = last_login
        self.profile_picture = profile_picture
    
    @property
    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def display_name(self):
        """Get display name (full name or username)"""
        full = self.full_name
        return full if full else self.username
    
    def get_id(self):
        """Return user ID as string for Flask-Login"""
        return str(self.id)
    
    def is_authenticated(self):
        """Return True if user is authenticated"""
        return True
    
    def is_anonymous(self):
        """Return True if user is anonymous"""
        return False
    
    def is_active_user(self):
        """Return True if user is active"""
        return bool(self.is_active)
    
    @staticmethod
    def get(user_id):
        """Get user by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_admin=bool(user_data['is_admin']),
                is_active=bool(user_data['is_active']),
                created_at=user_data['created_at'],
                last_login=user_data['last_login'],
                profile_picture=user_data['profile_picture']
            )
        return None
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_admin=bool(user_data['is_admin']),
                is_active=bool(user_data['is_active']),
                created_at=user_data['created_at'],
                last_login=user_data['last_login'],
                profile_picture=user_data['profile_picture']
            )
        return None
    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_admin=bool(user_data['is_admin']),
                is_active=bool(user_data['is_active']),
                created_at=user_data['created_at'],
                last_login=user_data['last_login'],
                profile_picture=user_data['profile_picture']
            )
        return None
    
    @staticmethod
    def verify_password(username, password):
        """Verify user password and return user if valid"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND is_active = 1', (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_admin=bool(user_data['is_admin']),
                is_active=bool(user_data['is_active']),
                created_at=user_data['created_at'],
                last_login=user_data['last_login'],
                profile_picture=user_data['profile_picture']
            )
        return None
    
    @staticmethod
    def create(username, email, password, first_name="", last_name="", is_admin=False):
        """Create a new user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username or email already exists
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            conn.close()
            return None, "Username or email already exists"
        
        # Create user
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, password_hash, first_name, last_name, int(is_admin), 1, datetime.now().isoformat()))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return User.get(user_id), "User created successfully"
    
    def update_last_login(self):
        """Update user's last login timestamp"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                      (datetime.now().isoformat(), self.id))
        conn.commit()
        conn.close()
        self.last_login = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert user to dictionary for JSON responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'display_name': self.display_name,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'profile_picture': self.profile_picture
        }

class UserManager:
    """Utility class for user management operations"""
    
    @staticmethod
    def get_all_users():
        """Get all users"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        users_data = cursor.fetchall()
        conn.close()
        
        users = []
        for user_data in users_data:
            users.append(User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_admin=bool(user_data['is_admin']),
                is_active=bool(user_data['is_active']),
                created_at=user_data['created_at'],
                last_login=user_data['last_login'],
                profile_picture=user_data['profile_picture']
            ))
        return users
    
    @staticmethod
    def get_user_stats():
        """Get user statistics"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM users')
        total = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as active FROM users WHERE is_active = 1')
        active = cursor.fetchone()['active']
        
        cursor.execute('SELECT COUNT(*) as admins FROM users WHERE is_admin = 1')
        admins = cursor.fetchone()['admins']
        
        conn.close()
        
        return {
            'total_users': total,
            'active_users': active,
            'admin_users': admins,
            'inactive_users': total - active
        }
    
    @staticmethod
    def delete_user(user_id):
        """Delete a user and reassign their movies to admin"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get admin user ID
        cursor.execute('SELECT id FROM users WHERE is_admin = 1 ORDER BY id LIMIT 1')
        admin = cursor.fetchone()
        if not admin:
            conn.close()
            return False, "No admin user found"
        
        admin_id = admin['id']
        
        # Reassign user's movies to admin
        cursor.execute('UPDATE movies SET user_id = ? WHERE user_id = ?', (admin_id, user_id))
        movies_reassigned = cursor.rowcount
        
        # Delete user
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        user_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if user_deleted:
            return True, f"User deleted successfully. {movies_reassigned} movies reassigned to admin."
        else:
            return False, "User not found"

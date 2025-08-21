"""
Database models and operations for user authentication
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from .config import AppConfig

class UserDatabase:
    """Handle user database operations"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or AppConfig.DB_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize the users database"""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    google_id TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    profile_picture TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    is_admin BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_count INTEGER DEFAULT 0,
                    user_info TEXT,  -- JSON field for additional user data
                    
                    -- Trading platform configuration
                    trading_user_id TEXT,
                    kite_api_key TEXT,
                    kite_access_token TEXT,
                    data_access_level INTEGER DEFAULT 1,
                    allowed_features TEXT DEFAULT 'dashboard,holdings,gtt',
                    timezone TEXT DEFAULT 'Asia/Kolkata',
                    
                    -- Access control
                    ip_whitelist TEXT,
                    session_timeout INTEGER DEFAULT 3600,
                    max_concurrent_sessions INTEGER DEFAULT 2
                )
            ''')
            
            # Create sessions table for better session management
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create user activity log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    resource TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT 1,
                    details TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            
            # Run migrations to add new columns to existing tables
            self._run_migrations(conn)
    
    def _run_migrations(self, conn):
        """Run database migrations to add new columns"""
        cursor = conn.cursor()
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # List of new columns to add
        new_columns = [
            ('trading_user_id', 'TEXT'),
            ('kite_api_key', 'TEXT'),
            ('kite_access_token', 'TEXT'),
            ('data_access_level', 'INTEGER DEFAULT 1'),
            ('allowed_features', 'TEXT DEFAULT "dashboard,holdings,gtt"'),
            ('timezone', 'TEXT DEFAULT "Asia/Kolkata"'),
            ('ip_whitelist', 'TEXT'),
            ('session_timeout', 'INTEGER DEFAULT 3600'),
            ('max_concurrent_sessions', 'INTEGER DEFAULT 2')
        ]
        
        # Add columns that don't exist
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}')
                    print(f"Added column: {column_name}")
                except Exception as e:
                    print(f"Error adding column {column_name}: {e}")
        
        conn.commit()

    def create_user(self, google_user_info: Dict) -> Optional[Dict]:
        """Create a new user from Google OAuth data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if user is admin
                is_admin = google_user_info.get('email', '') in AppConfig.ADMIN_EMAILS
                
                cursor.execute('''
                    INSERT INTO users (google_id, email, name, profile_picture, is_admin, user_info)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    google_user_info['sub'],
                    google_user_info['email'],
                    google_user_info['name'],
                    google_user_info.get('picture', ''),
                    is_admin,
                    json.dumps(google_user_info)
                ))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                return self.get_user_by_id(user_id)
                
        except sqlite3.IntegrityError:
            # User already exists
            return self.get_user_by_google_id(google_user_info['sub'])
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def get_user_by_google_id(self, google_id: str) -> Optional[Dict]:
        """Get user by Google ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE google_id = ? AND is_active = 1', (google_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE email = ? AND is_active = 1', (email,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE id = ? AND is_active = 1', (user_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def update_last_login(self, user_id: int):
        """Update user's last login time and increment login count"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
    
    def is_email_allowed(self, email: str) -> bool:
        """Check if email domain is allowed"""
        if not AppConfig.ALLOWED_EMAIL_DOMAINS:
            return True  # Allow all emails if no restrictions
        
        domain = email.split('@')[1].lower()
        return domain in [d.lower() for d in AppConfig.ALLOWED_EMAIL_DOMAINS]
    
    def get_all_users(self) -> List[Dict]:
        """Get all active users (admin function)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, email, name, profile_picture, is_admin, created_at, last_login, login_count
                FROM users WHERE is_active = 1
                ORDER BY created_at DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def toggle_user_admin(self, user_id: int) -> bool:
        """Toggle user admin status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET is_admin = NOT is_admin
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET is_active = 0
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    # Trading Configuration Methods
    def update_trading_config(self, user_id: int, config: Dict) -> bool:
        """Update user's trading configuration"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE users SET
                        trading_user_id = ?,
                        kite_api_key = ?,
                        kite_access_token = ?,
                        data_access_level = ?,
                        allowed_features = ?,
                        timezone = ?,
                        ip_whitelist = ?,
                        session_timeout = ?,
                        max_concurrent_sessions = ?
                    WHERE id = ?
                ''', (
                    config.get('trading_user_id'),
                    config.get('kite_api_key'),
                    config.get('kite_access_token'),
                    config.get('data_access_level', 1),
                    config.get('allowed_features', 'dashboard,holdings,gtt'),
                    config.get('timezone', 'Asia/Kolkata'),
                    config.get('ip_whitelist'),
                    config.get('session_timeout', 3600),
                    config.get('max_concurrent_sessions', 2),
                    user_id
                ))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating trading config: {e}")
            return False
    
    def get_trading_config(self, user_id: int) -> Optional[Dict]:
        """Get user's trading configuration"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT trading_user_id, kite_api_key, kite_access_token,
                       data_access_level, allowed_features, timezone,
                       ip_whitelist, session_timeout, max_concurrent_sessions
                FROM users WHERE id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def has_feature_access(self, user_id: int, feature: str) -> bool:
        """Check if user has access to a specific feature"""
        config = self.get_trading_config(user_id)
        if not config:
            return False
        
        allowed_features = config.get('allowed_features', '').split(',')
        return feature.lower() in [f.strip().lower() for f in allowed_features]
    
    def check_ip_access(self, user_id: int, ip_address: str) -> bool:
        """Check if IP address is allowed for user"""
        config = self.get_trading_config(user_id)
        if not config or not config.get('ip_whitelist'):
            return True  # No IP restriction
        
        allowed_ips = [ip.strip() for ip in config['ip_whitelist'].split(',')]
        return ip_address in allowed_ips
    
    # Activity Logging
    def log_activity(self, user_id: int, action: str, resource: str = None, 
                    ip_address: str = None, success: bool = True, details: str = None):
        """Log user activity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO user_activity 
                    (user_id, action, resource, ip_address, success, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, action, resource, ip_address, success, details))
                
                conn.commit()
        except Exception as e:
            print(f"Error logging activity: {e}")
    
    def get_user_activity(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's recent activity"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM user_activity 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]

# Global database instance
user_db = UserDatabase()

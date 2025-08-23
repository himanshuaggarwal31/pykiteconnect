"""
Database models and operations for user authentication using Oracle DB with caching
"""
import oracledb
import json
import time
from datetime import datetime
from typing import Optional, Dict, List
from .config import AppConfig
from .oracle_manager import connection_manager
from .cache_manager import cached_user_data, user_cache, config_cache, invalidate_user_cache
import sys
import os

class UserDatabase:
    """Handle user database operations using Oracle DB"""
    
    def __init__(self):
        # Oracle DB connection will be handled by get_connection()
        self.init_database()
    
    def get_connection(self):
        """Get Oracle database connection with retry logic"""
        return connection_manager.get_connection()
    
    def init_database(self):
        """Initialize the users database - Oracle tables should already exist"""
        # Oracle tables are created via oracle_schema.sql
        # This method can be used for any runtime initialization if needed
        try:
            with connection_manager.get_cursor() as cursor:
                # Test if tables exist
                cursor.execute("""
                    SELECT table_name FROM user_tables 
                    WHERE table_name IN ('USERS', 'USER_SESSIONS', 'USER_ACTIVITY')
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['USERS', 'USER_SESSIONS', 'USER_ACTIVITY']
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    raise Exception(f"Missing Oracle tables: {', '.join(missing_tables)}. Please run oracle_schema.sql first.")
                    
                print("Oracle authentication database initialized successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise

    def create_user(self, google_user_info: Dict) -> Optional[Dict]:
        """Create a new user from Google OAuth data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user is admin
                is_admin = 1 if google_user_info.get('email', '') in AppConfig.ADMIN_EMAILS else 0
                
                cursor.execute("""
                    INSERT INTO users (google_id, email, name, profile_picture, is_admin, user_info)
                    VALUES (:1, :2, :3, :4, :5, :6)
                """, (
                    google_user_info['sub'],
                    google_user_info['email'],
                    google_user_info['name'],
                    google_user_info.get('picture', ''),
                    is_admin,
                    json.dumps(google_user_info)
                ))
                
                conn.commit()
                
                # Get the user by Google ID instead of trying to get sequence value
                return self.get_user_by_google_id(google_user_info['sub'])
                
        except oracledb.IntegrityError:
            # User already exists
            return self.get_user_by_google_id(google_user_info['sub'])
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def get_user_by_google_id(self, google_id: str) -> Optional[Dict]:
        """Get user by Google ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM users WHERE google_id = :1 AND is_active = 1', (google_id,))
                row = cursor.fetchone()
                
                if row:
                    columns = [desc[0].lower() for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            print(f"Error getting user by Google ID: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM users WHERE email = :1 AND is_active = 1', (email,))
                row = cursor.fetchone()
                
                if row:
                    columns = [desc[0].lower() for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    @cached_user_data(timeout=300)  # Cache for 5 minutes
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID with caching"""
        try:
            with connection_manager.get_cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE id = :1 AND is_active = 1', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    columns = [desc[0].lower() for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def update_last_login(self, user_id: int):
        """Update user's last login time and increment login count"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
                    WHERE id = :1
                """, (user_id,))
                
                conn.commit()
        except Exception as e:
            print(f"Error updating last login: {e}")
    
    def is_email_allowed(self, email: str) -> bool:
        """Check if email domain is allowed"""
        if not AppConfig.ALLOWED_EMAIL_DOMAINS:
            return True  # Allow all emails if no restrictions
        
        domain = email.split('@')[1].lower()
        return domain in [d.lower() for d in AppConfig.ALLOWED_EMAIL_DOMAINS]
    
    def get_all_users(self) -> List[Dict]:
        """Get all active users (admin function)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, email, name, profile_picture, is_admin, created_at, last_login, login_count
                    FROM users WHERE is_active = 1
                    ORDER BY created_at DESC
                """)
                
                rows = cursor.fetchall()
                columns = [desc[0].lower() for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def toggle_user_admin(self, user_id: int) -> bool:
        """Toggle user admin status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users 
                    SET is_admin = CASE WHEN is_admin = 1 THEN 0 ELSE 1 END
                    WHERE id = :1
                """, (user_id,))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error toggling user admin: {e}")
            return False
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users 
                    SET is_active = 0
                    WHERE id = :1
                """, (user_id,))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deactivating user: {e}")
            return False
    
    # Trading Configuration Methods
    def update_trading_config(self, user_id: int, config: Dict) -> bool:
        """Update user's trading configuration and invalidate cache"""
        try:
            with connection_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE users SET
                        trading_user_id = :1,
                        kite_api_key = :2,
                        kite_access_token = :3,
                        data_access_level = :4,
                        allowed_features = :5,
                        timezone = :6,
                        ip_whitelist = :7,
                        session_timeout = :8,
                        max_concurrent_sessions = :9
                    WHERE id = :10
                """, (
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
                
                # Invalidate cache for this user
                invalidate_user_cache(user_id)
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating trading config: {e}")
            return False
    
    def needs_onboarding(self, user_id: int) -> bool:
        """Check if user needs to complete onboarding (configure trading settings)"""
        try:
            config = self.get_trading_config(user_id)
            if not config:
                return True
            
            # Check if essential trading fields are configured
            essential_fields = ['trading_user_id', 'kite_api_key']
            for field in essential_fields:
                if not config.get(field):
                    return True
            
            return False
        except Exception as e:
            print(f"Error checking onboarding status: {e}")
            return True  # Default to requiring onboarding if we can't check
    
    def mark_onboarding_complete(self, user_id: int):
        """Mark user as having completed onboarding"""
        try:
            with connection_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = :1
                """, (user_id,))
        except Exception as e:
            print(f"Error marking onboarding complete: {e}")

    @cached_user_data(timeout=600)  # Cache for 10 minutes
    def get_trading_config(self, user_id: int) -> Optional[Dict]:
        """Get user's trading configuration with caching"""
        try:
            with connection_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT trading_user_id, kite_api_key, kite_access_token,
                           data_access_level, allowed_features, timezone,
                           ip_whitelist, session_timeout, max_concurrent_sessions
                    FROM users WHERE id = :1
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0].lower() for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            print(f"Error getting trading config: {e}")
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
    def log_activity(self, user_id: int, action: str, resources: str = None, 
                    ip_address: str = None, success: bool = True, details: str = None):
        """Log user activity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO user_activity 
                    (user_id, action, resources, ip_address, success, details)
                    VALUES (:1, :2, :3, :4, :5, :6)
                """, (user_id, action, resources, ip_address, 1 if success else 0, details))
                
                conn.commit()
        except Exception as e:
            print(f"Error logging activity: {e}")
    
    def get_user_activity(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's recent activity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM user_activity 
                    WHERE user_id = :1 
                    ORDER BY timestamp DESC 
                    FETCH FIRST :2 ROWS ONLY
                """, (user_id, limit))
                
                rows = cursor.fetchall()
                columns = [desc[0].lower() for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error getting user activity: {e}")
            return []

# Global database instance
user_db = UserDatabase()

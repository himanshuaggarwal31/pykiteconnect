"""
Improved Oracle database connection management for Flask app with connection pooling
"""
import oracledb
import threading
import time
from contextlib import contextmanager
from functools import lru_cache
import sys
import os

# Add the path to import db_config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'gtt_webapp'))

class OracleConnectionManager:
    """Manage Oracle database connections with connection pooling for the auth system"""
    
    def __init__(self):
        self._pool = None
        self._lock = threading.Lock()
        self._init_pool()
        
    def _init_pool(self):
        """Initialize Oracle connection pool"""
        try:
            from db_config import configuration
            
            # Create connection pool with optimized settings
            self._pool = oracledb.create_pool(
                min=2,  # Minimum connections in pool
                max=10,  # Maximum connections in pool
                increment=1,  # Increment when pool needs to grow
                **configuration['db_config']
            )
            print("✅ Oracle connection pool created successfully")
            
        except Exception as e:
            print(f"❌ Failed to create Oracle connection pool: {e}")
            self._pool = None
            raise
    
    def get_connection(self):
        """Get a connection from the pool"""
        if not self._pool:
            with self._lock:
                if not self._pool:
                    self._init_pool()
        
        try:
            return self._pool.acquire()
        except Exception as e:
            print(f"Failed to acquire connection from pool: {e}")
            # Fallback to direct connection
            from db_config import get_connection
            return get_connection()
    
    @contextmanager
    def get_cursor(self):
        """Get a cursor with automatic connection management from pool"""
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except Exception as e:
            connection.rollback()
            raise
        finally:
            cursor.close()
            if hasattr(connection, 'close'):
                connection.close()  # Return to pool
    
    def close_pool(self):
        """Close the connection pool"""
        if self._pool:
            try:
                self._pool.close()
                print("Oracle connection pool closed")
            except:
                pass
            self._pool = None

# Global connection manager instance
connection_manager = OracleConnectionManager()

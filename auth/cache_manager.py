"""
Session caching system to reduce database queries
"""
import time
import threading
from functools import wraps
from typing import Dict, Any, Optional

class SessionCache:
    """Thread-safe cache for user session data"""
    
    def __init__(self, default_timeout=300):  # 5 minutes default
        self._cache = {}
        self._timestamps = {}
        self._lock = threading.RLock()
        self.default_timeout = default_timeout
        self._cleanup_thread = None
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background thread to cleanup expired items"""
        def cleanup_worker():
            while True:
                time.sleep(60)  # Cleanup every minute
                self.cleanup_expired()
        
        if not self._cleanup_thread or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
            self._cleanup_thread.start()
    
    def get(self, key: str, timeout: Optional[int] = None) -> Optional[Any]:
        """Get item from cache if not expired"""
        with self._lock:
            if key not in self._cache:
                return None
                
            # Check if expired
            timeout = timeout or self.default_timeout
            if time.time() - self._timestamps[key] > timeout:
                del self._cache[key]
                del self._timestamps[key]
                return None
                
            return self._cache[key]
    
    def set(self, key: str, value: Any):
        """Set item in cache"""
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    def delete(self, key: str):
        """Delete item from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
    
    def clear(self):
        """Clear all cache"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
    
    def cleanup_expired(self):
        """Remove expired items"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, timestamp in self._timestamps.items()
                if current_time - timestamp > self.default_timeout
            ]
            for key in expired_keys:
                del self._cache[key]
                del self._timestamps[key]
            
            if expired_keys:
                print(f"Cleaned up {len(expired_keys)} expired cache items")
    
    def stats(self):
        """Get cache statistics"""
        with self._lock:
            return {
                'total_items': len(self._cache),
                'cache_hit_potential': len(self._cache) > 0
            }

# Global cache instances
user_cache = SessionCache(default_timeout=300)  # 5 minutes for user data
config_cache = SessionCache(default_timeout=600)  # 10 minutes for config data

def cached_user_data(timeout=300):
    """Decorator to cache user data queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, user_id, *args, **kwargs):
            cache_key = f"user_{user_id}_{func.__name__}"
            
            # Try to get from cache first
            cached_result = user_cache.get(cache_key, timeout)
            if cached_result is not None:
                return cached_result
            
            # Not in cache, call the function
            result = func(self, user_id, *args, **kwargs)
            
            # Cache the result if it's not None
            if result is not None:
                user_cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator

def invalidate_user_cache(user_id: int):
    """Invalidate all cached data for a user"""
    keys_to_delete = []
    for key in user_cache._cache.keys():
        if key.startswith(f"user_{user_id}_"):
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        user_cache.delete(key)
    
    if keys_to_delete:
        print(f"Invalidated {len(keys_to_delete)} cache entries for user {user_id}")

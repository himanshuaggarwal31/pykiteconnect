"""
Fast session management for better performance
"""
from flask import session, request, g
from .database import user_db
from .cache_manager import user_cache
import time

def get_current_user_fast():
    """Get current user with optimized caching"""
    # First check if we already have user in request context
    if hasattr(g, 'current_user'):
        return g.current_user
    
    user_id = session.get('user_id')
    if not user_id:
        g.current_user = None
        return None
    
    # Try to get from cache first (very fast)
    cache_key = f"user_{user_id}_get_user_by_id"
    user = user_cache.get(cache_key, timeout=300)
    
    if user is None:
        # Not in cache, get from database
        user = user_db.get_user_by_id(user_id)
        if user:
            user_cache.set(cache_key, user)
    
    # Store in request context for this request
    g.current_user = user
    return user

def preload_user_data(user_id: int):
    """Preload frequently accessed user data into cache"""
    try:
        # Preload user and config data in a single database hit
        user = user_db.get_user_by_id(user_id)
        config = user_db.get_trading_config(user_id)
        
        # These will be cached by the @cached_user_data decorators
        return user, config
    except Exception as e:
        print(f"Error preloading user data: {e}")
        return None, None

def warm_cache_for_user(user_id: int):
    """Warm up cache for a user after login"""
    try:
        preload_user_data(user_id)
        print(f"Cache warmed for user {user_id}")
    except Exception as e:
        print(f"Error warming cache: {e}")

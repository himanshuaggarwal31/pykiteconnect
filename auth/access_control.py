"""
Access control decorators and middleware for user-specific data access
"""
from functools import wraps
from flask import session, request, jsonify, abort, redirect, url_for, flash
from .database import user_db
from .config import OAuthConfig

def feature_required(feature_name):
    """Decorator to check if user has access to a specific feature"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip checks if auth is bypassed
            if OAuthConfig.BYPASS_AUTH:
                return f(*args, **kwargs)
            
            user_id = session.get('user_id')
            if not user_id:
                return redirect(url_for('auth.login'))
            
            # Skip check for bypass user
            if user_id == 999:
                return f(*args, **kwargs)
            
            # Check feature access
            if not user_db.has_feature_access(user_id, feature_name):
                flash(f'Access denied. You do not have permission to access {feature_name}.', 'error')
                return redirect(url_for('main.dashboard'))
            
            # Log activity
            user_db.log_activity(
                user_id=user_id,
                action=f'access_{feature_name}',
                resource=request.endpoint,
                ip_address=request.remote_addr,
                success=True
            )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def data_access_level_required(min_level):
    """Decorator to check user's data access level"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip checks if auth is bypassed
            if OAuthConfig.BYPASS_AUTH:
                return f(*args, **kwargs)
            
            user_id = session.get('user_id')
            if not user_id:
                return redirect(url_for('auth.login'))
            
            # Skip check for bypass user
            if user_id == 999:
                return f(*args, **kwargs)
            
            # Check data access level
            config = user_db.get_trading_config(user_id)
            if not config or config.get('data_access_level', 0) < min_level:
                return jsonify({'error': 'Insufficient data access level'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def ip_whitelist_required(f):
    """Decorator to check if user's IP is whitelisted"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip checks if auth is bypassed
        if OAuthConfig.BYPASS_AUTH:
            return f(*args, **kwargs)
        
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Skip check for bypass user
        if user_id == 999:
            return f(*args, **kwargs)
        
        # Check IP whitelist
        client_ip = request.remote_addr
        if not user_db.check_ip_access(user_id, client_ip):
            user_db.log_activity(
                user_id=user_id,
                action='access_denied_ip',
                resource=request.endpoint,
                ip_address=client_ip,
                success=False,
                details=f'IP {client_ip} not in whitelist'
            )
            abort(403, description="Access denied from this IP address")
        
        return f(*args, **kwargs)
    return decorated_function

class UserDataFilter:
    """Filter data based on user's trading configuration"""
    
    @staticmethod
    def get_user_trading_id(user_id: int = None) -> str:
        """Get the trading user ID for the current or specified user"""
        if OAuthConfig.BYPASS_AUTH:
            return "DEV_USER"
        
        if not user_id:
            user_id = session.get('user_id')
        
        if user_id == 999:  # Bypass user
            return "DEV_USER"
        
        if not user_id:
            return None
        
        config = user_db.get_trading_config(user_id)
        return config.get('trading_user_id') if config else None
    
    @staticmethod
    def get_user_kite_credentials(user_id: int = None) -> dict:
        """Get Kite Connect credentials for user"""
        if OAuthConfig.BYPASS_AUTH:
            # Return default credentials for development
            return {
                'api_key': 'dev_api_key',
                'access_token': 'dev_access_token'
            }
        
        if not user_id:
            user_id = session.get('user_id')
        
        if user_id == 999:  # Bypass user
            return {
                'api_key': 'dev_api_key',
                'access_token': 'dev_access_token'
            }
        
        if not user_id:
            return {}
        
        config = user_db.get_trading_config(user_id)
        if config:
            return {
                'api_key': config.get('kite_api_key'),
                'access_token': config.get('kite_access_token')
            }
        return {}
    
    @staticmethod
    def filter_data_by_user(data, user_field='user_id', user_id: int = None):
        """Filter data to show only records belonging to the user"""
        if OAuthConfig.BYPASS_AUTH:
            return data  # Show all data in bypass mode
        
        trading_user_id = UserDataFilter.get_user_trading_id(user_id)
        if not trading_user_id:
            return []
        
        if isinstance(data, list):
            return [record for record in data if record.get(user_field) == trading_user_id]
        elif isinstance(data, dict):
            return data if data.get(user_field) == trading_user_id else {}
        
        return data

def log_user_action(action, resource=None, details=None):
    """Decorator to log user actions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if user_id and user_id != 999:  # Don't log bypass user actions
                user_db.log_activity(
                    user_id=user_id,
                    action=action,
                    resource=resource or request.endpoint,
                    ip_address=request.remote_addr,
                    success=True,
                    details=details
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

"""
OAuth Configuration and Environment Variables
"""
import os
from pathlib import Path

# OAuth Configuration
class OAuthConfig:
    """Google OAuth Configuration"""
    
    # Authentication bypass (set to True to disable authentication)
    BYPASS_AUTH = os.getenv('BYPASS_AUTH', 'False').lower() == 'true'
    
    # You'll need to set these environment variables or update directly
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', 'your-client-id-here')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', 'your-client-secret-here')
    
    # OAuth URLs
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid_configuration"
    
    # Manual endpoint configuration (fallback if discovery fails)
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"
    
    # Redirect URIs (these should match what you configured in Google Console)
    REDIRECT_URIS = [
        'http://localhost:5001/auth/callback',
        'http://127.0.0.1:5001/auth/callback',
        'http://gtt-local.dev:5001/auth/callback'
    ]
    
    # Scopes we need from Google
    SCOPES = [
        'openid',
        'email', 
        'profile'
    ]

# App Configuration
class AppConfig:
    """Flask App Configuration"""
    
    # Session security
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-very-secret-key-change-this-in-production')
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'gtt_'
    
    # Database configuration (Oracle DB via environment variables)
    # Oracle connection details are loaded from gtt_webapp/.env
    
    # Allowed email domains (leave empty to allow all)
    ALLOWED_EMAIL_DOMAINS = [
        # 'yourdomain.com',  # Only allow users from specific domains
        # 'gmail.com'        # Or allow gmail users
    ]
    
    # Admin emails (these users get admin privileges)
    ADMIN_EMAILS = [
        # 'your-email@gmail.com'  # Add your email here
    ]
    
    # App settings
    HOST = '0.0.0.0'  # Listen on all interfaces for network access
    PORT = 5001
    DEBUG = True

# Load configuration from .env file if it exists
def load_env_config():
    """Load configuration from .env file"""
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"\'')

# Auto-load environment
load_env_config()

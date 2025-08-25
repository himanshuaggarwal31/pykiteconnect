"""
Simplified Google OAuth authentication using official Google libraries
"""
import json
import secrets
import os
from flask import Blueprint, request, redirect, url_for, session, flash, jsonify, render_template_string
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests as google_requests
import google.auth.transport.requests
from .config import OAuthConfig, AppConfig
from .database import user_db
from functools import wraps

# Allow insecure transport for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# OAuth flow instance
oauth_flow = None

def create_oauth_flow():
    """Create Google OAuth flow"""
    global oauth_flow
    
    # Create client config
    client_config = {
        "web": {
            "client_id": OAuthConfig.GOOGLE_CLIENT_ID,
            "client_secret": OAuthConfig.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": OAuthConfig.REDIRECT_URIS
        }
    }
    
    oauth_flow = Flow.from_client_config(
        client_config,
        scopes=[
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'openid'
        ]
    )
    
    return oauth_flow

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Even in bypass mode, require a valid session (either real user or bypass user)
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        
        # Skip user verification for bypass mode (user_id 999)
        if session.get('user_id') == 999:
            return f(*args, **kwargs)
        
        # For real users, verify they still exist and are active
        user = user_db.get_user_by_id(session['user_id'])
        if not user:
            session.clear()
            flash('Your account is no longer active. Please contact an administrator.', 'error')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Require login first
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
            
        # Bypass mode user (999) is always admin
        if session.get('user_id') == 999:
            return f(*args, **kwargs)
        
        # For real users, check if they have admin privileges
        user = user_db.get_user_by_id(session['user_id'])
        if not user or not user.get('is_admin'):
            flash('Admin privileges required.', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login')
def login():
    """Login page and redirect to Google OAuth"""
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    
    # Show login page
    login_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - GTT Trading Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .login-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                padding: 2rem;
                max-width: 400px;
                width: 100%;
            }
            .btn-google {
                background: #4285f4;
                border: none;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                width: 100%;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            .btn-google:hover {
                background: #3367d6;
                color: white;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(66, 133, 244, 0.3);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="login-card text-center">
                        <div class="mb-4">
                            <i class="fas fa-chart-line fa-3x text-primary mb-3"></i>
                            <h2 class="fw-bold text-dark">GTT Trading Dashboard</h2>
                            <p class="text-muted">Sign in to access your trading dashboard</p>
                        </div>
                        
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show" role="alert">
                                        {{ message }}
                                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        
                        {% if bypass_enabled %}
                        <div class="alert alert-warning mb-3">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <strong>DEVELOPMENT MODE ACTIVE</strong><br>
                            <small>Google OAuth is disabled for security. Use bypass login below.</small>
                        </div>
                        
                        <div class="mb-3">
                            <button class="btn btn-google" disabled>
                                <i class="fab fa-google me-2"></i>
                                Google OAuth (Disabled in Dev Mode)
                            </button>
                        </div>
                        
                        <div class="mt-3">
                            <a href="{{ url_for('auth.bypass_login') }}" class="btn btn-warning w-100">
                                <i class="fas fa-unlock me-2"></i>
                                Development Mode - Bypass Login
                            </a>
                            <div class="mt-2">
                                <small class="text-danger">
                                    <i class="fas fa-exclamation-triangle me-1"></i>
                                    ⚠️ INSECURE: Only for localhost development
                                </small>
                            </div>
                        </div>
                        {% else %}
                        <a href="{{ url_for('auth.google_login') }}" class="btn btn-google">
                            <i class="fab fa-google me-2"></i>
                            Sign in with Google
                        </a>
                        {% endif %}
                        
                        <div class="mt-4">
                            <small class="text-muted">
                                <i class="fas fa-shield-alt me-1"></i>
                                Secure authentication powered by Google OAuth 2.0
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    
    return render_template_string(login_html, bypass_enabled=OAuthConfig.BYPASS_AUTH)

@auth_bp.route('/google')
def google_login():
    """Initiate Google OAuth login"""
    # Security: Disable Google OAuth when authentication is bypassed
    if OAuthConfig.BYPASS_AUTH:
        flash('Google OAuth is disabled in development mode. Use bypass login instead.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        flow = create_oauth_flow()
        flow.redirect_uri = url_for('auth.callback', _external=True)
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        session['oauth_state'] = state
        return redirect(authorization_url)
        
    except Exception as e:
        print(f"Error initiating Google login: {e}")
        flash('Failed to initiate Google login. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/callback')
def callback():
    """Handle OAuth callback from Google"""
    # Security: Disable OAuth callback when authentication is bypassed
    if OAuthConfig.BYPASS_AUTH:
        flash('Google OAuth is disabled in development mode.', 'error')
        return redirect(url_for('auth.login'))
        
    try:
        # Check for error parameter from Google
        if request.args.get('error'):
            error_description = request.args.get('error_description', 'Unknown error')
            flash(f'Google OAuth error: {error_description}', 'error')
            return redirect(url_for('auth.login'))
        
        # Verify state
        if request.args.get('state') != session.get('oauth_state'):
            flash('Invalid state parameter. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        flow = create_oauth_flow()
        flow.redirect_uri = url_for('auth.callback', _external=True)
        
        # Fetch token with proper error handling
        try:
            flow.fetch_token(authorization_response=request.url)
        except Exception as token_error:
            print(f"Token fetch error: {token_error}")
            # Clear session and try again
            session.pop('oauth_state', None)
            flash('Token exchange failed. Please try logging in again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Get user info
        credentials = flow.credentials
        
        # Get user info from Google using the userinfo endpoint
        import requests
        headers = {'Authorization': f'Bearer {credentials.token}'}
        
        try:
            resp = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers)
            resp.raise_for_status()
            user_info = resp.json()
        except Exception as api_error:
            print(f"Google API error: {api_error}")
            flash('Failed to get user information from Google. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Ensure we have required fields
        if not user_info.get('email'):
            flash('Failed to get user email from Google. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Add sub field if missing (using id as fallback)
        if 'sub' not in user_info:
            user_info['sub'] = user_info.get('id', user_info['email'])
        
        # Check if email is allowed
        if not user_db.is_email_allowed(user_info['email']):
            flash(f'Access denied. Email domain {user_info["email"].split("@")[1]} is not allowed.', 'error')
            return redirect(url_for('auth.login'))
        
        # Create or get user
        user = user_db.create_user(user_info)
        if not user:
            flash('Failed to create user account. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Update last login
        user_db.update_last_login(user['id'])
        
        # Create session
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        session['user_is_admin'] = user['is_admin']
        session['user_picture'] = user.get('profile_picture', '')
        
        # Clear OAuth state
        session.pop('oauth_state', None)
        
        flash(f'Welcome back, {user["name"]}!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        print(f"OAuth callback error: {e}")
        session.pop('oauth_state', None)
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    """Logout user"""
    user_name = session.get('user_name', 'User')
    session.clear()
    flash(f'Goodbye, {user_name}! You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = user_db.get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('auth.logout'))
    
    profile_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Profile - GTT Trading Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card shadow">
                        <div class="card-header bg-primary text-white">
                            <h4 class="mb-0"><i class="fas fa-user me-2"></i>User Profile</h4>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-4 text-center">
                                    {% if user.profile_picture %}
                                        <img src="{{ user.profile_picture }}" class="rounded-circle mb-3" width="120" height="120" alt="Profile Picture">
                                    {% else %}
                                        <div class="bg-secondary rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 120px; height: 120px;">
                                            <i class="fas fa-user fa-3x text-white"></i>
                                        </div>
                                    {% endif %}
                                </div>
                                <div class="col-md-8">
                                    <table class="table table-borderless">
                                        <tr>
                                            <td><strong>Name:</strong></td>
                                            <td>{{ user.name }}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>Email:</strong></td>
                                            <td>{{ user.email }}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>Role:</strong></td>
                                            <td>
                                                {% if user.is_admin %}
                                                    <span class="badge bg-success">Administrator</span>
                                                {% else %}
                                                    <span class="badge bg-primary">User</span>
                                                {% endif %}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><strong>Member Since:</strong></td>
                                            <td>{{ user.created_at }}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>Last Login:</strong></td>
                                            <td>{{ user.last_login or 'First time' }}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>Login Count:</strong></td>
                                            <td>{{ user.login_count }}</td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                            
                            <div class="text-center mt-4">
                                <a href="{{ url_for('main.dashboard') }}" class="btn btn-primary me-2">
                                    <i class="fas fa-arrow-left me-1"></i>Back to Dashboard
                                </a>
                                <a href="{{ url_for('auth.logout') }}" class="btn btn-outline-danger">
                                    <i class="fas fa-sign-out-alt me-1"></i>Logout
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    
    return render_template_string(profile_html, user=user)

@auth_bp.route('/admin/users')
@admin_required
def admin_users():
    """Admin page to manage users"""
    users = user_db.get_all_users()
    
    admin_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>User Management - GTT Trading Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="fas fa-users me-2"></i>User Management</h2>
                <a href="{{ url_for('main.dashboard') }}" class="btn btn-outline-primary">
                    <i class="fas fa-arrow-left me-1"></i>Back to Dashboard
                </a>
            </div>
            
            <div class="card shadow">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>Profile</th>
                                    <th>Name</th>
                                    <th>Email</th>
                                    <th>Role</th>
                                    <th>Joined</th>
                                    <th>Last Login</th>
                                    <th>Logins</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for user in users %}
                                <tr>
                                    <td>
                                        {% if user.profile_picture %}
                                            <img src="{{ user.profile_picture }}" class="rounded-circle" width="40" height="40" alt="Profile">
                                        {% else %}
                                            <div class="bg-secondary rounded-circle d-inline-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                                                <i class="fas fa-user text-white"></i>
                                            </div>
                                        {% endif %}
                                    </td>
                                    <td>{{ user.name }}</td>
                                    <td>{{ user.email }}</td>
                                    <td>
                                        {% if user.is_admin %}
                                            <span class="badge bg-success">Admin</span>
                                        {% else %}
                                            <span class="badge bg-primary">User</span>
                                        {% endif %}
                                    </td>
                                    <td>{{ user.created_at }}</td>
                                    <td>{{ user.last_login or 'Never' }}</td>
                                    <td>{{ user.login_count }}</td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <button class="btn btn-outline-warning" onclick="toggleAdmin({{ user.id }})">
                                                {% if user.is_admin %}Remove Admin{% else %}Make Admin{% endif %}
                                            </button>
                                            {% if user.id != session.user_id %}
                                            <button class="btn btn-outline-danger" onclick="deactivateUser({{ user.id }})">
                                                Deactivate
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function toggleAdmin(userId) {
                if (confirm('Are you sure you want to change this user\\'s admin status?')) {
                    fetch(`/auth/admin/toggle-admin/${userId}`, {method: 'POST'})
                        .then(() => location.reload());
                }
            }
            
            function deactivateUser(userId) {
                if (confirm('Are you sure you want to deactivate this user?')) {
                    fetch(`/auth/admin/deactivate-user/${userId}`, {method: 'POST'})
                        .then(() => location.reload());
                }
            }
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(admin_html, users=users)

@auth_bp.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    """Toggle user admin status"""
    if user_id == session['user_id']:
        return jsonify({'error': 'Cannot change your own admin status'}), 400
    
    success = user_db.toggle_user_admin(user_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to update user'}), 400

@auth_bp.route('/admin/deactivate-user/<int:user_id>', methods=['POST'])
@admin_required
def deactivate_user(user_id):
    """Deactivate a user"""
    if user_id == session['user_id']:
        return jsonify({'error': 'Cannot deactivate yourself'}), 400
    
    success = user_db.deactivate_user(user_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to deactivate user'}), 400

# Utility functions for templates
def get_current_user():
    """Get current user data for templates"""
    # If authentication is bypassed, return a mock user
    if OAuthConfig.BYPASS_AUTH:
        return {
            'id': 999,
            'name': 'Development User',
            'email': 'dev@localhost',
            'is_admin': True,
            'profile_picture': None,
            'created_at': '2025-01-01',
            'last_login': None,
            'login_count': 0
        }
    
    # Check for bypass session
    if 'user_id' in session and session['user_id'] == 999:
        return {
            'id': 999,
            'name': session.get('user_name', 'Development User'),
            'email': session.get('user_email', 'dev@localhost'),
            'is_admin': session.get('user_is_admin', True),
            'profile_picture': session.get('user_picture', None),
            'created_at': '2025-01-01',
            'last_login': None,
            'login_count': 0
        }
    
    if 'user_id' in session:
        return user_db.get_user_by_id(session['user_id'])
    return None

@auth_bp.route('/bypass')
def bypass_login():
    """Bypass route for development - only works when BYPASS_AUTH is enabled"""
    if not OAuthConfig.BYPASS_AUTH:
        flash('Authentication bypass is not enabled.', 'error')
        return redirect(url_for('auth.login'))
    
    # Security: Only allow bypass from localhost/127.0.0.1
    client_ip = request.environ.get('REMOTE_ADDR', request.remote_addr)
    allowed_ips = ['127.0.0.1', '::1', 'localhost']
    
    if client_ip not in allowed_ips:
        flash(f'Bypass login only allowed from localhost. Your IP: {client_ip}', 'error')
        return redirect(url_for('auth.login'))
    
    # Create a mock session for development
    session['user_id'] = -999999
    session['user_email'] = 'dev@localhost'
    session['user_name'] = 'Development User'
    session['user_is_admin'] = True
    session['user_picture'] = ''
    
    flash('🚨 DEVELOPMENT MODE: Authentication bypassed! This is NOT secure for production.', 'warning')
    return redirect(url_for('main.dashboard'))

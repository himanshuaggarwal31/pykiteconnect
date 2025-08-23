"""
OAuth authentication handlers and utilities
"""
import json
import secrets
from flask import Blueprint, request, redirect, url_for, session, flash, jsonify, render_template_string
from authlib.integrations.flask_client import OAuth
from .config import OAuthConfig, AppConfig
from .database import user_db
from functools import wraps

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# OAuth instance (will be initialized in create_oauth function)
oauth = None

def create_oauth(app):
    """Initialize OAuth with the Flask app"""
    global oauth
    oauth = OAuth(app)
    
    # Register Google OAuth with manual configuration
    oauth.register(
        name='google',
        client_id=OAuthConfig.GOOGLE_CLIENT_ID,
        client_secret=OAuthConfig.GOOGLE_CLIENT_SECRET,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        access_token_url='https://oauth2.googleapis.com/token',
        access_token_params=None,
        refresh_token_url=None,
        client_kwargs={'scope': 'openid email profile'},
    )
    
    return oauth

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        
        # Verify user still exists and is active
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
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        
        user = user_db.get_user_by_id(session['user_id'])
        if not user or not user['is_admin']:
            flash('Admin privileges required.', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login')
def login():
    """Login page and redirect to Google OAuth"""
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    
    # Check if this is an AJAX request
    if request.headers.get('Content-Type') == 'application/json':
        auth_url = url_for('auth.google_login', _external=True)
        return jsonify({'auth_url': auth_url})
    
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
                            <h2 class="fw-bold text-dark">GTT Orders Dashboard</h2>
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
                        
                        <a href="{{ url_for('auth.google_login') }}" class="btn btn-google">
                            <i class="fab fa-google me-2"></i>
                            Sign in with Google
                        </a>
                        
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
    
    return render_template_string(login_html)

@auth_bp.route('/google')
def google_login():
    """Initiate Google OAuth login"""
    if not oauth:
        flash('OAuth not configured properly', 'error')
        return redirect(url_for('auth.login'))
    
    # Generate a random state for security
    session['oauth_state'] = secrets.token_urlsafe(32)
    
    redirect_uri = url_for('auth.callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri, state=session['oauth_state'])

@auth_bp.route('/callback')
def callback():
    """Handle OAuth callback from Google"""
    if not oauth:
        flash('OAuth not configured properly', 'error')
        return redirect(url_for('auth.login'))
    
    # Verify state for security
    if request.args.get('state') != session.get('oauth_state'):
        flash('Invalid state parameter. Please try again.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        # Get token from Google
        token = oauth.google.authorize_access_token()
        
        # Get user info from Google using the token
        import requests
        headers = {'Authorization': f'Bearer {token["access_token"]}'}
        resp = requests.get('https://www.googleapis.com/oauth2/v1/userinfo', headers=headers)
        user_info = resp.json()
        
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

        # Check if this is a first-time user or needs onboarding
        is_first_time = user_db.needs_onboarding(user['id'])
        
        # Update last login
        user_db.update_last_login(user['id'])
        
        # Create session
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        session['user_is_admin'] = user['is_admin']
        session['user_picture'] = user.get('profile_picture', '')
        session['is_first_time'] = is_first_time
        
        # Clear OAuth state
        session.pop('oauth_state', None)
        
        # Handle users who need onboarding (either first-time or missing config)
        if is_first_time:
            session['needs_onboarding'] = True
            # No flash message - the onboarding banner will handle the welcome
            return redirect(url_for('profile.index'))
        else:
            # Check if existing user still needs onboarding
            if user_db.needs_onboarding(user['id']):
                session['needs_onboarding'] = True
                # No flash message - the onboarding banner will handle this
                return redirect(url_for('profile.index'))
            else:
                flash(f'Welcome back, {user["name"]}!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        print(f"OAuth callback error: {e}")
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
    if 'user_id' in session:
        return user_db.get_user_by_id(session['user_id'])
    return None

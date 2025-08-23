"""
User profile and trading configuration management
"""
from flask import Blueprint, render_template_string, request, redirect, url_for, flash, jsonify, session, current_app
from .simple_oauth import login_required, admin_required
from .database import user_db
from .access_control import log_user_action, feature_required

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.route('/')
@login_required
def index():
    """User profile and trading configuration page"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('auth.login'))
            
        user = user_db.get_user_by_id(user_id)
        if not user:
            flash('User not found. Please log in again.', 'error')
            return redirect(url_for('auth.login'))
            
        config = user_db.get_trading_config(user_id) or {}
        is_first_time = session.get('is_first_time', False)
        needs_setup = user_db.needs_onboarding(user_id)
        
        # Set onboarding flag for users who need setup
        if needs_setup:
            session['needs_onboarding'] = True
            # Clear any existing flash messages that might conflict with onboarding
            session.pop('_flashes', None)
        
    except Exception as e:
        print(f"Profile page error: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading profile. Please try again.', 'error')
        return redirect(url_for('main.dashboard'))
    
    profile_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trading Configuration - GTT Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-8">
                    <div class="card shadow">
                        <div class="card-header bg-primary text-white">
                            <h4 class="mb-0"><i class="fas fa-cog me-2"></i>Trading Configuration</h4>
                        </div>
                        <div class="card-body">
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
                            
                            {% if session.get('needs_onboarding') %}
                            <div class="alert alert-info alert-dismissible fade show border-0 shadow-sm mb-4" role="alert" style="background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%); border-left: 4px solid #2196f3 !important;">
                                <div class="d-flex align-items-start">
                                    <div class="me-3">
                                        <i class="fas fa-rocket text-primary" style="font-size: 1.5em; margin-top: 0.2em;"></i>
                                    </div>
                                    <div class="flex-grow-1">
                                        <h5 class="alert-heading text-primary mb-2">
                                            <i class="fas fa-star me-2"></i>Welcome to GTT Dashboard!
                                        </h5>
                                        <p class="mb-2">
                                            <strong>Let's get you started!</strong> To begin trading and managing your GTT orders, 
                                            please configure your trading credentials below:
                                        </p>
                                        <ul class="mb-2 ps-3">
                                            <li><strong>Trading User ID:</strong> Your unique trading platform identifier</li>
                                            <li><strong>Kite API Key:</strong> Get this from your <a href="https://kite.trade/connect/login" target="_blank" class="text-decoration-none">Kite Connect dashboard</a></li>
                                            <li><strong>Access Token:</strong> Generate this after API key setup</li>
                                        </ul>
                                        <div class="d-flex align-items-center justify-content-between">
                                            <small class="text-muted">
                                                <i class="fas fa-info-circle me-1"></i>
                                                This one-time setup ensures secure access to your trading data.
                                            </small>
                                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {% endif %}
                            
                            <form method="POST" action="{{ url_for('profile.update_config') }}">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h5 class="text-primary">Trading Platform</h5>
                                        
                                        <div class="mb-3">
                                            <label class="form-label">Trading User ID</label>
                                            <input type="text" class="form-control" name="trading_user_id" 
                                                   value="{{ config.get('trading_user_id', '') }}" 
                                                   placeholder="Your trading platform user ID">
                                            <div class="form-text">This ID will be used to filter your trading data</div>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label class="form-label">Kite API Key</label>
                                            <input type="text" class="form-control" name="kite_api_key" 
                                                   value="{{ config.get('kite_api_key', '') }}" 
                                                   placeholder="Your Kite Connect API key">
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label class="form-label">Kite Access Token</label>
                                            <input type="password" class="form-control" name="kite_access_token" 
                                                   value="{{ config.get('kite_access_token', '') }}" 
                                                   placeholder="Your Kite Connect access token">
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label class="form-label">Timezone</label>
                                            <select class="form-select" name="timezone">
                                                <option value="Asia/Kolkata" {{ 'selected' if config.get('timezone') == 'Asia/Kolkata' else '' }}>Asia/Kolkata (IST)</option>
                                                <option value="UTC" {{ 'selected' if config.get('timezone') == 'UTC' else '' }}>UTC</option>
                                                <option value="America/New_York" {{ 'selected' if config.get('timezone') == 'America/New_York' else '' }}>America/New_York (EST)</option>
                                            </select>
                                        </div>
                                    </div>
                                    
                                    <div class="col-md-6">
                                        <h5 class="text-primary">Access Control</h5>
                                        
                                        <div class="mb-3">
                                            <label class="form-label">Data Access Level</label>
                                            <select class="form-select" name="data_access_level">
                                                <option value="1" {{ 'selected' if config.get('data_access_level', 1) == 1 else '' }}>Level 1 - Basic (Dashboard, Holdings)</option>
                                                <option value="2" {{ 'selected' if config.get('data_access_level', 1) == 2 else '' }}>Level 2 - Intermediate (+ GTT Orders)</option>
                                                <option value="3" {{ 'selected' if config.get('data_access_level', 1) == 3 else '' }}>Level 3 - Advanced (+ Custom Data, SQL)</option>
                                            </select>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label class="form-label">Allowed Features</label>
                                            <div class="row">
                                                {% set features = config.get('allowed_features', 'dashboard,holdings,gtt').split(',') %}
                                                <div class="col-6">
                                                    <div class="form-check">
                                                        <input class="form-check-input" type="checkbox" name="features" value="dashboard" 
                                                               {{ 'checked' if 'dashboard' in features else '' }}>
                                                        <label class="form-check-label">Dashboard</label>
                                                    </div>
                                                    <div class="form-check">
                                                        <input class="form-check-input" type="checkbox" name="features" value="holdings" 
                                                               {{ 'checked' if 'holdings' in features else '' }}>
                                                        <label class="form-check-label">Holdings</label>
                                                    </div>
                                                    <div class="form-check">
                                                        <input class="form-check-input" type="checkbox" name="features" value="gtt" 
                                                               {{ 'checked' if 'gtt' in features else '' }}>
                                                        <label class="form-check-label">GTT Orders</label>
                                                    </div>
                                                </div>
                                                <div class="col-6">
                                                    <div class="form-check">
                                                        <input class="form-check-input" type="checkbox" name="features" value="custom_data" 
                                                               {{ 'checked' if 'custom_data' in features else '' }}>
                                                        <label class="form-check-label">Custom Data</label>
                                                    </div>
                                                    <div class="form-check">
                                                        <input class="form-check-input" type="checkbox" name="features" value="sql_results" 
                                                               {{ 'checked' if 'sql_results' in features else '' }}>
                                                        <label class="form-check-label">SQL Results</label>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label class="form-label">IP Whitelist (Optional)</label>
                                            <textarea class="form-control" name="ip_whitelist" rows="3" 
                                                      placeholder="192.168.1.100,203.123.45.67 (comma separated)">{{ config.get('ip_whitelist', '') }}</textarea>
                                            <div class="form-text">Leave empty to allow access from any IP</div>
                                        </div>
                                        
                                        <div class="row">
                                            <div class="col-6">
                                                <div class="mb-3">
                                                    <label class="form-label">Session Timeout (minutes)</label>
                                                    <input type="number" class="form-control" name="session_timeout" 
                                                           value="{{ (config.get('session_timeout', 3600) / 60) | int }}" min="30" max="480">
                                                </div>
                                            </div>
                                            <div class="col-6">
                                                <div class="mb-3">
                                                    <label class="form-label">Max Concurrent Sessions</label>
                                                    <input type="number" class="form-control" name="max_concurrent_sessions" 
                                                           value="{{ config.get('max_concurrent_sessions', 2) }}" min="1" max="5">
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="text-center mt-4">
                                    <button type="submit" class="btn btn-primary btn-lg">
                                        <i class="fas fa-save me-2"></i>Save Configuration
                                    </button>
                                    <a href="{{ url_for('main.dashboard') }}" class="btn btn-outline-secondary btn-lg ms-2">
                                        <i class="fas fa-arrow-left me-2"></i>Back to Dashboard
                                    </a>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card shadow">
                        <div class="card-header bg-info text-white">
                            <h5 class="mb-0"><i class="fas fa-user me-2"></i>Profile Info</h5>
                        </div>
                        <div class="card-body text-center">
                            {% if user.profile_picture %}
                                <img src="{{ user.profile_picture }}" class="rounded-circle mb-3" width="80" height="80" alt="Profile">
                            {% else %}
                                <div class="bg-secondary rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 80px; height: 80px;">
                                    <i class="fas fa-user fa-2x text-white"></i>
                                </div>
                            {% endif %}
                            <h5>{{ user.name }}</h5>
                            <p class="text-muted">{{ user.email }}</p>
                            <hr>
                            <small class="text-muted">
                                <strong>Current Trading ID:</strong><br>
                                {{ config.get('trading_user_id', 'Not configured') }}
                            </small>
                        </div>
                    </div>
                    
                    <div class="card shadow mt-3">
                        <div class="card-header bg-warning text-dark">
                            <h6 class="mb-0"><i class="fas fa-info-circle me-2"></i>Access Levels</h6>
                        </div>
                        <div class="card-body">
                            <small>
                                <strong>Level 1:</strong> Dashboard, Holdings<br>
                                <strong>Level 2:</strong> + GTT Orders<br>
                                <strong>Level 3:</strong> + Custom Data, SQL Results
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
    
    return render_template_string(profile_html, user=user, config=config)

@profile_bp.route('/update', methods=['POST'])
@login_required
@log_user_action('update_trading_config')
def update_config():
    """Update user's trading configuration"""
    user_id = session.get('user_id')
    
    # Collect form data
    config = {
        'trading_user_id': request.form.get('trading_user_id', '').strip(),
        'kite_api_key': request.form.get('kite_api_key', '').strip(),
        'kite_access_token': request.form.get('kite_access_token', '').strip(),
        'data_access_level': int(request.form.get('data_access_level', 1)),
        'timezone': request.form.get('timezone', 'Asia/Kolkata'),
        'ip_whitelist': request.form.get('ip_whitelist', '').strip(),
        'session_timeout': int(request.form.get('session_timeout', 60)) * 60,  # Convert to seconds
        'max_concurrent_sessions': int(request.form.get('max_concurrent_sessions', 2))
    }
    
    # Handle multiple checkbox values for features
    features = request.form.getlist('features')
    config['allowed_features'] = ','.join(features) if features else 'dashboard'
    
    # Update configuration
    if user_db.update_trading_config(user_id, config):
        # Clear onboarding flags since user has now configured trading settings
        session.pop('needs_onboarding', None)
        session.pop('is_first_time', None)
        flash('Trading configuration updated successfully!', 'success')
    else:
        flash('Failed to update configuration. Please try again.', 'error')
    
    return redirect(url_for('profile.index'))

@profile_bp.route('/activity')
@login_required
@feature_required('dashboard')
def activity():
    """User activity log"""
    user_id = session.get('user_id')
    activities = user_db.get_user_activity(user_id, limit=100)
    
    activity_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Activity Log - GTT Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-4">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0"><i class="fas fa-history me-2"></i>Activity Log</h4>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Action</th>
                                    <th>Resource</th>
                                    <th>IP Address</th>
                                    <th>Status</th>
                                    <th>Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for activity in activities %}
                                <tr>
                                    <td>{{ activity.timestamp }}</td>
                                    <td>
                                        <span class="badge bg-primary">{{ activity.action }}</span>
                                    </td>
                                    <td>{{ activity.resource or '-' }}</td>
                                    <td>{{ activity.ip_address or '-' }}</td>
                                    <td>
                                        {% if activity.success %}
                                            <span class="badge bg-success">Success</span>
                                        {% else %}
                                            <span class="badge bg-danger">Failed</span>
                                        {% endif %}
                                    </td>
                                    <td>{{ activity.details or '-' }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="text-center mt-3">
                        <a href="{{ url_for('profile.index') }}" class="btn btn-outline-primary">
                            <i class="fas fa-arrow-left me-2"></i>Back to Profile
                        </a>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    
    return render_template_string(activity_html, activities=activities)

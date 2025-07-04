from flask import Flask, flash, current_app, request
from flask_assets import Environment, Bundle
from flask_bootstrap import Bootstrap5
from dotenv import load_dotenv
import oracledb
from db_config import configuration
import os
import warnings
from kiteconnect import KiteConnect
import atexit
from logging_config import setup_logging
import logging

# Load environment variables
load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning)

# Initialize extensions
assets = Environment()
bootstrap = Bootstrap5()

def get_kite_instance():
    """Get or create KiteConnect instance with lazy initialization"""
    if current_app.config.get('kite') is not None:
        return current_app.config['kite']
        
    api_key = current_app.config.get('kite_api_key')
    access_token = current_app.config.get('kite_access_token')
    
    if not api_key or not access_token:
        current_app.logger.error("KiteConnect credentials not available")
        return None
        
    try:
        current_app.logger.debug("Creating new KiteConnect instance...")
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Test the connection
        profile = kite.profile()
        current_app.logger.info(f"KiteConnect connection successful. User: {profile.get('user_name', 'Unknown')}")
        
        # Cache the working instance
        current_app.config['kite'] = kite
        return kite
        
    except Exception as e:
        current_app.logger.error(f"Failed to create KiteConnect instance: {str(e)}")
        return None

def create_app():
    app = Flask(__name__)
    
    # Set up logging
    logger = setup_logging(app)
    logger.info("Starting GTT webapp...")
    logger.info("Application initialization starting...")

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    logger.debug(f"SECRET_KEY set: {app.config['SECRET_KEY']!r}")

    # Initialize Oracle DB connection
    try:
        logger.debug("Attempting Oracle DB connection...")
        connection = oracledb.connect(**configuration['db_config'])
        app.config['oracle_connection'] = connection
        logger.info("Oracle DB connection established successfully.")

        # Initialize custom GTT orders table
        from models.custom_gtt import create_custom_gtt_table
        create_custom_gtt_table()
        logger.info("Custom GTT table initialized.")

        # Register connection close on app shutdown
        def cleanup_connection():
            try:
                if 'oracle_connection' in app.config and app.config['oracle_connection'] is not None:
                    app.config['oracle_connection'].close()
                    logger.info("Oracle DB connection closed on shutdown.")
            except Exception as e:
                logger.error(f"Error closing Oracle connection: {str(e)}", exc_info=True)

        atexit.register(cleanup_connection)
        logger.debug("Registered Oracle DB cleanup on shutdown.")

    except Exception as e:
        logger.error(f"Error connecting to Oracle: {str(e)}", exc_info=True)
        app.config['oracle_connection'] = None

    # Initialize KiteConnect
    try:
        logger.debug("Initializing KiteConnect...")
        
        # Try to get API key from environment variable first
        api_key = os.getenv('API_KEY')
        
        # If not found in environment, try to read from api_key.txt file
        if not api_key:
            api_key_paths = [
                os.path.join(os.path.dirname(__file__), 'api_key.txt'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'api_key.txt')
            ]
            
            for api_key_path in api_key_paths:
                try:
                    logger.debug(f"Trying to read API key from: {api_key_path}")
                    with open(api_key_path, 'r') as f:
                        lines = f.read().strip().split('\n')
                        # Take the first line as API key
                        api_key = lines[0].strip()
                        logger.info(f"API key read from file: {api_key_path}")
                        break
                except FileNotFoundError:
                    logger.debug(f"API key file not found at: {api_key_path}")
                    continue
        
        if not api_key:
            raise ValueError("API key not found in environment variable or file")
        
        # Read access token
        token_path = os.path.join(os.path.dirname(__file__), 'access_token.txt')
        logger.debug(f"Reading access token from: {token_path}")
        with open(token_path, 'r') as f:
            access_token = f.read().strip()
            
        # Store connection details in config instead of testing connection immediately
        app.config['kite_api_key'] = api_key
        app.config['kite_access_token'] = access_token
        app.config['kite'] = None  # Will be initialized lazily
        logger.info("KiteConnect credentials loaded successfully")
                
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {str(e)}. Please ensure access_token.txt exists.")
        app.config['kite'] = None
        app.config['kite_api_key'] = None
        app.config['kite_access_token'] = None
    except Exception as e:
        logger.error(f"Error setting up KiteConnect: {str(e)}", exc_info=True)
        app.config['kite'] = None
        app.config['kite_api_key'] = None
        app.config['kite_access_token'] = None

    # Initialize extensions
    assets.init_app(app)
    logger.debug("Flask-Assets initialized.")
    bootstrap.init_app(app)
    logger.debug("Flask-Bootstrap initialized.")

    # Register blueprints
    from blueprints.main import main_bp
    from blueprints.custom_data import custom_data_bp
    from blueprints.holdings import holdings_bp
    # Import only one api_bp to avoid duplicate blueprint names
    from blueprints.api_bp import api_bp
    from blueprints.custom_gtt import custom_gtt_bp
    from blueprints.api.custom_gtt import custom_gtt_api
    from blueprints.api.debug import debug_api

    # First, register API blueprints with api_bp BEFORE registering api_bp with app
    try:
        # Make sure to give each sub-blueprint a unique name using the name parameter
        api_bp.register_blueprint(custom_gtt_api, url_prefix='/custom-gtt')
        logger.info(f"Registered custom_gtt_api blueprint within api_bp with prefix '/custom-gtt'")
        
        api_bp.register_blueprint(debug_api)
        logger.info(f"Registered debug_api blueprint within api_bp")
    except Exception as e:
        logger.error(f"Error registering sub-blueprints: {str(e)}", exc_info=True)
    
    # Register all the blueprints with the app
    app.register_blueprint(main_bp)
    logger.debug("Registered main_bp blueprint.")
    
    app.register_blueprint(custom_data_bp, url_prefix='/custom-data')
    logger.debug("Registered custom_data_bp blueprint.")
    
    app.register_blueprint(holdings_bp, url_prefix='/holdings')
    logger.debug("Registered holdings_bp blueprint.")
    
    try:
        # Register api_bp with app ONLY ONCE
        app.register_blueprint(api_bp, url_prefix='/api')
        logger.info("Registered api_bp blueprint with prefix '/api'. Full URL for debug: /api/debug/routes")
    except Exception as e:
        logger.error(f"Error registering api_bp: {str(e)}", exc_info=True)
    
    app.register_blueprint(custom_gtt_bp)
    logger.debug("Registered custom_gtt_bp blueprint.")

    # Configure assets
    css = Bundle('css/style.css', filters='cssmin', output='gen/packed.css')
    js = Bundle('js/script.js', filters='jsmin', output='gen/packed.js')
    assets.register('css_all', css)
    assets.register('js_all', js)
    logger.debug("Assets bundles registered.")

    # Error handling for missing connections
    @app.before_request
    def check_connections():
        # Only flash database connection errors for routes that need it
        if app.config['oracle_connection'] is None and request.endpoint and 'custom' in request.endpoint:
            flash('Database connection is not available', 'error')
            logger.warning("Database connection is not available.")
    
    # Print all registered routes on startup for debugging
    def list_routes():
        logger.info("Registered Routes:")
        for rule in app.url_map.iter_rules():
            logger.info(f"Route: {rule}, Endpoint: {rule.endpoint}, Methods: {rule.methods}")
    
    list_routes()
    
    # Check if KiteConnect credentials are available
    if app.config.get('kite_api_key') is None or app.config.get('kite_access_token') is None:
        logger.warning("KiteConnect credentials not available. Connection will be attempted when needed.")
    else:
        logger.info("KiteConnect credentials loaded successfully.")

    # Register custom Jinja2 filters
    @app.template_filter('currency')
    def currency_filter(amount):
        """Format amount as currency with commas"""
        try:
            return "{:,.2f}".format(float(amount))
        except (ValueError, TypeError):
            return "0.00"
    
    @app.template_filter('number')
    def number_filter(value):
        """Format number with commas"""
        try:
            return "{:,}".format(int(value))
        except (ValueError, TypeError):
            return "0"

    # We've already logged routes at startup, so we don't need to do it again on first request
    # The before_first_request decorator is also deprecated in newer Flask versions
    
    logger.info("Application successfully initialized!")
    logger.debug("App creation complete.")
    return app

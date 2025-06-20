from flask import Flask, flash
from flask_assets import Environment, Bundle
from flask_bootstrap import Bootstrap5
from dotenv import load_dotenv
import oracledb
from db_config import configuration
import os
import warnings
from kiteconnect import KiteConnect
import atexit

# Load environment variables
load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning)

# Initialize extensions
assets = Environment()
bootstrap = Bootstrap5()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

    # Initialize Oracle DB connection
    try:
        connection = oracledb.connect(**configuration['db_config'])
        app.config['oracle_connection'] = connection
        
        # Initialize custom GTT orders table
        # Run this in a separate connection since we're setting up the app
        from models.custom_gtt import create_custom_gtt_table
        create_custom_gtt_table()
        
        # Register connection close on app shutdown
        def cleanup_connection():
            try:
                if 'oracle_connection' in app.config and app.config['oracle_connection'] is not None:
                    app.config['oracle_connection'].close()
            except Exception as e:
                print(f"Error closing Oracle connection: {str(e)}")
        
        atexit.register(cleanup_connection)
        
    except Exception as e:
        print(f"Error connecting to Oracle: {str(e)}")
        app.config['oracle_connection'] = None

    # Initialize KiteConnect
    try:
        kite = KiteConnect(api_key=os.getenv('API_KEY'))
        # Get access token from file
        token_path = os.path.join(os.path.dirname(__file__), 'access_token.txt')
        with open(token_path, 'r') as f:
            access_token = f.read().strip()
            kite.set_access_token(access_token)
            app.config['kite'] = kite
    except FileNotFoundError:
        print("access_token.txt not found. Please run AutoConnect.py first to generate access token.")
        app.config['kite'] = None
    except Exception as e:
        print(f"Error setting up KiteConnect: {str(e)}")
        app.config['kite'] = None

    # Initialize extensions
    assets.init_app(app)
    bootstrap.init_app(app)

    # Register blueprints
    from blueprints.main import main_bp
    from blueprints.custom_data import custom_data_bp
    from blueprints.api import api_bp
    from blueprints.custom_gtt import custom_gtt_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(custom_data_bp, url_prefix='/custom-data')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(custom_gtt_bp)

    # Configure assets
    css = Bundle('css/style.css', filters='cssmin', output='gen/packed.css')
    js = Bundle('js/script.js', filters='jsmin', output='gen/packed.js')
    assets.register('css_all', css)
    assets.register('js_all', js)

    # Error handling for missing connections
    @app.before_request
    def check_connections():
        if app.config['oracle_connection'] is None:
            flash('Database connection is not available', 'error')
        if app.config['kite'] is None:
            flash('KiteConnect is not available. Please check access token.', 'error')

    return app

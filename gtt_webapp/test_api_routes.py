import sys
import os
from flask import url_for, current_app
import logging
from pprint import pprint

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app factory function
from app import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_routes():
    """Test if the API routes are correctly registered"""
    try:
        # Create the app with test config
        app = create_app()
        
        # Create an application context
        with app.app_context(), app.test_request_context():
            print("\n=== API ROUTES TEST ===")
            print("\n1. Listing all registered rules:")
            for rule in app.url_map.iter_rules():
                print(f"Route: {rule}, Endpoint: {rule.endpoint}, Methods: {rule.methods}")
            
            print("\n2. Looking for specific API routes:")
            test_routes = [
                '/api/test',
                '/api/debug/routes',
                '/api/custom-gtt/save-order'
            ]
            
            for route in test_routes:
                try:
                    print(f"Checking route {route}...")
                    # Check if the route is in the URL map
                    matched_rules = [rule for rule in app.url_map.iter_rules() if str(rule) == route]
                    if matched_rules:
                        print(f"✓ Route {route} exists: {matched_rules[0]}")
                    else:
                        print(f"✗ Route {route} does not exist in URL map")
                except Exception as e:
                    print(f"Error checking route {route}: {str(e)}")
            
            print("\n3. Testing URL generation for endpoints:")
            test_endpoints = [
                'api.test_api',
                'api.debug_api.list_routes',
                'api.api_custom_gtt.save_order'
            ]
            
            for endpoint in test_endpoints:
                try:
                    url = url_for(endpoint)
                    print(f"✓ Endpoint {endpoint} -> {url}")
                except Exception as e:
                    print(f"✗ Cannot generate URL for endpoint {endpoint}: {str(e)}")
                    
            print("\n=== TEST COMPLETE ===")
    except Exception as e:
        logger.error(f"Error testing API routes: {str(e)}", exc_info=True)
        
if __name__ == "__main__":
    test_api_routes()

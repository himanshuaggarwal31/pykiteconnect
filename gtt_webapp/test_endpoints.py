#!/usr/bin/env python3
"""
Test script to verify all Flask webapp endpoints are working correctly.
"""

import requests
import json
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5000"

def test_endpoint(path, method="GET", data=None, expected_status=200):
    """Test a single endpoint"""
    url = urljoin(BASE_URL, path)
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        status = response.status_code
        success = status == expected_status
        
        print(f"{'✓' if success else '✗'} {method} {path} - Status: {status}")
        
        if not success and response.text:
            print(f"  Error: {response.text[:200]}...")
            
        return success
        
    except requests.exceptions.RequestException as e:
        print(f"✗ {method} {path} - Connection Error: {str(e)}")
        return False

def main():
    """Test all main endpoints"""
    print("Testing Flask webapp endpoints...")
    print("=" * 50)
    
    # Test main pages
    endpoints = [
        ("/", "GET"),
        ("/holdings/", "GET"),
        ("/custom-gtt/", "GET"),
        ("/custom-data/", "GET"),
    ]
    
    # Test API endpoints
    api_endpoints = [
        ("/holdings/api/holdings", "GET"),
        ("/api/test", "GET"),  # Test the basic API blueprint
        ("/api/debug/routes", "GET"),
        ("/api/custom-gtt/orders", "GET"),
        ("/api/gtt/orders", "GET"), # KiteConnect GTT orders
        ("/custom-data/fetch", "GET"), # Custom data fetch endpoint
    ]
    
    all_passed = True
    
    print("\nTesting Main Pages:")
    for path, method in endpoints:
        success = test_endpoint(path, method)
        all_passed = all_passed and success
    
    print("\nTesting API Endpoints:")
    for path, method in api_endpoints:
        success = test_endpoint(path, method)
        all_passed = all_passed and success
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All endpoints are working correctly!")
    else:
        print("✗ Some endpoints have issues. Check the logs above.")
    
    return all_passed

if __name__ == "__main__":
    main()

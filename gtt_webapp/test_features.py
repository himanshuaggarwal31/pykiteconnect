#!/usr/bin/env python3
"""
Interactive test script to verify key webapp features.
Run this after the Flask server is running.
"""

import requests
import json
import time
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5000"

def test_feature(name, url, description):
    """Test a feature and display results"""
    print(f"\n🔍 Testing: {name}")
    print(f"📍 URL: {url}")
    print(f"📄 Description: {description}")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ Status: {response.status_code} - SUCCESS")
            
            # Check if it's JSON response
            try:
                data = response.json()
                if isinstance(data, dict):
                    if 'holdings' in data:
                        print(f"📊 Holdings count: {len(data['holdings'])}")
                    elif 'records' in data:
                        print(f"📋 Records count: {len(data['records'])}")
                    elif 'orders' in data:
                        print(f"📈 Orders count: {len(data['orders'])}")
                    elif 'success' in data:
                        print(f"✅ Success: {data['success']}")
            except:
                print(f"📄 HTML content length: {len(response.text)} chars")
                
        else:
            print(f"❌ Status: {response.status_code} - FAILED")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Make sure Flask server is running on port 5000")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def main():
    """Run comprehensive feature tests"""
    print("=" * 60)
    print("🚀 FLASK WEBAPP FEATURE VERIFICATION")
    print("=" * 60)
    
    # Test main pages
    features = [
        ("Dashboard", f"{BASE_URL}/", "Main dashboard with GTT orders"),
        ("Holdings Page", f"{BASE_URL}/holdings/", "Portfolio holdings management"),
        ("Custom GTT", f"{BASE_URL}/custom-gtt/", "Custom GTT order management"),
        ("Custom Data", f"{BASE_URL}/custom-data/", "Custom data management"),
    ]
    
    print("\n📱 TESTING MAIN PAGES:")
    for name, url, desc in features:
        test_feature(name, url, desc)
    
    # Test API endpoints
    api_features = [
        ("Holdings API", f"{BASE_URL}/holdings/api/holdings", "Fetch holdings data with portfolio summary"),
        ("API Health", f"{BASE_URL}/api/test", "Basic API functionality test"),
        ("Custom GTT API", f"{BASE_URL}/api/custom-gtt/orders", "Fetch custom GTT orders"),
        ("KiteConnect GTT", f"{BASE_URL}/api/gtt/orders", "Fetch KiteConnect GTT orders"),
        ("Custom Data API", f"{BASE_URL}/custom-data/fetch", "Fetch custom data records"),
    ]
    
    print("\n🔌 TESTING API ENDPOINTS:")
    for name, url, desc in api_features:
        test_feature(name, url, desc)
    
    # Interactive features test prompts
    print("\n" + "=" * 60)
    print("🎯 MANUAL TESTING CHECKLIST")
    print("=" * 60)
    
    manual_tests = [
        "📊 Holdings Page Features:",
        "  • Click column headers to test sorting (Symbol, Exchange, Quantity, etc.)",
        "  • Change row count limit (10, 25, 50, 100, All)",
        "  • Test Exchange filter (NSE, BSE, All)",
        "  • Test P&L filter (Profit, Loss, All)",
        "  • Click 'Export CSV' button",
        "  • Click refresh button (circular arrow)",
        "",
        "📈 Dashboard Features:",
        "  • Check if GTT orders load correctly",
        "  • Test search functionality",
        "  • Test order type filters",
        "",
        "🎛️ Custom GTT Features:",
        "  • Test 'Place Multiple GTT Orders' modal",
        "  • Check if two-leg orders show target and stop loss fields",
        "  • Test individual order creation",
        "",
        "📋 Custom Data Features:",
        "  • Check if data table loads",
        "  • Test add/edit/delete operations",
        "  • Test data filtering",
    ]
    
    for test in manual_tests:
        print(test)
    
    print("\n" + "=" * 60)
    print("🎉 TESTING COMPLETE!")
    print("=" * 60)
    print("✅ All automated tests finished")
    print("🔍 Please perform manual testing using the checklist above")
    print("🌐 Main URL: http://127.0.0.1:5000")
    print("💼 Holdings URL: http://127.0.0.1:5000/holdings/")

if __name__ == "__main__":
    main()

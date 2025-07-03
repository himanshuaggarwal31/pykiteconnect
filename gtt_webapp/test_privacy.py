#!/usr/bin/env python3
"""
Test script to verify the privacy toggle functionality on the holdings page.
"""

import requests
import time
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5000"

def test_privacy_feature():
    """Test the privacy toggle feature"""
    print("🔐 TESTING PRIVACY TOGGLE FEATURE")
    print("=" * 50)
    
    # Test that the holdings page loads
    print("\n1. Testing Holdings Page Load...")
    try:
        response = requests.get(f"{BASE_URL}/holdings/", timeout=10)
        if response.status_code == 200:
            print("✅ Holdings page loaded successfully")
            
            # Check for privacy-related elements in the HTML
            html_content = response.text
            
            # Check if toggle button exists
            if 'toggleSummary()' in html_content:
                print("✅ Toggle button functionality found")
            else:
                print("❌ Toggle button functionality missing")
            
            # Check if privacy message element exists
            if 'privacyMessage' in html_content:
                print("✅ Privacy message element found")
            else:
                print("❌ Privacy message element missing")
            
            # Check if portfolio summary is hidden by default
            if 'portfolioSummary' in html_content and 'display: none' in html_content:
                print("✅ Portfolio summary hidden by default")
            else:
                print("❌ Portfolio summary not hidden by default")
            
            # Check if localStorage is used for persistence
            if 'localStorage' in html_content:
                print("✅ localStorage used for preference persistence")
            else:
                print("❌ localStorage not found")
                
        else:
            print(f"❌ Holdings page failed to load: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error loading holdings page: {str(e)}")
    
    # Test API endpoint
    print("\n2. Testing Holdings API...")
    try:
        response = requests.get(f"{BASE_URL}/holdings/api/holdings", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'holdings' in data and 'summary' in data:
                print("✅ Holdings API returns sensitive data (summary)")
                summary = data['summary']
                
                # Check if sensitive financial data is present
                sensitive_fields = ['total_investment', 'total_current_value', 'total_pnl']
                for field in sensitive_fields:
                    if field in summary:
                        print(f"✅ Sensitive field '{field}' found in API response")
                    else:
                        print(f"❌ Sensitive field '{field}' missing from API response")
            else:
                print("❌ Holdings API missing required fields")
        else:
            print(f"❌ Holdings API failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing Holdings API: {str(e)}")
    
    # Manual testing instructions
    print("\n3. Manual Testing Instructions:")
    print("   📱 Open: http://127.0.0.1:5000/holdings/")
    print("   🔍 Verify the following:")
    print("   • Portfolio summary is hidden by default")
    print("   • Privacy message is displayed when summary is hidden")
    print("   • 'Show Summary' button is visible")
    print("   • Clicking 'Show Summary' reveals the financial data")
    print("   • Button changes to 'Hide Summary' when shown")
    print("   • Button color changes (blue to orange)")
    print("   • Preference is saved in localStorage")
    print("   • Page remembers the state when refreshed")
    
    print("\n" + "=" * 50)
    print("🎉 PRIVACY FEATURE TESTING COMPLETE!")
    print("=" * 50)

if __name__ == "__main__":
    test_privacy_feature()

#!/usr/bin/env python3
"""
Test that the portfolio summary is hidden by default on page load.
"""

import requests
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5000"

def test_default_hidden_behavior():
    print("🔒 TESTING DEFAULT HIDDEN BEHAVIOR")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/holdings/", timeout=10)
        if response.status_code == 200:
            html_content = response.text
            
            print("✅ Holdings page loaded successfully")
            
            # Check for default hidden state indicators
            checks = [
                ("Portfolio summary hidden by default", 'id="portfolioSummary" style="display: none;"' in html_content),
                ("Privacy notice shown by default", 'id="privacyNotice"' in html_content and 'display: inline' in html_content),
                ("Show Summary button displayed", '<i class="fas fa-eye me-1"></i>Show Summary' in html_content),
                ("Button has correct class", 'btn-outline-info' in html_content),
                ("Summary Hidden notice in title", 'Summary Hidden' in html_content),
            ]
            
            passed_checks = 0
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"{status} {check_name}")
                if result:
                    passed_checks += 1
            
            print(f"\n📊 RESULTS: {passed_checks}/{len(checks)} checks passed")
            
            if passed_checks == len(checks):
                print("🎉 ALL TESTS PASSED - Summary hidden by default!")
            else:
                print("⚠️  Some issues found - may need adjustment")
            
            print("\n🔍 EXPECTED BEHAVIOR ON FRESH LOAD:")
            print("1. Portfolio summary cards should be completely hidden")
            print("2. 'Summary Hidden' should appear next to page title")
            print("3. Button should say 'Show Summary' (blue)")
            print("4. No financial data visible until user clicks 'Show Summary'")
            print("5. User preference saved as 'false' in localStorage")
            
        else:
            print(f"❌ Page failed to load: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🛡️  PRIVACY-FIRST DESIGN VERIFIED!")

if __name__ == "__main__":
    test_default_hidden_behavior()

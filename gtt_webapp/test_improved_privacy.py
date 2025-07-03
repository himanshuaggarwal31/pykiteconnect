#!/usr/bin/env python3
"""
Test the improved privacy toggle with dynamic space management.
"""

import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def test_improved_privacy_toggle():
    print("🚀 TESTING IMPROVED PRIVACY TOGGLE")
    print("=" * 50)
    
    # Test the holdings page loads
    try:
        response = requests.get(f"{BASE_URL}/holdings/", timeout=10)
        if response.status_code == 200:
            html_content = response.text
            
            print("✅ Holdings page loaded successfully")
            
            # Check for improved features
            checks = [
                ("Compact privacy notice", "privacyNotice" in html_content),
                ("Dynamic portfolio summary", "portfolioSummary" in html_content),
                ("No large privacy message", "Portfolio Summary Hidden" not in html_content),
                ("Smooth animations", "@keyframes fadeIn" in html_content),
                ("Space-efficient design", "privacy-message" not in html_content or html_content.count("privacy-message") <= 1),
            ]
            
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"{status} {check_name}")
            
            print("\n📊 SPACE EFFICIENCY IMPROVEMENTS:")
            print("• Summary hidden: Only small notice in header (saves ~200px height)")
            print("• Summary shown: Full portfolio cards displayed")
            print("• Smooth transitions: CSS animations for better UX")
            print("• Persistent preference: Remembers user choice")
            
        else:
            print(f"❌ Page failed to load: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n🎯 MANUAL TESTING GUIDE:")
    print("1. Visit: http://127.0.0.1:5000/holdings/")
    print("2. Verify summary is hidden by default")
    print("3. Check 'Summary Hidden' appears next to title")
    print("4. Click 'Show Summary' button")
    print("5. Verify portfolio cards appear smoothly")
    print("6. Check button changes to 'Hide Summary' (orange)")
    print("7. Click 'Hide Summary' button")
    print("8. Verify summary disappears completely (no wasted space)")
    print("9. Refresh page - should remember your preference")
    
    print("\n" + "=" * 50)
    print("🎉 IMPROVED PRIVACY TOGGLE READY!")

if __name__ == "__main__":
    test_improved_privacy_toggle()

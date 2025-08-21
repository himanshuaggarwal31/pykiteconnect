#!/usr/bin/env python3
"""
Optimized Kite Connect Auto Login Script
Automatically logs into Kite Connect and generates access token
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from kiteconnect import KiteConnect
from pyotp import TOTP

# Get absolute paths
APP_DIR = os.path.dirname(os.path.abspath(__file__))
GTT_WEBAPP_DIR = os.path.join(os.path.dirname(APP_DIR), 'gtt_webapp')

# File paths
TOKEN_PATH = os.path.join(APP_DIR, 'api_key.txt')
ACCESS_TOKEN_PATH = os.path.join(APP_DIR, 'access_token.txt')
GTT_ACCESS_TOKEN_PATH = os.path.join(GTT_WEBAPP_DIR, 'access_token.txt')

def auto_connect():
    """Optimized auto-connect function"""
    start_time = time.time()
    driver = None
    
    try:
        print("🚀 Starting optimized Kite Connect authentication...")
        
        # Read credentials
        with open(TOKEN_PATH, 'r') as f:
            credentials = f.read().strip().split('\n')
        
        if len(credentials) < 5:
            raise Exception("Invalid credentials format in api_key.txt")
        
        api_key, api_secret, user_id, password, totp_secret = credentials[:5]
        
        # Initialize Kite Connect
        kite = KiteConnect(api_key=api_key)
        
        # Setup optimized Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript-harmony-shipping')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--aggressive-cache-discard')
        chrome_options.add_argument('--memory-pressure-off')
        
        # Performance preferences
        prefs = {
            "profile.default_content_setting_values": {
                "images": 2,
                "plugins": 2,
                "popups": 2,
                "geolocation": 2,
                "notifications": 2,
                "media_stream": 2,
            }
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        print("⏱️  Launching browser...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(10)  # Faster timeout
        
        # Navigate to login page
        print("🌐 Loading login page...")
        driver.get(kite.login_url())
        
        # Reduced wait time
        wait = WebDriverWait(driver, 8)
        
        # Enter credentials (simplified selectors)
        print("👤 Entering username...")
        username = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="User ID"]')))
        username.clear()
        username.send_keys(user_id)
        
        print("🔑 Entering password...")
        password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Password"]')))
        password_field.clear()
        password_field.send_keys(password)
        
        # Click login
        print("📝 Clicking login...")
        login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
        login_btn.click()
        
        # Enter TOTP (minimal wait)
        print("🔐 Entering TOTP...")
        time.sleep(0.8)  # Minimal wait for page transition
        
        pin_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="PIN"]')))
        totp = TOTP(totp_secret)
        token = totp.now()
        pin_field.clear()
        pin_field.send_keys(token)
        print(f"✓ TOTP {token} entered")
        
        # Click continue
        print("➡️  Clicking continue...")
        continue_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
        continue_btn.click()
        
        # Fast polling for request token
        print("🔄 Waiting for authorization...")
        for i in range(12):  # 6 second max wait
            current_url = driver.current_url
            if 'request_token=' in current_url:
                request_token = current_url.split('request_token=')[1].split('&')[0]
                print(f"✅ Request token obtained: {request_token}")
                break
            time.sleep(0.5)
        else:
            raise Exception("Authorization timeout - no request token found")
        
        # Generate access token
        print("🎫 Generating access token...")
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        
        # Save access token to both locations
        with open(ACCESS_TOKEN_PATH, 'w') as f:
            f.write(access_token)
        
        with open(GTT_ACCESS_TOKEN_PATH, 'w') as f:
            f.write(access_token)
        
        execution_time = time.time() - start_time
        print(f"🎉 Success! Access token generated in {execution_time:.2f} seconds")
        print(f"📁 Saved to: {ACCESS_TOKEN_PATH}")
        print(f"📁 Saved to: {GTT_ACCESS_TOKEN_PATH}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = auto_connect()
    if not success:
        print("\n🔍 Troubleshooting:")
        print("1. Check api_key.txt format")
        print("2. Verify TOTP secret")
        print("3. Check internet connection")

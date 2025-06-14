# -*- coding: utf-8 -*-
"""
Zerodha kiteconnect automated authentication

@author: Mayank Rasu (http://rasuquant.com/wp/)
"""

from kiteconnect import KiteConnect
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import os
from pyotp import TOTP

# Define the app directory path and file paths
APP_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(APP_DIR, "api_key.txt")
REQUEST_TOKEN_PATH = os.path.join(APP_DIR, "request_token.txt")
ACCESS_TOKEN_PATH = os.path.join(APP_DIR, "access_token.txt")

def autologin():
    try:
        key_secret = open(TOKEN_PATH, 'r').read().split()
        kite = KiteConnect(api_key=key_secret[0])
        
        # Setup Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        
        # Initialize Chrome driver
        driver = webdriver.Chrome(options=options)
        
        driver.get(kite.login_url())
        driver.implicitly_wait(10)
        
        username = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[1]/input')
        password = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/input')
        username.send_keys(key_secret[2])
        password.send_keys(key_secret[3])
        driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[4]/button').click()
        
        pin = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div[2]/div/div[2]/form/div[1]/input')
        totp = TOTP(key_secret[4])
        token = totp.now()
        pin.send_keys(token)
        driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div[2]/div/div[2]/form/div[2]/button').click()
        
        time.sleep(10)
        request_token = driver.current_url.split('request_token=')[1][:32]
        
        # Write request token to file using the full path
        with open(REQUEST_TOKEN_PATH, 'w') as the_file:
            the_file.write(request_token)
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"Error during login: {str(e)}")
        return False

# Try to login first
if autologin():
    try:
        # Read the request token using the full path
        request_token = open(REQUEST_TOKEN_PATH, 'r').read()
        key_secret = open(TOKEN_PATH, 'r').read().split()
        kite = KiteConnect(api_key=key_secret[0])
        data = kite.generate_session(request_token, api_secret=key_secret[1])
        
        # Write access token using the full path
        with open(ACCESS_TOKEN_PATH, 'w') as file:
            file.write(data["access_token"])
        print("Access token generated and stored in 'access_token.txt'.")
        
    except Exception as e:
        print(f"Error generating session: {str(e)}")
else:
    print("Login failed. Please check your credentials and try again.")
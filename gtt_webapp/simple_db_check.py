#!/usr/bin/env python3
"""
Check if OAuth trading credentials are stored in SQLite database
"""
import os
import sqlite3

def find_database():
    """Find the SQLite database file"""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'instance', 'users.db'),
        os.path.join(os.path.dirname(__file__), 'users.db'),
        os.path.join(os.path.dirname(__file__), '..', 'users.db'),
        os.path.join(os.path.dirname(__file__), 'instance', 'app.db'),
        os.path.join(os.path.dirname(__file__), 'app.db'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def check_oauth_credentials():
    """Check if OAuth trading credentials exist in database"""
    try:
        print("=== Checking OAuth Trading Credentials ===")
        
        # Find the database
        db_path = find_database()
        if not db_path:
            print("❌ No SQLite database found in expected locations")
            print("Searched in:")
            for path in [
                os.path.join(os.path.dirname(__file__), 'instance', 'users.db'),
                os.path.join(os.path.dirname(__file__), 'users.db'),
                os.path.join(os.path.dirname(__file__), '..', 'users.db'),
                os.path.join(os.path.dirname(__file__), 'instance', 'app.db'),
                os.path.join(os.path.dirname(__file__), 'app.db'),
            ]:
                print(f"  - {path}")
            return
        
        print(f"✅ Found database at: {db_path}")
        
        # Connect to SQLite database
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # Check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Tables in database: {[table[0] for table in tables]}")
        
        # Check if users table exists
        if ('users',) in tables:
            cursor.execute("SELECT user_id, email, name FROM users")
            users = cursor.fetchall()
            
            print(f"\n👥 Found {len(users)} users:")
            for user_id, email, name in users:
                print(f"  - User ID: {user_id}, Email: {email}, Name: {name}")
        else:
            print("❌ No 'users' table found")
        
        # Check if trading_config table exists
        if ('trading_config',) in tables:
            cursor.execute("SELECT user_id, kite_api_key, kite_access_token FROM trading_config")
            configs = cursor.fetchall()
            
            print(f"\n🔑 Found {len(configs)} trading configs:")
            for user_id, api_key, access_token in configs:
                api_display = f"{api_key[:10]}..." if api_key and len(api_key) > 10 else api_key
                token_display = f"{access_token[:10]}..." if access_token and len(access_token) > 10 else access_token
                print(f"  - User ID: {user_id}")
                print(f"    API Key: {api_display}")
                print(f"    Access Token: {token_display}")
        else:
            print("❌ No 'trading_config' table found")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_oauth_credentials()

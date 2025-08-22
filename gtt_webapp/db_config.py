import socket
import os
import oracledb
from flask import current_app
from dotenv import load_dotenv

# Load environment variables from .env file in the same directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Detect the host machine and configure paths accordingly
if socket.gethostname() == 'Tuf':
    configuration = {
        "download_folder": os.getenv('DOWNLOAD_FOLDER_WINDOWS', r"C:\Himanshu\Stocks_Data"),
        "log_folder": os.getenv('LOG_FOLDER_WINDOWS', r"C:\Himanshu\Stocks_Data\logs"),
        "db_config": {
            "user": os.getenv('ORACLE_USER'),
            "password": os.getenv('ORACLE_PASSWORD'),
            "dsn": os.getenv('ORACLE_DSN'),
            "config_dir": os.getenv('ORACLE_CONFIG_DIR_WINDOWS', r"C:\instantclient_19_9\network\admin"),
            "wallet_location": os.getenv('ORACLE_WALLET_LOCATION_WINDOWS', r"C:\instantclient_19_9\network\admin"),
            "wallet_password": os.getenv('ORACLE_WALLET_PASSWORD')
        }
    }
else:
    configuration = {
        "log_folder": os.getenv('LOG_FOLDER_LINUX', r"/home/opc/stocks_data/logs"),
        "download_folder": os.getenv('DOWNLOAD_FOLDER_LINUX', r"/home/opc/stocks_data/files"),
        "db_config": {
            "user": os.getenv('ORACLE_USER'),
            "password": os.getenv('ORACLE_PASSWORD'),
            "dsn": os.getenv('ORACLE_DSN'),
            "config_dir": os.getenv('ORACLE_CONFIG_DIR_LINUX', r"/home/opc/instantclient_19_21/network/admin"),
            "wallet_location": os.getenv('ORACLE_WALLET_LOCATION_LINUX', r"/home/opc/instantclient_19_21/network/admin"),
            "wallet_password": os.getenv('ORACLE_WALLET_PASSWORD')
        }
    }

def get_connection():
    """Get a fresh database connection"""
    try:
        # Validate that required environment variables are set
        required_vars = ['ORACLE_USER', 'ORACLE_PASSWORD', 'ORACLE_DSN', 'ORACLE_WALLET_PASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Required environment variables not set: {', '.join(missing_vars)}")
        
        return oracledb.connect(**configuration['db_config'])
    except oracledb.Error as e:
        print(f"Database connection error: {e}")
        raise
    except ValueError as e:
        print(f"Configuration error: {e}")
        raise

# Access the folders or config using config['log_folder'], etc.

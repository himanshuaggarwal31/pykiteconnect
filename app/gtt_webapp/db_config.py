import socket
import os
import oracledb
from flask import current_app

# Detect the host machine and configure paths accordingly
if socket.gethostname() == 'Tuf':
    configuration = {
        "download_folder": r"C:\Himanshu\Stocks_Data",
        "log_folder": r"C:\Himanshu\Stocks_Data\logs",
        "db_config": {
            "user": "Admin",
            "password": "Stocks4me@2024",  # Change password here when needed
            "dsn": "rc7e560lbdb02x6x_high",
            "config_dir": r"C:\instantclient_19_9\network\admin",
            "wallet_location": r"C:\instantclient_19_9\network\admin",
            "wallet_password": "Oracle@31"
        }
    }
else:
    configuration = {
        "log_folder": r"/home/opc/stocks_data/logs",
        "download_folder": r"/home/opc/stocks_data/files",
        "db_config": {
            "user": "Admin",
            "password": "Stocks4me@2024",  # Change password here when needed
            "dsn": "rc7e560lbdb02x6x_high",
            "config_dir": r"/home/opc/instantclient_19_21/network/admin",
            "wallet_location": r"/home/opc/instantclient_19_21/network/admin",
            "wallet_password": "Oracle@31"
        }
    }

def get_connection():
    """Get a database connection using the current app's connection or create a new one"""
    if current_app and 'oracle_connection' in current_app.config:
        return current_app.config['oracle_connection']
    return oracledb.connect(**configuration['db_config'])

# Access the folders or config using config['log_folder'], etc.

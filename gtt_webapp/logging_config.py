import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(app.root_path), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up file handler for custom_data operations with UTF-8 encoding
    custom_data_handler = RotatingFileHandler(
        os.path.join(log_dir, 'custom_data.log'),
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10,
        encoding='utf-8'
    )
    custom_data_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    
    # Create logger for custom_data
    custom_data_logger = logging.getLogger('custom_data')
    custom_data_logger.setLevel(logging.DEBUG)
    custom_data_logger.addHandler(custom_data_handler)
    
    # Add handler to app logger as well
    app.logger.addHandler(custom_data_handler)
    
    return custom_data_logger

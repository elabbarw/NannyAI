import logging
import os
from datetime import datetime

def setup_logger():
    """Setup and return the main logger"""
    logger = logging.getLogger('screen_monitor')
    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    os.makedirs('data/logs', exist_ok=True)

    # File handler
    log_file = f'data/logs/monitor_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def get_logger(name):
    """Get a named logger"""
    return logging.getLogger(f'screen_monitor.{name}')

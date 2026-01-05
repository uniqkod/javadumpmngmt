"""
Logging Configuration

Sets up structured logging for the application.
"""

import logging
import sys
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)


def setup_logging(log_level: str = 'INFO') -> logging.Logger:
    """
    Setup application logging.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Logger instance
    """
    # Convert string level to logging level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = JSONFormatter()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Get application logger
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized with level: {log_level}")
    
    return logger

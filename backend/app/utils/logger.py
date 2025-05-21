"""
Logging utility for TaxPoynt eInvoice.

This module provides a standardized logging setup for the entire application.
It configures loggers with appropriate handlers and formatters.
"""

import logging
import sys
from typing import Optional

from app.core.config import settings


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger configured with the application's standard settings.
    
    Args:
        name: Logger name, typically the module name using __name__
        
    Returns:
        Configured logger instance
    """
    logger_name = name or "taxpoynt.einvoice"
    logger = logging.getLogger(logger_name)
    
    # Only configure the logger if it hasn't been configured yet
    if not logger.handlers:
        # Set the log level from settings
        log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
        logger.setLevel(log_level)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        
        # Prevent propagation to the root logger to avoid duplicate logs
        logger.propagate = False
        
    return logger

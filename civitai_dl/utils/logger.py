"""Logging utilities for Civitai Downloader.

This module provides centralized logging configuration and utilities.
"""

import logging
import os
import sys
from typing import Dict, Optional, Union

# Default logging configuration
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LEVEL = logging.INFO

# Cache loggers to avoid duplicate configuration
_loggers: Dict[str, logging.Logger] = {}


def setup_logging(
    level: int = DEFAULT_LEVEL,
    log_file: Optional[str] = None,
    format_str: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
) -> None:
    """Set up global logging configuration.
    
    Args:
        level: Console log level
        log_file: Optional log file path
        format_str: Log format string
        date_format: Date format string
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(format_str, date_format)
    
    # Add console handler
    console = logging.StreamHandler(stream=sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    root_logger.addHandler(console)
    
    # Add file handler if specified
    if log_file:
        # Create directory if needed
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # File gets more detailed logs
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    _loggers[name] = logger
    return logger


def set_log_level(level: Union[int, str]) -> None:
    """Set log level for all loggers.
    
    Args:
        level: Log level as integer or string name
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Update existing handlers
    for handler in root_logger.handlers:
        handler.setLevel(level)

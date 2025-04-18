"""Environment variable handling utilities for Civitai Downloader.

This module provides functions for loading and managing environment variables,
including loading from .env files for application configuration.
"""

import os
import re
import logging
from typing import Dict, Optional

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


def load_env_file(env_file: Optional[str] = None) -> Dict[str, str]:
    """Load environment variables from a .env file.
    
    Args:
        env_file: Path to the .env file, if None will look in project root
        
    Returns:
        Dictionary of loaded environment variables
    """
    loaded_vars = {}
    
    if env_file is None:
        # Try to find project root directory
        current_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        env_file = os.path.join(current_dir, ".env")

    # Load .env file if it exists
    if os.path.isfile(env_file):
        logger.info(f"Loading environment variables from {env_file}")
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Parse variable assignments
                    match = re.match(r"^([A-Za-z0-9_]+)=(.*)$", line)
                    if match:
                        key, value = match.groups()
                        # Don't override existing environment variables
                        if key not in os.environ:
                            os.environ[key] = value
                            loaded_vars[key] = value
                            logger.debug(f"Set environment variable: {key}")
        except Exception as e:
            logger.error(f"Error loading .env file: {str(e)}")
    else:
        logger.debug(f"No .env file found at {env_file}")
    
    return loaded_vars


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with fallback to default.
    
    Args:
        key: Environment variable name
        default: Default value if variable is not set
        
    Returns:
        Environment variable value or default
    """
    return os.environ.get(key, default)


def set_env(key: str, value: str) -> None:
    """Set environment variable.
    
    Args:
        key: Environment variable name
        value: Value to set
    """
    os.environ[key] = value
    logger.debug(f"Set environment variable: {key}")

"""配置管理工具

处理程序配置的读取、保存和默认值设置
"""

import os
import json
from typing import Dict, Any, Optional

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)

# 定义配置文件路径
USER_HOME = os.path.expanduser("~")
CONFIG_DIR = os.path.join(USER_HOME, ".civitai_dl")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# 默认配置
DEFAULT_CONFIG = {
    "api_key": "",
    "output_dir": os.path.join(USER_HOME, "Downloads", "civitai"),
    "concurrent_downloads": 3,
    "max_retries": 3,
    "timeout": 30,
    "verify_ssl": True,
    "proxy": "",
    "download_images": True,
    "save_metadata": True,
    "file_exists_action": "ask",  # ask, skip, overwrite, rename
    "path_template": "{type}/{creator}/{name}",
    "preferred_format": "SafeTensor",
}

# 显式定义可以从此模块导入的名称
__all__ = [
    'CONFIG_DIR', 'CONFIG_FILE', 'DEFAULT_CONFIG',
    'get_config', 'save_config', 'update_config', 
    'get_config_value', 'set_config_value', 
    'add_recent_directory', 'get_download_dir',
    'ensure_config_dir', 'get_config_path'
]

def get_config_path() -> str:
    """Get the path to the configuration file.

    Uses environment variable if set, otherwise uses default path.

    Returns:
        Configuration file path
    """
    return os.environ.get("CIVITAI_CONFIG_PATH", CONFIG_FILE)


def get_config() -> Dict[str, Any]:
    """Load and return the application configuration.

    Loads from config file, with fallback to default configuration.

    Returns:
        Configuration dictionary
    """
    config_path = get_config_path()

    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.debug(f"Loaded configuration from {config_path}")
                return config
        else:
            logger.info(f"Configuration file not found at {config_path}, using defaults")
            return get_default_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        return get_default_config()


def save_config(config: Dict[str, Any]) -> bool:
    """Save the configuration to file.

    Args:
        config: Configuration dictionary to save

    Returns:
        True if successful, False otherwise
    """
    config_path = get_config_path()

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.debug(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save configuration: {str(e)}")
        return False


def get_default_config() -> Dict[str, Any]:
    """Get the default configuration.

    Returns:
        Default configuration dictionary
    """
    return DEFAULT_CONFIG


def set_config_value(key: str, value: Any) -> bool:
    """Set a specific configuration value.

    Args:
        key: Configuration key
        value: Value to set

    Returns:
        True if successful, False otherwise
    """
    try:
        config = get_config()
        config[key] = value
        return save_config(config)
    except Exception as e:
        logger.error(f"Failed to set config value: {str(e)}")
        return False


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value.

    Args:
        key: Configuration key
        default: Default value if key not found

    Returns:
        Configuration value or default
    """
    try:
        config = get_config()
        return config.get(key, default)
    except Exception as e:
        logger.error(f"Failed to get config value: {str(e)}")
        return default


def add_recent_directory(directory: str, max_entries: int = 10) -> bool:
    """Add a directory to the recent directories list.

    Args:
        directory: Directory path to add
        max_entries: Maximum number of recent directories to keep

    Returns:
        True if successful, False otherwise
    """
    try:
        config = get_config()
        recent_dirs = config.get("recent_directories", [])

        # Remove existing entry if present
        if directory in recent_dirs:
            recent_dirs.remove(directory)

        # Add to the beginning
        recent_dirs.insert(0, directory)

        # Limit list length
        config["recent_directories"] = recent_dirs[:max_entries]

        return save_config(config)
    except Exception as e:
        logger.error(f"Failed to add recent directory: {str(e)}")
        return False


def get_download_dir(model_type: Optional[str] = None) -> str:
    """Get the appropriate download directory for a model type.

    Args:
        model_type: Model type to get directory for

    Returns:
        Download directory path
    """
    config = get_config()
    base_dir = config.get("output_dir", os.path.join(os.getcwd(), "downloads"))

    if not model_type:
        return base_dir

    # Get type-specific directory mapping
    type_dirs = config.get("model_type_dirs", {})
    type_subdir = type_dirs.get(model_type, model_type)

    return os.path.join(base_dir, type_subdir)

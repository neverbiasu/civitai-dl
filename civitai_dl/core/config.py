"""Configuration management for Civitai Downloader.

Provides functionality for loading, saving, and accessing application configuration.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.civitai-downloader/config.json")
RECENT_DIRS_MAX = 10


class ConfigManager:
    """Configuration manager for storing and retrieving application settings."""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH) -> None:
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults.

        Returns:
            Configuration dictionary
        """
        try:
            if not os.path.exists(self.config_path):
                # Ensure config directory exists
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                return self._get_default_config()

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Ensure all required config keys exist
            default_config = self._get_default_config()
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value

            return config
        except Exception as e:
            logger.warning(f"Failed to load configuration: {str(e)}, using defaults")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration settings.

        Returns:
            Default configuration dictionary
        """
        return {
            "api_key": "",
            "proxy": "",
            "timeout": 30,
            "max_retries": 3,
            "verify_ssl": True,
            "concurrent_downloads": 3,
            "chunk_size": 8192,
            "output_dir": os.path.join(os.getcwd(), "downloads"),
            "model_type_dirs": {
                "Checkpoint": "Checkpoints",
                "LORA": "LoRAs",
                "TextualInversion": "Embeddings",
                "Hypernetwork": "Hypernetworks",
                "AestheticGradient": "AestheticGradients",
                "Controlnet": "ControlNets",
                "Poses": "Poses"
            },
            "ask_download_location": False,
            "use_original_filename": True,
            "file_exists_action": "ask",
            "recent_directories": [],
            "theme": "light"
        }

    def save_config(self) -> bool:
        """Save configuration to file.

        Ensures the directory exists before writing the configuration file
        and handles various error conditions gracefully.

        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Ensure config directory exists
            config_dir = os.path.dirname(self.config_path)
            os.makedirs(config_dir, exist_ok=True)
            logger.debug(f"Ensuring config directory exists: {config_dir}")

            # Write config with proper formatting
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)

            logger.debug(f"Configuration saved to {self.config_path}")
            return True

        except OSError as e:
            logger.error(f"Failed to create directory for config: {str(e)}")
            return False
        except IOError as e:
            logger.error(f"Failed to write config file: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            return False

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key name
            default: Value to return if key doesn't exist

        Returns:
            Configuration value or default if not found
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value.

        Args:
            key: Configuration key name
            value: New value for the configuration key

        Returns:
            True if the value was set successfully, False otherwise
        """
        self.config[key] = value
        return self.save_config()

    def get_download_dir(self, model_type: Optional[str] = None) -> str:
        """Get the download directory, optionally for a specific model type.

        Args:
            model_type: Model type

        Returns:
            Download directory path
        """
        base_dir = self.config.get("output_dir", os.path.join(os.getcwd(), "downloads"))

        # If a model type is specified, return the corresponding subdirectory
        if model_type and model_type in self.config.get("model_type_dirs", {}):
            type_dir = self.config["model_type_dirs"][model_type]
            return os.path.join(base_dir, type_dir)

        return base_dir

    def add_recent_directory(self, directory: str) -> None:
        """Add a directory to the list of recent directories.

        Args:
            directory: Directory path
        """
        # Ensure recent_directories exists
        if "recent_directories" not in self.config:
            self.config["recent_directories"] = []

        # If the directory is already in the list, remove it first
        if directory in self.config["recent_directories"]:
            self.config["recent_directories"].remove(directory)

        # Add to the beginning of the list
        self.config["recent_directories"].insert(0, directory)

        # Limit the list length
        self.config["recent_directories"] = self.config["recent_directories"][:RECENT_DIRS_MAX]

        # Save configuration
        self.save_config()

    def get_recent_directories(self) -> List[str]:
        """Get the list of recent directories.

        Returns:
            List of directory paths
        """
        return self.config.get("recent_directories", [])


# Create a global instance of the configuration manager
config_manager = ConfigManager()


def get_config() -> Dict[str, Any]:
    """Get the current configuration.

    Returns:
        Configuration dictionary
    """
    return config_manager.config


def set_config_value(key: str, value: Any) -> bool:
    """Set a configuration value.

    Args:
        key: Configuration key name
        value: New value for the configuration key

    Returns:
        True if the value was set successfully, False otherwise
    """
    return config_manager.set(key, value)


def get_config_value(key: str, default: Optional[Any] = None) -> Any:
    """Get a configuration value.

    Args:
        key: Configuration key name
        default: Value to return if key doesn't exist

    Returns:
        Configuration value or default if not found
    """
    return config_manager.get(key, default)

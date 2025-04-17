import os
import json
import logging
from typing import Dict, Any, List, Optional

# 配置日志
logger = logging.getLogger(__name__)

# 默认配置路径
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.civitai-downloader/config.json")

# 最近使用的目录数量
RECENT_DIRS_MAX = 10


class ConfigManager:
    """配置管理类，负责读取和保存用户配置"""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """从文件加载配置，如果文件不存在则返回默认配置"""
        try:
            if not os.path.exists(self.config_path):
                # 确保配置目录存在
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                return self._get_default_config()

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 确保所有必要的配置项都存在
            default_config = self._get_default_config()
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value

            return config
        except Exception as e:
            logger.warning(f"加载配置失败: {str(e)}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """返回默认配置"""
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
            "ask_download_location": False,  # 新选项：是否每次下载前询问目标位置
            "use_original_filename": True,   # 新选项：是否使用原始文件名
            "file_exists_action": "ask",     # 新选项：文件已存在时的操作 (ask/overwrite/rename/skip)
            "recent_directories": [],        # 新列表：最近使用的目录
            "theme": "light"
        }

    def save_config(self) -> bool:
        """保存配置到文件

        Returns:
            保存是否成功
        """
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False

    def get(self, key: str, default=None) -> Any:
        """获取配置项的值

        Args:
            key: 配置项键名
            default: 如果键不存在，返回的默认值

        Returns:
            配置项的值
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """设置配置项的值

        Args:
            key: 配置项键名
            value: 配置项的新值

        Returns:
            设置是否成功
        """
        self.config[key] = value
        return self.save_config()

    def get_download_dir(self, model_type: Optional[str] = None) -> str:
        """获取下载目录，可以根据模型类型获取不同的子目录

        Args:
            model_type: 模型类型

        Returns:
            下载目录路径
        """
        base_dir = self.config.get("output_dir", os.path.join(os.getcwd(), "downloads"))

        # 如果指定了模型类型，返回对应的子目录
        if model_type and model_type in self.config.get("model_type_dirs", {}):
            type_dir = self.config["model_type_dirs"][model_type]
            return os.path.join(base_dir, type_dir)

        return base_dir

    def add_recent_directory(self, directory: str) -> None:
        """添加一个目录到最近使用目录列表

        Args:
            directory: 目录路径
        """
        # 确保recent_directories存在
        if "recent_directories" not in self.config:
            self.config["recent_directories"] = []

        # 如果目录已在列表中，先移除
        if directory in self.config["recent_directories"]:
            self.config["recent_directories"].remove(directory)

        # 添加到列表开头
        self.config["recent_directories"].insert(0, directory)

        # 限制列表长度
        self.config["recent_directories"] = self.config["recent_directories"][:RECENT_DIRS_MAX]

        # 保存配置
        self.save_config()

    def get_recent_directories(self) -> List[str]:
        """获取最近使用的目录列表

        Returns:
            目录路径列表
        """
        return self.config.get("recent_directories", [])


# 创建全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> Dict[str, Any]:
    """获取当前配置

    Returns:
        配置字典
    """
    return config_manager.config


def set_config_value(key: str, value: Any) -> bool:
    """设置配置项的值

    Args:
        key: 配置项键名
        value: 配置项的新值

    Returns:
        设置是否成功
    """
    return config_manager.set(key, value)


def get_config_value(key: str, default=None) -> Any:
    """获取配置项的值

    Args:
        key: 配置项键名
        default: 如果键不存在，返回的默认值

    Returns:
        配置项的值
    """
    return config_manager.get(key, default)

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    "api_key": "",
    "output_dir": "./downloads",
    "concurrent_downloads": 3,
    "chunk_size": 8192,
    "timeout": 30,
    "max_retries": 3,
    "verify_ssl": True,
    "path_template": "{type}/{creator}/{name}",
    "image_path_template": "images/{model_id}/{image_id}",
    "proxy": "",
    "save_metadata": True,
    "theme": "light",
    "nsfw_filter": "exclude",  # options: exclude, include, only
}

# 配置文件路径
CONFIG_FILE = os.path.expanduser("~/.civitai-dl/config.json")

# 全局配置对象
_config = None


def get_config() -> Dict[str, Any]:
    """
    获取配置，如果尚未加载，则从文件加载
    
    Returns:
        配置字典
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def load_config() -> Dict[str, Any]:
    """
    从文件加载配置
    
    Returns:
        配置字典
    """
    # 确保配置目录存在
    config_dir = os.path.dirname(CONFIG_FILE)
    os.makedirs(config_dir, exist_ok=True)
    
    # 如果配置文件不存在，创建默认配置
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    # 加载配置文件
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 确保所有默认项都存在
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value
        
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """
    保存配置到文件
    
    Args:
        config: 配置字典
        
    Returns:
        是否成功保存
    """
    global _config
    _config = config
    
    # 确保配置目录存在
    config_dir = os.path.dirname(CONFIG_FILE)
    os.makedirs(config_dir, exist_ok=True)
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")
        return False


def get_config_value(key: str, default: Any = None) -> Any:
    """
    获取指定配置项的值
    
    Args:
        key: 配置项名称
        default: 如果配置项不存在，返回的默认值
        
    Returns:
        配置项值或默认值
    """
    config = get_config()
    return config.get(key, default)


def set_config_value(key: str, value: Any) -> bool:
    """
    设置指定配置项的值
    
    Args:
        key: 配置项名称
        value: 配置项值
        
    Returns:
        是否成功设置
    """
    config = get_config()
    config[key] = value
    return save_config(config)


def export_config(file_path: str) -> bool:
    """
    导出配置到指定文件
    
    Args:
        file_path: 导出文件路径
        
    Returns:
        是否成功导出
    """
    config = get_config()
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        return False


def import_config(file_path: str) -> bool:
    """
    从指定文件导入配置
    
    Args:
        file_path: 导入文件路径
        
    Returns:
        是否成功导入
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 确保关键字段存在
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value
        
        return save_config(config)
    except Exception as e:
        logger.error(f"导入配置失败: {e}")
        return False

import os
import json
from typing import Dict, Any, Optional

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    "api_key": None,
    "output_dir": "./downloads",
    "concurrent_downloads": 3,
    "nsfw_level": "None",
    "auto_extract_metadata": True,
    "default_model_format": None,
    "proxy": None,                # 默认不使用代理
    "verify_ssl": True,           # 默认验证SSL证书
    "timeout": 30,                # 默认超时时间(秒)
    "max_retries": 3,             # 默认最大重试次数
    "retry_delay": 2              # 默认重试间隔(秒)
}

# 配置文件路径
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.civitai-dl/config.json")

# 全局配置对象
_config: Optional[Dict[str, Any]] = None


def get_config(reload: bool = False) -> Dict[str, Any]:
    """获取应用配置"""
    global _config

    if _config is None or reload:
        _config = load_config()

    return _config


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载配置文件"""
    config_path = config_path or DEFAULT_CONFIG_PATH

    # 使用默认配置作为基础
    config = DEFAULT_CONFIG.copy()

    # 尝试读取配置文件
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
                logger.debug(f"已加载配置文件: {config_path}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
    else:
        logger.debug(f"配置文件不存在，使用默认配置: {config_path}")

    # 检查环境变量覆盖
    if 'CIVITAI_API_KEY' in os.environ:
        config['api_key'] = os.environ['CIVITAI_API_KEY']
        logger.debug("从环境变量加载了API密钥")

    if 'CIVITAI_PROXY' in os.environ:
        config['proxy'] = os.environ['CIVITAI_PROXY']
        logger.debug("从环境变量加载了代理设置")

    return config


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """保存配置到文件"""
    config_path = config_path or DEFAULT_CONFIG_PATH

    # 确保目录存在
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.debug(f"已保存配置到: {config_path}")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return False


def update_config(updates: Dict[str, Any], save: bool = True) -> Dict[str, Any]:
    """更新配置"""
    config = get_config()
    config.update(updates)

    if save:
        save_config(config)

    return config

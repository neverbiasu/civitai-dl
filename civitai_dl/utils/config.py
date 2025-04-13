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
    "proxy": None,  # 默认不使用代理
    "verify_ssl": True,  # 默认验证SSL证书
    "timeout": 30,  # 默认超时时间(秒)
    "max_retries": 3,  # 默认最大重试次数
    "retry_delay": 2,  # 默认重试间隔(秒)
    "path_template": "{type}/{creator}/{name}",  # 默认路径模板
    "extract_image_metadata": True,  # 默认提取图像元数据
    "save_model_metadata": True,  # 默认保存模型元数据
    "log_level": "info",  # 默认日志级别
    "log_file": None,  # 默认不使用日志文件
}

# 配置文件路径
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.civitai-dl/config.json")

# 全局配置对象
_config: Optional[Dict[str, Any]] = None


def get_config() -> Dict[str, Any]:
    """
    获取配置，如果尚未加载则从文件加载
    
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
    config = DEFAULT_CONFIG.copy()
    
    # 尝试从配置文件加载
    try:
        if os.path.exists(DEFAULT_CONFIG_PATH):
            with open(DEFAULT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                config.update(user_config)
                logger.debug(f"从 {DEFAULT_CONFIG_PATH} 加载配置")
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}，将使用默认配置")
    
    # 从环境变量加载配置
    for key in DEFAULT_CONFIG:
        env_key = f"CIVITAI_DL_{key.upper()}"
        if env_key in os.environ:
            value = os.environ[env_key]
            # 尝试转换布尔值
            if value.lower() in ('true', 'yes', '1'):
                config[key] = True
            elif value.lower() in ('false', 'no', '0'):
                config[key] = False
            # 尝试转换数字
            elif value.isdigit():
                config[key] = int(value)
            elif value.replace('.', '', 1).isdigit():
                config[key] = float(value)
            else:
                config[key] = value
                
    return config


def save_config(config: Dict[str, Any]) -> bool:
    """
    保存配置到文件
    
    Args:
        config: 配置字典
        
    Returns:
        保存是否成功
    """
    try:
        # 确保配置目录存在
        os.makedirs(os.path.dirname(DEFAULT_CONFIG_PATH), exist_ok=True)
        
        # 写入配置文件
        with open(DEFAULT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            
        # 更新全局配置对象
        global _config
        _config = config.copy()
        
        logger.info(f"配置已保存至 {DEFAULT_CONFIG_PATH}")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return False


def update_config(updates: Dict[str, Any]) -> bool:
    """
    更新部分配置项
    
    Args:
        updates: 要更新的配置项字典
        
    Returns:
        更新是否成功
    """
    # 获取当前配置
    config = get_config()
    
    # 应用更新
    config.update(updates)
    
    # 保存更新后的配置
    return save_config(config)


def reset_config() -> bool:
    """
    重置配置为默认值
    
    Returns:
        重置是否成功
    """
    return save_config(DEFAULT_CONFIG.copy())

"""
代理设置模块 - 配置和管理HTTP代理
"""

import os
from typing import Dict

# 默认代理设置
DEFAULT_PROXY = "http://127.0.0.1:7890"
DEFAULT_NO_PROXY = "localhost,127.0.0.1"

def get_proxy_settings() -> Dict[str, str]:
    """
    获取系统代理设置
    
    Returns:
        包含代理设置的字典，格式为 {'http': '...', 'https': '...'}
    """
    proxy_settings = {}
    
    # 首先尝试从环境变量获取
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    
    # 如果环境变量中没有设置，使用默认设置
    if not http_proxy:
        http_proxy = DEFAULT_PROXY
    if not https_proxy:
        https_proxy = DEFAULT_PROXY
    
    proxy_settings['http'] = http_proxy
    proxy_settings['https'] = https_proxy
    
    return proxy_settings

def setup_proxy_environment():
    """
    设置代理环境变量
    """
    os.environ['HTTP_PROXY'] = DEFAULT_PROXY
    os.environ['HTTPS_PROXY'] = DEFAULT_PROXY
    os.environ['NO_PROXY'] = DEFAULT_NO_PROXY
    
def get_verify_ssl() -> bool:
    """
    判断是否应该验证SSL
    
    Returns:
        布尔值，表示是否验证SSL
    """
    # 目前默认返回False以避免代理SSL问题
    # 在生产环境中应该根据实际情况调整
    return False

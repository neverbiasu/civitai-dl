"""
重定向导入到新的API客户端模块
为保持向后兼容性而保留此文件
"""

from civitai_dl.api.client import CivitaiAPI, APIError

# 为向后兼容性导出所有相同的符号
__all__ = ["CivitaiAPI", "APIError"]

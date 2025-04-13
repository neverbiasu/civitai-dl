"""路径模板解析与处理工具"""

import os
import re
import string
from typing import Dict, Any, Optional
import unicodedata
import datetime

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


def parse_template(
    template: str, 
    variables: Dict[str, Any], 
    default_value: str = "unknown"
) -> str:
    """
    解析路径模板，替换变量
    
    Args:
        template: 包含变量的模板字符串，例如"{type}/{creator}/{name}"
        variables: 变量值字典
        default_value: 变量不存在时的默认值
        
    Returns:
        替换变量后的路径字符串
    """
    try:
        # 使用string.Template进行变量替换
        # 首先将{var}格式转换为$var格式
        dollar_template = re.sub(r'\{([^}]+)\}', r'$\1', template)
        template_obj = string.Template(dollar_template)
        
        # 为缺失的变量提供默认值
        safe_vars = SafeDict(variables, default_value)
        
        # 执行替换
        result = template_obj.safe_substitute(safe_vars)
        
        # 清理路径（移除不安全字符）
        result = sanitize_path(result)
        
        return result
    except Exception as e:
        logger.error(f"解析模板失败: {str(e)}")
        # 出错时返回简单路径
        return datetime.datetime.now().strftime("%Y-%m-%d")


def sanitize_path(path: str) -> str:
    """
    清理路径字符串，移除不安全字符
    
    Args:
        path: 原始路径字符串
        
    Returns:
        清理后的安全路径字符串
    """
    # 规范化Unicode字符
    path = unicodedata.normalize('NFKD', path)
    
    # 替换Windows不支持的文件名字符
    invalid_chars = r'[<>:"/\\|?*]'
    path = re.sub(invalid_chars, '_', path)
    
    # 替换连续的分隔符
    path = re.sub(r'_{2,}', '_', path)
    
    # 移除前导和尾随空格，以及路径分隔符
    path = path.strip(' /')
    
    # 确保路径中的每个部分都不超过255个字符(Windows限制)
    parts = []
    for part in path.split('/'):
        if len(part) > 255:
            part = part[:252] + '...'
        parts.append(part)
    
    return '/'.join(parts)


class SafeDict(dict):
    """
    安全的字典类，当键不存在时返回默认值
    """
    def __init__(self, data: Dict[str, Any], default_value: str):
        super().__init__(data)
        self.default = default_value
        
    def __missing__(self, key):
        logger.debug(f"模板变量不存在: {key}，使用默认值: {self.default}")
        return self.default


def apply_model_template(
    template: str, 
    model_info: Dict[str, Any], 
    version_info: Optional[Dict[str, Any]] = None,
    file_info: Optional[Dict[str, Any]] = None
) -> str:
    """
    为模型应用路径模板
    
    Args:
        template: 路径模板
        model_info: 模型信息字典
        version_info: 版本信息字典(可选)
        file_info: 文件信息字典(可选)
        
    Returns:
        应用模板后的路径
    """
    variables = {}
    
    # 从模型信息提取变量
    if model_info:
        variables.update({
            "id": str(model_info.get("id", "")),
            "name": model_info.get("name", ""),
            "type": model_info.get("type", ""),
            "nsfw": "nsfw" if model_info.get("nsfw", False) else "sfw",
        })
        
        # 提取创建者信息
        creator = model_info.get("creator", {})
        if creator:
            variables["creator"] = creator.get("username", "")
            variables["creator_id"] = str(creator.get("id", ""))
        
    # 从版本信息提取变量
    if version_info:
        variables.update({
            "version_id": str(version_info.get("id", "")),
            "version_name": version_info.get("name", ""),
            "base_model": version_info.get("baseModel", ""),
        })
    
    # 从文件信息提取变量
    if file_info:
        variables.update({
            "file_id": str(file_info.get("id", "")),
            "file_name": file_info.get("name", ""),
            "file_format": os.path.splitext(file_info.get("name", ""))[1][1:],
        })
        
        # 从元数据提取格式信息
        metadata = file_info.get("metadata", {})
        if metadata:
            variables["format"] = metadata.get("format", "")
            
    # 添加日期变量
    now = datetime.datetime.now()
    variables.update({
        "year": now.strftime("%Y"),
        "month": now.strftime("%m"),
        "day": now.strftime("%d"),
        "date": now.strftime("%Y-%m-%d"),
    })
    
    return parse_template(template, variables)

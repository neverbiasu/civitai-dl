"""路径模板解析与处理工具"""

import datetime
import os
import re
import string
import unicodedata
from typing import Any, Dict, Optional

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


def parse_template(
    template: str, variables: Dict[str, Any], default_value: str = "unknown"
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
        dollar_template = re.sub(r"\{([^}]+)\}", r"$\1", template)
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
    path = unicodedata.normalize("NFKD", path)

    # 替换Windows不支持的文件名字符
    invalid_chars = r'[<>:"/\\|?*]'
    path = re.sub(invalid_chars, "_", path)

    # 替换连续的分隔符
    path = re.sub(r"_{2,}", "_", path)

    # 移除前导和尾随空格，以及路径分隔符
    path = path.strip(" /")

    # 确保路径中的每个部分都不超过255个字符(Windows限制)
    parts = []
    for part in path.split("/"):
        if len(part) > 255:
            part = part[:252] + "..."
        parts.append(part)

    return "/".join(parts)


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
    file_info: Optional[Dict[str, Any]] = None,
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
        variables.update(
            {
                "type": model_info.get("type", "Unknown"),
                "name": model_info.get("name", "Unknown"),
                "id": model_info.get("id", 0),
                "nsfw": "nsfw" if model_info.get("nsfw", False) else "sfw",
            }
        )

        # 提取创建者信息
        creator = model_info.get("creator", {})
        if creator:
            variables["creator"] = creator.get("username", "Unknown")
            variables["creator_id"] = creator.get("id", 0)

    # 从版本信息提取变量
    if version_info:
        variables.update(
            {
                "version": version_info.get("name", "Unknown"),
                "version_id": version_info.get("id", 0),
                "base_model": version_info.get("baseModel", "Unknown"),
            }
        )

    # 从文件信息提取变量
    if file_info:
        filename = file_info.get("name", "Unknown")
        variables.update(
            {
                "filename": filename,
                "format": os.path.splitext(filename)[1][1:].lower()
                if "." in filename
                else "",
            }
        )

    # 添加日期变量
    now = datetime.datetime.now()
    variables.update(
        {
            "year": now.strftime("%Y"),
            "month": now.strftime("%m"),
            "day": now.strftime("%d"),
            "date": now.strftime("%Y-%m-%d"),
        }
    )

    # 安全处理所有字符串值
    for k, v in variables.items():
        if isinstance(v, str):
            variables[k] = sanitize_path(v)

    # 应用模板
    try:
        path = template.format(**variables)
        # 规范化路径分隔符
        return os.path.normpath(path)
    except KeyError as e:
        logger.warning(f"模板格式错误，使用默认模板: {e}")
        # 如果模板中有未知字段，使用默认模板
        default_path = f"{variables.get('type', 'Unknown')}/ \
        {variables.get('creator', 'Unknown')}/{variables.get('name', 'Unknown')}"
        return os.path.normpath(default_path)


def apply_image_template(
    template: str, model_id: int, image_info: Dict[str, Any]
) -> str:
    """
    应用路径模板，生成图像文件的保存路径

    Args:
        template: 路径模板，如 "images/{model_id}/{hash}"
        model_id: 模型ID
        image_info: 图像信息字典

    Returns:
        根据模板生成的相对路径
    """
    # 提取可用于模板的字段
    fields = {
        "model_id": model_id,
        "image_id": image_info.get("id", 0),
        "hash": image_info.get("hash", "unknown"),
        "width": image_info.get("width", 0),
        "height": image_info.get("height", 0),
        "nsfw": "nsfw" if image_info.get("nsfw", False) else "sfw",
    }

    # 从元数据中提取生成参数
    meta = image_info.get("meta", {})
    if isinstance(meta, dict):
        fields.update(
            {"prompt_hash": hash(meta.get("prompt", "")) if meta.get("prompt") else 0}
        )

    # 安全处理所有字符串值
    for k, v in fields.items():
        if isinstance(v, str):
            fields[k] = sanitize_path(v)

    # 应用模板
    try:
        path = template.format(**fields)
        # 规范化路径分隔符
        return os.path.normpath(path)
    except KeyError as e:
        logger.warning(f"图像模板格式错误，使用默认模板: {e}")
        # 如果模板中有未知字段，使用默认模板
        default_path = f"images/model_{model_id}/{fields['image_id']}"
        return os.path.normpath(default_path)

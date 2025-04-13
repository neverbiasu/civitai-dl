"""图像和模型元数据提取与处理工具"""

import os
import json
import re
from typing import Optional, Dict, Any
from PIL import Image
import piexif

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


def extract_image_metadata(image_path: str) -> Optional[Dict[str, Any]]:
    """
    从图像文件中提取元数据，包括生成参数

    Args:
        image_path: 图像文件路径

    Returns:
        包含元数据的字典，如果提取失败则返回None
    """
    try:
        if not os.path.exists(image_path):
            logger.error(f"文件不存在: {image_path}")
            return None

        # 打开图像文件
        with Image.open(image_path) as img:
            # 尝试从EXIF数据中提取
            exif_data = extract_from_exif(img)
            if exif_data:
                return exif_data

            # 尝试从PNG文本块中提取
            png_data = extract_from_png(img)
            if png_data:
                return png_data

        # 如果前面的方法都失败了，尝试从文件名提取信息
        filename_data = extract_from_filename(os.path.basename(image_path))
        if filename_data:
            return filename_data

        logger.warning(f"未能从图像中提取元数据: {image_path}")
        return None

    except Exception as e:
        logger.error(f"提取图像元数据时出错: {str(e)}")
        return None


def extract_from_exif(img) -> Optional[Dict[str, Any]]:
    """从图像EXIF数据中提取元数据"""
    try:
        if "exif" in img.info:
            exif_dict = piexif.load(img.info["exif"])

            # 查找用户注释字段，通常包含生成参数
            if piexif.ExifIFD.UserComment in exif_dict.get("Exif", {}):
                user_comment = exif_dict["Exif"][piexif.ExifIFD.UserComment]
                if isinstance(user_comment, bytes):
                    # 解码字节数据
                    try:
                        comment_text = user_comment.decode('utf-8').strip()
                        # 去除可能的ASCII标记前缀
                        if comment_text.startswith("ASCII\0\0\0"):
                            comment_text = comment_text[8:]
                        return parse_generation_parameters(comment_text)
                    except BaseException:
                        pass

        return None
    except Exception as e:
        logger.debug(f"从EXIF提取元数据失败: {str(e)}")
        return None


def extract_from_png(img) -> Optional[Dict[str, Any]]:
    """从PNG图像文本块中提取元数据"""
    try:
        # PNG图像可能在文本块中存储元数据
        if hasattr(img, 'text') and img.text:
            # 查找常见的生成参数键
            for key in ['parameters', 'prompt', 'generation_parameters']:
                if key in img.text:
                    return parse_generation_parameters(img.text[key])

        return None
    except Exception as e:
        logger.debug(f"从PNG文本块提取元数据失败: {str(e)}")
        return None


def extract_from_filename(filename: str) -> Optional[Dict[str, Any]]:
    """尝试从文件名中提取元数据信息"""
    # 这个功能可以根据需要扩展
    # 目前只是一个占位实现
    return None


def parse_generation_parameters(text: str) -> Dict[str, Any]:
    """解析生成参数文本并返回结构化数据"""
    result = {}

    # 尝试提取提示词
    prompt_match = re.search(r"^(.*?)(?:Negative prompt:|Steps:)", text, re.DOTALL)
    if prompt_match:
        result["prompt"] = prompt_match.group(1).strip()

    # 尝试提取负面提示词
    negative_match = re.search(r"Negative prompt:(.*?)(?:Steps:|$)", text, re.DOTALL)
    if negative_match:
        result["negative_prompt"] = negative_match.group(1).strip()

    # 提取各种参数
    steps_match = re.search(r"Steps:\s*(\d+)", text)
    if steps_match:
        result["steps"] = int(steps_match.group(1))

    sampler_match = re.search(r"Sampler:\s*([^,]+)", text)
    if sampler_match:
        result["sampler"] = sampler_match.group(1).strip()

    cfg_match = re.search(r"CFG scale:\s*([\d.]+)", text)
    if cfg_match:
        result["cfg_scale"] = float(cfg_match.group(1))

    seed_match = re.search(r"Seed:\s*(\d+)", text)
    if seed_match:
        result["seed"] = int(seed_match.group(1))

    model_match = re.search(r"Model:\s*([^,]+)", text)
    if model_match:
        result["model"] = model_match.group(1).strip()

    # 添加原始参数文本
    result["raw_parameters"] = text

    return result


def save_metadata_to_json(metadata: Dict[str, Any], output_path: str) -> bool:
    """
    将元数据保存为JSON文件

    Args:
        metadata: 元数据字典
        output_path: 输出文件路径

    Returns:
        保存是否成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"元数据已保存至: {output_path}")
        return True
    except Exception as e:
        logger.error(f"保存元数据失败: {str(e)}")
        return False

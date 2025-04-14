"""图像和模型元数据提取与处理工具"""

import json
import os
import re
from typing import Any, Dict, Optional

import piexif
from PIL import Image, UnidentifiedImageError

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
    metadata = {}

    try:
        if not os.path.exists(image_path):
            logger.error(f"文件不存在: {image_path}")
            return None

        # 尝试打开图像文件
        with Image.open(image_path) as img:
            # 基本图像信息
            metadata["format"] = img.format
            metadata["mode"] = img.mode
            metadata["width"] = img.width
            metadata["height"] = img.height

            # 尝试读取EXIF数据
            exif_data = {}
            if hasattr(img, "_getexif") and callable(img._getexif):
                exif = img._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag_name = EXIF_TAGS.get(tag_id, tag_id)
                        exif_data[tag_name] = value

            if exif_data:
                metadata["exif"] = exif_data

            # 检查是否有PNG文本信息
            if img.format == "PNG" and hasattr(img, "text") and img.text:
                metadata["png_text"] = img.text

            # 尝试从PNG文本或EXIF中提取生成参数
            parameters = extract_generation_parameters(img)
            if parameters:
                metadata["generation_parameters"] = parameters

        # 如果前面的方法都失败了，尝试从文件名提取信息
        filename_data = extract_from_filename(os.path.basename(image_path))
        if filename_data:
            return filename_data

        logger.warning(f"未能从图像中提取元数据: {image_path}")
        return metadata

    except UnidentifiedImageError:
        metadata["error"] = "无法识别的图像格式"
    except Exception as e:
        metadata["error"] = str(e)

    return metadata


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
                        comment_text = user_comment.decode("utf-8").strip()
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
        if hasattr(img, "text") and img.text:
            # 查找常见的生成参数键
            for key in ["parameters", "prompt", "generation_parameters"]:
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


def extract_generation_parameters(img) -> Optional[Dict[str, Any]]:
    """
    从图像中提取生成参数

    Args:
        img: PIL Image对象

    Returns:
        生成参数字典或None
    """
    parameters = {}

    # 尝试从PNG文本中提取
    if hasattr(img, "text") and img.text:
        # 检查常见的参数键
        for key in ["parameters", "prompt", "negative_prompt", "seed", "steps"]:
            if key in img.text:
                parameters[key] = img.text[key]

        # 特殊处理Automatic1111参数格式
        if "parameters" in img.text:
            params_text = img.text["parameters"]
            # 尝试解析常见的参数格式
            try:
                # 提取提示词
                prompt_match = re.search(
                    r"^(.*?)(?:Negative prompt:|Steps:)", params_text, re.DOTALL
                )
                if prompt_match:
                    parameters["prompt"] = prompt_match.group(1).strip()

                # 提取负向提示词
                neg_match = re.search(
                    r"Negative prompt:(.*?)(?:Steps:|$)", params_text, re.DOTALL
                )
                if neg_match:
                    parameters["negative_prompt"] = neg_match.group(1).strip()

                # 提取其他参数
                steps_match = re.search(r"Steps: (\d+)", params_text)
                if steps_match:
                    parameters["steps"] = int(steps_match.group(1))

                sampler_match = re.search(r"Sampler: ([^,]+)", params_text)
                if sampler_match:
                    parameters["sampler"] = sampler_match.group(1).strip()

                cfg_match = re.search(r"CFG scale: ([0-9.]+)", params_text)
                if cfg_match:
                    parameters["cfg_scale"] = float(cfg_match.group(1))

                seed_match = re.search(r"Seed: (\d+)", params_text)
                if seed_match:
                    parameters["seed"] = int(seed_match.group(1))

                model_match = re.search(r"Model: ([^,]+)", params_text)
                if model_match:
                    parameters["model"] = model_match.group(1).strip()

            except Exception:
                # 如果解析失败，保留原始文本
                if not parameters.get("prompt"):
                    parameters["raw_parameters"] = params_text

    return parameters if parameters else None


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

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"元数据已保存至: {output_path}")
        return True
    except Exception as e:
        logger.error(f"保存元数据失败: {str(e)}")
        return False


# EXIF标签映射
EXIF_TAGS = {
    0x010E: "ImageDescription",
    0x010F: "Make",
    0x0110: "Model",
    0x0112: "Orientation",
    0x8769: "ExifOffset",
    0x9000: "ExifVersion",
    0x9003: "DateTimeOriginal",
    0x9004: "DateTimeDigitized",
    0x9291: "SubSecTimeOriginal",
    0x9292: "SubSecTimeDigitized",
    # 更多EXIF标签...
}

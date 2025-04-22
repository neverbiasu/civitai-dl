"""元数据处理工具

用于提取、保存和管理模型和图像的元数据信息
"""

import os
import re
import json
import time
from typing import Dict, Any, Optional

from civitai_dl.utils.logger import get_logger

# Try importing optional dependencies
try:
    from PIL import Image, ExifTags
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import piexif
    HAS_PIEXIF = True
except ImportError:
    HAS_PIEXIF = False

# Configure logger
logger = get_logger(__name__)


def extract_image_metadata(image_path: str) -> Dict[str, Any]:
    """Extract metadata from an image file.

    Attempts to extract various metadata including generation parameters,
    EXIF data, and embedded metadata from image files.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary of extracted metadata
    """
    metadata: Dict[str, Any] = {
        "extraction_time": time.time(),
        "path": image_path,
        "filename": os.path.basename(image_path)
    }

    if not HAS_PIL:
        logger.warning("PIL not available, skipping image metadata extraction")
        return metadata

    try:
        # Open image file
        with Image.open(image_path) as img:
            # Get basic image info
            metadata["dimensions"] = {"width": img.width, "height": img.height}
            metadata["format"] = img.format
            metadata["mode"] = img.mode

            # Extract EXIF data if available
            if hasattr(img, '_getexif') and callable(img._getexif):
                exif_data = img._getexif()
                if exif_data:
                    exif_dict = {}
                    for tag_id, value in exif_data.items():
                        tag = ExifTags.TAGS.get(tag_id, str(tag_id))
                        if isinstance(value, bytes):
                            # Skip binary data that's not JSON serializable
                            continue
                        exif_dict[tag] = value
                    metadata["exif"] = exif_dict

            # Extract image generation parameters
            parameters = extract_generation_parameters(img)
            if parameters:
                metadata["generation_parameters"] = parameters

            # Extract any PNG text chunks
            if img.format == 'PNG' and hasattr(img, 'text') and img.text:
                metadata["png_text"] = dict(img.text)

    except Exception as e:
        logger.error(f"Failed to extract metadata from {image_path}: {e}")

    # Look for external metadata file
    try:
        ext_metadata = load_external_metadata(image_path)
        if ext_metadata:
            metadata["external_metadata"] = ext_metadata
    except Exception as e:
        logger.warning(f"Failed to load external metadata: {e}")

    return metadata


def extract_generation_parameters(img: Any) -> Dict[str, Any]:
    """Extract generation parameters from an image.

    Attempts to extract AI image generation parameters from various formats
    used by different generation tools.

    Args:
        img: PIL Image object

    Returns:
        Dictionary of parameters or empty dict if none found
    """
    params: Dict[str, Any] = {}

    # Check for PNG text chunks (used by Stable Diffusion WebUI)
    if hasattr(img, 'text') and img.format == 'PNG':
        param_keys = ["parameters", "prompt", "Generation parameters"]
        for key in param_keys:
            if key in img.text:
                params = parse_parameters_string(img.text[key])
                if params:
                    return params

    # Check for parameters in EXIF data
    if HAS_PIEXIF and hasattr(img, 'info') and 'exif' in img.info:
        try:
            exif_dict = piexif.load(img.info['exif'])
            if piexif.ExifIFD.UserComment in exif_dict.get('Exif', {}):
                user_comment = exif_dict['Exif'][piexif.ExifIFD.UserComment]
                if user_comment:
                    if isinstance(user_comment, bytes):
                        try:
                            # Try to decode various formats
                            if user_comment.startswith(b'UNICODE\0'):
                                comment = user_comment[8:].decode('utf-16')
                            else:
                                comment = user_comment.decode('utf-8', errors='ignore')

                            params = parse_parameters_string(comment)
                            if params:
                                return params
                        except Exception as e:
                            logger.debug(f"Failed to decode EXIF user comment: {e}")
        except Exception as e:
            logger.debug(f"Failed to extract EXIF parameters: {e}")

    return params


def parse_parameters_string(param_string: str) -> Dict[str, Any]:
    """Parse generation parameters from string format.

    Handles different formats of parameter strings used by various
    AI image generation tools.

    Args:
        param_string: Parameter string to parse

    Returns:
        Dictionary of parsed parameters
    """
    # Empty check
    if not param_string or not isinstance(param_string, str):
        return {}

    # First try to parse as JSON
    if param_string.strip().startswith('{') and param_string.strip().endswith('}'):
        try:
            return json.loads(param_string)
        except json.JSONDecodeError:
            pass

    # Try to parse Automatic1111 WebUI format
    params: Dict[str, Any] = {}

    # Extract main prompt (everything before the first recognized parameter)
    known_params = ["Steps:", "Sampler:", "CFG scale:", "Seed:", "Size:", "Model:"]
    first_param_pos = len(param_string)

    for param_key in known_params:
        pos = param_string.find(param_key)
        if pos != -1 and pos < first_param_pos:
            first_param_pos = pos

    if first_param_pos < len(param_string):
        prompt = param_string[:first_param_pos].strip()
        if prompt:
            params["prompt"] = prompt

        # Parse key-value pairs
        param_section = param_string[first_param_pos:]
        parts = param_section.split(", ")

        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                params[key.strip()] = value.strip()

    return params


def load_external_metadata(image_path: str) -> Optional[Dict[str, Any]]:
    """Load metadata from an external file associated with the image.

    Checks for metadata stored in companion files with extensions like
    .json, .meta.json, etc.

    Args:
        image_path: Path to the image file

    Returns:
        Metadata dictionary or None if no metadata file found
    """
    base_path = os.path.splitext(image_path)[0]
    metadata_extensions = ['.meta.json', '.json', '.txt']

    for ext in metadata_extensions:
        meta_path = base_path + ext
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    if ext.endswith('.json'):
                        return json.load(f)
                    else:
                        # For text files, try to parse as parameters
                        content = f.read()
                        return {"text_content": content}
            except Exception as e:
                logger.warning(f"Failed to read metadata file {meta_path}: {e}")

    return None


def save_metadata(image_path: str, metadata: Dict[str, Any], format: str = 'json') -> bool:
    """Save metadata to an external file.

    Args:
        image_path: Path to the associated image file
        metadata: Metadata to save
        format: File format ('json' or 'txt')

    Returns:
        True if successful, False otherwise
    """
    base_path = os.path.splitext(image_path)[0]

    if format == 'json':
        output_path = base_path + '.meta.json'
    else:
        output_path = base_path + '.txt'

    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write metadata
        with open(output_path, 'w', encoding='utf-8') as f:
            if format == 'json':
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            else:
                # Write as plain text (simplified format)
                f.write(str(metadata))

        logger.debug(f"Saved metadata to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save metadata: {e}")
        return False


def extract_model_info_from_image(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extract model information from image metadata.

    Attempts to identify which AI models were used to generate an image
    based on its metadata.

    Args:
        metadata: Image metadata dictionary

    Returns:
        Dictionary with model information
    """
    model_info: Dict[str, Any] = {}

    # Check generation parameters
    params = metadata.get('generation_parameters', {})
    if not params and 'external_metadata' in metadata:
        params = metadata['external_metadata'].get('generation_parameters', {})

    if not params:
        return model_info

    # Extract model information from parameters
    if 'Model' in params:
        model_info['base_model'] = params['Model']
    elif 'model' in params:
        model_info['base_model'] = params['model']

    # Look for LoRA models
    lora_pattern = r'<lora:(.*?):(.*?)>'
    prompt = params.get('prompt', '')

    if prompt:
        loras = []
        for match in re.finditer(lora_pattern, prompt):
            lora_name = match.group(1)
            lora_weight = match.group(2)
            loras.append({
                'name': lora_name,
                'weight': float(lora_weight) if lora_weight.replace('.', '', 1).isdigit() else lora_weight
            })

        if loras:
            model_info['loras'] = loras

    return model_info


def save_metadata_to_json(metadata: Dict[str, Any], output_path: str, filename: Optional[str] = None) -> str:
    """将元数据保存为JSON文件
    
    Args:
        metadata: 要保存的元数据字典
        output_path: 保存目录
        filename: 可选的文件名，如果不提供则自动生成
        
    Returns:
        保存的JSON文件路径
        
    Raises:
        IOError: 如果无法创建目录或写入文件
    """
    try:
        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)
        
        # 如果没有提供文件名，使用默认名称
        if not filename:
            # 尝试从元数据中获取有意义的名称
            model_name = metadata.get("name", "")
            if model_name:
                # 规范化文件名，替换不允许的字符
                safe_name = re.sub(r'[\\/*?:"<>|]', "_", model_name)
                filename = f"{safe_name}_metadata.json"
            else:
                filename = "metadata.json"
        
        # 确保文件名有.json扩展名
        if not filename.endswith(".json"):
            filename += ".json"
        
        file_path = os.path.join(output_path, filename)
        
        # 保存为JSON文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"元数据已保存至 {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"保存元数据失败: {str(e)}")
        raise IOError(f"无法保存元数据: {str(e)}")


def extract_model_metadata(model_data: Dict[str, Any]) -> Dict[str, Any]:
    """从模型数据中提取元数据
    
    Args:
        model_data: 模型API响应数据
        
    Returns:
        提取的元数据字典
    """
    # ...existing code...
    metadata = {
        "id": model_data.get("id"),
        "name": model_data.get("name"),
        "type": model_data.get("type"),
        "description": model_data.get("description"),
        "creator": model_data.get("creator", {}).get("username"),
        "creator_id": model_data.get("creator", {}).get("id"),
        "stats": model_data.get("stats", {}),
        "tags": [tag.get("name") for tag in model_data.get("tags", [])],
        "nsfw": model_data.get("nsfw", False),
        "versions": []
    }
    
    # 添加版本信息
    for version in model_data.get("modelVersions", []):
        version_info = {
            "id": version.get("id"),
            "name": version.get("name"),
            "created_at": version.get("createdAt"),
            "updated_at": version.get("updatedAt"),
            "base_model": version.get("baseModel"),
            "trained_words": version.get("trainedWords", []),
            "files": []
        }
        
        # 添加文件信息
        for file in version.get("files", []):
            file_info = {
                "id": file.get("id"),
                "name": file.get("name"),
                "size_kb": file.get("sizeKB"),
                "type": file.get("type"),
                "format": file.get("metadata", {}).get("format"),
                "fp": file.get("metadata", {}).get("fp"),
                "is_primary": file.get("primary", False)
            }
            version_info["files"].append(file_info)
        
        metadata["versions"].append(version_info)
    
    return metadata


def load_metadata_from_json(file_path: str) -> Optional[Dict[str, Any]]:
    """从JSON文件加载元数据
    
    Args:
        file_path: JSON文件路径
        
    Returns:
        加载的元数据字典，如果加载失败则返回None
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"元数据文件不存在: {file_path}")
            return None
            
        with open(file_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        logger.debug(f"已从 {file_path} 加载元数据")
        return metadata
        
    except Exception as e:
        logger.error(f"加载元数据失败: {str(e)}")
        return None

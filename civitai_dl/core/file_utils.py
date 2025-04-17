import os
import re
import logging
import hashlib
from typing import Optional, Tuple
from urllib.parse import unquote

# 配置日志
logger = logging.getLogger(__name__)

# 文件名非法字符（Windows、macOS、Linux通用）
INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1F]'

# 将 config_manager 的导入移到函数内部，避免循环导入


def get_download_location(model_info: dict, version_info: dict,
                          ask_location: bool = None) -> str:
    """确定下载位置

    Args:
        model_info: 模型信息
        version_info: 版本信息
        ask_location: 是否询问下载位置，覆盖配置设置

    Returns:
        下载目录路径
    """
    # 延迟导入 config_manager，避免循环导入
    from .config import config_manager

    # 优先使用参数设置，否则使用配置
    if ask_location is None:
        ask_location = config_manager.get("ask_download_location", False)

    # 如果设置询问位置，执行终端询问流程
    if ask_location:
        # 获取默认位置建议
        model_type = model_info.get("type")
        default_dir = config_manager.get_download_dir(model_type)

        # 显示最近目录
        recent_dirs = config_manager.get_recent_directories()
        if recent_dirs:
            print("最近使用的下载目录:")
            for i, directory in enumerate(recent_dirs):
                print(f"{i+1}. {directory}")

        # 询问用户
        while True:
            response = input(f"请输入下载目录 [默认: {default_dir}]，输入数字选择最近目录，或直接回车使用默认目录: ")

            # 直接回车，使用默认目录
            if not response.strip():
                selected_dir = default_dir
                break

            # 尝试解析为数字，选择最近目录
            if response.isdigit() and recent_dirs:
                index = int(response) - 1
                if 0 <= index < len(recent_dirs):
                    selected_dir = recent_dirs[index]
                    break
                else:
                    print(f"无效的选择，请输入1-{len(recent_dirs)}之间的数字")
                    continue

            # 解析为路径
            if os.path.isabs(response):
                selected_dir = response
                break
            else:
                # 相对路径转为绝对路径
                selected_dir = os.path.abspath(response)
                break

        # 创建目录
        os.makedirs(selected_dir, exist_ok=True)

        # 添加到最近目录
        config_manager.add_recent_directory(selected_dir)

        return selected_dir

    # 不询问，使用系统设置的目录
    model_type = model_info.get("type")
    return config_manager.get_download_dir(model_type)


def sanitize_filename(filename: str) -> str:
    """净化文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 替换非法字符
    sanitized = re.sub(INVALID_CHARS, "_", filename)

    # 修剪文件名长度（Windows路径最大长度为260个字符，预留一些空间给路径）
    max_length = 200
    if len(sanitized) > max_length:
        # 保留扩展名
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:max_length - len(ext)] + ext

    # 处理以点或空格开头/结尾的情况
    sanitized = sanitized.strip(". ")

    # 确保文件名不为空
    if not sanitized:
        sanitized = "unnamed_file"

    return sanitized


def get_filename_from_model(model_info: dict, version_info: dict,
                            original_filename: Optional[str] = None) -> str:
    """从模型信息生成文件名

    Args:
        model_info: 模型信息
        version_info: 版本信息
        original_filename: 原始文件名（如果有）

    Returns:
        生成的文件名
    """
    # 延迟导入 config_manager，避免循环导入
    from .config import config_manager

    # 如果配置设置使用原始文件名且提供了原始文件名，则使用它
    if config_manager.get("use_original_filename", True) and original_filename:
        return sanitize_filename(original_filename)

    # 否则构建信息丰富的文件名
    model_name = model_info.get("name", "unknown_model")
    model_type = model_info.get("type", "unknown_type")
    creator = model_info.get("creator", {}).get("username", "unknown_creator")
    version_name = version_info.get("name", "")

    # 构建文件名
    if version_name:
        filename = f"{model_name}-{model_type}-{creator}-{version_name}"
    else:
        filename = f"{model_name}-{model_type}-{creator}"

    # 净化文件名
    return sanitize_filename(filename)


def extract_filename_from_headers(headers: dict) -> Optional[str]:
    """从HTTP响应头中提取文件名

    Args:
        headers: HTTP响应头

    Returns:
        文件名，如果无法提取则返回None
    """
    # 尝试从Content-Disposition提取
    if 'Content-Disposition' in headers:
        content_disposition = headers['Content-Disposition']
        filename_match = re.search(r'filename=["\']?([^"\';\n]+)', content_disposition)

        if filename_match:
            filename = filename_match.group(1)
            # 解码URL编码
            filename = unquote(filename)
            # 处理引号
            if filename.startswith('"') and filename.endswith('"'):
                filename = filename[1:-1]
            return filename

    # 尝试从Content-Type推测扩展名
    return None


def resolve_file_conflict(filepath: str, action: Optional[str] = None) -> Tuple[str, bool]:
    """解决文件冲突

    Args:
        filepath: 文件路径
        action: 冲突处理方式 (overwrite/rename/skip)，None表示使用配置

    Returns:
        新的文件路径和是否跳过下载的标志
    """
    if not os.path.exists(filepath):
        return filepath, False

    # 如果未指定行动，使用配置默认值
    if action is None:
        # 延迟导入 config_manager，避免循环导入
        from .config import config_manager
        action = config_manager.get("file_exists_action", "ask")

    # 询问用户
    if action == "ask":
        print(f"文件已存在: {filepath}")
        while True:
            choice = input("请选择处理方式: [o]覆盖 [r]重命名 [s]跳过: ").lower()
            if choice in ('o', 'overwrite'):
                action = "overwrite"
                break
            elif choice in ('r', 'rename'):
                action = "rename"
                break
            elif choice in ('s', 'skip'):
                action = "skip"
                break
            else:
                print("无效选择，请重试")

    # 处理冲突
    if action == "overwrite":
        return filepath, False
    elif action == "skip":
        return filepath, True
    elif action == "rename":
        # 自动生成新文件名
        directory, filename = os.path.split(filepath)
        name, ext = os.path.splitext(filename)

        index = 1
        while True:
            new_filename = f"{name}_{index}{ext}"
            new_filepath = os.path.join(directory, new_filename)

            if not os.path.exists(new_filepath):
                return new_filepath, False

            index += 1
    else:
        # 默认重命名
        return resolve_file_conflict(filepath, "rename")


def detect_duplicate_file(file_path: str, known_hashes: Optional[dict] = None) -> Optional[str]:
    """检测是否有重复文件（基于哈希）

    Args:
        file_path: 要检查的文件路径
        known_hashes: 已知文件的哈希值字典 {hash: file_path}

    Returns:
        如果是重复文件，返回原始文件的路径；否则返回None
    """
    if not known_hashes or not os.path.exists(file_path):
        return None

    try:
        # 计算文件哈希
        file_hash = calculate_file_hash(file_path)

        # 检查是否在已知哈希中
        if file_hash in known_hashes:
            return known_hashes[file_hash]
    except Exception as e:
        logger.warning(f"计算文件哈希失败: {str(e)}")

    return None


def calculate_file_hash(file_path: str) -> str:
    """计算文件的SHA-256哈希值

    Args:
        file_path: 文件路径

    Returns:
        文件的SHA-256哈希值
    """
    h = hashlib.sha256()

    with open(file_path, 'rb') as f:
        # 读取文件块并更新哈希
        chunk = f.read(8192)
        while chunk:
            h.update(chunk)
            chunk = f.read(8192)

    return h.hexdigest()


def verify_path_exists(path: str) -> bool:
    """验证路径是否有效并可以创建

    Args:
        path: 要验证的路径

    Returns:
        路径是否有效
    """
    try:
        # 如果路径已存在且是目录，则有效
        if os.path.exists(path) and os.path.isdir(path):
            return True

        # 如果不存在，尝试创建
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            return True

        # 如果存在但不是目录，则无效
        return False
    except Exception as e:
        logger.error(f"验证路径失败: {str(e)}")
        return False

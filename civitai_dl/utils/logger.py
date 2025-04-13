"""日志工具模块"""

import os
import logging
import logging.handlers
import sys
from typing import Optional

# 全局日志格式
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# 日志级别映射
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

# 默认日志级别
DEFAULT_LOG_LEVEL = logging.INFO

# 是否已初始化
_initialized = False


def setup_logging(level: int = DEFAULT_LOG_LEVEL,
                  log_file: Optional[str] = None,
                  max_bytes: int = 10485760,  # 10MB
                  backup_count: int = 3) -> None:
    """
    初始化日志系统

    Args:
        level: 日志级别
        log_file: 日志文件路径
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件数量
    """
    global _initialized

    if _initialized:
        # 更新全局日志级别
        logging.getLogger().setLevel(level)
        return

    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 创建输出到控制台的处理器
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(console)

    # 如果提供了日志文件路径，创建文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # 创建轮换日志文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(file_handler)

    # 设置第三方库的日志级别
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    获取带有指定名称的日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        配置好的日志记录器实例
    """
    # 如果日志系统尚未初始化，进行初始化
    if not _initialized:
        setup_logging()

    return logging.getLogger(name)


def set_log_level(level: str) -> None:
    """
    设置全局日志级别

    Args:
        level: 日志级别名称 ('debug', 'info', 'warning', 'error', 'critical')
    """
    level_value = LOG_LEVELS.get(level.lower(), DEFAULT_LOG_LEVEL)
    setup_logging(level_value)

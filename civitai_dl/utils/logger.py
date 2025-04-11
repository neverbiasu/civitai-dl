import os
import logging
from typing import Dict, Optional

# 全局日志配置
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_LOG_DIR = "./logs"

# 日志级别映射
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

_loggers: Dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)

    # 避免重复添加处理器
    if not logger.handlers:
        setup_logger(logger)

    _loggers[name] = logger
    return logger


def setup_logger(
    logger: logging.Logger, level: Optional[str] = None, log_file: Optional[str] = None
):
    """设置日志器的级别和处理器"""
    # 设置日志级别
    if level:
        logger.setLevel(LOG_LEVELS.get(level.lower(), DEFAULT_LOG_LEVEL))
    else:
        logger.setLevel(DEFAULT_LOG_LEVEL)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
    logger.addHandler(console_handler)

    # 如果指定了日志文件，添加文件处理器
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        logger.addHandler(file_handler)


def setup_root_logger(level: str = "info", log_file: Optional[str] = None):
    """设置根日志器"""
    logger = logging.getLogger()
    setup_logger(logger, level, log_file)
    return logger

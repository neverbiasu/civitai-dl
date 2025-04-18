# Civitai Downloader Coding Standards Cheatsheet

快速查阅编码规范的核心要点。

## 命名约定

| 类型      | 规范          | 示例                            |
| --------- | ------------- | ------------------------------- |
| 变量名    | 小写+下划线   | `filter_manager`, `api_params`  |
| 类名      | 大驼峰式      | `FilterManager`, `APIClient`    |
| 常量      | 全大写+下划线 | `MAX_RETRIES`, `INVALID_CHARS`  |
| 函数/方法 | 小写+下划线   | `parse_query()`, `get_models()` |
| 私有方法  | 单下划线开头  | `_validate_condition()`         |

## 文档字符串

```python
def function_name(param1: type1, param2: type2) -> return_type:
    """Short description of the function.

    Detailed description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception occurs
    """
    # Function implementation
```

## 导入顺序

1. 标准库 (`import os`, `import sys`)
2. 第三方库 (`import click`, `import requests`)
3. 本地导入 (`from ...api import client`)

## 错误处理

```python
try:
    # Code that might raise an exception
    result = api.get_models(params)
except SpecificError as e:
    logger.error(f"Specific error occurred: {e}")
    # Handle specific error
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    # General error handling
```

## 类型注解

```python
from typing import Dict, List, Optional, Union, Any

def process_data(
    items: List[Dict[str, Any]], 
    filter_by: Optional[str] = None
) -> Dict[str, Any]:
    # Function implementation
```

## 日志记录

```python
import logging
logger = logging.getLogger(__name__)

# Appropriate log levels
logger.debug("Detailed information for debugging")
logger.info("Confirmation of expected operations")
logger.warning("Something unexpected but not critical")
logger.error("Error that prevents normal function")
logger.critical("Very serious error, application may stop")
```

## 风格指南

- 行长度: 最大88字符（优先可读性）
- 缩进: 4个空格（不使用Tab）
- 空行: 使用空行分隔函数和逻辑块
- 注释: 使用英文，保持简洁明了

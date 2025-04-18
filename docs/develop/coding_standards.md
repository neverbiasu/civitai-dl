# Civitai Downloader 编码规范

本文档定义了 Civitai Downloader 项目的编码规范和最佳实践。遵循这些规范可以确保代码的一致性、可读性和可维护性。

## 1. 命名规范

### 1.1 变量命名
- 使用小写字母和下划线分隔：`filter_manager`, `api_params`
- 局部变量使用小写：`model`, `condition`
- 布尔类型的变量应当使用明确的状态描述：`is_valid`, `has_items`

### 1.2 类命名
- 使用大驼峰式命名法（首字母大写）：`FilterManager`, `APIClient`
- 缩写词应全部大写或首字母大写：`APIError`, `JSONEncoder`

### 1.3 常量命名
- 使用全大写字母和下划线分隔：`OPERATORS`, `DEFAULT_TEMPLATES`
- 类级别常量也应使用全大写：`FilterBuilder.OPERATORS`

### 1.4 函数/方法命名
- 使用小写字母和下划线分隔：`get_models()`, `apply_filter()`
- 私有方法以单下划线开头：`_validate_condition()`
- 动词开头，清晰表达动作：`parse_query()`, `display_results()`

### 1.5 模块命名
- 使用小写字母，简短且有意义：`filter.py`, `client.py`
- 避免使用连字符，使用下划线：`filter_parser.py`

## 2. 代码组织

### 2.1 导入顺序
按照以下顺序组织导入语句，每组之间用空行分隔：
1. 标准库导入（如 `import os`, `import sys`）
2. 相关第三方库导入（如 `import click`, `import gradio`）
3. 本地应用/库特定导入（相对导入，如 `from ...core.filter import FilterManager`）

### 2.2 类和函数组织
- 相关函数应放在一起
- 类的方法顺序：
  1. 特殊方法（`__init__`, `__str__`等）
  2. 公共方法
  3. 私有/辅助方法（`_private_method`）

### 2.3 注释和文档字符串
- 每个模块、类、方法和函数都应有文档字符串
- 使用简洁的英文注释，保持风格一致
- 使用Google风格的文档字符串，包含参数说明和返回值描述

```python
def function_name(param1: type1, param2: type2) -> return_type:
    """Short description of the function.

    Detailed description of the function,
    which can span multiple lines.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: Description of when this error is raised
    """
```

## 3. 类型注解

- 所有函数参数和返回值都应添加类型注解
- 使用 `typing` 模块中的类型：`List`, `Dict`, `Optional`, `Union`等
- 复杂的类型可以使用 `TypedDict` 或自定义类型

```python
from typing import Dict, List, Optional, Union

def process_data(data: List[Dict[str, Any]], filter_by: Optional[str] = None) -> Dict[str, Any]:
    # Function implementation
```

## 4. 错误处理

- 使用明确的异常类型，避免捕获所有异常
- 异常信息应清晰明了，包含上下文信息
- 对于网络请求、文件操作等，确保正确处理资源释放

```python
try:
    # Code that might raise an exception
    result = api.get_models(params)
except APIError as e:
    logger.error(f"API call failed: {str(e)}")
    raise
except ValueError as e:
    logger.warning(f"Parameter error: {str(e)}")
    # Handle the error
finally:
    # Clean up resources
```

## 5. 日志记录

- 使用 `logging` 模块，避免使用 `print`
- 根据重要性选择合适的日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
- 日志信息应包含足够的上下文，便于调试

```python
import logging
logger = logging.getLogger(__name__)

# Informational log
logger.info("Starting data processing")

# Warning log
logger.warning("Config file missing field %s, using default value", field_name)

# Error log
logger.error("Failed to process file %s: %s", filename, str(error))
```

## 6. 测试规范

- 使用 `pytest` 进行单元测试和集成测试
- 测试文件命名为 `test_<module_name>.py`
- 测试函数命名为 `test_<function_name>`
- 每个测试应当关注一个具体功能点

## 7. CLI设计规范

- 使用 `click` 库构建命令行界面
- 为每个命令和选项提供详细的帮助信息
- 支持短选项和长选项
- 提供合适的默认值
- 使用子命令组织复杂功能

## 8. API设计原则

- 遵循RESTful API设计原则
- 提供清晰的错误信息和状态码
- 实现适当的重试机制
- 支持身份验证和授权
- 考虑速率限制和缓存策略

## 9. 性能考虑

- 避免不必要的网络请求和数据处理
- 使用生成器处理大数据集
- 考虑并发和异步处理
- 对频繁访问的数据进行适当缓存

## 10. 版本控制与发布

- 使用语义化版本（Semantic Versioning）
- 发布前进行充分测试
- 提供详细的更新日志
- 在重大变更前提供迁移指南

遵循这些规范将有助于保持代码库的一致性和可维护性。

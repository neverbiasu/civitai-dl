# 工具类模块

## 模块概述

工具类模块提供各种辅助功能，为应用的其他部分提供通用功能支持，包括文件操作、哈希计算、路径管理、字符串处理等实用工具。该模块不包含业务逻辑，专注于提供可重用的基础功能组件。

### 主要职责

- 提供文件系统操作工具
- 实现哈希计算和校验
- 处理路径生成和模板解析
- 格式化和验证用户输入
- 提供日志记录和异常处理工具
- 实现简单的缓存机制

### 技术特性

- 纯功能性组件
- 无状态设计
- 高复用性接口
- 跨平台兼容性
- 性能优化实现
- 严格的错误处理

## 接口定义

### 文件操作工具

```python
class FileUtils:
    """文件操作相关工具类"""
    
    @staticmethod
    def ensure_dir(directory: str) -> bool:
        """
        确保目录存在，不存在则创建
        
        Args:
            directory: 目录路径
            
        Returns:
            是否成功创建或已存在
            
        Raises:
            PermissionError: 权限不足
        """
        pass
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        获取文件大小(字节)
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小
            
        Raises:
            FileNotFoundError: 文件不存在
        """
        pass
    
    @staticmethod
    def get_valid_filename(name: str) -> str:
        """
        将字符串转换为有效的文件名
        
        Args:
            name: 原始字符串
            
        Returns:
            有效的文件名
        """
        pass
    
    @staticmethod
    def get_free_space(directory: str) -> int:
        """
        获取指定目录的剩余空间(字节)
        
        Args:
            directory: 目录路径
            
        Returns:
            剩余空间字节数
            
        Raises:
            FileNotFoundError: 目录不存在
        """
        pass
    
    @staticmethod
    def check_file_exists(file_path: str, check_size: bool = False) -> Tuple[bool, int]:
        """
        检查文件是否存在，并可选地返回大小
        
        Args:
            file_path: 文件路径
            check_size: 是否返回文件大小
            
        Returns:
            (存在状态, 文件大小)元组，若文件不存在则大小为0
        """
        pass
```

### 哈希工具

```python
class HashUtils:
    """哈希计算和验证工具类"""
    
    @staticmethod
    def calculate_hash(file_path: str, algorithm: str = "sha256", 
                     chunk_size: int = 8192) -> str:
        """
        计算文件哈希值
        
        Args:
            file_path: 文件路径
            algorithm: 哈希算法 ("md5", "sha1", "sha256", "blake3", "crc32")
            chunk_size: 读取块大小
            
        Returns:
            哈希字符串
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的算法
        """
        pass
    
    @staticmethod
    def verify_hash(file_path: str, expected_hash: str, 
                  algorithm: str = "sha256") -> bool:
        """
        验证文件哈希值
        
        Args:
            file_path: 文件路径
            expected_hash: 期望的哈希值
            algorithm: 哈希算法
            
        Returns:
            是否匹配
        """
        pass
    
    @staticmethod
    def calculate_hash_from_content(content: bytes, 
                                  algorithm: str = "sha256") -> str:
        """
        计算内容哈希值
        
        Args:
            content: 字节内容
            algorithm: 哈希算法
            
        Returns:
            哈希字符串
        """
        pass
```

### 路径工具

```python
class PathUtils:
    """路径处理工具类"""
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """
        规范化路径(处理分隔符、相对路径等)
        
        Args:
            path: 输入路径
            
        Returns:
            规范化后的路径
        """
        pass
    
    @staticmethod
    def resolve_template_path(template: str, variables: Dict[str, str]) -> str:
        """
        解析路径模板变量
        
        Args:
            template: 路径模板，如"{type}/{creator}/{name}"
            variables: 变量字典，如{"type": "LORA", "creator": "user", "name": "model"}
            
        Returns:
            解析后的路径
        """
        pass
    
    @staticmethod
    def get_available_filename(directory: str, filename: str, 
                             auto_increment: bool = True) -> str:
        """
        获取可用的文件名(避免冲突)
        
        Args:
            directory: 目录路径
            filename: 原始文件名
            auto_increment: 是否自动增加序号
            
        Returns:
            可用的文件名
        """
        pass
    
    @staticmethod
    def extract_filename_from_url(url: str) -> str:
        """
        从URL中提取文件名
        
        Args:
            url: URL字符串
            
        Returns:
            文件名
        """
        pass
    
    @staticmethod
    def extract_filename_from_header(content_disposition: str) -> Optional[str]:
        """
        从Content-Disposition头中提取文件名
        
        Args:
            content_disposition: Content-Disposition头值
            
        Returns:
            文件名或None
        """
        pass
```

### 字符串工具

```python
class StringUtils:
    """字符串处理工具类"""
    
    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """
        截断文本到指定长度
        
        Args:
            text: 原始文本
            max_length: 最大长度
            suffix: 截断后的后缀
            
        Returns:
            截断后的文本
        """
        pass
    
    @staticmethod
    def strip_html(html: str) -> str:
        """
        去除HTML标签
        
        Args:
            html: HTML文本
            
        Returns:
            纯文本
        """
        pass
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        格式化文件大小为友好字符串
        
        Args:
            size_bytes: 文件大小(字节)
            
        Returns:
            格式化后的大小字符串，如"1.2 MB"
        """
        pass
    
    @staticmethod
    def format_timestamp(timestamp: Union[int, float, datetime]) -> str:
        """
        格式化时间戳为友好字符串
        
        Args:
            timestamp: 时间戳或datetime对象
            
        Returns:
            格式化后的时间字符串
        """
        pass
```

### 缓存工具

```python
class CacheUtils:
    """简单的内存缓存工具"""
    
    @staticmethod
    def timed_lru_cache(seconds: int = 600, maxsize: int = 128):
        """
        带超时的LRU缓存装饰器
        
        Args:
            seconds: 缓存有效期(秒)
            maxsize: 最大缓存项数
            
        Returns:
            装饰器函数
        """
        pass
    
    @staticmethod
    def file_cache(directory: str, expires: int = 86400):
        """
        文件缓存装饰器
        
        Args:
            directory: 缓存目录
            expires: 过期时间(秒)
            
        Returns:
            装饰器函数
        """
        pass
    
    @staticmethod
    def clear_cache(directory: str) -> int:
        """
        清理缓存文件
        
        Args:
            directory: 缓存目录
            
        Returns:
            清理的文件数量
        """
        pass
```

### 异常处理工具

```python
class ExceptionUtils:
    """异常处理工具类"""
    
    @staticmethod
    def safe_execute(func: Callable, default_value: Any = None, 
                   log_errors: bool = True, *args, **kwargs) -> Any:
        """
        安全执行函数，捕获异常并返回默认值
        
        Args:
            func: 要执行的函数
            default_value: 发生异常时返回的默认值
            log_errors: 是否记录异常
            *args, **kwargs: 传递给func的参数
            
        Returns:
            函数执行结果或默认值
        """
        pass
    
    @staticmethod
    def retry(times: int = 3, exceptions: Tuple[Exception, ...] = (Exception,), 
            delay: int = 1, backoff: int = 2, logger: Optional[logging.Logger] = None):
        """
        重试装饰器
        
        Args:
            times: 最大重试次数
            exceptions: 触发重试的异常类型
            delay: 初始延迟时间(秒)
            backoff: 延迟倍数(用于指数退避)
            logger: 记录器实例
            
        Returns:
            装饰器函数
        """
        pass
```

## 实现思路

### 文件操作实现

1. **路径管理**:
   - 使用`os.path`和`pathlib`处理路径
   - 确保跨平台一致性
   - 处理相对路径和绝对路径转换

2. **目录创建与验证**:
   - 递归创建目录结构
   - 验证路径权限和有效性
   - 处理路径冲突和特殊字符

3. **文件系统状态**:
   - 获取磁盘空间信息
   - 验证文件是否存在和大小
   - 原子文件操作确保一致性

### 哈希计算实现

1. **分块处理**:
   - 大文件分块读取避免内存问题
   - 支持多种哈希算法
   - 使用二进制模式处理文件

2. **哈希验证**:
   - 大小写不敏感的哈希比较
   - 支持前缀匹配(部分哈希)
   - 处理不同格式的哈希字符串

3. **性能优化**:
   - 使用最高性能的可用哈希实现
   - 自动选择合适的块大小
   - 对小文件使用优化策略

### 路径模板解析

1. **模板变量替换**:
   - 使用`string.Template`或格式化字符串
   - 处理缺少变量的情况，提供默认值
   - 验证结果路径的有效性

2. **路径规范化**:
   - 统一分隔符
   - 解析相对路径
   - 处理"."和".."路径

3. **文件名冲突处理**:
   - 检测现有文件
   - 添加数字后缀
   - 保留原始文件扩展名

### 缓存机制设计

1. **内存缓存**:
   - 基于`functools.lru_cache`实现
   - 添加时间过期机制
   - 提供缓存统计和控制

2. **文件缓存**:
   - 使用JSON或pickle序列化
   - 按键值哈希组织缓存文件
   - 实现后台清理和维护

## 依赖关系

- **外部依赖**:
  - `blake3` (可选): 用于高性能BLAKE3哈希算法
  - `zlib`: 用于CRC32计算

- **内部依赖**:
  - 无其他模块依赖，仅使用标准库

## 注意事项与限制

1. **跨平台兼容性**:
   - 路径处理需考虑Windows和POSIX差异
   - 文件名有效性规则因平台而异

2. **大文件处理**:
   - 哈希计算和文件操作对大文件需特别处理
   - 避免一次性加载大文件到内存

3. **字符编码**:
   - 文件名和内容处理需考虑编码问题
   - 默认使用UTF-8，但应处理其他编码

4. **并发安全**:
   - 工具函数应当是线程安全的
   - 文件操作需考虑并发访问问题

5. **性能考虑**:
   - 优化频繁调用的工具函数
   - 缓存重复计算的结果
   - 对资源密集型操作使用异步方法

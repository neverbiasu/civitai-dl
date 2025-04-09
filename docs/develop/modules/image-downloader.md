# 图像下载模块

## 模块概述

图像下载模块专注于获取和管理来自Civitai的图像资源，提供对模型示例图像的检索、批量下载和元数据提取能力。该模块处理图像API的游标分页特性，同时为不同使用场景提供灵活的图像获取方式。

### 主要职责

- 获取模型相关示例图像
- 批量下载图像资源
- 提取图像生成参数
- 保存图像元数据
- 处理图像API的游标分页
- 支持NSFW过滤和分级

### 技术特性

- 游标分页处理
- 并行图像下载
- 生成参数提取
- 图像分类与组织
- 重复图像检测
- 缩略图生成

## 接口定义

### 核心类

```python
class ImageDownloader:
    """
    Civitai图像下载管理器
    """
    
    def __init__(self, api_client: CivitaiAPI = None, download_engine: DownloadEngine = None,
                output_path: str = "./images", 
                path_template: str = "{model_id}/{id}"):
        """
        初始化图像下载管理器
        
        Args:
            api_client: Civitai API客户端实例，如果为None则创建新实例
            download_engine: 下载引擎实例，如果为None则创建新实例
            output_path: 图像文件保存的基础路径
            path_template: 图像保存路径模板，支持的变量包括:
                {model_id} - 关联的模型ID
                {model_name} - 关联的模型名称
                {id} - 图像ID
                {creator} - 上传者用户名
        """
        pass
    
    def download_model_images(self, model_id: int, limit: int = 0,
                            nsfw_levels: Optional[List[str]] = None,
                            save_metadata: bool = True) -> List[str]:
        """
        下载指定模型的所有示例图像
        
        Args:
            model_id: 模型ID
            limit: 最多下载图像数量，0表示无限制
            nsfw_levels: NSFW级别过滤，如 ["None", "Soft"]，None表示所有级别
            save_metadata: 是否保存图像元数据
            
        Returns:
            下载任务ID列表
            
        Raises:
            ApiError: API调用失败
        """
        pass
    
    def download_version_images(self, version_id: int, limit: int = 0,
                              nsfw_levels: Optional[List[str]] = None,
                              save_metadata: bool = True) -> List[str]:
        """
        下载指定模型版本的示例图像
        
        Args:
            version_id: 模型版本ID
            limit: 最多下载图像数量，0表示无限制
            nsfw_levels: NSFW级别过滤，如 ["None", "Soft"]，None表示所有级别
            save_metadata: 是否保存图像元数据
            
        Returns:
            下载任务ID列表
        """
        pass
    
    def download_creator_images(self, username: str, limit: int = 20,
                              nsfw_levels: Optional[List[str]] = None,
                              save_metadata: bool = True) -> List[str]:
        """
        下载指定创作者的图像
        
        Args:
            username: 创作者用户名
            limit: 最多下载图像数量
            nsfw_levels: NSFW级别过滤
            save_metadata: 是否保存图像元数据
            
        Returns:
            下载任务ID列表
        """
        pass
    
    def download_filtered_images(self, filter_params: Dict[str, Any],
                               limit: int = 20,
                               save_metadata: bool = True) -> List[str]:
        """
        根据筛选条件下载图像
        
        Args:
            filter_params: 筛选参数，将传递给API
            limit: 最多下载图像数量
            save_metadata: 是否保存图像元数据
            
        Returns:
            下载任务ID列表
        """
        pass
    
    def download_single_image(self, image_id: int, 
                           output_path: Optional[str] = None,
                           save_metadata: bool = True) -> str:
        """
        下载单张图像
        
        Args:
            image_id: 图像ID
            output_path: 自定义保存路径 (可选)
            save_metadata: 是否保存图像元数据
            
        Returns:
            下载任务ID
        """
        pass
    
    def get_task(self, task_id: str) -> Optional[ImageDownloadTask]:
        """
        获取指定的图像下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            图像下载任务对象，如不存在则返回None
        """
        pass
    
    def get_all_tasks(self) -> List[ImageDownloadTask]:
        """
        获取所有图像下载任务
        
        Returns:
            图像下载任务列表
        """
        pass
    
    def extract_image_metadata(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从图像数据中提取元数据
        
        Args:
            image_data: 图像API返回的数据
            
        Returns:
            处理后的元数据字典
        """
        pass
    
    def save_metadata_file(self, image_path: str, metadata: Dict[str, Any],
                          format: str = "json") -> str:
        """
        保存图像元数据到文件
        
        Args:
            image_path: 图像文件路径
            metadata: 元数据字典
            format: 保存格式 ("json", "txt", "exif")
            
        Returns:
            元数据文件路径
        """
        pass
    
    def register_image_downloaded_callback(self, 
                                        callback: Callable[[ImageDownloadTask], None]) -> None:
        """
        注册图像下载完成回调函数
        
        Args:
            callback: 接收ImageDownloadTask的回调函数
        """
        pass


class ImageDownloadTask:
    """
    表示单个图像下载任务的状态和元数据
    """
    
    def __init__(self, task_id: str, image_id: int, image_url: str,
                 model_id: Optional[int] = None, model_name: Optional[str] = None,
                 creator: Optional[str] = None, nsfw_level: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        初始化图像下载任务
        
        Args:
            task_id: 下载任务ID
            image_id: 图像ID
            image_url: 图像URL
            model_id: 关联的模型ID (可选)
            model_name: 关联的模型名称 (可选)
            creator: 上传者用户名 (可选)
            nsfw_level: NSFW级别 (可选)
            metadata: 图像元数据 (可选)
        """
        pass
    
    @property
    def id(self) -> str:
        """获取任务ID"""
        pass
    
    @property
    def image_id(self) -> int:
        """获取图像ID"""
        pass
    
    @property
    def image_url(self) -> str:
        """获取图像URL"""
        pass
    
    @property
    def status(self) -> str:
        """获取下载状态"""
        pass
    
    @property
    def progress(self) -> float:
        """获取下载进度"""
        pass
    
    @property
    def image_path(self) -> Optional[str]:
        """获取下载图像的保存路径"""
        pass
    
    @property
    def metadata_path(self) -> Optional[str]:
        """获取元数据文件的保存路径"""
        pass
    
    @property
    def error(self) -> Optional[str]:
        """获取错误信息(如果有)"""
        pass
```

## 实现思路

### 游标分页处理

图像API自2023年7月2日起改用游标分页，模块需要特殊处理确保能获取所有页面：

1. 初始请求不指定游标参数
2. 从响应的`metadata.nextCursor`获取下一页游标
3. 后续请求使用此游标值
4. 直到没有`nextCursor`或`nextPage`值

### 元数据提取与保存策略

1. 从API响应中解析`meta`字段获取生成参数
2. 根据配置选择以下保存格式：
   - JSON: 完整保存所有元数据
   - TXT: 保存关键生成参数，便于人工阅读
   - EXIF: 嵌入到图像文件本身(可选功能)

### 图像文件组织策略

1. 使用可配置的路径模板动态生成保存路径
2. 针对不同使用场景提供预设模板：
   - 按模型ID组织: `{model_id}/{image_id}`
   - 按创作者组织: `{creator}/{image_id}`
   - 按NSFW级别组织: `{nsfw_level}/{image_id}`
3. 自动创建必要的目录结构

### 并行下载控制

1. 使用下载引擎的线程池实现并行下载
2. 为图像下载设置独立的优先级
3. 批量下载时动态调整并发数

### 重复图像检测

1. 使用图像哈希或URL作为唯一标识
2. 下载前检查是否已存在相同文件
3. 可配置处理策略：跳过、替换或保留两者

## 配置选项

| 配置项                       | 类型   | 默认值             | 说明                            |
| ---------------------------- | ------ | ------------------ | ------------------------------- |
| `images.output_path`         | 字符串 | `./images`         | 图像保存的基础路径              |
| `images.path_template`       | 字符串 | `{model_id}/{id}`  | 图像保存路径模板                |
| `images.metadata_format`     | 字符串 | `json`             | 元数据保存格式(json, txt, exif) |
| `images.save_metadata`       | 布尔值 | `True`             | 是否保存元数据                  |
| `images.default_nsfw_filter` | 列表   | `["None", "Soft"]` | 默认NSFW过滤级别                |
| `images.max_concurrent`      | 整数   | `5`                | 最大并行下载数量                |
| `images.skip_existing`       | 布尔值 | `True`             | 是否跳过已存在的图像            |
| `images.generate_thumbnails` | 布尔值 | `False`            | 是否生成缩略图                  |
| `images.thumbnail_size`      | 元组   | `(256, 256)`       | 缩略图大小                      |

## 依赖关系

- **外部依赖**:
  - 依赖基础模块提供的API和下载能力

- **内部依赖**:
  - `CivitaiAPI`: 提供图像数据访问
  - `DownloadEngine`: 提供底层下载功能
  - `config`: 用于读取配置选项
  - `PIL` (可选): 用于图像处理和EXIF写入

## 注意事项与限制

1. **游标分页处理**:
   - 图像API使用游标分页，不能使用传统页码分页
   - 需要正确跟踪和使用nextCursor参数

2. **元数据格式不一致**:
   - 不同图像的meta字段可能包含不同的参数
   - 元数据提取需要健壮的错误处理

3. **图像URL有效期**:
   - 某些图像URL可能有访问限制或有效期
   - 建议及时下载而不是仅存储URL

4. **并发限制考虑**:
   - 过高的并发下载可能触发API限制
   - 应根据网络环境和服务器限制调整并发数

5. **存储空间问题**:
   - 图像可能占用大量存储空间
   - 应考虑添加存储空间检查功能

6. **NSFW内容处理**:
   - 需要尊重用户对NSFW内容的过滤偏好
   - 提供清晰的NSFW标记和隔离机制

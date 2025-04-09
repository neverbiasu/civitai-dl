# 模型下载模块

## 模块概述

模型下载模块提供了专门针对Civitai模型资源的下载管理功能，负责从API获取模型信息、处理下载请求、管理下载任务队列、验证文件完整性，并根据配置组织下载的文件。该模块构建在API客户端和下载引擎之上，为应用提供更高层次的模型下载业务逻辑。

### 主要职责

- 通过API获取模型和版本信息
- 处理模型下载请求并创建下载任务
- 按用户配置组织模型文件结构
- 验证下载文件的哈希值匹配性
- 管理批量下载队列和优先级
- 提供模型下载历史和状态查询

### 技术特性

- 模型版本智能选择
- 文件格式偏好匹配
- 自定义存储路径模板
- 文件哈希验证
- 批量下载队列管理
- 断点续传支持

## 接口定义

### 核心类

```python
class ModelDownloader:
    """
    Civitai模型下载管理器
    """
    
    def __init__(self, api_client: CivitaiAPI = None, download_engine: DownloadEngine = None,
                 output_path: str = "./downloads", 
                 path_template: str = "{type}/{creator}/{name}"):
        """
        初始化模型下载管理器
        
        Args:
            api_client: Civitai API客户端实例，如果为None则创建新实例
            download_engine: 下载引擎实例，如果为None则创建新实例
            output_path: 模型文件保存的基础路径
            path_template: 模型保存路径模板，支持的变量包括:
                {type} - 模型类型
                {creator} - 创建者名称
                {name} - 模型名称
                {id} - 模型ID
                {version} - 版本名称
                {version_id} - 版本ID
        """
        pass
    
    def download_model(self, model_id: int, version_id: Optional[int] = None,
                      preferred_format: Optional[str] = None,
                      output_path: Optional[str] = None) -> str:
        """
        下载指定的模型
        
        Args:
            model_id: 模型ID
            version_id: 特定版本ID (可选)，如不提供则下载最新版本
            preferred_format: 首选文件格式 ('SafeTensor', 'PickleTensor', 等)
            output_path: 自定义保存路径 (可选)
            
        Returns:
            下载任务ID
            
        Raises:
            ModelNotFoundError: 模型不存在
            VersionNotFoundError: 指定的版本不存在
            ApiError: API调用失败
        """
        pass
    
    def download_models(self, model_ids: List[int], 
                       preferred_format: Optional[str] = None) -> List[str]:
        """
        批量下载多个模型
        
        Args:
            model_ids: 模型ID列表
            preferred_format: 首选文件格式
            
        Returns:
            下载任务ID列表
        """
        pass
    
    def download_by_filter(self, filter_params: Dict[str, Any], 
                         limit: int = 10,
                         preferred_format: Optional[str] = None) -> List[str]:
        """
        根据筛选条件批量下载模型
        
        Args:
            filter_params: 筛选参数，传递给API的搜索参数
            limit: 最多下载的模型数量
            preferred_format: 首选文件格式
            
        Returns:
            下载任务ID列表
        """
        pass
    
    def get_task(self, task_id: str) -> Optional[ModelDownloadTask]:
        """
        获取指定的下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            模型下载任务对象，如不存在则返回None
        """
        pass
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消指定的下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            操作是否成功
        """
        pass
    
    def pause_task(self, task_id: str) -> bool:
        """
        暂停指定的下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            操作是否成功
        """
        pass
    
    def resume_task(self, task_id: str) -> bool:
        """
        恢复指定的下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            操作是否成功
        """
        pass
    
    def get_all_tasks(self) -> List[ModelDownloadTask]:
        """
        获取所有模型下载任务
        
        Returns:
            模型下载任务列表
        """
        pass
    
    def get_active_tasks(self) -> List[ModelDownloadTask]:
        """
        获取当前活动的模型下载任务
        
        Returns:
            活动的模型下载任务列表
        """
        pass
    
    def verify_model(self, model_path: str, model_hash: Dict[str, str]) -> bool:
        """
        验证下载的模型文件完整性
        
        Args:
            model_path: 模型文件路径
            model_hash: 哈希值字典，键为哈希算法，值为哈希字符串
            
        Returns:
            验证是否通过
        """
        pass
    
    def register_model_downloaded_callback(self, 
                                         callback: Callable[[ModelDownloadTask], None]) -> None:
        """
        注册模型下载完成回调函数
        
        Args:
            callback: 接收ModelDownloadTask的回调函数
        """
        pass


class ModelDownloadTask:
    """
    表示单个模型下载任务的状态和元数据
    """
    
    def __init__(self, task_id: str, model_id: int, version_id: int, 
                 model_name: str, version_name: str,
                 creator: Optional[str] = None, model_type: Optional[str] = None):
        """
        初始化模型下载任务
        
        Args:
            task_id: 下载任务ID
            model_id: 模型ID
            version_id: 版本ID
            model_name: 模型名称
            version_name: 版本名称
            creator: 创建者名称(可选)
            model_type: 模型类型(可选)
        """
        pass
    
    @property
    def id(self) -> str:
        """获取任务ID"""
        pass
    
    @property
    def model_id(self) -> int:
        """获取模型ID"""
        pass
    
    @property
    def version_id(self) -> int:
        """获取版本ID"""
        pass
    
    @property
    def model_name(self) -> str:
        """获取模型名称"""
        pass
    
    @property
    def version_name(self) -> str:
        """获取版本名称"""
        pass
    
    @property
    def creator(self) -> Optional[str]:
        """获取创建者名称"""
        pass
    
    @property
    def model_type(self) -> Optional[str]:
        """获取模型类型"""
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
    def download_path(self) -> Optional[str]:
        """获取下载文件保存路径"""
        pass
    
    @property
    def error(self) -> Optional[str]:
        """获取错误信息(如果有)"""
        pass
    
    @property
    def created_at(self) -> datetime:
        """获取任务创建时间"""
        pass
    
    @property
    def completed_at(self) -> Optional[datetime]:
        """获取任务完成时间"""
        pass
    
    @property
    def download_url(self) -> str:
        """获取下载URL"""
        pass
    
    @property
    def file_size(self) -> Optional[int]:
        """获取文件大小(字节)"""
        pass
    
    @property
    def download_speed(self) -> Optional[float]:
        """获取下载速度(字节/秒)"""
        pass
```

## 使用示例

### 基本模型下载

```python
from civitai.models.downloader import ModelDownloader
from civitai.api.client import CivitaiAPI

# 创建API客户端和下载管理器
api = CivitaiAPI(api_key="your_api_key")
downloader = ModelDownloader(
    api_client=api, 
    output_path="./my_models"
)

# 下载指定ID的模型(最新版本)
task_id = downloader.download_model(model_id=12345)
print(f"下载任务已创建: {task_id}")

# 获取任务并监控进度
task = downloader.get_task(task_id)
while task.status == "downloading":
    print(f"下载进度: {task.progress * 100:.1f}%")
    time.sleep(1)
    task = downloader.get_task(task_id)  # 刷新任务状态

if task.status == "completed":
    print(f"模型已下载到: {task.download_path}")
else:
    print(f"下载失败: {task.error}")
```

### 自定义版本和格式

```python
# 下载特定版本并指定首选格式
task_id = downloader.download_model(
    model_id=12345,
    version_id=67890,
    preferred_format="SafeTensor"
)

# 使用自定义路径保存
task_id = downloader.download_model(
    model_id=12345,
    output_path="./special_models/my_model"
)
```

### 批量下载

```python
# 批量下载多个模型
model_ids = [12345, 67890, 98765]
task_ids = downloader.download_models(model_ids)

# 监控所有任务的整体进度
active_tasks = len(task_ids)
while active_tasks > 0:
    tasks = downloader.get_all_tasks()
    completed = sum(1 for t in tasks if t.status == "completed")
    failed = sum(1 for t in tasks if t.status == "failed")
    active_tasks = len(task_ids) - completed - failed
    
    print(f"进度: 完成 {completed}/{len(task_ids)}, 失败 {failed}")
    time.sleep(2)

# 检查结果
for task_id in task_ids:
    task = downloader.get_task(task_id)
    if task.status == "completed":
        print(f"模型 {task.model_name} 已下载到: {task.download_path}")
    else:
        print(f"模型 {task.model_name} 下载失败: {task.error}")
```

### 使用筛选条件下载

```python
# 下载符合筛选条件的模型
filter_params = {
    "types": ["LORA"],
    "query": "portrait",
    "sort": "Most Downloaded",
    "period": "Month"
}

task_ids = downloader.download_by_filter(
    filter_params=filter_params,
    limit=5,  # 最多下载5个模型
    preferred_format="SafeTensor"
)

print(f"已添加 {len(task_ids)} 个下载任务")
```

### 注册下载完成回调

```python
def on_model_downloaded(task):
    """模型下载完成回调函数"""
    if task.status == "completed":
        print(f"模型 {task.model_name} 下载完成!")
        print(f"类型: {task.model_type}, 创建者: {task.creator}")
        print(f"保存位置: {task.download_path}")
        
        # 这里可以添加下载后处理逻辑
        if task.model_type == "LORA":
            print("正在处理LORA模型...")
            # process_lora_model(task.download_path)
    else:
        print(f"模型 {task.model_name} 下载失败: {task.error}")

# 注册回调函数
downloader.register_model_downloaded_callback(on_model_downloaded)

# 下载模型(完成后会自动调用回调函数)
downloader.download_model(12345)
```

## 实现细节

### 模型下载流程

模型下载的完整流程包含多个步骤，从获取元数据到执行下载：

```python
def download_model(self, model_id, version_id=None, preferred_format=None, output_path=None):
    """下载指定的模型"""
    # 步骤1: 从API获取模型信息
    try:
        model_info = self.api_client.get_model(model_id)
    except Exception as e:
        raise ModelNotFoundError(f"无法获取模型信息: {str(e)}")
    
    # 步骤2: 确定要下载的版本
    if version_id:
        # 使用指定版本
        version = next((v for v in model_info["modelVersions"] if v["id"] == version_id), None)
        if not version:
            raise VersionNotFoundError(f"找不到版本ID: {version_id}")
    else:
        # 默认使用最新版本(列表中的第一个)
        version = model_info["modelVersions"][0]
    
    # 步骤3: 选择最佳文件格式
    version_info = self.api_client.get_model_version(version["id"])
    target_file = self._select_preferred_file(version_info["files"], preferred_format)
    
    # 步骤4: 构建下载URL和保存路径
    download_url = f"https://civitai.com/api/download/models/{version['id']}"
    api_key = self.api_client.api_key
    if api_key:
        download_url += f"?token={api_key}"
    
    # 步骤5: 确定保存路径
    if output_path:
        save_path = output_path
    else:
        # 使用模板构建路径
        path_vars = {
            "type": model_info.get("type", "Unknown"),
            "creator": model_info.get("creator", {}).get("username", "Unknown"),
            "name": model_info.get("name", f"model_{model_id}"),
            "id": model_id,
            "version": version.get("name", "v1"),
            "version_id": version["id"]
        }
        relative_path = self.path_template.format(**path_vars)
        save_path = os.path.join(self.output_path, relative_path)
    
    # 步骤6: 确保目录存在
    os.makedirs(save_path, exist_ok=True)
    
    # 步骤7: 创建下载任务
    task = ModelDownloadTask(
        task_id=f"model_{model_id}_{version['id']}_{int(time.time())}",
        model_id=model_id,
        version_id=version["id"],
        model_name=model_info["name"],
        version_name=version["name"],
        creator=model_info.get("creator", {}).get("username"),
        model_type=model_info["type"]
    )
    
    # 步骤8: 启动下载
    download_task = self.download_engine.download(
        url=download_url,
        output_path=save_path,
        filename=target_file["name"] if target_file else None
    )
    
    # 步骤9: 关联下载任务和模型任务
    self.tasks[task.id] = {
        "model_task": task,
        "download_task": download_task
    }
    
    return task.id
```

### 文件格式选择逻辑

```python
def _select_preferred_file(self, files, preferred_format=None):
    """选择最佳文件格式"""
    if not files:
        return None
        
    # 如果只有一个文件，直接返回
    if len(files) == 1:
        return files[0]
    
    # 优先选择主文件
    primary_files = [f for f in files if f.get("primary", False)]
    if primary_files:
        candidates = primary_files
    else:
        candidates = files
    
    # 如果指定了首选格式，按格式筛选
    if preferred_format and candidates:
        format_matches = [f for f in candidates 
                          if f.get("metadata", {}).get("format") == preferred_format]
        if format_matches:
            candidates = format_matches
    
    # 优先选择SafeTensor格式
    safe_tensors = [f for f in candidates 
                    if f.get("metadata", {}).get("format") == "SafeTensor"]
    if safe_tensors:
        return safe_tensors[0]
    
    # 否则返回第一个文件
    return candidates[0]
```

### 下载状态跟踪

```python
def _update_task_status(self):
    """更新所有任务的状态"""
    for task_id, task_data in list(self.tasks.items()):
        model_task = task_data["model_task"]
        download_task = task_data["download_task"]
        
        # 更新模型任务状态
        if download_task.status == "completed":
            model_task.status = "completed"
            model_task.progress = 1.0
            model_task.download_path = download_task.file_path
            model_task.completed_at = datetime.now()
            
            # 调用回调函数
            for callback in self._downloaded_callbacks:
                try:
                    callback(model_task)
                except Exception as e:
                    print(f"回调函数执行错误: {str(e)}")
                    
        elif download_task.status == "failed":
            model_task.status = "failed"
            model_task.error = download_task.error
            model_task.completed_at = datetime.now()
            
            # 调用回调函数
            for callback in self._downloaded_callbacks:
                try:
                    callback(model_task)
                except Exception as e:
                    print(f"回调函数执行错误: {str(e)}")
                    
        else:
            # 更新进度
            model_task.status = download_task.status
            model_task.progress = download_task.progress
            model_task.file_size = download_task.total_size
            model_task.download_speed = download_task.speed
```

## 配置选项

| 配置项                            | 类型   | 默认值                    | 说明                   |
| --------------------------------- | ------ | ------------------------- | ---------------------- |
| `models.output_path`              | 字符串 | `./downloads`             | 模型文件保存的基础路径 |
| `models.path_template`            | 字符串 | `{type}/{creator}/{name}` | 模型存储路径模板       |
| `models.preferred_format`         | 字符串 | `SafeTensor`              | 首选模型文件格式       |
| `models.verify_hash`              | 布尔值 | `True`                    | 是否校验文件哈希       |
| `models.max_concurrent_downloads` | 整数   | `3`                       | 最大并行下载数量       |
| `models.auto_retry_failed`        | 布尔值 | `True`                    | 失败任务是否自动重试   |
| `models.max_retries`              | 整数   | `3`                       | 最大重试次数           |
| `models.retry_delay`              | 整数   | `5`                       | 重试间隔(秒)           |

## 依赖关系

- **外部依赖**:
  - 依赖基础模块提供的API和下载能力

- **内部依赖**:
  - `CivitaiAPI`: 提供模型数据访问
  - `DownloadEngine`: 提供底层下载功能
  - `config`: 用于读取配置选项
  - `utils.hash`: 用于验证文件完整性

## 注意事项与限制

1. **API密钥要求**:
   - 某些模型可能需要API密钥才能下载
   - 建议用户配置API密钥以确保所有模型可访问

2. **路径模板限制**:
   - 路径变量仅限于API返回的模型元数据字段
   - 特殊字符在不同操作系统上可能导致路径问题

3. **文件选择逻辑**:
   - 首选格式不可用时会自动选择其他格式
   - 优先选择SafeTensor格式以避免安全问题

4. **并行下载限制**:
   - 过多并行下载可能触发API限制
   - 应根据实际环境调整并行下载数量

5. **存储空间检查**:
   - 模块目前不会预检查磁盘空间
   - 大型模型文件可能导致存储空间不足问题

6. **哈希验证**:
   - 仅当API返回哈希值时才能进行验证
   - 不同算法的哈希支持取决于API返回数据

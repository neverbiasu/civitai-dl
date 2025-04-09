# 下载引擎模块

## 模块概述

下载引擎是Civitai Downloader的核心基础设施，负责提供高效、可靠的文件下载能力，支持断点续传、并行下载、进度跟踪和错误恢复等关键特性。该模块独立于特定的资源类型，为模型下载、图像下载等业务模块提供统一的底层下载服务。

### 主要职责

- 执行HTTP文件下载
- 管理下载任务和队列
- 实现断点续传
- 控制并行下载数量
- 提供下载进度跟踪
- 处理下载错误和重试
- 支持下载后回调处理

### 技术特性

- 基于线程池的并行下载
- HTTP Range请求支持
- 事件驱动的进度通知
- 可配置的重试策略
- 优先级下载队列
- 流式大文件处理

## 接口定义

### 核心类

```python
class DownloadTask:
    """
    表示单个下载任务的类
    """
    
    def __init__(self, url: str, output_path: str, filename: Optional[str] = None, 
                 headers: Optional[Dict[str, str]] = None, priority: int = 0):
        """
        初始化下载任务
        
        Args:
            url: 下载文件的URL
            output_path: 保存文件的目录路径
            filename: 保存的文件名(可选)，如果不提供则从URL或响应头中提取
            headers: 请求头(可选)
            priority: 任务优先级，数字越小优先级越高
        """
        pass
    
    @property
    def id(self) -> str:
        """获取任务唯一标识符"""
        pass
    
    @property
    def status(self) -> str:
        """获取当前状态 (pending, downloading, paused, completed, failed)"""
        pass
    
    @property
    def progress(self) -> float:
        """获取下载进度 (0.0 到 1.0)"""
        pass
    
    @property
    def speed(self) -> float:
        """获取当前下载速度 (bytes/s)"""
        pass
    
    @property
    def error(self) -> Optional[str]:
        """获取错误信息(如果有)"""
        pass
    
    @property
    def file_path(self) -> Optional[str]:
        """获取完整的文件保存路径"""
        pass
    
    @property
    def downloaded_size(self) -> int:
        """获取已下载的字节数"""
        pass
    
    @property
    def total_size(self) -> int:
        """获取文件总字节数"""
        pass
    
    @property
    def eta(self) -> Optional[int]:
        """获取预估完成时间(秒)"""
        pass
    
    def update_progress(self, progress: float) -> None:
        """
        更新下载进度
        
        Args:
            progress: 完成百分比 (0.0 到 1.0)
        """
        pass
    
    def cancel(self) -> bool:
        """
        取消下载任务
        
        Returns:
            操作是否成功
        """
        pass
    
    def pause(self) -> bool:
        """
        暂停下载任务
        
        Returns:
            操作是否成功
        """
        pass
    
    def resume(self) -> bool:
        """
        恢复下载任务
        
        Returns:
            操作是否成功
        """
        pass


class DownloadEngine:
    """
    下载引擎：管理下载任务并执行下载操作
    """
    
    def __init__(self, max_workers: int = 3, chunk_size: int = 8192, 
                 retry_times: int = 3, retry_delay: int = 5):
        """
        初始化下载引擎
        
        Args:
            max_workers: 最大并行下载线程数
            chunk_size: 下载分块大小(字节)
            retry_times: 下载失败重试次数
            retry_delay: 重试间隔(秒)
        """
        pass
    
    def download(self, url: str, output_path: str, filename: Optional[str] = None,
                headers: Optional[Dict[str, str]] = None, 
                priority: int = 0) -> DownloadTask:
        """
        创建并提交一个下载任务
        
        Args:
            url: 下载文件的URL
            output_path: 保存文件的目录路径
            filename: 保存的文件名(可选)，如果不提供则从URL或响应头中提取
            headers: 请求头(可选)
            priority: 任务优先级，数字越小优先级越高
            
        Returns:
            创建的下载任务对象
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
    
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """
        获取指定的下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            下载任务对象，如不存在则返回None
        """
        pass
    
    def get_all_tasks(self) -> List[DownloadTask]:
        """
        获取所有下载任务
        
        Returns:
            下载任务列表
        """
        pass
    
    def get_active_tasks(self) -> List[DownloadTask]:
        """
        获取当前活动的下载任务
        
        Returns:
            活动的下载任务列表
        """
        pass
    
    def register_progress_callback(self, callback: Callable[[DownloadTask], None]) -> None:
        """
        注册进度更新回调函数，当任务进度更新时调用
        
        Args:
            callback: 接收任务对象的回调函数
        """
        pass
    
    def register_completion_callback(self, callback: Callable[[DownloadTask], None]) -> None:
        """
        注册任务完成回调函数，当任务完成时调用
        
        Args:
            callback: 接收任务对象的回调函数
        """
        pass
    
    def shutdown(self, wait: bool = True) -> None:
        """
        关闭下载引擎
        
        Args:
            wait: 是否等待所有任务完成
        """
        pass
```

### 辅助类

```python
class DownloadQueue:
    """管理下载任务队列，支持优先级排序"""
    
    def __init__(self):
        """初始化下载队列"""
        pass
    
    def add_task(self, task: DownloadTask) -> None:
        """添加任务到队列"""
        pass
    
    def get_next_task(self) -> Optional[DownloadTask]:
        """获取下一个要执行的任务"""
        pass
    
    def remove_task(self, task_id: str) -> bool:
        """移除指定的任务"""
        pass
    
    def get_all_tasks(self) -> List[DownloadTask]:
        """获取所有队列中的任务"""
        pass
    
    def clear(self) -> None:
        """清空队列"""
        pass
    
    def __len__(self) -> int:
        """获取队列长度"""
        pass


class DownloadStats:
    """下载统计数据收集器"""
    
    def __init__(self):
        """初始化统计收集器"""
        pass
    
    def start_task(self, task_id: str) -> None:
        """记录任务开始"""
        pass
    
    def update_task_progress(self, task_id: str, bytes_downloaded: int, 
                            total_bytes: int, speed: float) -> None:
        """更新任务进度"""
        pass
    
    def complete_task(self, task_id: str) -> None:
        """记录任务完成"""
        pass
    
    def fail_task(self, task_id: str, error: str) -> None:
        """记录任务失败"""
        pass
    
    def get_overall_speed(self) -> float:
        """获取总体下载速度 (bytes/s)"""
        pass
    
    def get_completed_bytes(self) -> int:
        """获取已下载总字节数"""
        pass
    
    def get_total_bytes(self) -> int:
        """获取总计划下载字节数"""
        pass
    
    def get_overall_progress(self) -> float:
        """获取总体下载进度 (0.0 到 1.0)"""
        pass
```

## 使用示例

### 基本下载操作

```python
from civitai.core.downloader import DownloadEngine

# 创建下载引擎
engine = DownloadEngine(max_workers=3)

# 执行简单下载
task = engine.download(
    url="https://example.com/large-file.zip",
    output_path="./downloads",
    filename="my-download.zip"
)

# 打印任务ID供后续引用
print(f"任务ID: {task.id}")

# 等待下载完成
while task.status == "downloading":
    print(f"下载进度: {task.progress * 100:.1f}%, "
          f"速度: {task.speed / 1024 / 1024:.2f} MB/s, "
          f"已下载: {task.downloaded_size / 1024 / 1024:.2f} MB")
    time.sleep(1)

if task.status == "completed":
    print(f"下载完成: {task.file_path}")
else:
    print(f"下载失败: {task.error}")
```

### 使用进度回调

```python
def progress_callback(task):
    """任务进度更新时的回调函数"""
    if task.status == "downloading":
        print(f"任务 {task.id} 进度: {task.progress * 100:.1f}%")
    
def completion_callback(task):
    """任务完成时的回调函数"""
    if task.status == "completed":
        print(f"任务 {task.id} 已完成: {task.file_path}")
    elif task.status == "failed":
        print(f"任务 {task.id} 失败: {task.error}")

# 注册回调函数
engine.register_progress_callback(progress_callback)
engine.register_completion_callback(completion_callback)

# 执行下载
task = engine.download("https://example.com/large-file.zip", "./downloads")
```

### 批量下载管理

```python
# 同时提交多个下载任务
tasks = []
for url in urls_list:
    task = engine.download(url, "./downloads")
    tasks.append(task)

# 等待所有任务完成
while any(task.status == "downloading" or task.status == "pending" for task in tasks):
    completed = sum(1 for task in tasks if task.status == "completed")
    print(f"完成进度: {completed}/{len(tasks)}")
    time.sleep(1)

# 检查所有任务结果
for i, task in enumerate(tasks):
    if task.status == "completed":
        print(f"文件 {i+1} 下载成功: {task.file_path}")
    else:
        print(f"文件 {i+1} 下载失败: {task.error}")
```

### 暂停和恢复下载

```python
# 创建下载任务
task = engine.download("https://example.com/very-large-file.zip", "./downloads")
print(f"开始下载: {task.id}")

# 等待一段时间
time.sleep(10)

# 暂停下载
if engine.pause_task(task.id):
    print(f"已暂停下载，当前进度: {task.progress * 100:.1f}%")
    
time.sleep(5)  # 做些别的事情

# 恢复下载
if engine.resume_task(task.id):
    print("已恢复下载")
```

## 实现细节

### 断点续传实现

下载引擎通过HTTP Range请求支持断点续传，关键代码如下：

```python
def _download_file(self, task):
    """执行文件下载，支持进度跟踪和断点续传"""
    local_filename = None
    headers = {}
    
    try:
        # 检查文件是否已经存在（支持断点续传）
        file_path = os.path.join(task.output_path, task.filename)
        file_size = 0
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > 0:
                headers['Range'] = f'bytes={file_size}-'
        
        # 执行下载
        with requests.get(task.url, headers=headers, stream=True) as response:
            response.raise_for_status()
            
            if 'content-length' in response.headers:
                total_size = int(response.headers['content-length'])
                if 'Range' in headers and response.status_code == 206:
                    total_size += file_size
            else:
                total_size = 0
            
            mode = 'ab' if file_size > 0 else 'wb'
            with open(file_path, mode) as f:
                downloaded = file_size
                start_time = time.time()
                last_update_time = start_time
                bytes_since_last_update = 0
                
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if task.status == "cancelled":
                        return None
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        bytes_since_last_update += len(chunk)
                        
                        # 更新下载速度和进度
                        current_time = time.time()
                        if current_time - last_update_time >= 0.5:  # 每0.5秒更新一次
                            speed = bytes_since_last_update / (current_time - last_update_time)
                            progress = downloaded / total_size if total_size > 0 else 0
                            
                            # 更新任务状态
                            task.update_progress(progress)
                            task.speed = speed
                            task.downloaded_size = downloaded
                            task.total_size = total_size
                            
                            # 调用进度回调
                            for callback in self._progress_callbacks:
                                callback(task)
                                
                            last_update_time = current_time
                            bytes_since_last_update = 0
    
        # 下载完成
        task.status = "completed"
        task.progress = 1.0
        task.end_time = time.time()
        
        # 调用完成回调
        for callback in self._completion_callbacks:
            callback(task)
            
        return file_path
        
    except Exception as e:
        # 下载失败
        task.status = "failed"
        task.error = str(e)
        
        # 调用完成回调
        for callback in self._completion_callbacks:
            callback(task)
        
        raise e
```

### 优先级队列实现

下载队列使用优先级队列管理任务：

```python
class DownloadQueue:
    def __init__(self):
        self._queue = PriorityQueue()
        self._tasks = {}
        self._lock = threading.Lock()
    
    def add_task(self, task):
        """添加任务到队列"""
        with self._lock:
            if task.id not in self._tasks:
                self._queue.put((task.priority, task.id))
                self._tasks[task.id] = task
    
    def get_next_task(self):
        """获取下一个要执行的任务"""
        try:
            _, task_id = self._queue.get_nowait()
            with self._lock:
                if task_id in self._tasks:
                    return self._tasks[task_id]
            return None
        except Empty:
            return None
    
    def remove_task(self, task_id):
        """移除指定的任务"""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                # 注意：从优先级队列中移除特定项是困难的
                # 实际实现中，我们可以标记任务为已取消，并在获取时忽略它
                return True
        return False
```

### 线程池管理

使用线程池执行并行下载：

```python
class DownloadEngine:
    def __init__(self, max_workers=3, chunk_size=8192, retry_times=3, retry_delay=5):
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        
        # 创建线程池
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 任务管理
        self.tasks = {}
        self.queue = DownloadQueue()
        self.task_futures = {}
        self._lock = threading.Lock()
        
        # 回调注册
        self._progress_callbacks = []
        self._completion_callbacks = []
        
        # 启动调度线程
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self._scheduler_thread.daemon = True
        self._scheduler_thread.start()
    
    def _scheduler_loop(self):
        """任务调度循环，负责从队列取出任务并提交到线程池"""
        while self._scheduler_running:
            # 检查活动任务数，如果未达到上限则提交新任务
            active_count = sum(1 for f in self.task_futures.values() 
                              if f and not f.done())
            
            if active_count < self.max_workers:
                # 从队列中获取下一个任务
                task = self.queue.get_next_task()
                if task and task.status == "pending":
                    # 提交任务到线程池
                    task.status = "downloading"
                    task.start_time = time.time()
                    future = self.executor.submit(self._download_with_retry, task)
                    with self._lock:
                        self.task_futures[task.id] = future
            
            # 短暂睡眠避免CPU占用
            time.sleep(0.1)
```

## 配置选项

| 配置项                         | 类型   | 默认值 | 说明                   |
| ------------------------------ | ------ | ------ | ---------------------- |
| `downloader.max_workers`       | 整数   | `3`    | 最大并行下载线程数     |
| `downloader.chunk_size`        | 整数   | `8192` | 下载分块大小(字节)     |
| `downloader.retry_times`       | 整数   | `3`    | 下载失败最大重试次数   |
| `downloader.retry_delay`       | 整数   | `5`    | 重试间隔时间(秒)       |
| `downloader.timeout`           | 整数   | `30`   | 连接超时时间(秒)       |
| `downloader.progress_interval` | 浮点数 | `0.5`  | 进度更新间隔(秒)       |
| `downloader.verify_hash`       | 布尔值 | `True` | 是否验证下载文件哈希值 |

## 依赖关系

- **外部依赖**:
  - `requests`: HTTP请求库
  - `concurrent.futures`: 线程池管理

- **内部依赖**:
  - `config`: 用于获取下载相关配置
  - `utils.hash`: 用于文件哈希验证(可选)

## 注意事项与限制

1. **大文件处理**:
   - 下载大型模型文件时的内存使用需特别注意
   - 使用流式处理以避免内存问题

2. **断点续传限制**:
   - 依赖服务器对Range请求的支持
   - 如果服务器不支持206状态码，将重新下载整个文件

3. **速度与并发控制**:
   - 过高的并发数可能导致网络连接问题
   - 应根据网络环境和服务器限制调整最大工作线程数

4. **文件系统限制**:
   - 下载前应检查目标路径的可用空间
   - 注意文件名和路径长度限制

5. **正确关闭**:
   - 应用退出前应调用`shutdown`方法确保资源正确释放
   - 未完成的下载会在下次启动时继续

6. **错误处理策略**:
   - 网络错误会自动重试，重试次数和间隔可配置
   - 磁盘错误(如空间不足)不会重试，会立即失败
   - 权限错误需要手动处理

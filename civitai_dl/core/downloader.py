"""下载引擎模块，提供高效、可靠的文件下载能力"""

import os
import time
import uuid
import requests
import threading
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, unquote


class DownloadTask:
    """表示单个下载任务的类，记录下载状态和进度"""

    def __init__(
        self,
        url: str,
        output_path: str,
        filename: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        priority: int = 0,
    ):
        """
        初始化下载任务

        Args:
            url: 下载文件的URL
            output_path: 保存文件的目录路径
            filename: 保存的文件名(可选)，如果不提供则从URL或响应头中提取
            headers: 请求头(可选)
            priority: 任务优先级，数字越小优先级越高
        """
        self.url = url
        self.output_path = output_path
        self.filename = filename
        self.headers = headers or {}
        self.priority = priority
        self.status = "pending"  # pending, downloading, paused, completed, failed
        self.progress = 0.0
        self.error = None
        self.start_time = None
        self.end_time = None
        self.downloaded_size = 0
        self.total_size = 0
        self.speed = 0.0
        self._id = str(uuid.uuid4())
        self._file_path = None

    @property
    def id(self) -> str:
        """获取任务唯一标识符"""
        return self._id

    @property
    def file_path(self) -> Optional[str]:
        """获取完整的文件保存路径"""
        if not self._file_path and self.filename:
            self._file_path = os.path.join(self.output_path, self.filename)
        return self._file_path

    @property
    def eta(self) -> Optional[int]:
        """获取预估完成时间(秒)"""
        if self.speed > 0 and self.total_size > 0:
            remaining_bytes = self.total_size - self.downloaded_size
            return int(remaining_bytes / self.speed)
        return None

    def update_progress(self, progress: float) -> None:
        """
        更新下载进度

        Args:
            progress: 完成百分比 (0.0 到 1.0)
        """
        self.progress = max(0.0, min(1.0, progress))

    def set_filename(self, filename: str) -> None:
        """设置文件名"""
        self.filename = filename
        self._file_path = None  # 重置文件路径，将在下次访问file_path时重新计算


class DownloadEngine:
    """下载引擎：管理下载任务并执行下载操作"""

    def __init__(
        self,
        max_workers: int = 3,
        chunk_size: int = 8192,
        retry_times: int = 3,
        retry_delay: int = 5,
    ):
        """
        初始化下载引擎

        Args:
            max_workers: 最大并行下载线程数
            chunk_size: 下载分块大小(字节)
            retry_times: 下载失败重试次数
            retry_delay: 重试间隔(秒)
        """
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.retry_times = retry_times
        self.retry_delay = retry_delay

        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = {}  # 任务字典 {task_id: task}
        self.task_futures = {}  # 任务Future字典 {task_id: future}

        self._progress_callbacks = []  # 进度回调函数列表
        self._completion_callbacks = []  # 完成回调函数列表
        self._lock = threading.Lock()  # 线程锁，保护共享资源

    def download(
        self,
        url: str,
        output_path: str,
        filename: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        priority: int = 0,
    ) -> DownloadTask:
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
        # 创建目录
        os.makedirs(output_path, exist_ok=True)

        # 创建任务
        task = DownloadTask(url, output_path, filename, headers, priority)

        with self._lock:
            self.tasks[task.id] = task

            # 提交下载任务到线程池
            future = self.executor.submit(self._download_with_retry, task)
            self.task_futures[task.id] = future

        return task

    def _download_with_retry(self, task: DownloadTask) -> Optional[str]:
        """
        执行下载，支持自动重试

        Args:
            task: 下载任务对象

        Returns:
            下载文件路径，如果失败则返回None
        """
        retries = 0
        while retries <= self.retry_times:
            try:
                return self._download_file(task)
            except Exception as e:
                retries += 1
                if retries > self.retry_times:
                    task.status = "failed"
                    task.error = str(e)
                    return None

                # 等待后重试
                time.sleep(self.retry_delay)

    def _download_file(self, task: DownloadTask) -> Optional[str]:
        """
        执行文件下载，支持进度跟踪和断点续传

        Args:
            task: 下载任务对象

        Returns:
            下载文件路径，如果失败则返回None
        """
        headers = task.headers.copy() if task.headers else {}

        # 尝试发送HEAD请求获取文件信息
        try:
            head_response = requests.head(task.url, headers=headers, timeout=30)
            head_response.raise_for_status()

            # 从Content-Disposition获取文件名
            if not task.filename and "Content-Disposition" in head_response.headers:
                content_disposition = head_response.headers["Content-Disposition"]
                if "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[1]
                    if filename.startswith('"') and filename.endswith('"'):
                        filename = filename[1:-1]
                    task.set_filename(filename)
        except Exception:
            # HEAD请求失败，继续尝试GET请求
            pass

        # 如果仍未获取文件名，从URL中提取
        if not task.filename:
            url_path = urlparse(task.url).path
            filename = unquote(os.path.basename(url_path))
            if filename:
                task.set_filename(filename)
            else:
                task.set_filename(f"download_{int(time.time())}")

        # 准备文件路径
        file_path = task.file_path

        # 检查文件是否已经存在（支持断点续传）
        file_size = 0
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > 0:
                headers["Range"] = f"bytes={file_size}-"

        # 更新任务状态
        task.status = "downloading"
        task.start_time = time.time()
        task.downloaded_size = file_size

        # 执行下载
        try:
            with requests.get(
                task.url, headers=headers, stream=True, timeout=30
            ) as response:
                response.raise_for_status()

                # 获取文件大小
                total_size = int(response.headers.get("content-length", 0))
                if "Range" in headers and response.status_code == 206:
                    total_size += file_size
                task.total_size = total_size

                # 打开文件写入数据
                mode = "ab" if file_size > 0 else "wb"
                with open(file_path, mode) as f:
                    downloaded = file_size
                    last_update_time = time.time()
                    bytes_since_last_update = 0

                    # 分块下载文件
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if not chunk:
                            continue

                        f.write(chunk)
                        downloaded += len(chunk)
                        bytes_since_last_update += len(chunk)

                        # 计算进度和速度
                        current_time = time.time()
                        time_diff = current_time - last_update_time

                        if time_diff >= 0.5:  # 每0.5秒更新一次状态
                            # 计算速度 (bytes/s)
                            task.speed = bytes_since_last_update / time_diff
                            # 更新进度
                            if total_size > 0:
                                task.progress = downloaded / total_size
                            task.downloaded_size = downloaded

                            # 调用进度回调
                            for callback in self._progress_callbacks:
                                try:
                                    callback(task)
                                except Exception as e:
                                    print(f"进度回调错误: {e}")

                            # 重置计时
                            last_update_time = current_time
                            bytes_since_last_update = 0

            # 下载完成
            task.status = "completed"
            task.progress = 1.0
            task.end_time = time.time()

            # 调用完成回调
            for callback in self._completion_callbacks:
                try:
                    callback(task)
                except Exception as e:
                    print(f"完成回调错误: {e}")

            return file_path

        except Exception as e:
            # 下载失败
            task.status = "failed"
            task.error = str(e)
            task.end_time = time.time()

            # 调用完成回调通知失败
            for callback in self._completion_callbacks:
                try:
                    callback(task)
                except Exception as e:
                    print(f"完成回调错误: {e}")

            raise e

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """
        获取指定的下载任务

        Args:
            task_id: 任务ID

        Returns:
            下载任务对象，如不存在则返回None
        """
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[DownloadTask]:
        """
        获取所有下载任务

        Returns:
            下载任务列表
        """
        return list(self.tasks.values())

    def cancel_task(self, task_id: str) -> bool:
        """
        取消指定的下载任务

        Args:
            task_id: 任务ID

        Returns:
            操作是否成功
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        if task.status in ["pending", "downloading"]:
            task.status = "cancelled"

            # 取消Future
            future = self.task_futures.get(task_id)
            if future and not future.done():
                future.cancel()

            return True
        return False

    def register_progress_callback(
        self, callback: Callable[[DownloadTask], None]
    ) -> None:
        """
        注册进度更新回调函数，当任务进度更新时调用

        Args:
            callback: 接收任务对象的回调函数
        """
        if callback not in self._progress_callbacks:
            self._progress_callbacks.append(callback)

    def register_completion_callback(
        self, callback: Callable[[DownloadTask], None]
    ) -> None:
        """
        注册任务完成回调函数，当任务完成时调用

        Args:
            callback: 接收任务对象的回调函数
        """
        if callback not in self._completion_callbacks:
            self._completion_callbacks.append(callback)

    def shutdown(self, wait: bool = True) -> None:
        """
        关闭下载引擎

        Args:
            wait: 是否等待所有任务完成
        """
        self.executor.shutdown(wait=wait)

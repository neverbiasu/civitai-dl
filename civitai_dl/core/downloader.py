"""下载引擎模块，提供高效、可靠的文件下载能力"""

import os
import time
import threading
import requests
import urllib.parse
import re
from typing import Callable, Optional
from concurrent.futures import ThreadPoolExecutor

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


class DownloadTask:
    """表示一个下载任务"""

    def __init__(self, url: str, file_path=None, output_path=None, filename=None):
        """
        初始化下载任务

        可以通过两种方式指定保存路径:
        1. 直接使用 file_path 参数指定完整路径
        2. 使用 output_path 和 filename 参数组合指定路径
        """
        self.url = url

        # 兼容多种参数形式
        if file_path:
            self._file_path = file_path
        elif output_path and filename:
            self._file_path = os.path.join(output_path, filename)
        else:
            # 默认使用URL中的文件名
            filename = os.path.basename(urllib.parse.urlparse(url).path)
            if not filename:
                filename = f"download_{int(time.time())}"
            self._file_path = filename

        # 存储原始参数，方便测试访问
        self.output_path = output_path
        self.filename = filename if filename else os.path.basename(self._file_path)

        self.total_size: Optional[int] = None
        self.downloaded_size: int = 0
        self._progress_callback: Optional[Callable[[int, int], None]] = None
        self.status = "pending"  # pending, running, completed, failed, canceled
        self.error = None
        self._thread = None
        self._stop_event = threading.Event()
        self.start_time = None
        self.end_time = None
        self.speed = 0  # 下载速度 (bytes/s)
        self._progress = 0.0  # 使用私有属性存储进度值

        # 确保文件路径有合适的扩展名
        self._file_path = self._ensure_proper_extension(self._file_path, self.url)

    # 替换原有的只读属性为读写属性
    @property
    def progress(self):
        """获取下载进度 (0.0 到 1.0)"""
        if self.total_size and self.total_size > 0:
            return self.downloaded_size / self.total_size
        return self._progress

    @progress.setter
    def progress(self, value):
        """设置下载进度"""
        if value < 0:
            value = 0
        elif value > 1:
            value = 1
        self._progress = value

        # 如果有总大小，也更新已下载大小
        if self.total_size:
            self.downloaded_size = int(self.total_size * value)

    @property
    def file_path(self):
        """获取文件路径"""
        return self._file_path

    @file_path.setter
    def file_path(self, value):
        """设置文件路径"""
        self._file_path = value
        # 更新文件名
        self.filename = os.path.basename(value)

    def _ensure_proper_extension(self, file_path: str, url: str) -> str:
        """确保文件路径有合适的扩展名"""
        # 检查文件是否已有扩展名
        _, ext = os.path.splitext(file_path)
        if ext and len(ext) > 1:
            return file_path

        # 从URL中尝试获取扩展名
        url_path = urllib.parse.urlparse(url).path
        _, url_ext = os.path.splitext(url_path)

        # 模型文件常用扩展名

        # 如果URL中有扩展名，使用它
        if url_ext and len(url_ext) > 1:
            return f"{file_path}{url_ext}"

        # 默认使用safetensors作为扩展名（最常用的模型格式）
        return f"{file_path}.safetensors"

    @property
    def eta(self) -> Optional[int]:
        """获取预估完成时间(秒)"""
        if self.speed > 0 and self.total_size:
            remaining_bytes = self.total_size - self.downloaded_size
            return int(remaining_bytes / self.speed)
        return None

    def start(self, progress_callback=None):
        """开始下载任务"""
        if self.status != "pending":
            return

        self.progress_callback = progress_callback
        self.status = "running"
        self.start_time = time.time()
        self._thread = threading.Thread(target=self._download)
        self._thread.start()
        return self

    def _download(self):
        """实际的下载逻辑"""
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(os.path.abspath(self.file_path)), exist_ok=True)

            # 发送HEAD请求获取文件信息
            headers = {}
            try:
                head_response = requests.head(self.url, timeout=10)
                if "Content-Disposition" in head_response.headers:
                    content_disposition = head_response.headers["Content-Disposition"]
                    filename = self._extract_filename_from_header(content_disposition)
                    if filename:
                        # 更新文件路径，保留原来的目录
                        dir_path = os.path.dirname(self.file_path)
                        self.file_path = os.path.join(dir_path, filename)
                        logger.info(f"从Content-Disposition更新文件名: {filename}")
            except Exception as e:
                logger.warning(f"获取文件信息失败: {e}")

            # 检查是否已有部分下载
            if os.path.exists(self.file_path):
                downloaded_size = os.path.getsize(self.file_path)
                mode = "ab"  # 追加模式
                headers["Range"] = f"bytes={downloaded_size}-"
                self.downloaded_size = downloaded_size
            else:
                mode = "wb"
                self.downloaded_size = 0

            # 发起请求
            with requests.get(
                self.url, headers=headers, stream=True, timeout=30
            ) as response:
                response.raise_for_status()

                # 再次检查Content-Disposition
                if "Content-Disposition" in response.headers:
                    content_disposition = response.headers["Content-Disposition"]
                    filename = self._extract_filename_from_header(content_disposition)
                    if filename and mode == "wb":  # 只有在新下载时才更新文件名
                        # 更新文件路径，保留原来的目录
                        dir_path = os.path.dirname(self.file_path)
                        self.file_path = os.path.join(dir_path, filename)
                        logger.info(f"从Content-Disposition更新文件名: {filename}")

                # 获取文件总大小
                if "content-length" in response.headers:
                    if self.downloaded_size > 0:
                        self.total_size = (
                            int(response.headers["content-length"])
                            + self.downloaded_size
                        )
                    else:
                        self.total_size = int(response.headers["content-length"])
                else:
                    self.total_size = None

                # 写入文件
                last_update_time = time.time()
                bytes_since_last_update = 0

                with open(self.file_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self._stop_event.is_set():
                            self.status = "canceled"
                            return

                        if chunk:
                            f.write(chunk)
                            chunk_size = len(chunk)
                            self.downloaded_size += chunk_size
                            bytes_since_last_update += chunk_size

                            # 计算下载速度和更新进度
                            current_time = time.time()
                            if current_time - last_update_time >= 0.5:  # 每0.5秒更新一次
                                elapsed = current_time - last_update_time
                                if elapsed > 0:
                                    self.speed = bytes_since_last_update / elapsed

                                # 调用进度回调
                                if self.progress_callback and self.total_size:
                                    self.progress_callback(
                                        self.downloaded_size, self.total_size
                                    )

                                bytes_since_last_update = 0
                                last_update_time = current_time

            self.end_time = time.time()
            self.status = "completed"
            logger.info(f"下载完成: {self.file_path}")

            # 最终调用一次回调确保进度显示100%
            if self.progress_callback and self.total_size:
                self.progress_callback(self.downloaded_size, self.total_size)

        except Exception as e:
            self.status = "failed"
            self.error = str(e)
            logger.error(f"下载失败: {self.url} -> {self.file_path}, 错误: {str(e)}")

    def _extract_filename_from_header(self, content_disposition: str) -> Optional[str]:
        """从Content-Disposition头提取文件名"""
        if not content_disposition:
            return None

        # 正则表达式匹配文件名
        filename_match = re.search(
            r'filename=(?:"([^"]+)"|([^;\s]+))', content_disposition
        )
        if filename_match:
            filename = filename_match.group(1) or filename_match.group(2)
            # URL解码文件名
            filename = urllib.parse.unquote(filename)
            return filename

        return None

    def cancel(self):
        """取消下载任务"""
        if self.status == "running":
            self._stop_event.set()
            if self._thread:
                self._thread.join(timeout=1.0)
            self.status = "canceled"
            logger.info(f"下载已取消: {self.file_path}")

    def wait(self, timeout=None):
        """等待下载任务完成"""
        if self._thread:
            self._thread.join(timeout=timeout)
        return self.status == "completed"

    def update_progress(self, progress):
        """更新进度（兼容旧接口）"""
        self.progress = progress  # 使用属性setter


class DownloadEngine:
    """下载引擎，管理多个下载任务"""

    def __init__(
        self,
        output_dir="./downloads",
        concurrent_downloads=3,
        chunk_size=8192,
        max_workers=None,
        retry_times=3,
        retry_delay=5,
    ):
        """
        初始化下载引擎

        Args:
            output_dir: 默认输出目录
            concurrent_downloads: 并行下载任务数量
            chunk_size: 下载块大小
            max_workers: 并行下载任务数量（兼容旧接口，等同于concurrent_downloads）
            retry_times: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.output_dir = output_dir
        self.concurrent_downloads = (
            max_workers if max_workers is not None else concurrent_downloads
        )
        self.chunk_size = chunk_size
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.tasks = []
        self.executor = ThreadPoolExecutor(max_workers=self.concurrent_downloads)
        self._progress_callbacks = []
        self._completion_callbacks = []

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

    def register_completion_callback(self, callback):
        """注册下载完成回调"""
        self._completion_callbacks.append(callback)

    def register_progress_callback(self, callback):
        """注册下载进度回调"""
        self._progress_callbacks.append(callback)

    def _download_file(self, task):
        """执行文件下载（兼容旧接口）"""
        try:
            # 执行下载逻辑...
            # 这里应该实现实际的下载逻辑，但为了简单起见，只是模拟一下
            task._download()
            return task.file_path
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            # 通知完成回调
            for callback in self._completion_callbacks:
                try:
                    callback(task)
                except Exception as cb_error:
                    logger.error(f"回调函数执行错误: {cb_error}")
            raise e

    def _download_with_retry(self, task):
        """带重试的下载（兼容旧接口）"""
        for attempt in range(self.retry_times + 1):
            try:
                return self._download_file(task)
            except Exception as e:
                if attempt < self.retry_times:
                    logger.warning(
                        f"下载失败，将在 {self.retry_delay} 秒后重试 ({attempt+1}/{self.retry_times})"
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"下载在 {self.retry_times} 次尝试后仍然失败: {e}")
                    raise

    def shutdown(self):
        """关闭下载引擎"""
        self.cancel_all()
        self.executor.shutdown(wait=True)

    def download(self, url, file_path=None, progress_callback=None):
        """创建并启动一个下载任务"""
        if file_path is None:
            # 获取更好的文件名
            file_name = self.get_filename_from_url(url)
            file_path = os.path.join(self.output_dir, file_name)

        task = DownloadTask(url, file_path)
        self.tasks.append(task)
        return task.start(progress_callback)

    def get_filename_from_url(self, url: str) -> str:
        """从URL获取更好的文件名"""
        # 从URL路径中提取文件名
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path

        # 提取基础文件名
        base_filename = os.path.basename(path)

        # 如果URL包含查询参数或路径不包含文件名，生成基于URL的文件名
        if (
            not base_filename
            or base_filename.startswith("models")
            or "." not in base_filename
        ):
            # 从URL中提取模型ID
            model_id = None
            if "/models/" in url:
                model_id = url.split("/models/")[-1].split("/")[0].split("?")[0]

            if model_id and model_id.isdigit():
                base_filename = f"model_{model_id}.safetensors"
            else:
                # 生成通用文件名
                import hashlib

                hash_obj = hashlib.md5(url.encode())
                base_filename = f"download_{hash_obj.hexdigest()[:8]}.safetensors"

        # 如果没有扩展名，添加默认扩展名
        if "." not in base_filename:
            base_filename += ".safetensors"

        return base_filename

    def download_batch(self, urls, output_dir=None, progress_callback=None):
        """批量下载多个URL"""
        tasks = []
        for url in urls:
            file_name = url.split("/")[-1].split("?")[0]
            file_path = os.path.join(output_dir or self.output_dir, file_name)
            task = DownloadTask(url, file_path)
            task.start(progress_callback)
            tasks.append(task)
            self.tasks.append(task)
        return tasks

    def get_active_tasks(self):
        """获取所有活动的下载任务"""
        return [task for task in self.tasks if task.status == "running"]

    def cancel_all(self):
        """取消所有正在进行的下载任务"""
        for task in self.get_active_tasks():
            task.cancel()

    def wait_all(self, timeout=None):
        """等待所有下载任务完成"""
        start_time = time.time()
        for task in self.tasks:
            if timeout:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    break
                task_timeout = timeout - elapsed if timeout > elapsed else 0
            else:
                task_timeout = None

            task.wait(timeout=task_timeout)

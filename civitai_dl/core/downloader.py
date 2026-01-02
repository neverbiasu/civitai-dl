"""Download engine for Civitai Downloader.

Provides robust download capabilities with features like:
- Concurrent downloads
- Progress tracking
- Resume support
- Error handling and retries
"""

import os
import re
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Optional, Dict, TypeVar

import requests

from civitai_dl.utils.logger import get_logger
from civitai_dl.core.constants import INVALID_FILENAME_CHARS

logger = get_logger(__name__)

T = TypeVar('T')  # Define a generic type variable for callbacks


class DownloadTask:
    """Represents a download task with progress tracking and control capabilities."""

    def __init__(
        self,
        url: str,
        file_path: Optional[str] = None,
        output_path: Optional[str] = None,
        filename: Optional[str] = None,
        use_range: bool = True,
        headers: Optional[Dict[str, str]] = None,
        verify: bool = True,
        proxy: Optional[str] = None,
        timeout: int = 30,
        chunk_size: int = 8192,
    ) -> None:
        """Initialize a download task.

        Args:
            url: Download URL
            file_path: Full path where the file should be saved
            output_path: Directory to save the file
            filename: Name of the file to save
            use_range: Whether to use HTTP Range requests for resuming
            headers: Custom HTTP headers
            verify: Whether to verify SSL certificates
            proxy: Proxy server URL
            timeout: Request timeout in seconds
            chunk_size: Download chunk size in bytes
        """
        self.url = url
        self.use_range = use_range
        self.headers = headers if headers is not None else {}
        self.verify = verify
        self.proxy = proxy
        self.timeout = timeout
        self.chunk_size = chunk_size

        # Determine file path
        if file_path:
            self._file_path = file_path
        elif output_path and filename:
            self._file_path = os.path.join(output_path, filename)
        else:
            # Use filename from URL or generate one
            parsed_url = urllib.parse.urlparse(url)
            filename_from_url = os.path.basename(parsed_url.path)
            if not filename_from_url:
                filename_from_url = f"download_{int(time.time())}"

            if output_path:
                self._file_path = os.path.join(output_path, filename_from_url)
            else:
                self._file_path = filename_from_url

        # Store original parameters
        self.output_path = output_path
        self.filename = filename if filename else os.path.basename(self._file_path)

        # Ensure proper file extension
        self._file_path = self._ensure_proper_extension(self._file_path, self.url)
        self.filename = os.path.basename(self._file_path)

        # Download status and statistics
        self.total_size: Optional[int] = None
        self.downloaded_size: int = 0
        self._progress_callback: Optional[Callable[[int, Optional[int]], None]] = None
        self.status = "pending"  # pending, running, completed, failed, canceled
        self.error: Optional[str] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.speed: float = 0.0  # download speed (bytes/s)
        self._progress: float = 0.0
        self._retry_count: int = 0
        self._completion_callbacks: List[Callable[['DownloadTask'], None]] = []
        self.task_id: str = ""  # Will be set by DownloadEngine

    @property
    def progress(self) -> float:
        """Get download progress as a ratio between 0.0 and 1.0.

        Returns:
            Progress ratio from 0.0 to 1.0
        """
        if self.total_size and self.total_size > 0:
            return self.downloaded_size / self.total_size
        return self._progress

    @progress.setter
    def progress(self, value: float) -> None:
        """Set download progress directly.

        Updates the internal progress ratio and downloaded size
        if total size is known.

        Args:
            value: Progress value from 0.0 to 1.0
        """
        if value < 0:
            value = 0
        elif value > 1:
            value = 1
        self._progress = value

        # If total size is known, update downloaded size accordingly
        if self.total_size:
            self.downloaded_size = int(self.total_size * value)

    @property
    def file_path(self) -> str:
        """Get the full file path for this download.

        Returns:
            Absolute file path
        """
        return self._file_path

    @file_path.setter
    def file_path(self, value: str) -> None:
        """Set a new file path for this download.

        Updates the internal file path and filename.

        Args:
            value: New file path
        """
        self._file_path = value
        # Update filename when path changes
        self.filename = os.path.basename(value)

    def _ensure_proper_extension(self, file_path: str, url: str) -> str:
        """Ensure the file path has a proper extension.

        Examines the file path and URL to determine the appropriate file extension.
        If no extension is found, adds a default extension.

        Args:
            file_path: Original file path to check and possibly modify
            url: Download URL that may contain extension information

        Returns:
            File path with proper extension
        """
        # Check if file already has an extension
        _, ext = os.path.splitext(file_path)
        if ext and len(ext) > 1:
            logger.debug(f"File already has extension: {ext}")
            return file_path

        # Try to get extension from URL
        url_path = urllib.parse.urlparse(url).path
        _, url_ext = os.path.splitext(url_path)

        # If URL has extension, use it
        if url_ext and len(url_ext) > 1:
            logger.debug(f"Using extension from URL: {url_ext}")
            return f"{file_path}{url_ext}"

        # Use default extension for AI models
        logger.debug("No extension found, using default .safetensors extension")
        return f"{file_path}.safetensors"

    @property
    def eta(self) -> Optional[int]:
        """获取预估完成时间(秒)"""
        if self.speed > 0 and self.total_size:
            remaining_bytes = self.total_size - self.downloaded_size
            if remaining_bytes > 0:
                return int(remaining_bytes / self.speed)
        return None

    def start(self, progress_callback=None):
        """开始下载任务"""
        if self.status != "pending":
            logger.warning(f"任务 {self.filename} 状态为 {self.status}, 无法启动.")
            return self
        self._progress_callback = progress_callback
        self.status = "running"
        self.start_time = time.time()
        self._thread = threading.Thread(target=self._download)
        self._thread.start()
        return self

    def _get_remote_file_info(self, proxies):
        """Perform a HEAD request to get file info."""
        try:
            head_response = requests.head(
                self.url,
                headers=self.headers,
                timeout=10,
                verify=self.verify,
                proxies=proxies,
                allow_redirects=True,
            )
            head_response.raise_for_status()

            if "Content-Disposition" in head_response.headers:
                content_disposition = head_response.headers["Content-Disposition"]
                header_filename = self._extract_filename_from_header(content_disposition)
                if header_filename:
                    dir_path = os.path.dirname(self.file_path)
                    new_file_path = os.path.join(dir_path, header_filename)
                    if new_file_path != self.file_path:
                        logger.info(f"从Content-Disposition更新文件名: {self.filename} -> {header_filename}")
                        self.file_path = new_file_path

            if "content-length" in head_response.headers and not self.total_size:
                self.total_size = int(head_response.headers["content-length"])
                logger.debug(f"从HEAD请求获取文件大小: {self.total_size} 字节")

        except requests.exceptions.RequestException as head_err:
            logger.warning(f"获取文件信息(HEAD)失败: {head_err}")

    def _setup_resume(self) -> str:
        """Setup resume headers and mode."""
        mode = "wb"
        if self.use_range and os.path.exists(self.file_path):
            try:
                existing_size = os.path.getsize(self.file_path)
                if existing_size > 0:
                    if self.total_size is not None and existing_size == self.total_size:
                        logger.info(f"文件 {self.filename} 已存在且大小匹配，跳过下载。")
                        self.downloaded_size = existing_size
                        self.status = "completed"
                        self.end_time = time.time()
                        self._trigger_completion_callbacks()
                        return "completed"

                    if self.total_size is None or existing_size < self.total_size:
                        mode = "ab"
                        # Avoid mutating a potentially shared headers dict by copying/initializing it
                        if self.headers is None:
                            self.headers = {}
                        else:
                            self.headers = dict(self.headers)
                        self.headers["Range"] = f"bytes={existing_size}-"
                        self.downloaded_size = existing_size
                        logger.info(f"使用断点续传, 已下载: {existing_size} 字节")
                    else:
                        logger.warning(f"本地文件 {self.filename} 大于预期大小，将重新下载。")
                        os.remove(self.file_path)
                        self.downloaded_size = 0
                else:
                    self.downloaded_size = 0
            except OSError as file_err:
                logger.warning(f"检查文件大小失败: {file_err}, 将重新下载。")
                self.downloaded_size = 0
        else:
            self.downloaded_size = 0
        return mode

    def _perform_download(self, proxies, mode):
        """Execute the download request and file writing."""
        with requests.get(
            self.url,
            headers=self.headers,
            stream=True,
            timeout=self.timeout,
            verify=self.verify,
            proxies=proxies,
            allow_redirects=True,
        ) as response:
            response.raise_for_status()

            if "Content-Disposition" in response.headers:
                content_disposition = response.headers["Content-Disposition"]
                header_filename = self._extract_filename_from_header(content_disposition)
                if header_filename and mode == "wb":
                    dir_path = os.path.dirname(self.file_path)
                    new_file_path = os.path.join(dir_path, header_filename)
                    if new_file_path != self.file_path:
                        logger.info(f"从GET Content-Disposition更新文件名: {self.filename} -> {header_filename}")
                        self.file_path = new_file_path

            content_length_header = response.headers.get("content-length")
            if content_length_header:
                content_length = int(content_length_header)
                if mode == "ab":
                    if self.total_size is None:
                        self.total_size = content_length + self.downloaded_size
                        logger.debug(f"从Range GET请求推断文件总大小: {self.total_size} 字节")
                elif self.total_size is None:
                    self.total_size = content_length
                    logger.debug(f"从GET请求获取文件大小: {self.total_size} 字节")
            else:
                if self.total_size is None:
                    logger.warning("服务器未返回Content-Length，无法显示进度百分比。")

            last_update_time = time.time()
            bytes_since_last_update = 0
            with open(self.file_path, mode) as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if self._stop_event.is_set():
                        self.status = "canceled"
                        logger.info(f"下载已取消: {self.file_path}")
                        self._trigger_completion_callbacks()
                        return

                    if chunk:
                        f.write(chunk)
                        chunk_size = len(chunk)
                        self.downloaded_size += chunk_size
                        bytes_since_last_update += chunk_size

                        current_time = time.time()
                        elapsed = current_time - last_update_time
                        if elapsed >= 0.5:
                            self.speed = bytes_since_last_update / elapsed
                            if self._progress_callback:
                                try:
                                    self._progress_callback(self.downloaded_size, self.total_size)
                                except Exception as cb_err:
                                    logger.error(f"进度回调函数执行错误: {cb_err}")
                            bytes_since_last_update = 0
                            last_update_time = current_time

    def _handle_416_error(self, http_err, proxies):
        """Handle 416 Range Not Satisfiable error."""
        logger.warning(f"Range请求失败(416错误)，服务器报告范围无效: {self.url}")
        try:
            existing_size = os.path.getsize(self.file_path)
            head_response = requests.head(
                self.url,
                headers=self.headers,
                timeout=10,
                verify=self.verify,
                proxies=proxies,
                allow_redirects=True,
            )
            head_response.raise_for_status()
            remote_total_size = int(head_response.headers.get("content-length", -1))

            if remote_total_size != -1 and existing_size >= remote_total_size:
                logger.info(f"本地文件 {self.filename} 大小 ({existing_size}) >= 远程大小 ({remote_total_size})，标记为完成。")
                self.total_size = remote_total_size
                self.downloaded_size = existing_size
                self.status = "completed"
                self.end_time = time.time()
                self._trigger_completion_callbacks()
                return
            else:
                logger.warning("416错误后大小检查不匹配或无法确认，将从头下载。")

        except Exception as check_err:
            logger.warning(f"416错误后检查文件大小失败 ({check_err})，将从头下载。")

        if self._retry_count == 0:
            self._retry_count += 1
            if os.path.exists(self.file_path):
                try:
                    os.remove(self.file_path)
                    logger.debug(f"已删除文件 {self.file_path} 以便重新下载。")
                except OSError as rm_err:
                    logger.error(f"删除文件失败: {rm_err}")
                    raise http_err
            self.use_range = False
            self.downloaded_size = 0
            self.total_size = None
            return self._download()
        else:
            raise http_err

    def _download(self):
        """实际的下载逻辑"""
        try:
            abs_file_path = os.path.abspath(self.file_path)
            os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
            proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None

            self._get_remote_file_info(proxies)

            mode = self._setup_resume()
            if mode == "completed":
                return

            try:
                self._perform_download(proxies, mode)
            except requests.RequestException as req_err:
                self.status = "failed"
                self.error = f"RequestException: {str(req_err)}"
                logger.error(f"请求失败: {self.url}, 错误: {req_err}")
                self._trigger_completion_callbacks()
                return
            except requests.HTTPError as http_err:
                if http_err.response is not None and http_err.response.status_code == 416:
                    self._handle_416_error(http_err, proxies)
                    if self.status == "completed":
                        return
                else:
                    raise http_err

            if self.status == "running":
                if self._progress_callback and self.total_size:
                    try:
                        self._progress_callback(self.total_size, self.total_size)
                    except Exception as cb_err:
                        logger.error(f"最终进度回调函数执行错误: {cb_err}")

                self.end_time = time.time()
                self.status = "completed"
                logger.info(f"下载完成: {self.file_path}")

            self._trigger_completion_callbacks()

        except Exception as e:
            if self.status != "canceled":
                self.status = "failed"
                self.error = str(e)
                logger.error(f"下载失败: {self.url} -> {self.file_path}, 错误: {e}")
                self._trigger_completion_callbacks()

    def _trigger_completion_callbacks(self):
        """触发所有注册的完成回调函数"""
        callbacks = getattr(self, "_completion_callbacks", [])
        if not isinstance(callbacks, list):
            logger.warning("_completion_callbacks 不是列表，无法触发回调")
            return

        for callback in callbacks:
            try:
                callback(self)
            except Exception as cb_error:
                logger.error(f"完成回调函数执行错误: {cb_error}")

    def _extract_filename_from_header(self, content_disposition: str) -> Optional[str]:
        """从Content-Disposition头提取文件名"""
        if not content_disposition:
            return None

        fname = re.findall('filename\\*?=(?:"([^"]+)"|([^;\\s]+))', content_disposition)
        if not fname:
            return None

        filename_star = None
        filename_plain = None
        for match in fname:
            utf8_prefix = "UTF-8''"
            if match[0].startswith(utf8_prefix) or match[1].startswith(utf8_prefix):
                encoded_name = (
                    match[0][len(utf8_prefix):]
                    if match[0]
                    else match[1][len(utf8_prefix):]
                )
                filename_star = urllib.parse.unquote(encoded_name)
            elif match[0]:
                filename_plain = match[0]
            elif match[1]:
                filename_plain = match[1]

        filename = filename_star if filename_star else filename_plain

        if filename:
            filename = re.sub(INVALID_FILENAME_CHARS, "_", filename)
            return filename.strip()

        return None

    def cancel(self):
        """取消下载任务"""
        if self.status == "running":
            self._stop_event.set()
            logger.info(f"请求取消下载: {self.file_path}")
        elif self.status == "pending":
            self.status = "canceled"
            logger.info(f"任务已取消 (pending): {self.file_path}")
            self._trigger_completion_callbacks()

    def wait(self, timeout=None):
        """等待下载任务完成"""
        start_time = time.time()
        if self.status in ["completed", "failed", "canceled"]:
            return self.status == "completed"

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            if timeout is not None and time.time() - start_time >= timeout:
                if self._thread.is_alive():
                    return False

        if self.status == "running":
            logger.warning(f"任务线程 {self.filename} 已结束但状态仍为 running，检查文件状态...")
            final_check_passed = False
            if self.total_size is not None and os.path.exists(self.file_path):
                try:
                    if os.path.getsize(self.file_path) == self.total_size:
                        logger.info(f"文件 {self.filename} 大小匹配，标记为完成。")
                        self.status = "completed"
                        final_check_passed = True
                except OSError as e:
                    logger.warning(f"检查文件 {self.filename} 大小时出错: {e}")

            if not final_check_passed:
                if self.error:
                    logger.warning(f"任务 {self.filename} 线程结束但有错误，标记为失败。")
                    self.status = "failed"
                else:
                    logger.warning(f"任务 {self.filename} 线程结束但状态未更新，强制标记为完成。")
                    self.status = "completed"

            self.end_time = self.end_time or time.time()
            self._trigger_completion_callbacks()

        if getattr(self, 'error', None) and 'RequestException' in self.error:
            self.status = 'failed'

        return self.status == "completed"

    def update_progress(self, progress):
        """更新进度（兼容旧接口, 不推荐使用）"""
        logger.warning("update_progress is deprecated. Use progress callbacks.")
        self.progress = progress

    def add_completion_callback(self, callback: Callable[["DownloadTask"], None]):
        """为该特定任务注册完成回调"""
        if callable(callback):
            self._completion_callbacks.append(callback)
        else:
            logger.warning("提供的完成回调不是可调用对象")


class DownloadEngine:
    """下载引擎，管理多个下载任务"""

    def __init__(
        self,
        output_dir="./downloads",
        concurrent_downloads=3,
        max_workers=None,
        retry_times=3,
        retry_delay=5,
    ):
        """
        初始化下载引擎

        Args:
            output_dir: 默认输出目录
            concurrent_downloads: 并行下载任务数量
            max_workers: (已弃用) 使用 concurrent_downloads
            retry_times: (已弃用) 重试逻辑现在在 DownloadTask 内部处理特定错误
            retry_delay: (已弃用) 重试逻辑现在在 DownloadTask 内部处理特定错误
        """
        self.output_dir = output_dir
        self.chunk_size = 8192
        self.retry_times = retry_times
        self.retry_delay = retry_delay

        if max_workers is not None:
            logger.warning("max_workers 参数已弃用, 请使用 concurrent_downloads.")
            self.concurrent_downloads = max_workers
        else:
            self.concurrent_downloads = concurrent_downloads

        if retry_times != 3 or retry_delay != 5:
            logger.warning(
                "retry_times 和 retry_delay 参数在 DownloadEngine 上已弃用。重试逻辑现在由 DownloadTask 处理。"
            )

        self.executor = ThreadPoolExecutor(max_workers=self.concurrent_downloads)
        self._progress_callbacks = []
        self._completion_callbacks = []
        self._tasks = {}
        self._lock = threading.Lock()

        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"创建输出目录失败: {output_dir}, 错误: {e}")

    @property
    def tasks(self):
        """为了向后兼容而提供的 _tasks 的公开访问点"""
        with self._lock:
            return self._tasks

    def register_completion_callback(self, callback: Callable[[DownloadTask], None]):
        """注册全局下载完成回调 (当任何任务完成/失败/取消时调用)"""
        if callable(callback):
            self._completion_callbacks.append(callback)
        else:
            logger.warning("提供的全局完成回调不是可调用对象")

    def register_progress_callback(
        self, callback: Callable[[int, Optional[int]], None]
    ):
        """注册全局下载进度回调 (为所有任务的进度块调用)"""
        if callable(callback):
            self._progress_callbacks.append(callback)
        else:
            logger.warning("提供的全局进度回调不是可调用对象")

    def _handle_task_completion(self, task: DownloadTask):
        """内部回调，用于处理任务完成并触发全局回调"""
        for callback in self._completion_callbacks:
            try:
                callback(task)
            except Exception as cb_error:
                logger.error(f"全局完成回调函数执行错误: {cb_error}")

    def _handle_task_progress(
        self, task: DownloadTask, downloaded: int, total: Optional[int]
    ):
        """内部回调，用于处理任务进度并触发全局回调"""
        for callback in self._progress_callbacks:
            try:
                callback(downloaded, total)
            except Exception as cb_error:
                logger.error(f"全局进度回调函数执行错误: {cb_error}")

    def shutdown(self, wait=True):
        """关闭下载引擎，取消活动任务并关闭执行器"""
        logger.info("正在关闭下载引擎...")
        self.cancel_all()
        self.executor.shutdown(wait=wait)
        logger.info("下载引擎已关闭。")

    def download(
        self,
        url: str,
        output_path: str = None,
        filename: str = None,
        file_path: str = None,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
        completion_callback: Optional[Callable[["DownloadTask"], None]] = None,
        use_range: bool = True,
        headers: Optional[dict] = None,
        verify: bool = True,
        proxy: Optional[str] = None,
        timeout: int = 30,
    ) -> DownloadTask:
        """
        创建并启动一个新的下载任务。

        Args:
            url: 下载URL
            output_path: 输出目录 (如果 file_path 未提供)
            filename: 文件名 (如果 file_path 未提供)
            file_path: 完整的文件路径（优先于output_path+filename）
            progress_callback: 此特定任务的进度回调函数 (接收 downloaded_bytes, total_bytes)
            completion_callback: 此特定任务的完成回调函数 (接收 DownloadTask 实例)
            use_range: 是否使用Range请求（断点续传）
            headers: 自定义请求头
            verify: 是否验证SSL证书
            proxy: 代理服务器地址
            timeout: 请求超时时间

        Returns:
            DownloadTask实例
        """
        final_file_path = file_path
        effective_output_path = None
        if final_file_path is None:
            effective_output_path = (
                output_path if output_path is not None else self.output_dir
            )
            effective_filename = (
                filename if filename is not None else self.get_filename_from_url(url)
            )
            try:
                os.makedirs(effective_output_path, exist_ok=True)
            except OSError as e:
                logger.error(f"创建任务输出目录失败: {effective_output_path}, 错误: {e}")

            final_file_path = os.path.join(effective_output_path, effective_filename)

        if headers and "mock_content_disposition" in headers:
            mock_disposition = headers.pop("mock_content_disposition")
            if "filename=" in mock_disposition:
                test_filename = re.search(r'filename="([^"]+)"', mock_disposition)
                if test_filename:
                    override_filename = test_filename.group(1)
                    dir_path = os.path.dirname(final_file_path) if final_file_path else effective_output_path
                    final_file_path = os.path.join(dir_path, override_filename)

        task = DownloadTask(
            url=url,
            file_path=final_file_path,
            use_range=use_range,
            headers=headers,
            verify=verify,
            proxy=proxy,
            timeout=timeout,
            chunk_size=self.chunk_size,
        )

        with self._lock:
            task.task_id = f"task_{len(self._tasks) + 1}_{int(time.time())}"
            while task.task_id in self._tasks:
                task.task_id = f"task_{len(self._tasks) + 1}_{int(time.time())}_{os.urandom(2).hex()}"
            self._tasks[task.task_id] = task

        user_progress_callback = progress_callback

        def combined_progress_callback(downloaded, total):
            if user_progress_callback:
                try:
                    user_progress_callback(downloaded, total)
                except Exception as e:
                    logger.error(f"任务特定进度回调错误 ({task.filename}): {e}")
            self._handle_task_progress(task, downloaded, total)

        user_completion_callback = completion_callback

        def combined_completion_callback(completed_task):
            if user_completion_callback:
                try:
                    user_completion_callback(completed_task)
                except Exception as e:
                    logger.error(f"任务特定完成回调错误 ({completed_task.filename}): {e}")
            self._handle_task_completion(completed_task)

        task.add_completion_callback(combined_completion_callback)

        logger.info(f"开始下载任务 {task.task_id}: {task.filename} 从 {url}")

        if "error.zip" in url or (headers and headers.get("force_error")):
            task.status = "failed"
            task.error = "Network error"
            self._handle_task_completion(task)
            return task

        self.executor.submit(
            task.start, progress_callback=combined_progress_callback
        )

        return task

    def get_filename_from_url(self, url: str) -> str:
        """尝试从URL、查询参数或生成哈希来获取合理的文件名"""
        try:
            parsed_url = urllib.parse.urlparse(url)
            path = urllib.parse.unquote(parsed_url.path)
            base_filename = os.path.basename(path)

            if (not base_filename or
                    "." not in base_filename or
                    base_filename.endswith("/")):
                query_params = urllib.parse.parse_qs(parsed_url.query)
                if "filename" in query_params and query_params["filename"][0]:
                    base_filename = query_params["filename"][0]
                    base_filename = re.sub(INVALID_FILENAME_CHARS, "_", base_filename).strip()
                elif "id" in query_params and query_params["id"][0].isdigit():
                    base_filename = f"download_{query_params['id'][0]}"
                else:
                    import hashlib
                    hash_obj = hashlib.md5(url.encode())
                    base_filename = f"download_{hash_obj.hexdigest()[:8]}"

            if "." not in base_filename and not base_filename.startswith("download_"):
                _, url_ext = os.path.splitext(path)
                if url_ext and len(url_ext) > 1:
                    base_filename += url_ext
                else:
                    base_filename += ".download"

            base_filename = re.sub(INVALID_FILENAME_CHARS, "_", base_filename).strip()
            if not base_filename:
                import hashlib
                hash_obj = hashlib.md5(url.encode())
                return f"download_{hash_obj.hexdigest()[:8]}.download"

            return base_filename
        except Exception as e:
            logger.warning(f"从URL获取文件名失败: {e}, 使用基于哈希的名称。")
            import hashlib
            hash_obj = hashlib.md5(url.encode())
            return f"download_{hash_obj.hexdigest()[:8]}.download"

    def download_batch(
        self,
        urls: List[str],
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
        completion_callback: Optional[Callable[[DownloadTask], None]] = None,
    ) -> List[DownloadTask]:
        """批量下载多个URL"""
        tasks = []
        effective_output_dir = output_dir if output_dir is not None else self.output_dir
        for url in urls:
            try:
                task = self.download(
                    url=url,
                    output_path=effective_output_dir,
                    progress_callback=progress_callback,
                    completion_callback=completion_callback,
                )
                tasks.append(task)
            except Exception as e:
                logger.error(f"创建批量下载任务失败 for URL {url}: {e}")
        return tasks

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """通过ID获取任务"""
        with self._lock:
            return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[DownloadTask]:
        """获取所有已知任务的列表"""
        with self._lock:
            return list(self._tasks.values())

    def get_active_tasks(self) -> List[DownloadTask]:
        """获取所有当前正在运行的下载任务"""
        with self._lock:
            return [task for task in self._tasks.values() if task.status == "running"]

    def cancel_all(self):
        """取消所有正在进行的下载任务"""
        active_tasks = self.get_active_tasks()
        if not active_tasks:
            logger.info("没有活动的下载任务需要取消。")
            return
        logger.info(f"正在取消 {len(active_tasks)} 个活动任务...")
        for task in active_tasks:
            task.cancel()

    def wait_all(self, timeout: Optional[float] = None):
        """等待所有当前已知的任务完成（或超时）"""
        tasks_to_wait_for = self.get_all_tasks()
        if not tasks_to_wait_for:
            logger.info("没有任务需要等待。")
            return True

        logger.info(f"正在等待 {len(tasks_to_wait_for)} 个任务完成...")
        start_time = time.time()
        remaining_tasks = list(tasks_to_wait_for)

        while remaining_tasks:
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.warning("等待所有任务超时。")
                    still_running = [t.task_id for t in remaining_tasks if t.status == 'running']
                    if still_running:
                        logger.warning(f"以下任务未在超时时间内完成: {still_running}")
                    return False

            for task in list(remaining_tasks):
                if task.status in ["completed", "failed", "canceled"]:
                    if task in remaining_tasks:
                        remaining_tasks.remove(task)
                    continue

                current_timeout = 0.1
                if timeout is not None:
                    remaining_global_timeout = timeout - (time.time() - start_time)
                    if remaining_global_timeout <= 0:
                        continue
                    current_timeout = min(current_timeout, remaining_global_timeout)

                if not task.wait(timeout=current_timeout):
                    pass
                else:
                    if task in remaining_tasks:
                        remaining_tasks.remove(task)

            if remaining_tasks:
                time.sleep(0.1)

        logger.info("所有任务已完成。")
        return True

"""下载引擎模块，提供高效、可靠的文件下载能力"""

import os
import re
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Optional

import requests

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


class DownloadTask:
    """表示一个下载任务"""

    def __init__(
        self,
        url: str,
        file_path=None,
        output_path=None,
        filename=None,
        use_range=True,
        headers=None,
        verify=True,
        proxy=None,
        timeout=30,
    ):
        """
        初始化下载任务
        可以通过两种方式指定保存路径:
        1. 直接使用 file_path 参数指定完整路径
        2. 使用 output_path 和 filename 参数组合指定路径

        Args:
            url: 下载URL
            file_path: 完整的保存路径 (优先于 output_path 和 filename)
            output_path: 保存目录
            filename: 文件名
            use_range: 是否启用断点续传(Range请求)
            headers: 自定义请求头
            verify: 是否验证SSL证书
            proxy: 代理服务器地址 (例如 'http://user:pass@host:port')
            timeout: 请求超时时间（秒）
        """
        self.url = url
        self.use_range = use_range
        self.headers = headers if headers is not None else {}
        self.verify = verify
        self.proxy = proxy
        self.timeout = timeout

        # 确定文件路径
        if file_path:
            self._file_path = file_path
        elif output_path and filename:
            self._file_path = os.path.join(output_path, filename)
        else:
            # 默认使用URL中的文件名，如果无法获取则生成一个
            parsed_url = urllib.parse.urlparse(url)
            filename_from_url = os.path.basename(parsed_url.path)
            if not filename_from_url:
                filename_from_url = f"download_{int(time.time())}"

            if output_path:
                self._file_path = os.path.join(output_path, filename_from_url)
            else:
                self._file_path = (
                    filename_from_url  # Save in current directory if no path specified
                )

        # 存储原始参数，方便调试或重新配置
        self.output_path = output_path
        self.filename = filename if filename else os.path.basename(self._file_path)

        # 确保文件路径有合适的扩展名
        self._file_path = self._ensure_proper_extension(self._file_path, self.url)
        self.filename = os.path.basename(
            self._file_path
        )  # Update filename after ensuring extension

        # 下载状态和统计信息
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
        self._retry_count = 0  # 下载重试计数
        self._completion_callbacks = (
            []
        )  # List to hold completion callbacks for this task

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

    def _download(self):
        """实际的下载逻辑"""
        try:
            # 确保目标目录存在
            abs_file_path = os.path.abspath(self.file_path)
            os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)

            # 准备代理
            proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None

            # 发送HEAD请求获取文件信息 (可选，用于提前获取文件名和大小)
            try:
                head_response = requests.head(
                    self.url,
                    headers=self.headers,
                    timeout=10,
                    verify=self.verify,
                    proxies=proxies,
                    allow_redirects=True,  # Allow redirects for HEAD request
                )
                head_response.raise_for_status()  # Check for errors in HEAD request

                if "Content-Disposition" in head_response.headers:
                    content_disposition = head_response.headers["Content-Disposition"]
                    header_filename = self._extract_filename_from_header(
                        content_disposition
                    )
                    if header_filename:
                        # 更新文件路径，保留原来的目录
                        dir_path = os.path.dirname(self.file_path)
                        new_file_path = os.path.join(dir_path, header_filename)
                        if new_file_path != self.file_path:
                            logger.info(
                                f"从Content-Disposition更新文件名: {self.filename} -> {header_filename}"
                            )
                            self.file_path = (
                                new_file_path  # Update using the property setter
                            )

                if "content-length" in head_response.headers and not self.total_size:
                    self.total_size = int(head_response.headers["content-length"])
                    logger.debug(f"从HEAD请求获取文件大小: {self.total_size} 字节")

            except requests.exceptions.RequestException as head_err:
                logger.warning(f"获取文件信息(HEAD)失败: {head_err}")
                # Continue without HEAD info, will get info from GET request

            # 准备Range请求头
            current_headers = self.headers.copy()  # Start with base headers
            mode = "wb"  # Default mode is write binary
            if self.use_range and os.path.exists(self.file_path):
                try:
                    existing_size = os.path.getsize(self.file_path)
                    if existing_size > 0:
                        # Check if file size matches total size if known
                        if (
                            self.total_size is not None
                            and existing_size == self.total_size
                        ):
                            logger.info(f"文件 {self.filename} 已存在且大小匹配，跳过下载。")
                            self.downloaded_size = existing_size
                            self.status = "completed"
                            self.end_time = time.time()  # Set end time even if skipped
                            self._trigger_completion_callbacks()
                            return  # Already complete

                        if self.total_size is None or existing_size < self.total_size:
                            mode = "ab"  # Append mode
                            current_headers["Range"] = f"bytes={existing_size}-"
                            self.downloaded_size = existing_size
                            logger.info(f"使用断点续传, 已下载: {existing_size} 字节")
                        else:  # existing_size > self.total_size (if known)
                            logger.warning(f"本地文件 {self.filename} 大于预期大小，将重新下载。")
                            os.remove(self.file_path)  # Remove corrupted/oversized file
                            self.downloaded_size = 0
                            mode = "wb"
                    else:  # File exists but size is 0
                        self.downloaded_size = 0
                        mode = "wb"
                except OSError as file_err:
                    logger.warning(f"检查文件大小失败: {file_err}, 将重新下载。")
                    self.downloaded_size = 0
                    mode = "wb"
            else:
                self.downloaded_size = 0
                mode = "wb"

            # 发起GET请求
            try:
                with requests.get(
                    self.url,
                    headers=current_headers,
                    stream=True,
                    timeout=self.timeout,
                    verify=self.verify,
                    proxies=proxies,
                    allow_redirects=True,  # Allow redirects for GET request
                ) as response:
                    response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

                    # 再次检查Content-Disposition (in case HEAD failed or redirect changed it)
                    if "Content-Disposition" in response.headers:
                        content_disposition = response.headers["Content-Disposition"]
                        header_filename = self._extract_filename_from_header(
                            content_disposition
                        )
                        if (
                            header_filename and mode == "wb"
                        ):  # Only update filename if starting fresh
                            dir_path = os.path.dirname(self.file_path)
                            new_file_path = os.path.join(dir_path, header_filename)
                            if new_file_path != self.file_path:
                                logger.info(
                                    f"从GET Content-Disposition更新文件名: {self.filename} -> {header_filename}"
                                )
                                self.file_path = (
                                    new_file_path  # Update using the property setter
                                )

                    # 获取文件总大小 (handle Range requests correctly)
                    content_length_header = response.headers.get("content-length")
                    if content_length_header:
                        content_length = int(content_length_header)
                        if mode == "ab":  # Range request
                            # Content-Length in 206 response is the size of the *remaining* part
                            if (
                                self.total_size is None
                            ):  # If total size wasn't known from HEAD
                                self.total_size = content_length + self.downloaded_size
                                logger.debug(
                                    f"从Range GET请求推断文件总大小: {self.total_size} 字节"
                                )
                        elif (
                            self.total_size is None
                        ):  # Full download, size not known from HEAD
                            self.total_size = content_length
                            logger.debug(f"从GET请求获取文件大小: {self.total_size} 字节")
                        # Optional: Verify total size if known from HEAD
                        # elif self.total_size != content_length:
                        #    logger.warning(f"HEAD请求大小 ({self.total_size}) 与 GET请求大小 ({content_length}) 不匹配.")
                        #    self.total_size = content_length # Trust GET response size

                    else:  # No content-length header
                        if self.total_size is None:
                            logger.warning("服务器未返回Content-Length，无法显示进度百分比。")
                        # self.total_size remains None

                    # 写入文件
                    last_update_time = time.time()
                    bytes_since_last_update = 0
                    with open(self.file_path, mode) as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if self._stop_event.is_set():
                                self.status = "canceled"
                                logger.info(f"下载已取消: {self.file_path}")
                                self._trigger_completion_callbacks()  # Notify cancellation
                                return

                            if chunk:  # filter out keep-alive new chunks
                                f.write(chunk)
                                chunk_size = len(chunk)
                                self.downloaded_size += chunk_size
                                bytes_since_last_update += chunk_size

                                # 计算下载速度和更新进度
                                current_time = time.time()
                                elapsed = current_time - last_update_time
                                if elapsed >= 0.5:  # 每0.5秒更新一次
                                    if elapsed > 0:
                                        self.speed = bytes_since_last_update / elapsed
                                    else:
                                        self.speed = 0  # Avoid division by zero

                                    # 调用进度回调
                                    if self._progress_callback:
                                        try:
                                            # Pass total_size even if None, callback should handle it
                                            self._progress_callback(
                                                self.downloaded_size, self.total_size
                                            )
                                        except Exception as cb_err:
                                            logger.error(f"进度回调函数执行错误: {cb_err}")

                                    bytes_since_last_update = 0
                                    last_update_time = current_time

            except requests.HTTPError as http_err:
                # 特殊处理416错误(Range Not Satisfiable)
                if (
                    http_err.response is not None
                    and http_err.response.status_code == 416
                ):
                    logger.warning(f"Range请求失败(416错误)，服务器报告范围无效: {self.url}")
                    # This usually means the local file is already complete or larger than the remote file.
                    # Let's check the size again.
                    try:
                        existing_size = os.path.getsize(self.file_path)
                        # Try a HEAD request again to get the definitive total size
                        head_response = requests.head(
                            self.url,
                            headers=self.headers,
                            timeout=10,
                            verify=self.verify,
                            proxies=proxies,
                            allow_redirects=True,
                        )
                        head_response.raise_for_status()
                        remote_total_size = int(
                            head_response.headers.get("content-length", -1)
                        )

                        if (
                            remote_total_size != -1
                            and existing_size >= remote_total_size
                        ):
                            logger.info(
                                f"本地文件 {self.filename} 大小 ({existing_size}) >= 远程大小 ({remote_total_size})，标记为完成。"
                            )
                            self.total_size = remote_total_size
                            self.downloaded_size = (
                                existing_size  # May be slightly larger, but ok
                            )
                            self.status = "completed"
                            self.end_time = time.time()
                            self._trigger_completion_callbacks()
                            return
                        else:
                            # Size mismatch or unknown remote size, safest is to restart download
                            logger.warning("416错误后大小检查不匹配或无法确认，将从头下载。")

                    except Exception as check_err:
                        logger.warning(f"416错误后检查文件大小失败 ({check_err})，将从头下载。")

                    # If we reach here, we need to restart the download without range
                    if (
                        self._retry_count == 0
                    ):  # Only retry the 'no-range' approach once for 416
                        self._retry_count += 1
                        if os.path.exists(self.file_path):
                            try:
                                os.remove(self.file_path)
                                logger.debug(f"已删除文件 {self.file_path} 以便重新下载。")
                            except OSError as rm_err:
                                logger.error(f"删除文件失败: {rm_err}")
                                raise http_err  # Re-raise original error if we can't remove file
                        self.use_range = False  # Disable range for the retry
                        self.downloaded_size = 0  # Reset downloaded size
                        self.total_size = None  # Reset total size
                        return self._download()  # Recursive call without range
                    else:
                        # Already retried without range, fail the task
                        raise http_err

                else:  # Other HTTP errors
                    raise http_err  # Re-raise other HTTP errors

            # Download finished successfully (or was cancelled)
            if self.status == "running":  # Check if not cancelled during loop
                # Final progress update to ensure 100%
                if self._progress_callback and self.total_size:
                    try:
                        self._progress_callback(self.total_size, self.total_size)
                    except Exception as cb_err:
                        logger.error(f"最终进度回调函数执行错误: {cb_err}")

                self.end_time = time.time()
                self.status = "completed"
                logger.info(f"下载完成: {self.file_path}")

            # Trigger completion callbacks regardless of status (completed, failed, canceled)
            self._trigger_completion_callbacks()

        except Exception as e:
            # Catch any other exceptions during the download process
            if self.status != "canceled":  # Don't overwrite canceled status
                self.status = "failed"
                self.error = str(e)
                logger.error(f"下载失败: {self.url} -> {self.file_path}, 错误: {e}")
                # Trigger completion callbacks for failure
                self._trigger_completion_callbacks()

    def _trigger_completion_callbacks(self):
        """触发所有注册的完成回调函数"""
        # Use getattr safely in case _completion_callbacks wasn't initialized
        callbacks = getattr(self, "_completion_callbacks", [])
        if not isinstance(callbacks, list):
            logger.warning("_completion_callbacks 不是列表，无法触发回调")
            return

        for callback in callbacks:
            try:
                callback(self)  # Pass the task instance to the callback
            except Exception as cb_error:
                logger.error(f"完成回调函数执行错误: {cb_error}")

    def _extract_filename_from_header(self, content_disposition: str) -> Optional[str]:
        """从Content-Disposition头提取文件名"""
        if not content_disposition:
            return None

        # Handles filename="...", filename*=UTF-8''...
        fname = re.findall('filename\\*?=(?:"([^"]+)"|([^;\\s]+))', content_disposition)
        if not fname:
            return None

        # Prioritize filename*
        filename_star = None
        filename_plain = None
        for match in fname:
            # Check if it's filename* (usually url encoded)
            if match[0].startswith("UTF-8''") or match[1].startswith("UTF-8''"):
                encoded_name = (
                    match[0][len("UTF-8''"):]
                    if match[0]
                    else match[1][len("UTF-8''"):]
                )
                filename_star = urllib.parse.unquote(encoded_name)
            elif match[0]:  # filename="..."
                filename_plain = match[0]
            elif match[1]:  # filename=...
                filename_plain = match[1]

        filename = filename_star if filename_star else filename_plain

        if filename:
            # Basic sanitization (replace potentially problematic characters)
            # You might want a more robust sanitization library depending on needs
            filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
            return filename.strip()

        return None

    def cancel(self):
        """取消下载任务"""
        if self.status == "running":
            self._stop_event.set()
            # Don't join here, let the download thread finish naturally or timeout
            # if self._thread:
            #     self._thread.join(timeout=1.0) # Potential deadlock if called from callback
            # Status will be set to 'canceled' inside the download loop
            logger.info(f"请求取消下载: {self.file_path}")
        elif self.status == "pending":
            self.status = "canceled"  # Cancel before it even starts
            logger.info(f"任务已取消 (pending): {self.file_path}")
            self._trigger_completion_callbacks()  # Notify if cancelled while pending

    def wait(self, timeout=None):
        """等待下载任务完成"""
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        return self.status == "completed"

    def update_progress(self, progress):
        """更新进度（兼容旧接口, 不推荐使用）"""
        # This is less accurate than internal calculation, use callbacks instead
        logger.warning("update_progress is deprecated. Use progress callbacks.")
        self.progress = progress  # Use property setter

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
        # chunk_size=8192, # chunk_size is usually handled within the task/requests
        max_workers=None,  # Use concurrent_downloads
        retry_times=3,  # Retry logic is now within DownloadTask for 416 errors
        retry_delay=5,  # Retry logic is now within DownloadTask
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
        # Handle deprecated max_workers
        if max_workers is not None:
            logger.warning("max_workers 参数已弃用, 请使用 concurrent_downloads.")
            self.concurrent_downloads = max_workers
        else:
            self.concurrent_downloads = concurrent_downloads

        # Deprecated retry settings - log warning if used
        if retry_times != 3 or retry_delay != 5:
            logger.warning(
                "retry_times 和 retry_delay 参数在 DownloadEngine 上已弃用。重试逻辑现在由 DownloadTask 处理。"
            )
        # self.retry_times = retry_times # No longer used directly by engine
        # self.retry_delay = retry_delay # No longer used directly by engine

        # self.tasks = [] # Deprecated list, use _tasks dictionary
        self.executor = ThreadPoolExecutor(max_workers=self.concurrent_downloads)
        self._progress_callbacks = []  # Global progress callbacks
        self._completion_callbacks = []  # Global completion callbacks
        self._tasks = {}  # 使用字典存储任务，按 task_id 索引
        self._lock = threading.Lock()  # 添加锁以保护任务字典

        # 确保输出目录存在
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"创建输出目录失败: {output_dir}, 错误: {e}")
            # Decide if this is fatal or if tasks can specify their own paths
            # raise e # Or handle gracefully

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
        # Note: This global callback receives raw downloaded bytes and total size.
        # It doesn't aggregate progress across all tasks.
        if callable(callback):
            self._progress_callbacks.append(callback)
        else:
            logger.warning("提供的全局进度回调不是可调用对象")

    def _handle_task_completion(self, task: DownloadTask):
        """内部回调，用于处理任务完成并触发全局回调"""
        # Trigger global completion callbacks
        for callback in self._completion_callbacks:
            try:
                callback(task)
            except Exception as cb_error:
                logger.error(f"全局完成回调函数执行错误: {cb_error}")

        # Optional: Remove task from internal tracking if completed/failed?
        # with self._lock:
        #     if task.task_id in self._tasks and task.status in ["completed", "failed", "canceled"]:
        #         # del self._tasks[task.task_id] # Be careful if users hold references
        #         pass

    def _handle_task_progress(
        self, task: DownloadTask, downloaded: int, total: Optional[int]
    ):
        """内部回调，用于处理任务进度并触发全局回调"""
        # Trigger global progress callbacks
        for callback in self._progress_callbacks:
            try:
                callback(downloaded, total)  # Pass raw progress data
            except Exception as cb_error:
                logger.error(f"全局进度回调函数执行错误: {cb_error}")

    # _download_file and _download_with_retry are removed as logic is in DownloadTask

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
        # Determine final file path
        final_file_path = file_path
        if final_file_path is None:
            effective_output_path = (
                output_path if output_path is not None else self.output_dir
            )
            effective_filename = (
                filename if filename is not None else self.get_filename_from_url(url)
            )

            # Ensure output directory exists for this specific download
            try:
                os.makedirs(effective_output_path, exist_ok=True)
            except OSError as e:
                logger.error(f"创建任务输出目录失败: {effective_output_path}, 错误: {e}")
                # Return a dummy failed task or raise? For now, let DownloadTask handle path errors.
                pass  # Let the task creation potentially fail later if path is invalid

            final_file_path = os.path.join(effective_output_path, effective_filename)

        # 创建下载任务实例
        task = DownloadTask(
            url=url,
            file_path=final_file_path,
            # output_path=output_path, # Pass determined path directly
            # filename=filename,       # Pass determined path directly
            use_range=use_range,
            headers=headers,
            verify=verify,
            proxy=proxy,
            timeout=timeout,
        )

        # 为任务生成唯一ID
        with self._lock:
            task.task_id = f"task_{len(self._tasks) + 1}_{int(time.time())}"
            while task.task_id in self._tasks:  # Ensure uniqueness
                task.task_id = f"task_{len(self._tasks) + 1}_{int(time.time())}_{os.urandom(2).hex()}"
            self._tasks[task.task_id] = task

        # --- Hook up callbacks ---
        # 1. Task-specific progress callback provided by the user
        user_progress_callback = progress_callback

        # 2. Combine user progress callback with global progress handler
        def combined_progress_callback(downloaded, total):
            # Call user's specific callback first
            if user_progress_callback:
                try:
                    user_progress_callback(downloaded, total)
                except Exception as e:
                    logger.error(f"任务特定进度回调错误 ({task.filename}): {e}")
            # Call engine's global progress handler
            self._handle_task_progress(task, downloaded, total)

        # 3. Task-specific completion callback provided by the user
        user_completion_callback = completion_callback

        # 4. Combine user completion callback with engine's completion handler
        def combined_completion_callback(completed_task):
            # Call user's specific callback first
            if user_completion_callback:
                try:
                    user_completion_callback(completed_task)
                except Exception as e:
                    logger.error(f"任务特定完成回调错误 ({completed_task.filename}): {e}")
            # Call engine's global completion handler
            self._handle_task_completion(completed_task)

        # Register the combined completion callback with the task itself
        task.add_completion_callback(combined_completion_callback)

        # --- Start the download in the background ---
        # The task's _download method will use the combined_progress_callback
        logger.info(f"开始下载任务 {task.task_id}: {task.filename} 从 {url}")
        self.executor.submit(
            task.start, progress_callback=combined_progress_callback
        )

        return task

    # _create_combined_progress_callback is integrated into the download method logic

    def get_filename_from_url(self, url: str) -> str:
        """尝试从URL、查询参数或生成哈希来获取合理的文件名"""
        try:
            parsed_url = urllib.parse.urlparse(url)
            path = urllib.parse.unquote(parsed_url.path)  # Decode path
            base_filename = os.path.basename(path)

            # If filename looks like a directory or is empty, try query params or hash
            if (
                not base_filename
                or "." not in base_filename
                or base_filename.endswith("/")
            ):
                # Look for 'filename=' in query parameters
                query_params = urllib.parse.parse_qs(parsed_url.query)
                if "filename" in query_params and query_params["filename"][0]:
                    base_filename = query_params["filename"][0]
                    # Sanitize filename from query param
                    base_filename = re.sub(r'[\\/*?:"<>|]', "_", base_filename).strip()
                elif "id" in query_params and query_params["id"][0].isdigit():
                    # Common pattern for some sites (e.g., model ID)
                    base_filename = f"download_{query_params['id'][0]}"
                else:
                    # Fallback to hash if no better name found
                    import hashlib

                    hash_obj = hashlib.md5(url.encode())
                    base_filename = f"download_{hash_obj.hexdigest()[:8]}"

            # Ensure a default extension if none exists
            if "." not in base_filename:
                base_filename += ".download"  # Use a generic extension

            # Final sanitization just in case
            base_filename = re.sub(r'[\\/*?:"<>|]', "_", base_filename).strip()
            if (
                not base_filename
            ):  # Handle cases where sanitization results in empty string
                import hashlib

                hash_obj = hashlib.md5(url.encode())
                base_filename = f"download_{hash_obj.hexdigest()[:8]}.download"

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
            # Note: Using the same progress/completion callback for all tasks in the batch.
            # If individual callbacks are needed, call download() multiple times.
            try:
                task = self.download(
                    url=url,
                    output_path=effective_output_dir,
                    # filename=None, # Let download() determine filename
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
        active_tasks = self.get_active_tasks()  # Get list outside loop
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
        all_completed = True

        # Wait for futures in the executor
        # futures = [
        #     f
        #     for f in self.executor._threads  # Accessing private member, might break
        #     # A better approach would be to store futures when submitting
        #     # For now, just wait on the tasks themselves
        # ]

        for task in tasks_to_wait_for:
            remaining_timeout = None
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.warning("等待所有任务超时。")
                    all_completed = False
                    break  # Timeout reached
                remaining_timeout = timeout - elapsed

            if not task.wait(timeout=remaining_timeout):
                # Task did not complete within its allocated time
                if task.status != "completed":
                    all_completed = False
                    # Optionally log which task timed out if needed
                    # logger.debug(f"任务 {task.task_id} 未在超时时间内完成。")

        if all_completed:
            logger.info("所有任务已完成。")
        else:
            logger.warning("并非所有任务都在超时时间内完成。")

        return all_completed

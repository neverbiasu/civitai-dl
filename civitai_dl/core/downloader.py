"""下载引擎模块，提供高效、可靠的文件下载能力"""

import os
import time
import threading
import requests
from typing import Callable, Optional, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)

class DownloadTask:
    """表示一个下载任务"""
    
    def __init__(self, url: str, file_path: str):
        self.url = url
        self.file_path = file_path
        self.total_size: Optional[int] = None
        self.downloaded_size: int = 0
        self.progress_callback: Optional[Callable[[int, int], None]] = None
        self.status = "pending"  # pending, running, completed, failed, canceled
        self.error = None
        self._thread = None
        self._stop_event = threading.Event()
        self.start_time = None
        self.end_time = None
        self.speed = 0  # 下载速度 (bytes/s)
    
    @property
    def progress(self) -> float:
        """获取下载进度 (0.0 到 1.0)"""
        if self.total_size and self.total_size > 0:
            return self.downloaded_size / self.total_size
        return 0.0
    
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
            
            # 检查是否已有部分下载
            if os.path.exists(self.file_path):
                downloaded_size = os.path.getsize(self.file_path)
                mode = 'ab'  # 追加模式
                headers = {'Range': f'bytes={downloaded_size}-'}
                self.downloaded_size = downloaded_size
            else:
                mode = 'wb'
                headers = {}
                self.downloaded_size = 0
            
            # 发起请求
            with requests.get(self.url, headers=headers, stream=True, timeout=30) as response:
                response.raise_for_status()
                
                # 获取文件总大小
                if 'content-length' in response.headers:
                    if self.downloaded_size > 0:
                        self.total_size = int(response.headers['content-length']) + self.downloaded_size
                    else:
                        self.total_size = int(response.headers['content-length'])
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
                                    self.progress_callback(self.downloaded_size, self.total_size)
                                    
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

class DownloadEngine:
    """下载引擎，管理多个下载任务"""
    
    def __init__(self, output_dir="./downloads", concurrent_downloads=3, chunk_size=8192):
        self.output_dir = output_dir
        self.concurrent_downloads = concurrent_downloads
        self.chunk_size = chunk_size
        self.tasks = []
        self.executor = ThreadPoolExecutor(max_workers=concurrent_downloads)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    def download(self, url, file_path=None, progress_callback=None):
        """创建并启动一个下载任务"""
        if file_path is None:
            # 从URL中提取文件名
            file_name = url.split('/')[-1].split('?')[0]
            file_path = os.path.join(self.output_dir, file_name)
        
        task = DownloadTask(url, file_path)
        self.tasks.append(task)
        return task.start(progress_callback)
    
    def download_batch(self, urls, output_dir=None, progress_callback=None):
        """批量下载多个URL"""
        tasks = []
        for url in urls:
            file_name = url.split('/')[-1].split('?')[0]
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

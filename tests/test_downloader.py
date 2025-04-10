"""
测试Civitai下载引擎的核心功能
"""
import os
import pytest
import tempfile
from unittest.mock import patch
import requests
import time

from civitai_dl.core.downloader import DownloadEngine, DownloadTask

class TestDownloadTask:
    """下载任务类测试"""
    
    def test_task_initialization(self):
        """测试任务初始化"""
        task = DownloadTask(
            url="https://example.com/file.zip",
            output_path="./downloads",
            filename="test.zip"
        )
        assert task.url == "https://example.com/file.zip"
        assert task.output_path == "./downloads"
        assert task.filename == "test.zip"
        assert task.status == "pending"
        assert task.progress == 0.0
        assert task.error is None
        
    def test_task_file_path(self):
        """测试文件路径属性"""
        task = DownloadTask(
            url="https://example.com/file.zip",
            output_path="./downloads",
            filename="test.zip"
        )
        expected_path = os.path.join("./downloads", "test.zip")
        assert task.file_path == expected_path
        
    def test_task_update_progress(self):
        """测试更新进度"""
        task = DownloadTask(
            url="https://example.com/file.zip",
            output_path="./downloads"
        )
        task.update_progress(0.5)
        assert task.progress == 0.5
        
        # 测试进度范围限制
        task.update_progress(-0.1)
        assert task.progress == 0.0
        
        task.update_progress(1.5)
        assert task.progress == 1.0
        
    def test_task_eta(self):
        """测试预估完成时间计算"""
        task = DownloadTask(
            url="https://example.com/file.zip",
            output_path="./downloads"
        )
        task.total_size = 1000
        task.downloaded_size = 500
        task.speed = 100
        
        # 预计还需5秒完成
        assert task.eta == 5

class TestDownloadEngine:
    """下载引擎类测试"""
    
    @pytest.fixture
    def download_engine(self):
        """创建下载引擎实例"""
        engine = DownloadEngine(max_workers=2)
        yield engine
        engine.shutdown()
    
    @pytest.fixture
    def temp_download_dir(self):
        """提供临时下载目录"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield tmpdirname
    
    def test_engine_initialization(self, download_engine):
        """测试引擎初始化"""
        assert download_engine.max_workers == 2
        assert download_engine.chunk_size == 8192
        assert download_engine.retry_times == 3
        assert download_engine.retry_delay == 5
    
    @patch('requests.get')
    @patch('civitai_dl.core.downloader.DownloadEngine._download_with_retry')
    def test_download_file(self, mock_download, mock_get, download_engine, temp_download_dir):
        """测试文件下载功能"""
        # 准备一个完成的Future和下载结果
        result_file = os.path.join(temp_download_dir, "test.zip")
        
        # 直接模拟下载完成
        def download_complete(task):
            task.status = "completed"
            task.progress = 1.0
            task.end_time = time.time()
            return result_file
            
        mock_download.side_effect = download_complete
        
        # 创建测试文件
        with open(result_file, 'wb') as f:
            f.write(b'test_data')
        
        # 执行下载
        task = download_engine.download(
            url="https://example.com/file.zip",
            output_path=temp_download_dir,
            filename="test.zip"
        )
        
        # 验证下载参数和状态
        mock_download.assert_called_once()
        assert task.status == "completed"
        assert os.path.exists(result_file)
    
    @patch('requests.get')
    def test_download_error_handling(self, mock_get, download_engine, temp_download_dir):
        """测试错误处理"""
        # 使用更可控的方式模拟请求异常
        mock_get.side_effect = requests.RequestException("下载失败")
        
        # 先清空现有回调以避免测试相互影响
        download_engine._completion_callbacks.clear()
        
        # 简单存储回调触发计数
        callback_count = [0]
        def completion_callback(task):
            callback_count[0] += 1
        
        download_engine.register_completion_callback(completion_callback)
        
        # 直接调用内部方法而非异步提交任务
        task = DownloadTask(
            url="https://example.com/error.zip",
            output_path=temp_download_dir,
            filename="error.zip"
        )
        
        # 手动触发错误情况
        try:
            download_engine._download_file(task)
        except Exception:  # 改为具体异常或加上明确的注释
            pass  # 捕获预期异常
            
        # 验证错误状态
        assert task.status == "failed"
        assert "下载失败" in str(task.error)
        assert callback_count[0] == 1

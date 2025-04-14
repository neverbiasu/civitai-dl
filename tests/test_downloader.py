"""
测试Civitai下载引擎的核心功能
"""
import os
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, patch

import pytest
import requests

from civitai_dl.core.downloader import DownloadEngine, DownloadTask


class TestDownloadTask:
    """下载任务类测试 (pytest风格)"""

    def test_task_initialization(self):
        """测试任务初始化"""
        task = DownloadTask(
            url="https://example.com/file.zip",
            output_path="./downloads",
            filename="test.zip",
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
            filename="test.zip",
        )
        expected_path = os.path.join("./downloads", "test.zip")
        assert os.path.normpath(task.file_path) == os.path.normpath(expected_path)

    def test_task_update_progress(self):
        """测试更新进度"""
        task = DownloadTask(url="https://example.com/file.zip", output_path="./downloads")
        task.update_progress(0.5)
        assert task.progress == 0.5

        # 测试进度范围限制
        task.update_progress(-0.1)
        assert task.progress == 0.0

        task.update_progress(1.5)
        assert task.progress == 1.0

    def test_task_eta(self):
        """测试预估完成时间计算"""
        task = DownloadTask(url="https://example.com/file.zip", output_path="./downloads")
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
        engine = DownloadEngine(output_dir="./downloads", max_workers=2)
        yield engine
        engine.shutdown()

    @pytest.fixture
    def temp_download_dir(self):
        """提供临时下载目录"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield tmpdirname

    def test_engine_initialization(self, download_engine):
        """测试引擎初始化"""
        assert download_engine.concurrent_downloads == 2
        assert download_engine.chunk_size == 8192
        assert download_engine.retry_times == 3
        assert download_engine.retry_delay == 5

    @patch("requests.get")
    def test_download_file(self, mock_get, download_engine, temp_download_dir):
        """测试文件下载功能"""
        os.path.join(temp_download_dir, "test.zip")

        # 配置 mock_get 以模拟成功的下载
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {
            "content-length": "100",
            "Content-Disposition": 'attachment; filename="test.zip"',
        }
        # 模拟 iter_content 返回数据块
        mock_response.iter_content.return_value = [b"a" * 50, b"b" * 50]
        # 让 requests.get 返回这个模拟响应
        mock_get.return_value.__enter__.return_value = mock_response

        # 执行下载
        task = download_engine.download(
            url="https://example.com/file.zip",
            output_path=temp_download_dir,
            filename="original_name.zip",  # 使用一个不同的初始名测试 Content-Disposition
        )

        # 等待下载完成
        task.wait()

        # 验证下载状态和文件
        assert task.status == "completed", f"任务状态应为 completed，实际为 {task.status}"
        # 验证文件名是否根据 Content-Disposition 更新
        expected_final_path = os.path.join(temp_download_dir, "test.zip")
        assert task.file_path == expected_final_path, f"最终文件路径应为 {expected_final_path}，实际为 {task.file_path}"
        assert os.path.exists(expected_final_path), f"文件 {expected_final_path} 应存在"
        # 验证文件大小
        assert os.path.getsize(expected_final_path) == 100

    @patch("requests.get")
    def test_download_error_handling(self, mock_get, download_engine, temp_download_dir):
        """测试错误处理"""
        # 模拟请求失败
        mock_get.side_effect = requests.RequestException("下载失败")

        # 添加一个回调函数
        callback_called = threading.Event()  # 使用 Event 替代计数器，更适合线程环境

        def completion_callback(task):
            # 可以在这里添加断言检查 task 状态
            assert task.status == "failed"
            assert "下载失败" in str(task.error) if task.error else False
            callback_called.set()  # 设置事件表示回调被调用

        # 注册回调
        download_engine.register_completion_callback(completion_callback)

        # 创建并开始下载任务
        task = download_engine.download(
            url="https://example.com/error.zip",
            output_path=temp_download_dir,
            filename="error.zip",
        )

        # 等待任务完成（应该会失败）
        task.wait()

        # 验证错误状态
        assert task.status == "failed"
        assert "下载失败" in str(task.error) if task.error else ""
        # 等待回调函数设置事件，设置超时以防死锁
        assert callback_called.wait(timeout=5), "回调函数应该在5秒内被调用"


# Unittest风格的测试类 - 重命名以避免冲突
class TestDownloadTaskUnittest(unittest.TestCase):
    """测试DownloadTask类 (unittest风格)"""

    def setUp(self):
        self.url = "https://example.com/test.file"
        self.file_path = os.path.join(tempfile.gettempdir(), "test_download.file")
        self.task = DownloadTask(url=self.url, file_path=self.file_path)

    def test_task_initialization(self):
        """测试任务初始化"""
        self.assertEqual(self.task.url, self.url)
        self.assertEqual(self.task.file_path, self.file_path)
        self.assertEqual(self.task.status, "pending")
        self.assertIsNone(self.task.error)
        self.assertEqual(self.task.downloaded_size, 0)
        self.assertIsNone(self.task.total_size)

    def test_task_file_path(self):
        """测试文件路径属性"""
        self.assertEqual(self.task.file_path, self.file_path)

    def test_task_update_progress(self):
        """测试进度更新计算"""
        self.task.downloaded_size = 50
        self.task.total_size = 100
        self.assertEqual(self.task.progress, 0.5)

        # 测试没有总大小时的进度
        self.task.total_size = None
        self.assertEqual(self.task.progress, 0.0)

        # 测试总大小为0时的进度
        self.task.total_size = 0
        self.assertEqual(self.task.progress, 0.0)

    def test_task_eta(self):
        """测试ETA计算"""
        self.task.downloaded_size = 50
        self.task.total_size = 100
        self.task.speed = 10  # 10 bytes/s
        self.assertEqual(self.task.eta, 5)  # (100-50)/10 = 5秒

        # 测试速度为0时的ETA
        self.task.speed = 0
        self.assertIsNone(self.task.eta)


class TestDownloadEngineUnittest(unittest.TestCase):
    """测试DownloadEngine类 (unittest风格)"""

    def setUp(self):
        self.output_dir = tempfile.mkdtemp()
        self.engine = DownloadEngine(output_dir=self.output_dir, concurrent_downloads=2)

    @patch("requests.get")
    def test_engine_initialization(self, mock_get):
        """测试引擎初始化"""
        self.assertEqual(self.engine.output_dir, self.output_dir)
        self.assertEqual(self.engine.concurrent_downloads, 2)
        self.assertEqual(len(self.engine.tasks), 0)
        self.assertTrue(os.path.exists(self.output_dir))

    @patch("requests.get")
    def test_download_file(self, mock_get):
        """测试文件下载"""
        # 模拟成功的响应
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"content-length": "100"}
        mock_response.iter_content.return_value = [b"a" * 50, b"b" * 50]
        mock_get.return_value.__enter__.return_value = mock_response

        # 执行下载
        task = self.engine.download("https://example.com/file.txt")
        task.wait()

        # 验证结果
        self.assertEqual(task.status, "completed")
        self.assertTrue(os.path.exists(task.file_path))
        self.assertEqual(task.downloaded_size, 100)
        self.assertEqual(task.total_size, 100)

    @patch("requests.get")
    def test_download_error_handling(self, mock_get):
        """测试下载错误处理"""
        # 模拟请求失败
        mock_get.side_effect = Exception("Network error")

        # 执行下载
        task = self.engine.download("https://example.com/file.txt")
        task.wait()

        # 验证结果
        self.assertEqual(task.status, "failed")
        self.assertIn("Network error", task.error)
        # 验证结果        self.assertEqual(task.status, "failed")        self.assertIn("Network error", task.error)


if __name__ == "__main__":
    unittest.main()

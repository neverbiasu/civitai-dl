"""
Mock objects for testing
"""
import threading
from unittest.mock import MagicMock

from civitai_dl.api.client import ResourceNotFoundError


class MockCivitaiAPI:
    """测试用的Mock API客户端"""

    def __init__(self, **kwargs):
        self.headers = {}  # 添加headers以避免AttributeError
        self.base_url = "https://civitai.com/api/v1"
        self.api_key = kwargs.get("api_key")
        self.request_lock = threading.Lock()  # 添加lock对象以避免AttributeError
        self.session = MagicMock()  # 模拟session以避免真实请求

        # 添加其他必要的属性
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        self.mock_responses = {
            "models": {
                "items": [
                    {
                        "id": 1,
                        "name": "Test Model",
                        "creator": {"username": "tester"},
                        "type": "Checkpoint",
                        "stats": {"downloadCount": 100, "rating": 4.5},
                        "modelVersions": [
                            {
                                "id": 101,
                                "name": "v1.0",
                                "files": [
                                    {
                                        "name": "model.safetensors",
                                        "id": 1001,
                                        "sizeKB": 1024,
                                        "downloadUrl": "https://example.com/file.safetensors",
                                        "primary": True,
                                    }
                                ],
                            }
                        ],
                    }
                ],
                "metadata": {
                    "totalItems": 1,
                    "currentPage": 1,
                    "pageSize": 10,
                    "totalPages": 1,
                },
            },
            "images": {
                "items": [
                    {
                        "id": 101,
                        "url": "https://example.com/image.jpg",
                        "nsfw": False,
                        "width": 512,
                        "height": 512,
                    }
                ],
                "metadata": {"totalItems": 1},
            },
        }

    def get_model(self, model_id):
        """获取模型详细信息"""
        # 模拟特定ID的响应
        if model_id == 12345:
            # 直接抛出ResourceNotFoundError而不是HTTP错误
            raise ResourceNotFoundError(f"Resource not found: {self.base_url}/models/{model_id}")

        return {
            "id": model_id,
            "name": f"Test Model {model_id}",
            "creator": {"username": "tester"},
            "type": "Checkpoint",
            "stats": {"downloadCount": 100, "rating": 4.5},
            "modelVersions": [
                {
                    "id": 101,
                    "name": "v1.0",
                    "files": [
                        {
                            "name": "model.safetensors",
                            "id": 1001,
                            "sizeKB": 1024,
                            "downloadUrl": "https://example.com/file.safetensors",
                            "primary": True,
                        }
                    ],
                }
            ],
        }

    def search_models(self, **kwargs):
        """搜索模型"""
        return self.mock_responses["models"]

    def get_models(self, params=None):
        """获取模型列表"""
        return self.mock_responses["models"]

    def get_download_url(self, version_id):
        """获取下载URL"""
        return f"https://example.com/download/models/{version_id}"

    def get_images(self, params=None):
        """通用GET请求"""
        return self.mock_responses["images"]

    def get(self, endpoint, params=None):
        """通用GET请求"""
        if "models" in endpoint:
            return self.mock_responses["models"]
        elif "images" in endpoint:
            return self.mock_responses["images"]
        return {}

    def _process_response(self, response):
        """模拟响应处理"""
        if hasattr(response, "status_code") and response.status_code == 404:
            raise ResourceNotFoundError(f"Resource not found: {response.url}")
        elif hasattr(response, "json"):
            return response.json()
        return {}

    def _rate_limited_request(self, *args, **kwargs):
        """完全模拟的请求方法，永远不会进行真实网络请求"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        return mock_response

    def _make_request(self, *args, **kwargs):
        """完全模拟的请求方法"""
        if args and len(args) > 1 and "models/12345" in args[1]:
            raise ResourceNotFoundError(f"Resource not found: {self.base_url}/{args[1]}")
        return {}

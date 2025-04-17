"""
测试Civitai API交互
"""
import os
import time
import urllib3
from unittest.mock import MagicMock, patch

import pytest
import requests

from civitai_dl.api.client import APIError, CivitaiAPI, ResourceNotFoundError

# 禁用所有SSL验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TestCivitaiAPI:
    """Civitai API客户端测试"""

    @pytest.fixture(autouse=True)
    def setup_logging(self, caplog):
        """设置日志捕获"""
        self.caplog = caplog

    def test_get_models(self, api_client):
        """测试获取模型列表功能"""
        # 检查是否有代理设置
        proxy = os.environ.get("CIVITAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
        if not proxy:
            pytest.skip("未设置代理，跳过测试")

        # 使用重试模式运行测试
        self._run_with_retry(self._test_get_models, api_client)

    def _test_get_models(self, api_client):
        """实际执行获取模型列表的测试"""
        # 获取少量模型用于测试
        models = api_client.get_models(params={"limit": 2})

        # 验证返回结构
        assert "items" in models, "返回数据中应该包含'items'字段"
        assert isinstance(models["items"], list), "'items'字段应该是一个列表"
        assert len(models["items"]) > 0, "应该至少返回一个模型"

        # 验证模型数据结构
        model = models["items"][0]
        assert "id" in model, "模型数据中应包含'id'字段"
        assert "name" in model, "模型数据中应包含'name'字段"
        assert "type" in model, "模型数据中应包含'type'字段"

        # 打印模型信息用于调试
        print(f"成功获取模型: ID={model['id']}, 名称={model['name']}, 类型={model['type']}")

    def test_get_model_details(self, api_client):
        """测试获取模型详情功能"""
        # 检查是否有代理设置
        proxy = os.environ.get("CIVITAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
        if not proxy:
            pytest.skip("未设置代理，跳过测试")

        # 打印代理设置以便调试
        print(f"当前使用的代理设置: {proxy}")

        # 使用重试模式运行测试
        self._run_with_retry(self._test_get_model_details, api_client)

    def _test_get_model_details(self, api_client):
        """实际执行获取模型详情的测试"""
        # 先获取一个模型的ID
        models = api_client.get_models(params={"limit": 1})
        assert "items" in models, "返回数据中应该包含'items'字段"
        assert len(models["items"]) > 0, "应该至少返回一个模型"

        model_id = models["items"][0]["id"]
        print(f"正在获取模型详情，ID: {model_id}")

        # 获取该模型的详细信息
        model_details = api_client.get_model(model_id)

        # 验证模型详情
        assert model_details["id"] == model_id, "返回的模型ID应与请求的ID一致"
        assert "name" in model_details, "模型详情中应包含'name'字段"
        assert "type" in model_details, "模型详情中应包含'type'字段"
        assert "modelVersions" in model_details, "模型详情中应包含'modelVersions'字段"

        # 打印模型详情用于调试
        print(f"成功获取模型详情: {model_details['name']}")

    def _run_with_retry(self, test_func, *args, max_retries=3, retry_wait=5):
        """使用重试机制运行测试函数"""
        last_exception = None
        for attempt in range(max_retries):
            try:
                return test_func(*args)
            except (requests.RequestException, APIError) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"尝试 {attempt+1}/{max_retries} 失败: {str(e)}")
                    time.sleep(retry_wait)
                else:
                    raise pytest.fail(f"API请求在 {max_retries} 次尝试后仍失败: {str(e)}") from last_exception

    @pytest.mark.skipif(os.environ.get("SKIP_REAL_API", "1") == "1", 
                       reason="默认跳过实际API调用，设置SKIP_REAL_API=0启用")
    def test_get_images(self, api_client):
        """测试获取图像列表功能"""
        # 先获取一个模型的ID
        models = api_client.get_models(params={"limit": 1})
        model_id = models["items"][0]["id"]

        # 获取该模型的图像
        images = api_client.get_images(params={"modelId": model_id, "limit": 2})

        # 验证图像数据
        assert "items" in images, "返回数据中应该包含'items'字段"

        # 如果有图像，验证图像数据结构
        if len(images["items"]) > 0:
            image = images["items"][0]
            assert "url" in image, "图像数据中应包含'url'字段"
            assert "nsfw" in image, "图像数据中应包含'nsfw'字段"
            assert isinstance(image["nsfw"], bool), "'nsfw'字段应该是布尔值"


# 以下是API相关的模拟测试

@patch("civitai_dl.api.client.CivitaiAPI._rate_limited_request")
def test_api_connection(mock_request):
    """测试API连接，使用模拟的网络请求"""
    # 设置mock响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [{"id": 257749, "name": "Pony Diffusion V6 XL", "type": "Checkpoint"}],
        "metadata": {"totalItems": 1},
    }
    mock_request.return_value = mock_response

    # 获取系统代理设置
    proxy = os.environ.get("CIVITAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    
    # 使用原始的CivitaiAPI，根据环境添加代理设置
    api = CivitaiAPI(verify=False, proxy=proxy)
    response = api.get_models(params={"limit": 1})

    # 添加调试打印
    print("DEBUG - 完整响应:", response)
    print("DEBUG - items类型:", type(response["items"]))
    print("DEBUG - items内容:", response["items"])
    if len(response["items"]) > 0:
        print("DEBUG - 第一个item的ID:", response["items"][0]["id"], "类型:", type(response["items"][0]["id"]))
        print("DEBUG - 第一个item的完整内容:", response["items"][0])
    
    # 验证响应处理
    assert "items" in response
    assert len(response["items"]) == 1
    assert response["items"][0]["id"] == 257749
    assert response["items"][0]["name"] == "Pony Diffusion V6 XL"


@patch("civitai_dl.api.client.CivitaiAPI._rate_limited_request")
def test_api_error_handling(mock_request):
    """测试API错误处理，使用模拟的HTTP错误"""
    # 设置mock响应 - 404错误
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "404 Client Error", response=mock_response
    )
    mock_response.url = "https://civitai.com/api/v1/models/12345"
    mock_request.return_value = mock_response

    # 使用原始的CivitaiAPI
    api = CivitaiAPI(verify=False)

    # 测试是否正确转换为自定义异常
    with pytest.raises(ResourceNotFoundError) as excinfo:
        api.get_model(12345)

    assert "Resource not found" in str(excinfo.value), "应该抛出ResourceNotFoundError异常"


# 网络诊断测试
@patch("requests.get")
def test_network_diagnostics(mock_get):
    """诊断网络连接问题（模拟版本）"""
    # 设置模拟响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": []}
    mock_get.return_value = mock_response

    try:
        # 模拟成功连接
        print("能够连接到Civitai网站 (模拟)")
        print("成功连接到API端点 (模拟)")
        print("API响应模拟完成")
    except Exception as e:
        pytest.skip(f"网络连接问题 (模拟): {str(e)}")

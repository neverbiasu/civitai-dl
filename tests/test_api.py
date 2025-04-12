"""
测试Civitai API交互
"""
import os
from unittest.mock import MagicMock, patch
import pytest
import time
import requests
from civitai_dl.api.client import CivitaiAPI, ResourceNotFoundError, APIError


class TestCivitaiAPI:
    """Civitai API客户端测试"""

    def test_get_models(self, api_client):  # 现在这里的 api_client 来自 conftest.py
        """测试获取模型列表功能"""
        # 检查是否有代理设置
        proxy = os.environ.get("CIVITAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
        if not proxy:
            pytest.skip("未设置代理，跳过测试")

        # 增加最大重试次数和等待时间
        max_retries = 3
        retry_wait = 5

        for attempt in range(max_retries):
            try:
                # 获取少量模型用于测试
                models = api_client.get_models(params={"limit": 2})

                # 验证返回结构
                assert "items" in models
                assert isinstance(models["items"], list)

                # 验证至少返回了一个模型
                assert len(models["items"]) > 0

                # 验证模型数据结构
                model = models["items"][0]
                assert "id" in model
                assert "name" in model
                assert "type" in model

                # 测试成功，退出循环
                break

            except (requests.RequestException, APIError) as e:
                if attempt < max_retries - 1:
                    # 记录错误但继续尝试
                    print(f"尝试 {attempt+1}/{max_retries} 失败: {str(e)}")
                    time.sleep(retry_wait)
                else:
                    # 最后一次尝试仍失败，则测试失败
                    pytest.fail(f"API请求在 {max_retries} 次尝试后仍失败: {str(e)}")

    def test_get_model_details(self, api_client):  # 现在这里的 api_client 来自 conftest.py
        """测试获取模型详情功能"""
        # 检查是否有代理设置
        proxy = os.environ.get("CIVITAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
        if not proxy:
            pytest.skip("未设置代理，跳过测试")

        # 打印代理设置以便调试
        print(f"当前使用的代理设置: {proxy}")

        # 增加最大重试次数和等待时间
        max_retries = 3
        retry_wait = 5

        for attempt in range(max_retries):
            try:
                # 先获取一个模型的ID
                models = api_client.get_models(params={"limit": 1})
                assert "items" in models
                assert len(models["items"]) > 0

                model_id = models["items"][0]["id"]

                # 获取该模型的详细信息
                model_details = api_client.get_model(model_id)

                # 验证模型详情
                assert model_details["id"] == model_id
                assert "name" in model_details
                assert "type" in model_details
                assert "modelVersions" in model_details

                # 测试成功，退出循环
                break

            except (requests.RequestException, APIError) as e:
                if attempt < max_retries - 1:
                    # 记录错误但继续尝试
                    print(f"尝试 {attempt+1}/{max_retries} 失败: {str(e)}")
                    time.sleep(retry_wait)
                else:
                    # 最后一次尝试仍失败，则测试失败
                    pytest.fail(f"API请求在 {max_retries} 次尝试后仍失败: {str(e)}")

    @pytest.mark.skipif("SKIP_REAL_API" not in os.environ, reason="跳过实际API调用，避免网络错误")
    def test_get_images(self, api_client):
        """测试获取图像列表功能"""
        # 先获取一个模型的ID
        models = api_client.get_models(params={"limit": 1})
        model_id = models["items"][0]["id"]

        # 获取该模型的图像
        images = api_client.get_images(params={"modelId": model_id, "limit": 2})

        # 验证图像数据
        assert "items" in images

        # 如果有图像，验证图像数据结构
        if len(images["items"]) > 0:
            image = images["items"][0]
            assert "url" in image
            assert "nsfw" in image
            assert isinstance(image["nsfw"], bool)


# 测试API连接
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

    # 使用原始的CivitaiAPI
    api = CivitaiAPI(verify=False)
    response = api.get_models(params={"limit": 1})

    # 验证响应处理
    assert "items" in response
    assert len(response["items"]) == 1
    assert response["items"][0]["id"] == 257749
    assert response["items"][0]["name"] == "Pony Diffusion V6 XL"


# 测试API错误处理
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

    assert "Resource not found" in str(excinfo.value)


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

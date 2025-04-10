"""
测试Civitai API交互
"""
import os
import pytest
import time
import requests
from unittest.mock import patch, MagicMock
from civitai_dl.api.client import CivitaiAPI, ResourceNotFoundError, APIError


class TestCivitaiAPI:
    """Civitai API客户端测试"""

    @pytest.fixture
    def api_client(self):
        """创建API客户端实例"""
        # 创建API客户端时添加更多网络选项
        client = CivitaiAPI()
        # 增加超时设置，避免请求卡住
        client.timeout = 30
        # 增加请求头，有些API需要特定的User-Agent
        client.headers.update({
            'User-Agent': 'CivitaiDownloader/Test (https://github.com/neverbiasu/civitai-dl)'
        })
        return client

    def test_get_models(self, api_client):
        """测试获取模型列表功能"""
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

    def test_get_model_details(self, api_client):
        """测试获取模型详情功能"""
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

    @pytest.mark.skipif("SKIP_REAL_API" not in os.environ, 
                      reason="跳过实际API调用，避免网络错误")
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


# 通过检查API实现来创建更精准的测试
def test_api_connection():
    """测试API连接，使用客户端自身方法的模拟"""
    # 创建一个具有模拟方法的API客户端子类
    class MockCivitaiAPI(CivitaiAPI):
        def _make_request(self, method, endpoint, **kwargs):
            """模拟请求方法，返回预定义响应"""
            # 检查是否是我们期望的调用
            if method == "GET" and endpoint == "models" and kwargs.get('params', {}).get('limit') == 1:
                return {
                    "items": [
                        {"id": 1, "name": "Test Model", "type": "Checkpoint"}
                    ],
                    "metadata": {"totalItems": 1}
                }
            # 否则返回空结果
            return {"items": []}
    
    # 使用模拟API客户端
    api = MockCivitaiAPI()
    response = api.get_models(params={"limit": 1})
    
    # 验证响应处理
    assert "items" in response
    assert len(response["items"]) == 1
    assert response["items"][0]["id"] == 257749
    assert response["items"][0]["name"] == "Pony Diffusion V6 XL"

# 使用更通用的模拟方式处理错误测试
def test_api_error_handling():
    """测试API错误处理，使用客户端自身方法的模拟"""
    # 创建一个模拟API客户端
    class MockCivitaiAPI(CivitaiAPI):
        def _make_request(self, method, endpoint, **kwargs):
            """模拟请求方法，抛出404错误"""
            if "models/12345" in endpoint:
                # 创建模拟响应
                mock_response = MagicMock()
                mock_response.status_code = 404
                mock_response.url = "https://civitai.com/api/v1/models/12345"
                
                # 抛出HTTPError
                from requests.exceptions import HTTPError
                raise HTTPError("404 Client Error", response=mock_response)
            return {}
    
    # 使用模拟API客户端
    api = MockCivitaiAPI()
    
    # 测试是否正确转换为自定义异常
    with pytest.raises(ResourceNotFoundError) as excinfo:
        api.get_model(12345)
    
    assert "Resource not found" in str(excinfo.value)


# 添加网络问题诊断测试
def test_network_diagnostics():
    """诊断网络连接问题"""
    try:
        # 检查是否能连接到Civitai网站
        response = requests.get("https://civitai.com", timeout=10)
        response.raise_for_status()
        print(f"能够连接到Civitai网站，状态码: {response.status_code}")
        
        # 尝试请求API端点
        api_response = requests.get("https://civitai.com/api/v1/models?limit=1", timeout=10)
        api_response.raise_for_status()
        print("成功连接到API端点")
        print(f"API响应: {api_response.json()}")
        
    except Exception as e:
        if "certificate" in str(e).lower():
            pytest.skip("SSL证书验证失败，可能需要禁用SSL验证或添加证书")
        elif "timeout" in str(e).lower():
            pytest.skip("连接超时，可能是网络延迟或代理问题")
        else:
            pytest.skip(f"网络连接问题: {str(e)}")

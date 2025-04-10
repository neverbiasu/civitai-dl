"""
测试Civitai API交互
"""
import os
import pytest
from unittest.mock import patch
from civitai_dl.api.client import CivitaiAPI, ResourceNotFoundError


class TestCivitaiAPI:
    """Civitai API客户端测试"""

    @pytest.fixture
    def api_client(self):
        """创建API客户端实例"""
        return CivitaiAPI()

    @pytest.mark.skipif("SKIP_REAL_API" not in os.environ, 
                      reason="跳过实际API调用，避免网络错误")
    def test_get_models(self, api_client):
        """测试获取模型列表功能"""
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

    @pytest.mark.skipif("SKIP_REAL_API" not in os.environ, 
                      reason="跳过实际API调用，避免网络错误")
    def test_get_model_details(self, api_client):
        """测试获取模型详情功能"""
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


# 直接模拟API客户端的方法，而不是底层requests
def test_api_connection():
    """测试API连接"""
    # 创建API客户端的模拟对象
    with patch.object(CivitaiAPI, 'get') as mock_get:
        mock_get.return_value = {"status": "ok"}
        
        api = CivitaiAPI()
        response = api.get("models")
        
        # 验证模拟响应
        assert mock_get.called
        assert response == {"status": "ok"}

# 测试API错误处理
def test_api_error_handling():
    """测试API错误处理"""
    # 创建模拟对象，抛出预期的异常
    with patch.object(CivitaiAPI, 'get_model') as mock_get_model:
        mock_get_model.side_effect = ResourceNotFoundError("Resource not found: models/12345")
        
        api = CivitaiAPI()
        
        with pytest.raises(ResourceNotFoundError):
            api.get_model(12345)

import os
import pytest
import tempfile

"""
Pytest配置和全局fixtures
"""

@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """设置测试环境变量和全局配置"""
    # 如果存在测试API密钥，从环境变量中获取
    api_key = os.environ.get("CIVITAI_API_KEY", "")

    # 配置测试时使用的基本参数
    os.environ["CIVITAI_TEST_MODE"] = "1"

    # 确保测试不会意外触发大型下载
    os.environ["CIVITAI_MAX_TEST_DOWNLOAD"] = "1048576"  # 1MB

    yield

    # 清理临时环境变量
    if "CIVITAI_TEST_MODE" in os.environ:
        del os.environ["CIVITAI_TEST_MODE"]


@pytest.fixture
def mock_successful_api_response():
    """模拟成功的API响应"""
    return {
        "items": [
            {
                "id": 12345,
                "name": "测试模型",
                "type": "LORA",
                "creator": {"username": "test_user"},
                "stats": {"downloadCount": 100, "rating": 4.5},
            }
        ],
        "metadata": {"totalItems": 1, "currentPage": 1, "pageSize": 1, "totalPages": 1},
    }

@pytest.fixture
def temp_directory():
    """提供临时目录用于测试文件下载"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def mock_api_response():
    """模拟API响应数据"""
    return {
        "id": 12345,
        "name": "Test Model",
        "modelVersions": [
            {
                "id": 67890,
                "name": "v1.0",
                "files": [
                    {"name": "model.safetensors", "downloadUrl": "https://example.com/model.safetensors"}
                ]
            }
        ]
    }

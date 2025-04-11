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
    os.environ.get("CIVITAI_API_KEY")

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
                    {
                        "name": "model.safetensors",
                        "downloadUrl": "https://example.com/model.safetensors",
                    }
                ],
            }
        ],
    }


@pytest.fixture(autouse=True)
def disable_proxy_for_tests():
    """在测试中禁用代理设置，在CI环境中禁用代理"""
    # 保存原始环境变量
    original_proxy = os.environ.get("HTTP_PROXY")
    original_https_proxy = os.environ.get("HTTPS_PROXY")
    original_no_proxy = os.environ.get("NO_PROXY")

    # 在CI环境中禁用代理
    if "CI" in os.environ or "CI_TESTING" in os.environ:
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)
        os.environ["NO_PROXY"] = "*"
    else:
        # 确保使用系统或用户配置的代理
        civitai_proxy = os.environ.get("CIVITAI_PROXY")
        if civitai_proxy:
            os.environ["HTTP_PROXY"] = civitai_proxy
            os.environ["HTTPS_PROXY"] = civitai_proxy
            print(f"CIVITAI_PROXY环境变量设置代理: {civitai_proxy}")
        elif original_proxy or original_https_proxy:
            print(
                f"使用系统代理 HTTP_PROXY={original_proxy}, HTTPS_PROXY={original_https_proxy}"
            )

    yield

    # 恢复环境
    if original_proxy:
        os.environ["HTTP_PROXY"] = original_proxy
    else:
        os.environ.pop("HTTP_PROXY", None)

    if original_https_proxy:
        os.environ["HTTPS_PROXY"] = original_https_proxy
    else:
        os.environ.pop("HTTPS_PROXY", None)

    if original_no_proxy:
        os.environ["NO_PROXY"] = original_no_proxy
    else:
        os.environ.pop("NO_PROXY", None)


@pytest.fixture
def api_client():
    """提供API客户端实例"""
    from civitai_dl.api.client import CivitaiAPI

    # 使用环境变量中的代理设置（如果有）
    proxy = os.environ.get("CIVITAI_PROXY")

    return CivitaiAPI(
        api_key=os.environ.get("CIVITAI_API_KEY"),
        proxy=proxy,
        verify=False,  # 测试时禁用SSL验证
    )

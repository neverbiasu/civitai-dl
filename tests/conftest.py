import os
import pytest
import tempfile

import requests

"""
Pytest配置和全局fixtures
"""


@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """设置测试环境变量和全局配置"""
    # 尝试从.env文件加载环境变量
    try:
        from civitai_dl.utils.env import load_env_file
        load_env_file()
    except ImportError:
        pass

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
    """
    提供真实的API客户端实例，用于实际测试API连接情况。

    将使用环境变量中的API密钥和代理设置。
    """
    from civitai_dl.api.client import CivitaiAPI

    # 获取API密钥
    api_key = os.environ.get("CIVITAI_API_KEY")

    # 优先使用CIVITAI_PROXY，如果没有则尝试使用系统代理
    proxy = os.environ.get("CIVITAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

    if api_key:
        print(f"API客户端: 使用API密钥: {api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:] if len(api_key) > 8 else ''}")

    if proxy:
        print(f"API客户端: 使用代理: {proxy}")
        # 测试代理连接
        try:
            test_response = requests.get(
                "https://api.ipify.org",
                proxies={
                    "http": proxy,
                    "https": proxy},
                timeout=10,
                verify=False)
            print(f"代理连接测试: 成功! IP: {test_response.text}")
        except Exception as e:
            print(f"代理连接测试失败: {str(e)}")
            # 如果代理测试失败，尝试不同的设置格式
            if 'http://' in proxy:
                alt_proxy = proxy.replace('http://', 'socks5://')
                print(f"尝试替代代理格式: {alt_proxy}")
                try:
                    test_response = requests.get(
                        "https://api.ipify.org",
                        proxies={
                            "http": alt_proxy,
                            "https": alt_proxy},
                        timeout=10,
                        verify=False)
                    print(f"替代代理连接测试: 成功! IP: {test_response.text}")
                    proxy = alt_proxy  # 如果成功，使用新格式
                except Exception as e:
                    print(f"替代代理连接测试也失败: {str(e)}")
    else:
        print("警告: 未设置代理，可能无法访问Civitai API。请设置CIVITAI_PROXY、HTTP_PROXY或HTTPS_PROXY环境变量。")

    # 创建API客户端实例
    client = CivitaiAPI(
        api_key=api_key,
        proxy=proxy,
        verify=False,  # 禁用SSL验证以避免证书问题
        timeout=30     # 增加超时时间
    )

    # 检查client中的代理设置
    if hasattr(client, 'session') and hasattr(client.session, 'proxies'):
        print(f"API客户端session代理设置: {client.session.proxies}")

    return client

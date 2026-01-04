import os
import tempfile

import pytest
import requests

"""
Pytest configuration and global fixtures
"""


@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Set up test environment variables and global configuration"""
    # Try to load environment variables from .env file
    try:
        from civitai_dl.utils.env import load_env_file

        load_env_file()
    except ImportError:
        pass

    # Get API key from environment variables if present
    os.environ.get("CIVITAI_API_KEY")

    # Configure basic parameters for testing
    os.environ["CIVITAI_TEST_MODE"] = "1"

    # Ensure tests do not accidentally trigger large downloads
    os.environ["CIVITAI_MAX_TEST_DOWNLOAD"] = "1048576"  # 1MB

    yield

    # Clean up temporary environment variables
    if "CIVITAI_TEST_MODE" in os.environ:
        del os.environ["CIVITAI_TEST_MODE"]


@pytest.fixture
def mock_successful_api_response():
    """Mock successful API response"""
    return {
        "items": [
            {
                "id": 12345,
                "name": "Test Model",
                "type": "LORA",
                "creator": {"username": "test_user"},
                "stats": {"downloadCount": 100, "rating": 4.5},
            }
        ],
        "metadata": {"totalItems": 1, "currentPage": 1, "pageSize": 1, "totalPages": 1},
    }


@pytest.fixture
def temp_directory():
    """Provide a temporary directory for file download tests"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def mock_api_response():
    """Mock API response data"""
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
    """Disable proxy settings during tests, disable proxy in CI environment"""
    # Save original environment variables
    original_proxy = os.environ.get("HTTP_PROXY")
    original_https_proxy = os.environ.get("HTTPS_PROXY")
    original_no_proxy = os.environ.get("NO_PROXY")

    # Disable proxy in CI environment
    if "CI" in os.environ or "CI_TESTING" in os.environ:
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)
        os.environ["NO_PROXY"] = "*"
    else:
        # Ensure using system or user configured proxy
        civitai_proxy = os.environ.get("CIVITAI_PROXY")
        if civitai_proxy:
            os.environ["HTTP_PROXY"] = civitai_proxy
            os.environ["HTTPS_PROXY"] = civitai_proxy
            print(f"CIVITAI_PROXY environment variable set proxy: {civitai_proxy}")
        elif original_proxy or original_https_proxy:
            print(f"Using system proxy HTTP_PROXY={original_proxy}, HTTPS_PROXY={original_https_proxy}")

    yield

    # Restore environment
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
    Provide a real API client instance for actual API connection testing.

    Will use API key and proxy settings from environment variables.
    """
    from civitai_dl.api.client import CivitaiAPI

    # Get API key
    api_key = os.environ.get("CIVITAI_API_KEY")

    # Prefer CIVITAI_PROXY, if not set, try using system proxy
    proxy = os.environ.get("CIVITAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

    if api_key:
        print(f"API Client: Using API Key: {api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:] if len(api_key) > 8 else ''}")

    if proxy:
        print(f"API Client: Using Proxy: {proxy}")
        # Test proxy connection
        try:
            test_response = requests.get(
                "https://api.ipify.org",
                proxies={"http": proxy, "https": proxy},
                timeout=10,
                verify=False,
            )
            print(f"Proxy connection test: Success! IP: {test_response.text}")
        except Exception as e:
            print(f"Proxy connection test failed: {str(e)}")
            # If proxy test fails, try different format
            if "http://" in proxy:
                alt_proxy = proxy.replace("http://", "socks5://")
                print(f"Trying alternative proxy format: {alt_proxy}")
                try:
                    test_response = requests.get(
                        "https://api.ipify.org",
                        proxies={"http": alt_proxy, "https": alt_proxy},
                        timeout=10,
                        verify=False,
                    )
                    print(f"Alternative proxy connection test: Success! IP: {test_response.text}")
                    proxy = alt_proxy  # If successful, use new format
                except Exception as e:
                    print(f"Alternative proxy connection test also failed: {str(e)}")
    else:
        print("Warning: Proxy not set, may not be able to access Civitai API. Please set CIVITAI_PROXY, HTTP_PROXY or HTTPS_PROXY environment variables.")

    # Create API client instance
    client = CivitaiAPI(
        api_key=api_key,
        proxy=proxy,
        verify=False,  # Disable SSL verification to avoid certificate issues
        timeout=30,  # Increase timeout
    )

    # Check proxy settings in client
    if hasattr(client, "session") and hasattr(client.session, "proxies"):
        print(f"API client session proxy settings: {client.session.proxies}")

    return client

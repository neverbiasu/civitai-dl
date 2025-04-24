"""Civitai API client for interacting with the Civitai platform.

This module provides a client for accessing the Civitai API endpoints,
with support for common operations like model searching, downloading,
and image retrieval.
"""

import json
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

import requests
from requests.exceptions import RequestException, Timeout, HTTPError

from civitai_dl.utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)

# API base URL constant
CIVITAI_API_BASE = "https://civitai.com/api/v1/"


class APIError(Exception):
    """Exception raised for API-related errors.

    Attributes:
        status_code: HTTP status code if available
        message: Error message
        response: Full response object if available
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[requests.Response] = None
    ) -> None:
        """Initialize APIError with details.

        Args:
            message: Error description
            status_code: HTTP status code
            response: Response object that caused the error
        """
        self.status_code = status_code
        self.response = response
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation of the error.

        Returns:
            Formatted error message with status code if available
        """
        if self.status_code:
            return f"API Error ({self.status_code}): {self.message}"
        return f"API Error: {self.message}"


class ResourceNotFoundError(APIError):
    """Exception raised when a requested resource is not found (404 error)."""

    def __init__(self, message: str = "Requested resource not found", status_code: int = 404, response=None):
        super().__init__(message, status_code, response)


class CivitaiAPI:
    """Client for interacting with the Civitai API.

    Provides methods for searching models, retrieving images, and
    managing downloads from the Civitai platform.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        proxy: Optional[str] = None,
        verify: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
    ) -> None:
        """Initialize the Civitai API client.

        Args:
            api_key: Optional API key for authenticated requests
            proxy: Optional proxy URL for all requests
            verify: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            user_agent: Custom User-Agent header
        """
        self.api_key = api_key
        self.proxy = proxy
        self.verify = verify
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent or "CivitaiDownloader/1.0"
        self.base_url = CIVITAI_API_BASE
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create and configure a requests session.

        Sets up a session with appropriate headers, proxies, etc.

        Returns:
            Configured requests.Session object
        """
        session = requests.Session()
        session.headers.update(self.build_headers())

        # Configure proxy if provided
        if self.proxy:
            session.proxies = {
                "http": self.proxy,
                "https": self.proxy
            }

        return session

    def build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for API requests.

        Includes authentication if API key is available.

        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Send a request to the API with automatic retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: URL query parameters
            data: Form data to send
            json_data: JSON data to send
            headers: Additional headers
            retry_count: Current retry attempt count

        Returns:
            Parsed JSON response

        Raises:
            APIError: On request failures or invalid responses
        """
        url = urljoin(self.base_url, endpoint)
        request_headers = self.build_headers()
        if headers:
            request_headers.update(headers)

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=request_headers,
                timeout=self.timeout,
                verify=self.verify
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError:
                raise APIError(f"Invalid JSON response: {response.text[:100]}...")

        except Timeout:
            if retry_count < self.max_retries:
                wait_time = min(2 ** retry_count, 30)  # Exponential backoff
                logger.warning(f"Request timed out, retrying in {wait_time}s... ({retry_count+1}/{self.max_retries})")
                time.sleep(wait_time)
                return self._make_request(method, endpoint, params, data, json_data, headers, retry_count + 1)
            raise APIError(f"Request timed out after {self.max_retries} retries")

        except HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else None

            # Handle rate limiting
            if status_code == 429:
                if retry_count < self.max_retries:
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited, retrying in {retry_after}s... ({retry_count+1}/{self.max_retries})")
                    time.sleep(retry_after)
                    return self._make_request(method, endpoint, params, data, json_data, headers, retry_count + 1)

            error_message = f"HTTP Error: {e}"
            try:
                error_data = e.response.json()
                if 'message' in error_data:
                    error_message = f"API Error: {error_data['message']}"
            except (json.JSONDecodeError, AttributeError):
                pass

            raise APIError(error_message, status_code, getattr(e, 'response', None))

        except RequestException as e:
            if retry_count < self.max_retries:
                wait_time = min(2 ** retry_count, 30)
                logger.warning(f"Request failed, retrying in {wait_time}s... ({retry_count+1}/{self.max_retries})")
                time.sleep(wait_time)
                return self._make_request(method, endpoint, params, data, json_data, headers, retry_count + 1)
            raise APIError(f"Request failed: {str(e)}")

    def get_models(self, **params):
        """获取模型列表

        Args:
            **params: API查询参数，例如:
                limit: 结果数量限制 (int)
                page: 页码 (int)
                query: 搜索查询 (str)
                types: 模型类型列表 (如 ["Checkpoint", "LORA"])
                sort: 排序方式
                period: 时间范围
                nsfw: 是否包含NSFW内容
                username: 创作者用户名
                tag: 标签

        Returns:
            API响应，包含模型列表和元数据
        """
        # 类型转换与清理
        api_params = {}
        for k, v in params.items():
            if v in (None, "", [], {}):
                continue
            if k == "limit":
                try:
                    api_params[k] = int(v)
                except Exception:
                    continue
            elif k == "types":
                # 支持字符串、列表、元组
                if isinstance(v, str):
                    api_params[k] = [v]
                elif isinstance(v, (list, tuple)):
                    api_params[k] = list(v)
                else:
                    continue
            else:
                api_params[k] = v
        logger.debug(f"获取模型列表，最终API参数: {api_params}")
        return self._make_request("GET", "models", params=api_params)

    def get_model(self, model_id: int) -> Dict[str, Any]:
        """Get details for a specific model.

        Args:
            model_id: The model ID to retrieve

        Returns:
            Model details including description, creator info, and versions

        Raises:
            APIError: If the model cannot be retrieved
        """
        return self._make_request("GET", f"models/{model_id}")

    def search_creators(self, username: str) -> Dict[str, Any]:
        """Search for creators by username.

        Args:
            username: Partial or complete username to search for

        Returns:
            API response with list of matching creators
        """
        return self._make_request("GET", "creators", params={"query": username})

    def get_creator(self, creator_id: int) -> Dict[str, Any]:
        """Get details for a specific creator.

        Args:
            creator_id: The creator ID to retrieve

        Returns:
            Creator profile details
        """
        return self._make_request("GET", f"creators/{creator_id}")

    def search_tags(self, query: str) -> List[Dict[str, Any]]:
        """Search for tags by name.

        Args:
            query: Tag name to search for

        Returns:
            List of matching tags
        """
        response = self._make_request("GET", "tags", params={"query": query})
        return response.get("items", [])

    def get_model_versions(self, model_id: int) -> List[Dict[str, Any]]:
        """Get all versions of a specific model.

        Args:
            model_id: The model ID

        Returns:
            List of model versions
        """
        model_data = self.get_model(model_id)
        return model_data.get("modelVersions", [])

    def get_version(self, version_id: int) -> Dict[str, Any]:
        """Get details for a specific model version.

        Args:
            version_id: The version ID

        Returns:
            Version details
        """
        return self._make_request("GET", f"model-versions/{version_id}")

    def get_version_images(self, version_id: int) -> List[Dict[str, Any]]:
        """Get images for a specific model version.

        Args:
            version_id: The version ID

        Returns:
            List of images for the version
        """
        data = self.get_version(version_id)
        return data.get("images", [])

    def get_images(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search for images on Civitai.

        Args:
            params: Search parameters
                - limit: Maximum number of results
                - page: Page number
                - modelId: Filter by model
                - modelVersionId: Filter by model version
                - nsfw: Include NSFW content

        Returns:
            API response with image list and metadata
        """
        return self._make_request("GET", "images", params=params)

    def get_download_url(self, version_id: int, file_id: Optional[int] = None) -> Optional[str]:
        """Get the download URL for a model version.

        Args:
            version_id: The model version ID
            file_id: Optional specific file ID

        Returns:
            Download URL or None if not found
        """
        try:
            version_data = self.get_version(version_id)
            files = version_data.get("files", [])

            if not files:
                return None

            # 如果指定了file_id，尝试找到匹配的文件
            if file_id:
                target_file = next((f for f in files if f.get("id") == file_id), None)
            else:
                # 否则选择主文件或第一个文件
                target_file = next((f for f in files if f.get("primary", False)), files[0])

            if target_file:
                if "downloadUrl" in target_file:
                    return target_file["downloadUrl"]
                else:
                    # 有些API响应不直接包含downloadUrl，需要额外请求
                    download_info = self._make_request(
                        "GET",
                        f"model-versions/{version_id}/download",
                        params={"type": "model", "file_id": target_file.get("id")}
                    )
                    return download_info.get("downloadUrl")

            return None

        except Exception as e:
            logger.error(f"获取下载链接失败: {str(e)}")
            return None

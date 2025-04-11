"""Civitai API client implementation."""

import os
import time
import requests
from threading import Lock
import logging
import urllib3
from typing import Dict, Any, Optional, List

from ..config.proxy_settings import get_proxy_settings, get_verify_ssl

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, message, response=None, url=None):
        self.message = message
        self.response = response
        self.url = url
        self.status_code = response.status_code if response else None
        
        # 添加可能的解决方案
        self.solutions = self._get_solutions()
        
        # 构建包含解决方案的完整错误消息
        full_message = message
        if self.solutions:
            full_message += "\nPossible solutions:\n" + "\n".join([f"{i+1}. {s}" for i, s in enumerate(self.solutions)])
        
        super().__init__(full_message)
    
    def _get_solutions(self):
        """根据错误类型提供可能的解决方案"""
        solutions = []
        
        if 'Proxy' in self.message or 'proxy' in self.message:
            solutions.extend([
                "Check if the proxy server is running",
                "Verify the proxy address and port",
                "Ensure the proxy server allows access to the target site",
                "Try using a different proxy server",
                "Use --no-proxy option to disable proxy"
            ])
        elif 'timeout' in self.message.lower():
            solutions.extend([
                "Check your internet connection",
                "Try again later, the server might be busy",
                "Increase the timeout value using --timeout option"
            ])
        elif self.status_code == 401:
            solutions.extend([
                "Check your API key",
                "Ensure your API key has the necessary permissions"
            ])
        elif self.status_code == 403:
            solutions.extend([
                "You don't have permission to access this resource",
                "Check if you need to authenticate",
                "Ensure your API key is correct"
            ])
        elif self.status_code == 404:
            solutions.extend([
                "The requested resource does not exist",
                "Check the ID or endpoint URL"
            ])
        elif self.status_code and self.status_code >= 500:
            solutions.extend([
                "The server encountered an error",
                "Try again later",
                "Check Civitai status page for any outages"
            ])
        
        # 添加通用解决方案
        if not solutions:
            solutions.extend([
                "Check your internet connection",
                "Verify the API endpoint is correct",
                "Ensure you're using the latest version of the client"
            ])
        
        return solutions


class ResourceNotFoundError(APIError):
    """Exception raised when the requested resource is not found."""

    pass


class RateLimitError(APIError):
    """Exception raised when API rate limit is exceeded."""

    pass


class AuthenticationError(APIError):
    """Exception raised when API authentication fails."""

    pass


class CivitaiAPI:
    """Client for interacting with the Civitai API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://civitai.com/api/v1/",
        proxy: Optional[Dict[str, str]] = None,
        verify_ssl: Optional[bool] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 2,
    ):
        """
        Initialize API client.

        Args:
            api_key: Civitai API key
            base_url: API base URL
            proxy: Proxy settings, format {'http': 'http://proxy:port', 'https': 'https://proxy:port'}
                   Set to None to use system proxy, set to {} to disable all proxies
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
        """
        self.api_key = api_key or os.environ.get("CIVITAI_API_KEY")
        self.base_url = base_url
        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        # Create session object for connection reuse
        self.session = requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Set proxy
        if proxy is None:
            # Use default proxy settings
            proxy = get_proxy_settings()

        self.proxy = proxy
        if proxy:
            self.session.proxies = proxy
            logger.info(f"Using proxy settings: {proxy}")

        # Set SSL verification
        if verify_ssl is None:
            verify_ssl = get_verify_ssl()

        if not verify_ssl:
            # Disable SSL verification (not recommended, but may be needed in some environments)
            self.session.verify = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning(
                "Warning: SSL verification is disabled, this may pose security risks"
            )

        # Rate limiting controls
        self.min_request_interval = 0.5  # seconds
        self.last_request_time = 0
        self.request_lock = Lock()

    def _rate_limited_request(
        self, method: str, url: str, **kwargs
    ) -> requests.Response:
        """
        Execute a rate-limited API request.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional arguments passed to requests

        Returns:
            HTTP response

        Raises:
            APIError: On API connection failure
        """
        with self.request_lock:
            # Calculate and wait for rate limit
            current_time = time.time()
            elapsed = current_time - self.last_request_time
            if elapsed < self.min_request_interval:
                wait_time = self.min_request_interval - elapsed
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
                time.sleep(wait_time)

            # Execute request and update timestamp
            try:
                response = self.session.request(method, url, **kwargs)
                self.last_request_time = time.time()

                # Adjust request interval based on response status code
                if response.status_code == 429:  # Too Many Requests
                    logger.warning("Rate limit hit, increasing delay and retrying")
                    self.min_request_interval *= 2  # Exponential backoff
                    time.sleep(5)  # Additional wait
                    return self._rate_limited_request(method, url, **kwargs)  # Retry

                return response
            except requests.exceptions.SSLError as e:
                logger.error(f"SSL certificate verification error: {e}")
                error_msg = f"SSL certificate verification failed: {str(e)}\n"
                error_msg += "Possible solutions:\n"
                error_msg += "1. Check your proxy settings\n"
                error_msg += (
                    "2. Update your CA certificates: pip install --upgrade certifi\n"
                )
                error_msg += "3. If you trust this connection, use verify_ssl=False (not recommended)\n"
                error_msg += "4. Set a custom CA bundle: ca_bundle=path/to/cert.pem"
                raise APIError(error_msg)
            except requests.exceptions.ProxyError as e:
                logger.error(f"Proxy server error: {e}")
                error_msg = f"Proxy server connection failed: {str(e)}\n"
                error_msg += "Possible solutions:\n"
                error_msg += "1. Check if the proxy server is running\n"
                error_msg += "2. Verify the proxy address and port\n"
                error_msg += (
                    "3. Ensure the proxy server allows access to the target site\n"
                )
                error_msg += "4. Try using a different proxy server"
                raise APIError(error_msg)
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {e}")
                raise APIError(f"Unable to connect to API server: {str(e)}")
            except requests.exceptions.Timeout as e:
                logger.error(f"Request timeout: {e}")
                raise APIError(f"Request timeout: {str(e)}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception: {e}")
                raise APIError(f"Request failed: {str(e)}")

    def _process_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Process API response and handle errors.

        Args:
            response: HTTP response object

        Returns:
            JSON response data

        Raises:
            ResourceNotFoundError: When resource is not found
            AuthenticationError: When authentication fails
            RateLimitError: When rate limit is exceeded
            APIError: For other API errors
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.HTTPError:  # 移除未使用的 'e' 变量
            if response.status_code == 404:
                raise ResourceNotFoundError(f"Resource not found: {response.url}")
            elif response.status_code == 401:
                raise AuthenticationError("API authentication failed")
            elif response.status_code == 429:
                raise RateLimitError("API rate limit exceeded")
            else:
                error_msg = f"HTTP error {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg += f": {error_data['message']}"
                except ValueError:
                    error_msg += f": {response.text}"
                raise APIError(error_msg)
        except ValueError:
            raise APIError("Invalid JSON response")

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request to the API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            API response data
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        response = self._rate_limited_request(
            "GET", url, headers=self.headers, params=params
        )
        return self._process_response(response)

    def get_models(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get model listings.

        Args:
            params: Query parameters

        Returns:
            Model list data
        """
        return self.get("models", params)

    def get_model(self, model_id: int) -> Dict[str, Any]:
        """
        Get a specific model details.

        Args:
            model_id: Model ID

        Returns:
            Model details
        """
        return self.get(f"models/{model_id}")

    def get_model_version(self, version_id: int) -> Dict[str, Any]:
        """
        Get a specific model version details.

        Args:
            version_id: Model version ID

        Returns:
            Version details
        """
        return self.get(f"model-versions/{version_id}")

    def get_images(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get image listings.

        Args:
            params: Query parameters

        Returns:
            Image list data
        """
        return self.get("images", params)

    def get_all_images(
        self, base_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all images matching criteria, handling cursor pagination.

        Args:
            base_params: Base query parameters

        Returns:
            List of all image items
        """
        if base_params is None:
            base_params = {}

        results = []
        params = base_params.copy()

        while True:
            response = self.get_images(params)

            if "items" in response:
                results.extend(response["items"])

            # Handle cursor pagination
            if "metadata" in response and "nextCursor" in response["metadata"]:
                params["cursor"] = response["metadata"]["nextCursor"]
            else:
                break

        return results

    def get_download_url(self, version_id: int) -> str:
        """
        Get the download URL for a model version.

        Args:
            version_id: Model version ID

        Returns:
            Download URL
        """
        url = f"https://civitai.com/api/download/models/{version_id}"
        if self.api_key:
            url += f"?token={self.api_key}"
        return url

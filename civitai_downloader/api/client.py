"""Civitai API client implementation."""

import os
import time
import logging
import requests
from threading import Lock
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    pass


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
    ):
        """
        Initialize API client.

        Args:
            api_key: Civitai API key
            base_url: API base URL
        """
        self.api_key = api_key or os.environ.get("CIVITAI_API_KEY")
        self.base_url = base_url
        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

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
                response = requests.request(method, url, **kwargs)
                self.last_request_time = time.time()
            except requests.RequestException as e:
                raise APIError(f"Request failed: {str(e)}")

            # Handle rate limiting response
            if response.status_code == 429:
                logger.warning("Rate limit hit, increasing delay and retrying")
                self.min_request_interval *= 2
                time.sleep(5)
                return self._rate_limited_request(method, url, **kwargs)

            return response

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
        except requests.HTTPError as e:
            if response.status_code == 404:
                raise ResourceNotFoundError(f"Resource not found: {response.url}")
            elif response.status_code == 401:
                raise AuthenticationError("API authentication failed")
            elif response.status_code == 429:
                raise RateLimitError("API rate limit exceeded")
            else:
                raise APIError(f"API error: {str(e)}")
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

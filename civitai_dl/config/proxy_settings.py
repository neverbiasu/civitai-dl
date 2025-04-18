"""Proxy configuration module for network requests.

This module provides functions for configuring and managing HTTP proxy settings
for API requests and downloads. It handles environment variable integration,
CI environment detection, and default proxy configuration.
"""

import os
from typing import Dict, Optional

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)

# Default proxy settings
DEFAULT_PROXY = "http://127.0.0.1:7890"
DEFAULT_NO_PROXY = "localhost,127.0.0.1"


def is_ci_environment() -> bool:
    """Detect if running in a CI/CD environment.

    Returns:
        True if running in a CI environment, False otherwise
    """
    return (os.environ.get("CI") == "true" or
            os.environ.get("CI_TESTING") == "true" or
            os.environ.get("GITHUB_ACTIONS") == "true")


def get_proxy_settings() -> Dict[str, str]:
    """Get system proxy settings from environment or defaults.

    Checks environment variables for proxy settings and falls back to defaults.
    Disables proxies in CI environments or when explicitly requested.

    Returns:
        Dictionary with http/https proxy settings
    """
    proxy_settings = {}

    # Disable proxy in CI environment or when explicitly requested
    if (is_ci_environment() or
            os.environ.get("NO_PROXY") == "true" or
            os.environ.get("DISABLE_PROXY") == "true"):
        logger.debug("Proxy disabled due to environment settings")
        return {}

    # Try to get from environment variables first
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")

    # If not set in environment, use default settings
    if not http_proxy:
        http_proxy = DEFAULT_PROXY
        logger.debug(f"Using default HTTP proxy: {DEFAULT_PROXY}")
    else:
        logger.debug(f"Using HTTP proxy from environment: {http_proxy}")

    if not https_proxy:
        https_proxy = DEFAULT_PROXY
        logger.debug(f"Using default HTTPS proxy: {DEFAULT_PROXY}")
    else:
        logger.debug(f"Using HTTPS proxy from environment: {https_proxy}")

    proxy_settings["http"] = http_proxy
    proxy_settings["https"] = https_proxy

    return proxy_settings


def setup_proxy_environment() -> None:
    """Set proxy-related environment variables to default values.

    This ensures that other libraries that rely on environment variables
    for proxy configuration will use our default settings.
    """
    current_http = os.environ.get("HTTP_PROXY")
    current_https = os.environ.get("HTTPS_PROXY")

    if current_http:
        logger.debug(f"HTTP_PROXY already set to: {current_http}")
    else:
        os.environ["HTTP_PROXY"] = DEFAULT_PROXY
        logger.debug(f"Set HTTP_PROXY to: {DEFAULT_PROXY}")

    if current_https:
        logger.debug(f"HTTPS_PROXY already set to: {current_https}")
    else:
        os.environ["HTTPS_PROXY"] = DEFAULT_PROXY
        logger.debug(f"Set HTTPS_PROXY to: {DEFAULT_PROXY}")

    os.environ["NO_PROXY"] = DEFAULT_NO_PROXY
    logger.debug(f"Set NO_PROXY to: {DEFAULT_NO_PROXY}")


def get_verify_ssl() -> bool:
    """Determine whether SSL verification should be enabled.

    In some proxy environments, SSL verification may need to be disabled.
    This should be used with caution in production environments.

    Returns:
        Boolean indicating whether to verify SSL certificates
    """
    # Check environment variable for SSL verification setting
    ssl_verify = os.environ.get("VERIFY_SSL", "").lower()

    if ssl_verify in ("false", "0", "no"):
        logger.warning("SSL verification disabled by environment variable")
        return False

    if ssl_verify in ("true", "1", "yes"):
        return True

    # Default to True for security in production, False in development
    is_dev = os.environ.get("DEVELOPMENT_MODE", "").lower() in ("true", "1", "yes")
    result = not is_dev

    if not result:
        logger.warning("SSL verification disabled in development mode")

    return result


def get_proxy_for_url(url: str) -> Optional[Dict[str, str]]:
    """Get appropriate proxy settings for a specific URL.

    Some URLs may need different proxy settings or no proxy.

    Args:
        url: The URL to get proxy settings for

    Returns:
        Proxy dictionary or None if no proxy should be used
    """
    # Check if proxy should be bypassed for certain hosts
    no_proxy_list = os.environ.get("NO_PROXY", DEFAULT_NO_PROXY).split(",")

    for host in no_proxy_list:
        if host.strip() in url:
            logger.debug(f"Bypassing proxy for URL: {url}")
            return None

    # Use regular proxy settings
    return get_proxy_settings()

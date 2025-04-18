"""String formatting utilities for Civitai Downloader.

This module provides utilities for formatting strings, values, and displaying
information in a consistent manner throughout the application.
"""

import os
import re
from typing import Dict, Any, Union
from datetime import datetime

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


def format_file_size(size_bytes: Union[int, float], decimal_places: int = 2) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes
        decimal_places: Number of decimal places to show

    Returns:
        Formatted size string (e.g., "1.23 MB")
    """
    if size_bytes < 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0

    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024
        unit_index += 1

    return f"{size_bytes:.{decimal_places}f} {units[unit_index]}"


def format_timestamp(timestamp: Union[int, float], include_time: bool = True) -> str:
    """Format Unix timestamp as human-readable date/time.

    Args:
        timestamp: Unix timestamp
        include_time: Whether to include time or just the date

    Returns:
        Formatted date/time string
    """
    dt = datetime.fromtimestamp(timestamp)
    if include_time:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return dt.strftime("%Y-%m-%d")


def format_duration(seconds: Union[int, float]) -> str:
    """Format seconds as human-readable duration.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "2h 30m 15s")
    """
    if seconds < 0:
        return "0s"

    # Handle large values
    seconds = int(seconds)

    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Construct parts
    parts = []

    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or (hours > 0 and seconds > 0):
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def format_path_template(template: str, variables: Dict[str, Any]) -> str:
    """Format a path template with variables.

    Args:
        template: Path template with placeholders like {name}
        variables: Dictionary of variables to substitute

    Returns:
        Formatted path string
    """
    # Sanitize variables to ensure valid paths
    sanitized_vars = {}

    for key, value in variables.items():
        # Convert any non-string values to strings
        if not isinstance(value, str):
            value = str(value)

        # Replace characters that would cause path issues
        value = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", value)

        # Trim excessively long values
        if len(value) > 50:
            extension = ""
            if '.' in value[-10:]:  # Preserve file extension if present
                name, extension = os.path.splitext(value)
                value = name[:46] + "..." + extension
            else:
                value = value[:46] + "..."

        sanitized_vars[key] = value

    try:
        return template.format(**sanitized_vars)
    except KeyError as e:
        logger.warning(f"Missing key in template: {e}")
        # Fallback to partial formatting
        result = template
        for key, value in sanitized_vars.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, value)
        return result


def truncate_text(text: str, max_length: int = 80, ellipsis: str = "...") -> str:
    """Truncate text to specified length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length including ellipsis
        ellipsis: Ellipsis string to append

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    truncate_at = max_length - len(ellipsis)
    return text[:truncate_at] + ellipsis

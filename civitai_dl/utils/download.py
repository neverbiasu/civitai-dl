"""Download utility functions.

This module provides utility functions related to downloading operations,
separate from the core download engine.
"""

import os
import hashlib
from typing import Optional, Dict, List

from ..core.downloader import DownloadTask
from ..utils.logger import get_logger

logger = get_logger(__name__)


def calculate_download_hash(filepath: str, algorithm: str = 'sha256') -> Optional[str]:
    """Calculate hash of a downloaded file.

    Args:
        filepath: Path to the file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')

    Returns:
        Calculated hash string or None if calculation failed
    """
    if not os.path.exists(filepath):
        logger.warning(f"Cannot calculate hash, file does not exist: {filepath}")
        return None

    try:
        # Select hash algorithm
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha1':
            hash_obj = hashlib.sha1()
        else:  # Default to sha256
            hash_obj = hashlib.sha256()

        # Calculate hash in chunks to avoid loading large files into memory
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate file hash: {str(e)}")
        return None


def verify_download(filepath: str, expected_hash: Optional[str] = None, expected_size: Optional[int] = None) -> bool:
    """Verify that a downloaded file is complete and valid.

    Args:
        filepath: Path to the downloaded file
        expected_hash: Expected hash value (optional)
        expected_size: Expected file size in bytes (optional)

    Returns:
        True if file is valid, False otherwise
    """
    if not os.path.exists(filepath):
        logger.error(f"Cannot verify download, file does not exist: {filepath}")
        return False

    # Verify file size if expected size is provided
    if expected_size is not None:
        actual_size = os.path.getsize(filepath)
        if actual_size != expected_size:
            logger.warning(f"Size mismatch: expected {expected_size} bytes, got {actual_size} bytes")
            return False

    # Verify hash if expected hash is provided
    if expected_hash is not None:
        # Determine hash algorithm from hash length
        algorithm = 'sha256'  # Default
        if len(expected_hash) == 32:
            algorithm = 'md5'
        elif len(expected_hash) == 40:
            algorithm = 'sha1'

        actual_hash = calculate_download_hash(filepath, algorithm)
        if actual_hash is None:
            logger.error("Failed to calculate file hash")
            return False

        if actual_hash.lower() != expected_hash.lower():
            logger.warning(f"Hash mismatch: expected {expected_hash}, got {actual_hash}")
            return False

    return True


def get_download_status_summary(tasks: List[DownloadTask]) -> Dict[str, int]:
    """Get a summary of download tasks by status.

    Args:
        tasks: List of download tasks

    Returns:
        Dictionary with counts by status
    """
    status_count = {
        "pending": 0,
        "running": 0,
        "completed": 0,
        "failed": 0,
        "canceled": 0,
        "total": len(tasks)
    }

    for task in tasks:
        if task.status in status_count:
            status_count[task.status] += 1

    return status_count


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_speed(bytes_per_second: float) -> str:
    """Format download speed in human-readable format.

    Args:
        bytes_per_second: Speed in bytes per second

    Returns:
        Formatted speed string
    """
    if bytes_per_second < 1024:
        return f"{bytes_per_second:.1f} B/s"
    elif bytes_per_second < 1024 * 1024:
        return f"{bytes_per_second / 1024:.1f} KB/s"
    elif bytes_per_second < 1024 * 1024 * 1024:
        return f"{bytes_per_second / (1024 * 1024):.1f} MB/s"
    else:
        return f"{bytes_per_second / (1024 * 1024 * 1024):.2f} GB/s"


def format_time(seconds: int) -> str:
    """Format time in human-readable format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes}m {seconds}s"
    else:
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return f"{hours}h {minutes}m {seconds}s"

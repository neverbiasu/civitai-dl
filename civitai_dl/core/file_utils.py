"""File utility functions for Civitai Downloader.

This module provides file handling utilities including filename sanitization,
path management, and file conflict resolution.
"""

import os
import re
import hashlib
from typing import Optional, Tuple, Dict, Any
from urllib.parse import unquote

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)

# Constants for file handling
INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1F]'
MAX_FILENAME_LENGTH = 200


def get_download_location(model_info: Dict[str, Any], version_info: Dict[str, Any],
                          ask_location: Optional[bool] = None) -> str:
    """Determine download location based on model information.

    Args:
        model_info: Model information
        version_info: Version information
        ask_location: Whether to ask for download location, overrides config

    Returns:
        Download directory path
    """
    # Import config_manager lazily to avoid circular imports
    from civitai_dl.utils.config import get_download_dir, add_recent_directory, get_config_value

    # Prioritize parameter setting, otherwise use config
    if ask_location is None:
        ask_location = get_config_value("ask_download_location", False)

    # If asking for location is enabled, execute terminal query flow
    if ask_location:
        model_type = model_info.get("type")
        default_dir = get_download_dir(model_type)
        recent_dirs = get_config_value("recent_directories", [])

        if recent_dirs:
            print("Recent download directories:")
            for i, directory in enumerate(recent_dirs):
                print(f"{i+1}. {directory}")

        # Ask user for directory
        while True:
            import builtins
            response = builtins.input(
                f"Enter download directory [default: {default_dir}], enter number for recent dirs,  \
                or press Enter for default: ")

            # Empty input, use default
            if not response.strip():
                selected_dir = default_dir
                break

            # Try to parse as number to select recent directory
            if response.isdigit() and recent_dirs:
                index = int(response) - 1
                if 0 <= index < len(recent_dirs):
                    selected_dir = recent_dirs[index]
                    break
                else:
                    print(f"Invalid selection, please enter 1-{len(recent_dirs)}")
                    continue

            # Parse as path
            if os.path.isabs(response):
                selected_dir = response
                break
            else:
                # Convert relative path to absolute
                selected_dir = os.path.abspath(response)
                break

        # Create directory and add to recent directories
        os.makedirs(selected_dir, exist_ok=True)
        add_recent_directory(selected_dir)
        return selected_dir

    # Don't ask, use system setting
    model_type = model_info.get("type")
    return get_download_dir(model_type)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing illegal characters.

    Ensures filenames are safe for all operating systems by replacing illegal characters,
    trimming to legal length, and ensuring non-empty names.

    Args:
        filename: Original filename to sanitize

    Returns:
        Cleaned filename safe for all operating systems
    """
    if not filename:
        return "unnamed_file"

    # Replace invalid characters with underscores
    sanitized = re.sub(INVALID_CHARS, "_", filename)

    # Trim if filename exceeds maximum length (preserving extension)
    if len(sanitized) > MAX_FILENAME_LENGTH:
        name, ext = os.path.splitext(sanitized)
        max_name_length = MAX_FILENAME_LENGTH - len(ext)
        sanitized = name[:max_name_length] + ext
        logger.debug(f"Truncated filename to {MAX_FILENAME_LENGTH} characters")

    # Remove leading/trailing dots and spaces that cause issues
    sanitized = sanitized.strip(". ")

    # Ensure filename is not empty after cleaning
    if not sanitized:
        sanitized = "unnamed_file"

    # Log only if the filename was changed
    if sanitized != filename:
        logger.debug(f"Sanitized filename: '{filename}' → '{sanitized}'")

    return sanitized


def get_filename_from_model(model_info: Dict[str, Any], version_info: Dict[str, Any],
                            original_filename: Optional[str] = None) -> str:
    """Generate a filename from model information.

    Args:
        model_info: Model information dictionary
        version_info: Version information dictionary
        original_filename: Original filename (if available)

    Returns:
        Generated and sanitized filename
    """
    # Import config lazily to avoid circular imports
    from civitai_dl.utils.config import get_config_value

    # If configured to use original filename and it's provided, use it
    if get_config_value("use_original_filename", True) and original_filename:
        return sanitize_filename(original_filename)

    # Otherwise build an informative filename
    model_name = model_info.get("name", "unknown_model")
    model_type = model_info.get("type", "unknown_type")
    creator = model_info.get("creator", {}).get("username", "unknown_creator")
    version_name = version_info.get("name", "")

    # Construct filename
    if version_name:
        filename = f"{model_name}-{model_type}-{creator}-{version_name}"
    else:
        filename = f"{model_name}-{model_type}-{creator}"

    # Sanitize filename
    return sanitize_filename(filename)


def extract_filename_from_headers(headers: Dict[str, str]) -> Optional[str]:
    """Extract filename from HTTP response headers.

    Args:
        headers: HTTP response headers dictionary

    Returns:
        Extracted filename or None if not found
    """
    # Try to extract from Content-Disposition header
    if 'Content-Disposition' in headers:
        content_disposition = headers['Content-Disposition']
        filename_match = re.search(r'filename=["\']?([^"\';\n]+)', content_disposition)

        if filename_match:
            filename = filename_match.group(1)
            # Decode URL encoding
            filename = unquote(filename)
            # Handle quotes
            if filename.startswith('"') and filename.endswith('"'):
                filename = filename[1:-1]
            return filename

    # Could not extract filename
    return None


def resolve_file_conflict(filepath: str, action: Optional[str] = None) -> Tuple[str, bool]:
    """Resolve file conflicts when a file already exists.

    Args:
        filepath: File path that might have a conflict
        action: Conflict resolution action (overwrite/rename/skip), None to use config

    Returns:
        Tuple of (new_filepath, skip_flag) where skip_flag indicates if download should be skipped
    """
    if not os.path.exists(filepath):
        return filepath, False

    # If no action specified, use config default
    if action is None:
        # Import config lazily to avoid circular imports
        from civitai_dl.utils.config import get_config_value
        action = get_config_value("file_exists_action", "ask")

    # Ask user interactively
    if action == "ask":
        print(f"File already exists: {filepath}")
        while True:
            import builtins
            choice = builtins.input("Choose action: [o]verwrite [r]ename [s]kip: ").lower()
            if choice in ('o', 'overwrite'):
                action = "overwrite"
                break
            elif choice in ('r', 'rename'):
                action = "rename"
                break
            elif choice in ('s', 'skip'):
                action = "skip"
                break
            else:
                print("Invalid choice, please try again")

    # Handle conflict based on action
    if action == "overwrite":
        return filepath, False
    elif action == "skip":
        return filepath, True
    elif action == "rename":
        # Auto-generate new filename
        directory, filename = os.path.split(filepath)
        name, ext = os.path.splitext(filename)

        index = 1
        while True:
            new_filename = f"{name}_{index}{ext}"
            new_filepath = os.path.join(directory, new_filename)

            if not os.path.exists(new_filepath):
                return new_filepath, False

            index += 1
    else:
        # Default to rename if action is invalid
        return resolve_file_conflict(filepath, "rename")


def detect_duplicate_file(file_path: str, known_hashes: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Detect duplicate files based on content hash.

    Args:
        file_path: Path to file to check
        known_hashes: Dictionary of known file hashes {hash: file_path}

    Returns:
        Path to duplicate file if found, None otherwise
    """
    if not known_hashes or not os.path.exists(file_path):
        return None

    try:
        # Calculate file hash
        file_hash = calculate_file_hash(file_path)

        # Check if in known hashes
        if file_hash in known_hashes:
            return known_hashes[file_hash]
    except Exception as e:
        logger.warning(f"Failed to calculate file hash: {str(e)}")

    return None


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        SHA-256 hash as hex string
    """
    h = hashlib.sha256()

    with open(file_path, 'rb') as f:
        # Read file in chunks to handle large files efficiently
        chunk = f.read(8192)
        while chunk:
            h.update(chunk)
            chunk = f.read(8192)

    return h.hexdigest()


def verify_path_exists(path: str) -> bool:
    """Verify a path exists or can be created.

    Args:
        path: Path to verify

    Returns:
        True if path is valid and accessible, False otherwise
    """
    try:
        # If path already exists and is a directory, it's valid
        if os.path.exists(path) and os.path.isdir(path):
            return True

        # If it doesn't exist, try to create it
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            return True

        # If it exists but is not a directory, it's invalid
        return False
    except Exception as e:
        logger.error(f"Failed to verify path: {str(e)}")
        return False

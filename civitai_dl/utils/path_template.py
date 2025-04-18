"""Path template parsing and processing utilities.

This module provides functions for generating file paths from templates,
with variable substitution and safe path handling for different operating systems.
"""

import datetime
import os
import re
import string
import unicodedata
from typing import Any, Dict, Optional

from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


def parse_template(
    template: str, variables: Dict[str, Any], default_value: str = "unknown"
) -> str:
    """Parse a path template and substitute variables.

    Args:
        template: Template string containing variables, e.g. "{type}/{creator}/{name}"
        variables: Dictionary of variable values
        default_value: Default value for missing variables

    Returns:
        Path string with variables replaced
    """
    try:
        # Use string.Template for variable substitution
        # Convert {var} format to $var format first
        dollar_template = re.sub(r"\{([^}]+)\}", r"$\1", template)
        template_obj = string.Template(dollar_template)

        # Provide default values for missing variables
        safe_vars = SafeDict(variables, default_value)

        # Perform substitution
        result = template_obj.safe_substitute(safe_vars)

        # Clean the path (remove unsafe characters)
        result = sanitize_path(result)

        return result
    except Exception as e:
        logger.error(f"Failed to parse template: {str(e)}")
        # Return a simple path in case of error
        return datetime.datetime.now().strftime("%Y-%m-%d")


def sanitize_path(path: str) -> str:
    """Clean path string and remove unsafe characters.

    Args:
        path: Original path string

    Returns:
        Cleaned safe path string
    """
    # Normalize Unicode characters
    path = unicodedata.normalize("NFKD", path)

    # Replace characters not supported in Windows filenames
    invalid_chars = r'[<>:"/\\|?*]'
    path = re.sub(invalid_chars, "_", path)

    # Replace consecutive separators
    path = re.sub(r"_{2,}", "_", path)

    # Remove leading and trailing whitespace and path separators
    path = path.strip(" /")

    # Ensure each part of the path doesn't exceed 255 characters (Windows limit)
    parts = []
    for part in path.split("/"):
        if len(part) > 255:
            part = part[:252] + "..."
        parts.append(part)

    return "/".join(parts)


class SafeDict(dict):
    """Safe dictionary class that returns a default value when a key doesn't exist."""

    def __init__(self, data: Dict[str, Any], default_value: str):
        """Initialize safe dictionary with data and default value.

        Args:
            data: Dictionary of key-value pairs
            default_value: Value to return for missing keys
        """
        super().__init__(data)
        self.default = default_value

    def __missing__(self, key: str) -> str:
        """Handle missing keys by returning the default value.

        Args:
            key: The missing dictionary key

        Returns:
            Default value for missing keys
        """
        logger.debug(f"Template variable not found: {key}, using default: {self.default}")
        return self.default


def apply_model_template(
    template: str,
    model_info: Dict[str, Any],
    version_info: Optional[Dict[str, Any]] = None,
    file_info: Optional[Dict[str, Any]] = None,
) -> str:
    """Apply path template for model files.

    Args:
        template: Path template string
        model_info: Model information dictionary
        version_info: Version information dictionary (optional)
        file_info: File information dictionary (optional)

    Returns:
        Path generated from the template
    """
    variables = {}

    # Extract variables from model info
    if model_info:
        variables.update(
            {
                "type": model_info.get("type", "Unknown"),
                "name": model_info.get("name", "Unknown"),
                "id": model_info.get("id", 0),
                "nsfw": "nsfw" if model_info.get("nsfw", False) else "sfw",
            }
        )

        # Extract creator information
        creator = model_info.get("creator", {})
        if creator:
            variables["creator"] = creator.get("username", "Unknown")
            variables["creator_id"] = creator.get("id", 0)

    # Extract variables from version info
    if version_info:
        variables.update(
            {
                "version": version_info.get("name", "Unknown"),
                "version_id": version_info.get("id", 0),
                "base_model": version_info.get("baseModel", "Unknown"),
            }
        )

    # Extract variables from file info
    if file_info:
        filename = file_info.get("name", "Unknown")
        variables.update(
            {
                "filename": filename,
                "format": os.path.splitext(filename)[1][1:].lower()
                if "." in filename
                else "",
            }
        )

    # Add date variables
    now = datetime.datetime.now()
    variables.update(
        {
            "year": now.strftime("%Y"),
            "month": now.strftime("%m"),
            "day": now.strftime("%d"),
            "date": now.strftime("%Y-%m-%d"),
        }
    )

    # Sanitize all string values
    for k, v in list(variables.items()):
        if isinstance(v, str):
            variables[k] = sanitize_path(v)

    # Apply template
    try:
        path = template.format(**variables)
        # Normalize path separators
        return os.path.normpath(path)
    except KeyError as e:
        logger.warning(f"Template format error, using default template: {e}")
        # Use default template if unknown fields in template
        default_path = (
            f"{variables.get('type', 'Unknown')}/"
            f"{variables.get('creator', 'Unknown')}/"
            f"{variables.get('name', 'Unknown')}"
        )
        return os.path.normpath(default_path)


def apply_image_template(
    template: str, model_id: int, image_info: Dict[str, Any]
) -> str:
    """Apply path template for image files.

    Args:
        template: Path template, e.g. "images/{model_id}/{hash}"
        model_id: Model ID
        image_info: Image information dictionary

    Returns:
        Relative path generated from the template
    """
    # Extract fields available for the template
    fields = {
        "model_id": model_id,
        "image_id": image_info.get("id", 0),
        "hash": image_info.get("hash", "unknown"),
        "width": image_info.get("width", 0),
        "height": image_info.get("height", 0),
        "nsfw": "nsfw" if image_info.get("nsfw", False) else "sfw",
    }

    # Extract generation parameters from metadata
    meta = image_info.get("meta", {})
    if isinstance(meta, dict):
        # Create a deterministic hash from the prompt if available
        prompt = meta.get("prompt", "")
        if prompt:
            # Use a simple hash function for the prompt
            fields["prompt_hash"] = abs(hash(prompt)) % 10000
        else:
            fields["prompt_hash"] = 0

    # Sanitize all string values
    for k, v in list(fields.items()):
        if isinstance(v, str):
            fields[k] = sanitize_path(v)

    # Apply template
    try:
        path = template.format(**fields)
        # Normalize path separators
        return os.path.normpath(path)
    except KeyError as e:
        logger.warning(f"Image template format error, using default template: {e}")
        # Use default template if unknown fields in template
        default_path = f"images/model_{model_id}/{fields['image_id']}"
        return os.path.normpath(default_path)

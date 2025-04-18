"""API client redirection module for backwards compatibility.

This module redirects imports to the new API client location in the api package.
It is maintained for backwards compatibility with code that imports from the
original location.
"""

from civitai_dl.api.client import APIError, CivitaiAPI

# Export all symbols for backwards compatibility
__all__ = ["CivitaiAPI", "APIError"]

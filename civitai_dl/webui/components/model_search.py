"""Model search component for Civitai Downloader WebUI.

This module provides functionality for searching and browsing models on Civitai,
with support for various filtering and sorting options.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging

from civitai_dl.api.client import CivitaiAPI
from civitai_dl.core.downloader import DownloadEngine
from civitai_dl.utils.config import get_config
from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


class ModelSearcher:
    """Model search component that provides model search and browsing functionality.
    
    This component interacts with the Civitai API to search for models using various
    criteria and filters, and manages search results for display and download.
    """

    def __init__(self, api: CivitaiAPI, downloader: DownloadEngine):
        """Initialize the model searcher.
        
        Args:
            api: Configured Civitai API client
            downloader: Download engine for handling downloads
        """
        self.api = api
        self.downloader = downloader
        self.config = get_config()
        self.current_results = []  # Current search results
        self.last_search_params = {}  # Last used search parameters

    def search_models(
        self,
        query: str = "",
        model_types: Optional[List[str]] = None,
        sort: str = "Highest Rated",
        nsfw: bool = False,
        page: int = 1,
        page_size: int = 20,
        tags: Optional[List[str]] = None,
        creator: Optional[str] = None,
        base_model: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for models on Civitai using specified criteria.

        Args:
            query: Search keyword
            model_types: List of model types to include
            sort: Sort method for results
            nsfw: Whether to include NSFW content
            page: Page number for pagination
            page_size: Number of results per page
            tags: List of tags to filter by
            creator: Creator username to filter by
            base_model: Base model to filter by
            additional_params: Additional API parameters

        Returns:
            Dictionary containing search results and metadata
        """
        try:
            # Build API parameters
            params = {
                "query": query if query else None,
                "types": model_types,
                "sort": sort,
                "nsfw": str(nsfw).lower(),
                "page": page,
                "limit": page_size,
            }
            
            # Add optional parameters if provided
            if tags:
                params["tag"] = tags[0] if len(tags) == 1 else None  # API only supports one tag
            if creator:
                params["username"] = creator
            if base_model:
                params["baseModel"] = base_model
                
            # Add any additional parameters
            if additional_params:
                params.update(additional_params)
                
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            # Save search parameters for potential reuse
            self.last_search_params = params.copy()
            
            # Execute search via API
            logger.info(f"Searching models with params: {params}")
            response = self.api.get_models(params)
            
            # Process and format results
            models = response.get("items", [])
            formatted_results = []
            
            for model in models:
                # Extract key information
                model_id = model.get("id")
                name = model.get("name", "Unknown")
                model_type = model.get("type", "Unknown")
                creator = model.get("creator", {}).get("username", "Unknown")
                download_count = model.get("stats", {}).get("downloadCount", 0)
                rating = model.get("stats", {}).get("rating", 0)
                
                # Format for display
                formatted_results.append([
                    model_id, name, model_type, creator, download_count, rating
                ])
            
            # Store results for later use
            self.current_results = formatted_results
            
            # Return with metadata
            metadata = response.get("metadata", {})
            return {
                "data": formatted_results,
                "total": metadata.get("totalItems", len(formatted_results)),
                "page": metadata.get("currentPage", page),
                "total_pages": metadata.get("totalPages", 1)
            }

        except Exception as e:
            logger.error(f"Error searching models: {str(e)}", exc_info=True)
            return {
                "data": [],
                "error": str(e),
                "total": 0,
                "page": page,
                "total_pages": 1
            }

    def get_model_details(self, model_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific model.
        
        Args:
            model_id: Civitai model ID
            
        Returns:
            Dictionary containing detailed model information
        """
        try:
            return self.api.get_model(model_id)
        except Exception as e:
            logger.error(f"Error getting model details for ID {model_id}: {str(e)}")
            return {"error": str(e)}

    def download_selected(self, selected_indices: List[int]) -> str:
        """Download models selected from search results.

        Args:
            selected_indices: List of indices in current results to download

        Returns:
            Status message describing the operation result
        """
        if not selected_indices or not self.current_results:
            return "No models selected or no search results available"

        try:
            # Filter to valid selected models
            selected_models = [
                self.current_results[i]
                for i in selected_indices
                if 0 <= i < len(self.current_results)
            ]
            
            if not selected_models:
                return "No valid models selected"
                
            # Extract model IDs
            model_ids = [model[0] for model in selected_models]
            
            # Queue downloads
            download_tasks = []
            
            for model_id in model_ids:
                try:
                    # Get model details
                    model_details = self.get_model_details(model_id)
                    
                    if "error" in model_details:
                        logger.warning(f"Skipping model {model_id}: {model_details['error']}")
                        continue
                    
                    # Get latest version
                    versions = model_details.get("modelVersions", [])
                    
                    if not versions:
                        logger.warning(f"Model {model_id} has no versions available")
                        continue
                        
                    latest_version = versions[0]  # First version is the latest
                    version_id = latest_version.get("id")
                    
                    # Get download URL
                    download_url = self.api.get_download_url(version_id)
                    
                    if not download_url:
                        logger.warning(f"No download URL available for model {model_id}, version {version_id}")
                        continue
                    
                    # Start download
                    task = self.downloader.download(
                        url=download_url,
                        # Additional parameters can be added here
                    )
                    
                    download_tasks.append(task)
                    
                except Exception as e:
                    logger.error(f"Error setting up download for model {model_id}: {str(e)}")
            
            # Summarize operation
            if download_tasks:
                return f"Started downloading {len(download_tasks)} models: {', '.join(map(str, model_ids))}"
            else:
                return "No downloads were started. Check logs for details."

        except Exception as e:
            logger.error(f"Error downloading selected models: {str(e)}", exc_info=True)
            return f"Error downloading selected models: {str(e)}"

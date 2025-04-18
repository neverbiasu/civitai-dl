"""Image browser component for Civitai Downloader WebUI.

Provides functionality for browsing, previewing, and downloading images from
Civitai model pages and galleries.
"""

import os
import json
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, unquote

from civitai_dl.api.client import CivitaiAPI
from civitai_dl.core.downloader import DownloadEngine
from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


class ImageDownloader:
    """Component for searching, browsing and downloading images from Civitai."""

    def __init__(self, api: CivitaiAPI, download_engine: DownloadEngine) -> None:
        """Initialize the image downloader component.

        Args:
            api: Civitai API client instance
            download_engine: Download engine for handling downloads
        """
        self.api = api
        self.download_engine = download_engine
        self.current_images: List[Dict[str, Any]] = []
        self.gallery_urls: List[str] = []

    def search_images(
        self,
        model_id: int,
        version_id: Optional[int] = None,
        nsfw_filter: str = "排除NSFW",
        gallery: bool = False,
        limit: int = 10
    ) -> List[str]:
        """Search for images for a model or version.

        Args:
            model_id: Model ID to search for
            version_id: Optional specific version ID
            nsfw_filter: NSFW filtering option ("排除NSFW", "包含NSFW", "仅NSFW")
            gallery: Whether to include community gallery images
            limit: Maximum number of images to return

        Returns:
            List of image URLs for display in gallery
        """
        logger.info(f"Searching images for model {model_id}, version {version_id}")

        # Reset current state
        self.current_images = []
        self.gallery_urls = []

        try:
            # Convert NSFW filter option
            include_nsfw = nsfw_filter in ["包含NSFW", "仅NSFW"]
            only_nsfw = nsfw_filter == "仅NSFW"

            # First get version-specific images if a version is specified
            if version_id:
                version_images = self.api.get_version_images(version_id)

                # Filter by NSFW preference
                filtered_images = []
                for img in version_images:
                    is_nsfw = img.get("nsfw", False)
                    if only_nsfw and is_nsfw:
                        filtered_images.append(img)
                    elif not only_nsfw and (include_nsfw or not is_nsfw):
                        filtered_images.append(img)

                self.current_images.extend(filtered_images[:limit])

            # If we need more images and gallery option is enabled
            remaining = limit - len(self.current_images)
            if gallery and remaining > 0:
                # Get gallery images
                params = {
                    "modelId": model_id,
                    "limit": remaining,
                    "nsfw": str(include_nsfw).lower()
                }

                if version_id:
                    params["modelVersionId"] = version_id

                gallery_response = self.api.get_images(params)
                gallery_images = gallery_response.get("items", [])

                # Filter by NSFW preference
                filtered_gallery = []
                for img in gallery_images:
                    is_nsfw = img.get("nsfw", False)
                    if only_nsfw and is_nsfw:
                        filtered_gallery.append(img)
                    elif not only_nsfw and (include_nsfw or not is_nsfw):
                        filtered_gallery.append(img)

                self.current_images.extend(filtered_gallery)

            # Extract URLs for the gallery
            self.gallery_urls = [img.get("url", "") for img in self.current_images if img.get("url")]

            logger.info(f"Found {len(self.gallery_urls)} images")
            return self.gallery_urls

        except Exception as e:
            logger.error(f"Error searching images: {str(e)}")
            return []

    def get_image_metadata(self, index: int) -> Dict[str, Any]:
        """Get metadata for an image by index.

        Args:
            index: Index of the image in the current results

        Returns:
            Image metadata dictionary
        """
        if 0 <= index < len(self.current_images):
            return self.current_images[index]

        return {"error": "Image index out of range"}

    def download_images(
        self,
        model_id: int,
        version_id: Optional[int] = None,
        nsfw_filter: str = "排除NSFW",
        gallery: bool = False,
        limit: int = 10,
        output_dir: Optional[str] = None
    ) -> str:
        """Download images for a model.

        Args:
            model_id: Model ID
            version_id: Optional version ID
            nsfw_filter: NSFW filtering option
            gallery: Whether to include community gallery
            limit: Maximum images to download
            output_dir: Custom output directory

        Returns:
            Status message about the download
        """
        # If no current images, perform search first
        if not self.current_images:
            self.search_images(model_id, version_id, nsfw_filter, gallery, limit)

        if not self.current_images:
            return "No images found to download"

        # Determine output directory
        if not output_dir:
            version_str = f"_v{version_id}" if version_id else ""
            folder_name = f"model_{model_id}{version_str}_images"
            output_dir = os.path.join(self.download_engine.output_dir, "images", folder_name)

        # Create directory
        os.makedirs(output_dir, exist_ok=True)

        # Start downloads
        download_count = 0
        tasks = []

        for i, image in enumerate(self.current_images[:limit]):
            url = image.get("url")
            if not url:
                continue

            # Create filename from URL
            parsed_url = urlparse(url)
            filename = os.path.basename(unquote(parsed_url.path))
            if not filename or not os.path.splitext(filename)[1]:
                filename = f"image_{model_id}_{i+1}.jpg"

            # Prefix with index for ordering
            filename = f"{i+1:03d}_{filename}"

            # Start download task
            task = self.download_engine.download(
                url=url,
                output_path=output_dir,
                filename=filename,
                use_range=False,  # Images don't usually need range requests
                verify=self.api.verify,
                proxy=self.api.proxy,
                timeout=self.api.timeout,
                completion_callback=self._create_metadata_callback(image, output_dir, filename)
            )

            tasks.append(task)
            download_count += 1

        if download_count > 0:
            return f"Started downloading {download_count} images to {output_dir}"
        else:
            return "No images were queued for download"

    def _create_metadata_callback(self, image: Dict[str, Any],
                                  output_dir: str, filename: str) -> callable:
        """Create a callback to save image metadata after download.

        Args:
            image: Image metadata dictionary
            output_dir: Output directory
            filename: Image filename

        Returns:
            Callback function for the download task
        """
        def save_metadata_callback(task):
            if task.status == "completed":
                try:
                    # Save metadata JSON alongside the image
                    meta_path = os.path.join(output_dir, os.path.splitext(filename)[0] + ".meta.json")
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump(image, f, indent=2, ensure_ascii=False)
                    logger.debug(f"Saved metadata to {meta_path}")
                except Exception as e:
                    logger.error(f"Failed to save image metadata: {str(e)}")

        return save_metadata_callback

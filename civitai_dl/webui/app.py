"""Web UI application for Civitai Downloader."""

import os
from typing import Dict, Any

import gradio as gr

from civitai_dl import __version__
from civitai_dl.api.client import CivitaiAPI
from civitai_dl.core.downloader import DownloadEngine
from civitai_dl.utils.config import get_config
from civitai_dl.utils.logger import get_logger
from civitai_dl.webui.components.filter_builder import FilterBuilder
from civitai_dl.webui.components.image_browser import ImageDownloader
from civitai_dl.webui.callbacks import setup_callbacks

# Configure logger
logger = get_logger(__name__)


def create_app() -> gr.Blocks:
    """Create and configure the WebUI application.

    Creates the Gradio interface with tabs for model downloading, searching,
    image browsing, download queue management, and application settings.

    Returns:
        Configured Gradio Blocks application
    """
    config = get_config()
    api = CivitaiAPI(
        api_key=config.get("api_key"),
        proxy=config.get("proxy"),
        verify=config.get("verify_ssl", True),
        timeout=config.get("timeout", 30),
        max_retries=config.get("max_retries", 3),
    )
    download_engine = DownloadEngine(
        output_dir=config.get("output_dir", "./downloads"),
        concurrent_downloads=config.get("concurrent_downloads", 3),
    )

    # Create image downloader instance
    image_downloader = ImageDownloader(api, download_engine)

    # Dictionary to store download tasks
    download_tasks: Dict[str, Any] = {}

    # Setup callbacks
    callbacks = setup_callbacks(api, download_engine, image_downloader, config, download_tasks)

    with gr.Blocks(
        title=f"Civitai Downloader v{__version__}", theme=gr.themes.Soft()
    ) as app:
        # Top header and navigation
        with gr.Row():
            gr.Markdown(f"# Civitai Downloader v{__version__}")

        # Main content area with tabs
        with gr.Tabs() as tabs:
            # ===== Download Model Tab =====
            with gr.Tab("Download Model"):
                with gr.Row():
                    with gr.Column(scale=1):
                        model_id = gr.Number(label="Model ID", precision=0, minimum=1)
                        version_id = gr.Number(
                            label="Version ID (Optional)", precision=0, minimum=1
                        )
                        output_dir = gr.Textbox(
                            label="Output Directory",
                            value=config.get(
                                "output_dir", os.path.join(os.getcwd(), "downloads")
                            ),
                        )
                        with_images = gr.Checkbox(label="Download Sample Images", value=True)
                        image_limit = gr.Slider(
                            minimum=0,
                            maximum=20,
                            step=1,
                            value=5,
                            label="Image Limit (0 for no limit)",
                        )
                        download_btn = gr.Button("Download", variant="primary")

                    with gr.Column(scale=1):
                        status = gr.Textbox(label="Status", interactive=False)
                        progress = gr.Slider(
                            minimum=0,
                            maximum=100,
                            value=0,
                            step=0.1,
                            label="Download Progress",
                            interactive=False,
                        )

            # ===== Model Search Tab =====
            with gr.Tab("Model Search"):
                with gr.Row():
                    with gr.Column(scale=1):
                        search_query = gr.Textbox(label="Keywords")
                        model_types = gr.Dropdown(
                            choices=[
                                "Checkpoint",
                                "LORA",
                                "TextualInversion",
                                "Hypernetwork",
                                "AestheticGradient",
                                "Controlnet",
                                "Poses",
                            ],
                            label="Model Type",
                            multiselect=True,
                        )
                        sort_options = gr.Dropdown(
                            choices=[
                                "Highest Rated",
                                "Most Downloaded",
                                "Newest",
                            ],
                            label="Sort By",
                            value="Highest Rated",
                        )
                        nsfw = gr.Checkbox(label="Include NSFW", value=False)
                        search_btn = gr.Button("Search")

                    with gr.Column(scale=2):
                        results = gr.Dataframe(
                            headers=["ID", "Name", "Type", "Creator", "Downloads", "Rating"],
                            label="Search Results",
                            interactive=False,
                        )

                # Search results action area
                with gr.Row():
                    download_selected_btn = gr.Button("Download Selected", interactive=False)
                    refresh_btn = gr.Button("Refresh", interactive=True)

                # Help text
                gr.Markdown(
                    """
                > **Note**: The model search function is under development. Currently showing sample data. Full functionality will be available in future versions.
                """
                )

                # Advanced filter components
                filter_builder = FilterBuilder()
                (filter_accordion, current_filter, apply_filter_btn,
                 save_template_btn, load_template_btn) = filter_builder.create_ui()

                filter_builder.setup_callbacks(
                    (filter_accordion, current_filter, apply_filter_btn,
                     save_template_btn, load_template_btn),
                    api,
                    on_preview=callbacks["on_preview_filter"],
                    on_apply=lambda filter_condition: callbacks["update_results"](
                        callbacks["on_apply_filter"](filter_condition)
                    )
                )

                search_btn.click(
                    fn=callbacks["on_search"],
                    inputs=[search_query, model_types, sort_options, nsfw],
                    outputs=[results],
                )

                apply_filter_btn.click(
                    fn=lambda: None,  # Actual handling in setup_callbacks
                    inputs=[],
                    outputs=[results],
                )

            # ===== Image Download Tab =====
            with gr.Tab("Image Download"):
                with gr.Row():
                    with gr.Column(scale=1):
                        image_model_id = gr.Number(label="Model ID", precision=0, minimum=1)
                        image_version_id = gr.Number(
                            label="Version ID (Optional)", precision=0, minimum=1
                        )
                        nsfw_filter = gr.Radio(
                            choices=["Exclude NSFW", "Include NSFW", "NSFW Only"],
                            label="NSFW Filter",
                            value="Exclude NSFW",
                        )
                        gallery_option = gr.Checkbox(label="Community Gallery", value=False)
                        image_limit_slider = gr.Slider(
                            minimum=5, maximum=50, step=5, value=10, label="Max Images"
                        )
                        search_images_btn = gr.Button("Get Images")

                    with gr.Column(scale=2):
                        image_gallery = gr.Gallery(
                            label="Image Preview", show_label=True, columns=3, rows=3, height=600
                        )

                # Image details and actions
                with gr.Row():
                    download_images_btn = gr.Button("Download All Images")
                    image_metadata = gr.JSON(label="Image Metadata")

            # ===== Settings Tab =====
            with gr.Tab("Settings"):
                with gr.Accordion("Basic Settings", open=True):
                    api_key = gr.Textbox(
                        label="Civitai API Key",
                        value=config.get("api_key", ""),
                        type="password",
                    )
                    proxy = gr.Textbox(
                        label="Proxy (e.g. http://127.0.0.1:7890)",
                        value=config.get("proxy", ""),
                    )
                    theme = gr.Radio(
                        choices=["Light", "Dark"],
                        label="Theme",
                        value="Light" if config.get("theme") == "light" else "Dark",
                    )

                with gr.Accordion("Download Settings"):
                    default_output = gr.Textbox(
                        label="Default Download Path", value=config.get("output_dir", "./downloads")
                    )
                    concurrent = gr.Slider(
                        minimum=1,
                        maximum=10,
                        step=1,
                        value=config.get("concurrent_downloads", 3),
                        label="Concurrent Downloads",
                    )
                    chunk_size = gr.Slider(
                        minimum=1024,
                        maximum=1024 * 32,
                        step=1024,
                        value=config.get("chunk_size", 8192),
                        label="Chunk Size (bytes)",
                    )

                with gr.Accordion("Path Settings"):
                    model_template = gr.Textbox(
                        label="Model Path Template",
                        value=config.get("path_template", "{type}/{creator}/{name}"),
                    )
                    image_template = gr.Textbox(
                        label="Image Path Template",
                        value=config.get(
                            "image_path_template", "images/{model_id}/{image_id}"
                        ),
                    )
                    gr.Markdown(
                        """
                    **Available Variables:**
                    - Model: `{type}`, `{name}`, `{id}`, `{creator}`, `{version}`, `{base_model}`
                    - Image: `{model_id}`, `{image_id}`, `{hash}`, `{width}`, `{height}`, `{nsfw}`
                    """
                    )

                with gr.Accordion("Advanced Settings"):
                    timeout = gr.Slider(
                        minimum=5,
                        maximum=120,
                        step=5,
                        value=config.get("timeout", 30),
                        label="Request Timeout (s)",
                    )
                    max_retries = gr.Slider(
                        minimum=0,
                        maximum=10,
                        step=1,
                        value=config.get("max_retries", 3),
                        label="Max Retries",
                    )
                    verify_ssl = gr.Checkbox(
                        label="Verify SSL", value=config.get("verify_ssl", True)
                    )

                with gr.Row():
                    save_settings_btn = gr.Button("Save Settings", variant="primary")
                    gr.Button("Export Settings")
                    gr.Button("Import Settings")
                    settings_status = gr.Textbox(label="Status", interactive=False)

        # Footer information
        with gr.Row():
            gr.Markdown(
                "Civitai Downloader | "
                "[Project URL](https://github.com/neverbiasu/civitai-dl) | "
                "[Issues](https://github.com/neverbiasu/civitai-dl/issues)"
            )

        # Connect event handlers
        download_btn.click(
            fn=callbacks["on_download"],
            inputs=[model_id, version_id, output_dir, with_images, image_limit],
            outputs=[status, progress],
        )

        search_images_btn.click(
            fn=callbacks["on_image_search"],
            inputs=[
                image_model_id,
                image_version_id,
                nsfw_filter,
                gallery_option,
                image_limit_slider,
            ],
            outputs=[image_gallery, image_metadata],
        )

        # Add image selection event handler
        image_gallery.select(fn=callbacks["on_image_selected"], inputs=None, outputs=image_metadata)

        download_images_btn.click(
            fn=callbacks["on_download_images"],
            inputs=[
                image_model_id,
                image_version_id,
                nsfw_filter,
                gallery_option,
                image_limit_slider,
            ],
            outputs=[image_metadata],
        )

        save_settings_btn.click(
            fn=callbacks["save_settings"],
            inputs=[
                api_key,
                proxy,
                theme,
                default_output,
                concurrent,
                chunk_size,
                model_template,
                image_template,
                timeout,
                max_retries,
                verify_ssl,
            ],
            outputs=[settings_status],
        )

        def update_progress() -> None:
            """Deprecated: background progress updates are now handled by callbacks.

            This function is kept for backward compatibility but intentionally
            performs no work and does not start any background thread.
            """
            logger.debug("update_progress() called; background progress thread is deprecated.")

        # Note: Background progress thread is deprecated and no longer started
        # Progress updates are now handled via callbacks

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch()

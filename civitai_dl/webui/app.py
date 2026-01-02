"""Web UI application for Civitai Downloader."""

import os
import time
from threading import Thread
from typing import Dict, Any, List

import gradio as gr

from civitai_dl import __version__
from civitai_dl.api.client import CivitaiAPI
from civitai_dl.core.downloader import DownloadEngine
from civitai_dl.utils.config import get_config
from civitai_dl.utils.logger import get_logger
from civitai_dl.webui.components.filter_builder import FilterBuilder
from civitai_dl.webui.components.image_browser import ImageDownloader
from civitai_dl.webui.callbacks import setup_callbacks

# 设置日志记录器
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
            with gr.Tab("下载模型"):
                with gr.Row():
                    with gr.Column(scale=1):
                        model_id = gr.Number(label="模型ID", precision=0, minimum=1)
                        version_id = gr.Number(
                            label="版本ID (可选)", precision=0, minimum=1
                        )
                        output_dir = gr.Textbox(
                            label="输出目录",
                            value=config.get(
                                "output_dir", os.path.join(os.getcwd(), "downloads")
                            ),
                        )
                        with_images = gr.Checkbox(label="同时下载示例图像", value=True)
                        image_limit = gr.Slider(
                            minimum=0,
                            maximum=20,
                            step=1,
                            value=5,
                            label="图像下载数量 (0表示不限制)",
                        )
                        download_btn = gr.Button("下载", variant="primary")

                    with gr.Column(scale=1):
                        status = gr.Textbox(label="状态", interactive=False)
                        progress = gr.Slider(
                            minimum=0,
                            maximum=100,
                            value=0,
                            step=0.1,
                            label="下载进度",
                            interactive=False,
                        )

            # ===== Model Search Tab =====
            with gr.Tab("模型搜索"):
                with gr.Row():
                    with gr.Column(scale=1):
                        search_query = gr.Textbox(label="搜索关键词")
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
                            label="模型类型",
                            multiselect=True,
                        )
                        sort_options = gr.Dropdown(
                            choices=[
                                "Highest Rated",
                                "Most Downloaded",
                                "Newest",
                            ],
                            label="排序方式",
                            value="Highest Rated",
                        )
                        nsfw = gr.Checkbox(label="包含NSFW内容", value=False)
                        search_btn = gr.Button("搜索")

                    with gr.Column(scale=2):
                        results = gr.Dataframe(
                            headers=["ID", "名称", "类型", "创作者", "下载量", "评分"],
                            label="搜索结果",
                            interactive=False,
                        )

                # Search results action area
                with gr.Row():
                    download_selected_btn = gr.Button("下载选中模型", interactive=False)
                    refresh_btn = gr.Button("刷新", interactive=True)

                # Help text
                gr.Markdown(
                    """
                > **注意**: 模型搜索功能正在开发中，目前展示的是示例数据。完整功能将在后续版本中提供。
                """
                )

                # Advanced filter components
                filter_builder = FilterBuilder()
                filter_accordion, current_filter, apply_filter_btn, save_template_btn, load_template_btn = filter_builder.create_ui()

                filter_builder.setup_callbacks(
                    (filter_accordion, current_filter, apply_filter_btn, save_template_btn, load_template_btn),
                    api,
                    on_preview=callbacks["on_preview_filter"],
                    on_apply=lambda filter_condition: callbacks["update_results"](callbacks["on_apply_filter"](filter_condition))
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
            with gr.Tab("图像下载"):
                with gr.Row():
                    with gr.Column(scale=1):
                        image_model_id = gr.Number(label="模型ID", precision=0, minimum=1)
                        image_version_id = gr.Number(
                            label="版本ID (可选)", precision=0, minimum=1
                        )
                        nsfw_filter = gr.Radio(
                            choices=["排除NSFW", "包含NSFW", "仅NSFW"],
                            label="NSFW过滤",
                            value="排除NSFW",
                        )
                        gallery_option = gr.Checkbox(label="社区画廊图像", value=False)
                        image_limit_slider = gr.Slider(
                            minimum=5, maximum=50, step=5, value=10, label="最大图像数量"
                        )
                        search_images_btn = gr.Button("获取图像")

                    with gr.Column(scale=2):
                        image_gallery = gr.Gallery(
                            label="图像预览", show_label=True, columns=3, rows=3, height=600
                        )

                # Image details and actions
                with gr.Row():
                    download_images_btn = gr.Button("下载所有图像")
                    image_metadata = gr.JSON(label="图像元数据")

            # ===== Settings Tab =====
            with gr.Tab("设置"):
                with gr.Accordion("基本设置", open=True):
                    api_key = gr.Textbox(
                        label="Civitai API密钥",
                        value=config.get("api_key", ""),
                        type="password",
                    )
                    proxy = gr.Textbox(
                        label="代理设置 (e.g. http://127.0.0.1:7890)",
                        value=config.get("proxy", ""),
                    )
                    theme = gr.Radio(
                        choices=["亮色", "暗色"],
                        label="界面主题",
                        value="亮色" if config.get("theme") == "light" else "暗色",
                    )

                with gr.Accordion("下载设置"):
                    default_output = gr.Textbox(
                        label="默认下载路径", value=config.get("output_dir", "./downloads")
                    )
                    concurrent = gr.Slider(
                        minimum=1,
                        maximum=10,
                        step=1,
                        value=config.get("concurrent_downloads", 3),
                        label="并行下载任务数",
                    )
                    chunk_size = gr.Slider(
                        minimum=1024,
                        maximum=1024 * 32,
                        step=1024,
                        value=config.get("chunk_size", 8192),
                        label="下载分块大小(bytes)",
                    )

                with gr.Accordion("路径设置"):
                    model_template = gr.Textbox(
                        label="模型路径模板",
                        value=config.get("path_template", "{type}/{creator}/{name}"),
                    )
                    image_template = gr.Textbox(
                        label="图像路径模板",
                        value=config.get(
                            "image_path_template", "images/{model_id}/{image_id}"
                        ),
                    )
                    gr.Markdown(
                        """
                    **可用的模板变量:**
                    - 模型: `{type}`, `{name}`, `{id}`, `{creator}`, `{version}`, `{base_model}`
                    - 图像: `{model_id}`, `{image_id}`, `{hash}`, `{width}`, `{height}`, `{nsfw}`
                    """
                    )

                with gr.Accordion("高级设置"):
                    timeout = gr.Slider(
                        minimum=5,
                        maximum=120,
                        step=5,
                        value=config.get("timeout", 30),
                        label="请求超时(秒)",
                    )
                    max_retries = gr.Slider(
                        minimum=0,
                        maximum=10,
                        step=1,
                        value=config.get("max_retries", 3),
                        label="最大重试次数",
                    )
                    verify_ssl = gr.Checkbox(
                        label="验证SSL证书", value=config.get("verify_ssl", True)
                    )

                with gr.Row():
                    save_settings_btn = gr.Button("保存设置", variant="primary")
                    gr.Button("导出设置")
                    gr.Button("导入设置")
                    settings_status = gr.Textbox(label="设置状态", interactive=False)

        # Footer information
        with gr.Row():
            gr.Markdown(
                "Civitai Downloader | [项目地址](https://github.com/neverbiasu/civitai-dl) | [问题反馈](https://github.com/neverbiasu/civitai-dl/issues)"
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
            """Periodically update download progress."""
            while True:
                # Sleep for 1 second
                time.sleep(1)

                # Get the first active download task
                active_task = None
                for task_id, task in download_tasks.items():
                    if task.status == "downloading":
                        active_task = task
                        break

                if active_task:
                    pass

        # Start progress update thread
        Thread(target=update_progress, daemon=True).start()

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch()

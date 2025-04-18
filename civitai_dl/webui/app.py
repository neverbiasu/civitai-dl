"""Web UI application for Civitai Downloader."""

import json
import os
import time
from threading import Thread
from typing import Dict, Any, List, Optional, Tuple, Union, Callable

import gradio as gr

from civitai_dl import __version__
from civitai_dl.api.client import CivitaiAPI
from civitai_dl.core.downloader import DownloadEngine
from civitai_dl.core.filter import FilterParser, apply_filter
from civitai_dl.utils.config import get_config, set_config_value
from civitai_dl.utils.logger import get_logger
from civitai_dl.webui.components.filter_builder import FilterBuilder
from civitai_dl.webui.components.image_browser import ImageDownloader

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

                # Set up filter callbacks
                def on_preview_filter(filter_condition: Dict[str, Any]) -> str:
                    """Preview filter results count.
                    
                    Args:
                        filter_condition: Filter condition to preview
                        
                    Returns:
                        String describing matching models count
                    """
                    try:
                        api_params = FilterParser.to_api_params(filter_condition)
                        api_params["limit"] = 1
                        response = api.get_models(api_params)
                        count = response.get("metadata", {}).get("totalItems", 0)
                        return f"符合条件的模型数量: {count}"
                    except Exception as e:
                        return f"预览失败: {str(e)}"

                def on_apply_filter(filter_condition: Dict[str, Any]) -> List[List[Any]]:
                    """Apply filter and return matching models.
                    
                    Args:
                        filter_condition: Filter condition to apply
                        
                    Returns:
                        List of model data rows for display
                    """
                    try:
                        api_params = FilterParser.to_api_params(filter_condition)
                        api_params["limit"] = 50
                        response = api.get_models(api_params)
                        models = response.get("items", [])

                        # Apply client-side filtering
                        filtered_models = apply_filter(models, filter_condition)

                        # Convert to table data
                        table_data = [
                            [
                                model.get("id", ""),
                                model.get("name", ""),
                                model.get("type", ""),
                                model.get("creator", {}).get("username", ""),
                                model.get("stats", {}).get("downloadCount", 0),
                                model.get("stats", {}).get("rating", 0),
                            ]
                            for model in filtered_models
                        ]

                        return table_data
                    except Exception as e:
                        gr.Warning(f"搜索失败: {str(e)}")
                        return []

                filter_builder.setup_callbacks(
                    (filter_accordion, current_filter, apply_filter_btn, save_template_btn, load_template_btn),
                    api,
                    on_preview=on_preview_filter,
                    on_apply=lambda filter_condition: update_results(on_apply_filter(filter_condition))
                )

                def update_results(data: List[List[Any]]) -> List[List[Any]]:
                    """Update results display.
                    
                    Args:
                        data: New table data
                        
                    Returns:
                        Updated table data
                    """
                    return data

                # Basic search button callback
                def on_search(query: str, types: List[str], sort: str, nsfw_enabled: bool) -> List[List[Any]]:
                    """Search models with basic parameters.
                    
                    Args:
                        query: Search query string
                        types: Model type filters
                        sort: Sort method
                        nsfw_enabled: Whether to include NSFW content
                        
                    Returns:
                        Search results as table data
                    """
                    try:
                        params = {}
                        if query:
                            params["query"] = query
                        if types:
                            params["types"] = types
                        if sort:
                            params["sort"] = sort
                        if not nsfw_enabled:
                            params["nsfw"] = "false"
                        params["limit"] = 50

                        response = api.get_models(params)
                        models = response.get("items", [])

                        # Convert to table data
                        table_data = [
                            [
                                model.get("id", ""),
                                model.get("name", ""),
                                model.get("type", ""),
                                model.get("creator", {}).get("username", ""),
                                model.get("stats", {}).get("downloadCount", 0),
                                model.get("stats", {}).get("rating", 0),
                            ]
                            for model in models
                        ]

                        return table_data
                    except Exception as e:
                        gr.Warning(f"搜索失败: {str(e)}")
                        return []

                search_btn.click(
                    fn=on_search,
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

            # ===== Download Queue Tab =====
            with gr.Tab("下载队列"):
                with gr.Row():
                    queue_table = gr.Dataframe(
                        headers=["任务ID", "类型", "名称", "状态", "进度", "速度", "剩余时间"],
                        label="当前下载队列",
                        interactive=False,
                    )

                with gr.Row():
                    gr.Button("全部暂停")
                    gr.Button("全部恢复")
                    gr.Button("全部取消")
                    gr.Button("刷新队列")

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

        # == Callback functions ==
        def on_download(model_id: int, version_id: Optional[int], output_dir: str, 
                       with_images: bool, image_limit: int) -> Tuple[str, float]:
            """Handle model download request.
            
            Args:
                model_id: Civitai model ID
                version_id: Specific version ID (optional)
                output_dir: Directory to save files
                with_images: Whether to download example images
                image_limit: Maximum number of images to download
                
            Returns:
                Status message and initial progress value
            """
            if not model_id:
                return "请输入有效的模型ID", 0

            try:
                # Get model information
                model_info = api.get_model(model_id)
                if not model_info:
                    return f"错误: 未找到ID为{model_id}的模型", 0

                # Get version information
                versions = model_info.get("modelVersions", [])
                if not versions:
                    return f"错误: 模型 {model_info.get('name')} 没有可用版本", 0

                target_version = None
                if version_id:
                    for v in versions:
                        if v.get("id") == version_id:
                            target_version = v
                            break
                    if not target_version:
                        return f"错误: 未找到ID为{version_id}的版本", 0
                else:
                    target_version = versions[0]

                # Get file information
                files = target_version.get("files", [])
                if not files:
                    return f"错误: 版本 {target_version.get('name')} 没有可用文件", 0

                # Select primary file (prioritize primary-marked files)
                target_file = next(
                    (f for f in files if f.get("primary", False)), files[0]
                )

                # Build download URL
                download_url = api.get_download_url(target_version.get("id"))

                if not download_url:
                    return f"错误: 无法获取下载链接", 0

                # Set output path
                if not output_dir:
                    output_dir = config.get("output_dir", "./downloads")

                # Log download info for debugging
                print(
                    f"正在下载模型: {model_info.get('name')} - {target_version.get('name')}"
                )
                print(f"下载URL: {download_url}")
                print(f"输出目录: {output_dir}")
                print(f"使用代理: {api.proxy}")
                print(f"API Key设置: {'已设置' if api.api_key else '未设置'}")

                # Create download task
                task_id = f"model_{model_id}_{int(time.time())}"
                download_tasks[task_id] = download_engine.download(
                    url=download_url,
                    output_path=output_dir,
                    filename=target_file.get("name"),
                    headers=api.build_headers(),
                    use_range=True,
                    verify=api.verify,
                    proxy=api.proxy,
                    timeout=api.timeout,
                )

                # If downloading example images
                if with_images and image_limit > 0:
                    # Create thread to download images
                    Thread(
                        target=download_model_images,
                        args=(
                            api,
                            download_engine,
                            model_id,
                            target_version.get("id"),
                            image_limit,
                            output_dir,
                        ),
                        daemon=True,
                    ).start()

                return (
                    f"开始下载: {model_info.get('name')} - {target_version.get('name')}",
                    0,
                )

            except Exception as e:
                return f"下载出错: {str(e)}", 0

        def download_model_images(
            api: CivitaiAPI, 
            downloader: DownloadEngine, 
            model_id: int, 
            version_id: int, 
            limit: int, 
            output_dir: str
        ) -> None:
            """Background task to download model example images.
            
            Args:
                api: API client
                downloader: Download engine
                model_id: Model ID
                version_id: Version ID
                limit: Maximum images to download
                output_dir: Directory to save images
            """
            try:
                # Get version images
                images = api.get_version_images(version_id)
                if not images:
                    print(f"版本 {version_id} 没有示例图像")
                    return

                # Limit number of images
                images = images[:limit]

                # Create save directory
                folder_name = f"model_{model_id}_examples_v{version_id}"
                image_dir = os.path.join(output_dir, "images", folder_name)
                os.makedirs(image_dir, exist_ok=True)

                print(f"开始下载 {len(images)} 张示例图像到 {image_dir}")

                # Download images
                for i, image in enumerate(images):
                    image_url = image.get("url")
                    if not image_url:
                        continue

                    # Build filename
                    filename = f"{model_id}_{i+1}_{os.path.basename(image_url)}"
                    if not os.path.splitext(filename)[1]:  # Ensure extension exists
                        filename += ".jpg"

                    # Start download
                    try:
                        task = downloader.download(
                            url=image_url,
                            output_path=image_dir,
                            filename=filename,
                            use_range=False,
                            verify=api.verify,
                            proxy=api.proxy,
                            timeout=api.timeout,
                        )

                        # Wait for completion
                        task.wait()

                        # Process metadata after download success
                        if task.status == "completed":
                            try:
                                from civitai_dl.utils.metadata import (
                                    extract_image_metadata,
                                )

                                # Extract and save metadata
                                image_path = os.path.join(image_dir, filename)
                                metadata = extract_image_metadata(image_path)
                                if metadata:
                                    # Add API metadata
                                    api_meta = {
                                        "id": image.get("id"),
                                        "model_id": model_id,
                                        "version_id": version_id,
                                        "nsfw": image.get("nsfw", False),
                                        "width": image.get("width"),
                                        "height": image.get("height"),
                                        "hash": image.get("hash"),
                                        "meta": image.get("meta"),
                                    }
                                    metadata.update(api_meta)

                                    # Save metadata
                                    metadata_path = (
                                        os.path.splitext(image_path)[0] + ".meta.json"
                                    )
                                    with open(
                                        metadata_path, "w", encoding="utf-8"
                                    ) as f:
                                        json.dump(
                                            metadata, f, indent=2, ensure_ascii=False
                                        )
                            except Exception as e:
                                print(f"保存图像元数据失败: {e}")

                    except Exception as e:
                        print(f"下载图像 {filename} 失败: {e}")

                print(f"示例图像下载完成")

            except Exception as e:
                print(f"下载示例图像时出错: {e}")

        def on_image_search(model_id: int, version_id: Optional[int], 
                           nsfw_filter: str, gallery: bool, limit: int) -> Tuple[List[str], Dict[str, Any]]:
            """Handle image search request.
            
            Args:
                model_id: Model ID
                version_id: Version ID (optional)
                nsfw_filter: NSFW filter setting
                gallery: Whether to include community gallery
                limit: Maximum number of images
                
            Returns:
                List of image URLs and metadata object
            """
            if not model_id:
                return [], {"error": "请输入有效的模型ID"}

            try:
                # Use ImageDownloader to get images
                gallery_images = image_downloader.search_images(
                    model_id=model_id,
                    version_id=version_id,
                    nsfw_filter=nsfw_filter,
                    gallery=gallery,
                    limit=limit,
                )

                # If no images found
                if not gallery_images:
                    return [], {
                        "status": "warning",
                        "message": "未找到符合条件的图像",
                        "params": {
                            "model_id": model_id,
                            "version_id": version_id,
                            "nsfw_filter": nsfw_filter,
                            "gallery": gallery,
                            "limit": limit,
                        },
                    }

                # Return images and empty metadata (will be filled by image selection)
                return gallery_images, {}
            except Exception as e:
                return [], {"error": f"获取图像出错: {str(e)}"}

        def on_image_selected(evt: gr.SelectData, index: Optional[int] = None) -> Dict[str, Any]:
            """Handle image selection event.
            
            Args:
                evt: Selection event data
                index: Optional explicitly provided index
                
            Returns:
                Image metadata
            """
            try:
                # Get index from event or parameter
                selected_index = evt.index if hasattr(evt, "index") else index
                if selected_index is None:
                    return {"error": "未能获取选择的图像索引"}

                # Get metadata from ImageDownloader
                metadata = image_downloader.get_image_metadata(selected_index)
                return metadata
            except Exception as e:
                import traceback
                traceback.print_exc()
                return {"error": f"获取图像元数据失败: {str(e)}"}

        def on_download_images(model_id: int, version_id: Optional[int],
                              nsfw_filter: str, gallery: bool, limit: int) -> Dict[str, Any]:
            """Handle image download request.
            
            Args:
                model_id: Model ID
                version_id: Version ID (optional)
                nsfw_filter: NSFW filter setting
                gallery: Whether to include community gallery
                limit: Maximum number of images
                
            Returns:
                Download result status
            """
            if not model_id:
                return {"error": "请输入有效的模型ID"}

            try:
                # Use ImageDownloader to download images
                result = image_downloader.download_images(
                    model_id=model_id,
                    version_id=version_id,
                    nsfw_filter=nsfw_filter,
                    gallery=gallery,
                    limit=limit,
                )

                # Return download result
                return {"status": "success", "message": result}
            except Exception as e:
                return {"error": f"下载图像时出错: {str(e)}"}

        def save_settings(
            api_key: str,
            proxy: str,
            theme: str,
            output_dir: str,
            concurrent: int,
            chunk_size: int,
            model_template: str,
            image_template: str,
            timeout: int,
            max_retries: int,
            verify_ssl: bool,
        ) -> str:
            """Save application settings.
            
            Args:
                api_key: Civitai API key
                proxy: Proxy server address
                theme: UI theme
                output_dir: Default download directory
                concurrent: Number of concurrent downloads
                chunk_size: Download chunk size
                model_template: Model path template
                image_template: Image path template
                timeout: Request timeout
                max_retries: Maximum retry attempts
                verify_ssl: Whether to verify SSL certificates
                
            Returns:
                Status message
            """
            try:
                # Convert theme option
                theme_value = "light" if theme == "亮色" else "dark"

                # Update configuration
                set_config_value("api_key", api_key)
                set_config_value("proxy", proxy)
                set_config_value("theme", theme_value)
                set_config_value("output_dir", output_dir)
                set_config_value("concurrent_downloads", int(concurrent))
                set_config_value("chunk_size", int(chunk_size))
                set_config_value("path_template", model_template)
                set_config_value("image_path_template", image_template)
                set_config_value("timeout", int(timeout))
                set_config_value("max_retries", int(max_retries))
                set_config_value("verify_ssl", verify_ssl)

                # Update API and download engine configuration
                api.api_key = api_key
                api.proxy = proxy
                api.timeout = int(timeout)
                api.max_retries = int(max_retries)
                api.verify = verify_ssl

                download_engine.output_dir = output_dir
                download_engine.concurrent_downloads = int(concurrent)

                return "设置已保存"

            except Exception as e:
                return f"保存设置失败: {str(e)}"

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
                    # Calculate progress percentage
                    progress_value = (
                        (active_task.downloaded / active_task.total) * 100
                        if active_task.total
                        else 0
                    )
                    status_text = f"下载中: {active_task.filename} - {progress_value:.1f}%"

                    # Update UI via Gradio's queue (simplified for example)
                    # In real implementation, needs more complex mechanism

        # Connect event handlers
        download_btn.click(
            fn=on_download,
            inputs=[model_id, version_id, output_dir, with_images, image_limit],
            outputs=[status, progress],
        )

        search_images_btn.click(
            fn=on_image_search,
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
        image_gallery.select(fn=on_image_selected, inputs=None, outputs=image_metadata)

        download_images_btn.click(
            fn=on_download_images,
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
            fn=save_settings,
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

        # Start progress update thread
        Thread(target=update_progress, daemon=True).start()

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch()

"""Callbacks for the WebUI application."""

import os
import time
import json
from threading import Thread
from typing import Dict, Any, List, Optional, Tuple

import gradio as gr
from civitai_dl.api.client import CivitaiAPI
from civitai_dl.core.downloader import DownloadEngine
from civitai_dl.core.filter import FilterParser, apply_filter
from civitai_dl.utils.config import set_config_value
from civitai_dl.webui.components.image_browser import ImageDownloader

def setup_callbacks(
    api: CivitaiAPI,
    download_engine: DownloadEngine,
    image_downloader: ImageDownloader,
    config: Dict[str, Any],
    download_tasks: Dict[str, Any]
):
    """Setup and return all callbacks."""

    def on_download(model_id: int, version_id: Optional[int], output_dir: str,
                    with_images: bool, image_limit: int) -> Tuple[str, float]:
        if not model_id:
            return "请输入有效的模型ID", 0

        try:
            model_info = api.get_model(model_id)
            if not model_info:
                return f"错误: 未找到ID为{model_id}的模型", 0

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

            files = target_version.get("files", [])
            if not files:
                return f"错误: 版本 {target_version.get('name')} 没有可用文件", 0

            target_file = next(
                (f for f in files if f.get("primary", False)), files[0]
            )

            download_url = api.get_download_url(target_version.get("id"))

            if not download_url:
                return f"错误: 无法获取下载链接", 0

            if not output_dir:
                output_dir = config.get("output_dir", "./downloads")

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

            if with_images and image_limit > 0:
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
        try:
            images = api.get_version_images(version_id)
            if not images:
                return

            images = images[:limit]
            folder_name = f"model_{model_id}_examples_v{version_id}"
            image_dir = os.path.join(output_dir, "images", folder_name)
            os.makedirs(image_dir, exist_ok=True)

            for i, image in enumerate(images):
                image_url = image.get("url")
                if not image_url:
                    continue

                filename = f"{model_id}_{i+1}_{os.path.basename(image_url)}"
                if not os.path.splitext(filename)[1]:
                    filename += ".jpg"

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
                    task.wait()

                    if task.status == "completed":
                        try:
                            from civitai_dl.utils.metadata import (
                                extract_image_metadata,
                            )
                            image_path = os.path.join(image_dir, filename)
                            metadata = extract_image_metadata(image_path)
                            if metadata:
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
                                metadata_path = (
                                    os.path.splitext(image_path)[0] + ".meta.json"
                                )
                                with open(
                                    metadata_path, "w", encoding="utf-8"
                                ) as f:
                                    json.dump(
                                        metadata, f, indent=2, ensure_ascii=False
                                    )
                        except Exception:
                            pass

                except Exception:
                    pass

        except Exception:
            pass

    def on_image_search(model_id: int, version_id: Optional[int],
                        nsfw_filter: str, gallery: bool, limit: int) -> Tuple[List[str], Dict[str, Any]]:
        if not model_id:
            return [], {"error": "请输入有效的模型ID"}

        try:
            gallery_images = image_downloader.search_images(
                model_id=model_id,
                version_id=version_id,
                nsfw_filter=nsfw_filter,
                gallery=gallery,
                limit=limit,
            )

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

            return gallery_images, {}
        except Exception as e:
            return [], {"error": f"获取图像出错: {str(e)}"}

    def on_image_selected(evt: gr.SelectData, index: Optional[int] = None) -> Dict[str, Any]:
        try:
            selected_index = evt.index if hasattr(evt, "index") else index
            if selected_index is None:
                return {"error": "未能获取选择的图像索引"}

            metadata = image_downloader.get_image_metadata(selected_index)
            return metadata
        except Exception as e:
            return {"error": f"获取图像元数据失败: {str(e)}"}

    def on_download_images(model_id: int, version_id: Optional[int],
                           nsfw_filter: str, gallery: bool, limit: int) -> Dict[str, Any]:
        if not model_id:
            return {"error": "请输入有效的模型ID"}

        try:
            result = image_downloader.download_images(
                model_id=model_id,
                version_id=version_id,
                nsfw_filter=nsfw_filter,
                gallery=gallery,
                limit=limit,
            )
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
        try:
            theme_value = "light" if theme == "亮色" else "dark"

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

    def on_preview_filter(filter_condition: Dict[str, Any]) -> str:
        try:
            api_params = FilterParser.to_api_params(filter_condition)
            api_params["limit"] = 1
            response = api.get_models(api_params)
            count = response.get("metadata", {}).get("totalItems", 0)
            return f"符合条件的模型数量: {count}"
        except Exception as e:
            return f"预览失败: {str(e)}"

    def on_apply_filter(filter_condition: Dict[str, Any]) -> List[List[Any]]:
        try:
            api_params = FilterParser.to_api_params(filter_condition)
            api_params["limit"] = 50
            response = api.get_models(api_params)
            models = response.get("items", [])
            filtered_models = apply_filter(models, filter_condition)
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

    def on_search(query: str, types: List[str], sort: str, nsfw_enabled: bool) -> List[List[Any]]:
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

    def update_results(data: List[List[Any]]) -> List[List[Any]]:
        return data

    return {
        "on_download": on_download,
        "on_image_search": on_image_search,
        "on_image_selected": on_image_selected,
        "on_download_images": on_download_images,
        "save_settings": save_settings,
        "on_preview_filter": on_preview_filter,
        "on_apply_filter": on_apply_filter,
        "on_search": on_search,
        "update_results": update_results
    }

import json
import os
from typing import Dict, List, Optional

from civitai_dl.api.client import CivitaiAPI
from civitai_dl.core.downloader import DownloadEngine
from civitai_dl.utils.config import get_config
from civitai_dl.utils.metadata import extract_image_metadata


class ImageDownloader:
    """图像下载器组件，提供图像搜索和下载功能"""

    def __init__(self, api: CivitaiAPI, downloader: DownloadEngine):
        """初始化图像下载器"""
        self.api = api
        self.downloader = downloader
        self.config = get_config()
        self.current_images = []  # 当前显示的图像列表

    def search_images(
        self,
        model_id: int,
        version_id: Optional[int] = None,
        nsfw_filter: str = "排除NSFW",
        gallery: bool = False,
        limit: int = 10,
    ) -> List[Dict]:
        """
        搜索模型的图像

        Args:
            model_id: 模型ID
            version_id: 版本ID（可选）
            nsfw_filter: NSFW过滤选项
            gallery: 是否获取社区画廊图像
            limit: 返回结果数量限制

        Returns:
            图像列表
        """
        try:
            # 转换NSFW过滤选项
            include_nsfw = False
            if nsfw_filter == "包含NSFW":
                include_nsfw = True
            elif nsfw_filter == "仅NSFW":
                include_nsfw = "only"

            # 根据gallery参数调用不同的API
            if gallery:
                images = self.api.get_model_images(
                    model_id=model_id,
                    version_id=version_id,
                    limit=limit,
                    nsfw=include_nsfw,
                )
            else:
                if version_id:
                    # 获取版本图像 - 注意：不传入limit参数
                    images = self.api.get_version_images(version_id)
                    # 手动限制结果数量
                    images = images[:limit] if images else []
                else:
                    # 先获取模型信息，再获取最新版本的图像
                    model_info = self.api.get_model(model_id)
                    if not model_info or "modelVersions" not in model_info:
                        return []

                    versions = model_info.get("modelVersions", [])
                    if not versions:
                        return []

                    # 获取最新版本的图像
                    latest_version_id = versions[0].get("id")
                    images = self.api.get_version_images(latest_version_id)
                    # 手动限制结果数量
                    images = images[:limit] if images else []

            # 过滤NSFW内容（如果API没有正确处理）
            if nsfw_filter == "排除NSFW":
                images = [img for img in images if not img.get("nsfw", False)]
            elif nsfw_filter == "仅NSFW":
                images = [img for img in images if img.get("nsfw", False)]

            # 保存当前图像列表
            self.current_images = images

            # 转换为Gradio Gallery可用的格式
            gallery_images = []
            for img in images:
                url = img.get("url")
                if url:
                    # 提取元信息作为标题
                    meta = img.get("meta", {})
                    prompt = (
                        meta.get("prompt", "无提示词") if isinstance(meta, dict) else "无元数据"
                    )
                    # 截取长提示词
                    if len(prompt) > 100:
                        prompt = prompt[:97] + "..."

                    # 添加到画廊
                    gallery_images.append((url, prompt))

            return gallery_images

        except Exception as e:
            print(f"搜索图像时出错: {e}")
            import traceback

            traceback.print_exc()
            return []

    def get_image_metadata(self, selected_index: int) -> Dict:
        """
        获取选中图像的元数据

        Args:
            selected_index: 选中的图像索引

        Returns:
            图像元数据
        """
        try:
            if 0 <= selected_index < len(self.current_images):
                image = self.current_images[selected_index]
                # 提取API返回的元数据
                metadata = {
                    "id": image.get("id"),
                    "width": image.get("width"),
                    "height": image.get("height"),
                    "nsfw": image.get("nsfw", False),
                    "hash": image.get("hash", ""),
                    "meta": image.get("meta", {}),
                    "stats": {
                        "downloadCount": image.get("stats", {}).get("downloadCount", 0),
                        "favoriteCount": image.get("stats", {}).get("favoriteCount", 0),
                        "commentCount": image.get("stats", {}).get("commentCount", 0),
                    },
                }
                return metadata
            return {"message": "无效的图像索引"}
        except Exception as e:
            import traceback

            traceback.print_exc()
            return {"error": f"获取元数据失败: {str(e)}"}

    def download_images(
        self,
        model_id: int,
        version_id: Optional[int] = None,
        gallery: bool = False,
        nsfw_filter: str = "排除NSFW",
        limit: int = 10,
    ) -> str:
        """
        下载模型的图像

        Args:
            model_id: 模型ID
            version_id: 版本ID（可选）
            gallery: 是否下载社区画廊图像
            nsfw_filter: NSFW过滤选项
            limit: 下载数量限制

        Returns:
            下载结果信息
        """
        try:
            # 转换NSFW过滤选项
            if nsfw_filter == "包含NSFW":
                pass
            elif nsfw_filter == "仅NSFW":
                pass

            # 获取图像列表（如果尚未获取）
            if not self.current_images:
                self.search_images(model_id, version_id, nsfw_filter, gallery, limit)

            if not self.current_images:
                return "未找到可下载的图像"

            # 创建保存目录
            folder_name = f"model_{model_id}_{'gallery' if gallery else 'examples'}"
            if version_id:
                folder_name += f"_v{version_id}"

            output_dir = os.path.join(
                self.config.get("output_dir", "./downloads"), "images", folder_name
            )
            os.makedirs(output_dir, exist_ok=True)

            # 开始下载
            download_count = 0
            for i, image in enumerate(self.current_images[:limit]):
                image_url = image.get("url")
                if not image_url:
                    continue

                # 构建文件名
                filename = f"{model_id}_{i+1}_{os.path.basename(image_url)}"
                if not os.path.splitext(filename)[1]:  # 确保有扩展名
                    filename += ".jpg"

                # 开始下载
                task = self.downloader.download(
                    url=image_url, output_path=output_dir, filename=filename
                )

                # 等待下载完成
                task.wait()
                if task.status == "completed":
                    download_count += 1

                    # 提取和保存元数据
                    try:
                        image_path = os.path.join(output_dir, filename)
                        metadata = extract_image_metadata(image_path)
                        if metadata:
                            # 添加API元数据
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
                            # 合并元数据
                            metadata.update(api_meta)

                            # 保存元数据
                            metadata_path = (
                                os.path.splitext(image_path)[0] + ".meta.json"
                            )
                            with open(metadata_path, "w", encoding="utf-8") as f:
                                json.dump(metadata, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        print(f"保存图像元数据失败: {e}")

            return f"成功下载 {download_count}/{len(self.current_images[:limit])} 张图像到 {output_dir}"

        except Exception as e:
            return f"下载图像时出错: {e}"

import os
import gradio as gr
import time
from typing import List, Optional

from civitai_dl.api import CivitaiAPI
from civitai_dl.core.downloader import DownloadEngine
from civitai_dl.utils.config import get_config
from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


class DownloadPage:
    """下载页面组件"""

    def __init__(self, api: CivitaiAPI):
        self.api = api
        self.config = get_config()
        self.output_dir = self.config.get("output_dir", "./downloads")
        # 使用DownloadEngine替代DownloadManager
        self.download_engine = DownloadEngine(
            output_dir=self.output_dir,
            concurrent_downloads=self.config.get("concurrent_downloads", 3)
        )
        self.active_tasks = {}  # 追踪活动的下载任务

    def build(self) -> gr.Blocks:
        """构建下载页面UI"""
        with gr.Blocks() as download_page:
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("## 模型下载")

                    # 模型下载表单
                    with gr.Group():
                        model_id = gr.Number(label="模型ID", precision=0)
                        version_id = gr.Number(label="版本ID (可选)", precision=0)
                        output_path = gr.Textbox(label="保存路径", value=self.output_dir)
                        with_images = gr.Checkbox(label="同时下载示例图像", value=True)

                        download_btn = gr.Button("下载模型", variant="primary")

                    # 下载状态显示
                    download_status = gr.Markdown("准备就绪")

                with gr.Column(scale=1):
                    gr.Markdown("## 当前下载")

                    # 下载任务列表
                    tasks_dataframe = gr.Dataframe(
                        headers=["任务", "状态", "进度", "文件大小", "速度"],
                        row_count=5,
                        col_count=(5, "fixed"),
                        interactive=False
                    )

                    # 刷新和取消按钮
                    with gr.Row():
                        refresh_btn = gr.Button("刷新状态")
                        cancel_btn = gr.Button("取消所有", variant="stop")

            # 设置事件处理
            download_btn.click(
                fn=self.handle_download,
                inputs=[model_id, version_id, output_path, with_images],
                outputs=[download_status]
            )

            refresh_btn.click(
                fn=self.refresh_tasks,
                outputs=[tasks_dataframe]
            )

            cancel_btn.click(
                fn=self.cancel_all_tasks,
                outputs=[download_status, tasks_dataframe]
            )

            # 定期自动刷新
            download_page.load(lambda: None).then(
                lambda: gr.update(value=self.refresh_tasks_periodically()),
                None,
                tasks_dataframe,
                every=2
            )

        return download_page

    def handle_download(self, model_id: int, version_id: Optional[int],
                        output_path: str, with_images: bool) -> str:
        """处理模型下载请求"""
        try:
            if not model_id:
                return "错误: 请提供有效的模型ID"

            # 获取模型信息
            model_info = self.api.get_model(model_id)
            if not model_info:
                return f"错误: 找不到模型 {model_id} 或无法获取模型信息"

            # 确定版本
            versions = model_info.get("modelVersions", [])
            if not versions:
                return f"错误: 模型 {model_id} 没有可用版本"

            target_version = None
            if version_id:
                for v in versions:
                    if v["id"] == version_id:
                        target_version = v
                        break
                if not target_version:
                    return f"错误: 找不到指定的版本ID: {version_id}"
            else:
                target_version = versions[0]  # 使用最新版本

            # 获取文件信息
            files = target_version.get("files", [])
            if not files:
                return f"错误: 版本 {target_version.get('id')} 没有可用文件"

            target_file = files[0]  # 使用第一个文件

            # 确保目标路径存在
            if not os.path.exists(output_path):
                os.makedirs(output_path, exist_ok=True)

            # 显示下载信息
            model_name = model_info.get("name", f"模型 {model_id}")
            download_url = target_file["downloadUrl"]

            # 直接使用DownloadEngine下载
            task = self.download_engine.download(
                url=download_url,
                output_path=output_path,
                filename=target_file["name"]
            )

            # 将任务添加到活动任务列表
            task_id = f"model_{model_id}_{int(time.time())}"
            self.active_tasks[task_id] = {
                "task": task,
                "type": "model",
                "name": model_name,
                "version": target_version.get("name"),
                "start_time": time.time()
            }

            # 如果需要下载图像
            if with_images:
                self.download_model_images(model_id, target_version.get("id"), output_path)

            return f"开始下载: {model_name} ({target_version.get('name')})"

        except Exception as e:
            logger.exception("模型下载失败")
            return f"下载失败: {str(e)}"

    def download_model_images(self, model_id: int, version_id: int, output_path: str):
        """下载模型相关图像"""
        try:
            # 获取版本的示例图像
            images = self.api.get_version_images(version_id)
            if not images:
                logger.warning(f"模型版本 {version_id} 没有示例图像")
                return

            # 创建图像子目录
            images_dir = os.path.join(output_path, f"model_{model_id}_images")
            os.makedirs(images_dir, exist_ok=True)

            # 下载前5张图像
            for i, image in enumerate(images[:5]):
                image_url = image.get("url")
                if not image_url:
                    continue

                # 构建文件名
                filename = f"{model_id}_{i+1}_{os.path.basename(image_url)}"
                if not os.path.splitext(filename)[1]:
                    filename += ".jpg"

                # 下载图像
                task = self.download_engine.download(
                    url=image_url,
                    output_path=images_dir,
                    filename=filename,
                    use_range=False  # 图像通常不需要断点续传
                )

                # 将任务添加到活动任务列表
                task_id = f"image_{model_id}_{i}_{int(time.time())}"
                self.active_tasks[task_id] = {
                    "task": task,
                    "type": "image",
                    "name": f"示例图像 {i+1}",
                    "version": f"模型 {model_id}",
                    "start_time": time.time()
                }

        except Exception as e:
            logger.exception("下载模型图像失败")

    def refresh_tasks(self) -> List[List[str]]:
        """刷新任务状态并返回任务列表"""
        # 移除已完成的任务
        current_time = time.time()
        tasks_to_remove = []
        for task_id, task_info in self.active_tasks.items():
            task = task_info["task"]
            # 如果任务已完成/失败且超过30秒，从列表中移除
            if task.status in ["completed", "failed"] and current_time - task_info.get("end_time", current_time) > 30:
                tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.active_tasks[task_id]

        # 更新和返回任务列表
        results = []
        for task_id, task_info in self.active_tasks.items():
            task = task_info["task"]

            # 如果任务刚完成，记录结束时间
            if task.status in ["completed", "failed"] and "end_time" not in task_info:
                task_info["end_time"] = time.time()

            # 计算进度百分比
            progress_str = "N/A"
            if task.total_size and task.total_size > 0:
                progress = (task.downloaded_size / task.total_size) * 100
                progress_str = f"{progress:.1f}%"

            # 格式化文件大小
            size_str = "N/A"
            if task.total_size:
                if task.total_size < 1024:
                    size_str = f"{task.total_size} B"
                elif task.total_size < 1024 * 1024:
                    size_str = f"{task.total_size/1024:.1f} KB"
                elif task.total_size < 1024 * 1024 * 1024:
                    size_str = f"{task.total_size/(1024*1024):.1f} MB"
                else:
                    size_str = f"{task.total_size/(1024*1024*1024):.1f} GB"

            # 计算下载速度
            speed_str = "N/A"
            if task.speed > 0:
                if task.speed < 1024:
                    speed_str = f"{task.speed:.1f} B/s"
                elif task.speed < 1024 * 1024:
                    speed_str = f"{task.speed/1024:.1f} KB/s"
                else:
                    speed_str = f"{task.speed/(1024*1024):.1f} MB/s"

            # 添加任务信息
            task_name = f"{task_info['name']} ({task_info['version']})"
            results.append([
                task_name,
                task.status,
                progress_str,
                size_str,
                speed_str
            ])

        return results

    def refresh_tasks_periodically(self):
        """定期刷新任务列表（用于UI自动更新）"""
        return self.refresh_tasks()

    def cancel_all_tasks(self) -> tuple:
        """取消所有活动任务"""
        try:
            for task_id, task_info in self.active_tasks.items():
                task = task_info["task"]
                if task.status == "running":
                    task.cancel()

            message = "已取消所有下载任务"
            return message, self.refresh_tasks()
        except Exception as e:
            logger.exception("取消任务失败")
            return f"取消任务失败: {str(e)}", self.refresh_tasks()

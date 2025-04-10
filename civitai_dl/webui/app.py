"""Web UI application for Civitai Downloader."""

import os
import gradio as gr
from typing import Optional

from civitai_dl import __version__
from civitai_dl.api.client import CivitaiAPI
from civitai_dl.core.downloader import DownloadEngine


def create_app():
    """创建并配置WebUI应用"""
    api = CivitaiAPI()
    download_engine = DownloadEngine()

    with gr.Blocks(title=f"Civitai Downloader v{__version__}") as app:
        with gr.Tab("下载模型"):
            with gr.Row():
                with gr.Column():
                    model_id = gr.Number(label="模型ID", precision=0, minimum=1)
                    version_id = gr.Number(
                        label="版本ID (可选)", precision=0, minimum=1
                    )
                    output_dir = gr.Textbox(
                        label="输出目录", value=os.path.join(os.getcwd(), "downloads")
                    )
                    download_btn = gr.Button("下载")

                with gr.Column():
                    status = gr.Textbox(label="状态", interactive=False)
                    progress = gr.Slider(
                        minimum=0, maximum=100, value=0, step=0.1, label="下载进度"
                    )

        with gr.Tab("浏览模型"):
            with gr.Row():
                with gr.Column(scale=1):
                    search_query = gr.Textbox(label="搜索关键词")
                    model_type = gr.Dropdown(
                        choices=[
                            "Checkpoint",
                            "LORA",
                            "TextualInversion",
                            "Hypernetwork",
                        ],
                        label="模型类型",
                        multiselect=True,
                    )
                    search_btn = gr.Button("搜索")

                with gr.Column(scale=2):
                    results = gr.Dataframe(
                        headers=["ID", "名称", "类型", "创作者", "下载量"],
                        label="搜索结果",
                    )

        # 简单的示例回调函数
        def on_download(model_id, version_id, output_dir):
            if not model_id:
                return "请输入有效的模型ID"
            return f"正在下载模型ID: {model_id}，这是一个示例响应，实际下载功能正在开发中..."

        def on_search(query, types):
            # 这是示例数据，实际应用中会从API获取
            return {
                "data": [
                    [12345, "示例模型 1", "LORA", "创作者A", 1250],
                    [67890, "示例模型 2", "Checkpoint", "创作者B", 3400],
                ]
            }

        # 绑定事件
        download_btn.click(
            fn=on_download, inputs=[model_id, version_id, output_dir], outputs=[status]
        )

        search_btn.click(
            fn=on_search, inputs=[search_query, model_type], outputs=[results]
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch()

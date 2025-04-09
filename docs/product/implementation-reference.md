# 简化版实现方案

本文档提供Civitai Downloader简化版的实现方案，聚焦于核心下载功能，使用Click实现CLI接口和Gradio实现WebUI。

## 技术栈选择

| 组件       | 技术选择           | 说明                         |
| ---------- | ------------------ | ---------------------------- |
| CLI框架    | Click              | Python命令行工具库，简洁易用 |
| WebUI框架  | Gradio             | 快速构建AI应用界面的Python库 |
| HTTP客户端 | Requests           | 处理API请求和文件下载        |
| 并发处理   | ThreadPoolExecutor | 处理多任务下载               |

## 核心功能实现

### 模型下载核心功能

| 功能           | 实现方式                     | API端点                                                                     |
| -------------- | ---------------------------- | --------------------------------------------------------------------------- |
| 单个模型下载   | 通过模型ID获取版本信息并下载 | `GET /api/v1/models/:modelId`<br>`GET /api/download/models/:modelVersionId` |
| 按类型批量下载 | 搜索特定类型模型并批量下载   | `GET /api/v1/models?types=LORA`                                             |
| 按创作者下载   | 获取特定创作者的模型并下载   | `GET /api/v1/models?username=创作者名`                                      |
| 按筛选条件下载 | 应用多种筛选条件搜索并下载   | `GET /api/v1/models?types=X&tag=Y&rating=Z`                                 |
| 从列表下载     | 通过模型ID列表批量下载       | 多次调用单模型下载接口                                                      |

### 2. 图像下载核心功能

| 功能             | 实现方式                   | API端点                                |
| ---------------- | -------------------------- | -------------------------------------- |
| 模型示例图下载   | 获取模型相关图像并下载     | `GET /api/v1/images?modelId=X`         |
| 版本示例图下载   | 获取特定版本的图像并下载   | `GET /api/v1/images?modelVersionId=X`  |
| 创作者图像下载   | 获取特定创作者的图像并下载 | `GET /api/v1/images?username=创作者名` |
| 批量筛选图像下载 | 应用筛选条件批量下载图像   | `GET /api/v1/images?多个筛选参数组合`  |

## 模块结构设计

```
civitai_downloader/
├── cli/                   # 命令行接口
│   ├── __init__.py
│   ├── commands/          # 命令实现
│   │   ├── __init__.py
│   │   ├── browse.py      # 搜索命令
│   │   ├── download.py    # 下载命令
│   │   └── version.py     # 版本信息
│   └── main.py            # CLI入口
├── core/                  # 核心功能
│   ├── __init__.py
│   ├── api.py             # API客户端
│   ├── downloader.py      # 下载引擎
│   ├── model_browser.py   # 模型浏览
│   └── image_browser.py   # 图像浏览
├── webui/                 # Gradio界面
│   ├── __init__.py
│   ├── app.py             # 应用主体
│   └── pages/             # 页面组件
│       ├── __init__.py
│       ├── browse.py      # 浏览页面
│       ├── download.py    # 下载页面
│       └── settings.py    # 简单设置
└── __main__.py            # 程序入口
```

## CLI实现示例 (Click)

```python
# cli/commands/download.py
import click
from ...core.api import CivitaiAPI
from ...core.downloader import ModelDownloader

@click.group()
def download():
    """Download models or images from Civitai"""
    pass

@download.command("model")
@click.argument("model_id", type=int)
@click.option("--version", type=int, help="Specific version ID to download")
@click.option("--output", help="Output directory")
def download_model(model_id, version, output):
    """Download a specific model by ID"""
    api = CivitaiAPI()
    downloader = ModelDownloader(output_path=output)
    
    if version:
        downloader.download_model_version(version)
    else:
        model = api.get_model(model_id)
        latest_version = model['modelVersions'][0]['id']
        downloader.download_model_version(latest_version)

@download.command("models")
@click.option("--type", "-t", help="Model type (LORA, Checkpoint, etc)")
@click.option("--creator", "-c", help="Creator username")
@click.option("--list", "-l", help="Comma-separated list of model IDs")
@click.option("--query", "-q", help="Search query")
@click.option("--output", "-o", help="Output directory")
@click.option("--limit", type=int, default=20, help="Maximum number of models to download")
def download_models(type, creator, list, query, output, limit):
    """Download multiple models based on criteria"""
    api = CivitaiAPI()
    downloader = ModelDownloader(output_path=output)
    
    if list:
        model_ids = [int(id.strip()) for id in list.split(",")]
        for model_id in model_ids:
            model = api.get_model(model_id)
            latest_version = model['modelVersions'][0]['id']
            downloader.download_model_version(latest_version)
    elif creator:
        params = {"username": creator, "limit": limit}
        if type:
            params["types"] = type
        models = api.get_models(params)
        for model in models["items"]:
            latest_version = model['modelVersions'][0]['id']
            downloader.download_model_version(latest_version)
    elif type:
        models = api.get_models({"types": type, "limit": limit})
        for model in models["items"]:
            latest_version = model['modelVersions'][0]['id']
            downloader.download_model_version(latest_version)
    else:
        params = {"limit": limit}
        if query:
            params["query"] = query
        models = api.get_models(params)
        for model in models["items"]:
            latest_version = model['modelVersions'][0]['id']
            downloader.download_model_version(latest_version)
```

## Gradio界面实现示例

```python
# webui/app.py
import gradio as gr
import os
from ..core.api import CivitaiAPI
from ..core.downloader import ModelDownloader, ImageDownloader

def create_app():
    api = CivitaiAPI()
    model_downloader = ModelDownloader()
    image_downloader = ImageDownloader()
    
    # 保存下载任务状态
    download_tasks = []
    
    def search_models(query, model_type, creator):
        params = {"limit": 20}
        if query:
            params["query"] = query
        if model_type:
            params["types"] = model_type
        if creator:
            params["username"] = creator
            
        results = api.get_models(params)
        
        # 格式化结果用于显示
        formatted_results = []
        for model in results["items"]:
            formatted_results.append({
                "id": model["id"],
                "name": model["name"],
                "type": model["type"],
                "creator": model.get("creator", {}).get("username", "Unknown"),
                "rating": model.get("stats", {}).get("rating", "N/A"),
                "downloads": model.get("stats", {}).get("downloadCount", 0)
            })
        
        return gr.DataFrame.update(value=formatted_results)
    
    def download_selected_models(selected_rows, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        for row in selected_rows:
            model_id = row["id"]
            model = api.get_model(model_id)
            latest_version = model['modelVersions'][0]['id']
            task = model_downloader.download_model_version(latest_version, output_dir)
            download_tasks.append(task)
            
        return f"Started download of {len(selected_rows)} models to {output_dir}"
    
    with gr.Blocks(title="Civitai Downloader") as app:
        with gr.Tab("Browse & Download Models"):
            with gr.Row():
                with gr.Column(scale=3):
                    query = gr.Textbox(label="Search Query")
                    model_type = gr.Dropdown(
                        choices=["Checkpoint", "LORA", "TextualInversion", "Hypernetwork", 
                                 "AestheticGradient", "Controlnet", "Poses"],
                        label="Model Type",
                        multiselect=True
                    )
                    creator = gr.Textbox(label="Creator")
                    search_btn = gr.Button("Search")
                    
                with gr.Column(scale=7):
                    results_df = gr.DataFrame(
                        headers=["id", "name", "type", "creator", "rating", "downloads"],
                        datatype=["number", "str", "str", "str", "number", "number"],
                        label="Search Results",
                        interactive=True
                    )
            
            with gr.Row():
                output_dir = gr.Textbox(label="Output Directory", value="./downloads")
                download_btn = gr.Button("Download Selected")
                
            status_box = gr.Textbox(label="Status", interactive=False)
            
        with gr.Tab("Download Images"):
            with gr.Row():
                model_id = gr.Number(label="Model ID")
                nsfw_level = gr.CheckboxGroup(
                    choices=["None", "Soft", "Mature", "X"],
                    label="NSFW Level",
                    value=["None", "Soft"]
                )
            
            with gr.Row():
                images_output_dir = gr.Textbox(label="Images Output Directory", value="./images")
                download_images_btn = gr.Button("Download Images")
                
            images_status = gr.Textbox(label="Status", interactive=False)
        
        # 设置事件处理
        search_btn.click(
            fn=search_models, 
            inputs=[query, model_type, creator], 
            outputs=[results_df]
        )
        
        download_btn.click(
            fn=download_selected_models, 
            inputs=[results_df.get_selected_rows(), output_dir], 
            outputs=[status_box]
        )
        
        # 图像下载功能绑定
        def download_model_images(model_id, nsfw_levels, output_dir):
            if not model_id:
                return "Please enter a valid Model ID"
                
            params = {"modelId": model_id, "nsfw": nsfw_levels}
            images = api.get_images(params)
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            for img in images["items"]:
                image_downloader.download_image(img["url"], output_dir, img["id"])
                
            return f"Downloaded {len(images['items'])} images to {output_dir}"
            
        download_images_btn.click(
            fn=download_model_images,
            inputs=[model_id, nsfw_level, images_output_dir],
            outputs=[images_status]
        )
            
    return app

# 启动应用
def main():
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    main()
```

## 核心类实现

### CivitaiAPI 类

```python
# core/api.py
import requests
import os

class CivitaiAPI:
    def __init__(self):
        self.base_url = "https://civitai.com/api/v1"
        self.api_key = os.environ.get("CIVITAI_API_KEY")
        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    def get_models(self, params=None):
        """获取模型列表"""
        url = f"{self.base_url}/models"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_model(self, model_id):
        """获取单个模型详情"""
        url = f"{self.base_url}/models/{model_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_model_version(self, version_id):
        """获取模型版本详情"""
        url = f"{self.base_url}/model-versions/{version_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_images(self, params=None):
        """获取图像列表"""
        url = f"{self.base_url}/images"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
```

### ModelDownloader 类

```python
# core/downloader.py
import os
import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, unquote
import time

class DownloadTask:
    def __init__(self, url, output_path, filename=None):
        self.url = url
        self.output_path = output_path
        self.filename = filename
        self.status = "pending"  # pending, downloading, completed, failed
        self.progress = 0
        self.error = None
        self.start_time = None
        self.end_time = None
    
    def update_progress(self, progress):
        self.progress = progress

class ModelDownloader:
    def __init__(self, output_path="./downloads", max_workers=3):
        self.output_path = output_path
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = {}
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)
    
    def download_model_version(self, version_id, output_path=None):
        """下载特定版本的模型"""
        if output_path is None:
            output_path = self.output_path
            
        download_url = f"https://civitai.com/api/download/models/{version_id}"
        api_key = os.environ.get("CIVITAI_API_KEY")
        if api_key:
            download_url += f"?token={api_key}"
            
        # 创建下载任务
        task = DownloadTask(download_url, output_path)
        task_id = f"model_{version_id}_{int(time.time())}"
        self.tasks[task_id] = task
        
        # 提交下载任务
        future = self.executor.submit(self._download_file, task)
        return task_id
    
    def _download_file(self, task):
        """执行文件下载，支持进度跟踪和断点续传"""
        task.status = "downloading"
        task.start_time = time.time()
        
        headers = {}
        local_filename = None
        
        try:
            # 发送HEAD请求获取文件信息
            head_response = requests.head(task.url)
            head_response.raise_for_status()
            
            # 从Content-Disposition获取文件名
            if 'Content-Disposition' in head_response.headers:
                content_disposition = head_response.headers['Content-Disposition']
                if 'filename=' in content_disposition:
                    local_filename = content_disposition.split('filename=')[1]
                    if local_filename.startswith('"') and local_filename.endswith('"'):
                        local_filename = local_filename[1:-1]
            
            # 如果获取不到文件名，从URL中提取
            if not local_filename:
                local_filename = os.path.basename(urlparse(task.url).path)
                local_filename = unquote(local_filename)
            
            # 如果传入了指定文件名，使用指定的
            if task.filename:
                local_filename = task.filename
            
            file_path = os.path.join(task.output_path, local_filename)
            
            # 检查文件是否已经存在，支持断点续传
            file_size = 0
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > 0:
                    headers['Range'] = f'bytes={file_size}-'
            
            # 执行下载
            with requests.get(task.url, headers=headers, stream=True) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                if 'Range' in headers and response.status_code == 206:
                    total_size += file_size
                
                mode = 'ab' if file_size > 0 else 'wb'
                with open(file_path, mode) as f:
                    downloaded = file_size
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress = downloaded / total_size if total_size > 0 else 0
                            task.update_progress(progress)
            
            task.status = "completed"
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            raise e
            
        finally:
            task.end_time = time.time()
            
        return file_path

class ImageDownloader:
    def __init__(self, output_path="./images", max_workers=5):
        self.output_path = output_path
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)
    
    def download_image(self, url, output_path=None, image_id=None):
        """下载单张图像"""
        if output_path is None:
            output_path = self.output_path
            
        # 从URL中提取文件名
        filename = os.path.basename(urlparse(url).path)
        if not filename:
            filename = f"image_{image_id if image_id else int(time.time())}.jpg"
        
        file_path = os.path.join(output_path, filename)
        
        # 提交下载任务
        future = self.executor.submit(self._download_image, url, file_path)
        return future
    
    def _download_image(self, url, file_path):
        """执行图像下载"""
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            return file_path
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")
            raise e
```

## 注意事项和限制

1. **简化设计原则**
   - 专注核心下载功能，不实现本地资源管理
   - 使用简单的文件结构保存下载内容
   - 最小化依赖项，仅使用Click、Gradio和Requests

2. **API Key处理**
   - 通过环境变量CIVITAI_API_KEY传递，避免硬编码
   - 某些模型可能需要API Key才能下载

3. **当前限制**
   - 没有实现复杂的配置管理，使用默认设置
   - 没有实现API限制处理和优化策略
   - 没有实现插件系统
   - 本地数据保存仅使用简单文件结构，无数据库

4. **用户界面**
   - CLI使用Click提供命令行界面
   - WebUI使用Gradio提供简单直观的界面
   - 界面专注于功能而非美观

5. **可扩展性**
   - 代码结构支持未来添加更多功能
   - 核心类设计允许在不修改基础代码的情况下扩展功能

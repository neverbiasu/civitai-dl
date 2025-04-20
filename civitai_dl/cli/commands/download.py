import json
import os
import sys
import time
from typing import Optional

import click
from more_itertools import strip

from civitai_dl.api import CivitaiAPI
from civitai_dl.core.downloader import DownloadEngine
from civitai_dl.utils.config import get_config
from civitai_dl.utils.logger import get_logger
from civitai_dl.utils.metadata import extract_image_metadata, save_metadata_to_json
from civitai_dl.utils.path_template import apply_model_template

logger = get_logger(__name__)


@click.group()
def download():
    """下载模型和图像"""


@download.command("model")
@click.argument("model_id")
@click.option("--version", "-v", help="模型版本ID，不指定则下载最新版本")
@click.option("--output", "-o", help="输出目录")
@click.option("--with-images", is_flag=True, help="同时下载模型图像")
def download_model(model_id, version=None, output=None, with_images=False):
    """下载指定ID的模型

    MODEL_ID 是Civitai模型的唯一标识符
    """
    try:
        config = get_config()
        output_dir = output or config.get("output_dir", "./downloads")

        # 创建API客户端
        api = CivitaiAPI(
            api_key=config.get("api_key"),
            proxy=config.get("proxy"),
            verify=config.get("verify_ssl", True),
            timeout=config.get("timeout", 30),
            max_retries=config.get("max_retries", 3),
        )

        # 获取模型信息
        click.echo(f"获取模型 {model_id} 信息...")
        model_info = api.get_model(model_id)
        if not model_info:
            click.secho(f"错误: 找不到模型 {model_id} 或无法获取模型信息", fg="red")
            return

        # 确定版本
        versions = model_info.get("modelVersions", [])
        if not versions:
            click.secho(f"错误: 模型 {model_id} 没有可用版本", fg="red")
            return

        target_version = None
        if version:
            for v in versions:
                if str(v["id"]) == str(version):
                    target_version = v
                    break
            if not target_version:
                click.secho(f"错误: 找不到指定的版本ID: {version}", fg="red")
                return
        else:
            target_version = versions[0]
            click.echo(f"使用最新版本: {target_version.get('name')} (ID: {target_version.get('id')})")

        # 获取文件
        files = target_version.get("files", [])
        if not files:
            click.secho(f"错误: 版本 {target_version.get('id')} 没有可用文件", fg="red")
            return

        target_file = files[0]  # 使用第一个文件

        # 初始化下载引擎
        downloader = DownloadEngine(
            output_dir=output_dir,
            concurrent_downloads=1,
        )

        # 构建文件路径
        file_path = os.path.join(output_dir, target_file["name"])

        # 显示下载信息
        model_name = model_info.get("name", f"模型 {model_id}")
        click.echo(f"开始下载 {model_name}, 版本: {target_version.get('name')}")
        click.echo(f"文件: {target_file['name']} ({format_size(target_file.get('sizeKB', 0) * 1024)})")

        # 定义进度回调
        def progress_callback(downloaded, total):
            if total:
                progress = (downloaded / total) * 100
                click.echo(f"\r下载进度: {progress:.1f}% [{format_size(downloaded)}/{format_size(total)}]", nl=False)
            else:
                click.echo(f"\r已下载: {format_size(downloaded)}", nl=False)

        # 执行下载
        download_task = downloader.download(
            url=target_file["downloadUrl"],
            output_path=output_dir,
            filename=target_file["name"],
            progress_callback=progress_callback
        )

        # 等待下载完成
        download_task.wait()

        if download_task.status == "completed":
            click.echo("\n下载完成!")
            click.echo(f"文件保存至: {download_task.file_path}")

            # 下载关联图像
            if with_images:
                click.echo("\n开始下载模型示例图像...")
                download_images(
                    api,
                    downloader,
                    model_id,
                    target_version.get("id"),
                    limit=5,  # 默认下载5张示例图像
                    output_dir=output_dir,
                    include_nsfw=False,
                    gallery=False
                )
        else:
            click.secho(f"\n下载失败: {download_task.error}", fg="red")

    except Exception as e:
        click.secho(f"\n下载失败: {str(e)}", fg="red")
        logger.exception("模型下载失败")


@download.command("images")
@click.option("--model", "-m", type=int, help="模型ID")
@click.option("--version", "-v", type=int, help="版本ID")
@click.option("--limit", "-l", type=int, default=10, help="下载数量限制")
@click.option("--output", "-o", help="输出目录")
@click.option("--nsfw", is_flag=True, help="包含NSFW内容")
@click.option("--gallery", is_flag=True, help="下载社区画廊图像而非模型示例图像")
def download_images_cmd(
    model: Optional[int],
    version: Optional[int],
    limit: int,
    output: Optional[str],
    nsfw: bool,
    gallery: bool,
):
    """下载模型示例图像或社区画廊图像"""
    try:
        if not model and not version:
            click.secho("错误: 请指定模型ID或版本ID", fg="red")
            sys.exit(1)

        config = get_config()

        # 创建API客户端
        api = CivitaiAPI(
            api_key=config.get("api_key"),
            proxy=config.get("proxy"),
            verify=config.get("verify_ssl", True),
            timeout=config.get("timeout", 30),
            max_retries=config.get("max_retries", 3),
        )

        # 初始化下载引擎
        downloader = DownloadEngine(
            output_dir=output or config.get("output_dir", "./downloads/images"),
            concurrent_downloads=config.get("concurrent_downloads", 3),
        )

        download_images(api, downloader, model, version, limit, output, nsfw, gallery)

    except Exception as e:
        click.secho(f"下载图像过程中出错: {str(e)}", fg="red")
        logger.exception("图像下载失败")
        sys.exit(1)


# 添加一个命令别名，让单数形式也能使用
@download.command("image")
@click.argument("model_id", type=int)  # 允许直接传入模型ID作为参数
@click.option("--version", "-v", type=int, help="版本ID")
@click.option("--limit", "-l", type=int, default=10, help="下载数量限制")
@click.option("--output", "-o", help="输出目录")
@click.option("--nsfw", is_flag=True, help="包含NSFW内容")
@click.option("--gallery", is_flag=True, help="下载社区画廊图像而非模型示例图像")
def download_image_cmd(
    model_id: int,
    version: Optional[int],
    limit: int,
    output: Optional[str],
    nsfw: bool,
    gallery: bool,
):
    """下载单个模型的示例图像或社区画廊图像"""
    try:
        config = get_config()

        # 创建API客户端
        api = CivitaiAPI(
            api_key=config.get("api_key"),
            proxy=config.get("proxy"),
            verify=config.get("verify_ssl", True),
            timeout=config.get("timeout", 30),
            max_retries=config.get("max_retries", 3),
        )

        # 初始化下载引擎
        downloader = DownloadEngine(
            output_dir=output or config.get("output_dir", "./downloads/images"),
            concurrent_downloads=config.get("concurrent_downloads", 3),
        )

        # 直接使用模型ID参数
        download_images(
            api, downloader, model_id, version, limit, output, nsfw, gallery
        )

    except Exception as e:
        click.secho(f"下载图像过程中出错: {str(e)}", fg="red")
        logger.exception("图像下载失败")
        sys.exit(1)


@download.command("models")
@click.option("--ids", "-i", help="模型ID列表，用逗号分隔")
@click.option("--from-file", "-f", help="从文件读取模型ID列表")
@click.option("--output", "-o", help="输出目录")
@click.option("--format", help="首选文件格式")
@click.option("--concurrent", "-c", type=int, default=2, help="并行下载数量")
@click.option("--template", "-t", help="输出路径模板")
@click.option("--save-metadata", is_flag=True, default=True, help="保存模型元数据")
def download_models(
    ids: Optional[str],
    from_file: Optional[str],
    output: Optional[str],
    format: Optional[str],
    concurrent: int,
    template: Optional[str],
    save_metadata: bool,
):
    """批量下载多个模型"""
    model_ids = []

    # 从参数获取ID列表
    if ids:
        model_ids = [int(x.strip()) for x in ids.split(",") if x.strip().isdigit()]

    # 从文件获取ID列表
    if from_file:
        try:
            with open(from_file, "r") as f:
                for line in f:
                    line = strip()
                    if line.isdigit():
                        model_ids.append(int(line))
        except Exception as e:
            click.secho(f"读取文件失败: {str(e)}", fg="red")
            sys.exit(1)

    if not model_ids:
        click.secho("错误: 请提供至少一个模型ID", fg="red")
        sys.exit(1)

    config = get_config()

    # 设置最大并发数
    concurrent = min(max(1, concurrent), 10)  # 限制在1-10之间

    click.echo(f"准备下载 {len(model_ids)} 个模型，并发数: {concurrent}")

    # 获取路径模板
    path_template = template or config.get("path_template", "{type}/{creator}/{name}")

    # 创建API和下载引擎
    api = CivitaiAPI(
        api_key=config.get("api_key"),
        proxy=config.get("proxy"),
        verify=config.get("verify_ssl", True),
        timeout=config.get("timeout", 30),
        max_retries=config.get("max_retries", 3),
    )

    # 初始化下载状态追踪
    download_results = []
    success_count = 0
    failed_count = 0

    # 使用ThreadPoolExecutor实现并行下载
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent) as executor:
        # 提交所有下载任务
        future_to_model = {
            executor.submit(
                download_model_with_metadata,
                api=api,
                model_id=model_id,
                version_id=None,
                output=output,
                format=format,
                path_template=path_template,
                save_metadata=save_metadata,
            ): model_id
            for model_id in model_ids
        }

        # 处理完成的任务
        for future in concurrent.futures.as_completed(future_to_model):
            model_id = future_to_model[future]
            try:
                result = future.result()
                if result["status"] == "success":
                    success_count += 1
                    click.secho(
                        f"模型 {model_id} 下载成功: {result['file_path']}", fg="green"
                    )
                else:
                    failed_count += 1
                    click.secho(f"模型 {model_id} 下载失败: {result['error']}", fg="red")
                # 记录结果
                download_results.append(result)
            except Exception as e:
                failed_count += 1
                click.secho(f"模型 {model_id} 下载过程中出错: {str(e)}", fg="red")
                download_results.append(
                    {"model_id": model_id, "status": "failed", "error": str(e)}
                )

            # 显示进度
            total_done = success_count + failed_count
            click.echo(
                f"进度: {total_done}/{len(model_ids)} "
                f"(成功: {success_count}, 失败: {failed_count})"
            )

    # 显示总结
    click.echo("\n下载完成!")
    click.echo(f"总计: {len(model_ids)} 模型, 成功: {success_count}, 失败: {failed_count}")


def download_model_with_metadata(
    api,
    model_id,
    version_id=None,
    output=None,
    format=None,
    path_template=None,
    save_metadata=True,
):
    """下载模型并保存元数据的工作函数"""
    try:
        config = get_config()
        output_dir = output or config.get("output_dir", "./downloads")

        # 获取模型信息
        model_info = api.get_model(model_id)
        if not model_info:
            return {"model_id": model_id, "status": "failed", "error": "模型不存在或无法获取模型信息"}

        # 确定版本
        versions = model_info.get("modelVersions", [])
        if not versions:
            return {"model_id": model_id, "status": "failed", "error": "模型没有可用版本"}

        target_version = None
        if version_id:
            for v in versions:
                if v["id"] == version_id:
                    target_version = v
                    break
        else:
            target_version = versions[0]

        if not target_version:
            return {
                "model_id": model_id,
                "status": "failed",
                "error": f"找不到指定的版本ID: {version_id}",
            }

        # 获取文件
        files = target_version.get("files", [])
        if not files:
            return {"model_id": model_id, "status": "failed", "error": "版本没有可用文件"}

        # 选择文件格式
        target_file = None
        if format:
            for file in files:
                if file["name"].lower().endswith(format.lower()):
                    target_file = file
                    break
        if not target_file:
            target_file = files[0]

        # 构建保存路径
        if path_template:
            # 使用模板生成相对路径
            relative_path = apply_model_template(
                path_template, model_info, target_version, target_file
            )
            # 组合完整路径
            model_dir = os.path.join(output_dir, relative_path)
            os.makedirs(model_dir, exist_ok=True)
            file_path = os.path.join(model_dir, target_file["name"])
        else:
            # 不使用模板，直接保存到输出目录
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, target_file["name"])

        # 初始化下载引擎
        downloader = DownloadEngine(
            output_dir=os.path.dirname(file_path),
            concurrent_downloads=1,
        )

        # 执行下载
        download_task = downloader.download(
            url=target_file["downloadUrl"], file_path=file_path
        )

        # 等待下载完成
        download_task.wait()

        if download_task.status != "completed":
            return {
                "model_id": model_id,
                "status": "failed",
                "error": download_task.error or "下载失败",
            }

        # 保存模型元数据
        if save_metadata:
            metadata = {
                "id": model_info.get("id"),
                "name": model_info.get("name"),
                "description": model_info.get("description"),
                "type": model_info.get("type"),
                "creator": model_info.get("creator"),
                "version": {
                    "id": target_version.get("id"),
                    "name": target_version.get("name"),
                    "description": target_version.get("description"),
                    "baseModel": target_version.get("baseModel"),
                    "trainedWords": target_version.get("trainedWords", []),
                },
                "stats": model_info.get("stats"),
                "tags": model_info.get("tags"),
                "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file": {
                    "name": target_file.get("name"),
                    "size": target_file.get("sizeKB"),
                    "metadata": target_file.get("metadata"),
                    "hashes": target_file.get("hashes", {}),
                },
            }

            # 保存元数据JSON
            metadata_path = os.path.splitext(file_path)[0] + ".meta.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

        # 返回下载结果
        return {
            "model_id": model_id,
            "status": "success",
            "file_path": file_path,
            "model_info": {
                "name": model_info.get("name"),
                "type": model_info.get("type"),
                "version": target_version.get("name"),
            },
        }

    except Exception as e:
        logger.exception(f"下载模型 {model_id} 时出错")
        return {"model_id": model_id, "status": "failed", "error": str(e)}


def download_images(
    api,
    downloader,
    model_id,
    version_id=None,
    limit=10,
    output_dir=None,
    include_nsfw=False,
    gallery=False,
):
    """下载模型示例图像或社区画廊图像的实现"""
    try:
        # 获取模型图像
        click.echo(f"正在获取{'社区画廊' if gallery else '模型示例'}图像...")

        model_info = None
        versions = []

        # 1. 如果提供了模型ID，首先获取模型信息
        if model_id:
            try:
                model_info = api.get_model(model_id)
                if model_info:
                    click.echo(
                        f"✓ 已验证模型: {model_info.get('name', 'Unknown')} (ID: {model_id})"
                    )
                    click.echo(f"模型类型: {model_info.get('type', 'Unknown')}")
                    versions = model_info.get("modelVersions", [])
                else:
                    click.secho(f"警告: 无法获取模型 {model_id} 的信息，可能不是有效的模型ID", fg="yellow")
            except Exception as e:
                click.secho(f"获取模型信息出错: {str(e)}", fg="yellow")

        # 2. 如果提供了版本ID，直接获取版本信息
        if version_id:
            try:
                version_info = api.get_model_version(version_id)
                if version_info:
                    click.echo(
                        f"✓ 已验证版本: {version_info.get('name', 'Unknown')} (ID: {version_id})"
                    )
                    # 如果需要但没有模型ID，从版本信息中获取
                    if not model_id and version_info.get("modelId"):
                        model_id = version_info.get("modelId")
                        click.echo(f"从版本信息推断模型ID: {model_id}")

                    # 将此版本添加到版本列表中(如果尚未存在)
                    if not any(v.get("id") == version_id for v in versions):
                        versions.append(version_info)
                else:
                    click.secho(f"警告: 无法获取版本 {version_id} 的信息，可能不是有效的版本ID", fg="yellow")
            except Exception as e:
                click.secho(f"获取版本信息出错: {str(e)}", fg="yellow")

        # 3. 决定要处理的版本
        target_versions = []
        if version_id:
            # 只处理指定的版本
            target_versions = [v for v in versions if v.get("id") == version_id]
        elif versions:
            # 处理所有版本
            target_versions = versions
            click.echo(f"模型有 {len(target_versions)} 个版本，将获取所有版本的图像")

        if not target_versions and not gallery:
            click.secho("错误: 未找到有效的模型版本", fg="red")
            return

        images = []

        # 根据gallery标志决定获取哪种图像
        if gallery:
            # 社区画廊图像
            click.echo(
                f"获取社区画廊图像, 参数: modelId={model_id}, versionId={version_id}, limit={limit}, nsfw={include_nsfw}"
            )
            images = api.get_model_images(model_id, version_id, limit, include_nsfw)
        else:
            # 模型示例图像 - 集合所有版本的图片
            total_limit = limit
            image_count = 0

            for ver in target_versions:
                v_id = ver.get("id")
                v_name = ver.get("name", "Unknown")
                click.echo(f"获取版本 {v_name} (ID: {v_id}) 的示例图像...")

                version_images = api.get_version_images(v_id)
                if version_images:
                    # 计算要取的图片数量，确保不超过总限制
                    per_version_limit = min(
                        len(version_images), total_limit - image_count
                    )
                    images.extend(version_images[:per_version_limit])
                    image_count += per_version_limit
                    click.echo(f"获取到 {per_version_limit} 张图像")
                else:
                    click.echo(f"版本 {v_name} 没有示例图像")

                if image_count >= total_limit:
                    break

        # 添加验证步骤，确保图像数据格式正确
        if not isinstance(images, list):
            click.secho(f"错误: API返回的图像格式不正确: {type(images)}", fg="red")
            logger.error(f"API返回的图像格式不正确: {images}")
            return

        if not images:
            click.echo(f"没有找到符合条件的{'社区画廊' if gallery else '模型示例'}图像")

            # 给用户提示
            click.secho("提示: 您可以尝试以下操作:", fg="yellow")
            if gallery:
                click.echo(" - 尝试下载模型示例图像 (不使用--gallery选项)")
            else:
                click.echo(" - 尝试下载社区画廊图像 (使用--gallery选项)")

            click.echo(" - 检查模型/版本ID是否正确")
            click.echo(" - 增加下载限制 (使用--limit参数)")
            click.echo(" - 启用NSFW内容 (使用--nsfw标志)")
            return

        click.echo(f"找到 {len(images)} 张{'社区画廊' if gallery else '模型示例'}图像，开始下载...")

        # 分析返回的图像信息，帮助用户确认是否获取了正确的图像
        if images and isinstance(images[0], dict):
            first_image = images[0]
            # 安全地检查元数据
            if "meta" in first_image:
                meta = first_image.get("meta")
                if isinstance(meta, dict) and "Model" in meta:
                    model_name = meta.get("Model")
                    click.echo(f"图像关联的模型: {model_name}")

        # 创建模型专用的图像文件夹
        folder_name = f"model_{model_id}_{'gallery' if gallery else 'examples'}"
        if version_id:
            folder_name += f"_v{version_id}"

        if output_dir:
            model_images_dir = os.path.join(output_dir, folder_name)
        else:
            model_images_dir = os.path.join(downloader.output_dir, folder_name)

        os.makedirs(model_images_dir, exist_ok=True)

        # 下载图像并显示进度
        total_downloaded = 0
        with click.progressbar(length=len(images), label="下载图像") as bar:
            for i, image in enumerate(images):
                # 获取图像URL
                image_url = image.get("url")
                if not image_url:
                    logger.warning(f"图像 {i+1} 没有URL，跳过")
                    continue

                # 构建文件名
                filename = f"{model_id}_{i+1}_{os.path.basename(image_url)}"
                if not os.path.splitext(filename)[1]:  # 确保有扩展名
                    filename += ".jpg"

                # 下载图像
                try:
                    download_task = downloader.download(
                        url=image_url,
                        output_path=model_images_dir,
                        filename=filename,
                        use_range=False,  # 显式禁用断点续传，避免416错误
                    )

                    # 等待下载完成
                    download_task.wait()
                    if download_task.status == "completed":
                        total_downloaded += 1

                        # 提取和保存图像元数据
                        try:
                            image_path = os.path.join(model_images_dir, filename)
                            metadata = extract_image_metadata(image_path)
                            if metadata:
                                # 添加来自API的元数据
                                metadata.update(
                                    {
                                        "id": image.get("id"),
                                        "model_id": model_id,
                                        "version_id": version_id,
                                        "nsfw": image.get("nsfw", False),
                                        "width": image.get("width"),
                                        "height": image.get("height"),
                                        "hash": image.get("hash"),
                                        "meta": image.get("meta"),
                                    }
                                )

                                # 保存元数据
                                metadata_path = (
                                    os.path.splitext(image_path)[0] + ".meta.json"
                                )
                                save_metadata_to_json(metadata, metadata_path)
                        except Exception as e:
                            logger.warning(f"提取图像元数据失败: {str(e)}")

                    elif download_task.status == "failed":
                        logger.error(f"图像 {filename} 下载失败: {download_task.error}")

                    # 更新进度条
                    bar.update(1)

                except Exception as e:
                    logger.error(f"下载图像 {filename} 时出错: {str(e)}")
                    # 继续下载其他图像
                    bar.update(1)

        # 汇报下载结果
        click.echo(f"\n图像下载完成! 成功下载 {total_downloaded}/{len(images)} 张图像")
        click.echo(f"保存位置: {model_images_dir}")

    except Exception as e:
        click.secho(f"下载图像失败: {str(e)}", fg="red")
        raise


def format_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.1f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.1f} GB"

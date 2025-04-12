import os
import sys
import click
from typing import Optional

from civitai_dl.api import CivitaiAPI
from civitai_dl.core.downloader import DownloadEngine
from civitai_dl.utils.logger import get_logger
from civitai_dl.utils.config import get_config

logger = get_logger(__name__)


@click.group()
def download():
    """下载模型和图像"""


@download.command("model")
@click.argument("model_id", type=int)
@click.option("--version", "-v", type=int, help="版本ID")
@click.option("--output", "-o", help="输出路径")
@click.option("--format", "-f", help="首选文件格式")
@click.option("--with-images", is_flag=True, help="同时下载示例图像")
@click.option("--image-limit", type=int, default=5, help="下载的图像数量限制")
def download_model(model_id: int, version: Optional[int], output: Optional[str],
                   format: Optional[str], with_images: bool, image_limit: int):
    """下载指定ID的模型"""
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
            output_dir=output or config.get("output_dir", "./downloads"),
            concurrent_downloads=1,
        )

        # 获取模型信息
        click.echo(f"正在获取模型信息 (ID: {model_id})...")
        model_info = api.get_model(model_id)

        if not model_info:
            click.secho(f"错误: 未找到ID为{model_id}的模型", fg="red")
            sys.exit(1)

        click.echo(f"模型名称: {model_info['name']}")

        # 获取版本信息
        versions = model_info["modelVersions"]

        if not versions:
            click.secho("错误: 该模型没有可用版本", fg="red")
            sys.exit(1)

        target_version = None

        if version:
            # 查找指定版本
            for v in versions:
                if v["id"] == version:
                    target_version = v
                    break

            if not target_version:
                click.secho(f"错误: 未找到ID为{version}的版本", fg="red")
                sys.exit(1)
        else:
            # 使用最新版本
            target_version = versions[0]

        click.echo(f"版本: {target_version['name']}")

        # 获取下载文件
        files = target_version["files"]

        if not files:
            click.secho("错误: 该版本没有可用文件", fg="red")
            sys.exit(1)

        # 如果指定了格式，尝试找到匹配的文件
        target_file = None

        if format:
            for file in files:
                if file["name"].lower().endswith(format.lower()):
                    target_file = file
                    break

            if not target_file:
                click.secho(f"警告: 未找到格式为{format}的文件，将下载默认文件", fg="yellow")
                target_file = files[0]
        else:
            # 使用第一个文件（通常是主模型文件）
            target_file = files[0]

        # 开始下载
        file_name = target_file["name"]
        file_size = target_file.get("sizeKB", 0) * 1024
        download_url = target_file["downloadUrl"]

        click.echo(f"准备下载: {file_name} ({format_size(file_size)})")

        # 设置进度回调
        def progress_callback(downloaded, total):
            percent = (downloaded / total) * 100 if total else 0
            click.echo(
                f"\r下载进度: {percent:.1f}% ({format_size(downloaded)}/{format_size(total)})",
                nl=False,
            )

        # 下载文件
        save_path = os.path.join(downloader.output_dir, file_name)
        click.echo(f"下载到: {save_path}")

        download_task = downloader.download(
            url=download_url, file_path=save_path, progress_callback=progress_callback
        )

        try:
            # 等待下载完成
            download_task.wait()
            click.echo("\n下载完成!")

            # 如果需要下载图像
            if with_images:
                click.echo("开始下载模型示例图像...")
                download_images(api, downloader, model_id, target_version["id"], image_limit, output)

            # 确保完全退出
            return

        except KeyboardInterrupt:
            click.echo("\n下载已取消")
            download_task.cancel()
            sys.exit(0)

    except Exception as e:
        click.secho(f"下载过程中出错: {str(e)}", fg="red")
        logger.exception("下载失败")
        sys.exit(1)


@download.command("images")
@click.option("--model", "-m", type=int, help="模型ID")
@click.option("--version", "-v", type=int, help="版本ID")
@click.option("--limit", "-l", type=int, default=10, help="下载数量限制")
@click.option("--output", "-o", help="输出目录")
@click.option("--nsfw", is_flag=True, help="包含NSFW内容")
def download_images_cmd(model: Optional[int], version: Optional[int], limit: int,
                        output: Optional[str], nsfw: bool):
    """下载模型示例图像"""
    try:
        if not model:
            click.secho("错误: 请指定模型ID", fg="red")
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

        download_images(api, downloader, model, version, limit, output, nsfw)

    except Exception as e:
        click.secho(f"下载图像过程中出错: {str(e)}", fg="red")
        logger.exception("图像下载失败")
        sys.exit(1)


@download.command("models")
@click.option("--ids", "-i", help="模型ID列表，用逗号分隔")
@click.option("--from-file", "-f", help="从文件读取模型ID列表")
@click.option("--output", "-o", help="输出目录")
@click.option("--format", help="首选文件格式")
@click.option("--concurrent", type=int, default=1, help="并行下载数量")
def download_models(ids: Optional[str], from_file: Optional[str], output: Optional[str],
                    format: Optional[str], concurrent: int):
    """批量下载多个模型"""
    model_ids = []

    # 从参数获取ID列表
    if ids:
        model_ids = [int(x.strip()) for x in ids.split(",") if x.strip().isdigit()]

    # 从文件获取ID列表
    if from_file:
        try:
            with open(from_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.isdigit():
                        model_ids.append(int(line))
        except Exception as e:
            click.secho(f"读取文件失败: {str(e)}", fg="red")
            sys.exit(1)

    if not model_ids:
        click.secho("错误: 请提供至少一个模型ID", fg="red")
        sys.exit(1)

    click.echo(f"准备下载 {len(model_ids)} 个模型...")

    # 这里实现批量下载逻辑
    # 为简化示例，依次下载每个模型
    for model_id in model_ids:
        click.echo(f"\n开始下载模型 {model_id}")
        try:
            download_model(model_id, None, output, format, False, 0)
        except Exception as e:
            click.secho(f"模型 {model_id} 下载失败: {str(e)}", fg="red")
            logger.error(f"模型 {model_id} 下载失败: {str(e)}")


def download_images(api, downloader, model_id, version_id=None, limit=10,
                    output_dir=None, include_nsfw=False):
    """下载模型示例图像的实现"""
    try:
        # 获取模型图像
        click.echo(f"正在获取模型 {model_id} 的图像...")

        # 这里需要实现图像获取和下载逻辑
        # 目前只提供占位实现
        click.echo("图像下载功能即将实现...")

        # 以下是示例实现框架
        """
        images = api.get_model_images(model_id, version_id, limit)

        if not images:
            click.echo("没有找到符合条件的图像")
            return

        click.echo(f"找到 {len(images)} 张图像，开始下载...")

        for i, image in enumerate(images):
            if not include_nsfw and image.get("nsfw", False):
                continue

            url = image["url"]
            filename = f"{model_id}_{i}_{os.path.basename(url)}"

            click.echo(f"下载图像 {i+1}/{len(images)}: {filename}")
            downloader.download(url, output_path=output_dir, filename=filename)

        click.echo("图像下载完成!")
        """

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

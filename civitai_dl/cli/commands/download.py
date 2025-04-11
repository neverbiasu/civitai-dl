import os
import sys
import click
from typing import Optional

# 更新导入以使用新的API模块
from civitai_dl.api import CivitaiAPI
from civitai_dl.core.downloader import DownloadEngine
from civitai_dl.utils.logger import get_logger
from civitai_dl.utils.config import get_config

logger = get_logger(__name__)


@click.group()
def download():
    """下载模型和图像"""
    pass


@download.command("model")
@click.argument("model_id", type=int)
@click.option("--version", "-v", type=int, help="版本ID")
@click.option("--output", "-o", help="输出路径")
@click.option("--format", "-f", help="首选文件格式")
@click.option("--with-images", is_flag=True, help="同时下载示例图像")
@click.option("--image-limit", type=int, default=5, help="下载的图像数量限制")
@click.option("--proxy", help="代理服务器地址(格式: 'http://user:pass@host:port')")
@click.option("--no-proxy", is_flag=True, help="禁用代理")
@click.option("--no-verify-ssl", is_flag=True, help="不验证SSL证书")
@click.option("--timeout", type=int, default=30, help="请求超时时间(秒)")
@click.option("--retries", type=int, default=3, help="最大重试次数")
def download_model(model_id, version, output, format, with_images, image_limit,
                   proxy, no_proxy, no_verify_ssl, timeout, retries):
    """下载指定ID的模型"""
    try:
        config = get_config()

        # 处理代理配置
        if no_proxy:
            effective_proxy = None
        elif proxy:
            effective_proxy = proxy
        else:
            effective_proxy = config.get('proxy')

        # 更新: 使用 verify 替代 verify_ssl
        api = CivitaiAPI(
            api_key=config.get('api_key'),
            proxy=effective_proxy,
            verify=not no_verify_ssl,  # 更改这里
            timeout=timeout,
            max_retries=retries
        )

        # 初始化下载引擎
        downloader = DownloadEngine(
            output_dir=output or config.get('output_dir', './downloads'),
            concurrent_downloads=1
        )

        # 获取模型信息
        click.echo(f"正在获取模型信息 (ID: {model_id})...")
        model_info = api.get_model(model_id)

        if not model_info:
            click.secho(f"错误: 未找到ID为{model_id}的模型", fg='red')
            sys.exit(1)

        click.echo(f"模型名称: {model_info['name']}")

        # 获取版本信息
        versions = model_info['modelVersions']

        if not versions:
            click.secho(f"错误: 该模型没有可用版本", fg='red')
            sys.exit(1)

        target_version = None

        if version:
            # 查找指定版本
            for v in versions:
                if v['id'] == version:
                    target_version = v
                    break

            if not target_version:
                click.secho(f"错误: 未找到ID为{version}的版本", fg='red')
                sys.exit(1)
        else:
            # 使用最新版本
            target_version = versions[0]

        click.echo(f"版本: {target_version['name']}")

        # 获取下载文件
        files = target_version['files']

        if not files:
            click.secho(f"错误: 该版本没有可用文件", fg='red')
            sys.exit(1)

        # 如果指定了格式，尝试找到匹配的文件
        target_file = None

        if format:
            for file in files:
                if file['name'].lower().endswith(format.lower()):
                    target_file = file
                    break

            if not target_file:
                click.secho(f"警告: 未找到格式为{format}的文件，将下载默认文件", fg='yellow')
                target_file = files[0]
        else:
            # 使用第一个文件（通常是主模型文件）
            target_file = files[0]

        # 开始下载
        file_name = target_file['name']
        file_size = target_file['sizeKB'] * 1024
        download_url = target_file['downloadUrl']

        click.echo(f"准备下载: {file_name} ({format_size(file_size)})")

        # 设置进度回调
        def progress_callback(downloaded, total):
            percent = (downloaded / total) * 100
            click.echo(f"\r下载进度: {percent:.1f}% ({format_size(downloaded)}/{format_size(total)})", nl=False)

        # 下载文件
        save_path = os.path.join(downloader.output_dir, file_name)
        click.echo(f"下载到: {save_path}")

        download_task = downloader.download(
            url=download_url,
            file_path=save_path,
            progress_callback=progress_callback
        )

        # 等待下载完成
        download_task.wait()
        click.echo("\n下载完成!")

        # 如果需要下载图像
        if with_images:
            click.echo(f"开始下载模型示例图像...")
            download_images(model_id, target_version['id'], image_limit, output)

    except Exception as e:
        click.secho(f"下载过程中出错: {str(e)}", fg='red')
        logger.exception("下载失败")
        sys.exit(1)


def download_images(model_id, version_id, limit, output_dir):
    """下载模型示例图像"""
    # 这里实现图像下载逻辑
    # 为了简化，这部分将在后续任务中实现
    click.echo("图像下载功能即将实现...")


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

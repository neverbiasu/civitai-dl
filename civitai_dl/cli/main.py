"""Command-line interface for Civitai Downloader."""

import click
import sys
from typing import Optional

from civitai_dl import __version__
from civitai_dl.cli.commands.download import download
from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", "-v", count=True, help="增加详细程度")
@click.option("--quiet", "-q", is_flag=True, help="静默模式")
def cli(verbose=0, quiet=False):
    """Civitai Downloader - 下载和管理Civitai资源"""
    # 这里可以添加日志级别设置逻辑


# 注册命令组
cli.add_command(download)
# 注册其他命令组...


@cli.command()
def webui():
    """启动Web图形界面"""
    try:
        from civitai_dl.webui.app import create_app

        app = create_app()
        click.echo("启动WebUI界面，请在浏览器中访问...")
        app.launch(server_name="0.0.0.0", server_port=7860)
    except ImportError as e:
        click.echo(f"启动WebUI失败: {str(e)}", err=True)
        click.echo("请确保已安装所有必要的依赖(gradio)", err=True)
        sys.exit(1)


@cli.group()
def browse():
    """浏览和搜索Civitai上的模型"""


@browse.command("models")
@click.option("--query", "-q", help="搜索关键词")
@click.option("--type", "-t", help="模型类型")
@click.option("--limit", "-l", type=int, default=20, help="结果数量")
def browse_models(query: Optional[str], type: Optional[str], limit: int):
    """搜索和浏览模型"""
    click.echo(f"搜索模型: {query or '全部'} (类型: {type or '全部'}, 限制: {limit})")
    # 这里将实现实际的搜索逻辑
    click.echo("搜索功能正在开发中...")


def main():
    """主入口函数"""
    cli()


if __name__ == "__main__":
    main()

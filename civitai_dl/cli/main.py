"""Command-line interface for Civitai Downloader."""

import logging
import sys
import os
from importlib import import_module
from typing import Optional

import click

from civitai_dl import __version__
from civitai_dl.cli.commands.config import config  # 导入配置命令模块
from civitai_dl.cli.commands.download import download
from civitai_dl.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", "-v", count=True, help="增加详细程度")
@click.option("--quiet", "-q", is_flag=True, help="静默模式")
def cli(verbose=0, quiet=False):
    """Civitai Downloader - 下载和管理Civitai资源"""
    # 设置日志级别
    if quiet:
        log_level = logging.ERROR  # 静默模式下只显示错误
    else:
        # 根据verbose的计数决定日志级别
        log_levels = [logging.INFO, logging.DEBUG, logging.NOTSET]
        # 确保索引不越界
        level_index = min(verbose, len(log_levels) - 1)
        log_level = log_levels[level_index]

    # 初始化日志系统
    setup_logging(log_level)

    # 根据日志级别输出不同的消息
    if log_level == logging.DEBUG:
        logger.debug("调试模式已启用")
    elif log_level == logging.INFO:
        logger.info("详细日志模式已启用")


# 动态导入命令模块
def import_commands():
    """动态导入所有命令模块"""
    commands_dir = os.path.join(os.path.dirname(__file__), "commands")
    for filename in os.listdir(commands_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]  # 去掉.py后缀
            module = import_module(f"civitai_dl.cli.commands.{module_name}")
            if hasattr(module, module_name):
                command = getattr(module, module_name)
                cli.add_command(command)


# 注册命令组
cli.add_command(download)
cli.add_command(config)  # 注册配置命令
# 注册其他命令组...
import_commands()


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
    pass

# 删除现有的browse_models命令实现，我们会从browse.py导入完整版本
from civitai_dl.cli.commands.browse import browse as browse_commands

# 将browse.py中的命令添加到browse命令组
for command in getattr(browse_commands, 'commands', {}).values():
    browse.add_command(command)


def main():
    """主入口函数"""
    cli()


if __name__ == "__main__":
    main()

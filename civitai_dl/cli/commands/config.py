"""配置管理命令"""

import os
from typing import Any, Dict, Optional

import click

from civitai_dl.utils.config import CONFIG_FILE, DEFAULT_CONFIG, get_config, save_config
from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
def config():
    """管理配置选项"""


@config.command("get")
@click.argument("key", required=False)
def config_get(key: Optional[str]):
    """获取配置值"""
    cfg = get_config()

    if not key:
        # 显示全部配置
        click.echo("当前配置:")
        for k, v in cfg.items():
            # 隐藏API密钥的具体值
            if k == "api_key" and v:
                v = f"{v[:4]}..." if len(v) > 8 else "设置了密钥"
            click.echo(f"  {k}: {v}")
    else:
        # 显示指定键的值
        if key in cfg:
            value = cfg[key]
            # 隐藏API密钥的具体值
            if key == "api_key" and value:
                value = f"{value[:4]}..." if len(value) > 8 else "设置了密钥"
            click.echo(f"{key}: {value}")
        else:
            click.secho(f"未找到配置项: {key}", fg="yellow")
            click.echo("可用的配置项:")
            for k in DEFAULT_CONFIG.keys():
                click.echo(f"  {k}")


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """设置配置值"""
    if key not in DEFAULT_CONFIG:
        click.secho(f"未知配置项: {key}", fg="red")
        click.echo("可用的配置项:")
        for k in DEFAULT_CONFIG.keys():
            click.echo(f"  {k}")
        return

    # 加载当前配置
    current_config = get_config()

    # 尝试转换值为适当的类型
    typed_value = _convert_value_type(key, value, DEFAULT_CONFIG)

    # 更新配置
    current_config[key] = typed_value

    # 保存配置
    save_config(current_config)

    click.secho(f"已设置 {key} = {typed_value}", fg="green")


@config.command("reset")
@click.argument("key", required=False)
@click.option("--all", is_flag=True, help="重置所有配置")
def config_reset(key: Optional[str], all: bool):
    """重置配置为默认值"""
    current_config = get_config()

    if all:
        # 重置全部配置
        save_config(DEFAULT_CONFIG.copy())
        click.secho("已重置所有配置为默认值", fg="green")
        return

    if not key:
        click.secho("请指定要重置的配置项，或使用 --all 重置所有配置", fg="yellow")
        return

    if key not in DEFAULT_CONFIG:
        click.secho(f"未知配置项: {key}", fg="red")
        return

    # 重置指定键
    current_config[key] = DEFAULT_CONFIG[key]

    # 保存配置
    save_config(current_config)

    click.secho(f"已重置 {key} = {DEFAULT_CONFIG[key]}", fg="green")


@config.command("path")
def config_path():
    """显示配置文件路径"""
    click.echo(f"配置文件位置: {CONFIG_FILE}")
    if os.path.exists(CONFIG_FILE):
        click.echo(f"文件大小: {os.path.getsize(CONFIG_FILE)} 字节")
        click.echo(f"修改时间: {os.path.getmtime(CONFIG_FILE)}")
    else:
        click.echo("配置文件尚未创建")


def _convert_value_type(key: str, value: str, default_config: Dict[str, Any]) -> Any:
    """根据默认值的类型转换配置值"""
    default_value = default_config.get(key)

    if default_value is None:
        # 如果默认值为None，尝试判断value是否为"null"/"none"
        if value.lower() in ("null", "none", ""):
            return None
        return value

    # 根据默认值的类型进行转换
    if isinstance(default_value, bool):
        return value.lower() in ("true", "yes", "1", "y", "t")
    elif isinstance(default_value, int):
        try:
            return int(value)
        except ValueError:
            logger.warning(f"无法将 {value} 转换为整数，使用原始字符串")
            return value
    elif isinstance(default_value, float):
        try:
            return float(value)
        except ValueError:
            logger.warning(f"无法将 {value} 转换为浮点数，使用原始字符串")
            return value
    else:
        # 字符串或其他类型，保持不变
        return value

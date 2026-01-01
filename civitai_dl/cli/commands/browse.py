"""Browse and search Civitai resources through the command line interface.

Provides commands for browsing models, filter templates, and search history.
"""

import sys
import json
import difflib
from typing import Dict, List, Any, Optional

import click
from tabulate import tabulate

from civitai_dl.api import CivitaiAPI
from civitai_dl.api import APIError
from civitai_dl.core.filter import FilterBuilder, FilterManager, parse_filter_condition
from civitai_dl.utils.config import get_config
from civitai_dl.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Create API client
api = CivitaiAPI()

# Create filter manager
filter_manager = FilterManager()


@click.group(help="Browse and search Civitai resources")
def browse() -> None:
    """Command group for browsing Civitai resources."""


@browse.command("models")
@click.option("--query", "-q", help="搜索关键词")
@click.option("--types", "-t", multiple=True, help="模型类型 (Checkpoint, LORA, TextualInversion等，可多选)")
@click.option("--tag", help="模型标签")
@click.option("--sort", help="排序方式 (最新, 下载数, 点赞数等)")
@click.option("--limit", "-l", type=int, default=20, help="结果数量限制")
@click.option("--nsfw", is_flag=True, help="包含NSFW内容")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table", help="输出格式")
@click.option("--creator", "-c", help="创作者用户名")
@click.option("--base-model", "-b", help="基础模型")
@click.option("--filter", help="高级筛选条件 (JSON格式)")
@click.option("--template", help="使用筛选模板")
def browse_models(query, types, tag, sort, limit, nsfw, format, creator, base_model, filter, template):
    """浏览和搜索模型"""
    try:
        # 获取配置
        config = get_config()

        # 创建API客户端
        api = CivitaiAPI(
            api_key=config.get("api_key"),
            proxy=config.get("proxy"),
            verify=config.get("verify_ssl", True),
            timeout=config.get("timeout", 30),
            max_retries=config.get("max_retries", 3),
        )

        # 使用筛选条件管理器
        filter_manager = FilterManager()

        # 确定筛选条件
        condition = determine_filter_condition(
            query=query,
            types=types,
            tag=tag,
            sort=sort,
            limit=limit,
            nsfw=nsfw,
            creator=creator,
            base_model=base_model,
            filter_json=filter,
            template_name=template,
            filter_manager=filter_manager
        )

        # 使用FilterBuilder构建API参数
        filter_builder = FilterBuilder()
        params = filter_builder.build_params(condition)

        # 保存筛选历史
        filter_manager.add_to_history(condition)

        # 获取模型列表
        results = api.get_models(**params)

        # 处理结果
        display_model_results(results, format)

    except Exception as e:
        click.secho(f"浏览模型时出错: {str(e)}", fg="red")
        logger.exception("浏览模型失败")
        sys.exit(1)

# 这个函数用来确定最终的筛选条件


def determine_filter_condition(
    query: Optional[str] = None,
    types: Optional[List[str]] = None,
    tag: Optional[str] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    nsfw: Optional[bool] = None,
    creator: Optional[str] = None,
    base_model: Optional[str] = None,
    filter_json: Optional[str] = None,
    template_name: Optional[str] = None,
    filter_manager: Optional[FilterManager] = None
) -> Dict[str, Any]:
    """确定筛选条件，优先级: 筛选模板 > 高级筛选条件 > 基本参数"""

    # 如果提供了模板名称，使用模板
    if template_name and filter_manager:
        template = filter_manager.get_template(template_name)
        if template:
            # 添加限制参数（如果模板中没有指定）
            if limit and "limit" not in json.dumps(template):
                # 深拷贝模板以避免修改原始模板
                import copy
                condition = copy.deepcopy(template)
                if "and" in condition:
                    condition["and"].append({"field": "limit", "op": "eq", "value": limit})
                else:
                    condition = {
                        "and": [
                            condition,
                            {"field": "limit", "op": "eq", "value": limit}
                        ]
                    }
                return condition
            return template
        else:
            click.echo(f"未找到模板: {template_name}")

    # 如果提供了高级筛选条件，解析并使用
    if filter_json:
        try:
            condition = parse_filter_condition(filter_json)

            # 添加限制参数（如果没有指定）
            if limit and "limit" not in filter_json:
                if "and" in condition:
                    condition["and"].append({"field": "limit", "op": "eq", "value": limit})
                else:
                    condition = {
                        "and": [
                            condition,
                            {"field": "limit", "op": "eq", "value": limit}
                        ]
                    }

            return condition
        except Exception as e:
            logger.error(f"解析筛选条件失败: {e}")
            click.echo(f"解析筛选条件失败: {e}")

    # 使用基本参数构建条件
    condition = {"and": []}

    if query:
        condition["and"].append({"field": "query", "op": "eq", "value": query})

    if types:
        # 支持多类型
        condition["and"].append({"field": "types", "op": "eq", "value": list(types)})

    if tag:
        condition["and"].append({"field": "tag", "op": "eq", "value": tag})

    if sort:
        condition["and"].append({"field": "sort", "op": "eq", "value": sort})

    if limit:
        condition["and"].append({"field": "limit", "op": "eq", "value": limit})

    if nsfw:
        condition["and"].append({"field": "nsfw", "op": "eq", "value": nsfw})

    if creator:
        condition["and"].append({"field": "username", "op": "eq", "value": creator})

    if base_model:
        condition["and"].append({"field": "baseModel", "op": "eq", "value": base_model})

    # 如果没有任何条件，返回空查询
    if not condition["and"]:
        condition = {"field": "query", "op": "eq", "value": ""}

    return condition


@browse.command("templates")
@click.option("--list", "-l", is_flag=True, help="列出所有模板")
@click.option("--add", "-a", help="添加新模板 (需要同时指定--filter)")
@click.option("--filter", "-f", help="模板筛选条件 (JSON格式)")
@click.option("--remove", "-r", help="删除模板")
@click.option("--show", "-s", help="显示模板内容")
def browse_templates(
        list: bool,
        add: Optional[str],
        filter: Optional[str],
        remove: Optional[str],
        show: Optional[str]) -> None:
    """管理筛选模板"""
    # 如果没有指定任何操作，默认列出所有模板
    if not any([list, add, remove, show]):
        list = True

    # 列出所有模板
    if list:
        templates = filter_manager.list_templates()
        if not templates:
            click.echo("没有保存的筛选模板")
            return

        click.echo("保存的筛选模板:")
        for name in templates:
            click.echo(f"  - {name}")

    # 添加新模板
    if add:
        if not filter:
            click.echo("错误: 添加模板时必须指定 --filter 参数", err=True)
            return

        try:
            condition = json.loads(filter)
            if filter_manager.add_template(add, condition):
                click.echo(f"模板 '{add}' 添加成功")
            else:
                click.echo("添加模板失败", err=True)
        except json.JSONDecodeError:
            click.echo("错误: 筛选条件必须是有效的JSON格式", err=True)

    # 删除模板
    if remove:
        if filter_manager.remove_template(remove):
            click.echo(f"模板 '{remove}' 删除成功")
        else:
            click.echo(f"模板 '{remove}' 不存在", err=True)

    # 显示模板内容
    if show:
        template = filter_manager.get_template(show)
        if template:
            click.echo(f"模板 '{show}':")
            click.echo(json.dumps(template, indent=2))
        else:
            click.echo(f"模板 '{show}' 不存在", err=True)


@browse.command("history")
@click.option("--limit", "-l", type=int, default=10, help="显示历史记录数量")
@click.option("--clear", "-c", is_flag=True, help="清空历史记录")
def browse_history(limit: int, clear: bool) -> None:
    """查看筛选历史"""
    if clear:
        filter_manager.clear_history()
        click.echo("历史记录已清空")
        return

    history = filter_manager.get_history()
    if not history:
        click.echo("没有筛选历史记录")
        return

    click.echo("最近的筛选历史:")
    for i, record in enumerate(history[:limit]):
        click.echo(f"{i + 1}. [{record['timestamp']}]\n   {json.dumps(record['condition'], indent=2)}")
        if i < len(history) - 1:
            click.echo("")


def display_search_results(models: List[Dict[str, Any]], format_type: str, output_file: Optional[str] = None) -> None:
    """Display search results in the specified format.

    Args:
        models: List of model data
        format_type: Output format (table/json)
        output_file: Output file path for saving results
    """
    if format_type == "json":
        result = json.dumps(models, indent=2)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            click.echo(f"Results saved to {output_file}")
        else:
            click.echo(result)
    else:  # table
        # Extract table data
        table_data = []
        for model in models:
            row = [
                model.get("id", ""),
                model.get("name", ""),
                model.get("type", ""),
                model.get("creator", {}).get("username", ""),
                model.get("stats", {}).get("downloadCount", 0),
                model.get("stats", {}).get("rating", 0),
            ]
            table_data.append(row)

        # Generate table
        headers = ["ID", "Name", "Type", "Creator", "Downloads", "Rating"]
        table = tabulate(table_data, headers=headers, tablefmt="grid")

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(table)
            click.echo(f"Results saved to {output_file}")
        else:
            click.echo(table)


def interactive_filter_builder() -> Dict[str, Any]:
    """Interactive filter condition builder.

    Provides an interactive interface for building complex filter conditions.

    Returns:
        Dict containing the built filter condition
    """
    conditions = []
    available_fields = [
        "name", "type", "creator.username", "tags",
        "modelVersions.baseModel", "stats.rating",
        "stats.downloadCount", "stats.favoriteCount",
        "publishedAt", "updatedAt"
    ]

    available_operators = {
        "=": "eq",
        "==": "eq",
        "!=": "ne",
        ">": "gt",
        ">=": "ge",
        "<": "lt",
        "<=": "le",
        "contains": "contains",
        "startswith": "startswith",
        "endswith": "endswith",
        "regex": "regex",
        "in": "in"
    }

    # Print colored title and instructions
    click.secho("=== Interactive Filter Builder ===", fg="green", bold=True)
    click.echo("Enter filter conditions one by one. Submit empty line when finished.")

    # Display available fields
    click.secho("Available fields:", fg="cyan")
    for field in available_fields:
        click.echo(f"  - {field}")

    # Display available operators
    click.secho("Available operators:", fg="cyan")
    click.echo("  - = (equals), != (not equals)")
    click.echo("  - > (greater than), >= (greater or equal)")
    click.echo("  - < (less than), <= (less or equal)")
    click.echo("  - contains (string contains)")
    click.echo("  - startswith (string starts with)")
    click.echo("  - endswith (string ends with)")
    click.echo("  - regex (regular expression match)")

    click.secho("Examples:", fg="yellow")
    click.echo("  - name contains lora")
    click.echo("  - stats.rating > 4.5")
    click.echo("  - type = LORA")
    click.echo("Press Ctrl+C to cancel")

    try:
        while True:
            # Colored prompt
            condition_str = click.prompt(click.style("Filter condition", fg="bright_blue"),
                                         default="", show_default=False)
            if not condition_str.strip():
                break

            # Parse condition
            parts = condition_str.split(maxsplit=2)
            if len(parts) != 3:
                click.secho("Invalid format. Please use 'field operator value'", fg="red")
                continue

            field, op_str, value = parts

            # Check if field is in suggested fields
            if field not in available_fields:
                suggestion = ""
                # Try to suggest a field if not in list
                matches = difflib.get_close_matches(field, available_fields, n=1)
                if matches:
                    suggestion = f", did you mean '{matches[0]}'?"

                if click.confirm(click.style(
                    f"Warning: '{field}' is not a common field{suggestion} Continue anyway?",
                        fg="yellow"), default=True):
                    pass
                else:
                    continue

            # Check operator
            if op_str not in available_operators:
                click.secho(f"Unsupported operator: {op_str}", fg="red")
                # Suggest valid operators
                click.echo("Please use one of: " + ", ".join(list(available_operators.keys())[:8]))
                continue

            # Try to convert value type
            try:
                # Try to convert to number
                if value.isdigit():
                    value = int(value)
                elif value.replace(".", "", 1).isdigit() and value.count(".") <= 1:
                    value = float(value)
            except (ValueError, TypeError):
                pass

            # Add condition
            conditions.append({
                "field": field,
                "op": available_operators[op_str],
                "value": value
            })

            # Show the added condition with color
            click.secho("✓ Added condition: ", fg="green", nl=False)
            click.echo(f"{field} {op_str} {value}")

            # Show total condition count
            click.secho(f"Total conditions: {len(conditions)}", fg="cyan")

    except (KeyboardInterrupt, EOFError):
        click.echo("\nFilter building cancelled")
        return {}

    # If no conditions, return empty dict
    if not conditions:
        click.secho("No filter conditions created", fg="yellow")
        return {}

    # If multiple conditions, ask for logical relationship
    if len(conditions) > 1:
        click.secho("Select logical relationship between conditions:", fg="bright_blue")
        click.echo("AND - All conditions must be met")
        click.echo("OR  - Any condition can be met")
        logic = click.prompt("Logic",
                             type=click.Choice(["AND", "OR"], case_sensitive=False),
                             default="AND")

        # Convert to lowercase for API compatibility
        logic = logic.lower()
        click.secho(f"Selected {logic.upper()} logic", fg="green")
        return {logic: conditions}
    else:
        # Only one condition, return directly
        click.secho("Created 1 filter condition", fg="green")
        return conditions[0]


def display_model_results(results: Dict[str, Any], format_type: str) -> None:
    """处理并显示模型搜索结果

    Args:
        results: API返回的搜索结果
        format_type: 输出格式 (table/json)
    """
    if not results or "items" not in results:
        click.echo("未找到结果")
        return

    models = results.get("items", [])
    metadata = results.get("metadata", {})

    # 调用已有的display_search_results函数来显示结果
    display_search_results(models, format_type)

    # 显示元数据信息
    total_items = metadata.get("totalItems", len(models))
    current_page = metadata.get("currentPage", 1)
    total_pages = metadata.get("totalPages", 1)

    click.echo(f"总共找到 {total_items} 个模型, 当前页: {current_page} / {total_pages}")


@click.command("search")
@click.argument("query", required=False)
@click.option("--limit", type=int, default=10, help="结果数量限制")
@click.option("--page", type=int, default=1, help="页码")
@click.option("--type", help="模型类型 (Checkpoint, LORA, etc.)")
@click.option("--sort", help="排序方式 (Highest Rated, Most Downloaded, Newest)")
@click.option("--period", help="时间范围 (Day, Week, Month, Year, AllTime)")
@click.option("--nsfw/--no-nsfw", default=None, help="是否包含NSFW内容")
@click.option("--username", help="创作者用户名")
@click.option("--tag", help="标签")
def search_models(
    query: Optional[str],
    limit: int,
    page: int,
    type: Optional[str],
    sort: Optional[str],
    period: Optional[str],
    nsfw: Optional[bool],
    username: Optional[str],
    tag: Optional[str]
) -> None:
    """搜索Civitai上的模型"""
    try:
        config = get_config()
        api = CivitaiAPI(
            api_key=config.get("api_key"),
            proxy=config.get("proxy"),
            verify=config.get("verify_ssl", True),
            timeout=config.get("timeout", 30),
            max_retries=config.get("max_retries", 3),
        )

        params = {
            "limit": limit,
            "page": page,
            "query": query,
            "type": type,  # 修改这里，从"types"改为"type"
            "sort": sort,
            "period": period,
            "nsfw": nsfw,
            "username": username,
            "tag": tag,
        }
        # 移除空值参数
        params = {k: v for k, v in params.items() if v is not None}

        click.echo(f"正在搜索模型 (查询: {query or '无'}, 类型: {type or '所有'}, 限制: {limit})...")
        results = api.get_models(**params)

        models = results.get("items", [])
        metadata = results.get("metadata", {})

        if models:
            click.echo("-" * 110)
            click.echo(
                # Ensure this line uses standard string formatting
                "{:<10} {:<40} {:<15} {:<20} {:<10} {:<5}".format(
                    "ID", "名称", "类型", "创作者", "下载量", "评分"
                )
            )
            click.echo("-" * 110)
            for model in models:
                model_id = model.get("id", "N/A")
                model_name = model.get("name", "N/A")
                model_type = model.get("type", "N/A")
                creator = model.get("creator", {}).get("username", "N/A")
                downloads = model.get("stats", {}).get("downloadCount", 0)
                rating = model.get("stats", {}).get("rating", 0)
                click.echo(
                    f"{model_id:<10} {model_name:<40} {model_type:<15} {creator:<20} {downloads:<10} {rating:<5.1f}"
                )
            click.echo("-" * 110)
            click.echo(
                "总共找到 {} 个模型, 当前页: {} / {}".format(
                    metadata.get('totalItems', 0),
                    metadata.get('currentPage', 1),
                    metadata.get('totalPages', 1)
                )
            )
        else:
            click.echo("未找到符合条件的模型。")

    except APIError as e:
        click.secho(f"API错误: {str(e)}", fg="red")
    except Exception as e:
        click.secho(f"搜索模型时发生错误: {str(e)}", fg="red")


if __name__ == "__main__":
    browse()

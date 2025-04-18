"""Browse and search Civitai resources through the command line interface.

Provides commands for browsing models, filter templates, and search history.
"""

import sys
import json
import difflib
from typing import Dict, List, Any, Optional, Union, Tuple, cast

import click
from tabulate import tabulate

from ...api.client import CivitaiAPI, APIError
from ...core.filter import (
    FilterParser, FilterManager, apply_filter,
    sort_results
)
from ...utils.config import get_config
from ...utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Create API client
api = CivitaiAPI()

# Create filter manager
filter_manager = FilterManager()


@click.group(help="Browse and search Civitai resources")
def browse() -> None:
    """Command group for browsing Civitai resources."""
    pass


@browse.command("models")
@click.option("--query", "-q", help="Search keyword")
@click.option(
    "--type", "-t", 
    help="Model type",
    type=click.Choice([
        "Checkpoint", "LORA", "TextualInversion",
        "Hypernetwork", "AestheticGradient", 
        "Controlnet", "Poses"
    ])
)
@click.option(
    "--sort", "-s", 
    help="Sort method",
    type=click.Choice([
        "Highest Rated", "Most Downloaded", 
        "Newest", "Most Liked"
    ])
)
@click.option("--creator", "-c", help="Creator name")
@click.option("--tag", help="Tag")
@click.option("--base-model", help="Base model")
@click.option("--nsfw/--no-nsfw", default=True, help="Include NSFW content")
@click.option("--limit", "-l", type=int, default=20, help="Result limit")
@click.option(
    "--format", "-f", 
    type=click.Choice(["table", "json"]), 
    default="table", 
    help="Output format"
)
@click.option("--output", "-o", help="Output file path")
@click.option("--filter", help="Complex filter condition (JSON format)")
@click.option("--filter-template", help="Use saved filter template")
@click.option("--min-rating", type=float, help="Minimum rating")
@click.option("--max-rating", type=float, help="Maximum rating")
@click.option("--min-downloads", type=int, help="Minimum downloads")
@click.option("--max-downloads", type=int, help="Maximum downloads")
@click.option("--interactive", "-i", is_flag=True, help="Interactive filter mode")
def browse_models(
    query: Optional[str], 
    type: Optional[str], 
    sort: Optional[str],
    creator: Optional[str], 
    tag: Optional[str], 
    base_model: Optional[str],
    nsfw: bool, 
    limit: int, 
    format: str, 
    output: Optional[str],
    filter: Optional[str], 
    filter_template: Optional[str],
    min_rating: Optional[float], 
    max_rating: Optional[float],
    min_downloads: Optional[int], 
    max_downloads: Optional[int],
    interactive: bool
) -> None:
    """Search and browse models on Civitai.
    
    Searches for models using various filters and displays results in
    table or JSON format. Supports client-side filtering and sorting.
    """
    # Display current search parameters
    model_type_str = type if type else "All"
    click.echo(f"Searching models: {query or 'no keyword'} (Type: {model_type_str}, Limit: {limit})")

    try:
        # Build filter condition
        if interactive:
            filter_condition = interactive_filter_builder()
            if not filter_condition:
                click.echo("Search canceled.")
                return
        else:
            # Determine filter condition based on parameters
            filter_condition = determine_filter_condition(
                filter, filter_template, query, type, creator, tag, base_model,
                min_rating, max_rating, min_downloads, max_downloads
            )

        # Convert filter condition to API parameters
        api_params = {}
        if filter_condition:
            api_params = FilterParser.to_api_params(filter_condition)
            logger.debug(f"Filter condition converted to API params: {api_params}")

        # Add basic parameters to API request
        api_params["limit"] = limit
        if query and "query" not in api_params:
            api_params["query"] = query
        if type and "types" not in api_params:
            api_params["types"] = type
        if sort:
            api_params["sort"] = sort
        if not nsfw:
            api_params["nsfw"] = "false"
        if creator and "username" not in api_params:
            api_params["username"] = creator
        if tag and "tag" not in api_params:
            api_params["tag"] = tag
        if base_model:
            api_params["baseModel"] = base_model

        # Warn if filters need client-side processing
        if filter_condition and len(api_params) <= 3:
            click.echo("Warning: Some filter conditions cannot be converted to API parameters and will be applied client-side", err=True)

        # Execute search
        click.echo("Searching models, please wait...")
        response = api.get_models(api_params)
        models = response.get("items", [])

        if not models:
            click.echo("No matching models found")
            return

        # Apply client-side filtering if needed
        if filter_condition:
            original_count = len(models)
            models = apply_filter(models, filter_condition)
            if len(models) < original_count:
                click.echo(f"Client-side filtering: {len(models)} matches out of {original_count} results")

        # Apply client-side sorting for parameters that can't be handled by API
        client_sort_fields = {
            "min_rating": "stats.rating",
            "max_rating": "stats.rating",
            "min_downloads": "stats.downloadCount",
            "max_downloads": "stats.downloadCount"
        }

        for param, field in client_sort_fields.items():
            if locals()[param] is not None:
                click.echo(f"Sorting results by {field}")
                ascending = param.startswith("min_")
                models = sort_results(models, field, ascending)

        # Add to search history
        if filter_condition:
            filter_manager.add_to_history(filter_condition)

        # Display results
        display_search_results(models, format, output)

        # Show pagination info
        metadata = response.get("metadata", {})
        total_count = metadata.get("totalItems", 0)
        current_page = metadata.get("currentPage", 1)
        total_pages = metadata.get("totalPages", 1)
        click.echo(f"\nTotal: {total_count} results, Page: {current_page}/{total_pages}")

        # Show tips
        click.echo("Tip: Use --filter for complex filter conditions")
        click.echo("     Use --filter-template to apply saved filter templates")

    except APIError as e:
        logger.error(f"API Error: {str(e)}")
        click.echo(f"Search failed: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Search failed: {str(e)}")
        click.echo(f"Search failed: {str(e)}", err=True)
        sys.exit(1)


@browse.command("templates")
@click.option("--list", "-l", is_flag=True, help="列出所有模板")
@click.option("--add", "-a", help="添加新模板 (需要同时指定--filter)")
@click.option("--filter", "-f", help="模板筛选条件 (JSON格式)")
@click.option("--remove", "-r", help="删除模板")
@click.option("--show", "-s", help="显示模板内容")
def browse_templates(list: bool, add: Optional[str], filter: Optional[str], remove: Optional[str], show: Optional[str]) -> None:
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
        click.echo(f"{i+1}. [{record['timestamp']}]\n   {json.dumps(record['condition'], indent=2)}")
        if i < len(history) - 1:
            click.echo("")


def determine_filter_condition(
    filter_json: Optional[str], 
    template_name: Optional[str], 
    query: Optional[str], 
    type: Optional[str], 
    creator: Optional[str],
    tag: Optional[str], 
    base_model: Optional[str], 
    min_rating: Optional[float], 
    max_rating: Optional[float],
    min_downloads: Optional[int], 
    max_downloads: Optional[int]
) -> Dict[str, Any]:
    """Determine filter condition with priority: filter > template > other parameters.
    
    Args:
        filter_json: JSON filter condition (highest priority)
        template_name: Name of a saved filter template
        query: Search query keyword
        type: Model type filter
        creator: Creator username filter
        tag: Tag filter
        base_model: Base model filter
        min_rating: Minimum rating threshold
        max_rating: Maximum rating threshold
        min_downloads: Minimum downloads threshold
        max_downloads: Maximum downloads threshold
        
    Returns:
        Filter condition dictionary
        
    Raises:
        SystemExit: If filter JSON parsing fails or template not found
    """
    if filter_json:
        try:
            return json.loads(filter_json)
        except json.JSONDecodeError as e:
            click.echo(f"Failed to parse filter condition: {str(e)}", err=True)
            sys.exit(1)

    if template_name:
        template = filter_manager.get_template(template_name)
        if template:
            return template
        else:
            click.echo(f"Filter template '{template_name}' not found", err=True)
            sys.exit(1)

    # Build filter condition from parameters
    cli_params = {
        "query": query,
        "type": type,
        "creator": creator,
        "tag": tag,
        "base_model": base_model,
        "min_rating": min_rating,
        "max_rating": max_rating,
        "min_downloads": min_downloads,
        "max_downloads": max_downloads
    }

    # Remove None values
    cli_params = {k: v for k, v in cli_params.items() if v is not None}

    # Return empty dict if no parameters provided
    if not cli_params:
        return {}

    # Convert to filter condition
    return FilterParser.parse_cli_params(cli_params)


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
            click.secho(f"✓ Added condition: ", fg="green", nl=False)
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
            "types": [type] if type else None,
            "sort": sort,
            "period": period,
            "nsfw": nsfw,
            "username": username,
            "tag": tag,
        }
        # 移除空值参数
        params = {k: v for k, v in params.items() if v is not None}

        click.echo(f"正在搜索模型 (查询: {query or '无'}, 类型: {type or '所有'}, 限制: {limit})...")
        results = api.get_models(params=params)

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
                f"总共找到 {metadata.get('totalItems', 0)} 个模型, "
                f"当前页: {metadata.get('currentPage', 1)} / {metadata.get('totalPages', 1)}"
            )
        else:
            click.echo("未找到符合条件的模型。")

    except APIError as e:
        click.secho(f"API错误: {str(e)}", fg="red")
    except Exception as e:
        click.secho(f"搜索模型时发生错误: {str(e)}", fg="red")


if __name__ == "__main__":
    browse()

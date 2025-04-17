import os
import sys
import json
import click
import logging
from typing import Dict, List, Any, Optional
from tabulate import tabulate

from ...api.client import CivitaiAPI, APIError
from ...core.filter import (
    FilterParser, FilterManager, apply_filter, 
    sort_results, DEFAULT_TEMPLATES
)

# 配置日志
logger = logging.getLogger(__name__)

# 创建API客户端
api = CivitaiAPI()

# 创建筛选管理器
filter_manager = FilterManager()

@click.group(help="浏览和搜索Civitai资源")
def browse():
    """浏览命令组"""
    pass

@browse.command("models")
@click.option("--query", "-q", help="搜索关键词")
@click.option("--type", "-t", help="模型类型", 
              type=click.Choice(["Checkpoint", "LORA", "TextualInversion", 
                              "Hypernetwork", "AestheticGradient", "Controlnet", "Poses"]))
@click.option("--sort", "-s", help="排序方式", 
              type=click.Choice(["Newest", "Most Downloaded", "Highest Rated", "Most Liked"]))
@click.option("--creator", "-c", help="创作者名称")
@click.option("--tag", help="标签")
@click.option("--base-model", help="基础模型")
@click.option("--nsfw/--no-nsfw", default=True, help="是否包含NSFW内容")
@click.option("--limit", "-l", type=int, default=20, help="结果数量")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table", help="输出格式")
@click.option("--output", "-o", help="输出文件路径")
@click.option("--filter", help="复杂筛选条件(JSON格式)")
@click.option("--filter-template", help="使用筛选模板")
@click.option("--min-rating", type=float, help="最低评分")
@click.option("--max-rating", type=float, help="最高评分")
@click.option("--min-downloads", type=int, help="最低下载量")
@click.option("--max-downloads", type=int, help="最高下载量")
@click.option("--interactive", "-i", is_flag=True, help="交互式筛选模式")
def browse_models(query, type, sort, creator, tag, base_model, nsfw, limit, 
                format, output, filter, filter_template, min_rating, max_rating, 
                min_downloads, max_downloads, interactive):
    """搜索和浏览模型"""
    # 显示当前搜索条件
    model_type_str = type if type else "全部"
    click.echo(f"搜索模型: {query or '无关键词'} (类型: {model_type_str}, 限制: {limit})")
    
    try:
        # 如果选择交互式模式，进入交互式筛选
        if interactive:
            filter_condition = interactive_filter_builder()
        else:
            # 确定筛选条件
            filter_condition = determine_filter_condition(
                filter, filter_template, query, type, creator, tag, base_model,
                min_rating, max_rating, min_downloads, max_downloads
            )
        
        # 将筛选条件转换为API参数
        api_params = {}
        if filter_condition:
            api_params = FilterParser.to_api_params(filter_condition)
        
        # 添加基本参数
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
        
        # 如果有参数未能转换为API参数，记录提示
        if filter_condition and len(api_params) <= 3:  # 基本上只有limit和可能的类型/查询参数
            click.echo("警告: 部分筛选条件无法直接转换为API参数，将在客户端进行筛选", err=True)
        
        # 显示正在执行搜索
        click.echo("正在搜索模型，请稍候...")
        
        # 获取模型列表
        response = api.get_models(api_params)
        
        # 提取模型列表
        models = response.get("items", [])
        
        if not models:
            click.echo("没有找到匹配的模型")
            return
        
        # 应用客户端筛选
        if filter_condition:
            original_count = len(models)
            models = apply_filter(models, filter_condition)
            if len(models) < original_count:
                click.echo(f"客户端筛选: 从 {original_count} 个结果中筛选出 {len(models)} 个匹配项")
        
        # 应用客户端排序 (如果需要)
        client_sort_fields = {
            "min_rating": "stats.rating",
            "max_rating": "stats.rating", 
            "min_downloads": "stats.downloadCount",
            "max_downloads": "stats.downloadCount"
        }
        
        for param, field in client_sort_fields.items():
            if locals()[param] is not None:
                click.echo(f"按 {field} 排序结果")
                ascending = param.startswith("min_")
                models = sort_results(models, field, ascending)
        
        # 添加到历史记录
        if filter_condition:
            filter_manager.add_to_history(filter_condition)
        
        # 格式化输出
        display_search_results(models, format, output)
        
        # 显示分页信息
        metadata = response.get("metadata", {})
        total_count = metadata.get("totalItems", 0)
        current_page = metadata.get("currentPage", 1)
        total_pages = metadata.get("totalPages", 1)
        
        click.echo(f"\n总共 {total_count} 个结果，当前第 {current_page}/{total_pages} 页")
        
        # 显示提示
        click.echo("提示: 使用 --filter 参数可以指定复杂筛选条件")
        click.echo("      使用 --filter-template 参数可以使用保存的筛选模板")
    
    except APIError as e:
        logger.error(f"API错误: {str(e)}")
        click.echo(f"搜索失败: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.exception(f"搜索失败: {str(e)}")
        click.echo(f"搜索失败: {str(e)}", err=True)
        sys.exit(1)

@browse.command("templates")
@click.option("--list", "-l", is_flag=True, help="列出所有模板")
@click.option("--add", "-a", help="添加新模板 (需要同时指定--filter)")
@click.option("--filter", "-f", help="模板筛选条件 (JSON格式)")
@click.option("--remove", "-r", help="删除模板")
@click.option("--show", "-s", help="显示模板内容")
def browse_templates(list, add, filter, remove, show):
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
                click.echo(f"添加模板失败", err=True)
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
def browse_history(limit, clear):
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
        click.echo(f"{i+1}. [{record['timestamp']}]")
        click.echo(f"   {json.dumps(record['condition'], indent=2)}")
        if i < len(history) - 1:
            click.echo("")

def determine_filter_condition(filter_json, template_name, query, type, creator, 
                               tag, base_model, min_rating, max_rating, 
                               min_downloads, max_downloads) -> Dict[str, Any]:
    """确定筛选条件，优先级: filter > template > 其他参数"""
    if filter_json:
        try:
            return json.loads(filter_json)
        except json.JSONDecodeError as e:
            click.echo(f"解析筛选条件失败: {str(e)}", err=True)
            sys.exit(1)
    
    if template_name:
        template = filter_manager.get_template(template_name)
        if template:
            return template
        else:
            click.echo(f"筛选模板 '{template_name}' 不存在", err=True)
            sys.exit(1)
    
    # 构建基于参数的筛选条件
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
    
    # 过滤掉None值
    cli_params = {k: v for k, v in cli_params.items() if v is not None}
    
    # 如果没有参数，返回空条件
    if not cli_params:
        return {}
    
    # 转换为筛选条件
    return FilterParser.parse_cli_params(cli_params)

def display_search_results(models: List[Dict[str, Any]], format_type: str, output_file: Optional[str] = None) -> None:
    """显示搜索结果
    
    Args:
        models: 模型列表
        format_type: 输出格式 (table/json)
        output_file: 输出文件路径
    """
    if format_type == "json":
        result = json.dumps(models, indent=2)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            click.echo(f"结果已保存到 {output_file}")
        else:
            click.echo(result)
    else:  # table
        # 提取表格数据
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
        
        # 生成表格
        headers = ["ID", "名称", "类型", "创作者", "下载次数", "评分"]
        table = tabulate(table_data, headers=headers, tablefmt="grid")
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(table)
            click.echo(f"结果已保存到 {output_file}")
        else:
            click.echo(table)

def interactive_filter_builder() -> Dict[str, Any]:
    """交互式筛选条件构建器
    
    Returns:
        构建的筛选条件
    """
    conditions = []
    
    click.echo("=== 交互式筛选条件构建器 ===")
    click.echo("输入筛选条件，每次一个，输入空行完成")
    click.echo("格式：字段 操作符 值")
    click.echo("例如：type = LORA")
    click.echo("可用操作符：= (等于), != (不等于), > (大于), >= (大于等于), < (小于), <= (小于等于)")
    click.echo("按Ctrl+C取消")
    
    try:
        while True:
            condition_str = click.prompt("筛选条件", default="", show_default=False)
            if not condition_str.strip():
                break
            
            # 解析条件
            parts = condition_str.split(maxsplit=2)
            if len(parts) != 3:
                click.echo("无效格式，请使用'字段 操作符 值'")
                continue
            
            field, op_str, value = parts
            
            # 映射操作符
            op_map = {
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
                "in": "in"
            }
            
            if op_str not in op_map:
                click.echo(f"不支持的操作符: {op_str}")
                continue
            
            # 尝试转换值类型
            try:
                # 尝试转换为数字
                if value.isdigit():
                    value = int(value)
                elif value.replace(".", "", 1).isdigit():
                    value = float(value)
            except (ValueError, TypeError):
                pass
            
            # 添加条件
            conditions.append({
                "field": field,
                "op": op_map[op_str],
                "value": value
            })
            
            # 显示当前条件
            click.echo(f"添加条件: {field} {op_str} {value}")
    
    except (KeyboardInterrupt, EOFError):
        click.echo("\n已取消")
        return {}
    
    # 如果没有条件，返回空字典
    if not conditions:
        return {}
    
    # 如果有多个条件，询问逻辑关系
    if len(conditions) > 1:
        logic = click.prompt("条件间的逻辑关系", type=click.Choice(["and", "or"]), default="and")
        return {logic: conditions}
    else:
        return conditions[0]

if __name__ == "__main__":
    browse()

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
@click.option("--query", "-q", help="Search keywords")
@click.option("--types", "-t", multiple=True, help="Model type (Checkpoint, LORA, TextualInversion, etc., multiple selections allowed)")
@click.option("--tag", help="Model tag")
@click.option("--sort", help="Sort order (Newest, Most Downloaded, Highest Rated, etc.)")
@click.option("--limit", "-l", type=int, default=20, help="Result limit")
@click.option("--nsfw", is_flag=True, help="Include NSFW content")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json"]), default="table", help="Output format")
@click.option("--creator", "-c", help="Creator username")
@click.option("--base-model", "-b", help="Base model")
@click.option("--filter", "filter_json", help="Advanced filter conditions (JSON format)")
@click.option("--template", help="Use filter template")
def browse_models(query, types, tag, sort, limit, nsfw, output_format, creator, base_model, filter_json, template):
    """Browse and search models"""
    try:
        # Get configuration
        config = get_config()

        # Create API client
        api_client = CivitaiAPI(
            api_key=config.get("api_key"),
            proxy=config.get("proxy"),
            verify=config.get("verify_ssl", True),
            timeout=config.get("timeout", 30),
            max_retries=config.get("max_retries", 3),
        )

        # Use filter manager
        mgr = FilterManager()

        # Determine filter conditions
        condition = determine_filter_condition(
            query=query,
            types=types,
            tag=tag,
            sort=sort,
            limit=limit,
            nsfw=nsfw,
            creator=creator,
            base_model=base_model,
            filter_json=filter_json,
            template_name=template,
            filter_manager=mgr
        )

        # Build API parameters using FilterBuilder
        filter_builder = FilterBuilder()
        params = filter_builder.build_params(condition)

        # Save filter history
        mgr.add_to_history(condition)

        # Get model list
        results = api_client.get_models(**params)

        # Process results
        display_model_results(results, output_format)

    except Exception as e:
        click.secho(f"Error browsing models: {str(e)}", fg="red")
        logger.exception("Failed to browse models")
        sys.exit(1)


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
    """Determine filter conditions, priority: Filter Template > Advanced Filter Conditions > Basic Parameters"""

    # If template name is provided, use template
    if template_name and filter_manager:
        condition = _get_template_condition(template_name, filter_manager, limit)
        if condition:
            return condition

    # If advanced filter conditions are provided, parse and use
    if filter_json:
        condition = _get_json_condition(filter_json, limit)
        if condition:
            return condition

    # Build conditions using basic parameters
    return _build_basic_condition(query, types, tag, sort, limit, nsfw, creator, base_model)


def _get_template_condition(
    template_name: str, filter_manager: FilterManager, limit: Optional[int]
) -> Optional[Dict[str, Any]]:
    """Get template condition"""
    template = filter_manager.get_template(template_name)
    if not template:
        click.echo(f"Template not found: {template_name}")
        return None

    # Add limit parameter (if not specified in template)
    if limit and "limit" not in json.dumps(template):
        import copy
        condition = copy.deepcopy(template)
        _add_limit_to_condition(condition, limit)
        return condition
    return template


def _get_json_condition(filter_json: str, limit: Optional[int]) -> Optional[Dict[str, Any]]:
    """Get JSON condition"""
    try:
        condition = parse_filter_condition(filter_json)
        if limit and "limit" not in filter_json:
            _add_limit_to_condition(condition, limit)
        return condition
    except Exception as e:
        logger.error(f"Failed to parse filter conditions: {e}")
        click.echo(f"Failed to parse filter conditions: {e}")
        return None


def _add_limit_to_condition(condition: Dict[str, Any], limit: int) -> None:
    """Add limit to condition"""
    limit_condition = {"field": "limit", "op": "eq", "value": limit}

    # If already an AND condition, just append the limit.
    if "and" in condition:
        and_clause = condition.get("and")
        if isinstance(and_clause, list):
            and_clause.append(limit_condition)
        else:
            # Defensive: avoid corrupting unexpected structures.
            logger.warning("Cannot add limit to condition: 'and' clause is not a list, skipping automatic limit.")
        return

    # For simple conditions (only field/op/value), safely transform to AND condition.
    simple_keys = {"field", "op", "value"}
    condition_keys = set(condition.keys())
    if condition_keys == simple_keys:
        original_condition = condition.copy()
        condition.clear()
        condition["and"] = [
            original_condition,
            limit_condition,
        ]
        return

    # Defensive fallback: condition shape is more complex than expected.
    # Do not attempt to restructure it to avoid losing or misplacing data.
    logger.warning("Complex filter condition structure detected, skipping automatic limit addition.")


def _build_basic_condition(query, types, tag, sort, limit, nsfw, creator, base_model) -> Dict[str, Any]:
    """Build basic condition"""
    condition = {"and": []}

    if query:
        condition["and"].append({"field": "query", "op": "eq", "value": query})
    if types:
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

    # If no conditions, return empty query
    if not condition["and"]:
        return {"field": "query", "op": "eq", "value": ""}

    return condition


@browse.command("templates")
@click.option("--list", "-l", "list_templates_flag", is_flag=True, help="List all templates")
@click.option("--add", "-a", help="Add new template (requires --filter)")
@click.option("--filter", "-f", "filter_json", help="Template filter conditions (JSON format)")
@click.option("--remove", "-r", help="Remove template")
@click.option("--show", "-s", help="Show template content")
def browse_templates(
        list_templates_flag: bool,
        add: Optional[str],
        filter_json: Optional[str],
        remove: Optional[str],
        show: Optional[str]) -> None:
    """Manage filter templates"""
    # If no operation specified, default to listing all templates
    if not any([list_templates_flag, add, remove, show]):
        list_templates_flag = True

    # List all templates
    if list_templates_flag:
        templates = filter_manager.list_templates()
        if not templates:
            click.echo("No saved filter templates")
            return

        click.echo("Saved filter templates:")
        for name in templates:
            click.echo(f"  - {name}")

    # Add new template
    if add:
        if not filter_json:
            click.echo("Error: Must specify --filter parameter when adding template", err=True)
            return

        try:
            condition = json.loads(filter_json)
            if filter_manager.add_template(add, condition):
                click.echo(f"Template '{add}' added successfully")
            else:
                click.echo("Failed to add template", err=True)
        except json.JSONDecodeError:
            click.echo("Error: Filter condition must be valid JSON format", err=True)

    # Remove template
    if remove:
        if filter_manager.remove_template(remove):
            click.echo(f"Template '{remove}' removed successfully")
        else:
            click.echo(f"Template '{remove}' does not exist", err=True)

    # Show template content
    if show:
        template = filter_manager.get_template(show)
        if template:
            click.echo(f"Template '{show}':")
            click.echo(json.dumps(template, indent=2))
        else:
            click.echo(f"Template '{show}' does not exist", err=True)


@browse.command("history")
@click.option("--limit", "-l", type=int, default=10, help="Number of history records to show")
@click.option("--clear", "-c", is_flag=True, help="Clear history")
def browse_history(limit: int, clear: bool) -> None:
    """View filter history"""
    if clear:
        filter_manager.clear_history()
        click.echo("History cleared")
        return

    history = filter_manager.get_history()
    if not history:
        click.echo("No filter history")
        return

    click.echo("Recent filter history:")
    for i, record in enumerate(history[:limit]):
        click.echo(f"{i+1}. [{record['timestamp']}]\n   {json.dumps(record['condition'], indent=2)}")
        if i < len(history) - 1:
            click.echo("")


def display_model_results(results: Dict[str, Any], format_type: str, output_file: Optional[str] = None) -> None:
    """Process and display model search results

    Args:
        results: Search results returned by API
        format_type: Output format (table/json)
    """
    if not results or "items" not in results:
        click.echo("No results found")
        return

    models = results.get("items", [])
    metadata = results.get("metadata", {})

    # Call existing display_search_results function to display results
    display_search_results(models, format_type)

    # Display metadata info
    total_items = metadata.get("totalItems", len(models))
    current_page = metadata.get("currentPage", 1)
    total_pages = metadata.get("totalPages", 1)

    click.echo(f"Found {total_items} models in total, Current Page: {current_page} / {total_pages}")


@click.command("search")
@click.argument("query", required=False)
@click.option("--limit", type=int, default=10, help="Result limit")
@click.option("--page", type=int, default=1, help="Page number")
@click.option("--type", "model_type", help="Model type (Checkpoint, LORA, etc.)")
@click.option("--sort", help="Sort order (Highest Rated, Most Downloaded, Newest)")
@click.option("--period", help="Time period (Day, Week, Month, Year, AllTime)")
@click.option("--nsfw/--no-nsfw", default=None, help="Include NSFW content")
@click.option("--username", help="Creator username")
@click.option("--tag", help="Tag")
def search_models(
    query: Optional[str],
    limit: int,
    page: int,
    model_type: Optional[str],
    sort: Optional[str],
    period: Optional[str],
    nsfw: Optional[bool],
    username: Optional[str],
    tag: Optional[str]
) -> None:
    """Search models on Civitai"""
    try:
        config = get_config()
        api_client = CivitaiAPI(
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
            "type": model_type,
            "sort": sort,
            "period": period,
            "nsfw": nsfw,
            "username": username,
            "tag": tag,
        }
        # Remove null parameters
        params = {k: v for k, v in params.items() if v is not None}

        click.echo(f"Searching models (Query: {query or 'None'}, Type: {model_type or 'All'}, Limit: {limit})...")
        results = api_client.get_models(**params)

        models = results.get("items", [])
        metadata = results.get("metadata", {})

        if models:
            click.echo("-" * 110)
            click.echo(
                "{:<10} {:<40} {:<15} {:<20} {:<10} {:<5}".format(
                    "ID", "Name", "Type", "Creator", "Downloads", "Rating"
                )
            )
            click.echo("-" * 110)
            for model in models:
                model_id = model.get("id", "N/A")
                model_name = model.get("name", "N/A")
                model_type_str = model.get("type", "N/A")
                creator = model.get("creator", {}).get("username", "N/A")
                downloads = model.get("stats", {}).get("downloadCount", 0)
                rating = model.get("stats", {}).get("rating", 0)
                click.echo(
                    f"{model_id:<10} {model_name:<40} {model_type_str:<15} {creator:<20} {downloads:<10} {rating:<5.1f}"
                )
            click.echo("-" * 110)
            click.echo(
                "Found {} models in total, Current Page: {} / {}".format(
                    metadata.get('totalItems', 0),
                    metadata.get('currentPage', 1),
                    metadata.get('totalPages', 1)
                )
            )
        else:
            click.echo("No matching models found.")

    except APIError as e:
        click.secho(f"API Error: {str(e)}", fg="red")
    except Exception as e:
        click.secho(f"Error searching models: {str(e)}", fg="red")


if __name__ == "__main__":
    browse()

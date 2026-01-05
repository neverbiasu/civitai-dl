import re
import os
import json
import operator
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TypeVar

from civitai_dl.utils.config import CONFIG_DIR
from civitai_dl.utils.logger import get_logger
from civitai_dl.core.constants import NON_QUOTE_CHARS, STATS_RATING, STATS_DOWNLOAD_COUNT

logger = get_logger(__name__)

T = TypeVar('T')

OPERATORS = {
    "eq": operator.eq,
    "ne": operator.ne,
    "lt": operator.lt,
    "le": operator.le,
    "gt": operator.gt,
    "ge": operator.ge,
    "in": lambda x, y: x in y,
    "nin": lambda x, y: x not in y,
    "contains": lambda x, y: y in x if isinstance(x, str) else False,
    "startswith": lambda x, y: x.startswith(y) if isinstance(x, str) else False,
    "endswith": lambda x, y: x.endswith(y) if isinstance(x, str) else False,
    "regex": lambda x, y: bool(re.search(y, x)) if isinstance(x, str) else False,
}

LOGIC_OPS = {"and", "or", "not"}


class FilterCondition:
    """Represents a filter condition expression that can be evaluated against data items."""

    def __init__(self, condition: Dict[str, Any]):
        self.condition = condition
        self._validate_condition(condition)

    def _validate_condition(self, condition: Dict[str, Any]) -> None:
        if any(op in condition for op in LOGIC_OPS):
            logic_ops = [op for op in LOGIC_OPS if op in condition]
            if len(logic_ops) != 1:
                raise ValueError(f"Only one logic operator allowed: {condition}")

            logic_op = logic_ops[0]
            if logic_op == "not":
                if not isinstance(condition["not"], dict):
                    raise ValueError(f"'not' operator requires a condition dictionary: {condition}")
            else:
                if not isinstance(condition[logic_op], list) or len(condition[logic_op]) < 1:
                    raise ValueError(f"'{logic_op}' operator requires a list of conditions: {condition}")
        else:
            if "field" not in condition or "op" not in condition or "value" not in condition:
                raise ValueError(f"Simple condition requires 'field', 'op', and 'value' keys: {condition}")

            if condition["op"] not in OPERATORS:
                raise ValueError(f"Unsupported operator: {condition['op']}")

    def match(self, item: Dict[str, Any]) -> bool:
        return self._evaluate(self.condition, item)

    def _evaluate_simple(self, condition: Dict[str, Any], item: Dict[str, Any]) -> bool:
        field = condition["field"]
        op = condition["op"]
        value = condition["value"]

        field_value = item
        for part in field.split('.'):
            if isinstance(field_value, dict) and part in field_value:
                field_value = field_value[part]
            else:
                return False

        if isinstance(value, str) and isinstance(field_value, (int, float)):
            try:
                value = type(field_value)(value)
            except (ValueError, TypeError):
                return False

        try:
            return OPERATORS[op](field_value, value)
        except Exception as e:
            logger.debug(f"Filter condition evaluation error: {op}({field_value}, {value}): {str(e)}")
            return False

    def _evaluate(self, condition: Dict[str, Any], item: Dict[str, Any]) -> bool:
        if "and" in condition:
            return all(self._evaluate(subcond, item) for subcond in condition["and"])

        if "or" in condition:
            return any(self._evaluate(subcond, item) for subcond in condition["or"])

        if "not" in condition:
            return not self._evaluate(condition["not"], item)

        return self._evaluate_simple(condition, item)


class FilterParser:
    """Filter condition parser for parsing and converting different formats of filter conditions."""

    @staticmethod
    def _parse_op(op_str: str) -> str:
        if not op_str:
            return "eq"
        if op_str == '>':
            return "gt"
        elif op_str == '>=':
            return "ge"
        elif op_str == '<':
            return "lt"
        elif op_str == '<=':
            return "le"
        elif op_str == '~':
            return "contains"
        elif op_str == '!':
            return "ne"
        return "eq"

    @staticmethod
    def parse_query_string(query: str) -> Dict[str, Any]:
        if not query.strip():
            return {}

        parts = re.findall(rf'([a-zA-Z0-9_.]+)(:([<>]?=?|~|!)?({NON_QUOTE_CHARS}|\".+?\")|\s+|$)', query)
        conditions = []

        for field, _, op_str, value in parts:
            if not field or not value:
                continue

            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]

            op = FilterParser._parse_op(op_str)

            conditions.append({
                "field": field,
                "op": op,
                "value": value
            })

        if len(conditions) > 1:
            return {"and": conditions}
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {}

    @staticmethod
    def parse_json(json_str: str) -> Dict[str, Any]:
        try:
            condition = json.loads(json_str)
            FilterCondition(condition)
            return condition
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")

    @staticmethod
    def parse_cli_params(params: Dict[str, Any]) -> Dict[str, Any]:
        conditions = []
        mapping = {
            "query": {"field": "name", "op": "contains"},
            "type": {"field": "type", "op": "eq"},
            "creator": {"field": "creator.username", "op": "eq"},
            "tag": {"field": "tags", "op": "in"},
            "base_model": {"field": "modelVersions.baseModel", "op": "eq"},
            "min_rating": {"field": STATS_RATING, "op": "ge"},
            "max_rating": {"field": STATS_RATING, "op": "le"},
            "min_downloads": {"field": STATS_DOWNLOAD_COUNT, "op": "ge"},
            "max_downloads": {"field": STATS_DOWNLOAD_COUNT, "op": "le"},
        }

        for param, value in params.items():
            if param in mapping and value is not None:
                field_map = mapping[param]
                conditions.append({
                    "field": field_map["field"],
                    "op": field_map["op"],
                    "value": value
                })

        if len(conditions) > 1:
            return {"and": conditions}
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {}

    @staticmethod
    def to_api_params(condition: Dict[str, Any]) -> Dict[str, Any]:
        if not condition:
            return {}

        if "field" in condition and "op" in condition and "value" in condition:
            return FilterParser._map_condition_to_param(condition)

        if "and" in condition:
            params = {}
            for subcond in condition["and"]:
                params.update(FilterParser.to_api_params(subcond))
            return params

        if "or" in condition:
            if condition["or"]:
                return FilterParser.to_api_params(condition["or"][0])
            return {}

        return {}

    @staticmethod
    def _map_condition_to_param(condition: Dict[str, Any]) -> Dict[str, Any]:
        field = condition["field"]
        op = condition["op"]
        value = condition["value"]

        field_mapping = {
            "name": "query",
            "types": "types",
            "tag": "tag",
            "sort": "sort",
            "limit": "limit",
            "nsfw": "nsfw",
            "creator.username": "username",
            "modelVersions.baseModel": "baseModel",
        }

        op_mapping = {
            "eq": "",
            "in": "",
            "contains": "",
        }

        if field in field_mapping:
            param_name = field_mapping[field]
            if op in op_mapping:
                return {param_name: value}

        return {}


class FilterManager:
    def __init__(self, templates_file: Optional[str] = None, history_file: Optional[str] = None):
        self.templates_file = templates_file or os.path.join(CONFIG_DIR, "filter_templates.json")
        self.history_file = history_file or os.path.join(CONFIG_DIR, "filter_history.json")
        self.templates = self._load_templates()
        self.history = self._load_history()

    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        try:
            if os.path.exists(self.templates_file):
                with open(self.templates_file, "r", encoding="utf-8") as f:
                    templates = json.load(f)
                return templates
            return DEFAULT_TEMPLATES.copy()
        except Exception as e:
            logger.error(f"Failed to load filter templates: {str(e)}")
            return DEFAULT_TEMPLATES.copy()

    def _save_templates(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.templates_file), exist_ok=True)
            with open(self.templates_file, "w", encoding="utf-8") as f:
                json.dump(self.templates, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save filter templates: {str(e)}")
            return False

    def _load_history(self) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
                return history
            return []
        except Exception as e:
            logger.error(f"Failed to load filter history: {str(e)}")
            return []

    def _save_history(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save filter history: {str(e)}")
            return False

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        return self.templates.get(name)

    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        return self.templates

    def add_template(self, name: str, condition: Dict[str, Any]) -> bool:
        self.templates[name] = condition
        return self._save_templates()

    def remove_template(self, name: str) -> bool:
        if name in self.templates:
            del self.templates[name]
            return self._save_templates()
        return False

    def add_to_history(self, condition: Dict[str, Any]) -> bool:
        record = {
            "timestamp": datetime.now().isoformat(),
            "condition": condition
        }
        self.history.insert(0, record)
        if len(self.history) > 50:
            self.history = self.history[:50]
        return self._save_history()

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history

    def clear_history(self) -> bool:
        self.history = []
        return self._save_history()

    def list_templates(self) -> Dict[str, Dict[str, Any]]:
        return self.get_all_templates()


def apply_filter(items: List[Dict[str, Any]], condition: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not condition:
        return items

    try:
        filter_condition = FilterCondition(condition)
        return [item for item in items if filter_condition.match(item)]
    except Exception as e:
        logger.error(f"Failed to apply filter condition: {str(e)}")
        return items


def sort_results(items: List[Dict[str, Any]], sort_by: str, ascending: bool = False) -> List[Dict[str, Any]]:
    if not sort_by:
        return items

    def get_value(item, field):
        value = item
        for part in field.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value

    try:
        sorted_items = sorted(
            items,
            key=lambda x: (get_value(x, sort_by) is None, get_value(x, sort_by)),
            reverse=not ascending
        )
        return sorted_items
    except Exception as e:
        logger.error(f"Failed to sort: {str(e)}")
        return items


DEFAULT_TEMPLATES = {
    "High Quality LORA": {
        "and": [
            {"field": "type", "op": "eq", "value": "LORA"},
            {"field": STATS_RATING, "op": "ge", "value": 4.5},
            {"field": STATS_DOWNLOAD_COUNT, "op": "ge", "value": 1000}
        ]
    },
    "New Popular Checkpoint": {
        "and": [
            {"field": "type", "op": "eq", "value": "Checkpoint"},
            {"field": STATS_DOWNLOAD_COUNT, "op": "ge", "value": 500},
            {"field": "publishedAt", "op": "ge", "value": (datetime.now() - timedelta(days=30)).isoformat()}
        ]
    }
}


class FilterBuilder:
    """Builder class for constructing filter parameters from conditions."""

    def build_params(self, condition: Dict[str, Any]) -> Dict[str, Any]:
        return FilterParser.to_api_params(condition)


def parse_filter_condition(condition_str: str) -> Dict[str, Any]:
    if condition_str.strip().startswith("{"):
        try:
            return FilterParser.parse_json(condition_str)
        except ValueError:
            pass

    return FilterParser.parse_query_string(condition_str)

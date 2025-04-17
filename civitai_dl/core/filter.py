import re
import os
import json
import logging
import operator
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 配置日志
logger = logging.getLogger(__name__)

# 筛选操作符映射
OPERATORS = {
    "eq": operator.eq,            # 等于
    "ne": operator.ne,            # 不等于
    "lt": operator.lt,            # 小于
    "le": operator.le,            # 小于等于
    "gt": operator.gt,            # 大于
    "ge": operator.ge,            # 大于等于
    "in": lambda x, y: x in y,    # 包含于
    "nin": lambda x, y: x not in y,  # 不包含于
    "contains": lambda x, y: y in x if isinstance(x, str) else False,  # 字符串包含
    "startswith": lambda x, y: x.startswith(y) if isinstance(x, str) else False,  # 字符串开头
    "endswith": lambda x, y: x.endswith(y) if isinstance(x, str) else False,     # 字符串结尾
    "regex": lambda x, y: bool(re.search(y, x)) if isinstance(x, str) else False,  # 正则匹配
}

# 逻辑操作符
LOGIC_OPS = {"and", "or", "not"}


class FilterCondition:
    """筛选条件表达式"""

    def __init__(self, condition: Dict[str, Any]):
        """初始化筛选条件

        Args:
            condition: 条件字典
        """
        self.condition = condition
        self._validate_condition(condition)

    def _validate_condition(self, condition: Dict[str, Any]) -> None:
        """验证条件格式是否有效

        Args:
            condition: 条件字典

        Raises:
            ValueError: 条件格式无效
        """
        # 检查逻辑操作符
        if any(op in condition for op in LOGIC_OPS):
            # 逻辑条件
            logic_ops = [op for op in LOGIC_OPS if op in condition]
            if len(logic_ops) != 1:
                raise ValueError(f"只能有一个逻辑操作符: {condition}")

            logic_op = logic_ops[0]
            if logic_op == "not":
                if not isinstance(condition["not"], dict):
                    raise ValueError(f"'not'操作符需要一个条件字典: {condition}")
            else:  # and, or
                if not isinstance(condition[logic_op], list) or len(condition[logic_op]) < 1:
                    raise ValueError(f"'{logic_op}'操作符需要一个条件列表: {condition}")
        else:
            # 简单条件
            if "field" not in condition or "op" not in condition or "value" not in condition:
                raise ValueError(f"简单条件需要'field'、'op'和'value'键: {condition}")

            if condition["op"] not in OPERATORS:
                raise ValueError(f"不支持的操作符: {condition['op']}")

    def match(self, item: Dict[str, Any]) -> bool:
        """判断一个项是否匹配条件

        Args:
            item: 要匹配的项

        Returns:
            是否匹配
        """
        return self._evaluate(self.condition, item)

    def _evaluate(self, condition: Dict[str, Any], item: Dict[str, Any]) -> bool:
        """递归评估条件

        Args:
            condition: 条件字典
            item: 要匹配的项

        Returns:
            是否匹配
        """
        # 处理逻辑操作符
        if "and" in condition:
            return all(self._evaluate(subcond, item) for subcond in condition["and"])

        if "or" in condition:
            return any(self._evaluate(subcond, item) for subcond in condition["or"])

        if "not" in condition:
            return not self._evaluate(condition["not"], item)

        # 处理简单条件
        field = condition["field"]
        op = condition["op"]
        value = condition["value"]

        # 处理嵌套字段 (例如 "creator.username")
        field_value = item
        for part in field.split('.'):
            if isinstance(field_value, dict) and part in field_value:
                field_value = field_value[part]
            else:
                # 如果字段不存在，视为不匹配
                return False

        # 处理类型转换
        if isinstance(value, str) and isinstance(field_value, (int, float)):
            try:
                value = type(field_value)(value)
            except (ValueError, TypeError):
                return False

        # 应用操作符
        try:
            return OPERATORS[op](field_value, value)
        except Exception as e:
            logger.debug(f"筛选条件评估错误: {op}({field_value}, {value}): {str(e)}")
            return False


class FilterParser:
    """筛选条件解析器，用于解析和转换不同格式的筛选条件"""

    @staticmethod
    def parse_query_string(query: str) -> Dict[str, Any]:
        """解析简单查询字符串为条件字典

        Args:
            query: 查询字符串 (例如 "type:LORA rating:>4.5")

        Returns:
            条件字典
        """
        if not query.strip():
            return {}

        parts = re.findall(r'([a-zA-Z0-9_.]+)(:([<>]?=?|~|!)?([\w.-]+|\".+?\")|\s+|$)', query)
        conditions = []

        for field, _, op_str, value in parts:
            if not field or not value:
                continue

            # 处理引号
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]

            # 映射操作符
            op = "eq"  # 默认等于
            if op_str:
                if op_str == '>':
                    op = "gt"
                elif op_str == '>=':
                    op = "ge"
                elif op_str == '<':
                    op = "lt"
                elif op_str == '<=':
                    op = "le"
                elif op_str == '~':
                    op = "contains"
                elif op_str == '!':
                    op = "ne"

            conditions.append({
                "field": field,
                "op": op,
                "value": value
            })

        # 如果有多个条件，组合为AND
        if len(conditions) > 1:
            return {"and": conditions}
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {}

    @staticmethod
    def parse_json(json_str: str) -> Dict[str, Any]:
        """解析JSON格式的筛选条件

        Args:
            json_str: JSON字符串

        Returns:
            条件字典

        Raises:
            ValueError: JSON格式无效
        """
        try:
            condition = json.loads(json_str)
            # 验证结构
            FilterCondition(condition)
            return condition
        except json.JSONDecodeError as e:
            raise ValueError(f"无效的JSON格式: {str(e)}")

    @staticmethod
    def parse_cli_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """将CLI参数转换为筛选条件

        Args:
            params: CLI参数字典

        Returns:
            条件字典
        """
        conditions = []

        # 映射CLI参数到筛选条件
        mapping = {
            "query": {"field": "name", "op": "contains"},
            "type": {"field": "type", "op": "eq"},
            "creator": {"field": "creator.username", "op": "eq"},
            "tag": {"field": "tags", "op": "in"},
            "base_model": {"field": "modelVersions.baseModel", "op": "eq"},
            "min_rating": {"field": "stats.rating", "op": "ge"},
            "max_rating": {"field": "stats.rating", "op": "le"},
            "min_downloads": {"field": "stats.downloadCount", "op": "ge"},
            "max_downloads": {"field": "stats.downloadCount", "op": "le"},
        }

        for param, value in params.items():
            if param in mapping and value is not None:
                field_map = mapping[param]
                conditions.append({
                    "field": field_map["field"],
                    "op": field_map["op"],
                    "value": value
                })

        # 如果有多个条件，组合为AND
        if len(conditions) > 1:
            return {"and": conditions}
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {}

    @staticmethod
    def to_api_params(condition: Dict[str, Any]) -> Dict[str, Any]:
        """将筛选条件转换为API参数

        Args:
            condition: 筛选条件

        Returns:
            API参数字典
        """
        # 处理为空的情况
        if not condition:
            return {}

        # 如果是简单条件，直接映射
        if "field" in condition and "op" in condition and "value" in condition:
            return FilterParser._map_condition_to_param(condition)

        # 处理复合条件 (AND/OR)
        if "and" in condition:
            params = {}
            for subcond in condition["and"]:
                params.update(FilterParser.to_api_params(subcond))
            return params

        if "or" in condition:
            # CivitAI API不直接支持OR，我们只转换第一个条件
            # 其余条件需要在客户端过滤
            if condition["or"]:
                return FilterParser.to_api_params(condition["or"][0])
            return {}

        if "not" in condition:
            # CivitAI API不直接支持NOT，我们忽略这个条件
            # 需要在客户端过滤
            return {}

        # 未知条件类型
        return {}

    @staticmethod
    def _map_condition_to_param(condition: Dict[str, Any]) -> Dict[str, Any]:
        """将单个条件映射到API参数

        Args:
            condition: 单个筛选条件

        Returns:
            API参数字典
        """
        field = condition["field"]
        op = condition["op"]
        value = condition["value"]

        # 字段映射到API参数
        field_mapping = {
            "name": "query",
            "type": "types",
            "creator.username": "username",
            "tags": "tag",
            "modelVersions.baseModel": "baseModel",
            # 评分和下载量等需要在客户端筛选
        }

        # 操作符映射
        op_mapping = {
            "eq": "",     # 直接使用值
            "in": "",     # 对于tags，直接使用值
            "contains": "",  # 对于name，就是query参数
        }

        # 如果字段可以映射到API参数
        if field in field_mapping:
            param_name = field_mapping[field]

            # 如果操作符支持直接映射
            if op in op_mapping:
                return {param_name: value}

        # 对于不能直接映射的条件，返回空字典
        # 这些条件需要在客户端筛选
        return {}


class FilterManager:
    """筛选管理器，用于存储和加载筛选模板"""

    def __init__(self, templates_file: str = None):
        """初始化筛选管理器

        Args:
            templates_file: 模板文件路径
        """
        self.templates_file = templates_file or self._get_default_templates_path()
        self.templates = self._load_templates()
        self.history = []

        # 如果没有模板，添加默认模板
        if not self.templates:
            self._add_default_templates()

    def _get_default_templates_path(self) -> str:
        """获取默认的模板文件路径

        Returns:
            默认模板文件路径
        """
        # 使用用户主目录下的配置目录
        config_dir = os.path.join(os.path.expanduser("~"), ".civitai-downloader")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "filter_templates.json")

    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载筛选模板

        Returns:
            模板字典 {名称: 条件}
        """
        try:
            if not os.path.exists(self.templates_file):
                return {}

            with open(self.templates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载筛选模板失败: {str(e)}")
            return {}

    def _save_templates(self) -> bool:
        """保存筛选模板

        Returns:
            是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.templates_file), exist_ok=True)

            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存筛选模板失败: {str(e)}")
            return False

    def _add_default_templates(self) -> None:
        """添加默认的筛选模板"""
        for name, template in DEFAULT_TEMPLATES.items():
            self.add_template(name, template)

    def add_template(self, name: str, condition: Dict[str, Any]) -> bool:
        """添加筛选模板

        Args:
            name: 模板名称
            condition: 筛选条件

        Returns:
            是否成功
        """
        try:
            # 验证条件格式
            FilterCondition(condition)

            # 保存模板
            self.templates[name] = condition
            return self._save_templates()
        except Exception as e:
            logger.error(f"添加筛选模板失败: {str(e)}")
            return False

    def remove_template(self, name: str) -> bool:
        """删除筛选模板

        Args:
            name: 模板名称

        Returns:
            是否成功
        """
        if name not in self.templates:
            return False

        del self.templates[name]
        return self._save_templates()

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """获取筛选模板

        Args:
            name: 模板名称

        Returns:
            筛选条件，如果不存在则返回None
        """
        return self.templates.get(name)

    def list_templates(self) -> Dict[str, Dict[str, Any]]:
        """列出所有筛选模板

        Returns:
            模板字典
        """
        return self.templates.copy()

    def add_to_history(self, condition: Dict[str, Any]) -> None:
        """添加筛选条件到历史记录

        Args:
            condition: 筛选条件
        """
        # 添加到历史记录开头
        self.history.insert(0, {
            "condition": condition,
            "timestamp": datetime.now().isoformat()
        })

        # 限制历史记录长度
        if len(self.history) > 20:
            self.history = self.history[:20]

    def get_history(self) -> List[Dict[str, Any]]:
        """获取筛选历史记录

        Returns:
            历史记录列表
        """
        return self.history.copy()

    def clear_history(self) -> None:
        """清空历史记录"""
        self.history = []


def apply_filter(items: List[Dict[str, Any]], condition: Dict[str, Any]) -> List[Dict[str, Any]]:
    """应用筛选条件到项目列表

    Args:
        items: 项目列表
        condition: 筛选条件

    Returns:
        筛选后的项目列表
    """
    if not condition:
        return items

    try:
        filter_condition = FilterCondition(condition)
        return [item for item in items if filter_condition.match(item)]
    except Exception as e:
        logger.error(f"应用筛选条件失败: {str(e)}")
        return items


def sort_results(items: List[Dict[str, Any]], sort_by: str, ascending: bool = False) -> List[Dict[str, Any]]:
    """对结果进行排序

    Args:
        items: 项目列表
        sort_by: 排序字段
        ascending: 是否升序排序

    Returns:
        排序后的项目列表
    """
    if not sort_by:
        return items

    def get_value(item, field):
        """安全获取嵌套字段的值"""
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
        logger.error(f"排序失败: {str(e)}")
        return items


# 样例筛选模板
DEFAULT_TEMPLATES = {
    "高质量LORA": {
        "and": [
            {"field": "type", "op": "eq", "value": "LORA"},
            {"field": "stats.rating", "op": "ge", "value": 4.5},
            {"field": "stats.downloadCount", "op": "ge", "value": 1000}
        ]
    },
    "新人气Checkpoint": {
        "and": [
            {"field": "type", "op": "eq", "value": "Checkpoint"},
            {"field": "stats.downloadCount", "op": "ge", "value": 500},
            {"field": "publishedAt", "op": "ge", "value": (datetime.now() - timedelta(days=30)).isoformat()}
        ]
    }
}

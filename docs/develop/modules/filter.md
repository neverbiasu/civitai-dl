# Filter 模块设计与实现

## 作用

负责将用户的筛选条件（无论是CLI参数、WebUI表单还是JSON/交互式构建）统一转换为Civitai API支持的参数，并支持本地复杂筛选（如AND/OR/NOT逻辑、客户端二次过滤）。

## 支持的API参数

| 字段名    | 说明         | 支持方式     |
| --------- | ------------ | ------------ |
| query     | 搜索关键词   | 支持         |
| types     | 模型类型列表 | 支持（数组） |
| tag       | 标签         | 支持         |
| sort      | 排序方式     | 支持         |
| limit     | 结果数量     | 支持         |
| nsfw      | NSFW内容     | 支持         |
| username  | 创作者用户名 | 支持         |
| baseModel | 基础模型     | 支持         |

## 参数映射实现

FilterParser._map_condition_to_param 负责将筛选条件字段映射为API参数，严格遵循官方API文档，不做多余映射。

## 用法

- CLI和WebUI均通过 FilterBuilder.build_params(condition) 自动获得API参数，无需手动拼接。
- 支持复杂条件（如AND/OR/NOT），API不支持的部分自动降级为本地过滤。

## 扩展点

- 可扩展更多API参数，只需在 field_mapping 中添加映射。
- 支持筛选模板、历史记录、交互式构建等高级用法。

## 示例

```python
# 构建筛选条件
condition = {
    "and": [
        {"field": "query", "op": "eq", "value": "realistic"},
        {"field": "types", "op": "eq", "value": ["Checkpoint"]},
        {"field": "limit", "op": "eq", "value": 5}
    ]
}
params = FilterBuilder().build_params(condition)
# params: {'query': 'realistic', 'types': ['Checkpoint'], 'limit': 5}
```

## 相关

- 该模块被CLI和WebUI直接调用，保证参数一致性和扩展性。

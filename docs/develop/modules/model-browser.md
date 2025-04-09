# 模型浏览器模块

## 模块概述

模型浏览器模块负责处理与Civitai模型搜索、浏览和筛选相关的业务逻辑，为CLI和WebUI提供统一的模型发现能力。该模块基于API客户端提供的数据，实现高级搜索、结果处理和本地缓存功能。

### 主要职责

- 处理模型搜索请求
- 实现高级筛选逻辑
- 格式化和整理API结果
- 提供模型元数据提取
- 支持搜索历史记录
- 管理本地搜索缓存

### 技术特性

- 组合条件搜索
- 搜索结果缓存
- 本地二次排序
- 分页结果合并
- 数据转换和标准化
- 历史搜索记录

## 接口定义

### 核心类

```python
class ModelBrowser:
    """
    模型浏览器，提供模型搜索和浏览功能
    """
    
    def __init__(self, api_client: CivitaiAPI = None):
        """
        初始化模型浏览器
        
        Args:
            api_client: Civitai API客户端实例，如为None则创建新实例
        """
        pass
    
    def search_models(self, query: Optional[str] = None, 
                     types: Optional[List[str]] = None,
                     tag: Optional[str] = None,
                     username: Optional[str] = None,
                     nsfw: Optional[bool] = None,
                     sort: Optional[str] = None,
                     period: Optional[str] = None,
                     limit: int = 20,
                     use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        搜索模型
        
        Args:
            query: 搜索关键词
            types: 模型类型列表
            tag: 按标签筛选
            username: 按创作者筛选
            nsfw: 是否包含NSFW内容
            sort: 排序方式
            period: 时间范围
            limit: 结果数量限制
            use_cache: 是否使用缓存结果
            
        Returns:
            标准化的模型信息列表
        """
        pass
    
    def get_model_details(self, model_id: int, 
                         use_cache: bool = True) -> Dict[str, Any]:
        """
        获取模型详细信息
        
        Args:
            model_id: 模型ID
            use_cache: 是否使用缓存结果
            
        Returns:
            标准化的模型详细信息
            
        Raises:
            ModelNotFoundError: 模型不存在
        """
        pass
    
    def get_popular_models(self, model_type: Optional[str] = None, 
                          limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取热门模型
        
        Args:
            model_type: 模型类型
            limit: 结果数量限制
            
        Returns:
            热门模型列表
        """
        pass
    
    def get_creator_models(self, username: str, 
                          limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取特定创作者的模型
        
        Args:
            username: 创作者用户名
            limit: 结果数量限制
            
        Returns:
            创作者的模型列表
            
        Raises:
            ResourceNotFoundError: 创作者不存在
        """
        pass
    
    def get_model_versions(self, model_id: int) -> List[Dict[str, Any]]:
        """
        获取模型的所有版本
        
        Args:
            model_id: 模型ID
            
        Returns:
            版本信息列表
            
        Raises:
            ModelNotFoundError: 模型不存在
        """
        pass
    
    def get_similar_models(self, model_id: int, 
                         limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取相似模型推荐
        
        Args:
            model_id: 模型ID
            limit: 结果数量限制
            
        Returns:
            相似模型列表
        """
        pass
    
    def get_tags(self, query: Optional[str] = None, 
                limit: int = 20) -> List[Dict[str, str]]:
        """
        获取标签列表
        
        Args:
            query: 搜索关键词
            limit: 结果数量限制
            
        Returns:
            标签信息列表
        """
        pass
    
    def get_creators(self, query: Optional[str] = None, 
                    limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取创作者列表
        
        Args:
            query: 搜索关键词
            limit: 结果数量限制
            
        Returns:
            创作者信息列表
        """
        pass
    
    def save_search_history(self, query: str, 
                          results_count: int) -> None:
        """
        保存搜索历史记录
        
        Args:
            query: 搜索关键词
            results_count: 结果数量
        """
        pass
    
    def get_search_history(self, 
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取搜索历史
        
        Args:
            limit: 结果数量限制
            
        Returns:
            搜索历史记录列表
        """
        pass
    
    def clear_cache(self) -> None:
        """
        清除搜索缓存
        """
        pass
```

### 辅助类

```python
class SearchFilter:
    """构建和组合搜索过滤条件"""
    
    def __init__(self):
        """初始化空过滤器"""
        pass
    
    def add_text_filter(self, field: str, value: str) -> 'SearchFilter':
        """添加文本过滤条件"""
        pass
    
    def add_type_filter(self, types: List[str]) -> 'SearchFilter':
        """添加类型过滤条件"""
        pass
    
    def add_sort(self, sort_by: str, direction: str = "desc") -> 'SearchFilter':
        """添加排序条件"""
        pass
    
    def build(self) -> Dict[str, Any]:
        """构建API请求参数"""
        pass


class ModelStandardizer:
    """标准化模型数据结构"""
    
    @staticmethod
    def standardize_model(model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将API返回的模型数据转换为标准格式
        
        Args:
            model_data: API返回的原始模型数据
            
        Returns:
            标准化后的模型数据
        """
        pass
    
    @staticmethod
    def extract_main_image(model_data: Dict[str, Any]) -> Optional[str]:
        """
        提取模型主图
        
        Args:
            model_data: 模型数据
            
        Returns:
            主图URL或None
        """
        pass
```

## 实现思路

### 搜索策略设计

1. **参数转换**:
   - 将用户搜索参数转换为API接受的格式
   - 处理复合条件和特殊语法
   - 管理默认参数和限制

2. **缓存策略**:
   - 使用LRU缓存存储最近搜索结果
   - 针对热门查询实现持久化缓存
   - 定期过期缓存数据确保新鲜度

3. **多页面结果合并**:
   - 当请求结果超过单页限制时自动获取多页
   - 合并页面结果并移除重复项
   - 按请求的排序方式重新排列结果

### 数据标准化流程

将API返回的数据转换为内部统一结构：

1. **数据提取**:
   - 从API响应中提取关键字段
   - 处理可选字段和嵌套数据
   - 标准化字段名称和格式

2. **元数据增强**:
   - 增加内部使用的计算字段
   - 提取主图和缩略图URL
   - 生成人类友好的文本描述

3. **格式转换**:
   - 转换日期格式为统一标准
   - 处理多语言内容
   - 确保数值字段类型一致

### 搜索结果处理

1. **二次排序**:
   - 支持基于本地计算字段的排序
   - 实现多级排序逻辑
   - 提供排序方向控制

2. **结果过滤**:
   - 应用本地附加过滤条件
   - 实现更复杂的过滤逻辑
   - 支持正则表达式过滤

3. **结果分组**:
   - 按类别、创建者等维度分组
   - 计算分组统计信息
   - 支持分组展开和折叠

## 依赖关系

- **外部依赖**:
  - 无直接外部依赖

- **内部依赖**:
  - `CivitaiAPI`: 用于发送API请求获取数据

## 注意事项与限制

1. **API限制**:
   - 搜索功能受Civitai API性能和限制影响
   - 复杂查询可能导致响应时间增加

2. **缓存一致性**:
   - 缓存数据可能不反映最新的模型更新
   - 提供刷新机制以获取最新数据

3. **结果数量上限**:
   - API限制单次查询最多返回100条结果
   - 获取更多结果需要分页，可能影响性能

4. **搜索准确度**:
   - 搜索结果取决于API的搜索算法
   - 某些复杂查询可能无法通过API直接满足

5. **离线功能限制**:
   - 离线模式下只能访问已缓存的搜索结果
   - 首次使用需要网络连接

# API客户端模块

## 模块概述

API客户端模块是Civitai Downloader与Civitai平台通信的核心组件，负责封装所有API调用逻辑，处理认证、请求限制和错误恢复，为其他模块提供标准化的数据访问接口。

### 主要职责

- 封装Civitai REST API调用
- 管理API认证和密钥
- 实现请求频率控制
- 处理API错误和重试机制
- 解析和验证API响应

### 技术特性

- 请求频率自适应控制
- 指数退避重试策略
- 透明的错误处理
- 支持API密钥认证
- 请求缓存(可选)

## 接口定义

### 核心类

```python
class CivitaiAPI:
    """Civitai API客户端，提供对Civitai API的访问"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://civitai.com/api/v1/"):
        """
        初始化API客户端
        
        Args:
            api_key: Civitai API密钥，用于认证
            base_url: API基础URL，默认为官方API地址
        """
        pass
    
    def get_models(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        获取模型列表
        
        Args:
            params: 查询参数，支持以下选项:
                - limit: 每页结果数量 (默认: 20, 最大: 100)
                - page: 页码 (默认: 1)
                - query: 搜索关键词
                - tag: 按标签筛选
                - types: 模型类型列表
                - sort: 排序方式
                
        Returns:
            包含模型列表及元数据的字典
            
        Raises:
            APIError: API调用失败
            RateLimitError: 请求频率超限
            AuthenticationError: 认证失败
        """
        pass
    
    def get_model(self, model_id: int) -> Dict[str, Any]:
        """
        获取单个模型详情
        
        Args:
            model_id: 模型ID
            
        Returns:
            模型详情字典
            
        Raises:
            APIError: API调用失败
            ResourceNotFoundError: 模型不存在
        """
        pass
    
    def get_model_version(self, version_id: int) -> Dict[str, Any]:
        """
        获取模型版本详情
        
        Args:
            version_id: 版本ID
            
        Returns:
            版本详情字典
            
        Raises:
            APIError: API调用失败
            ResourceNotFoundError: 版本不存在
        """
        pass
    
    def get_model_versions_by_hash(self, hash_value: str) -> Dict[str, Any]:
        """
        通过哈希值查找模型版本
        
        Args:
            hash_value: 模型文件哈希值
            
        Returns:
            版本详情字典
            
        Raises:
            APIError: API调用失败
            ResourceNotFoundError: 没有匹配的版本
        """
        pass
    
    def get_images(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        获取图像列表
        
        Args:
            params: 查询参数，支持以下选项:
                - limit: 每页结果数量
                - modelId: 按模型ID筛选
                - modelVersionId: 按模型版本ID筛选
                - nsfw: NSFW筛选级别
                
        Returns:
            包含图像列表及元数据的字典
            
        Raises:
            APIError: API调用失败
        """
        pass
    
    def get_all_images(self, base_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        获取所有匹配的图像，自动处理分页
        
        Args:
            base_params: 基础查询参数
            
        Returns:
            图像对象列表
            
        Raises:
            APIError: API调用失败
        """
        pass
    
    def get_creators(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        获取创作者列表
        
        Args:
            params: 查询参数
            
        Returns:
            包含创作者列表及元数据的字典
            
        Raises:
            APIError: API调用失败
        """
        pass
    
    def get_tags(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        获取标签列表
        
        Args:
            params: 查询参数
            
        Returns:
            包含标签列表及元数据的字典
            
        Raises:
            APIError: API调用失败
        """
        pass
    
    def get_download_url(self, version_id: int, use_token: bool = True) -> str:
        """
        获取模型下载URL
        
        Args:
            version_id: 版本ID
            use_token: 是否在URL中包含API密钥
            
        Returns:
            下载URL字符串
            
        Raises:
            ValueError: 如果需要API密钥但未提供
        """
        pass
```

### 异常类

```python
class APIError(Exception):
    """API调用失败的基类异常"""
    pass

class ResourceNotFoundError(APIError):
    """请求的资源不存在"""
    pass

class RateLimitError(APIError):
    """API请求频率超限"""
    pass

class AuthenticationError(APIError):
    """API认证失败"""
    pass
```

### 数据模型

```python
@dataclass
class ModelInfo:
    """模型基本信息"""
    id: int
    name: str
    type: str
    nsfw: bool
    creator: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
@dataclass
class ImageInfo:
    """图像信息"""
    id: int
    url: str
    width: int
    height: int
    nsfw: bool
    hash: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)
```

## 使用示例

### 基本API调用

```python
from civitai.api import CivitaiAPI

# 创建API客户端
api = CivitaiAPI(api_key="your_api_key_here")

# 搜索LORA模型
results = api.get_models(params={
    "types": ["LORA"],
    "query": "portrait",
    "limit": 10
})

# 显示结果
print(f"找到 {results['metadata']['totalItems']} 个模型")
for model in results["items"]:
    print(f"ID: {model['id']}, 名称: {model['name']}")

# 获取特定模型详情
model = api.get_model(12345)
print(f"模型名称: {model['name']}")
print(f"创作者: {model['creator']['username']}")
print(f"下载次数: {model['stats']['downloadCount']}")

# 获取模型相关图像
images = api.get_images({"modelId": 12345, "limit": 5})
for image in images["items"]:
    print(f"图像URL: {image['url']}")
```

### 处理分页获取所有结果

```python
# 获取特定模型的所有图像（自动处理分页）
all_images = api.get_all_images({"modelId": 12345, "nsfw": ["None", "Soft"]})
print(f"共获取到 {len(all_images)} 张图像")
```

### 错误处理

```python
from civitai.api import CivitaiAPI, ResourceNotFoundError, RateLimitError

api = CivitaiAPI()

try:
    # 尝试获取可能不存在的模型
    model = api.get_model(9999999)
    print(f"模型名称: {model['name']}")
except ResourceNotFoundError:
    print("模型不存在")
except RateLimitError:
    print("API请求频率超限，请稍后再试")
except Exception as e:
    print(f"发生错误: {str(e)}")
```

## 实现细节

### 请求频率控制

API客户端实现了自适应的请求频率控制，根据服务器响应动态调整请求间隔：

```python
def _rate_limited_request(self, method, url, **kwargs):
    """实现请求频率控制的请求方法"""
    with self.request_lock:
        # 计算需要等待的时间
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_request_interval:
            wait_time = self.min_request_interval - elapsed
            time.sleep(wait_time)
        
        # 执行请求并记录时间
        response = requests.request(method, url, **kwargs)
        self.last_request_time = time.time()
        
        # 根据响应状态码调整请求间隔
        if response.status_code == 429:  # 请求过于频繁
            self.min_request_interval *= 2  # 指数退避
            time.sleep(5)  # 额外等待
            return self._rate_limited_request(method, url, **kwargs)  # 重试
            
        return response
```

### 游标分页处理

处理图像API的游标分页特性：

```python
def get_all_images(self, base_params=None):
    """获取所有匹配的图像，自动处理游标分页"""
    if base_params is None:
        base_params = {}
        
    results = []
    params = base_params.copy()
    
    while True:
        response = self.get_images(params)
        
        if "items" in response:
            results.extend(response["items"])
            
        # 获取下一页游标
        if "metadata" in response and "nextCursor" in response["metadata"]:
            params["cursor"] = response["metadata"]["nextCursor"]
        else:
            break  # 没有更多页面，结束循环
    
    return results
```

### 错误映射

将HTTP错误转换为特定的异常类型：

```python
def _process_response(self, response):
    """处理API响应，转换HTTP错误为应用异常"""
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            raise ResourceNotFoundError(f"请求的资源不存在: {response.url}")
        elif response.status_code == 401:
            raise AuthenticationError("API认证失败，请检查API密钥")
        elif response.status_code == 429:
            raise RateLimitError("API请求频率超限，请稍后再试")
        else:
            raise APIError(f"API调用失败: {str(e)}")
    except requests.exceptions.RequestException as e:
        raise APIError(f"请求异常: {str(e)}")
    except ValueError as e:
        raise APIError(f"无效的响应格式: {str(e)}")
```

## 配置选项

| 配置项                 | 类型   | 默认值                        | 说明                 |
| ---------------------- | ------ | ----------------------------- | -------------------- |
| `api.key`              | 字符串 | `None`                        | Civitai API密钥      |
| `api.base_url`         | 字符串 | `https://civitai.com/api/v1/` | API基础URL           |
| `api.request_interval` | 浮点数 | `0.5`                         | 请求最小间隔(秒)     |
| `api.max_retries`      | 整数   | `3`                           | 请求失败最大重试次数 |
| `api.timeout`          | 整数   | `30`                          | 请求超时时间(秒)     |
| `api.cache_ttl`        | 整数   | `300`                         | 缓存生存时间(秒)     |

## 依赖关系

- **外部依赖**:
  - `requests`: HTTP请求库
  - `requests_cache`(可选): 用于缓存请求结果

- **内部依赖**:
  - `config`: 配置管理模块，用于获取API密钥

## 注意事项与限制

1. **API速率限制**:
   - Civitai API对未认证请求限制为每分钟10次
   - 使用API密钥可提高限制，但仍需控制请求频率

2. **认证要求**:
   - 某些模型需要API密钥才能下载
   - API密钥应安全存储，不应硬编码在源代码中

3. **API变更风险**:
   - Civitai API仍在开发中，可能发生变更
   - 响应结构可能随时间变化，需保持更新

4. **图像API特性**:
   - 2023年7月2日后，图像API改用游标分页而非传统页码分页
   - 必须使用cursor参数而非page获取后续页面

5. **API响应大小**:
   - 某些API响应可能很大，特别是模型详情
   - 处理大型响应时应考虑内存使用

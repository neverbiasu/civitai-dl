# WebUI 接口模块

## 模块概述

WebUI接口模块基于Gradio框架，为Civitai Downloader提供图形化用户界面，使非技术用户能够轻松访问所有功能。该模块通过直观的界面元素展示功能，并与核心业务逻辑层交互，提供友好的用户体验。

### 主要职责

- 提供图形化用户界面
- 展示模型和图像浏览结果
- 管理和展示下载队列
- 提供直观的设置界面
- 展示下载进度和状态
- 支持交互式筛选和搜索

### 技术特性

- 基于Gradio的响应式界面
- 标签页式功能组织
- 实时进度更新
- 与CLI共享业务逻辑
- 浏览器内本地运行
- 丰富的数据可视化组件

## 接口定义

### 核心类

```python
class WebUI:
    """
    Civitai Downloader的Web图形界面
    """
    
    def __init__(self, model_browser: ModelBrowser = None, 
                model_downloader: ModelDownloader = None,
                image_downloader: ImageDownloader = None):
        """
        初始化WebUI
        
        Args:
            model_browser: 模型浏览器实例
            model_downloader: 模型下载器实例
            image_downloader: 图像下载器实例
        """
        pass
    
    def launch(self, server_name: str = "127.0.0.1", 
              server_port: int = 7860, 
              share: bool = False) -> None:
        """
        启动WebUI服务
        
        Args:
            server_name: 服务器主机名
            server_port: 服务器端口
            share: 是否创建公共链接
        """
        pass
    
    def shutdown(self) -> None:
        """关闭WebUI服务"""
        pass
```

### 页面组件

```python
class BrowsePage:
    """
    模型浏览页面组件，提供模型搜索和浏览功能
    """
    
    def __init__(self, model_browser: ModelBrowser):
        """初始化浏览页面"""
        pass
    
    def build(self) -> None:
        """构建UI组件"""
        pass
    
    def handle_search(self, query: str, model_type: str, 
                    sort: str, nsfw: bool) -> Dict[str, Any]:
        """
        处理搜索请求
        
        Args:
            query: 搜索关键词
            model_type: 模型类型
            sort: 排序方式
            nsfw: 是否包括NSFW内容
            
        Returns:
            搜索结果，适用于Gradio组件展示
        """
        pass


class DownloadsPage:
    """
    下载管理页面组件，提供下载队列管理
    """
    
    def __init__(self, model_downloader: ModelDownloader, 
                image_downloader: ImageDownloader):
        """初始化下载页面"""
        pass
    
    def build(self) -> None:
        """构建UI组件"""
        pass
    
    def handle_download_model(self, model_id: int, 
                            version_id: Optional[int], 
                            output_path: str) -> str:
        """
        处理模型下载请求
        
        Args:
            model_id: 模型ID
            version_id: 版本ID (可选)
            output_path: 输出路径
            
        Returns:
            操作结果消息
        """
        pass
    
    def update_queue_display(self) -> List[Dict[str, Any]]:
        """
        更新队列显示
        
        Returns:
            当前队列中的任务信息列表
        """
        pass


class ImagesPage:
    """
    图像管理页面组件，提供图像浏览和下载功能
    """
    
    def __init__(self, image_downloader: ImageDownloader):
        """初始化图像页面"""
        pass
    
    def build(self) -> None:
        """构建UI组件"""
        pass
    
    def handle_image_search(self, model_id: int, 
                          nsfw_levels: List[str]) -> List[Dict[str, Any]]:
        """
        处理图像搜索
        
        Args:
            model_id: 模型ID
            nsfw_levels: NSFW级别列表
            
        Returns:
            搜索到的图像列表
        """
        pass


class SettingsPage:
    """
    设置页面组件，提供应用配置界面
    """
    
    def __init__(self):
        """初始化设置页面"""
        pass
    
    def build(self) -> None:
        """构建UI组件"""
        pass
    
    def handle_api_key_update(self, api_key: str) -> str:
        """
        更新API密钥
        
        Args:
            api_key: Civitai API密钥
            
        Returns:
            操作结果消息
        """
        pass
    
    def handle_download_settings_update(self, max_workers: int, 
                                      chunk_size: int) -> str:
        """
        更新下载设置
        
        Args:
            max_workers: 最大并行下载数
            chunk_size: 分块大小
            
        Returns:
            操作结果消息
        """
        pass
```

## 实现思路

### 页面结构设计

WebUI采用标签页式结构，将功能分为四个主要页面：

1. **浏览页面**:
   - 搜索表单区域：关键词、模型类型、排序方式等筛选选项
   - 结果展示区域：网格或列表视图，显示模型缩略图和基本信息
   - 详情查看区：点击模型后显示详细信息和版本选项

2. **下载页面**:
   - 当前下载任务：显示正在进行的下载，带进度条和控制按钮
   - 下载队列：显示待处理任务，可调整优先级
   - 历史记录：显示已完成的下载

3. **图像页面**:
   - 模型ID输入区：指定要获取图像的模型
   - NSFW过滤选项：选择可接受的内容级别
   - 图像网格：显示搜索到的图像缩略图
   - 图像详情：点击图像后显示大图和生成参数

4. **设置页面**:
   - API设置：API密钥输入和验证
   - 下载设置：工作线程数、分块大小等
   - 路径设置：默认下载位置
   - 界面设置：主题选择等

### 实时更新机制

使用Gradio的更新机制实现实时进度显示和状态更新：

1. **进度更新**:
   - 使用定时器函数每秒查询下载状态
   - 在UI中动态更新进度条和状态信息

2. **状态通知**:
   - 使用Gradio的通知组件显示重要事件
   - 下载完成或失败时显示提醒

3. **队列刷新**:
   - 定期自动刷新任务队列显示
   - 允许用户手动刷新

### 数据展示与交互

1. **模型结果展示**:
   - 使用DataTable或自定义Grid组件展示搜索结果
   - 支持按列排序和多选操作
   - 点击行显示详细信息面板

2. **下载进度可视化**:
   - 使用进度条显示整体下载进度
   - 显示当前下载速度和剩余时间
   - 使用饼图显示队列状态分布

3. **图像浏览**:
   - 使用图像网格组件展示搜索结果
   - 支持缩略图和原图切换
   - 显示图像关联的生成参数

## 依赖关系

- **外部依赖**:
  - `gradio`: 用于构建WebUI界面
  - `pillow`: 图像处理
  - `pandas`: 数据处理和表格展示

- **内部依赖**:
  - `ModelBrowser`: 提供模型搜索功能
  - `ModelDownloader`: 提供模型下载功能
  - `ImageDownloader`: 提供图像下载功能

## 注意事项与限制

1. **浏览器兼容性**:
   - 推荐使用现代浏览器(Chrome, Firefox, Edge最新版)
   - 旧版浏览器可能存在兼容性问题

2. **资源消耗**:
   - 大量图片显示可能导致浏览器内存占用较高
   - 在展示大型搜索结果时考虑分页或虚拟滚动技术

3. **网络相关**:
   - WebUI依赖网络连接获取API数据
   - 断网状态下仅能访问已缓存的数据

4. **多用户支持**:
   - WebUI默认为单用户设计
   - 使用`share=True`可创建临时公共URL，但多用户同时操作可能导致冲突

5. **界面适应性**:
   - 自适应布局支持桌面和平板设备
   - 小屏幕手机设备可能需要额外优化

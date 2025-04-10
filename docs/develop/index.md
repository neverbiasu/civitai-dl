# Civitai Downloader 开发指南

## 项目架构

Civitai Downloader 采用模块化架构，分为核心下载引擎、API客户端、CLI界面和WebUI界面。

```
civitai-downloader/
├── core/          # 核心功能模块
│   ├── api/       # Civitai API 客户端
│   └── downloader/# 下载引擎
├── cli/           # 命令行界面
├── webui/         # Web用户界面
└── utils/         # 通用工具函数
```

## 技术栈

### 后端
- Python 3.8+
- 网络请求: `requests`
- CLI框架: `click`
- API框架: `FastAPI`
- 并发处理: `asyncio`

### 前端
- WebUI框架: `Gradio` (初期), `Vue.js` (后期)
- CSS框架: `Tailwind CSS`
- 打包工具: `vite`

## 开发环境设置

### 环境准备

1. 安装Python 3.8+
2. 克隆代码库:
   ```bash
   git clone https://github.com/username/civitai-downloader.git
   cd civitai-downloader
   ```
3. 创建虚拟环境:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```
4. 安装依赖:
   ```bash
   pip install -r requirements.txt
   pip install -e .  # 开发模式安装
   ```

### 开发工具推荐
- 代码编辑器: VS Code with Python插件
- API测试: Postman 或 curl

## Civitai API 集成

### API 基础

Civitai API 基础URL: `https://civitai.com/api/v1/`

主要端点:
- `models` - 获取模型列表和详情
- `images` - 获取图像信息
- `tags` - 获取标签信息
- `creators` - 获取创作者信息

### API 客户端实现

API客户端应实现以下功能:
- 处理身份验证 (API密钥)
- 请求速率限制
- 错误处理和重试机制
- 响应数据解析

样例代码:
```python
class CivitaiAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://civitai.com/api/v1/"
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def get_model(self, model_id):
        """获取指定ID的模型信息"""
        response = self.session.get(f"{self.base_url}models/{model_id}")
        response.raise_for_status()
        return response.json()
        
    # 其他API方法...
```

## 下载引擎设计

下载引擎负责:
- 管理下载队列
- 处理并行下载
- 支持断点续传
- 验证文件完整性

实现考虑:
- 使用`aiohttp`或`asyncio`实现异步下载
- 采用分块下载策略
- 实现进度跟踪和状态报告

## CLI 开发指南

使用`click`库构建CLI:
- 每个主要功能对应一个命令组
- 提供详细的帮助文档
- 支持配置文件

示例:
```python
@click.group()
def cli():
    """Civitai Downloader CLI工具"""
    pass

@cli.command()
@click.argument("model_id", type=int)
@click.option("--output", "-o", help="输出目录")
def download(model_id, output):
    """下载指定ID的模型"""
    # 实现下载逻辑...
```

## WebUI 开发指南

使用`Gradio`快速实现初期WebUI:
- 围绕核心功能构建简单界面
- 与CLI共享后端逻辑

后期使用Vue.js重构:
- 使用组件化架构
- 实现响应式设计
- 提供自定义主题支持

## 代码规范

### Python代码规范
- 遵循PEP 8风格指南
- 使用类型注解
- 编写文档字符串(docstrings)
- 使用pylint或flake8进行代码检查

### JavaScript代码规范
- 使用ESLint
- 采用Prettier格式化
- 遵循Vue风格指南(后期)

## 测试策略

### 单元测试
- 使用pytest框架
- 为核心模块编写测试用例
- 使用mock模拟API响应

### 集成测试
- 测试组件间协作
- 验证完整功能流程

### 自动化测试
- 设置GitHub Actions CI流程
- 自动运行测试和代码检查

## 日志与调试

- 使用Python的`logging`模块
- 配置不同级别的日志
- 实现日志轮转

示例:
```python
import logging

logger = logging.getLogger(__name__)

def setup_logging(level=logging.INFO):
    """设置日志系统"""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("civitai-downloader.log")
        ]
    )
```

## 错误处理

- 定义自定义异常类
- 实现全局异常处理
- 提供用户友好的错误消息

## 贡献指南

1. Fork项目仓库
2. 创建功能分支
3. 提交更改
4. 运行测试
5. 提交Pull Request

## 版本发布流程

1. 更新版本号(`__version__.py`)
2. 更新CHANGELOG.md
3. 创建Release标签
4. 构建发布包:
   ```bash
   python setup.py sdist bdist_wheel
   ```
5. 发布到PyPI:
   ```bash
   twine upload dist/*
   ```

## 资源与参考

- [Civitai API文档](https://civitai.com/api/docs)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Gradio文档](https://gradio.app/docs/)
- [Click文档](https://click.palletsprojects.com/)

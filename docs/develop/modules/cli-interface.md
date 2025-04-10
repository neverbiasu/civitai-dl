# CLI 接口模块

## 模块概述

CLI接口模块基于Click框架，提供命令行界面，使用户能够通过终端访问Civitai Downloader的全部功能。该模块设计了清晰的命令结构、参数系统和帮助文档，支持脚本化和自动化操作。

### 主要职责

- 提供命令行交互界面
- 解析命令行参数和选项
- 执行相应的业务逻辑
- 展示结果和进度信息
- 提供帮助和文档

### 技术特性

- 基于Click框架的命令结构
- 丰富的命令选项
- 自动生成帮助文档
- 交互式提示
- 彩色输出
- 进度显示

## 接口定义

### 核心命令结构

```python
import click
from typing import Optional
import sys

@click.group()
@click.version_option()
@click.option("--verbose", "-v", count=True, help="增加详细程度")
@click.option("--quiet", "-q", is_flag=True, help="静默模式")
def cli():
    """Civitai Downloader - 下载和管理Civitai资源"""
    pass
```

### 主要命令组

```python
@cli.group()
def browse():
    """浏览和搜索Civitai上的模型"""
    pass

@browse.command("models")
@click.option("--query", "-q", help="搜索关键词")
@click.option("--type", "-t", help="模型类型")
@click.option("--sort", "-s", 
             type=click.Choice(["Highest Rated", "Most Downloaded", "Newest"]),
             default="Most Downloaded",
             help="排序方式")
@click.option("--limit", "-l", type=int, default=20, help="结果数量")
@click.option("--nsfw", is_flag=True, help="是否包含NSFW内容")
@click.option("--output", "-o", help="将结果保存为JSON文件")
@click.option("--creator", "-c", help="按创作者筛选")
@click.option("--tag", help="按标签筛选")
def browse_models(query, type, sort, limit, nsfw, output, creator, tag):
    """搜索和浏览模型"""
    pass

@browse.command("tags")
@click.option("--query", "-q", help="搜索关键词")
@click.option("--limit", "-l", type=int, default=20, help="结果数量")
@click.option("--output", "-o", help="将结果保存为JSON文件")
def browse_tags(query, limit, output):
    """浏览可用标签"""
    pass

@browse.command("creators")
@click.option("--query", "-q", help="搜索关键词")
@click.option("--limit", "-l", type=int, default=20, help="结果数量")
@click.option("--output", "-o", help="将结果保存为JSON文件")
def browse_creators(query, limit, output):
    """浏览创作者列表"""
    pass
```

### 下载命令组

```python
@cli.group()
def download():
    """下载模型和图像"""
    pass

@download.command("model")
@click.argument("model_id", type=int)
@click.option("--version", "-v", type=int, help="版本ID")
@click.option("--output", "-o", help="输出路径")
@click.option("--format", "-f", help="首选文件格式")
@click.option("--with-images", is_flag=True, help="同时下载示例图像")
@click.option("--image-limit", type=int, default=5, help="下载的图像数量限制")
def download_model(model_id, version, output, format, with_images, image_limit):
    """下载指定ID的模型"""
    pass

@download.command("models")
@click.option("--ids", "-i", help="逗号分隔的模型ID列表")
@click.option("--from-file", "-f", help="包含模型ID的文件路径")
@click.option("--query", "-q", help="搜索关键词")
@click.option("--type", "-t", help="模型类型")
@click.option("--limit", "-l", type=int, default=10, help="下载数量限制")
@click.option("--output", "-o", help="输出目录")
@click.option("--format", help="首选文件格式")
@click.option("--concurrent", "-c", type=int, default=3, help="并行下载数量")
def download_models(ids, from_file, query, type, limit, output, format, concurrent):
    """批量下载多个模型"""
    pass
```

### 图像命令组

```python
@download.command("images")
@click.option("--model", "-m", type=int, help="模型ID")
@click.option("--version", "-v", type=int, help="版本ID")
@click.option("--creator", "-c", help="创作者用户名")
@click.option("--limit", "-l", type=int, default=20, help="下载数量限制")
@click.option("--nsfw", multiple=True, 
            type=click.Choice(["None", "Soft", "Mature", "X"]), 
            help="NSFW级别过滤")
@click.option("--output", "-o", help="输出目录")
@click.option("--save-metadata", is_flag=True, default=True, 
            help="是否保存元数据")
@click.option("--concurrent", type=int, default=5, help="并行下载数量")
def download_images(model, version, creator, limit, nsfw, output, save_metadata, concurrent):
    """下载模型示例图像"""
    pass

@cli.group()
def image():
    """图像相关操作"""
    pass

@image.command("info")
@click.argument("path")
@click.option("--format", "-f", 
            type=click.Choice(["json", "text"]), 
            default="text", 
            help="输出格式")
def image_info(path, format):
    """提取图像元数据"""
    pass

@image.command("batch")
@click.argument("directory")
@click.option("--recursive", "-r", is_flag=True, help="递归处理子目录")
@click.option("--extract-params", "-e", is_flag=True, 
           help="提取生成参数")
def batch_process_images(directory, recursive, extract_params):
    """批量处理图像"""
    pass
```

## 接口设计原则

### 命令行界面设计原则

1. **简单分层结构**:
   - 使用子命令设计模式提供清晰的命令组织
   - 相关功能集中在同一命令组
   - 命令参数保持一致性

2. **直观的帮助信息**:
   - 每个命令和参数提供清晰说明
   - 使用示例和默认值
   - 错误提示明确指出问题

3. **渐进式界面**:
   - 基本命令简单直观
   - 高级选项通过可选参数提供
   - 支持批处理和自动化

### 输出格式和显示

1. **多种输出格式**:
   - 人类友好的文本格式(默认)
   - 结构化数据格式(JSON, YAML)
   - 表格形式展示(适用于列表数据)

2. **进度显示**:
   - 使用进度条显示下载进度
   - 显示总体完成百分比
   - 预估剩余时间计算

3. **彩色输出**:
   - 成功信息使用绿色
   - 错误信息使用红色
   - 警告信息使用黄色
   - 支持--no-color选项禁用彩色输出

### 错误处理

1. **清晰的错误信息**:
   - 错误消息准确描述问题
   - 包含可能的解决方案
   - 提供详细日志选项

2. **参数验证**:
   - 命令行参数先验证再执行
   - 提供类型转换和范围检查
   - 互斥参数组和依赖参数检查

## 使用示例

### 搜索模型

```bash
# 搜索LORA类型的写实模型
civitai-dl browse models --query "realistic" --type LORA

# 获取特定创作者的模型
civitai-dl browse models --creator "username" --limit 50

# 将搜索结果保存为JSON文件
civitai-dl browse models --query "portrait" --output results.json
```

### 下载模型

```bash
# 下载指定ID的模型
civitai-dl download model 12345 --output "./models"

# 下载特定版本
civitai-dl download model 12345 --version 67890

# 下载模型及其示例图像
civitai-dl download model 12345 --with-images --image-limit 10

# 批量下载多个模型
civitai-dl download models --ids "12345,67890,13579"

# 从搜索结果下载
civitai-dl download models --query "portrait" --type "LORA" --limit 5
```

### 图像操作

```bash
# 下载模型相关图像
civitai-dl download images --model 12345 --output "./images"

# 提取图像元数据
civitai-dl image info "./images/example.png" --format json

# 批量处理图像
civitai-dl image batch "./images" --recursive --extract-params
```

## 依赖关系

- **外部依赖**:
  - `click`: 用于构建命令行界面

- **内部依赖**:
  - `ModelBrowser`: 提供模型搜索功能
  - `ModelDownloader`: 提供模型下载功能
  - `ImageDownloader`: 提供图像下载功能
  - `MetadataExtractor`: 提供元数据提取功能

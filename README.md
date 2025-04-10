# Civitai Downloader

一款专为AI艺术创作者设计的工具，用于高效浏览、下载和管理Civitai平台上的模型资源。

## 功能特点

- 模型搜索和浏览
- 批量下载模型和图像
- 断点续传和下载队列管理
- 图形界面和命令行两种交互方式

## 安装说明

### 使用pip安装

```bash
pip install civitai-downloader
```

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/username/civitai-downloader.git
cd civitai-downloader

# 使用Poetry安装
poetry install
```

## 快速入门

### 命令行使用

```bash
# 下载指定ID的模型
civitai-dl download model 12345

# 搜索模型
civitai-dl browse models --query "portrait" --type "LORA"
```

### 启动Web界面

```bash
civitai-dl webui
```

## 文档

详细文档请访问[项目文档网站](https://github.com/username/civitai-downloader)。

## 贡献

欢迎提交Pull Request或创建Issue。

## 许可证

MIT License

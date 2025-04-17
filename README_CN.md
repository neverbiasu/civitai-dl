# Civitai-DL

[![PyPI - Version](https://img.shields.io/pypi/v/civitai-dl.svg)](https://pypi.org/project/civitai-dl/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/civitai-dl.svg)](https://pypi.org/project/civitai-dl/)
[![GitHub License](https://img.shields.io/github/license/neverbiasu/civitai-dl.svg)](https://github.com/neverbiasu/civitai-dl/blob/main/LICENSE)

一款专为AI艺术创作者设计的工具，用于高效浏览、下载和管理Civitai平台上的模型资源。

中文 | [English](README.md)

## 功能特点

- 模型搜索和浏览
- 批量下载模型和图像
- 断点续传和下载队列管理
- 图形界面和命令行两种交互方式

## 安装说明

### 使用pip安装

```bash
pip install civitai-dl
```

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/neverbiasu/civitai-dl.git
cd civitai-dl

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

详细文档请访问[项目文档网站](https://github.com/neverbiasu/civitai-dl)。

## 更新日志

### v0.1.1 (2023-11-22)

- **功能**: 新增 `browse` 命令组，支持从命令行搜索和浏览模型
- **功能**: 实现高级筛选构建器组件，同时支持WebUI和命令行界面的复杂搜索
- **功能**: 添加筛选模板功能，可保存和重用复杂的搜索条件

### v0.1.0 (2023-11-15)

- 初始版本发布
- 支持通过模型ID下载模型文件
- 支持通过模型ID和版本ID下载特定版本文件
- 支持下载模型关联的示例图片
- 提供基本的命令行界面 (CLI)
- 提供实验性的 Web 用户界面 (WebUI)
- 支持代理设置
- 支持 API 密钥认证

## 贡献

欢迎提交Pull Request或创建Issue。

## 许可证

MIT License

# Civitai Downloader

## 项目概述

开发一个高效的Civitai资源下载与管理工具，提供CLI和WebUI两种交互方式，解决AI创作者获取和组织Civitai资源的痛点。

## 核心目标

- 提供比网站更高效的模型筛选与发现体验
- 实现可靠的批量下载功能，支持断点续传和任务管理
- 智能组织下载的模型和图像资源
- 满足从命令行到图形界面的不同用户需求

## 技术架构

- 前端: Click (CLI), Gradio (WebUI)
- 后端: Python, Requests, ThreadPoolExecutor
- 存储: SQLite (可选), 文件系统
- 部署: PyPI包, 单文件可执行程序

## 开发路线图

1. **v0.1-0.3**: 核心API集成与基础下载功能
2. **v0.4-0.6**: 批量下载与图像管理
3. **v0.7-0.9**: WebUI界面与高级筛选
4. **v1.0**: 完整功能集与正式发布

## 关联文档

- [功能设计](functionalities.md) - 详细功能矩阵
- [模块设计](modules.md) - 系统架构与组件
- [API参考](civitai-api.md) - Civitai API使用指南

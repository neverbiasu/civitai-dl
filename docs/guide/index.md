# Civitai Downloader 使用指南

欢迎使用Civitai Downloader！本指南将帮助您快速了解并使用所有功能。

## 目录

- [下载命令使用指南](./download-commands.md) - 学习如何下载模型和图像
- [浏览和搜索命令使用指南](./browse-commands.md) - 学习如何搜索和浏览Civitai资源
- [配置命令使用指南](./config-commands.md) - 学习如何配置应用程序设置
- [下载队列命令使用指南](./queue-commands.md) - 学习如何管理下载任务
- [图像命令使用指南](./image-commands.md) - 学习如何处理和管理图像
- [WebUI命令使用指南](./webui-command.md) - 学习如何使用Web图形界面

## 快速入门

### 安装

```bash
pip install civitai-dl
```

### 基本命令

下载模型：
```bash
civitai-dl download model 12345
```

搜索模型：
```bash
civitai-dl browse models --query "portrait"
```

启动WebUI：
```bash
civitai-dl webui
```

## 配置

首次使用前，建议设置API密钥（可选）：

```bash
civitai-dl config set api_key "your-api-key-here"
```

设置默认下载目录：

```bash
civitai-dl config set output_dir "./my-downloads"
```

## 获取帮助

如需查看任何命令的帮助信息，可以使用`--help`选项：

```bash
civitai-dl --help
civitai-dl download --help
civitai-dl download model --help
```

## 功能概览

- 模型搜索和下载
- 批量下载多个模型
- 模型图像下载和管理
- 下载队列管理
- 断点续传
- 图像元数据提取
- 可自定义的文件保存结构
- Web图形界面
```

# 配置命令使用指南

本文档详细介绍了Civitai Downloader提供的所有配置相关命令及其用法。

## 配置文件

Civitai Downloader使用JSON格式的配置文件存储设置。默认配置文件位于`~/.civitai-dl/config.json`（Windows上通常在`C:\Users\<用户名>\.civitai-dl\config.json`）。

## 查看配置

### 基本用法
```bash
civitai-dl config get [KEY]
```

### 参数
- `KEY`：可选参数，指定要查看的配置项名称。如不提供，将显示所有配置项。

### 示例
```bash
# 查看所有配置
civitai-dl config get

# 查看特定配置项
civitai-dl config get api_key
civitai-dl config get output_dir
```

## 设置配置

### 基本用法
```bash
civitai-dl config set KEY VALUE
```

### 参数
- `KEY`：必填参数，指定要设置的配置项名称
- `VALUE`：必填参数，指定要设置的配置项值

### 示例
```bash
# 设置API密钥
civitai-dl config set api_key "your-api-key-here"

# 设置默认输出目录
civitai-dl config set output_dir "./downloads"

# 设置并行下载数
civitai-dl config set concurrent_downloads 5

# 设置代理服务器
civitai-dl config set proxy "http://127.0.0.1:7890"
```

## 重置配置

### 基本用法
```bash
civitai-dl config reset [KEY] [--all]
```

### 参数和选项
- `KEY`：可选参数，指定要重置的配置项名称
- `--all`：重置所有配置项为默认值

### 示例
```bash
# 重置特定配置项
civitai-dl config reset output_dir

# 重置所有配置
civitai-dl config reset --all
```

## 查看配置文件路径

### 基本用法
```bash
civitai-dl config path
```

### 示例
```bash
# 显示配置文件的路径
civitai-dl config path
```

## 常用配置项

| 配置项                 | 描述                 | 默认值                         |
| ---------------------- | -------------------- | ------------------------------ |
| `api_key`              | Civitai API密钥      | ""                             |
| `output_dir`           | 默认下载目录         | "./downloads"                  |
| `concurrent_downloads` | 并行下载任务数量     | 3                              |
| `chunk_size`           | 下载分块大小(bytes)  | 8192                           |
| `timeout`              | API请求超时时间(秒)  | 30                             |
| `max_retries`          | 下载失败最大重试次数 | 3                              |
| `verify_ssl`           | 是否验证SSL证书      | true                           |
| `proxy`                | 代理服务器设置       | ""                             |
| `path_template`        | 模型文件路径模板     | "{type}/{creator}/{name}"      |
| `image_path_template`  | 图像文件路径模板     | "images/{model_id}/{image_id}" |
```

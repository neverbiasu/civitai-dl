# 下载队列命令使用指南

本文档详细介绍了Civitai Downloader提供的所有下载队列管理相关命令及其用法。

## 查看下载队列

### 基本用法
```bash
civitai-dl queue list
```

### 示例
```bash
# 显示当前下载队列中的所有任务
civitai-dl queue list
```

## 添加任务到队列

### 基本用法
```bash
civitai-dl queue add URL [OPTIONS]
```

### 参数
- `URL`：要下载的文件URL（必填）

### 选项
- `--output`, `-o`：指定下载文件的保存目录
- `--filename`, `-f`：指定保存的文件名
- `--priority`, `-p`：任务优先级（1-10，数字越小优先级越高）

### 示例
```bash
# 添加下载任务到队列
civitai-dl queue add https://example.com/file.zip

# 添加任务并指定输出路径
civitai-dl queue add https://example.com/file.zip --output "./downloads"

# 添加任务并指定文件名
civitai-dl queue add https://example.com/file.zip --filename "my-file.zip"

# 添加高优先级任务
civitai-dl queue add https://example.com/file.zip --priority 1
```

## 移除队列中的任务

### 基本用法
```bash
civitai-dl queue remove TASK_ID
```

### 参数
- `TASK_ID`：要移除的任务ID（必填）

### 示例
```bash
# 移除指定ID的任务
civitai-dl queue remove 12345
```

## 暂停任务

### 基本用法
```bash
civitai-dl queue pause [TASK_ID]
```

### 参数
- `TASK_ID`：要暂停的任务ID（可选，如不提供则暂停所有任务）

### 示例
```bash
# 暂停特定任务
civitai-dl queue pause 12345

# 暂停所有任务
civitai-dl queue pause
```

## 恢复任务

### 基本用法
```bash
civitai-dl queue resume [TASK_ID]
```

### 参数
- `TASK_ID`：要恢复的任务ID（可选，如不提供则恢复所有已暂停的任务）

### 示例
```bash
# 恢复特定任务
civitai-dl queue resume 12345

# 恢复所有已暂停的任务
civitai-dl queue resume
```

## 取消任务

### 基本用法
```bash
civitai-dl queue cancel [TASK_ID]
```

### 参数
- `TASK_ID`：要取消的任务ID（可选，如不提供则取消所有任务）

### 示例
```bash
# 取消特定任务
civitai-dl queue cancel 12345

# 取消所有任务
civitai-dl queue cancel
```

## 清空队列

### 基本用法
```bash
civitai-dl queue clear
```

### 示例
```bash
# 清空整个下载队列
civitai-dl queue clear
```

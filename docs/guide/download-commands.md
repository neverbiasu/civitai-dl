# 下载命令使用指南

本文档详细介绍了Civitai Downloader提供的所有下载相关命令及其用法。

## 下载单个模型

### 基本用法
```bash
civitai-dl download model MODEL_ID [OPTIONS]
```

### 参数
- `MODEL_ID`：要下载的模型ID（必填）

### 选项
- `--version`, `-v`：指定要下载的版本ID（默认下载最新版本）
- `--output`, `-o`：指定下载文件的保存目录（默认为配置中的`output_dir`）
- `--format`, `-f`：首选文件格式，如`safetensors`（如有多种格式可选时）
- `--with-images`：同时下载模型的示例图像
- `--image-limit`：下载的示例图像数量限制（默认5，0表示无限制）

### 示例
```bash
# 下载ID为12345的模型（最新版本）
civitai-dl download model 12345

# 下载指定版本的模型
civitai-dl download model 12345 --version 67890

# 下载模型并保存到指定目录
civitai-dl download model 12345 --output "./my_models"

# 下载模型并同时下载10张示例图像
civitai-dl download model 12345 --with-images --image-limit 10
```

## 批量下载多个模型

### 基本用法
```bash
civitai-dl download models [OPTIONS]
```

### 选项
- `--ids`, `-i`：要下载的模型ID列表，用逗号分隔
- `--from-file`, `-f`：从文件读取模型ID列表，每行一个ID
- `--output`, `-o`：指定下载文件的保存目录
- `--format`：首选文件格式
- `--concurrent`, `-c`：并行下载的任务数量（默认3）
- `--save-metadata`：保存模型元数据（默认为true）

### 示例
```bash
# 下载多个指定ID的模型
civitai-dl download models --ids "12345,67890,13579"

# 从文件读取模型ID列表进行下载
civitai-dl download models --from-file models.txt

# 批量下载并指定5个并行任务
civitai-dl download models --ids "12345,67890,13579" --concurrent 5
```

## 下载模型示例图像

### 基本用法
```bash
civitai-dl download images [OPTIONS]
```

### 选项
- `--model`, `-m`：模型ID（必填，除非指定了`--version`）
- `--version`, `-v`：版本ID（与`--model`二选一）
- `--limit`, `-l`：下载数量限制（默认10）
- `--output`, `-o`：指定下载文件的保存目录
- `--nsfw`：NSFW级别过滤，可选值为`None`, `Soft`, `Mature`, `X`，可多选
- `--gallery`：是否包含社区画廊图像
- `--save-metadata`：保存图像元数据（默认为true）

### 示例
```bash
# 下载特定模型的示例图像
civitai-dl download images --model 12345

# 下载特定版本的示例图像
civitai-dl download images --version 67890

# 下载模型的示例图像，限制数量为20张
civitai-dl download images --model 12345 --limit 20

# 下载包括社区画廊的图像
civitai-dl download images --model 12345 --gallery

# 下载包含特定NSFW级别的图像
civitai-dl download images --model 12345 --nsfw Soft --nsfw Mature
```
```

### [browse-commands.md](file:///c%3A/Users/kcloud/workspace/civitai-downloader/docs/guide/browse-commands.md)

```markdown
# 浏览和搜索命令使用指南

本文档详细介绍了Civitai Downloader提供的所有浏览和搜索相关命令及其用法。

## 搜索和浏览模型

### 基本用法
```bash
civitai-dl browse models [OPTIONS]
```

### 选项
- `--query`, `-q`：搜索关键词
- `--type`, `-t`：模型类型筛选，如`Checkpoint`, `LORA`, `TextualInversion`等
- `--sort`, `-s`：排序方式，可选值为`Highest Rated`, `Most Downloaded`, `Newest`（默认为`Most Downloaded`）
- `--limit`, `-l`：结果数量限制（默认20）
- `--nsfw`：是否包含NSFW内容（默认不包含）
- `--output`, `-o`：将结果保存到指定的JSON文件
- `--creator`, `-c`：按创作者筛选
- `--tag`：按标签筛选

### 示例
```bash
# 搜索关键词为"portrait"的模型
civitai-dl browse models --query "portrait"

# 搜索LORA类型的模型
civitai-dl browse models --type "LORA"

# 组合搜索：搜索关键词为"portrait"且类型为"LORA"的模型
civitai-dl browse models --query "portrait" --type "LORA"

# 搜索并按评分排序
civitai-dl browse models --query "portrait" --sort "Highest Rated"

# 搜索并显示更多结果
civitai-dl browse models --query "portrait" --limit 50

# 搜索特定创作者的模型
civitai-dl browse models --creator "username"

# 将搜索结果保存为JSON文件
civitai-dl browse models --query "portrait" --output results.json
```

## 浏览标签

### 基本用法
```bash
civitai-dl browse tags [OPTIONS]
```

### 选项
- `--query`, `-q`：搜索关键词
- `--limit`, `-l`：结果数量限制（默认20）
- `--output`, `-o`：将结果保存到指定的JSON文件

### 示例
```bash
# 浏览所有热门标签
civitai-dl browse tags

# 搜索特定关键词的标签
civitai-dl browse tags --query "portrait"

# 显示更多标签
civitai-dl browse tags --limit 50

# 将标签保存到文件
civitai-dl browse tags --output tags.json
```

## 浏览创作者

### 基本用法
```bash
civitai-dl browse creators [OPTIONS]
```

### 选项
- `--query`, `-q`：搜索关键词
- `--limit`, `-l`：结果数量限制（默认20）
- `--output`, `-o`：将结果保存到指定的JSON文件

### 示例
```bash
# 浏览热门创作者
civitai-dl browse creators

# 搜索特定创作者
civitai-dl browse creators --query "username"

# 显示更多创作者
civitai-dl browse creators --limit 50

# 将创作者列表保存到文件
civitai-dl browse creators --output creators.json
```

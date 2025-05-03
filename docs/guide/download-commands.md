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
- `--version`, `-v`：版本ID（与`--model`二选一，建议同时提供model和version以获得更好的结果）
- `--limit`, `-l`：下载数量限制（默认10）
- `--output`, `-o`：指定下载文件的保存目录
- `--nsfw`：NSFW级别过滤，可选值为`None`, `Soft`, `Mature`, `X`，可多选
- `--gallery`：是否包含社区画廊图像
- `--save-metadata`：保存图像元数据（默认为true）
- `--pattern`：图片文件命名模式，支持以下变量：{model_id}、{version_id}、{index}、{image_id}、{width}、{height}（默认为"{model_id}_{index}_{image_id}"）

### 示例
```bash
# 下载特定模型的示例图像
civitai-dl download images --model 12345

# 下载特定版本的示例图像（同时提供模型ID可提高成功率）
civitai-dl download images --model 12345 --version 67890

# 下载模型的示例图像，限制数量为20张
civitai-dl download images --model 12345 --limit 20

# 下载包括社区画廊的图像
civitai-dl download images --model 12345 --gallery

# 下载包含特定NSFW级别的图像
civitai-dl download images --model 12345 --nsfw Soft --nsfw Mature

# 下载并指定输出目录
civitai-dl download images --model 12345 --output "./images"

# 使用自定义文件命名模式下载图像
civitai-dl download images --model 12345 --pattern "{model_id}_{image_id}_{width}x{height}"
```

### 注意事项
1. 当只提供`--version`参数而不提供`--model`参数时，程序会尝试从API中获取该版本的模型ID。但为了获得最佳结果，建议同时提供两个参数。
2. 若下载过程中遇到文件路径问题，可尝试使用`--output`参数指定一个绝对路径，确保程序有权限创建和写入该目录。
3. 默认情况下，图片将保存在以下路径格式中：`<output_dir>/model_<model_id>_examples_v<version_id>/<filename>`。您可以通过`--pattern`参数自定义文件名格式。
4. 下载的每张图片会同时保存一个同名的元数据文件（.meta.json），包含图片的生成参数和相关信息。
5. 如果遇到"No such file or directory"错误，这通常是因为程序无法创建嵌套目录结构。解决方案：
   - 使用`--output`参数指定一个已存在的目录
   - 确保您有写入权限
   - 避免路径中使用特殊字符
   - 在Windows上，路径长度不要超过260个字符

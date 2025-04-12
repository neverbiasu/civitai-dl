# 命令行工具使用指南

Civitai Downloader 提供了功能强大的命令行界面(CLI)，让您可以方便地下载模型和图像，无需图形界面即可操作。

## 基础用法

在安装完成后，您可以通过`civitai-dl`命令访问所有功能。使用`--help`选项可查看命令帮助:

```bash
civitai-dl --help
```

## 基本命令结构

命令行工具采用层级命令结构，主要包含以下几组命令：

- `download`: 下载模型和图像
- `browse`: 浏览和搜索模型库
- `webui`: 启动Web图形界面

## 下载命令

### 下载单个模型

```bash
civitai-dl download model MODEL_ID [OPTIONS]
```

**参数:**
- `MODEL_ID`: Civitai模型ID（必填）

**选项:**
- `--version`, `-v`: 指定版本ID
- `--output`, `-o`: 输出路径
- `--format`, `-f`: 首选文件格式(如safetensors)
- `--with-images`: 同时下载示例图像
- `--image-limit`: 下载的图像数量限制(默认5)

**示例:**

下载指定ID的模型（最新版本）:
```bash
civitai-dl download model 12345
```

下载指定版本:
```bash
civitai-dl download model 12345 --version 67890
```

下载到指定路径:
```bash
civitai-dl download model 12345 --output "./my_models"
```

下载模型及其示例图像:
```bash
civitai-dl download model 12345 --with-images --image-limit 10
```

### 批量下载多个模型

```bash
civitai-dl download models [OPTIONS]
```

**选项:**
- `--ids`, `-i`: 模型ID列表，用逗号分隔
- `--from-file`, `-f`: 从文件读取模型ID列表
- `--output`, `-o`: 输出目录
- `--format`: 首选文件格式
- `--concurrent`: 并行下载数量(默认1)

**示例:**

下载多个模型:
```bash
civitai-dl download models --ids "12345,67890,13579"
```

从文件读取模型ID列表:
```bash
civitai-dl download models --from-file models.txt
```

### 下载模型示例图像

```bash
civitai-dl download images [OPTIONS]
```

**选项:**
- `--model`, `-m`: 模型ID
- `--version`, `-v`: 版本ID
- `--limit`, `-l`: 下载数量限制(默认10)
- `--output`, `-o`: 输出目录
- `--nsfw`: 包含NSFW内容

**示例:**

下载模型的示例图像:
```bash
civitai-dl download images --model 12345 --limit 20
```

下载特定版本的图像:
```bash
civitai-dl download images --model 12345 --version 67890
```

## 浏览和搜索命令

### 搜索模型

```bash
civitai-dl browse models [OPTIONS]
```

**选项:**
- `--query`, `-q`: 搜索关键词
- `--type`, `-t`: 模型类型
- `--limit`, `-l`: 结果数量(默认20)

**示例:**

搜索特定关键词的模型:
```bash
civitai-dl browse models --query "portrait" --limit 50
```

搜索特定类型的模型:
```bash
civitai-dl browse models --type "LORA"
```

## 启动Web界面

```bash
civitai-dl webui
```

此命令将启动基于Web的图形界面，您可以在浏览器中访问和操作。

## 配置文件

Civitai Downloader的配置文件默认位于`~/.civitai-dl/config.json`，您可以通过编辑此文件来设置默认选项。

**主要配置项:**
- `api_key`: Civitai API密钥
- `output_dir`: 默认下载目录
- `concurrent_downloads`: 并行下载数量
- `nsfw_level`: NSFW内容级别过滤
- `proxy`: 代理服务器设置

## 使用技巧

1. **处理大型文件**  
   下载大型模型时会显示进度条，可以安全地中断下载，重新运行相同命令将会从断点续传。

2. **批量操作**  
   创建模型ID列表文件便于批量下载，每行一个ID:
   ```
   12345
   67890
   13579
   ```
   
3. **模型组织**  
   下载的模型默认保存在`./downloads`目录，建议根据项目需求设置自定义输出路径。

## 命令行选项通用说明

以下选项适用于所有命令:

- `--verbose`, `-v`: 增加输出的详细程度
- `--quiet`, `-q`: 静默模式，减少输出信息
- `--version`: 显示版本信息

## 常见问题

**Q: 如何设置API密钥？**  
A: 编辑`~/.civitai-dl/config.json`文件，添加`"api_key": "您的密钥"`。

**Q: 下载失败怎么办？**  
A: 默认情况下会自动重试，您也可以重新运行相同的命令继续下载。

**Q: 如何在代理环境中使用？**  
A: 在配置中设置`"proxy": "http://user:pass@host:port"`。

## 高级使用场景

### 与其他工具集成

您可以将Civitai Downloader集成到脚本或其他工具中:

```bash
# 下载特定模型并处理
civitai-dl download model 12345 --output ./models
some_other_tool --input ./models/model_file.safetensors
```

### 配置代理服务器

如果您需要通过代理访问Civitai:

```json
// ~/.civitai-dl/config.json
{
  "proxy": "http://127.0.0.1:1080",
  "verify_ssl": true
}
```

## 获取帮助

如需更多帮助，可以查看每个命令的详细说明:

```bash
civitai-dl download --help
civitai-dl download model --help
```

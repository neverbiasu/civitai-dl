# 图像命令使用指南

本文档详细介绍了Civitai Downloader提供的所有图像处理相关命令及其用法。

## 提取图像元数据

### 基本用法
```bash
civitai-dl image info PATH [OPTIONS]
```

### 参数
- `PATH`：图像文件路径（必填）

### 选项
- `--format`, `-f`：输出格式，可选值为`json`或`text`（默认为`text`）

### 示例
```bash
# 提取图像元数据并以文本形式显示
civitai-dl image info "./images/example.png"

# 提取图像元数据并以JSON格式显示
civitai-dl image info "./images/example.png" --format json
```

## 批量处理图像

### 基本用法
```bash
civitai-dl image batch DIRECTORY [OPTIONS]
```

### 参数
- `DIRECTORY`：要处理的图像目录（必填）

### 选项
- `--recursive`, `-r`：是否递归处理子目录中的图像
- `--extract-params`, `-e`：是否提取生成参数
- `--output`, `-o`：输出结果保存路径

### 示例
```bash
# 处理指定目录中的所有图像
civitai-dl image batch "./images"

# 递归处理子目录中的所有图像
civitai-dl image batch "./images" --recursive

# 处理图像并提取生成参数
civitai-dl image batch "./images" --extract-params

# 处理图像并将结果保存到指定文件
civitai-dl image batch "./images" --output "metadata.json"
```

## 图像元数据提取内容

提取的图像元数据通常包含以下信息：

1. 基本信息：尺寸、格式、创建日期
2. EXIF数据：相机参数、GPS信息（如果有）
3. 生成参数：用于AI生成的提示词、模型设置、采样器设置等
4. 模型信息：创建图像使用的模型、版本等

提取的元数据格式示例：

```json
{
  "basic": {
    "width": 1024,
    "height": 1024,
    "format": "PNG",
    "created": "2023-04-17T12:34:56"
  },
  "parameters": {
    "prompt": "portrait of a woman, highly detailed...",
    "negative_prompt": "blurry, bad hands...",
    "steps": 30,
    "sampler": "DPM++ 2M Karras",
    "cfg_scale": 7.0,
    "seed": 1234567890
  },
  "model": {
    "name": "Example Model",
    "type": "Checkpoint",
    "id": 12345,
    "version": "v1.0",
    "version_id": 67890
  }
}
```
```

### [webui-command.md](file:///c%3A/Users/kcloud/workspace/civitai-downloader/docs/guide/webui-command.md)

```markdown
# WebUI命令使用指南

本文档详细介绍了如何使用Civitai Downloader的Web图形界面。

## 启动WebUI

### 基本用法
```bash
civitai-dl webui [OPTIONS]
```

### 选项
- `--host`: WebUI服务器主机地址（默认为"0.0.0.0"，表示监听所有网络接口）
- `--port`: WebUI服务器端口（默认为7860）
- `--share`: 是否创建公共链接，使WebUI可以通过互联网访问（默认为false）

### 示例
```bash
# 使用默认设置启动WebUI
civitai-dl webui

# 指定端口启动WebUI
civitai-dl webui --port 8080

# 只在本地访问（不允许其他设备连接）
civitai-dl webui --host "127.0.0.1"

# 创建可公开访问的链接
civitai-dl webui --share
```

## WebUI界面说明

启动WebUI后，您可以通过浏览器访问`http://localhost:7860`（或您指定的其他地址和端口）来使用图形界面。

### 主要标签页

WebUI包含以下几个主要标签页：

1. **下载模型**：通过ID下载指定的模型
2. **模型搜索**：搜索和浏览Civitai上的模型
3. **图像下载**：下载模型相关的示例图像
4. **下载队列**：管理下载任务队列
5. **设置**：配置应用程序选项

### 下载模型页面

在此页面，您可以通过模型ID下载特定模型：
- 输入模型ID和（可选的）版本ID
- 设置输出目录
- 选择是否同时下载示例图像
- 点击"下载"按钮开始下载

### 图像下载页面

在此页面，您可以下载模型相关的图像：
- 输入模型ID或版本ID
- 设置NSFW过滤选项
- 选择是否包含社区画廊图像
- 设置下载数量限制
- 点击"获取图像"预览图像
- 点击"下载所有图像"开始下载

### 下载队列页面

在此页面，您可以管理所有下载任务：
- 查看当前下载队列中的所有任务
- 暂停、恢复或取消特定任务
- 批量操作（全部暂停/恢复/取消）
- 查看任务进度和下载速度

### 设置页面

在此页面，您可以配置应用程序的各项设置：
- **基本设置**：API密钥、代理设置、界面主题
- **下载设置**：默认下载路径、并行下载任务数、分块大小
- **路径设置**：模型和图像的路径模板
- **高级设置**：请求超时、最大重试次数、SSL验证等

所有设置项都会自动保存，无需手动提交。

## 使用提示

1. WebUI与CLI命令使用相同的配置文件，修改其中一个将影响另一个
2. 部分高级功能可能仅在CLI中提供，未来会逐步添加到WebUI中
3. 界面支持深色/浅色模式切换，可根据个人偏好设置
4. 在移动设备上也可使用，界面会自动适应屏幕尺寸
```

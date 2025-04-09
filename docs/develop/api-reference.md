# Civitai Downloader API 参考

## Civitai API 端点

本文档提供 Civitai API 主要端点的使用方法和示例。

### 模型相关 API

#### 获取模型列表

```
GET https://civitai.com/api/v1/models
```

**参数:**
- `limit`: 每页结果数量 (默认: 20, 最大: 100)
- `page`: 页码 (默认: 1)
- `query`: 搜索关键词
- `tag`: 按标签筛选
- `type`: 模型类型 (Checkpoint, TextualInversion, LORA, 等)
- `sort`: 排序方式 (Highest Rated, Most Downloaded, 等)

**示例请求:**
```bash
curl -X GET "https://civitai.com/api/v1/models?limit=10&query=portrait&type=LORA"
```

#### 获取模型详情

```
GET https://civitai.com/api/v1/models/{id}
```

**示例请求:**
```bash
curl -X GET "https://civitai.com/api/v1/models/12345"
```

#### 获取模型版本

```
GET https://civitai.com/api/v1/model-versions/{id}
```

**示例请求:**
```bash
curl -X GET "https://civitai.com/api/v1/model-versions/54321"
```

### 图像相关 API

#### 获取图像列表

```
GET https://civitai.com/api/v1/images
```

**参数:**
- `limit`: 每页结果数量
- `modelId`: 按模型ID筛选
- `modelVersionId`: 按模型版本ID筛选

**示例请求:**
```bash
curl -X GET "https://civitai.com/api/v1/images?modelId=12345&limit=20"
```

#### 获取图像详情

```
GET https://civitai.com/api/v1/images/{id}
```

**示例请求:**
```bash
curl -X GET "https://civitai.com/api/v1/images/67890"
```

### 创作者相关 API

#### 获取创作者信息

```
GET https://civitai.com/api/v1/creators/{username}
```

**示例请求:**
```bash
curl -X GET "https://civitai.com/api/v1/creators/username123"
```

### 标签相关 API

#### 获取标签列表

```
GET https://civitai.com/api/v1/tags
```

**参数:**
- `limit`: 每页结果数量
- `query`: 搜索关键词

**示例请求:**
```bash
curl -X GET "https://civitai.com/api/v1/tags?query=portrait"
```

## 身份验证

某些API操作需要API密钥:

```bash
curl -X GET "https://civitai.com/api/v1/models" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 错误处理

API返回标准HTTP状态码:
- `200 OK`: 请求成功
- `400 Bad Request`: 参数无效
- `401 Unauthorized`: 身份验证失败
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `429 Too Many Requests`: 请求过于频繁
- `500 Internal Server Error`: 服务器错误

## 速率限制

未经身份验证的请求限制为每分钟10次，使用API密钥可提高限制。

## 数据模型

### 模型对象结构

```json
{
  "id": 12345,
  "name": "模型名称",
  "description": "模型描述",
  "type": "Checkpoint",
  "nsfw": false,
  "tags": ["portrait", "realistic"],
  "creator": {
    "username": "creator123",
    "image": "https://example.com/avatar.jpg"
  },
  "stats": {
    "downloadCount": 1000,
    "favoriteCount": 500,
    "commentCount": 50,
    "ratingCount": 200,
    "rating": 4.8
  },
  "modelVersions": [
    {
      "id": 54321,
      "name": "v1.0",
      "createdAt": "2023-01-01T00:00:00.000Z",
      "downloadUrl": "https://civitai.com/api/download/models/54321"
    }
  ]
}
```

### 图像对象结构

```json
{
  "id": 67890,
  "url": "https://example.com/image.png",
  "nsfw": false,
  "width": 512,
  "height": 768,
  "hash": "abcdef123456",
  "meta": {
    "prompt": "超详细的生成提示词...",
    "negativePrompt": "反向提示词...",
    "steps": 30,
    "sampler": "Euler a",
    "cfgScale": 7,
    "seed": 1234567890
  },
  "model": {
    "id": 12345,
    "name": "模型名称",
    "modelVersionId": 54321
  }
}
```

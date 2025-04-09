# Civitai API 参考

## API概览

| 端点                         | 作用           | 分页方式 | 主要参数                        |
| ---------------------------- | -------------- | -------- | ------------------------------- |
| `/api/v1/models`             | 获取模型列表   | page     | limit, query, types, sort, nsfw |
| `/api/v1/models/:id`         | 获取模型详情   | -        | modelId                         |
| `/api/v1/model-versions/:id` | 获取版本详情   | -        | modelVersionId                  |
| `/api/v1/images`             | 获取图像列表   | cursor   | limit, modelId, nsfw            |
| `/api/v1/creators`           | 获取创作者列表 | page     | limit, query                    |
| `/api/v1/tags`               | 获取标签列表   | page     | limit, query                    |
| `/api/download/models/:id`   | 下载模型文件   | -        | modelVersionId, token           |

## 认证方式

- **请求头认证**: 通过Authorization头部传递API密钥
- **URL参数认证**: 通过查询参数传递API密钥

## 重要注意事项

1. 2023年7月2日后，图像API改用游标分页而非页码分页
2. 部分模型下载需要API Key认证
3. 服务器会对过于频繁的请求进行限流
4. 对于大型模型，要处理断点续传
5. 文件名应从`content-disposition`头部获取

# 引言

本文档描述了如何使用 Civitai REST API。我们将描述每个操作的 HTTP method、path 和 parameters。API 将返回 response status code、response headers 和 response body。

> 这仍在积极开发中，一旦有更多端点向公众开放，将会进行更新

## Civitai API v1

- [授权](#授权)

### Creators
 - [GET /api/v1/creators](#get-apiv1creators)

### Images
- [GET /api/v1/images](#get-apiv1images)

### Models
 - [GET /api/v1/models](#get-apiv1models)

### Model
 - [GET /api/v1/models/:modelId](#get-apiv1modelsmodelid)

### Model Version
 - [GET /api/v1/model-versions/:modelVersionId](#get-apiv1models-versionsmodelversionid)
 - [GET /api/v1/model-versions/by-hash/:hash](#get-apiv1models-versionsby-hashhash)

### Tags
 - [GET /api/v1/tags](#get-apiv1tags)

## 授权

要以用户身份发出经授权的请求，您必须使用 API Key。您可以从您的[用户账户设置](https://civitai.com/user/account)生成 API Key。

一旦您拥有 API Key，您可以使用 Authorization Header 或 Query String 进行身份验证。

创作者可以要求用户登录才能下载他们的资源。这是我们提供的一个选项，但并非强制要求——这完全取决于资源所有者。

有关更多详细信息，请参阅[通过 API 下载指南](https://education.civitai.com/civitais-guide-to-downloading-via-api/)，如果您在下载时仍遇到问题，请提交 issue。

### 授权标头

您可以使用 `Authorization` 标头将 API token 作为 Bearer token 传递：

```
GET https://civitai.com/api/v1/models
Content-Type: application/json
Authorization: Bearer {api_key}
```

### 查询字符串

您可以使用 `?token=` 参数将 API token 作为查询参数传递：

```
GET https://civitai.com/api/v1/models?token={api_key}
Content-Type: application/json
```

在某些 notebook 和脚本中，这种方法可能更简单。

### GET /api/v1/creators

#### 端点 URL

`https://civitai.com/api/v1/creators`

#### 查询参数

| Name               | Type   | Description                                                                                                      |
| ------------------ | ------ | ---------------------------------------------------------------------------------------------------------------- |
| limit `(OPTIONAL)` | number | 每页返回的结果数量。这个数字可以在 0 到 200 之间。默认情况下，每页返回 20 个结果。如果设置为 0，则返回所有创作者 |
| page `(OPTIONAL)`  | number | 开始获取创作者的页面                                                                                             |
| query `(OPTIONAL)` | string | 用于按用户名筛选创作者的搜索查询                                                                                 |

#### 响应字段

| Name                 | Type   | Description              |
| -------------------- | ------ | ------------------------ |
| username             | string | 创作者的用户名           |
| modelCount           | number | 与此用户关联的模型数量   |
| link                 | string | 获取此用户所有模型的 Url |
| metadata.totalItems  | string | 可用的总项目数           |
| metadata.currentPage | string | 您当前所在的页面         |
| metadata.pageSize    | string | 批次的大小               |
| metadata.totalPages  | string | 总页数                   |
| metadata.nextPage    | string | 获取下一批项目的 url     |
| metadata.prevPage    | string | 获取上一批项目的 url     |

#### 示例

以下示例显示了一个从我们的数据库中获取前 3 个模型标签的请求：
```sh
curl https://civitai.com/api/v1/creators?limit=3 \
-H "Content-Type: application/json" \
-X GET
```

这将产生以下响应：
```json
{
  "items": [
    {
      "username": "Civitai",
      "modelCount": 848,
      "link": "https://civitai.com/api/v1/models?username=Civitai"
    },
    {
      "username": "JustMaier",
      "modelCount": 8,
      "link": "https://civitai.com/api/v1/models?username=JustMaier"
    },
    {
      "username": "maxhulker",
      "modelCount": 2,
      "link": "https://civitai.com/api/v1/models?username=maxhulker"
    }
  ],
  "metadata": {
    "totalItems": 46,
    "currentPage": 1,
    "pageSize": 3,
    "totalPages": 16,
    "nextPage": "https://civitai.com/api/v1/creators?limit=3&page=2"
  }
}
```

### GET /api/v1/images

#### 端点 URL

`https://civitai.com/api/v1/images`

#### 查询参数

| Name                        | Type                                           | Description                                                                         |
| --------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------- |
| limit `(OPTIONAL)`          | number                                         | 每页返回的结果数量。这个数字可以在 0 到 200 之间。默认情况下，每页返回 100 个结果。 |
| postId `(OPTIONAL)`         | number                                         | 要从中获取图像的帖子的 ID                                                           |
| modelId `(OPTIONAL)`        | number                                         | 要从中获取图像的模型的 ID（模型画廊）                                               |
| modelVersionId `(OPTIONAL)` | number                                         | 要从中获取图像的模型版本的 ID（筛选到特定版本的模型画廊）                           |
| username `(OPTIONAL)`       | string                                         | 筛选特定用户的图像                                                                  |
| nsfw `(OPTIONAL)`           | boolean \| enum `(None, Soft, Mature, X)`      | 筛选是否包含成人内容标记的图像（undefined 返回所有）                                |
| sort `(OPTIONAL)`           | enum `(Most Reactions, Most Comments, Newest)` | 您希望对结果进行排序的顺序                                                          |
| period `(OPTIONAL)`         | enum `(AllTime, Year, Month, Week, Day)`       | 图像排序的时间范围                                                                  |
| page `(OPTIONAL)`           | number                                         | 开始获取创作者的页面                                                                |

#### 响应字段

| Name                 | Type                           | Description                      |
| -------------------- | ------------------------------ | -------------------------------- |
| id                   | number                         | 图像的 id                        |
| url                  | string                         | 图像在其源分辨率下的 url         |
| hash                 | string                         | 图像的 blurhash                  |
| width                | number                         | 图像的宽度                       |
| height               | number                         | 图像的高度                       |
| nsfw                 | boolean                        | 图像是否具有任何成人内容标签     |
| nsfwLevel            | enum `(None, Soft, Mature, X)` | 图像的 NSFW 级别                 |
| createdAt            | date                           | 图像发布的日期                   |
| postId               | number                         | 图像所属帖子的 ID                |
| stats.cryCount       | number                         | cry 反应的数量                   |
| stats.laughCount     | number                         | laugh 反应的数量                 |
| stats.likeCount      | number                         | like 反应的数量                  |
| stats.heartCount     | number                         | heart 反应的数量                 |
| stats.commentCount   | number                         | comment 反应的数量               |
| meta                 | object                         | 图像的生成参数（已解析或输入的） |
| username             | string                         | 创作者的用户名                   |
| metadata.nextCursor  | number                         | 下一批次中第一个图像的 id        |
| metadata.currentPage | number                         | 您当前所在的页面（如果使用分页） |
| metadata.pageSize    | number                         | 批次的大小（如果使用分页）       |
| metadata.nextPage    | string                         | 获取下一批项目的 url             |

#### 示例

以下示例显示了一个获取第一张图像的请求：
```sh
curl https://civitai.com/api/v1/images?limit=1 \
-H "Content-Type: application/json" \
-X GET
```

这将产生以下响应：
<details>
  <summary>点击展开</summary>

  ```json
  {
    "items": [
      {
        "id": 469632,
        "url": "https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/cc5caabb-e05f-4976-ff3c-7058598c4e00/width=1024/cc5caabb-e05f-4976-ff3c-7058598c4e00.jpeg",
        "hash": "UKHU@6H?_ND*_3M{t84o^+%MD%xuXSxasAt7",
        "width": 1024,
        "height": 1536,
        "nsfw": false,
        "nsfwLevel": "None",
        "createdAt": "2023-04-11T15:33:12.500Z",
        "postId": 138779,
        "stats": {
          "cryCount": 0,
          "laughCount": 0,
          "likeCount": 0,
          "dislikeCount": 0,
          "heartCount": 0,
          "commentCount": 0
        },
        "meta": {
          "Size": "512x768",
          "seed": 234871805,
          "Model": "Meina",
          "steps": 35,
          "prompt": "<lora:setsunaTokage_v10:0.6>, green hair, long hair, standing, (ribbed dress), zettai ryouiki, choker, (black eyes), looking at viewer, adjusting hair, hand in own hair, street, grin, sharp teeth, high ponytail, [Style of boku no hero academia]",
          "sampler": "DPM++ SDE Karras",
          "cfgScale": 7,
          "Clip skip": "2",
          "Hires upscale": "2",
          "Hires upscaler": "4x-AnimeSharp",
          "negativePrompt": "(worst quality, low quality, extra digits:1.3), easynegative,",
          "Denoising strength": "0.4"
        },
        "username": "Cooler_Rider"
      }
    ],
    "metadata": {
      "nextCursor": 101,
      "currentPage": 1,
      "pageSize": 100,
      "nextPage": "https://civitai.com/api/v1/images?page=2"
    }
  }
  ```
</details>

**注意：**
- 由于此端点的数据量和请求量巨大，我们于 2023 年 7 月 2 日从分页系统切换到基于游标的系统。
- 无论您使用分页还是游标，都可以使用 `metadata.nextPage` 获取下一页结果

### GET /api/v1/models

#### 端点 URL

`https://civitai.com/api/v1/models`

#### 查询参数

| Name                                | Type                                                                                              | Description                                                                              |
| ----------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| limit `(OPTIONAL)`                  | number                                                                                            | 每页返回的结果数量。这个数字可以在 1 到 100 之间。默认情况下，每页返回 100 个结果        |
| page `(OPTIONAL)`                   | number                                                                                            | 开始获取模型的页面                                                                       |
| query `(OPTIONAL)`                  | string                                                                                            | 用于按名称筛选模型的搜索查询                                                             |
| tag `(OPTIONAL)`                    | string                                                                                            | 用于按标签筛选模型的搜索查询                                                             |
| username `(OPTIONAL)`               | string                                                                                            | 用于按用户筛选模型的搜索查询                                                             |
| types `(OPTIONAL)`                  | enum[] `(Checkpoint, TextualInversion, Hypernetwork, AestheticGradient, LORA, Controlnet, Poses)` | 您想要筛选的模型类型。如果未指定，则返回所有类型                                         |
| sort `(OPTIONAL)`                   | enum `(Highest Rated, Most Downloaded, Newest)`                                                   | 您希望对结果进行排序的顺序                                                               |
| period `(OPTIONAL)`                 | enum `(AllTime, Year, Month, Week, Day)`                                                          | 模型排序的时间范围                                                                       |
| rating `(OPTIONAL)` (Deprecated)    | number                                                                                            | 您希望筛选模型的评分。如果未指定，则返回任何评分的模型                                   |
| favorites `(OPTIONAL)` `(AUTHED)`   | boolean                                                                                           | 筛选已验证用户的收藏夹（这需要 API token 或 session cookie）                             |
| hidden `(OPTIONAL)` `(AUTHED)`      | boolean                                                                                           | 筛选已验证用户的隐藏模型（这需要 API token 或 session cookie）                           |
| primaryFileOnly `(OPTIONAL)`        | boolean                                                                                           | 每个模型仅包含主文件（如果您使用 API token 或 session cookie，这将使用您的首选格式选项） |
| allowNoCredit `(OPTIONAL)`          | boolean                                                                                           | 筛选需要或不需要标注创作者的模型                                                         |
| allowDerivatives `(OPTIONAL)`       | boolean                                                                                           | 筛选允许或不允许创建衍生品的模型                                                         |
| allowDifferentLicenses `(OPTIONAL)` | boolean                                                                                           | 筛选允许或不允许衍生品具有不同许可证的模型                                               |
| allowCommercialUse `(OPTIONAL)`     | enum `(None, Image, Rent, Sell)`                                                                  | 根据其商业许可筛选模型                                                                   |
| nsfw `(OPTIONAL)`                   | boolean                                                                                           | 如果为 false，将返回更安全的图像并隐藏没有安全图像的模型                                 |
| supportsGeneration `(OPTIONAL)`     | boolean                                                                                           | 如果为 true，将返回支持生成的模型                                                        |

#### 响应字段

| Name                                 | Type                                                                                            | Description                                                                                        |
| ------------------------------------ | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| id                                   | number                                                                                          | 模型的标识符                                                                                       |
| name                                 | string                                                                                          | 模型的名称                                                                                         |
| description                          | string                                                                                          | 模型的描述 (HTML)                                                                                  |
| type                                 | enum `(Checkpoint, TextualInversion, Hypernetwork, AestheticGradient, LORA, Controlnet, Poses)` | 模型类型                                                                                           |
| nsfw                                 | boolean                                                                                         | 模型是否为 NSFW                                                                                    |
| tags                                 | string[]                                                                                        | 与模型关联的标签                                                                                   |
| mode                                 | enum `(Archived, TakenDown)` \| null                                                            | 模型当前所处的模式。如果为 `Archived`，`files` 字段将为空。如果为 `TakenDown`，`images` 字段将为空 |
| creator.username                     | string                                                                                          | 创作者的名称                                                                                       |
| creator.image                        | string \| null                                                                                  | 创作者头像的 url                                                                                   |
| stats.downloadCount                  | number                                                                                          | 模型的下载次数                                                                                     |
| stats.favoriteCount                  | number                                                                                          | 模型的收藏次数                                                                                     |
| stats.commentCount                   | number                                                                                          | 模型的评论次数                                                                                     |
| stats.ratingCount                    | number                                                                                          | 模型的评分次数                                                                                     |
| stats.rating                         | number                                                                                          | 模型的平均评分                                                                                     |
| modelVersions.id                     | number                                                                                          | 模型版本的标识符                                                                                   |
| modelVersions.name                   | string                                                                                          | 模型版本的名称                                                                                     |
| modelVersions.description            | string                                                                                          | 模型版本的描述（通常是变更日志）                                                                   |
| modelVersions.createdAt              | Date                                                                                            | 版本创建的日期                                                                                     |
| modelVersions.downloadUrl            | string                                                                                          | 获取此特定版本模型文件的下载 url                                                                   |
| modelVersions.trainedWords           | string[]                                                                                        | 用于触发模型的词语                                                                                 |
| modelVersions.files.sizeKb           | number                                                                                          | 模型文件的大小（KB）                                                                               |
| modelVersions.files.pickleScanResult | string                                                                                          | pickle 扫描的状态 ('Pending', 'Success', 'Danger', 'Error')                                        |
| modelVersions.files.virusScanResult  | string                                                                                          | 病毒扫描的状态 ('Pending', 'Success', 'Danger', 'Error')                                           |
| modelVersions.files.scannedAt        | Date \| null                                                                                    | 文件扫描的日期                                                                                     |
| modelVersions.files.primary          | boolean \| undefined                                                                            | 文件是否为模型版本的主文件                                                                         |
| modelVersions.files.metadata.fp      | enum (`fp16`, `fp32`) \| undefined                                                              | 文件指定的浮点精度                                                                                 |
| modelVersions.files.metadata.size    | enum (`full`, `pruned`) \| undefined                                                            | 文件指定的模型大小                                                                                 |
| modelVersions.files.metadata.format  | enum (`SafeTensor`, `PickleTensor`, `Other`) \| undefined                                       | 文件指定的模型格式                                                                                 |
| modelVersions.images.id              | string                                                                                          | 图像的 id                                                                                          |
| modelVersions.images.url             | string                                                                                          | 图像的 url                                                                                         |
| modelVersions.images.nsfw            | string                                                                                          | 图像是否为 NSFW（注意：如果模型是 NSFW，则将模型上的所有图像视为 NSFW）                            |
| modelVersions.images.width           | number                                                                                          | 图像的原始宽度                                                                                     |
| modelVersions.images.height          | number                                                                                          | 图像的原始高度                                                                                     |
| modelVersions.images.hash            | string                                                                                          | 图像的 [blurhash](https://blurha.sh/)                                                              |
| modelVersions.images.meta            | object \| null                                                                                  | 图像的生成参数                                                                                     |
| modelVersions.stats.downloadCount    | number                                                                                          | 模型的下载次数                                                                                     |
| modelVersions.stats.ratingCount      | number                                                                                          | 模型的评分次数                                                                                     |
| modelVersions.stats.rating           | number                                                                                          | 模型的平均评分                                                                                     |
| metadata.totalItems                  | string                                                                                          | 可用的总项目数                                                                                     |
| metadata.currentPage                 | string                                                                                          | 您当前所在的页面                                                                                   |
| metadata.pageSize                    | string                                                                                          | 批次的大小                                                                                         |
| metadata.totalPages                  | string                                                                                          | 总页数                                                                                             |
| metadata.nextPage                    | string                                                                                          | 获取下一批项目的 url                                                                               |
| metadata.prevPage                    | string                                                                                          | 获取上一批项目的 url                                                                               |

**注意：** 下载 url 使用 `content-disposition` 标头来正确设置文件名。请确保在获取下载时启用该标头。例如，使用 `wget`：
```
wget https://civitai.com/api/download/models/{modelVersionId} --content-disposition
```

如果您尝试下载的资源的创建者需要身份验证，那么您将需要一个 API Key 来下载它：
```
wget https://civitai.com/api/download/models/{modelVersionId}?token={api_key} --content-disposition
```

#### 示例

以下示例显示了一个从我们的数据库中获取前 3 个 `TextualInversion` 模型的请求：
```sh
curl https://civitai.com/api/v1/models?limit=3&types=TextualInversion \
-H "Content-Type: application/json" \
-X GET
```

这将产生以下响应：
<details>
  <summary>点击展开</summary>

  ```json
  {
    "items":[
      {
        "id":3036,
        "name":"CharTurner - Character Turnaround helper for 1.5 AND 2.1!",
        "description":"<h1>CharTurner</h1><p>Edit: <strong>controlNet</strong> works <strong>great </strong>with this. Charturner keeps the outfit consistent, controlNet openPose keeps the turns under control. </p><p><strong>Three versions,</strong> scroll down to pick the right one for you.</p><p>If you're unsure of what version you are running, it's <em>probably</em> 1.5, as it is more popular, but 2.1 is newer and gaining ground fast.</p><p><strong>Version 2, for 2.0 and 2.1 models<br />Version 2, for 1.5 models<br />Version 1, for 1.5 models</strong></p><p>BONUS: <a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/7252/charturnerbeta-lora-experimental\">Experimental </a>LORA released<br />used at your own risk. :D (mixes well tho)</p><p>Hey there! I'm a working artist, and I loathe doing character turnarounds, I find it the least fun part of character design. I've been working on an embedding that helps with this process, and, though it's not where I want it to be, I was encouraged to release it under the <a target=\"_blank\" rel=\"ugc\" href=\"https://en.wikipedia.org/wiki/Minimum_viable_product\"><u>MVP</u></a> principle.</p><p>I'm also working on a few more character embeddings, including a head turn around and an expression sheet. They're still way too raw to release tho.</p><p>Is there some type of embedding that would be useful for you? Let me know, i'm having fun making tools to fix all the stuff I hate doing by hand.</p><p>v1 is still a little bit... fiddly.</p><ul><li><p>Sampler: I use DPM++ 2m Karras or DDIM most often.</p></li><li><p>Highres. fix ON for best results</p></li><li><p>landscape orientation will get you more 'turns'; square images tend toward just front and back.</p></li><li><p>I like <a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/2540/elldreths-stolendreams-mix\"><u>https://civitai.com/models/2540/elldreths-stolendreams-mix</u></a> to make characters in.</p></li><li><p>I use an embedding trained on my own art (smoose) that I will release if people want it? But it's an aesthetic thing, just my own vibe.</p></li><li><p>I didn't really test this in any of the waifu/NAI type models, as I don't usually use them. Looks like it works but it probably has its own special dance.</p></li></ul><p>Things I'm working on for v2: EDIT: <strong>V2 out, see below! (also v2 2.1)</strong></p><ul><li><p>It fights you on style sometimes. I'm adding more various types of art styles to the dataset to combat this. -<strong> V2 has much better styles</strong></p></li><li><p>Open front coats and such tend to be open 'back' on the back view. Adding more types of clothing to the dataset to combat this. - <strong>Still has this problem</strong></p></li><li><p>Tends toward white and 'fit' characters, which isn't useful. Adding more diversity in body and skin tone to the dataset to combat this. - <strong>v2 Much more body and racial diversity added to the set, easier to get different results.</strong></p></li></ul><p>Helps create multiple full body views of a character. The intention is to get at least a front and back, and ideally, a front, 3/4, profile, 1/4 and back versions, in the same outfit.</p><p></p>",
        "type":"TextualInversion",
        "poi":false,
        "nsfw":false,
        "allowNoCredit":true,
        "allowCommercialUse":"Rent",
        "allowDerivatives":true,
        "allowDifferentLicense":true,
        "stats":{
          "downloadCount":56206,
          "favoriteCount":7433,
          "commentCount":236,
          "ratingCount":56,
          "rating":4.63
        },
        "creator":{
          "username":"mousewrites",
          "image":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/bdfe115f-4430-4ee7-31bc-eff38f86c500/width=96/mousewrites.jpeg"
        },
        "tags":[
          "character",
          "consistent character",
          "turnaround",
          "model sheet"
        ],
        "modelVersions":[
          {
            "id":9857,
            "modelId":3036,
            "name":"CharTurner V2 - For 2.1",
            "createdAt":"2023-02-12T22:44:01.442Z",
            "updatedAt":"2023-03-15T18:58:13.476Z",
            "trainedWords":[
              "21charturnerv2"
            ],
            "baseModel":"SD 2.1",
            "earlyAccessTimeFrame":0,
            "description":"<p>I'm not great at prompting for 2.1 yet, so I\"m sure your prompts will work better with it. Works fantastic with negative embeds. (still collecting links)</p><p><a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/7728/negativemutation\">https://civitai.com/models/7728/negativemutation</a></p>",
            "stats":{
              "downloadCount":25874,
              "ratingCount":7,
              "rating":4.29
            },
            "files":[
              {
                "name":"21charturnerv2.pt",
                "id":9500,
                "sizeKB":17.017578125,
                "type":"Model",
                "metadata":{
                  "fp":"fp16",
                  "size":"full",
                  "format":"PickleTensor"
                },
                "pickleScanResult":"Success",
                "pickleScanMessage":"No Pickle imports",
                "virusScanResult":"Success",
                "scannedAt":"2023-02-12T22:45:53.210Z",
                "hashes":{
                  "AutoV2":"F253ABB016",
                  "SHA256":"F253ABB016C22DD426D6E482F4F8C3960766DE6E4C02F151478BFB98F6985383",
                  "CRC32":"F500AADD",
                  "BLAKE3":"E7163C1A3F6B135A3E473CDD749BC1E6F4ED2D1AB43FEB1ACC4BEB1E5C205260"
                },
                "downloadUrl":"https://civitai.com/api/download/models/9857",
                "primary":true
              }
            ],
            "images":[
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/d197481b-1c21-4c14-c7fd-708f838a1000/width=450/96744.jpeg",
                "nsfw":false,
                "width":1238,
                "height":1293,
                "hash":"UAEVA;?]JoR6+^OaNxxC^jXSWXjF?G$~s.WY",
                "meta":null
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/e1fe96b4-c2e0-4e8b-094f-051a7e69e700/width=450/95916.jpeg",
                "nsfw":false,
                "width":1398,
                "height":1259,
                "hash":"U4FrbC^ljH_MFV00IUx[00McbvoM03o}t7xG",
                "meta":null
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/613ec8af-7010-4b24-38b3-aa4488b9b000/width=450/95915.jpeg",
                "nsfw":false,
                "width":992,
                "height":792,
                "hash":"U7Du;[xZRj~A-pt7a#Rj0hR+ofNH01WBoJbI",
                "meta":{
                  "ENSD":"31337",
                  "Size":"640x512",
                  "seed":2457887243,
                  "Score":"6.66",
                  "steps":30,
                  "prompt":"21CharTurnerV2 (character turnaround:1) of a woman in a greek outfit. Goddess, laurel leaves, rimlight, subsurface scattering",
                  "sampler":"DDIM",
                  "Eta DDIM":"0.16",
                  "cfgScale":4.5,
                  "resources":[

                  ],
                  "Model hash":"5f8c744ab3",
                  "Hires upscale":"1.55",
                  "Hires upscaler":"Latent (nearest-exact)",
                  "negativePrompt":"costume variations, outfit variations, sci-fi, tight clothes, skin tight, muscles.",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/478efb4a-d63c-4b0d-8f19-bd60d52fc700/width=450/95914.jpeg",
                "nsfw":false,
                "width":1184,
                "height":792,
                "hash":"USIEU--:xut6tmofWWoL~UV@ayay-pbHjZbH",
                "meta":{
                  "ENSD":"31337",
                  "Size":"768x512",
                  "seed":2930407241,
                  "Score":"4.53",
                  "steps":30,
                  "prompt":"21CharTurnerV2 (character turnaround:1) of a mailman. Male, dark hair, tattoos, blue uniform. multiple views of the same character, Highly detailed,, classicnegative",
                  "sampler":"DDIM",
                  "Eta DDIM":"0.16",
                  "cfgScale":13,
                  "resources":[

                  ],
                  "Model hash":"2c29f8668c",
                  "Hires upscale":"1.55",
                  "Hires upscaler":"Latent (nearest-exact)",
                  "negativePrompt":"costume variations, outfit variations, sci-fi, tight clothes, skin tight, muscles., cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry,bad anatomy , liquid body, malformed, mutated, bad proportions, uncoordinated body, unnatural body, disfigured, ugly, gross proportions ,mutation, disfigured, deformed, (mutation), (poorly drawn), wet, legs feet, cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands,",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/04e55b16-e671-463a-bde9-3898f053e600/width=450/95913.jpeg",
                "nsfw":false,
                "width":792,
                "height":792,
                "hash":"UFG+R6NLs+D*02xujGRkH?S$V?kV?^RjkVtR",
                "meta":{
                  "ENSD":"31337",
                  "Size":"512x512",
                  "seed":2355045755,
                  "Score":"5.84",
                  "steps":30,
                  "prompt":"21CharTurnerV2 character turnaround of young boy as a paperboy, cute adorable little kid, full body, standing, same outfit",
                  "sampler":"DDIM",
                  "Eta DDIM":"0.16",
                  "cfgScale":6.5,
                  "resources":[

                  ],
                  "Model hash":"5f8c744ab3",
                  "Hires upscale":"1.55",
                  "Hires upscaler":"Latent (nearest-exact)",
                  "negativePrompt":"costume variations, outfit variations, sci-fi, tight clothes, skin tight, muscles., cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry,bad anatomy , liquid body, malformed, mutated, bad proportions, uncoordinated body, unnatural body, disfigured, ugly, gross proportions ,mutation, disfigured, deformed, (mutation), (poorly drawn), wet, legs feet, cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands,",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/a70413cb-e2bf-4a92-25e5-ed4786452a00/width=450/95912.jpeg",
                "nsfw":false,
                "width":792,
                "height":792,
                "hash":"UIHLI%E3D*02~TbcaKEM0M%1$$^%9^WWsm-n",
                "meta":{
                  "ENSD":"31337",
                  "Size":"512x512",
                  "seed":4205732814,
                  "Score":"6.53",
                  "steps":30,
                  "prompt":"21CharTurnerV2 character turnaround of young boy as a paperboy, cute adorable little kid, full body, standing, same outfit, concept-art",
                  "sampler":"DDIM",
                  "Eta DDIM":"0.16",
                  "cfgScale":3.5,
                  "resources":[

                  ],
                  "Model hash":"639d0db70f",
                  "Hires upscale":"1.55",
                  "Hires upscaler":"Latent (nearest-exact)",
                  "negativePrompt":"costume variations, outfit variations, sci-fi, tight clothes, skin tight, muscles., cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry,bad anatomy , liquid body, malformed, mutated, bad proportions, uncoordinated body, unnatural body, disfigured, ugly, gross proportions ,mutation, disfigured, deformed, (mutation), (poorly drawn), wet, legs feet, cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands,",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/dd2d972b-42d4-45d2-9be5-ce4baf407700/width=450/95911.jpeg",
                "nsfw":false,
                "width":792,
                "height":792,
                "hash":"U7DI:yoe~V%L^*jsRkof9Zay9ZWC-oofM{WB",
                "meta":{
                  "ENSD":"31337",
                  "Size":"512x512",
                  "seed":3743692480,
                  "Score":"6.4",
                  "steps":30,
                  "prompt":"21CharTurnerV2 character turnaround of Native american man in a business suit, full body, standing, same outfit",
                  "sampler":"DDIM",
                  "Eta DDIM":"0.16",
                  "cfgScale":6.5,
                  "resources":[

                  ],
                  "Model hash":"88ecb78256",
                  "Hires upscale":"1.55",
                  "Hires upscaler":"Latent (nearest-exact)",
                  "negativePrompt":"child, costume variations, outfit variations, sci-fi, tight clothes, skin tight, muscles., cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry,bad anatomy , liquid body, malformed, mutated, bad proportions, uncoordinated body, unnatural body, disfigured, ugly, gross proportions ,mutation, disfigured, deformed, (mutation), (poorly drawn), wet, legs feet, cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands,, bad_prompt_version2, DreamArtistBADHAND-neg, NG_DeepNegative_V1_75T, Unspeakable-Horrors-Composition-4v",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/04bab185-a5f6-447a-870c-2fd1b1fc9c00/width=450/95910.jpeg",
                "nsfw":false,
                "width":792,
                "height":792,
                "hash":"UAG8.ZoL00E1%0oMV@M|8{xt?axt~pj[xtxu",
                "meta":{
                  "ENSD":"31337",
                  "Size":"512x512",
                  "seed":789330043,
                  "Score":"4.82",
                  "steps":30,
                  "prompt":"21CharTurnerV2 character turnaround of Native american man in a business suit, full body, standing, same outfit",
                  "sampler":"DDIM",
                  "Eta DDIM":"0.16",
                  "cfgScale":6.5,
                  "resources":[

                  ],
                  "Model hash":"5f8c744ab3",
                  "Hires upscale":"1.55",
                  "Hires upscaler":"Latent (nearest-exact)",
                  "negativePrompt":"child, costume variations, outfit variations, sci-fi, tight clothes, skin tight, muscles., cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry,bad anatomy , liquid body, malformed, mutated, bad proportions, uncoordinated body, unnatural body, disfigured, ugly, gross proportions ,mutation, disfigured, deformed, (mutation), (poorly drawn), wet, legs feet, cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands,",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/c8ae65bb-2616-4774-ce6b-4527f20b1b00/width=450/95909.jpeg",
                "nsfw":false,
                "width":1184,
                "height":792,
                "hash":"UNIE@Nt7%MoftSofofay~pogM{oz_3kCRjof",
                "meta":{
                  "ENSD":"31337",
                  "Size":"768x512",
                  "seed":2930407238,
                  "Score":"4.54",
                  "steps":30,
                  "prompt":"21CharTurnerV2 (character turnaround:1) of a mailman. Male, dark hair, tattoos, blue uniform. multiple views of the same character, Highly detailed,, classicnegative",
                  "sampler":"DDIM",
                  "Eta DDIM":"0.16",
                  "cfgScale":13,
                  "resources":[

                  ],
                  "Model hash":"2c29f8668c",
                  "Hires upscale":"1.55",
                  "Hires upscaler":"Latent (nearest-exact)",
                  "negativePrompt":"costume variations, outfit variations, sci-fi, tight clothes, skin tight, muscles., cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry,bad anatomy , liquid body, malformed, mutated, bad proportions, uncoordinated body, unnatural body, disfigured, ugly, gross proportions ,mutation, disfigured, deformed, (mutation), (poorly drawn), wet, legs feet, cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands,",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/d91b46e7-7d69-43db-239d-412bdd8ed400/width=450/95908.jpeg",
                "nsfw":false,
                "width":792,
                "height":792,
                "hash":"UGF6CBnNI9xB~WxDs:RPVtaJofRQ00bwj@ad",
                "meta":{
                  "ENSD":"31337",
                  "Size":"512x512",
                  "seed":2355045759,
                  "Score":"5.88",
                  "steps":30,
                  "prompt":"21CharTurnerV2 character turnaround of young boy as a paperboy, cute adorable little kid, full body, standing, same outfit",
                  "sampler":"DDIM",
                  "Eta DDIM":"0.16",
                  "cfgScale":6.5,
                  "resources":[

                  ],
                  "Model hash":"5f8c744ab3",
                  "Hires upscale":"1.55",
                  "Hires upscaler":"Latent (nearest-exact)",
                  "negativePrompt":"costume variations, outfit variations, sci-fi, tight clothes, skin tight, muscles., cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry,bad anatomy , liquid body, malformed, mutated, bad proportions, uncoordinated body, unnatural body, disfigured, ugly, gross proportions ,mutation, disfigured, deformed, (mutation), (poorly drawn), wet, legs feet, cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands,",
                  "Denoising strength":"0.7"
                }
              }
            ],
            "downloadUrl":"https://civitai.com/api/download/models/9857"
          },
          {
            "id":8387,
            "modelId":3036,
            "name":"CharTurner V2 - For 1.5",
            "createdAt":"2023-02-07T03:46:57.500Z",
            "updatedAt":"2023-03-15T18:58:13.476Z",
            "trainedWords":[
              "charturnerv2"
            ],
            "baseModel":"SD 1.5",
            "earlyAccessTimeFrame":0,
            "description":"<p>2.1 and LoRa versions coming soon.</p><p><strong>Prompt hints</strong>: format something like this: \"A character turnaround of a (X) wearing (Y). \" In some of the prompts the token is spelled differently: due to some technical issues with xformers, I trained this badboy about 40 times, and some of the examples are from those trainings. All the same dataset, I promise.  Just change any weird token names to CharTurnerV2 if you use them.</p><p><strong>Token - \"CharTurnerV2\"</strong> place at the front for stronger effect, place at the end for a weaker effect. Token weighting works too</p><p><strong>Add</strong>:</p><ul><li><p>\"Multiple views of the same character in the same outfit\"</p></li><li><p>Add original CharTurner to mix back in some anime/turns</p></li><li><p>Add charTurner Lora (uploading soon) on top (at very low strength, like .3) to really force the turn. Will affect style.</p></li></ul><p>Next Version: (after the v2 lora and 2.1 versions): Looking for more variety for the data set! Post a review or comment with your best turn around (especially if it was a hard one to get it to do!) and I will use it in the V3 dataset.  </p>",
            "stats":{
              "downloadCount":17908,
              "ratingCount":27,
              "rating":4.7
            },
            "files":[
              {
                "name":"charturnerv2.pt",
                "id":8384,
                "sizeKB":45.92578125,
                "type":"Model",
                "metadata":{
                  "fp":"fp16",
                  "size":"full",
                  "format":"PickleTensor"
                },
                "pickleScanResult":"Success",
                "pickleScanMessage":"No Pickle imports",
                "virusScanResult":"Success",
                "scannedAt":"2023-02-07T17:05:48.272Z",
                "hashes":{
                  "AutoV2":"A91B570185",
                  "SHA256":"A91B570185766FF71F242F83D5BEB6D658348900EDB706A2092BA23D6E1E2CF8",
                  "CRC32":"F874123A",
                  "BLAKE3":"29322FB6F5E7C19E49F8C1CFEFE0C638BD47CF6BCE0778A7202F175816B4D26C"
                },
                "downloadUrl":"https://civitai.com/api/download/models/8387",
                "primary":true
              }
            ],
            "images":[
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/6b404ab7-c1f1-4c56-8df6-3a5871faa100/width=450/79565.jpeg",
                "nsfw":false,
                "width":2026,
                "height":2714,
                "hash":"U9D+h~I;R+oeOUEMxa-V00~VNHE200IAkCoz",
                "meta":null
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/b1a654d8-0ece-4488-1689-1dbf33b3b200/width=450/79564.jpeg",
                "nsfw":false,
                "width":2178,
                "height":2506,
                "hash":"U797Lo~VM{WX004:t7oe^+%MWBWCWBaxayj]",
                "meta":null
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/f21f7b7e-7431-484e-5079-4f1c6501f000/width=450/79563.jpeg",
                "nsfw":false,
                "width":2472,
                "height":2711,
                "hash":"U6CF#COsK5Sd01w]M|jF00xY-Sso~pEht5bH",
                "meta":null
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/ad240caa-1c18-40d9-de17-2569775d8b00/width=450/79562.jpeg",
                "nsfw":false,
                "width":2201,
                "height":2047,
                "hash":"U4DIg?hyTKy?00TJVsvf00.8ofEL%fnit7kC",
                "meta":null
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/035cbefd-7770-424a-4a63-0ffb18dae200/width=450/79561.jpeg",
                "nsfw":false,
                "width":1772,
                "height":2047,
                "hash":"U7Bf;FxaIo%M00ayt7M{xuRjofof~qt8NGof",
                "meta":null
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/1a9a83c6-faba-472e-77bf-c6d2f81da700/width=450/79560.jpeg",
                "nsfw":false,
                "width":768,
                "height":536,
                "hash":"U5H-_a~pE1WW00%LofR*kXD*t7t700D%bHof",
                "meta":{
                  "ENSD":"31337",
                  "Size":"640x448",
                  "seed":1133046487,
                  "Score":"5.4",
                  "steps":20,
                  "prompt":"photographic full body character turnaround of beautiful curvy redhead (Hildai17:0.8) (wearing a long white sundress:1.2). Multiple views of the same character in the same outfit. Photorealistic, subsurface scattering, photo real, 8k, hyperreal  <lora:mw_charturn3:.4> (15Charturn_longCap_D:.3)",
                  "sampler":"DDIM",
                  "Eta DDIM":"0.16",
                  "cfgScale":4,
                  "Clip skip":"2",
                  "resources":[
                    {
                      "name":"mw_charturn3",
                      "type":"lora",
                      "weight":0.4
                    }
                  ],
                  "Model hash":"777f034bc3",
                  "Hires upscale":"1.2",
                  "Hires upscaler":"Latent (nearest-exact)",
                  "negativePrompt":"naked, nude, boobs, nsfw, nipples, bad_prompt_version2, (((deformed))), blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, (extra_limb), (ugly), (poorly drawn hands), fused fingers, messy drawing, broken legs censor, censored, censor_bar, multiple breasts, (mutated hands and fingers:1.5), (long body :1.3), (mutation, poorly drawn :1.2), black-white, bad anatomy, liquid body, liquid tongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy, bad proportions, bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, missing breasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf, disappearing legs, fusedears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, fused animal ears, bad animal ears, poorly drawn animal ears, extra animal ears, liquid animal ears, heavy animal ears, missing animal ears, text, ui, error, missing fingers, missing limb, fused fingers, one hand with more than 5 fingers, one hand with less than 5 fingers, one hand with more than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, fused digit, missing digit, bad digit, liquid digit, colorful tongue, blacktongue, cropped, watermark, username, blurry, JPEG artifacts, signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, extra feet, bad feet, poorly drawn feet, fused feet, missing feet, extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, big face, long face, badeyes, fused eyes poorly drawn eyes, extra eyes, malformed limbs, more than 2 nipples, missing nipples, different nipples, fused nipples, bad nipples, poorly drawnnipples, black nipples, colorful nipples, gross proportions. short arm, (((missing arms))), missing thighs, missing calf, missing legs, mutation, duplicate, morbid, mutilated, poorly drawn hands, more than 1 left hand, more than 1 right hand, deformed, (blurry), disfigured, missing legs, extra arms, extra thighs, more than 2 thighs, extra calf,fused calf, extra legs, bad knee, extra knee, more than 2 legs, bad tails, bad mouth, fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, too long tongue, black tongue, big mouth, cracked mouth, bad mouth, dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, fused cloth, poorly drawn cloth, badpantie, yellow teeth, thick lips, bad camel toe, colorful camel toe, bad asshole, poorly drawn asshole, fused asshole, missing asshole, bad anus, bad pussy, bad crotch, bad crotch seam, fused anus, fused pussy, fused anus, fused crotch, poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, poorly drawn crotch, poorly drawn crotch seam, bad thigh gap, missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh gap, poorly drawn anus, bad collarbone, fused collarbone, missing collarbone, liquid collarbone, strong girl, obesity, worst quality, low quality, normal quality, liquid tentacles, bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, missing clit, bad clit, fused clit, colorful clit, black clit, liquid clit, QR code, bar code, censored, safety panties, safety knickers, beard, furry, pony, pubic hair, mosaic, futa, testis, (((deformed))), blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, (extra_limb), (ugly), (poorly drawn hands), fused fingers, messy drawing, broken legs censor, censored, censor_bar, multiple breasts, (mutated hands and fingers:1.5), (long body :1.3), (mutation, poorly drawn :1.2), black-white, bad anatomy, liquid body, liquid tongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy, bad proportions, bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, missing breasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf, disappearing legs, fusedears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, fused animal ears, bad animal ears, poorly drawn animal ears, extra animal ears, liquid animal ears, heavy animal ears, missing animal ears, text, ui, error, missing fingers, missing limb, fused fingers, one hand with more than 5 fingers, one hand with less than 5 fingers, one hand with more than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, fused digit, missing digit, bad digit, liquid digit, colorful tongue, blacktongue, cropped, watermark, username, blurry, JPEG artifacts, signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, extra feet, bad feet, poorly drawn feet, fused feet, missing feet, extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, big face, long face, badeyes, fused eyes poorly drawn eyes, extra eyes, malformed limbs, more than 2 nipples, missing nipples, different nipples, fused nipples, bad nipples, poorly drawnnipples, black nipples, colorful nipples, gross proportions. short arm, (((missing arms))), missing thighs, missing calf, missing legs, mutation, duplicate, morbid, mutilated, poorly drawn hands, more than 1 left hand, more than 1 right hand, deformed, (blurry), disfigured, missing legs, extra arms, extra thighs, more than 2 thighs, extra calf,fused calf, extra legs, bad knee, extra knee, more than 2 legs, bad tails, bad mouth, fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, too long tongue, black tongue, big mouth, cracked mouth, bad mouth, dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, fused cloth, poorly drawn cloth, badpantie, yellow teeth, thick lips, bad camel toe, colorful camel toe, bad asshole, poorly drawn asshole, fused asshole, missing asshole, bad anus, bad pussy, bad crotch, bad crotch seam, fused anus, fused pussy, fused anus, fused crotch, poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, poorly drawn crotch, poorly drawn crotch seam, bad thigh gap, missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh gap, poorly drawn anus, bad collarbone, fused collarbone, missing collarbone, liquid collarbone, worst quality, low quality, normal quality, liquid tentacles, bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, missing clit, bad clit, fused clit, colorful clit, black clit, liquid clit, QR code, bar code, censored, safety panties, safety knickers, beard, mosaic, futa, testis",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/0b0550e6-1034-4b5b-63c7-e545545cfb00/width=450/79559.jpeg",
                "nsfw":false,
                "width":816,
                "height":816,
                "hash":"U5F;TjT1s.}q19bvoejF^QxDR*I=ZLenaeNw",
                "meta":{
                  "ENSD":"31337",
                  "Size":"512x512",
                  "seed":1280899878,
                  "Score":"6.29",
                  "steps":30,
                  "prompt":"<lora:mw_charturn3:.1> (15Charturn_longCap_D:.4)  a character turnaround young male cyberpunk netrunner, (high detailed skin:1.2),  RAW photo. Human, cybernetic hands,  (Multiple views of the same character:1.2) (on the same background:1.1) , modelshoot style, nousr robot",
                  "sampler":"DDIM",
                  "Eta DDIM":"0.16",
                  "cfgScale":5.5,
                  "Clip skip":"2",
                  "resources":[
                    {
                      "name":"mw_charturn3",
                      "type":"lora",
                      "weight":0.1
                    }
                  ],
                  "Model hash":"847da9eead",
                  "Hires upscale":"1.6",
                  "Hires upscaler":"Latent (nearest-exact)",
                  "negativePrompt":"(naked:1), (military:1.2),",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/d102e6a2-3f44-49ea-33ab-47633f090c00/width=450/79558.jpeg",
                "nsfw":false,
                "width":816,
                "height":608,
                "hash":"ULI50xs.%MIU~qt7ofWCMxofR*t7D%WCaxof",
                "meta":{
                  "ENSD":"31337",
                  "Size":"512x384",
                  "seed":254644189,
                  "Score":"6.36",
                  "steps":30,
                  "prompt":"(15Charturn_longCap_D:1)  a character turnaround of 30 y.o woman, red hair, short haircut, pale skin, (high detailed skin:1.2),  RAW photo.  (Multiple views of the same character:1.2) (on the same background:1.1), modelshoot style, nousr robot",
                  "sampler":"DDIM",
                  "Eta DDIM":"0.16",
                  "cfgScale":5.5,
                  "Clip skip":"2",
                  "resources":[

                  ],
                  "Model hash":"847da9eead",
                  "Hires upscale":"1.6",
                  "Hires upscaler":"Latent (nearest-exact)",
                  "negativePrompt":"(naked:1), (military:1.2), (deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime:1.4), text, close up, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/aff87e58-f731-42dc-7838-cc811e7e4700/width=450/79557.jpeg",
                "nsfw":false,
                "width":944,
                "height":824,
                "hash":"U9Kw|Mae4n4o4no0t7Rj~qjt%M-;?bNGt7xu",
                "meta":{
                  "ENSD":"31337",
                  "Size":"512x448",
                  "seed":2719393072,
                  "Score":"6.17",
                  "steps":30,
                  "prompt":"(15Charturn_longCap_D:1) a character turnaround of A rat. Subsurface scattering, rimlight, (charturner:1). art by smoose2. Multiple views of the same character in the same outfit.   , ANALOG STYLE, MODELSHOOT STYLE, NSFW, NUDITY",
                  "sampler":"DDIM",
                  "Eta DDIM":"0.16",
                  "cfgScale":8.5,
                  "Clip skip":"2",
                  "resources":[

                  ],
                  "Model hash":"c35782bad8",
                  "Hires upscale":"1.85",
                  "Hires upscaler":"Latent (nearest-exact)",
                  "negativePrompt":"naked, nude, boobs, nsfw, nipples",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/f8ff5342-06a4-4a72-aa5f-11762c417a00/width=450/79556.jpeg",
                "nsfw":false,
                "width":944,
                "height":944,
                "hash":"UEG[+o$*aet6D%RkjsoL~pxut7R*Rjayayj[",
                "meta":{
                  "ENSD":"31337",
                  "Size":"512x512",
                  "seed":3400864224,
                  "Score":"5.87",
                  "steps":30,
                  "prompt":"(15Charturn_longCap_D:1) a facial character turnaround of A (rat:1.3). fursona  Subsurface scattering, rimlight, (charturner:1). Covered with fur. Dark fur, art by smoose2. Multiple views of the same character in the same outfit.   , ANALOG STYLE, MODELSHOOT STYLE, NSFW, NUDITY",
                  "sampler":"DDIM",
                  "Eta DDIM":"0.16",
                  "cfgScale":8.5,
                  "Clip skip":"2",
                  "resources":[

                  ],
                  "Model hash":"c35782bad8",
                  "Hires upscale":"1.85",
                  "Hires upscaler":"Latent (nearest-exact)",
                  "negativePrompt":"hoodie, human, military, armor, boots, (naked:1.6), nude, boobs, nsfw, nipples",
                  "Denoising strength":"0.7"
                }
              }
            ],
            "downloadUrl":"https://civitai.com/api/download/models/8387"
          },
          {
            "id":3334,
            "modelId":3036,
            "name":"CharTurner V1 - For 1.5",
            "createdAt":"2022-12-28T23:21:25.362Z",
            "updatedAt":"2023-03-15T18:58:13.476Z",
            "trainedWords":[
              "charturner"
            ],
            "baseModel":"SD 1.5",
            "earlyAccessTimeFrame":0,
            "description":"<p>First version. Still has things I'm working on fixing. Adding \"multiple views of the same character\" can help if your character is being stubborn. </p>",
            "stats":{
              "downloadCount":12424,
              "ratingCount":23,
              "rating":4.65
            },
            "files":[
              {
                "name":"charturner.pt",
                "id":3231,
                "sizeKB":12.9169921875,
                "type":"Model",
                "metadata":{
                  "fp":"fp16",
                  "size":"full",
                  "format":"PickleTensor"
                },
                "pickleScanResult":"Success",
                "pickleScanMessage":"**Detected Pickle imports (3)**\n```\ncollections.OrderedDict\ntorch.FloatStorage\ntorch._utils._rebuild_tensor_v2\n```",
                "virusScanResult":"Success",
                "scannedAt":"2022-12-28T23:28:40.051Z",
                "hashes":{
                  "AutoV2":"733E24A8F4",
                  "SHA256":"733E24A8F4F9741DF4C936380BE9F25DF2F79FACD23AB956E03F9D9F75872DFD",
                  "CRC32":"45B06535",
                  "BLAKE3":"E89566CFC12D5596C9F373838C58778DE9833AED6B23348FCA0EAEEBC18ACE32"
                },
                "downloadUrl":"https://civitai.com/api/download/models/3334",
                "primary":true
              }
            ],
            "images":[
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/1ade236c-eabe-4e9e-9719-37adaf55c300/width=450/22507.jpeg",
                "nsfw":false,
                "width":768,
                "height":768,
                "hash":"U8GRSVXmPU$*00n%IoI:BTxGn4Io?^ozxaso",
                "meta":{
                  "Size":"768x768",
                  "seed":3644685645,
                  "steps":30,
                  "prompt":"highly detailed Full body charturner of a postman. multiple views of the same character.  . Subsurface scattering, rimlight,, art by smoose2",
                  "sampler":"DPM++ 2M Karras",
                  "cfgScale":8.5,
                  "Model hash":"993f52a4",
                  "negativePrompt":"woman, girl, toy, Deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, blurry, floating limbs, disconnected limbs, malformed hands, blur, out of focus, long neck, long body, ((((mutated hands and fingers)))), (((out of frame))), cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands",
                  "First pass size":"512x512",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/0cd2ed10-3582-40e5-8b4f-0612f6841400/width=450/22516.jpeg",
                "nsfw":false,
                "width":768,
                "height":768,
                "hash":"UNIX~zofRj?bxbofayay~qoetRV@%gaeofof",
                "meta":{
                  "Size":"768x768",
                  "seed":355585046,
                  "steps":30,
                  "prompt":"highly detailed Full body of character turnaround of a mailman. multiple views of the same character.  . Subsurface scattering, rimlight, charturner, art by smoose2",
                  "sampler":"DPM++ 2M Karras",
                  "cfgScale":8.5,
                  "Model hash":"993f52a4",
                  "negativePrompt":"orange, woman, girl, toy, Deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, blurry, floating limbs, disconnected limbs, malformed hands, blur, out of focus, long neck, long body, ((((mutated hands and fingers)))), (((out of frame))), cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands",
                  "First pass size":"512x512",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/1aa3e6e1-316f-4da7-3d9c-1f5934d11900/width=450/22515.jpeg",
                "nsfw":false,
                "width":896,
                "height":576,
                "hash":"UBGbYZ-pbIIowJWBR+t6~qoft7aeW=j[V@jY",
                "meta":{
                  "Size":"896x576",
                  "seed":2294001164,
                  "steps":30,
                  "prompt":"a 2d character turnaround of A rat.  Subsurface scattering, rimlight, (charturner:1)., art by smoose2",
                  "sampler":"DPM++ 2M Karras",
                  "cfgScale":10.5,
                  "Model hash":"993f52a4",
                  "negativePrompt":"toy, Deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, blurry, floating limbs, disconnected limbs, malformed hands, blur, out of focus, long neck, long body, ((((mutated hands and fingers)))), (((out of frame))), cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands",
                  "First pass size":"512x320",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/b76df236-a854-434e-d78e-e876ca2a0900/width=450/22514.jpeg",
                "nsfw":false,
                "width":896,
                "height":576,
                "hash":"U8GbSK^+00IA00kB-;?b~WITxvMy00RkRPe-",
                "meta":{
                  "Size":"896x576",
                  "seed":2294001167,
                  "steps":30,
                  "prompt":"a 2d character turnaround of A rat.  Subsurface scattering, rimlight, (charturner:1)., art by smoose2",
                  "sampler":"DPM++ 2M Karras",
                  "cfgScale":10.5,
                  "Model hash":"993f52a4",
                  "negativePrompt":"toy, Deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, blurry, floating limbs, disconnected limbs, malformed hands, blur, out of focus, long neck, long body, ((((mutated hands and fingers)))), (((out of frame))), cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands",
                  "First pass size":"512x320",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/d4bebcee-7be0-4595-3c98-93eb46460600/width=450/22513.jpeg",
                "nsfw":false,
                "width":896,
                "height":576,
                "hash":"U8Fg@2%2s-s:DlS~NGS2NdR*OER+{dnNofWV",
                "meta":{
                  "Size":"896x576",
                  "seed":2760083340,
                  "steps":30,
                  "prompt":"a character turnaround of a curvy redheaded pinup girl(Hildai17:0.8).  Subsurface scattering, rimlight, (charturner:1)., art by smoose2",
                  "sampler":"DPM++ 2M Karras",
                  "cfgScale":10.5,
                  "Model hash":"993f52a4",
                  "negativePrompt":"toy, Deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, blurry, floating limbs, disconnected limbs, malformed hands, blur, out of focus, long neck, long body, ((((mutated hands and fingers)))), (((out of frame))), cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands",
                  "First pass size":"512x320",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/fcfed606-93b1-4d8c-451c-b2a378d70500/width=450/22512.jpeg",
                "nsfw":false,
                "width":1024,
                "height":768,
                "hash":"UKGuq9$%Mxxt?Hs:t7j[_NWqt8f+RkWBRjae",
                "meta":{
                  "Size":"1024x768",
                  "seed":2094869509,
                  "steps":30,
                  "prompt":"highly detailed Full body Character turnaround of a evil badger mage. front, side, back,  multiple views of the same character.  charturner. Subsurface scattering, rimlight, pouches and herbs. Highly detailed soft clumpy fur, art by smoose2",
                  "sampler":"DPM++ 2M Karras",
                  "cfgScale":15.5,
                  "Model hash":"993f52a4",
                  "negativePrompt":"toy, Deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, blurry, floating limbs, disconnected limbs, malformed hands, blur, out of focus, long neck, long body, ((((mutated hands and fingers)))), (((out of frame))), cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands",
                  "First pass size":"576x448",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/3e1128ee-1d06-4923-5ffb-ee989762ad00/width=450/22511.jpeg",
                "nsfw":false,
                "width":1024,
                "height":768,
                "hash":"UEE:0poz%gaKaKWVWBn%~qt7WBoLazRPRjV@",
                "meta":{
                  "Size":"1024x768",
                  "seed":767967615,
                  "steps":30,
                  "prompt":"highly detailed Full body Character turnaround of a male ninja. front, side, back,  multiple views of the same character.  charturner. Subsurface scattering, rimlight,, art by smoose2",
                  "sampler":"DPM++ 2M Karras",
                  "cfgScale":7.5,
                  "Model hash":"993f52a4",
                  "negativePrompt":"woman, girl, toy, Deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, blurry, floating limbs, disconnected limbs, malformed hands, blur, out of focus, long neck, long body, ((((mutated hands and fingers)))), (((out of frame))), cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands",
                  "First pass size":"576x448",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/badde49e-83e2-4a5d-bb68-b19847242e00/width=450/22510.jpeg",
                "nsfw":false,
                "width":1024,
                "height":768,
                "hash":"UAD]PV%gsp?v~qn$R*Rj?vn$W;V@%MR*n%j[",
                "meta":{
                  "Size":"1024x768",
                  "seed":555145518,
                  "steps":30,
                  "prompt":"Full body Character turnaround of a evil badger mage. front, side, back,  multiple views of the same character.  charturner, art by smoose2",
                  "sampler":"DPM++ 2M Karras",
                  "cfgScale":10,
                  "Model hash":"993f52a4",
                  "negativePrompt":"toy, Deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, blurry, floating limbs, disconnected limbs, malformed hands, blur, out of focus, long neck, long body, ((((mutated hands and fingers)))), (((out of frame))), cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands",
                  "First pass size":"576x448",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/e64532fb-142f-4a56-1d87-56efdec04800/width=450/22509.jpeg",
                "nsfw":false,
                "width":768,
                "height":768,
                "hash":"U8G+tBRjx]0000ozR*%M~qo#Rj%g%hM{RPxv",
                "meta":{
                  "Size":"768x768",
                  "seed":2373222042,
                  "steps":30,
                  "prompt":"highly detailed Full body of character turnaround of a robot paper boy. multiple views of the same character in the same outfit. Subsurface scattering, rimlight, charturner, art by smoose2",
                  "sampler":"DPM++ 2M Karras",
                  "cfgScale":8.5,
                  "Model hash":"993f52a4",
                  "negativePrompt":"orange, woman, girl, toy, Deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, blurry, floating limbs, disconnected limbs, malformed hands, blur, out of focus, long neck, long body, ((((mutated hands and fingers)))), (((out of frame))), cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands",
                  "First pass size":"512x512",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/a8d05704-751f-4d8e-ab4b-3be5b50c5400/width=450/22508.jpeg",
                "nsfw":false,
                "width":896,
                "height":576,
                "hash":"UBHL3poM9Fiv~VWXNGt7SKV@WBof$$j?V@nO",
                "meta":{
                  "Size":"896x576",
                  "seed":2936119404,
                  "steps":30,
                  "prompt":"Full body of character turnaround of a (kitten animal :1.1). highly detailed  front, back, side, 3/4 (multiple views:1.1) of the (same character :1.1)in the same outfit. Subsurface scattering, rimlight, (charturner:1.3)., art by smoose2",
                  "sampler":"DPM++ 2M Karras",
                  "cfgScale":10.5,
                  "Model hash":"993f52a4",
                  "negativePrompt":"humanoid, woman, girl, toy, Deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, blurry, floating limbs, disconnected limbs, malformed hands, blur, out of focus, long neck, long body, ((((mutated hands and fingers)))), (((out of frame))), cartoon, 3d, (disfigured), (bad art), (deformed), (poorly drawn), (extra limbs), strange colours, blurry, boring, sketch, lacklustre, repetitive, cropped, hands",
                  "First pass size":"512x320",
                  "Denoising strength":"0.7"
                }
              }
            ],
            "downloadUrl":"https://civitai.com/api/download/models/3334"
          }
        ]
      },
      {
        "id":4514,
        "name":"Pure Eros Face",
        "description":"<p>This embedding will generate <strong>good-looking girl faces</strong>, close concept of <strong><u>kpop idols or Instagram girls</u></strong>. For <strong>SD1.5</strong> based models.</p><p></p><p><em>what means \"Pure Eros\"?</em></p><p><em>&gt; Pure Eros is a simple translation of the Chinese word \"</em><strong><em>纯欲</em></strong><em>\", which is a popular memes in the Chinese internet, the english words close to the semantics of this word are \"ulzzang face\", \"korean idol face\", so obviously this embedding will be close to the Asian aesthetic.🤗</em></p><p></p><p><strong>Recommended config:</strong></p><p>1. prompt</p><ul><li><p><strong>[:(detailed face:1.2):0.2]</strong>: When drawing high-quality faces, do not use the \"detail face\" tag at 0 steps, otherwise it may lead to deviation from the original semantics of embedding</p></li><li><p><strong>shiny eyes, looking at viewer</strong>: If your generated faces often close their eyes, adding \"shiny eyes, looking at viewer\" will open them instantly</p></li></ul><p>2. negative prompt:</p><ul><li><p><strong>long hair</strong>: add it to fix some errors caused by training data bias...(<em>although it does not always affect the output, my experiments found that it seems that the length of the hair in a certain scene will affect the quality of the clothes. In short, the relationship is very subtle, you can try to control the length of the hair to change the outfit quality)</em></p></li><li><p><strong>full body</strong>: Most of the data set is close-up, so it doesn't perform well on the \"full body\" scene, <em>I'm trying to fix it in the next version</em></p></li><li><p><strong>disabled body</strong>: If a deformed body structure is produced, please add it</p></li><li><p><strong>DeepNegative</strong>: A negative embedding I released can be used with PureErosFace very well, it is recommended to try</p><p><a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/4629/deep-negative-v1x\">https://civitai.com/models/4629/deep-negative-v1x</a></p></li></ul><p></p><p></p><p><strong>Recommended model:</strong></p><p>It is best to use a model with a realistic style. If it is an anime-style model, it may output a mask-like face.</p><p></p><p><strong>1. LOFI</strong></p><p>merged model I released, works fine with this embedding</p><p><a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/9052/lofi\">https://civitai.com/models/9052/lofi</a></p><img src=\"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/8e1c68da-4e15-49bf-0090-25a89a438800/width=525\" /><p></p><p>examples <a target=\"_blank\" rel=\"ugc\" href=\"https://imgur.com/a/nFRE1Z4.jpg\">https://imgur.com/a/nFRE1Z4.jpg</a></p><img src=\"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/29349082-39d2-45bf-4221-b49134ba3000/width=525\" /><p></p><p>2. <strong>izumi</strong></p><p>Most of my example images are generated by izumi:</p><p><a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/1364/izumi\">https://civitai.com/models/1364/izumi</a></p><p></p><p>examples and test: <a target=\"_blank\" rel=\"ugc\" href=\"https://imgur.com/ZirqVWK.jpg\">https://imgur.com/ZirqVWK.jpg</a></p><img src=\"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/9c53760b-fce1-4c3a-0339-d7f393e0d800/width=525\" /><p></p><p>3. <strong>F222</strong></p><p>Also produced a good-looking face, although I only experimented with a few, but they all look good for work</p><p><a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/1188/f222\">https://civitai.com/models/1188/f222</a></p><p></p><p>examples and test: <a target=\"_blank\" rel=\"ugc\" href=\"https://imgur.com/ixyVXTP.jpg\">https://imgur.com/ixyVXTP.jpg</a></p><img src=\"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/711d2fde-6c76-4702-b392-23f79d1ebe00/width=525\" /><p></p><p>4. <strong>HassanBlend</strong></p><p><a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/1173/hassanblend-1512-and-previous-versions\">https://civitai.com/models/1173/hassanblend-1512-and-previous-versions</a></p><p></p><p>examples and test: <a target=\"_blank\" rel=\"ugc\" href=\"https://imgur.com/no066sF.jpg\">https://imgur.com/no066sF.jpg</a></p><img src=\"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/885d0191-ba9f-4001-7693-6e56ff3adc00/width=525\" /><p></p><p><strong>my discord server, find me here:</strong></p><p><a target=\"_blank\" rel=\"ugc\" href=\"https://discord.gg/v5HFg47J6U\"><strong>https://discord.gg/v5HFg47J6U</strong></a></p><p><strong>-</strong></p>",
        "type":"TextualInversion",
        "poi":false,
        "nsfw":true,
        "allowNoCredit":false,
        "allowCommercialUse":"Rent",
        "allowDerivatives":true,
        "allowDifferentLicense":false,
        "stats":{
          "downloadCount":66498,
          "favoriteCount":8427,
          "commentCount":38,
          "ratingCount":50,
          "rating":4.9
        },
        "creator":{
          "username":"FapMagi",
          "image":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/625d4b36-c648-4a5d-5282-f35fe7cdd100/width=96/FapMagi.jpeg"
        },
        "tags":[
          "girl",
          "person",
          "photorealistic",
          "textual inversion",
          "beauties",
          "asian",
          "kpop",
          "woman",
          "faces",
          "girls",
          "photography",
          "portraits",
          "realistic"
        ],
        "modelVersions":[
          {
            "id":5119,
            "modelId":4514,
            "name":"PureErosFace_v1",
            "createdAt":"2023-01-14T12:01:59.609Z",
            "updatedAt":"2023-02-24T03:35:55.300Z",
            "trainedWords":[
              "pureerosface_v1"
            ],
            "baseModel":"SD 1.5",
            "earlyAccessTimeFrame":0,
            "description":"<p>Training Config:</p><p>initialization text: ulzzang face,kpop idol</p><p>number of vectors per token: 1</p><p>lr: 0.05:10, 0.02:20, 0.01:60, 0.005:200, 0.002:500, 0.001:3000, 0.0005</p><p>(Here is not the complete lr formula, because I manually selected several iterations as branches during training, but I did not record it completely...here is just a part)</p><p>batch size: 10</p><p>images: 100+ images (close-up portrait girl face)</p><p>size: 512x512</p><p>steps: 1000</p>",
            "stats":{
              "downloadCount":66504,
              "ratingCount":50,
              "rating":4.9
            },
            "files":[
              {
                "name":"pureerosface_v1.pt",
                "id":5162,
                "sizeKB":3.9169921875,
                "type":"Model",
                "metadata":{
                  "fp":"fp16",
                  "size":"full",
                  "format":"PickleTensor"
                },
                "pickleScanResult":"Success",
                "pickleScanMessage":"**Detected Pickle imports (3)**\n```\ntorch.FloatStorage\ntorch._utils._rebuild_tensor_v2\ncollections.OrderedDict\n```",
                "virusScanResult":"Success",
                "scannedAt":"2023-01-14T12:09:02.454Z",
                "hashes":{
                  "AutoV2":"DEDB4322E4",
                  "SHA256":"DEDB4322E42E360FE01775BA817BE03AC6A6C307744562BB0D6759368BC681DA",
                  "CRC32":"8E3194F8",
                  "BLAKE3":"7F529ED966666F01C58DE4576421C8A2FB438F82043CEBABD976CF8ECF4D308A"
                },
                "downloadUrl":"https://civitai.com/api/download/models/5119",
                "primary":true
              }
            ],
            "images":[
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/9fbf8bf0-aad7-4360-eeb0-3e2e09628900/width=450/110973.jpeg",
                "nsfw":true,
                "width":512,
                "height":768,
                "hash":"UIG,eU~qYPAb-VITysoy00IVwJr??a$*IAS$",
                "meta":{
                  "Size":"256x384",
                  "seed":2430721844,
                  "steps":15,
                  "prompt":"symmetrical,High detail RAW color photo professional close photograph,\n[:(highly detail face: 1.2):0.1], (PureErosFace_V1:0.8), twintails, half body, pore, real human skin,\n\na portrait of a 18yo woman bathing in a river,body contact water and ripple around,\nreeds,clear and clean water,\nshiny eyes,looking at viewer,\nwearing tight sports top, wet clothes, see-through clothes, nipples, wet body, wet hair,\n\ntindal effect,lens flare,shade, bloom,\nbacklighting, depth of field, natural lighting, hard focus, film grain, photographed with a Sony a9 II Mirrorless Camera, by Laurence Demaison",
                  "sampler":"Euler a",
                  "cfgScale":7,
                  "resources":[

                  ],
                  "Model hash":"959205938e",
                  "Hires steps":"40",
                  "Hires upscale":"2",
                  "Hires upscaler":"Latent",
                  "negativePrompt":"NG_DeepNegative_V1_75T,\n disabled body,extra head,extra person,duplicate, copy, cropped,\nlowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, crown, hat, chromatic aberration, child",
                  "Denoising strength":"0.7"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/fbd0cb59-8730-4a2f-120f-3a0f06e1e000/width=450/39166.jpeg",
                "nsfw":false,
                "width":512,
                "height":768,
                "hash":"UDJG+t170$~p}]=}0gXUXS#RRQtS0f-p-pNb",
                "meta":{
                  "seed":1689791114,
                  "steps":40,
                  "prompt":"symmetrical,High detail RAW color photo professional close photograph,\n[:(highly detail face: 1.2):0.1], PureErosFace_V1, twintails，\n\na portrait of a 18yo woman bathing in a river,body contact water and ripple around,\nreeds,clear and clean water,\nshiny eyes,looking at viewer,\nwearing tight sports top, wet clothes, see-through clothes, nipples, wet body, wet hair,\n\ntindal effect,lens flare,shade, bloom,\nbacklighting, depth of field, natural lighting, hard focus, film grain, photographed with a Sony a9 II Mirrorless Camera, by Laurence Demaison",
                  "sampler":"Euler a",
                  "cfgScale":7,
                  "negativePrompt":" disabled body,extra head,extra person,duplicate, copy, cropped,\nlowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, crown, hat, chromatic aberration, child"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/bde04434-d879-4f9f-63e7-e7f125b63e00/width=450/38248.jpeg",
                "nsfw":false,
                "width":512,
                "height":768,
                "hash":"UOH13|}@D%IU6MFax[X7=exF$g%2t5wdoKof",
                "meta":{
                  "Size":"512x768",
                  "seed":633455752,
                  "steps":40,
                  "prompt":"dark late at night,mid-night,(symmetry:1.1),\n\n(highly detailed face:1.1),PureErosFace_v1,(short hair:1.1), \nclosed up portrait of an elegant girl wearing gorgeous red flower kimono and flower in hair,21yo girl,\n\nnighttown,(fireworks display:1.2),blurry background,\nperspective,(half_body:1.1),\n\nhighly detailed, sharp focus, 8k,natural light,lens 135mm,f1.8,",
                  "sampler":"Euler a",
                  "cfgScale":7,
                  "Model hash":"c785dff0",
                  "negativePrompt":"nsfw,nude,nipples,plant,full_body,bad_prompt_version2,day,sunlight,long hair,\nextra limbs, extra arms, extra hands, extra fingers, extra legs, extra digit, deformed limbs, deformed arms, deformed hands, deformed fingers, deformed legs, deformed digit, malformed limbs, malformed arms, malformed hands, malformed fingers, malformed legs, malformed digit, fused limbs, fused arms, fused hands, fused fingers, fused legs, fused digit, mutated limbs, mutated arms, mutated hands, mutated fingers, mutated legs, mutated digit, mutilated limbs, mutilated arms, mutilated hands, mutilated fingers, mutilated legs, mutilated digit, fewer limbs, fewer arms, fewer hands, fewer fingers, fewer legs, fewer digit, disconnected limbs, disconnected arms, disconnected hands, disconnected fingers, disconnected legs, disconnected digit, missing limbs, missing arms, missing hands, missing fingers, missing legs, missing digit, poorly drawn limbs, poorly drawn arms, poorly drawn hands, poorly drawn fingers, poorly drawn legs, poorly drawn digit,"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/e8409490-308a-4a19-8d6b-e987574e9000/width=450/38241.jpeg",
                "nsfw":true,
                "width":512,
                "height":768,
                "hash":"UIGkI5Os0JE1OTRQ#;xbH?RQ?Ho}~BJ7xGni",
                "meta":{
                  "Size":"512x768",
                  "seed":2082299184,
                  "steps":40,
                  "prompt":"(dark late at night,mid-night:1.1),(symmetry:1.1),\n\n(highly detailed face:1.1),PureErosFace_v1,(short hair:1.1), \nclosed up portrait of an elegant girl wearing gorgeous red flower kimono and flower in hair,21yo girl,\n\n(fireworks background:1.1),blurry background,\nperspective,(half_body:1.1),\n\nhighly detailed, sharp focus, 8k,natural light,lens 135mm,f1.8,",
                  "sampler":"Euler a",
                  "cfgScale":7,
                  "Model hash":"c785dff0",
                  "negativePrompt":"nsfw,nude,nipples,plant,full_body,bad_prompt_version2,day,sunlight,long hair,\nextra limbs, extra arms, extra hands, extra fingers, extra legs, extra digit, deformed limbs, deformed arms, deformed hands, deformed fingers, deformed legs, deformed digit, malformed limbs, malformed arms, malformed hands, malformed fingers, malformed legs, malformed digit, fused limbs, fused arms, fused hands, fused fingers, fused legs, fused digit, mutated limbs, mutated arms, mutated hands, mutated fingers, mutated legs, mutated digit, mutilated limbs, mutilated arms, mutilated hands, mutilated fingers, mutilated legs, mutilated digit, fewer limbs, fewer arms, fewer hands, fewer fingers, fewer legs, fewer digit, disconnected limbs, disconnected arms, disconnected hands, disconnected fingers, disconnected legs, disconnected digit, missing limbs, missing arms, missing hands, missing fingers, missing legs, missing digit, poorly drawn limbs, poorly drawn arms, poorly drawn hands, poorly drawn fingers, poorly drawn legs, poorly drawn digit,"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/48e7d790-4366-41fb-de54-9448c28c1200/width=450/38243.jpeg",
                "nsfw":true,
                "width":512,
                "height":768,
                "hash":"UJJRHg?I9EWX00MyO-M|4-IV%gNG*Ibc$yxa",
                "meta":{
                  "Size":"512x768",
                  "seed":2628228709,
                  "steps":40,
                  "prompt":"(symmetry!:1.2),(half_body:1.1),\n\ntwintails,24yo girl,(short hair:1.1), [:big breasts:0.5],\nPureErosFace_v1, [:(detailed face:1.1):0.1],\nvisible navel,Clearly visible pores, real skin texture,\n(shiny eyes:1.1),(looking at viewer, facing viewer:1.1),\navocado green clothes,exposed half breasts, \ntight [qipao:yoga clothing:0.5],outdoors,\n\ndepth of field,blurry background,natural light,\ntelephoto lens, soft focus, 8k canon RAW, art photography,",
                  "sampler":"Euler a",
                  "cfgScale":7,
                  "Model hash":"c785dff0",
                  "negativePrompt":"nsfw,nude,nipples,plant,full_body,bad_prompt_version2,day,sunlight,long hair,(disabled body:1.1),(closed eyes:1.2), \nmissing hand, missing arms,back to viewer,\nextra limbs, extra arms, extra hands, extra fingers, extra legs, extra digit, deformed limbs, deformed arms, deformed hands, deformed fingers, deformed legs, deformed digit, malformed limbs, malformed arms, malformed hands, malformed fingers, malformed legs, malformed digit, fused limbs, fused arms, fused hands, fused fingers, fused legs, fused digit, mutated limbs, mutated arms, mutated hands, mutated fingers, mutated legs, mutated digit, mutilated limbs, mutilated arms, mutilated hands, mutilated fingers, mutilated legs, mutilated digit, fewer limbs, fewer arms, fewer hands, fewer fingers, fewer legs, fewer digit, disconnected limbs, disconnected arms, disconnected hands, disconnected fingers, disconnected legs, disconnected digit, missing limbs, missing arms, missing hands, missing fingers, missing legs, missing digit, poorly drawn limbs, poorly drawn arms, poorly drawn hands, poorly drawn fingers, poorly drawn legs, poorly drawn digit,child, child like"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/e3c1055a-b9bb-4c57-428f-69206f8a2300/width=450/38247.jpeg",
                "nsfw":false,
                "width":512,
                "height":768,
                "hash":"UOJtYs_35*x]0{XA?I%MtTW@-:ox~qxuRjV@",
                "meta":{
                  "Size":"512x768",
                  "seed":245553777,
                  "steps":50,
                  "prompt":"(symmetry:1.2),(half_body:1.2),(highly detailed face:1.2)\n\nPureErosFace_v1,24yo girl,wearing see-through light_pink tight sports top,\nportrait of face, running motion,\ndusk in middle of a crowd in the street market fair, (at noon),\nd750 hdr color photo by Relja Penezic, rim halo light, soft focus, flare, telephoto lens, kodak portra",
                  "sampler":"Euler a",
                  "cfgScale":7,
                  "Model hash":"c785dff0",
                  "negativePrompt":"(bad_prompt_version2:0.8),\nextra limbs, extra arms, extra hands, extra fingers, extra legs, extra digit, deformed limbs, deformed arms, deformed hands, deformed fingers, deformed legs, deformed digit, malformed limbs, malformed arms, malformed hands, malformed fingers, malformed legs, malformed digit, fused limbs, fused arms, fused hands, fused fingers, fused legs, fused digit, mutated limbs, mutated arms, mutated hands, mutated fingers, mutated legs, mutated digit, mutilated limbs, mutilated arms, mutilated hands, mutilated fingers, mutilated legs, mutilated digit, fewer limbs, fewer arms, fewer hands, fewer fingers, fewer legs, fewer digit, disconnected limbs, disconnected arms, disconnected hands, disconnected fingers, disconnected legs, disconnected digit, missing limbs, missing arms, missing hands, missing fingers, missing legs, missing digit, poorly drawn limbs, poorly drawn arms, poorly drawn hands, poorly drawn fingers, poorly drawn legs, poorly drawn digit,child, child like"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/dec6d254-1f37-4dcd-8f16-353e370f9600/width=450/38244.jpeg",
                "nsfw":false,
                "width":512,
                "height":768,
                "hash":"UYJHR8~pEL_3NHx].8xuD%WBt6RPWBaxt7t7",
                "meta":{
                  "Size":"512x768",
                  "seed":4204041621,
                  "steps":40,
                  "prompt":"(symmetry!:1.2),facing viewer,\n(half_body:1.1),\n\ntwintails,24yo girl,(short hair:1.1), \nPureErosFace_v1, [:(detailed face:1.1):0.3],shiny eyes,looking at viewer, \n(wedding dress,bridal veil|(qipao:1.2)),indoors,\n\ndepth of field,blurry background,\ntelephoto lens, soft focus, 8k canon RAW, art photography,",
                  "sampler":"Euler a",
                  "cfgScale":7,
                  "Model hash":"c785dff0",
                  "negativePrompt":"nsfw,nude,nipples,plant,full_body,bad_prompt_version2,day,sunlight,long hair,disabled body,\nextra limbs, extra arms, extra hands, extra fingers, extra legs, extra digit, deformed limbs, deformed arms, deformed hands, deformed fingers, deformed legs, deformed digit, malformed limbs, malformed arms, malformed hands, malformed fingers, malformed legs, malformed digit, fused limbs, fused arms, fused hands, fused fingers, fused legs, fused digit, mutated limbs, mutated arms, mutated hands, mutated fingers, mutated legs, mutated digit, mutilated limbs, mutilated arms, mutilated hands, mutilated fingers, mutilated legs, mutilated digit, fewer limbs, fewer arms, fewer hands, fewer fingers, fewer legs, fewer digit, disconnected limbs, disconnected arms, disconnected hands, disconnected fingers, disconnected legs, disconnected digit, missing limbs, missing arms, missing hands, missing fingers, missing legs, missing digit, poorly drawn limbs, poorly drawn arms, poorly drawn hands, poorly drawn fingers, poorly drawn legs, poorly drawn digit,child, child like"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/869b8476-0213-49a3-e1cc-7ba591bed200/width=450/38242.jpeg",
                "nsfw":false,
                "width":512,
                "height":768,
                "hash":"UKGtNf=d56%2vz}@-pJ7$l$ls:9t0gIXR--o",
                "meta":{
                  "Size":"512x768",
                  "seed":1563306171,
                  "steps":40,
                  "prompt":"(dark late at night,mid-night:1.2),(symmetry:1.2),\nperspective,(half_body:1.1),(highly detailed face:1.1),\n(night fireworks background:1.1),blurry background,\n(facing viewer,looking at viewer:1.1),\n\nPureErosFace_v1,(short hair:1.1),\nportrait of an elegant 21yo girl wearing pink flower kimono and cute flower in hair,\n\nhighly detailed, sharp focus, 8k,natural light,lens 135mm,f1.8,art photography,",
                  "sampler":"Euler a",
                  "cfgScale":7,
                  "Model hash":"c785dff0",
                  "negativePrompt":"nsfw,nude,nipples,plant,full_body,bad_prompt_version2,day,sunlight,long hair,\nextra limbs, extra arms, extra hands, extra fingers, extra legs, extra digit, deformed limbs, deformed arms, deformed hands, deformed fingers, deformed legs, deformed digit, malformed limbs, malformed arms, malformed hands, malformed fingers, malformed legs, malformed digit, fused limbs, fused arms, fused hands, fused fingers, fused legs, fused digit, mutated limbs, mutated arms, mutated hands, mutated fingers, mutated legs, mutated digit, mutilated limbs, mutilated arms, mutilated hands, mutilated fingers, mutilated legs, mutilated digit, fewer limbs, fewer arms, fewer hands, fewer fingers, fewer legs, fewer digit, disconnected limbs, disconnected arms, disconnected hands, disconnected fingers, disconnected legs, disconnected digit, missing limbs, missing arms, missing hands, missing fingers, missing legs, missing digit, poorly drawn limbs, poorly drawn arms, poorly drawn hands, poorly drawn fingers, poorly drawn legs, poorly drawn digit,child, child like"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/7061f7bd-6425-47da-d5a6-b0c91e189800/width=450/38246.jpeg",
                "nsfw":false,
                "width":512,
                "height":768,
                "hash":"UMI|wDo|-:?GR~t7wcNG~UoJNeRj=xt79Zt6",
                "meta":{
                  "Size":"512x768",
                  "seed":2540924381,
                  "steps":40,
                  "prompt":"(symmetry!:1.2),facing viewer,\n(half_body:1.1),\n\nhazel eyes caramel,twintails,24yo girl,(short hair:1.1), \nPureErosFace_v1, [:(detailed face:1.2):0.3]\nwedding dress,indoors,bridal veil,\n\ndepth of field,blurry background,\ntelephoto lens, soft focus, 8k canon RAW, art photography,",
                  "sampler":"Euler a",
                  "cfgScale":7,
                  "Model hash":"c785dff0",
                  "negativePrompt":"nsfw,nude,nipples,plant,full_body,bad_prompt_version2,day,sunlight,long hair,\nextra limbs, extra arms, extra hands, extra fingers, extra legs, extra digit, deformed limbs, deformed arms, deformed hands, deformed fingers, deformed legs, deformed digit, malformed limbs, malformed arms, malformed hands, malformed fingers, malformed legs, malformed digit, fused limbs, fused arms, fused hands, fused fingers, fused legs, fused digit, mutated limbs, mutated arms, mutated hands, mutated fingers, mutated legs, mutated digit, mutilated limbs, mutilated arms, mutilated hands, mutilated fingers, mutilated legs, mutilated digit, fewer limbs, fewer arms, fewer hands, fewer fingers, fewer legs, fewer digit, disconnected limbs, disconnected arms, disconnected hands, disconnected fingers, disconnected legs, disconnected digit, missing limbs, missing arms, missing hands, missing fingers, missing legs, missing digit, poorly drawn limbs, poorly drawn arms, poorly drawn hands, poorly drawn fingers, poorly drawn legs, poorly drawn digit,child, child like"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/c7561317-9bf0-4e86-d484-e5d8b2d30000/width=450/38245.jpeg",
                "nsfw":false,
                "width":512,
                "height":768,
                "hash":"UDKmw#8_Dh8_0Kr?~qSO9F-V~WoIyDNbMcIo",
                "meta":{
                  "Size":"512x768",
                  "seed":725376857,
                  "steps":40,
                  "prompt":"(symmetry!:1.2),facing viewer,\n(half_body:1.1),\n\ntwintails,24yo girl,(short hair:1.1), \nPureErosFace_v1, [:(detailed face:1.1):0.3],shiny eyes,\n(wedding dress,bridal veil|(qipao:1.2)),indoors,\n\ndepth of field,blurry background,\ntelephoto lens, soft focus, 8k canon RAW, art photography,",
                  "sampler":"Euler a",
                  "cfgScale":7,
                  "Model hash":"c785dff0",
                  "negativePrompt":"nsfw,nude,nipples,plant,full_body,bad_prompt_version2,day,sunlight,long hair,\nextra limbs, extra arms, extra hands, extra fingers, extra legs, extra digit, deformed limbs, deformed arms, deformed hands, deformed fingers, deformed legs, deformed digit, malformed limbs, malformed arms, malformed hands, malformed fingers, malformed legs, malformed digit, fused limbs, fused arms, fused hands, fused fingers, fused legs, fused digit, mutated limbs, mutated arms, mutated hands, mutated fingers, mutated legs, mutated digit, mutilated limbs, mutilated arms, mutilated hands, mutilated fingers, mutilated legs, mutilated digit, fewer limbs, fewer arms, fewer hands, fewer fingers, fewer legs, fewer digit, disconnected limbs, disconnected arms, disconnected hands, disconnected fingers, disconnected legs, disconnected digit, missing limbs, missing arms, missing hands, missing fingers, missing legs, missing digit, poorly drawn limbs, poorly drawn arms, poorly drawn hands, poorly drawn fingers, poorly drawn legs, poorly drawn digit,child, child like"
                }
              }
            ],
            "downloadUrl":"https://civitai.com/api/download/models/5119"
          }
        ]
      },
      {
        "id":8109,
        "name":"Ulzzang-6500 (Korean doll aesthetic)",
        "description":"<h2>The OG Korean doll-aesthetic mod for Stable Diffusion</h2><p><strong>Donate for civilians in Ukraine, Syria, Mali etc.: </strong><a target=\"_blank\" rel=\"ugc\" href=\"https://www.icrc.org/en/donate\"><strong>Red Cross</strong></a><strong> | </strong><a target=\"_blank\" rel=\"ugc\" href=\"https://donate.doctorswithoutborders.org/secure/donate\"><strong>Doctors without Borders</strong></a><strong> | </strong><a target=\"_blank\" rel=\"ugc\" href=\"https://www.directrelief.org/\"><strong>DirectRelief</strong></a><strong> | </strong><a target=\"_blank\" rel=\"ugc\" href=\"https://www.feedthechildren.org/\"><strong>Feed The Children</strong></a></p><p>Slava Ukraini</p><p>___</p><p><em>» I like to use \"Ulzzang-6500\" embeddings (I used that for all sample images).This is my type....I couldn't avoid generating with this.... «</em></p><p>-Tasuku, who made <a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/6424/chilloutmix\">ChilloutMix</a></p><p></p><p>Works best for <strong>semirealism</strong> and <strong>photorealism</strong>, but most likely only on SD 1.x (tested on 1.4 and 1.5). Is often used in combination with the <a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/6424/chilloutmix\">ChilloutMix</a> and <a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/8281/aom2h-basilmix\">aom2h-basilmix</a>. No bias in terms of eye and hair color and also not mimicking an individual person! Also handles angles well, you can throw pretty much anything at it and use it for inpainting of the face as well. There is a significant bias towards pale skin, as a heads up.</p><h3><strong>How to use</strong></h3><p>Simply download and put into your /embeddings folder in the Automatic1111 folder. Then use 'ulzzang-6500' in your prompt. Reduce or increase the weight of the embedding by using this syntax:</p><p>(ulzzang-6500:1.2) increases the weight, or values below 1 to decrease (such as 0.8)</p><p>I recommend putting ulzzang-6500 towards the end of the prompt, it's strong enough.</p><p><strong>Inpainting</strong></p><p>Another useful approach with this model is to inpaint on top of already existing images that were generated without the embedding if you want to see how they look with the ulzzang face.</p><p>In Automatic1111, on the img2img tab -&gt; Inpaint tab paint over the face (you can include the hair as well). Then describe that specific masked area in the prompt, which means that you should remove \"bad hands\" or \"perfect body\" from the prompt.</p><p>Select \"Inpaint only masked area\" and set the steps to around 70 (this is important, inpainting and img2img require higher step counts). Set the denoising strength to 0.4 to 0.75. The more closely the existing face resembles the ulzzang aesthetic the lower you can set this value. Set the resolution to 512x512, this is plenty for the face region.</p><h3><strong>Note on the concept</strong></h3><p>The embedding is neither intended to provoke childish features (the 'doll-like' refers to an uncanny level of supposed beauty standards, like a slim nose, aegyo sal and tear-drop chin) nor does it have a bias towards them from my testing. If the face in a generation should appear too young that's a bias from the latent model and can be countered by adding 'loli' and 'child' to the negative prompt.</p><p>For the LORA fans there is a similar model as well named Korean doll.</p><p>V1 demo image by <a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/gallery/78258\"><strong>yatagarasu</strong></a>, second one by me, third one by <a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/8281/aom2h-basilmix\"><strong>Bloodsuga</strong></a></p><p>V1.1 images by me</p>",
        "type":"TextualInversion",
        "poi":false,
        "nsfw":true,
        "allowNoCredit":true,
        "allowCommercialUse":"Rent",
        "allowDerivatives":true,
        "allowDifferentLicense":true,
        "stats":{
          "downloadCount":78057,
          "favoriteCount":7864,
          "commentCount":56,
          "ratingCount":38,
          "rating":4.95
        },
        "creator":{
          "username":"festival",
          "image":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/1cde28d2-3b4e-4b35-219e-35863ac1d100/width=96/festival.jpeg"
        },
        "tags":[
          "girl",
          "person",
          "photorealistic",
          "sexy",
          "female",
          "textual inversion",
          "asian",
          "ulzzang",
          "woman",
          "embedding",
          "faces",
          "girls",
          "korean",
          "portraits",
          "realistic"
        ],
        "modelVersions":[
          {
            "id":10107,
            "modelId":8109,
            "name":"v1.1",
            "createdAt":"2023-02-13T18:41:53.579Z",
            "updatedAt":"2023-02-23T18:08:51.680Z",
            "trainedWords":[
              "ulzzang-6500-v1.1"
            ],
            "baseModel":"SD 1.4",
            "earlyAccessTimeFrame":0,
            "description":"<p>Changed weights, should produce cleaner faces and be more close to the prompt. Test both embeddings and see which one works better, this one probably will improve the image in 3 out of 5 cases.</p>",
            "stats":{
              "downloadCount":73361,
              "ratingCount":29,
              "rating":4.93
            },
            "files":[
              {
                "name":"ulzzang-6500-v1.1.bin",
                "id":9682,
                "sizeKB":9.9462890625,
                "type":"Model",
                "metadata":{
                  "fp":"fp16",
                  "size":"full",
                  "format":"Other"
                },
                "pickleScanResult":"Success",
                "pickleScanMessage":"No Pickle imports",
                "virusScanResult":"Success",
                "scannedAt":"2023-02-13T18:46:05.843Z",
                "hashes":{
                  "AutoV2":"8C1AF299C7",
                  "SHA256":"8C1AF299C7E8C2283892A7AD61A5FE5574E88C9C2EE77CD0CDFC0615155FA315",
                  "CRC32":"F80635F8",
                  "BLAKE3":"3FD8439086F0B32982EB736BC0F9BE220BC28562C98559C3DF13CD0ADA32D604"
                },
                "downloadUrl":"https://civitai.com/api/download/models/10107",
                "primary":true
              }
            ],
            "images":[
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/0bf5ee92-9c61-42a4-7ec4-f166738b6800/width=450/98566.jpeg",
                "nsfw":true,
                "width":792,
                "height":1096,
                "hash":"UNH.E4~qNq9t^%XTS~%M?c%g-;xt.A-;V[WB",
                "meta":{
                  "ENSD":"-1",
                  "Size":"512x712",
                  "seed":3671048516,
                  "steps":29,
                  "prompt":"best quality, ultra high res, (photorealistic:1.4), 1 girl, looking at viewer, ulzzang-6500-v1.1",
                  "sampler":"Euler a",
                  "cfgScale":7,
                  "resources":[

                  ],
                  "Model hash":"95afa0d9ea",
                  "Hires steps":"30",
                  "Hires upscale":"1.55",
                  "Hires upscaler":"Latent",
                  "negativePrompt":"paintings, sketches, (worst quality:2), (low quality:2), (normal quality:2), lowres, normal quality, ((monochrome)), ((grayscale)), skin spots, acnes, skin blemishes, age spot, (outdoor:1.6), manboobs, backlight, double navel, mutad arms, hused arms, light",
                  "Denoising strength":"0.6"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/cc8b88a4-6ca8-45be-ddad-a54b9fc22600/width=450/98565.jpeg",
                "nsfw":true,
                "width":768,
                "height":1112,
                "hash":"UEF$6IxE9Z~q4nE2I9s9-;Mwr=-;WB^+_3bc",
                "meta":{
                  "ENSD":"-1",
                  "Size":"512x512",
                  "seed":3536241935,
                  "steps":27,
                  "prompt":"[model = dalcefo paint v3] masterpiece, realistic, realistic lighting, painting, 1girl, arousing, lewd, ecchi, bust, dalcefo, jewelry, small breasts, cleavage cutout, live in wild, depth of field, cinematic angle, ulzzang-6500-v1.1",
                  "sampler":"DPM++ 2M Karras",
                  "cfgScale":7,
                  "Mask blur":"4",
                  "resources":[

                  ],
                  "Model hash":"dce6b18d01",
                  "negativePrompt":"(worst quality, low quality:1.4), blurry, loli, child",
                  "Denoising strength":"0.45"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/39e5753e-c772-41a1-15e2-4a7b218a7600/width=450/98564.jpeg",
                "nsfw":true,
                "width":792,
                "height":1096,
                "hash":"UDJHH*~W00IA00V@-pWBt,D%%2xaAdxZIoWB",
                "meta":{
                  "ENSD":"-1",
                  "Size":"512x712",
                  "seed":350504261,
                  "steps":29,
                  "prompt":"best quality, ultra high res, (photorealistic:1.4), 1 girl, looking at viewer, ulzzang-6500-v1.1",
                  "sampler":"Euler a",
                  "cfgScale":7,
                  "resources":[

                  ],
                  "Model hash":"95afa0d9ea",
                  "Hires steps":"30",
                  "Hires upscale":"1.55",
                  "Hires upscaler":"Latent",
                  "negativePrompt":"paintings, sketches, (worst quality:2), (low quality:2), (normal quality:2), lowres, normal quality, ((monochrome)), ((grayscale)), skin spots, acnes, skin blemishes, age spot, (outdoor:1.6), manboobs, backlight, double navel, mutad arms, hused arms, light",
                  "Denoising strength":"0.6"
                }
              }
            ],
            "downloadUrl":"https://civitai.com/api/download/models/10107"
          },
          {
            "id":9573,
            "modelId":8109,
            "name":"1.0",
            "createdAt":"2023-02-12T00:07:29.189Z",
            "updatedAt":"2023-02-23T18:08:51.680Z",
            "trainedWords":[

            ],
            "baseModel":"SD 1.4",
            "earlyAccessTimeFrame":0,
            "description":null,
            "stats":{
              "downloadCount":4698,
              "ratingCount":11,
              "rating":5
            },
            "files":[
              {
                "name":"ulzzang-6500.pt",
                "id":9270,
                "sizeKB":9.9169921875,
                "type":"Model",
                "metadata":{
                  "fp":"fp16",
                  "size":"full",
                  "format":"PickleTensor"
                },
                "pickleScanResult":"Success",
                "pickleScanMessage":"No Pickle imports",
                "virusScanResult":"Success",
                "scannedAt":"2023-02-12T00:10:58.393Z",
                "hashes":{
                  "AutoV2":"66D481A222",
                  "SHA256":"66D481A222EE4638E254A411890F2A8716E4CE5C3E1B1957891C7628BBDEAC78",
                  "CRC32":"AFF65BC0",
                  "BLAKE3":"19FD55C3765AD09F190EEFE0F8F4F67C8CB2C3BEC8E7CF104489BC3746A21CC4"
                },
                "downloadUrl":"https://civitai.com/api/download/models/9573",
                "primary":true
              }
            ],
            "images":[
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/b97d99de-8d00-482b-e828-75b6c43a7400/width=450/97833.jpeg",
                "nsfw":true,
                "width":768,
                "height":1112,
                "hash":"UGF=t1s99Z_N4-ELI9nOxuMd$%-;ay?b?vIp",
                "meta":{
                  "seed":3536241935,
                  "steps":27,
                  "prompt":"[model = dalcefo paint v3] masterpiece, realistic, realistic lighting, painting, 1girl, arousing, lewd, ecchi, bust, dalcefo, jewelry, small breasts, cleavage cutout, live in wild, depth of field, cinematic angle, ulzzang-6500",
                  "sampler":"DPM++ 2M Karras",
                  "cfgScale":7,
                  "negativePrompt":"(worst quality, low quality:1.4), blurry, loli, child"
                }
              },
              {
                "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/6f08c2fe-105f-4e7d-4ea9-7de1d351ec00/width=450/97299.jpeg",
                "nsfw":true,
                "width":1024,
                "height":1536,
                "hash":"UAIzh$IB00~W0eXmpH9tJPVtNaxaDPaKt8xu",
                "meta":{
                  "ENSD":"31337",
                  "Size":"512x768",
                  "seed":3219398508,
                  "Model":"AOM2H+BasilMix(50-50)",
                  "steps":25,
                  "prompt":"ulzzang-6500, ultra realistic 8k cg, unparalleled masterpiece, absurdres, extraordinary, incredible, exquisite, sensational, perfect artwork, perfect female figure, perfect anatomy, unique, sexy, mature female, solo, very long hair, multicolored hair, huge breasts, looking at viewer, aesthetic, spectacular, splendid, superb, grand, astounding, stunning, magnificent, elegant, graceful, luxury, jewelry, gem, glint, beautiful, gorgeous, charismatic, charming, alluring, erotic, seductive, gothic, fantasy, divine, clean, rich, prestige, fantastic, supreme, apex, paramount, goddess, lace, lace trim, delicate pattern, shiny skin, gold, royal, queen, supernatural, phenomenal, fabulous, marvelous, stupendous, terrific, ((nsfw, breasts out, nipples, puffy nipples))",
                  "sampler":"Euler a",
                  "cfgScale":7,
                  "Clip skip":"2",
                  "resources":[
                    {
                      "hash":"5cec660d69",
                      "name":"AOM2H+BasilMix(50-50)",
                      "type":"model"
                    }
                  ],
                  "Model hash":"5cec660d69",
                  "Hires upscale":"2",
                  "Hires upscaler":"R-ESRGAN 4x+",
                  "negativePrompt":"(worst quality, low quality:1.2), username, watermark, signature, text",
                  "Denoising strength":"0.5"
                }
              }
            ],
            "downloadUrl":"https://civitai.com/api/download/models/9573"
          }
        ]
      }
    ],
    "metadata":{
      "totalItems":1676,
      "currentPage":1,
      "pageSize":3,
      "totalPages":559,
      "nextPage":"https://civitai.com/api/v1/models?limit=3&types=TextualInversion&page=2"
    }
  }
  ```
</details>


### GET /api/v1/models/:modelId

#### 端点 URL

`https://civitai.com/api/v1/models/:modelId`

#### 响应字段

| Name                                 | Type                                                                                            | Description                                                                                        |
| ------------------------------------ | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| id                                   | number                                                                                          | 模型的标识符                                                                                       |
| name                                 | string                                                                                          | 模型的名称                                                                                         |
| description                          | string                                                                                          | 模型的描述 (HTML)                                                                                  |
| type                                 | enum `(Checkpoint, TextualInversion, Hypernetwork, AestheticGradient, LORA, Controlnet, Poses)` | 模型类型                                                                                           |
| nsfw                                 | boolean                                                                                         | 模型是否为 NSFW                                                                                    |
| tags                                 | string[]                                                                                        | 与模型关联的标签                                                                                   |
| mode                                 | enum `(Archived, TakenDown)` \| null                                                            | 模型当前所处的模式。如果为 `Archived`，`files` 字段将为空。如果为 `TakenDown`，`images` 字段将为空 |
| creator.username                     | string                                                                                          | 创作者的名称                                                                                       |
| creator.image                        | string \| null                                                                                  | 创作者头像的 url                                                                                   |
| modelVersions.id                     | number                                                                                          | 模型版本的标识符                                                                                   |
| modelVersions.name                   | string                                                                                          | 模型版本的名称                                                                                     |
| modelVersions.description            | string                                                                                          | 模型版本的描述（通常是变更日志）                                                                   |
| modelVersions.createdAt              | Date                                                                                            | 版本创建的日期                                                                                     |
| modelVersions.downloadUrl            | string                                                                                          | 获取此特定版本模型文件的下载 url                                                                   |
| modelVersions.trainedWords           | string[]                                                                                        | 用于触发模型的词语                                                                                 |
| modelVersions.files.sizeKb           | number                                                                                          | 模型文件的大小（KB）                                                                               |
| modelVersions.files.pickleScanResult | string                                                                                          | pickle 扫描的状态 ('Pending', 'Success', 'Danger', 'Error')                                        |
| modelVersions.files.virusScanResult  | string                                                                                          | 病毒扫描的状态 ('Pending', 'Success', 'Danger', 'Error')                                           |
| modelVersions.files.scannedAt        | Date \| null                                                                                    | 文件扫描的日期                                                                                     |
| modelVersions.files.metadata.fp      | enum (`fp16`, `fp32`) \| undefined                                                              | 文件指定的浮点精度                                                                                 |
| modelVersions.files.metadata.size    | enum (`full`, `pruned`) \| undefined                                                            | 文件指定的模型大小                                                                                 |
| modelVersions.files.metadata.format  | enum (`SafeTensor`, `PickleTensor`, `Other`) \| undefined                                       | 文件指定的模型格式                                                                                 |
| modelVersions.images.url             | string                                                                                          | 图像的 url                                                                                         |
| modelVersions.images.nsfw            | string                                                                                          | 图像是否为 NSFW（注意：如果模型是 NSFW，则将模型上的所有图像视为 NSFW）                            |
| modelVersions.images.width           | number                                                                                          | 图像的原始宽度                                                                                     |
| modelVersions.images.height          | number                                                                                          | 图像的原始高度                                                                                     |
| modelVersions.images.hash            | string                                                                                          | 图像的 [blurhash](https://blurha.sh/)                                                              |
| modelVersions.images.meta            | object \| null                                                                                  | 图像的生成参数                                                                                     |

**注意：** 下载 url 使用 `content-disposition` 标头来正确设置文件名。请确保在获取下载时启用该标头。例如，使用 `wget`：
```
wget https://civitai.com/api/download/models/{modelVersionId} --content-disposition
```

#### 示例

以下示例显示了一个从我们的数据库中获取前 3 个 `TextualInversion` 模型的请求：
```sh
curl https://civitai.com/api/v1/models/1102 \
-H "Content-Type: application/json" \
-X GET
```

这将产生以下响应：
<details>
  <summary>点击展开</summary>

  ```json
  {
    "id":1102,
    "name":"SynthwavePunk",
    "description":"<p>This is a 50/50 Merge of <a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/1061\">Synthwave</a> and <a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/1087\">InkPunk</a> you can use both of their keywords and use prompt weighting to balance between these two cool and complimentary styles.</p><p><strong>I'm on the search for V3!</strong> Check out these <a rel=\"ugc\" href=\"https://civitai.com/models/2856/synthpunk-search\">potential candidates</a> and let me know which you prefer and if either of them are good enough to be the latest version of this model.</p>",
    "type":"Checkpoint",
    "poi":false,
    "nsfw":false,
    "allowNoCredit":true,
    "allowCommercialUse":"Sell",
    "allowDerivatives":true,
    "allowDifferentLicense":true,
    "stats":{
      "downloadCount":15347,
      "favoriteCount":2540,
      "commentCount":22,
      "ratingCount":27,
      "rating":4.93
    },
    "creator":{
      "username":"justmaier",
      "image":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/6046154e-6d32-4500-8772-602edb4a4600/width=96/justmaier.jpeg"
    },
    "tags":[
      {
        "name":"punk"
      },
      {
        "name":"synthwave"
      },
      {
        "name":"style"
      }
    ],
    "modelVersions":[
      {
        "id":1144,
        "modelId":1102,
        "name":"V2",
        "createdAt":"2022-11-30T01:14:36.498Z",
        "updatedAt":"2023-02-18T23:08:24.115Z",
        "trainedWords":[
          "snthwve style",
          "nvinkpunk"
        ],
        "baseModel":"SD 1.5",
        "earlyAccessTimeFrame":0,
        "description":"<p>Upgraded to InkPunk V2.</p><p>This version definitely seems to have picked up more of the InkPunk side of things.</p>",
        "stats":{
          "downloadCount":14195,
          "ratingCount":19,
          "rating":4.89
        },
        "files":[
          {
            "name":"synthwavepunk_v2.ckpt",
            "id":196,
            "sizeKB":2082690.173828125,
            "type":"Model",
            "metadata":{
              "fp":"fp16",
              "size":"pruned",
              "format":"PickleTensor"
            },
            "pickleScanResult":"Success",
            "pickleScanMessage":"No Pickle imports",
            "virusScanResult":"Success",
            "scannedAt":"2022-12-07T10:52:53.433Z",
            "hashes":{
              "AutoV1":"27EA8C02",
              "AutoV2":"DC4C67171E",
              "SHA256":"DC4C67171E2EB64B1A79DA7FDE1CB3FCBEF65364B12C8F5E30A0141FD8C88233",
              "CRC32":"A72626DB",
              "BLAKE3":"02B54CF802A83AEE4DC531E13DA29EEA6DD26FAFFB73E706A0B073FA2304A8F9"
            },
            "downloadUrl":"https://civitai.com/api/download/models/1144",
            "primary":true
          }
        ],
        "images":[
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/3cabeab1-a1c9-4a02-ac76-3a9ed69a1700/width=450/9304.jpeg",
            "nsfw":true,
            "width":512,
            "height":704,
            "hash":"UGH,Y~2o0Y=@5O||S=ENA7vy4.JC9#B-=|rx",
            "meta":{
              "Size":"512x704",
              "seed":785137026,
              "steps":30,
              "prompt":"snthwve style nvinkpunk drunken beautiful woman as delirium from sandman, (hallucinating colorful soap bubbles), by jeremy mann, by sandra chevrier, by dave mckean and richard avedon and maciej kuciara, punk rock, tank girl, high detailed, 8k",
              "sampler":"Euler a",
              "cfgScale":7,
              "Model hash":"27ea8c02",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/12016264-9e99-457b-d50c-8f262706e000/width=450/9417.jpeg",
            "nsfw":false,
            "width":512,
            "height":704,
            "hash":"UhHVPLO=PCxt?@XAFYs9--w|r?wJt3busmSM",
            "meta":{
              "Size":"512x704",
              "seed":2296294451,
              "steps":30,
              "prompt":"(snthwve style:1) (nvinkpunk:0.7) drunken beautiful woman as delirium from sandman, (hallucinating colorful soap bubbles), by jeremy mann, by sandra chevrier, by dave mckean and richard avedon and maciej kuciara, punk rock, tank girl, high detailed, 8k,\nsharp focus, natural lighting, subsurface scattering, f2, 35mm, film grain",
              "sampler":"DPM++ 2M Karras",
              "cfgScale":7,
              "Batch pos":"0",
              "Batch size":"4",
              "Model hash":"27ea8c02",
              "negativePrompt":"cartoon, 3d, (illustration:1.2), ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/6feece23-ac13-44b5-fa8c-1dd334c31000/width=450/9303.jpeg",
            "nsfw":false,
            "width":512,
            "height":512,
            "hash":"UKHBb}og0Mbbd9ofS~bH2uW;#-a|PnkBMejZ",
            "meta":{
              "Size":"512x512",
              "seed":3972917809,
              "steps":30,
              "prompt":"snthwve style nvinkpunk (symmetry:1.1) (portrait of floral:1.05) a woman as a beautiful goddess, (assassins creed style:0.8), pink and gold and opal color scheme, beautiful intricate filegrid facepaint, intricate, elegant, highly detailed, digital painting, artstation, concept art, smooth, sharp focus, illustration, art by greg rutkowski and alphonse mucha, 8k",
              "sampler":"DPM++ 2M Karras",
              "cfgScale":7,
              "Model hash":"27ea8c02",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/02b8537c-bfc5-4a3a-74c8-2155b82f2500/width=450/9302.jpeg",
            "nsfw":false,
            "width":512,
            "height":768,
            "hash":"UoLWe-Cu?wY4=^;9rrM{w0WUn#W?cCSzX7kD",
            "meta":{
              "Size":"512x768",
              "seed":887573803,
              "steps":30,
              "prompt":"snthwve style nvinkpunk award winning half body portrait of a woman in a croptop and cargo pants with ombre navy blue teal hairstyle with head in motion and hair flying, paint splashes, splatter, outrun, vaporware, shaded flat illustration, digital art, trending on artstation, highly detailed, fine detail, intricate",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"0",
              "Batch size":"4",
              "Model hash":"27ea8c02",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/6d82a887-8408-4326-fc6c-371f98214c00/width=450/9301.jpeg",
            "nsfw":false,
            "width":512,
            "height":768,
            "hash":"U?NuJ8XS}7#mxGWUWCofVsn%t7SfxHazSdbH",
            "meta":{
              "Size":"512x768",
              "seed":887573827,
              "steps":30,
              "prompt":"snthwve style nvinkpunk award winning half body portrait of a woman in a croptop and cargo pants with ombre navy blue teal hairstyle with head in motion and hair flying, paint splashes, splatter, outrun, vaporware, shaded flat illustration, digital art, trending on artstation, highly detailed, fine detail, intricate",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"0",
              "Batch size":"4",
              "Model hash":"27ea8c02",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/4f225192-5fa3-48e5-8436-c48c6dcbae00/width=450/9300.jpeg",
            "nsfw":false,
            "width":512,
            "height":768,
            "hash":"UxJ#~D}?oIWEENI=ahnjSLoLbGS3afWCoet6",
            "meta":{
              "Size":"512x768",
              "seed":1251855776,
              "steps":30,
              "prompt":"snthwve style nvinkpunk Charlie Bowater realistic Lithography sketch portrait of a woman, flowers, [gears], pipes, dieselpunk, multi-colored ribbons, old paper texture, highly detailed",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"2",
              "Batch size":"4",
              "Model hash":"27ea8c02",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/756f5932-0ccb-4db1-e0b4-e92565442e00/width=450/9299.jpeg",
            "nsfw":false,
            "width":512,
            "height":768,
            "hash":"U8HTg=t80Js;HXni6[R%0JoK3CJ8yQWX}FxF",
            "meta":{
              "Size":"512x768",
              "seed":383762516,
              "steps":30,
              "prompt":"snthwve style nvinkpunk (symmetry:1.1) (portrait of floral:1.05) a woman as a beautiful goddess, (assassins creed style:0.8), pink and gold and opal color scheme, beautiful intricate filegrid facepaint, intricate, elegant, highly detailed, digital painting, artstation, concept art, smooth, sharp focus, illustration, art by greg rutkowski and alphonse mucha, 8k",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"1",
              "Batch size":"4",
              "Model hash":"27ea8c02",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/687d3ba4-ccb0-4237-2a90-24b6fc73d900/width=450/9298.jpeg",
            "nsfw":false,
            "width":512,
            "height":768,
            "hash":"UfJ?Hkv}{|xtTHEQ9^s+NFxGI:S$MzxsS5NG",
            "meta":{
              "Size":"512x768",
              "seed":1703997512,
              "steps":30,
              "prompt":"(nvinkpunk:1.2) (snthwve style:0.8) fox, anthro, lightwave, sunset, intricate, highly detailed",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"1",
              "Batch size":"4",
              "Model hash":"27ea8c02",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/c4b46a2e-138e-4df8-23ce-32b58fcb0b00/width=450/9297.jpeg",
            "nsfw":false,
            "width":512,
            "height":768,
            "hash":"U]J%3Gu1k:tR}roaoIoLwGaLniadoyX9f,W.",
            "meta":{
              "Size":"512x768",
              "seed":3002697959,
              "steps":30,
              "prompt":"(nvinkpunk:1.2) (snthwve style:0.8) wolf, anthro, lightwave, sunset, intricate, highly detailed",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"3",
              "Batch size":"4",
              "Model hash":"27ea8c02",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/f111f1ee-7821-4d5c-4fc1-ddd0df8b8100/width=450/9295.jpeg",
            "nsfw":false,
            "width":512,
            "height":768,
            "hash":"UTK9iUx@}tw{0gs:S_j?0gM}0}S3?AWUnlR.",
            "meta":{
              "Size":"512x768",
              "seed":283810348,
              "steps":30,
              "prompt":"(nvinkpunk:1.2) (snthwve style:0.8) lion, anthro, lightwave, sunset, intricate, highly detailed",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"3",
              "Batch size":"4",
              "Model hash":"27ea8c02",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          }
        ],
        "downloadUrl":"https://civitai.com/api/download/models/1144"
      },
      {
        "id":1292,
        "modelId":1102,
        "name":"V3 Alpha",
        "createdAt":"2022-12-07T10:40:26.799Z",
        "updatedAt":"2023-02-18T23:08:24.115Z",
        "trainedWords":[
          "nvinkpunk",
          "snthwve style",
          "style of joemadureira"
        ],
        "baseModel":"SD 1.5",
        "earlyAccessTimeFrame":0,
        "description":"<p>I wanted something that gave characters a little more depth so I've been experimenting with merging in some other models. This one is the new <a href=\"https://civitai.com/models/1223/jomad-diffusion\" rel=\"ugc\" target=\"_blank\">JoMad model</a> with SynthwavePunk V2 added as a difference.</p><p><strong>Warning:</strong> The JoeMad model makes it nearly impossible to get things other than people...</p>",
        "stats":{
          "downloadCount":761,
          "ratingCount":5,
          "rating":5
        },
        "files":[
          {
            "name":"synthwavepunk_v3Alpha.ckpt",
            "id":5149,
            "sizeKB":2082918.40625,
            "type":"Model",
            "metadata":{
              "fp":"fp16",
              "size":"full",
              "format":"PickleTensor"
            },
            "pickleScanResult":"Success",
            "pickleScanMessage":"**Detected Pickle imports (5)**\n```\ncollections.OrderedDict\ntorch._utils._rebuild_tensor_v2\ntorch.HalfStorage\ntorch.IntStorage\ntorch.FloatStorage\n```",
            "virusScanResult":"Success",
            "scannedAt":"2023-01-14T03:05:15.488Z",
            "hashes":{
              "AutoV1":"9CE5CEA2",
              "AutoV2":"76F3EED071",
              "SHA256":"76F3EED071327C9075053368D6997CD613AF949D10B2D3034CEF30A1D1D9FEBA",
              "CRC32":"F15BA0A8",
              "BLAKE3":"F83958C6BD911A59456186EA466C2C17B1827178324CF03CC6C427FB064FFFF9"
            },
            "downloadUrl":"https://civitai.com/api/download/models/1292?type=Model&format=PickleTensor"
          },
          {
            "name":"synthwavepunk_v3Alpha.safetensors",
            "id":194,
            "sizeKB":2082691,
            "type":"Model",
            "metadata":{
              "fp":"fp16",
              "size":"full",
              "format":"SafeTensor"
            },
            "pickleScanResult":"Success",
            "pickleScanMessage":"No Pickle imports",
            "virusScanResult":"Success",
            "scannedAt":"2022-12-07T10:49:05.931Z",
            "hashes":{
              "AutoV1":"5D83B27C",
              "AutoV2":"EE2AB6D872",
              "SHA256":"EE2AB6D8723611D9A2FA9B0C8CE5A3770A84189A92B53D5E6CF44B02B9F8E033",
              "CRC32":"97DD6FF4",
              "BLAKE3":"910E778DE880D7EA9511A075B5D4C59B9ED1EE7A9C6B98FFE4EB5C198F0E5240"
            },
            "downloadUrl":"https://civitai.com/api/download/models/1292",
            "primary":true
          }
        ],
        "images":[
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/e82adceb-cae1-45c5-ab39-74850d027200/width=450/10650.jpeg",
            "nsfw":true,
            "width":512,
            "height":704,
            "hash":"USI=DS+|?^V[7z55K#X-DkV[IVtQR*$%V?In",
            "meta":{
              "ENSD":"31337",
              "Size":"512x704",
              "seed":107073939,
              "Model":"joMad+synth-ink-25",
              "steps":24,
              "prompt":"style of joemadureira (nvinkpunk:1.3) (snthwve style:1.4) award winning half body portrait of a woman in a croptop and cargo pants with ombre navy blue teal hairstyle with head in motion and hair flying, paint splashes, splatter, outrun, vaporware, shaded flat illustration, digital art, trending on artstation, highly detailed, fine detail, intricate",
              "sampler":"DPM++ 2M Karras",
              "cfgScale":7,
              "Batch pos":"2",
              "Batch size":"4",
              "Model hash":"5d83b27c",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((deformed)), ((poorly drawn)), ((extra limbs)), blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/f1471530-4263-4424-d298-ecc484470d00/width=450/10649.jpeg",
            "nsfw":false,
            "width":512,
            "height":704,
            "hash":"UHGuXg~U?bM|NeNwIU-BEkr]=xbE9~NK-oE1",
            "meta":{
              "ENSD":"31337",
              "Size":"512x704",
              "seed":107073947,
              "Model":"joMad+synth-ink-25",
              "steps":24,
              "prompt":"style of joemadureira (nvinkpunk:1.3) (snthwve style:1.4) award winning half body portrait of a woman in a croptop and cargo pants with ombre navy blue teal hairstyle with head in motion and hair flying, paint splashes, splatter, outrun, vaporware, shaded flat illustration, digital art, trending on artstation, highly detailed, fine detail, intricate",
              "sampler":"DPM++ 2M Karras",
              "cfgScale":7,
              "Batch pos":"2",
              "Batch size":"4",
              "Model hash":"5d83b27c",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((deformed)), ((poorly drawn)), ((extra limbs)), blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/c8ea989a-d540-4be9-e593-d937e379be00/width=450/10648.jpeg",
            "nsfw":true,
            "width":512,
            "height":704,
            "hash":"UBH1c9$S]@ox*Iw30_#TES9{wGIqVeWs=GI:",
            "meta":{
              "ENSD":"31337",
              "Size":"512x704",
              "seed":2328744801,
              "Model":"joMad+synth-ink-25",
              "steps":24,
              "prompt":"style of joemadureira (nvinkpunk:1.3) (snthwve style:1.4) drunken beautiful woman as delirium from sandman, (hallucinating colorful soap bubbles), by jeremy mann, by sandra chevrier, by dave mckean and richard avedon and maciej kuciara, punk rock, tank girl, high detailed, 8",
              "sampler":"DPM++ 2M Karras",
              "cfgScale":7,
              "Batch pos":"2",
              "Batch size":"4",
              "Model hash":"5d83b27c",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((deformed)), ((poorly drawn)), ((extra limbs)), blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/64389092-cc40-4c0f-f801-dd157e270700/width=450/10647.jpeg",
            "nsfw":true,
            "width":512,
            "height":704,
            "hash":"UAEoxpmm02Mf1$NHV|$j0i%g+bXR9vs-~Ui{",
            "meta":{
              "ENSD":"31337",
              "Size":"512x704",
              "seed":2328744793,
              "Model":"joMad+synth-ink-25",
              "steps":24,
              "prompt":"style of joemadureira (nvinkpunk:1.3) (snthwve style:1.4) drunken beautiful woman as delirium from sandman, (hallucinating colorful soap bubbles), by jeremy mann, by sandra chevrier, by dave mckean and richard avedon and maciej kuciara, punk rock, tank girl, high detailed, 8",
              "sampler":"DPM++ 2M Karras",
              "cfgScale":7,
              "Batch pos":"2",
              "Batch size":"4",
              "Model hash":"5d83b27c",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((deformed)), ((poorly drawn)), ((extra limbs)), blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/2bcadd33-2449-4fd0-b390-a2714e159f00/width=450/10646.jpeg",
            "nsfw":true,
            "width":512,
            "height":704,
            "hash":"UAID?f-o00-o$mWC00IV?ZoeMeMy_LXR~V$*",
            "meta":{
              "ENSD":"31337",
              "Size":"512x704",
              "seed":1957317575,
              "Model":"joMad+synth-ink-25",
              "steps":24,
              "prompt":"style of joemadureira (nvinkpunk:1.3) (snthwve style:1.4) (symmetry:1.1) (portrait of floral:1.05) a woman as a beautiful goddess, (assassins creed style:0.8), pink and gold and opal color scheme, beautiful intricate filegrid facepaint, intricate, elegant, highly detailed, digital painting, artstation, concept art, smooth, sharp focus, illustration, art by greg rutkowski and alphonse mucha, 8k",
              "sampler":"DPM++ 2M Karras",
              "cfgScale":7,
              "Batch pos":"3",
              "Batch size":"4",
              "Model hash":"5d83b27c",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((deformed)), ((poorly drawn)), ((extra limbs)), blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/876ef068-a60f-4e9a-baab-7644a2771600/width=450/10645.jpeg",
            "nsfw":true,
            "width":512,
            "height":704,
            "hash":"UUG*j3IotRoL~Vaf%foLW=ay-obGbZoLWBj[",
            "meta":{
              "ENSD":"31337",
              "Size":"512x704",
              "seed":2782249604,
              "Model":"joMad+synth-ink-25",
              "steps":24,
              "prompt":"style of joemadureira (nvinkpunk:1.3) (snthwve style:1.4) Charlie Bowater realistic Lithography sketch portrait of a woman, flowers, [gears], pipes, dieselpunk, multi-colored ribbons, old paper texture, highly detailed",
              "sampler":"DPM++ 2M Karras",
              "cfgScale":7,
              "Batch pos":"1",
              "Batch size":"4",
              "Model hash":"5d83b27c",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((deformed)), ((poorly drawn)), ((extra limbs)), blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/ccf225a7-8910-476a-6008-14746d4ba100/width=450/10644.jpeg",
            "nsfw":true,
            "width":512,
            "height":704,
            "hash":"UOHd]W%M~qxu^+WXI:j?~Vxa-paxxut6oJoL",
            "meta":{
              "ENSD":"31337",
              "Size":"512x704",
              "seed":2782249592,
              "Model":"joMad+synth-ink-25",
              "steps":24,
              "prompt":"style of joemadureira (nvinkpunk:1.3) (snthwve style:1.4) Charlie Bowater realistic Lithography sketch portrait of a woman, flowers, [gears], pipes, dieselpunk, multi-colored ribbons, old paper texture, highly detailed",
              "sampler":"DPM++ 2M Karras",
              "cfgScale":7,
              "Batch pos":"1",
              "Batch size":"4",
              "Model hash":"5d83b27c",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((deformed)), ((poorly drawn)), ((extra limbs)), blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/a9fb4398-e8ca-46dc-0444-53624ecdf800/width=450/10643.jpeg",
            "nsfw":true,
            "width":512,
            "height":704,
            "hash":"UDHBc5uOTh+I7y7V?Dv$+jocv#rEyD%1ROQ:",
            "meta":{
              "ENSD":"31337",
              "Size":"512x704",
              "seed":107073960,
              "Model":"joMad+synth-ink-25",
              "steps":24,
              "prompt":"style of joemadureira (nvinkpunk:1.3) (snthwve style:1.4) award winning half body portrait of a woman in a croptop and cargo pants with ombre navy blue teal hairstyle with head in motion and hair flying, paint splashes, splatter, outrun, vaporware, shaded flat illustration, digital art, trending on artstation, highly detailed, fine detail, intricate",
              "sampler":"DPM++ 2M Karras",
              "cfgScale":7,
              "Batch pos":"3",
              "Batch size":"4",
              "Model hash":"5d83b27c",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((deformed)), ((poorly drawn)), ((extra limbs)), blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/2cafe44e-57ae-41b0-e408-8770cf56b700/width=450/10642.jpeg",
            "nsfw":true,
            "width":512,
            "height":704,
            "hash":"UGG[$gFM3D%z*JsmTJx]EMn3M}xu9aIV$%t7",
            "meta":{
              "ENSD":"31337",
              "Size":"512x704",
              "seed":107073952,
              "Model":"joMad+synth-ink-25",
              "steps":24,
              "prompt":"style of joemadureira (nvinkpunk:1.3) (snthwve style:1.4) award winning half body portrait of a woman in a croptop and cargo pants with ombre navy blue teal hairstyle with head in motion and hair flying, paint splashes, splatter, outrun, vaporware, shaded flat illustration, digital art, trending on artstation, highly detailed, fine detail, intricate",
              "sampler":"DPM++ 2M Karras",
              "cfgScale":7,
              "Batch pos":"3",
              "Batch size":"4",
              "Model hash":"5d83b27c",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((deformed)), ((poorly drawn)), ((extra limbs)), blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/bf791676-9e1f-472d-d5a3-38f43bd73d00/width=450/10641.jpeg",
            "nsfw":true,
            "width":512,
            "height":704,
            "hash":"UDGum~_%C3%4RsVYkVtSmt.RVrIUV|4:4:_3",
            "meta":{
              "ENSD":"31337",
              "Size":"512x704",
              "seed":3446499621,
              "Model":"joMad+synth-ink-25",
              "steps":24,
              "prompt":"style of joemadureira (nvinkpunk:1.3) (snthwve style:1.4) a woman by agnes cecile, luminous design, pastel colours, ink drips, autumn lights",
              "sampler":"DPM++ 2M Karras",
              "cfgScale":7,
              "Batch pos":"0",
              "Batch size":"4",
              "Model hash":"5d83b27c",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((deformed)), ((poorly drawn)), ((extra limbs)), blurry"
            }
          }
        ],
        "downloadUrl":"https://civitai.com/api/download/models/1292"
      },
      {
        "id":1105,
        "modelId":1102,
        "name":"V1",
        "createdAt":"2022-11-27T22:29:29.401Z",
        "updatedAt":"2023-02-18T23:08:24.115Z",
        "trainedWords":[
          "snthwve style",
          "nvinkpunk"
        ],
        "baseModel":"SD 1.5",
        "earlyAccessTimeFrame":0,
        "description":"<p>A 50/50 Merge of <a href=\"https://civitai.com/models/1061\" rel=\"ugc\" target=\"_blank\">Synthwave</a> and <a href=\"https://civitai.com/models/1087\" rel=\"ugc\" target=\"_blank\">InkPunk</a></p>",
        "stats":{
          "downloadCount":390,
          "ratingCount":3,
          "rating":5
        },
        "files":[
          {
            "name":"synthwavepunk_v1.ckpt",
            "id":951,
            "sizeKB":2082867.794921875,
            "type":"Model",
            "metadata":{
              "fp":"fp16",
              "size":"full",
              "format":"PickleTensor"
            },
            "pickleScanResult":"Success",
            "pickleScanMessage":"No Pickle imports",
            "virusScanResult":"Success",
            "scannedAt":"2022-11-27T23:25:17.557Z",
            "hashes":{
              "AutoV1":"C0E7C884",
              "AutoV2":"D7C4EB223D",
              "SHA256":"D7C4EB223DDD4C89D76D2A9A17E32A135CC9E0ADD0D96D196C95F3E3813FBF88",
              "CRC32":"1F103FDD",
              "BLAKE3":"B2DD8EED7EEAA7E5E13321F64B1077B0828F83384BB4FC3180D737F75AAC0A4B"
            },
            "downloadUrl":"https://civitai.com/api/download/models/1105",
            "primary":true
          }
        ],
        "images":[
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/c78c9dab-284a-4268-f12d-db66bb0cc700/width=450/9040.jpeg",
            "nsfw":true,
            "width":512,
            "height":704,
            "hash":"UPJs^hPW~oIc@2AEZokW0=Nb5WW=%B$_TAV?",
            "meta":{
              "Size":"512x704",
              "seed":785137024,
              "steps":30,
              "prompt":"snthwve style nvinkpunk drunken beautiful woman as delirium from sandman, (hallucinating colorful soap bubbles), by jeremy mann, by sandra chevrier, by dave mckean and richard avedon and maciej kuciara, punk rock, tank girl, high detailed, 8k",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"0",
              "Batch size":"4",
              "Model hash":"c0e7c884",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/849364cf-1707-40bf-1432-e95fe4f4fb00/width=450/9048.jpeg",
            "nsfw":false,
            "width":512,
            "height":704,
            "hash":"UFHv$62U0=~756}GP2IA5hZg9bo}E,B-tK#G",
            "meta":{
              "Size":"512x704",
              "seed":785137026,
              "steps":30,
              "prompt":"snthwve style nvinkpunk drunken beautiful woman as delirium from sandman, (hallucinating colorful soap bubbles), by jeremy mann, by sandra chevrier, by dave mckean and richard avedon and maciej kuciara, punk rock, tank girl, high detailed, 8k",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"2",
              "Batch size":"4",
              "Model hash":"c0e7c884",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/7d771fe6-eca7-40e6-e6de-49dddfff4200/width=450/9203.jpeg",
            "nsfw":false,
            "width":512,
            "height":512,
            "hash":"UYH0ky}W^isDOq$$ods.4=NME3ocv~I@wNWC",
            "meta":{
              "Size":"512x512",
              "seed":2958940867,
              "steps":30,
              "prompt":"(nvinkpunk:1.2) snthwve style motorcyle, lightwave, sunset, intricate, highly detailed",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"1",
              "Batch size":"4",
              "Model hash":"c0e7c884",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/ea3828c5-b342-4138-fe6c-2bca085b9900/width=450/9047.jpeg",
            "nsfw":false,
            "width":512,
            "height":512,
            "hash":"UCMFn=4S7#yA01.pv4+c1steKtK~BVtMobIu",
            "meta":{
              "Size":"512x512",
              "seed":1684812368,
              "steps":30,
              "prompt":"snthwve style nvinkpunk a woman by agnes cecile, luminous design, pastel colours, ink drips, autumn lights",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"0",
              "Batch size":"4",
              "Model hash":"c0e7c884",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/bfc31e9b-e75c-48b8-836d-9e5b5dba0200/width=450/9046.jpeg",
            "nsfw":false,
            "width":512,
            "height":512,
            "hash":"UoNt9VxJ^RSh--s+t3W.NYs+RjNH}an,RkV[",
            "meta":{
              "Size":"512x512",
              "seed":1684812376,
              "steps":30,
              "prompt":"snthwve style nvinkpunk a woman by agnes cecile, luminous design, pastel colours, ink drips, autumn lights",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"0",
              "Batch size":"4",
              "Model hash":"c0e7c884",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/4dd6eb51-6445-459b-36ee-b377709c9d00/width=450/9202.jpeg",
            "nsfw":false,
            "width":512,
            "height":512,
            "hash":"UAFg6G1U%#ER8^z-:jt71R~VFg$w0^vz$PI]",
            "meta":{
              "Size":"512x512",
              "seed":3028378750,
              "steps":30,
              "prompt":"(nvinkpunk:1.2) (snthwve style:0.8) corvette, lightwave, sunset, intricate, highly detailed",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"0",
              "Batch size":"4",
              "Model hash":"c0e7c884",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((b&w)),blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/f992c49f-fc4b-4fa1-133a-2fbd52b35400/width=450/9045.jpeg",
            "nsfw":true,
            "width":512,
            "height":704,
            "hash":"UcKvar}4xK-:D,IwIowMJPKhSJNIE}n,SzjG",
            "meta":{
              "Size":"512x704",
              "seed":785137007,
              "steps":30,
              "prompt":"snthwve style nvinkpunk drunken beautiful woman as delirium from sandman, (hallucinating colorful soap bubbles), by jeremy mann, by sandra chevrier, by dave mckean and richard avedon and maciej kuciara, punk rock, tank girl, high detailed, 8k",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"3",
              "Batch size":"4",
              "Model hash":"c0e7c884",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/19315e0e-7ea1-4cdc-0f22-69c668596800/width=450/9044.jpeg",
            "nsfw":false,
            "width":512,
            "height":512,
            "hash":"UKLMbo3Z3B^w4U[A04M~opv}x-I[5qO=-nox",
            "meta":{
              "Size":"512x512",
              "seed":3972917789,
              "steps":30,
              "prompt":"snthwve style nvinkpunk (symmetry:1.1) (portrait of floral:1.05) a woman as a beautiful goddess, (assassins creed style:0.8), pink and gold and opal color scheme, beautiful intricate filegrid facepaint, intricate, elegant, highly detailed, digital painting, artstation, concept art, smooth, sharp focus, illustration, art by greg rutkowski and alphonse mucha, 8k",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"1",
              "Batch size":"4",
              "Model hash":"c0e7c884",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/8f8ee75b-12a3-4f90-9968-8254b9111900/width=450/9043.jpeg",
            "nsfw":false,
            "width":512,
            "height":512,
            "hash":"URGk].^*YgAC_Lxsxsba1gJTRk$iF{SgI=S4",
            "meta":{
              "Size":"512x512",
              "seed":3972917803,
              "steps":30,
              "prompt":"snthwve style nvinkpunk (symmetry:1.1) (portrait of floral:1.05) a woman as a beautiful goddess, (assassins creed style:0.8), pink and gold and opal color scheme, beautiful intricate filegrid facepaint, intricate, elegant, highly detailed, digital painting, artstation, concept art, smooth, sharp focus, illustration, art by greg rutkowski and alphonse mucha, 8k",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"3",
              "Batch size":"4",
              "Model hash":"c0e7c884",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          },
          {
            "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/cd279adf-8f84-4a10-8ba3-f40fa76bdb00/width=450/9042.jpeg",
            "nsfw":false,
            "width":512,
            "height":512,
            "hash":"USGRf5of4ojbHTbGa3a}Bmayoca{t,j[Rja{",
            "meta":{
              "Size":"512x512",
              "seed":3972917809,
              "steps":30,
              "prompt":"snthwve style nvinkpunk (symmetry:1.1) (portrait of floral:1.05) a woman as a beautiful goddess, (assassins creed style:0.8), pink and gold and opal color scheme, beautiful intricate filegrid facepaint, intricate, elegant, highly detailed, digital painting, artstation, concept art, smooth, sharp focus, illustration, art by greg rutkowski and alphonse mucha, 8k",
              "sampler":"Euler a",
              "cfgScale":7,
              "Batch pos":"1",
              "Batch size":"4",
              "Model hash":"c0e7c884",
              "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
            }
          }
        ],
        "downloadUrl":"https://civitai.com/api/download/models/1105"
      }
    ]
  }
  ```
</details>


### GET /api/v1/models-versions/:modelVersionId

#### 端点 URL

`https://civitai.com/api/v1/model-versions/:id`

#### 响应字段

| Name                   | Type                                                                                            | Description                                                                                        |
| ---------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| id                     | number                                                                                          | 模型版本的标识符                                                                                   |
| name                   | string                                                                                          | 模型版本的名称                                                                                     |
| description            | string                                                                                          | 模型版本的描述（通常是变更日志）                                                                   |
| model.name             | string                                                                                          | 模型的名称                                                                                         |
| model.type             | enum `(Checkpoint, TextualInversion, Hypernetwork, AestheticGradient, LORA, Controlnet, Poses)` | 模型类型                                                                                           |
| model.nsfw             | boolean                                                                                         | 模型是否为 NSFW                                                                                    |
| model.poi              | boolean                                                                                         | 模型是否涉及相关人物 (person of interest)                                                          |
| model.mode             | enum `(Archived, TakenDown)` \| null                                                            | 模型当前所处的模式。如果为 `Archived`，`files` 字段将为空。如果为 `TakenDown`，`images` 字段将为空 |
| modelId                | number                                                                                          | 模型的标识符                                                                                       |
| createdAt              | Date                                                                                            | 版本创建的日期                                                                                     |
| downloadUrl            | string                                                                                          | 获取此特定版本模型文件的下载 url                                                                   |
| trainedWords           | string[]                                                                                        | 用于触发模型的词语                                                                                 |
| files.sizeKb           | number                                                                                          | 模型文件的大小（KB）                                                                               |
| files.pickleScanResult | string                                                                                          | pickle 扫描的状态 ('Pending', 'Success', 'Danger', 'Error')                                        |
| files.virusScanResult  | string                                                                                          | 病毒扫描的状态 ('Pending', 'Success', 'Danger', 'Error')                                           |
| files.scannedAt        | Date \| null                                                                                    | 文件扫描的日期                                                                                     |
| files.metadata.fp      | enum (`fp16`, `fp32`) \| undefined                                                              | 文件指定的浮点精度                                                                                 |
| files.metadata.size    | enum (`full`, `pruned`) \| undefined                                                            | 文件指定的模型大小                                                                                 |
| files.metadata.format  | enum (`SafeTensor`, `PickleTensor`, `Other`) \| undefined                                       | 文件指定的模型格式                                                                                 |
| stats.downloadCount    | number                                                                                          | 模型的下载次数                                                                                     |
| stats.ratingCount      | number                                                                                          | 模型的评分次数                                                                                     |
| stats.rating           | number                                                                                          | 模型的平均评分                                                                                     |
| images.url             | string                                                                                          | 图像的 url                                                                                         |
| images.nsfw            | string                                                                                          | 图像是否为 NSFW（注意：如果模型是 NSFW，则将模型上的所有图像视为 NSFW）                            |
| images.width           | number                                                                                          | 图像的原始宽度                                                                                     |
| images.height          | number                                                                                          | 图像的原始高度                                                                                     |
| images.hash            | string                                                                                          | 图像的 [blurhash](https://blurha.sh/)                                                              |
| images.meta            | object \| null                                                                                  | 图像的生成参数                                                                                     |

**注意：** 下载 url 使用 `content-disposition` 标头来正确设置文件名。请确保在获取下载时启用该标头。例如，使用 `wget`：
```
wget https://civitai.com/api/download/models/{modelVersionId} --content-disposition
```

#### 示例

以下示例显示了一个从我们的数据库中获取模型版本的请求：
```sh
curl https://civitai.com/api/v1/model-versions/1318 \
-H "Content-Type: application/json" \
-X GET
```

这将产生以下响应：
<details>
  <summary>点击展开</summary>

  ```json
  {
    "id":1318,
    "modelId":1244,
    "name":"toad",
    "createdAt":"2022-12-08T19:58:49.765Z",
    "updatedAt":"2022-12-08T20:24:50.330Z",
    "trainedWords":[
      "ttdddd"
    ],
    "baseModel":"SD 1.5",
    "earlyAccessTimeFrame":0,
    "description":null,
    "stats":{
      "downloadCount":438,
      "ratingCount":1,
      "rating":5
    },
    "model":{
      "name":"froggy style",
      "type":"Checkpoint",
      "nsfw":false,
      "poi":false
    },
    "files":[
      {
        "name":"froggyStyle_toad.ckpt",
        "id":289,
        "sizeKB":2546414.971679688,
        "type":"Model",
        "metadata":{
          "fp":"fp16",
          "size":"full",
          "format":"PickleTensor"
        },
        "pickleScanResult":"Success",
        "pickleScanMessage":"**Detected Pickle imports (3)**\n```\ncollections.OrderedDict\ntorch.HalfStorage\ntorch._utils._rebuild_tensor_v2\n```",
        "virusScanResult":"Success",
        "scannedAt":"2022-12-08T20:15:36.133Z",
        "hashes":{
          "AutoV1":"5F06AA6F",
          "AutoV2":"0DF040C8CD",
          "SHA256":"0DF040C8CD48125174B54C251A87822E8ED61D529A92C42C1FA1BEF483B10B0D",
          "CRC32":"32AEB036",
          "BLAKE3":"7E2030574C35F33545951E6588A19E41D88CEBB30598C17805A87EFFD0DB0A99"
        },
        "primary":true,
        "downloadUrl":"https://civitai.com/api/download/models/1318"
      }
    ],
    "images":[
      {
        "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/c6ed4a9d-ae75-463b-7762-da0455cc5700/width=450/10852.jpeg",
        "nsfw":false,
        "width":832,
        "height":832,
        "hash":"U8Civ__MTeSP?utJ9IDj?^Ek=}RQyEE1-Vr=",
        "meta":null
      },
      {
        "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/ed1af033-e944-49ae-5957-f516710f8c00/width=450/10853.jpeg",
        "nsfw":false,
        "width":1024,
        "height":1024,
        "hash":"UMECq1DkIoMy_LIVD+Rk-oRjMytRslWBoeoe",
        "meta":null
      },
      {
        "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/98a3556e-829d-40f1-be5d-f450020d7e00/width=450/10854.jpeg",
        "nsfw":false,
        "width":1024,
        "height":1024,
        "hash":"U5CsBK~p%qIqB+^zH^?a%#?a9G$~-SbxtmE4",
        "meta":null
      },
      {
        "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/3c16ae9e-a789-4ba9-d005-46b7beb6e200/width=450/10855.jpeg",
        "nsfw":false,
        "width":832,
        "height":832,
        "hash":"UHD+-uDkaJfz_N9Gt7jcX9Int7V[-UnOs;kB",
        "meta":null
      },
      {
        "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/06b24fe1-73cc-4610-9f55-cfa46c400900/width=450/10856.jpeg",
        "nsfw":false,
        "width":832,
        "height":832,
        "hash":"UCBpI657NH%0~TIWR*t6ois:RkWBInt4s:R*",
        "meta":null
      },
      {
        "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/f62b8940-ca9e-4a75-5998-aea7d9ce1c00/width=450/10857.jpeg",
        "nsfw":false,
        "width":832,
        "height":832,
        "hash":"U7D0JY00pHNz?]4XD.t2%_aOH[x@^=%OVYR.",
        "meta":null
      },
      {
        "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/3eecff60-7a03-4d4c-adfa-2e2a98b38000/width=450/10858.jpeg",
        "nsfw":false,
        "width":832,
        "height":832,
        "hash":"UFCZY5Io?voJ?wt6-;M{9aogRQV@t6NGR+oL",
        "meta":null
      },
      {
        "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/feb91735-3e80-4a40-5dad-552c781f0c00/width=450/10859.jpeg",
        "nsfw":false,
        "width":832,
        "height":832,
        "hash":"UBBM-+E1.6oM_LV[xtax?ZM}RjWBE1t7ahk8",
        "meta":null
      },
      {
        "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/1cd42261-548f-4f3f-1f88-9fd6100b4100/width=450/10860.jpeg",
        "nsfw":false,
        "width":832,
        "height":832,
        "hash":"UDEL_]r?02%y_JoyD+nO_0NH9I-nxaocM|og",
        "meta":null
      },
      {
        "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/155b8ce8-cb9b-407e-4b48-f07711845b00/width=450/10861.jpeg",
        "nsfw":false,
        "width":832,
        "height":832,
        "hash":"U8ATJ^E355Nd~DE2D*%MNxNHnN-oOYxaxCM|",
        "meta":null
      }
    ],
    "downloadUrl":"https://civitai.com/api/download/models/1318"
  }
  ```
</details>

### GET /api/v1/models-versions/by-hash/:hash

#### 端点 URL

`https://civitai.com/api/v1/model-versions/by-hash/:hash`

#### 响应字段

[与标准 model-versions 端点相同](#response-fields-5)

**注意：** 我们支持以下哈希算法：AutoV1、AutoV2、SHA256、CRC32 和 Blake3

**注意 2：** 我们仍在对旧文件进行哈希处理，因此这些结果尚不完整

### GET /api/v1/tags

#### 端点 URL

`https://civitai.com/api/v1/tags`

#### 查询参数

| 名称           | 类型   | 描述                                                                                                               |
| -------------- | ------ | ------------------------------------------------------------------------------------------------------------------ |
| limit `(可选)` | number | 每页返回的结果数量。这个数字可以在 1 到 200 之间。默认情况下，每页将返回 20 个结果。如果设置为 0，它将返回所有标签 |
| page `(可选)`  | number | 开始获取标签的页面                                                                                                 |
| query `(可选)` | string | 按名称筛选标签的搜索查询                                                                                           |

#### 响应字段

| 名称                 | 类型   | 描述                       |
| -------------------- | ------ | -------------------------- |
| name                 | string | 标签的名称                 |
| modelCount           | number | 链接到此标签的模型数量     |
| link                 | string | 获取此标签的所有模型的 URL |
| metadata.totalItems  | string | 可用的总项目数             |
| metadata.currentPage | string | 您当前所在的页面           |
| metadata.pageSize    | string | 批次的大小                 |
| metadata.totalPages  | string | 总页数                     |
| metadata.nextPage    | string | 获取下一批项目的 URL       |
| metadata.prevPage    | string | 获取上一批项目的 URL       |

#### 示例

以下示例显示了一个从我们的数据库中获取前 3 个模型标签的请求：
```sh
curl https://civitai.com/api/v1/tags?limit=3 \
-H "Content-Type: application/json" \
-X GET
```

这将产生以下响应：
```json
{
    "items": [
        {
            "name": "Pepe Larraz",
            "modelCount": 1,
            "link": "https://civitai.com/api/v1/models?tag=Pepe Larraz"
        },
        {
            "name": "comic book",
            "modelCount": 7,
            "link": "https://civitai.com/api/v1/models?tag=comic book"
        },
        {
            "name": "style",
            "modelCount": 91,
            "link": "https://civitai.com/api/v1/models?tag=style"
        }
    ],
    "metadata": {
        "totalItems": 200,
        "currentPage": 1,
        "pageSize": 3,
        "totalPages": 67,
        "nextPage": "https://civitai.com/api/v1/tags?limit=3&page=2"
    }
}
```

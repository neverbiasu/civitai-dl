# Civitai Downloader 项目规划

## 项目概述

Civitai Downloader 是一款专为 AI 艺术创作者设计的工具，用于高效浏览、下载和管理 Civitai 平台上的模型资源。本文档规划项目的研发周期和实施策略。

## 开发策略

我们采用每周一个小里程碑的快速迭代模式，同步开发命令行和WebUI界面，优先实现核心下载功能。每周末都会有一个可用的产品增量，以保持开发动力。

## 资源需求

| 角色     | 数量  | 主要职责              | 技能要求                   |
| -------- | ----- | --------------------- | -------------------------- |
| 后端开发 | 1-2名 | API集成、下载引擎实现 | Python, Requests, 并发编程 |
| 前端开发 | 1名   | WebUI界面实现         | Gradio                     |
| 项目管理 | 0.5名 | 进度跟踪、协调沟通    | 敏捷方法、技术管理         |
| 测试     | 0.5名 | 功能测试、bug验证     | Python, 自动化测试         |

**注意**: 第1-3周至少需要1名全职后端+1名前端开发；第4-6周可能需要增加0.5名开发以处理高级功能。

## 研发周期规划

### 第1周: 基础下载引擎 (CLI + 简单WebUI)

| 天数 | 任务                | 产出                                 |
| ---- | ------------------- | ------------------------------------ |
| 1-2  | 项目搭建与API客户端 | 能成功连接Civitai API并获取基本数据  |
| 2-4  | 核心下载引擎        | 能下载单个模型文件，处理断点续传     |
| 4-5  | CLI基础命令         | 可用的`download model`命令           |
| 5-6  | 最简WebUI框架       | 能运行的WebUI，显示下载表单          |
| 7    | 测试与优化          | 周末可演示：从CLI和WebUI下载指定模型 |

**周末产出**: 能通过CLI和简易WebUI下载指定ID的模型文件

### 第2周: 多模型管理与基础搜索 (完善CLI + WebUI)

| 天数 | 任务                      | 产出                               |
| ---- | ------------------------- | ---------------------------------- |
| 1-2  | 下载队列管理              | 支持多文件并行下载，任务管理       |
| 2-3  | 搜索API集成               | 支持通过关键词和基本筛选搜索模型   |
| 3-5  | CLI搜索命令与下载管理命令 | 完整的`browse`和`queue`命令        |
| 5-6  | WebUI搜索与下载管理页面   | 可搜索并查看下载队列的WebUI        |
| 7    | 集成测试                  | 周末可演示：搜索并批量下载多个模型 |

**周末产出**: 可搜索模型、查看结果并添加到下载队列，管理下载任务

### 第3周: 图像下载与元数据管理

| 天数 | 任务                  | 产出                                             |
| ---- | --------------------- | ------------------------------------------------ |
| 1-2  | 图像下载功能          | 支持下载模型示例图像，提取生成参数               |
| 2-3  | 文件组织系统          | 自定义保存路径，文件夹结构和命名规则             |
| 3-5  | CLI图像命令与配置命令 | 完整的`images`和`config`命令                     |
| 5-6  | WebUI图像和设置页面   | 显示图像和配置选项的WebUI页面                    |
| 7    | 用户测试              | 周末可演示：下载模型及其示例图像，自定义保存位置 |

**周末产出**: 可同时获取模型和示例图像，自定义文件组织方式

### 第4周: 高级筛选与搜索增强

| 天数 | 任务            | 产出                                 |
| ---- | --------------- | ------------------------------------ |
| 1-3  | 高级筛选系统    | 支持复杂组合条件筛选、保存筛选模板   |
| 3-5  | CLI高级筛选命令 | 增强`browse`命令的高级筛选选项       |
| 5-6  | WebUI高级筛选UI | 直观的高级搜索界面                   |
| 7    | 用户体验优化    | 周末可演示：使用高级筛选条件搜索模型 |

**周末产出**: 使用高级筛选条件精确搜索需要的模型

### 第5周: 性能优化与跨平台支持

| 天数 | 任务             | 产出                            |
| ---- | ---------------- | ------------------------------- |
| 1-2  | 性能优化         | 改进下载速度和搜索性能          |
| 2-3  | 跨平台测试与修复 | 确保在Windows/Mac/Linux正常工作 |
| 3-5  | 配置导入导出     | 支持配置和筛选模板导入导出      |
| 5-6  | 完善文档和帮助   | 完整的用户指南和内置帮助        |
| 7    | 打包与发布准备   | 周末可演示：优化的完整应用程序  |

**周末产出**: 性能优化版本，支持配置导出，完整文档

### 第6周: 高级特性与社区版发布

| 天数 | 任务           | 产出                         |
| ---- | -------------- | ---------------------------- |
| 1-2  | 插件系统       | 基础插件框架，支持自定义行为 |
| 2-3  | 批处理脚本     | 自动化批处理脚本支持         |
| 3-5  | UI主题和定制   | 可定制的UI主题和布局         |
| 5-6  | 最终测试与修复 | 全面的测试覆盖和bug修复      |
| 7    | v1.0版本打包   | 周末产出：v1.0正式版发布     |

**周末产出**: v1.0正式版，完整功能集，社区发布

## 每周成果与激励

| 周次    | 可用功能         | 激励点                               |
| ------- | ---------------- | ------------------------------------ |
| 第1周末 | 基础下载系统     | 首次成功下载一个完整模型文件！       |
| 第2周末 | 搜索和下载队列   | 能搜索并批量下载喜欢的模型！         |
| 第3周末 | 图像和元数据管理 | 能下载完整的模型和示例，建立资源库！ |
| 第4周末 | 本地库和高级搜索 | 拥有个人模型库，使用强大搜索！       |
| 第5周末 | 优化与跨平台     | 高性能版本，随处可用！               |
| 第6周末 | v1.0正式版       | 完整产品发布，成就感满满！           |

## 开发优先级原则

1. **功能优先级**:
   - 第一优先: 核心下载功能 - 确保可靠获取模型文件
   - 第二优先: 搜索与浏览 - 帮助发现所需资源
   - 第三优先: 组织与管理 - 整理本地资源库

2. **界面开发**:
   - CLI和WebUI同步开发，但功能实现先在CLI验证
   - 每个功能都同时提供命令行和Web界面
   - WebUI逐步完善，从功能性到美观性

3. **开发策略**:
   - 小步快跑，每天都有可见进展
   - 周末必有可演示的功能增量
   - 先求可用，再求完美

## 技术选择建议

1. **后端**:
   - Python (requests, click, FastAPI)
   - SQLite (本地数据存储)

2. **前端**:
   - Vue.js + Tailwind CSS (轻量且美观)
   - 嵌入式WebUI (不依赖外部服务器)

3. **部署**:
   - PyPI包 (pip安装)
   - 单文件可执行程序 (使用PyInstaller)

## 后续工作计划

为确保项目按时完成并提供优质的用户体验，制定以下后续工作计划。工作安排按照优先级从高到低排列。

| 周期  | 任务内容           | 优先级 | 状态     | 计划完成时间 | 实际完成时间 |
| ----- | ------------------ | ------ | -------- | ------------ | ------------ |
| 第4周 | 高级筛选系统       | 高     | 已完成   | 第4周末      | 2023-04-30   |
| 第4周 | 下载位置设置       | 中     | 已完成   | 第4周中      | 2023-04-22   |
| 第4周 | 下载队列优先级功能 | 中     | 已完成   | 第4周末      | 2023-04-30   |
| 第5周 | 下载性能优化       | 高     | 未开始   | 第5周中      | -            |
| 第5周 | 跨平台兼容性测试   | 高     | 未开始   | 第5周末      | -            |
| 第5周 | 配置导入/导出功能  | 中     | 部分完成 | 第5周中      | -            |
| 第5周 | 批量操作增强       | 中     | 未开始   | 第5周末      | -            |
| 第6周 | 插件系统架构设计   | 高     | 未开始   | 第6周中      | -            |
| 第6周 | 常用批处理脚本实现 | 中     | 未开始   | 第6周中      | -            |
| 第6周 | WebUI主题系统      | 低     | 未开始   | 第6周末      | -            |
| 第6周 | 发布准备与文档完善 | 高     | 未开始   | 第6周末      | -            |

## 项目完成标准

1. 所有计划功能已实现且通过测试
2. CLI和WebUI功能保持一致
3. 文档已完善，包括安装、使用和开发指南
4. 至少在Windows、macOS和Linux上进行过测试
5. 性能指标满足预期，支持大型模型下载
6. 发布v1.0版本至PyPI

## 风险分析与应对策略

| 风险点                 | 可能性 | 影响 | 应对策略                                     |
| ---------------------- | ------ | ---- | -------------------------------------------- |
| Civitai API变更        | 中     | 高   | 抽象API接口层，设计版本适配机制              |
| 大型模型下载性能不足   | 低     | 高   | 优化并行下载算法，添加智能负载均衡           |
| WebUI与CLI功能不一致   | 中     | 中   | 建立统一的业务逻辑层，UI仅负责展示和交互     |
| 用户需求与开发计划不符 | 高     | 中   | 提早发布测试版，收集用户反馈，调整开发优先级 |
| 跨平台兼容性问题       | 中     | 中   | 使用虚拟环境进行多平台测试，避免平台特定代码 |

## 阶段性评估指标

1. **第一阶段 (Week 1-2)**
   - 核心下载引擎稳定性 > 99%
   - CLI支持下载指定ID的模型和图像

2. **第二阶段 (Week 3-4)**
   - 搜索功能支持5种以上筛选条件
   - WebUI实现与CLI相同的核心功能
   - 本地索引系统支持快速查询和筛选

3. **第三阶段 (Week 5-6)**
   - 系统整体性能达到预期（大型模型下载速度优化）
   - 跨平台测试覆盖率 100%
   - 文档完成度 > 90%
   - 插件系统支持自定义扩展

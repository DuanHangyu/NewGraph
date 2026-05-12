<div align="center">

<img src="images/LOGO.jpg" alt="NewGraph" width="400" />

**基于 Graphiti + Neo4j 的知识图谱构建与智能问答平台**

自动构建领域知识图谱 · 混合检索智能问答 · 交互式图谱可视化

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![Vue 3](https://img.shields.io/badge/Vue-3.5-42b883?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.x-018BFF?logo=neo4j&logoColor=white)](https://neo4j.com/)
[![Graphiti](https://img.shields.io/badge/Graphiti-Core-orange)](https://github.com/getzep/graphiti)

</div>

---

<img src="images/xuanchuantu.jpg" alt="NewGraph Banner" width="100%" />

---

## 功能特性

### 知识图谱构建

导入预设数据集或上传自定义文件，Graphiti SDK 自动提取实体与关系，一键构建领域知识图谱。

- **预设数据集** — 内置 AI 基础领域、AI 前沿技术、量子计算三大主题数据集，开箱即用
- **自定义导入** — 支持 PDF / Markdown / TXT 文件上传，自动解析并提取知识实体
- **自动实体识别** — Graphiti SDK 自动提取 Technology、Researcher、Organization、Concept、Application 五类实体及其关系
- **异步导入** — 后台异步处理，实时显示导入进度

### 交互式图谱可视化

D3.js 力导向布局实时渲染知识图谱，支持丰富的交互操作。

- **力导向布局** — 节点自动排列，关系一目了然
- **颜色编码** — 五种实体类型以不同颜色区分，快速识别节点类别
- **缩放拖拽** — 支持鼠标滚轮缩放与画布拖拽，自由探索大规模图谱
- **节点详情** — 点击节点查看实体名称、类型、属性等详细信息
- **节点/关系统计** — 实时显示当前图谱的节点数和关系数

### 知识图谱问答（KGQA）

基于知识图谱的智能问答，三阶段管道：**图谱检索 → 上下文组装 → LLM 生成**。

- **混合检索** — 向量相似度 + 图遍历双重搜索策略，精准定位相关实体与关系
- **SSE 流式输出** — 实时生成回答，逐字流式返回
- **来源引用** — 每条回答附带知识图谱中的来源实体，可折叠查看
- **图谱联动** — 检索命中的节点和边在图谱中自动高亮，可视化展示推理路径
- **会话管理** — 支持多轮对话，自动维护会话历史

---

## 界面展示

https://github.com/user-attachments/assets/eca9f416-c968-408e-9859-447a495a6ff9

**知识图谱可视化**

<img src="images/using.png" alt="知识图谱可视化" />

**图谱问答联动**

<img src="images/using2.png" alt="图谱问答联动" />

---

## 系统架构

```
┌──────────────────────────────────────────────────────┐
│                  Vue 3 前端 (SPA)                     │
│  D3.js 可视化 · Vue Router · I18n · Axios · marked   │
└──────────────────────┬───────────────────────────────┘
                       │ REST API / SSE
┌──────────────────────▼───────────────────────────────┐
│                 Flask 后端 (Python)                    │
│                                                       │
│  ┌────────────────┐  ┌──────────────┐                 │
│  │ Graphiti 服务   │  │  QA 问答管道  │                │
│  │ graphiti_service│  │  qa_service   │                │
│  └───────┬────────┘  └──────┬───────┘                │
│          │                  │                         │
│  ┌───────▼──────────────────▼───────┐                 │
│  │     LLM Client (OpenAI 兼容)     │                 │
│  └───────────────┬──────────────────┘                 │
└──────────────────┼────────────────────────────────────┘
                   │
            ┌──────▼──────┐
            │    Neo4j     │
            │   图谱存储   │
            └─────────────┘
```

---

## 快速开始

### 环境要求

| 工具 | 版本 | 说明 | 验证命令 |
|------|------|------|----------|
| **Node.js** | >= 18 | 前端运行环境 | `node -v` |
| **Python** | >= 3.11, <= 3.12 | 后端运行环境 | `python --version` |
| **uv** | 最新版 | Python 包管理器 | `uv --version` |

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入以下必需配置：

```env
# LLM API（支持 OpenAI SDK 兼容格式的任意 LLM）
# 推荐：阿里百炼 qwen-plus https://bailian.console.aliyun.com/
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# Neo4j（二选一）
# 选项 A：AuraDB 云托管（推荐，有免费层）https://neo4j.com/cloud/aura/
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# 选项 B：本地 Docker（docker compose up -d）
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_password
```

可选配置：

```env
# 加速 LLM（用于特定任务）
LLM_BOOST_API_KEY=your_key
LLM_BOOST_BASE_URL=https://...
LLM_BOOST_MODEL_NAME=your_model
```

### 2. 安装依赖

```bash
# 一键安装所有依赖
npm run setup:all
```

或分步安装：

```bash
npm run setup          # Node 依赖（根目录 + 前端）
npm run setup:backend  # Python 依赖（自动创建虚拟环境）
```

### 3. 启动服务

```bash
# 前后端同时启动
npm run dev

# 单独启动
npm run backend    # 后端 http://localhost:5001
npm run frontend   # 前端 http://localhost:3000
```

### Docker 部署

```bash
cp .env.example .env
# 编辑 .env 填入 LLM API Key 和 Neo4j 配置
docker compose up -d
```

包含本地 Neo4j 容器，前端映射 `3000` 端口，后端映射 `5001` 端口。

---

## 项目结构

```
Newgraph/
├── backend/                        # Flask API 服务 (Python)
│   ├── app/
│   │   ├── api/                    # 路由蓝图
│   │   │   ├── qa.py               # KGQA 问答端点（SSE 流式）
│   │   │   ├── data.py             # 数据集导入/上传
│   │   │   └── graph.py            # 图谱数据查询
│   │   ├── services/               # 核心业务逻辑
│   │   │   ├── graphiti_service.py # Graphiti SDK 封装（实体提取、混合搜索）
│   │   │   ├── qa_service.py       # QA 管道：检索 → 上下文组装 → LLM 生成
│   │   │   ├── neo4j_operations.py # Neo4j CRUD 操作
│   │   │   └── data_loader.py      # 数据集导入编排（中文分块）
│   │   ├── models/                 # 数据模型（JSON 文件持久化）
│   │   ├── utils/                  # 工具类
│   │   │   ├── llm_client.py       # LLM 客户端（OpenAI 兼容，JSON 截断修复）
│   │   │   ├── async_bridge.py     # asyncio ↔ Flask 同步桥接
│   │   │   ├── file_parser.py      # PDF / MD / TXT 文件解析
│   │   │   └── text_processor.py   # 文本规范化
│   │   └── config.py               # 环境变量配置
│   ├── data/datasets/              # 预设数据集目录
│   │   ├── ai_fundamentals/        # AI 基础领域（5 个文件）
│   │   ├── ai_frontier/            # AI 前沿技术（4 个文件）
│   │   └── quantum_computing/      # 量子计算（2 个文件）
│   └── run.py
├── frontend/                       # Vue 3 SPA
│   └── src/
│       ├── views/                  # 页面组件
│       │   ├── Home.vue            # 首页（数据集选择 + 文档上传）
│       │   ├── DatasetManager.vue  # 数据集管理
│       │   ├── Process.vue         # 图谱可视化（D3.js 力导向布局）
│       │   ├── QAGraph.vue         # 图谱 + 问答分屏视图
│       │   ├── QA.vue              # 纯问答聊天界面
│       │   └── History.vue         # 项目历史列表
│       ├── components/
│       │   └── GraphPanel.vue      # D3.js 图谱面板组件
│       ├── composables/
│       │   └── useGraphRenderer.js # D3.js 力导向布局渲染逻辑
│       ├── api/                    # API 客户端（Axios + 自动重试）
│       ├── store/                  # 状态管理
│       ├── i18n/                   # 国际化（中 / 英）
│       └── router/                 # Vue Router
├── images/                         # README 素材
├── docs/                           # 详细文档
└── docker-compose.yml
```

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端框架** | Vue 3 + Composition API | 渐进式 JavaScript 框架 |
| **前端路由** | Vue Router 4 | SPA 路由管理 |
| **前端国际化** | Vue I18n | 中 / 英文切换 |
| **图谱可视化** | D3.js v7 | 力导向布局，节点颜色编码 |
| **HTTP 客户端** | Axios | 含自动重试 |
| **Markdown 渲染** | marked | QA 回答 Markdown 渲染 |
| **后端框架** | Flask 3.1 | Python WSGI 框架 |
| **图谱引擎** | Graphiti Core | 实体/关系自动提取 + 混合搜索 |
| **图数据库** | Neo4j 5.x | 图谱存储与查询 |
| **LLM 集成** | OpenAI SDK | 兼容格式，JSON mode，截断修复 |
| **异步桥接** | AsyncBridge | asyncio 事件循环 → Flask 同步调用 |
| **文件解析** | PyMuPDF + chardet | PDF / MD / TXT，多编码回退 |
| **包管理** | uv (Python) + npm (Node) | 快速依赖安装 |

---

## API 端点

### 数据集 (`/api/data`)

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/presets` | 列出预设数据集 |
| `POST` | `/ingest` | 导入预设数据集（异步） |
| `POST` | `/upload` | 上传自定义文件（异步） |
| `GET` | `/ingest-status/:id` | 查询导入进度 |

### 图谱 (`/api/graph`)

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/graphiti-data/:id` | 获取 Graphiti 图谱数据 |
| `GET` | `/data/:id` | 获取图谱可视化数据 |
| `GET` | `/project/list` | 列出所有项目 |
| `GET` | `/project/:id` | 获取项目详情 |
| `DELETE` | `/project/:id` | 删除项目 |

### 问答 (`/api/qa`)

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/ask` | 提问（非流式） |
| `POST` | `/ask-stream` | 提问（SSE 流式） |
| `GET` | `/history/:id` | 获取会话历史 |
| `DELETE` | `/history/:id` | 清除会话 |

---

## 预设数据集

| 数据集 | 显示名 | 文件数 | 内容 |
|--------|--------|--------|------|
| `ai_fundamentals` | AI 基础领域 | 5 | 机器学习、深度学习、计算机视觉、自然语言处理、知识图谱 |
| `ai_frontier` | AI 前沿技术 | 4 | 大语言模型、多模态 AI、前沿技术、中国 AI 产业 |
| `quantum_computing` | 量子计算 | 2 | 量子计算基础、中国量子发展 |

导入后 Graphiti SDK 自动提取以下实体类型：`Technology`、`Researcher`、`Organization`、`Concept`、`Application`。

---

## 常见问题

<details>
<summary><b>Neo4j 连接超时怎么办？</b></summary>

- AuraDB 云端可能因网络延迟较高导致超时，系统已优化连接池配置
- 网络不稳定时建议使用本地 Docker 部署：`docker compose up -d`
- 确认 `.env` 中的连接信息正确（URI、用户名、密码）

</details>

<details>
<summary><b>LLM 回答质量不佳？</b></summary>

- 推荐使用 `qwen-plus` 或同等能力的模型，较弱的模型可能导致回答不完整
- 尝试更具体的提问，避免过于宽泛的问题
- 确保数据集已完整导入（在数据集管理页面查看导入状态）

</details>

<details>
<summary><b>数据集导入失败？</b></summary>

- 检查 LLM API Key 是否正确配置
- 确认 Neo4j 连接正常（访问 `http://localhost:5001/health` 检查）
- 大文件导入耗时较长，请耐心等待或在数据集管理页面查看进度

</details>

<details>
<summary><b>图谱不显示或节点为空？</b></summary>

- 确认数据集导入状态为"已完成"
- 检查浏览器控制台是否有 API 错误
- 刷新页面重新加载图谱数据

</details>

<details>
<summary><b>如何使用自定义数据？</b></summary>

- 在首页点击"上传文件"按钮，支持 PDF / Markdown / TXT 格式
- 上传后系统自动调用 Graphiti 提取实体和关系
- 导入完成后即可在图谱页面查看和进行问答

</details>

---

## 文档

| 文档 | 说明 |
|------|------|
| [API 接口文档](docs/API.md) | 完整请求/响应示例 |
| [架构文档](docs/ARCHITECTURE.md) | 代码架构、数据流、LLM 提示工程 |
| [AuraDB 配置](docs/AURADB_SETUP.md) | Neo4j 云托管配置指南 |

---

## 许可证

本项目基于 [AGPL-3.0](LICENSE) 许可证开源。

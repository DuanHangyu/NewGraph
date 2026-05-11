<div align="center">
  <img src="frontend/src/assets/logo/Evolith_logo_left.jpg" alt="Evolith" width="600" />
</div>

---

## ⚡ 项目概述

**Evolith** 是一款基于 LLM 和 Neo4j 的**PBL驱动学习路径知识图谱 + 虚拟课堂一体化平台**。通过分析课程描述和文档，自动提取知识点并构建**项目驱动+环形知识链**的学习图谱，并与 OpenMAIC 虚拟课堂引擎深度集成，为每个知识点生成沉浸式 AI 虚拟课堂（含播客模式），帮助学习者通过递进式项目掌握知识、通过虚拟课堂进行实践学习。

> 你只需：用自然语言描述课程目标（可选上传课程材料）
> Evolith 将返回：结构清晰、路径明确的项目驱动学习路径知识图谱 + 可交互的虚拟课堂

### 我们的理念

Evolith 不只是构建知识关联图谱，而是构建**以项目为驱动的学习路径**：

```
[项目1: 基础环境搭建] ─NEXT_STEP→ [项目2: 数据处理] ─NEXT_STEP→ [项目3: 模型训练] ─NEXT_STEP→ [项目4: 综合实战]
  ↑↘REQUIRES                      ↑↘REQUIRES                    ↑↘REQUIRES                    ↑↘REQUIRES
  │ [K1: Python基础]              │ [K1: 数据结构]              │ [K1: 梯度下降]              │ [K1: 模型评估]
  │ [K2: 环境配置]                │ [K2: Pandas库]              │ [K2: 反向传播]              │ [K2: 超参调优]
  │ [K3: 包管理]                  │ [K3: 数据清洗]              │ [K3: 损失函数]              │ [K3: 部署流程]
  └─PREREQUISITE_OF→ K3→K2→K1 ──┘ └─PREREQUISITE_OF→ K3→K2→K1┘ └─PREREQUISITE_OF→ K3→K2→K1 ┘ └─PREREQUISITE_OF→ K3→K2→K1─┘
     ↗ 环形闭合: K1 ─REQUIRES→ 项目1   环形闭合: K1 ─REQUIRES→ 项目2                    ...                   ↗ 环形闭合
```

- **项目节点（Project）**：核心学习单元，按 NEXT_STEP 构成主路径和分支路径
- **知识链（Knowledge Chain）**：每个项目拥有独立的环形知识链（2-5个知识点），通过 REQUIRES 边与项目关联
- **环形闭合**：项目 → K1 → K2 → ... → Kn → 项目，知识链首尾相连形成环
- **知识点互不共享**：每个项目的知识链是独立的，不会跨项目复用

### 我们的愿景

- **对教育者**：自动生成学习路径图谱，可视化知识结构和教学顺序，提升教学质量
- **对学习者**：清晰了解学什么、先学什么、学完能做什么，掌握系统化学习路线；还可进入虚拟课堂进行沉浸式实践学习
- **对研究者**：从教育资源中提取和分析知识结构，用于研究目的

## ✨ 核心功能

### 🤖 LLM 智能学习路径提取
- 自动分析课程描述和文档，提取项目节点和知识点，构建 PBL 驱动的学习路径
- **项目驱动+环形知识链结构**：LLM 自动识别项目序列（主路径+分支项目）及每个项目的知识链
- 每个项目包含：难度级别、学习顺序、前置知识摘要、学习成果摘要；每个知识点包含：难度级别、学习顺序
- **2种节点类型**：Project（项目）和 KnowledgePoint（知识点），结构清晰
- **3种边类型**：NEXT_STEP（项目顺序）、REQUIRES（项目↔知识点）、PREREQUISITE_OF（知识点顺序）
- **环形知识链**：每个项目的知识点形成闭合环，项目→K1→K2→...→Kn→项目
- **自动环检测**：检测并移除 PREREQUISITE_OF 边中的循环依赖
- **自动修复截断的 JSON**：当 LLM 输出被截断时，自动修复并解析
- **支持大图谱**：最大支持 16K tokens 的输出

### 📊 Neo4j 图谱存储
- 基于 Neo4j 构建项目驱动的学习路径知识图谱
- **双节点类型存储**：Project（项目）和 KnowledgePoint（知识点）
- **有向边存储**：边以有向关系存储（source→target），方向对学习路径至关重要
- **环形知识链**：REQUIRES 边双向连接项目和知识点，形成闭合环
- 支持高效的图遍历和学习路径查询
- Cypher 注入防护：属性键名和标签验证

### 🎨 双模式交互式可视化

**全图视图**（力导向布局）：
- D3.js 力导向布局展示所有节点和边
- 学习路径边带**方向箭头**，清晰展示知识流向
- **边颜色编码**：NEXT_STEP 项目顺序（黑色粗线）、REQUIRES 项目↔知识点（紫色）、PREREQUISITE_OF 知识点顺序（橙色）
- **节点形状区分**：项目节点为圆角矩形（16-24px），知识点节点为圆形（8-14px）
- **节点大小按难度区分**：入门=8px，中级=11px，高级=14px（知识点）；入门=16px，中级=20px，高级=24px（项目）

**学习路径视图**（分层布局）：
- 项目沿主路径水平排列，从左到右（从入门到高级）
- 分支项目在主路径上方或下方展开，通过 NEXT_STEP 汇回主路径
- 每个项目的环形知识链环绕项目节点展示
- 清晰的"项目序列与知识环绕"视觉隐喻
- 支持缩放和平移

**增强的详情面板**：
- 节点类型徽章（项目/知识点）
- 难度级别徽章（入门/中级/高级）
- 学习顺序编号
- 前置知识摘要和学习成果摘要
- 项目节点：显示关联的知识链内容
- 知识点节点：显示所属项目和知识链位置

**学习路径侧边栏**：
- 项目序列有序列表（含难度徽章）
- 每个项目下可折叠的知识链列表
- 环形闭合指示器，标识知识链首尾相连
- 点击可聚焦到图谱中对应节点

### 🌍 多语言支持
- 中英文界面
- 实时语言切换
- 国际化错误提示

### 🎓 虚拟课堂集成
- 知识点可直接生成 OpenMAIC 虚拟 AI 课堂
- 课堂ID 缓存到 Neo4j，再次访问无需重新生成
- 全屏 iframe 沉浸式学习体验
- 支持麦克风、摄像头、自动播放权限
- 一键启动 Evolith + OpenMAIC 全部服务

### 🎙️ 播客模式
- 生成课堂时可选择"课堂模式"（单人 TTS）或"播客模式"（双人对话音频）
- 播客模式使用火山引擎（Volcengine）Podcast TTS API 生成连续双人播客音频
- **两种声音配对可选**：咪仔+大意（mizai-dayi）、刘飞+潇磊（liufei-xiaolei）
- 笔记区域显示每轮对话文字内容（带说话人标识）
- 播客音频连续播放，基于时间轴的字幕和说话人头像同步
- 播客生成失败时自动回退到单人 TTS 模式
- 需在 OpenMAIC 端 `.env.local` 配置 `PODCAST_VOLCENGINE_APP_ID` 和 `PODCAST_VOLCENGINE_ACCESS_KEY`

### 📂 项目历史记录
- 自动保存所有构建完成的知识图谱项目
- 一键查看历史项目列表
- 快速打开已保存的项目
- 支持删除不需要的项目
- 项目状态可视化（已完成、进行中、失败等）

### 🔄 向后兼容
- 旧项目（使用旧的多节点类型和六种边类型模型）仍可正常渲染
- 新项目使用 PBL 驱动模型（Project + KnowledgePoint 双节点类型，三种边类型）
- 无学习路径边时不显示视图模式切换按钮
- 全图视图对旧项目和新项目完全兼容

## 🔄 工作流程

1. **课程描述**：用自然语言描述课程目标
2. **文档上传**：（可选）上传课程材料（PDF、MD、TXT）作为补充
3. **学习路径提取**：LLM 分析课程描述和文档，提取项目节点、知识点和环形知识链
4. **图谱存储**：以有向关系存储到 Neo4j
5. **双模式可视化**：全图视图 / 学习路径视图交互式探索（项目驱动+环形知识链）
6. **虚拟课堂**：点击知识点生成或进入 AI 虚拟课堂，可选择课堂模式或播客模式
7. **历史记录**：所有项目自动保存，随时可查看和重新打开

## 🚀 快速开始

### 一、源码部署（推荐）

#### 前置要求

| 工具 | 版本要求 | 说明 | 安装检查 |
|------|---------|------|---------|
| **Node.js** | 18+ | 前端运行环境，包含 npm | `node -v` |
| **Python** | ≥3.11, ≤3.12 | 后端运行环境 | `python --version` |
| **uv** | 最新版 | Python 包管理器 | `uv --version` |

#### 1. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入必要的 API 密钥
```

**必需的环境变量：**

```env
# LLM API配置（支持 OpenAI SDK 格式的任意 LLM API）
# 推荐使用阿里百炼平台 qwen-plus 模型：https://bailian.console.aliyun.com/
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# Neo4j AuraDB 配置（推荐生产环境使用）
# 从 Neo4j Console 获取连接字符串
# 免费层：https://neo4j.com/cloud/aura/
NEO4J_URI=neo4j+s://username:password@xxxxx.databases.neo4j.io

# ===== 或使用本地 Neo4j =====
# 需要运行 Neo4j 容器：docker compose up -d
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

**可选的环境变量：**

```env
# ===== 加速 LLM 配置（可选）=====
# 使用不同的 LLM API 用于图谱提取加速
LLM_BOOST_API_KEY=your_api_key
LLM_BOOST_BASE_URL=your_base_url
LLM_BOOST_MODEL_NAME=your_model_name

# ===== OpenMAIC 虚拟课堂配置（可选）=====
OPENMAIC_BASE_URL=http://localhost:3001
OPENMAIC_TIMEOUT=300
OPENMAIC_DIR=F:\AI Projects\OpenMAIC
```

> **注意**：Neo4j AuraDB 和本地 Neo4j 只需配置一种，推荐使用 AuraDB 免费层。
> **播客模式注意**：播客模式的环境变量（`PODCAST_VOLCENGINE_APP_ID`、`PODCAST_VOLCENGINE_ACCESS_KEY`）需要在 OpenMAIC 端的 `.env.local` 中配置，而非 Evolith 的 `.env`。

#### 2. 安装依赖

```bash
# 一键安装所有依赖（根目录 + 前端 + 后端）
npm run setup:all
```

或者分步安装：

```bash
# 安装 Node 依赖（根目录 + 前端）
npm run setup

# 安装 Python 依赖（后端，自动创建虚拟环境）
npm run setup:backend
```

#### 3. 启动服务

```bash
# 同时启动前后端（在项目根目录执行）
npm run dev

# 同时启动前后端 + OpenMAIC 虚拟课堂（需要 OpenMAIC 项目）
npm run dev:all
```

**服务地址：**
- 前端：`http://localhost:3000`（或下一个可用端口）
- 后端 API：`http://localhost:5001`
- OpenMAIC 课堂：`http://localhost:3001`（仅 `dev:all` 模式）

**单独启动：**

```bash
npm run backend   # 仅启动后端
npm run frontend  # 仅启动前端
```

**OpenMAIC 路径配置**（`dev:all` 模式需要）：

在 `.env` 中添加 OpenMAIC 项目路径：
```env
OPENMAIC_DIR=F:\AI Projects\OpenMAIC
```

或通过环境变量指定：
```bash
# Windows CMD
set OPENMAIC_DIR=F:\AI Projects\OpenMAIC

# bash/zsh
export OPENMAIC_DIR=/path/to/OpenMAIC
```

**跨域 iframe 音频权限配置**（课堂音频正常播放需要 4 项配置，详见 [OPENMAIC_INTEGRATION.md](docs/OPENMAIC_INTEGRATION.md)）：

1. OpenMAIC `next.config.ts`：设置 `ALLOWED_FRAME_ANCESTORS=http://localhost:3000`
2. Evolith `vite.config.js`：设置 `Permissions-Policy: autoplay=(self "http://localhost:3001")`
3. Evolith `Classroom.vue`：iframe `allow="microphone; camera; autoplay 'src'"`
4. OpenMAIC 音频播放器：使用 AudioContext 并通过用户手势 unlock

### 二、Docker 部署

```bash
# 1. 配置环境变量（同源码部署）
cp .env.example .env

# 2. 拉取镜像并启动（含本地 Neo4j）
docker compose up -d
```

默认会读取根目录下的 `.env`，并映射端口 `3000（前端）/5001（后端）`。Neo4j 端口 `7474（HTTP）/7687（Bolt）`。

> 在 `docker-compose.yml` 中已通过注释提供加速镜像地址，可按需替换

## 🛠️ 技术栈

### 前端
- **Vue 3**: 渐进式 JavaScript 框架，使用 Composition API
- **Vue Router 4**: Vue.js 官方路由
- **Vue I18n**: 国际化插件
- **Axios**: HTTP 客户端（含 retry 逻辑）
- **D3.js**: 数据可视化库（力导向布局 + 学习路径分层布局，支持圆角矩形和圆形节点）

### 后端
- **Flask 3.1**: WSGI Web 应用框架
- **Flask-CORS**: 跨域资源共享
- **Neo4j >= 5.0.0**: 图谱存储和检索（有向边，Project/KnowledgePoint 双节点类型）
- **OpenAI SDK**: LLM API 客户端（含 JSON 截断修复、600s 超时、JSON mode 回退）
- **requests**: HTTP 客户端（代理调用 OpenMAIC，含 ValueError/JSONDecodeError 容错）
- **uv**: 快速 Python 包管理器

### 工具库
- **PyMuPDF**: PDF 文档解析
- **chardet/charset-normalizer**: 字符编码检测

### 外部服务
- **OpenMAIC**：AI 虚拟课堂生成引擎（Next.js + React，姐妹项目）
- **Volcengine Podcast TTS API**：播客模式双人对话音频生成（WebSocket SAMI 二进制协议）

## 📝 日志系统

后端使用双层日志系统：

### 日志输出位置
- **控制台**（stderr）：实时查看日志，方便调试
- **日志文件**（`backend/logs/YYYY-MM-DD.log`）：持久化存储，按日期轮转（10MB，5份备份）

### 日志级别
- **DEBUG**：详细调试信息（仅写入文件）
- **INFO**：一般信息（控制台 + 文件）
- **WARNING**：警告信息（控制台 + 文件）
- **ERROR**：错误信息（控制台 + 文件）

### 日志格式
- **控制台**：简洁格式，适合快速查看
  ```
  [14:05:09] INFO: === 开始提取图谱 ===
  ```
- **文件**：详细格式，包含函数名和行号
  ```
  [2026-04-19 14:05:09] INFO [evolith.api.extract_graph:161] === 开始提取图谱 ===
  ```

## 📁 项目结构

```
Evolith/
├── backend/                 # Python 后端
│   ├── app/
│   │   ├── api/              # API 路由
│   │   │   ├── graph.py     # 图谱相关端点（含学习路径接口）
│   │   │   └── classroom.py # 虚拟课堂端点（代理 OpenMAIC，含播客模式）
│   │   ├── models/           # 数据模型（Project, ProjectStatus）
│   │   ├── services/         # 业务逻辑
│   │   │   ├── neo4j_manager.py        # Neo4j 连接管理
│   │   │   ├── neo4j_operations.py    # Neo4j CRUD + 学习路径查询 + 节点属性更新
│   │   │   ├── graph_extractor.py       # LLM PBL驱动图谱提取（项目+环形知识链）
│   │   │   └── text_processor.py       # 文本处理
│   │   ├── utils/            # 工具类
│   │   │   ├── llm_client.py          # LLM 客户端（含 JSON 截断修复）
│   │   │   ├── file_parser.py         # 文件解析（PDF/MD/TXT）
│   │   │   ├── logger.py              # 双层日志系统
│   │   │   ├── locale.py              # 国际化（zh/en）
│   │   │   └── retry.py               # API 请求重试逻辑
│   │   ├── config.py         # 配置管理
│   │   └── __init__.py       # Flask 应用工厂
│   ├── pyproject.toml       # 项目配置
│   └── run.py               # 入口点
├── frontend/                # Vue 3 前端
│   └── src/
│       ├── views/            # 页面组件
│       │   ├── Home.vue      # 首页（课程描述+文件上传）
│       │   ├── History.vue   # 历史记录页面
│       │   ├── Process.vue   # 主流程页面（双模式可视化+虚拟课堂+播客选项）
│       │   └── Classroom.vue # 虚拟课堂页面（iframe 嵌入 OpenMAIC）
│       ├── components/       # 可复用组件
│       │   ├── GraphPanel.vue      # 图谱可视化（D3.js）
│       │   └── LanguageSwitcher.vue # 语言切换
│       ├── api/              # API 客户端（含 retry）
│       ├── router/           # Vue Router 配置
│       ├── store/            # 状态管理
│       └── i18n/             # 国际化
├── locales/                 # 翻译文件
│   ├── zh.json             # 中文
│   └── en.json             # 英文
├── scripts/                 # 脚本
│   └── dev-all.mjs         # 一键启动 Evolith + OpenMAIC
├── docs/                    # 详细文档
├── .env.example            # 环境变量模板
├── docker-compose.yml      # Docker 配置（含 Neo4j 容器）
└── Dockerfile              # 前端+后端一体化镜像
```

## 🔧 API 端点

### 项目管理
- `GET /api/graph/project/list` - 列出所有项目
- `GET /api/graph/project/{project_id}` - 获取项目详情
- `DELETE /api/graph/project/{project_id}` - 删除项目
- `POST /api/graph/project/{project_id}/reset` - 重置项目

### 图谱提取
- `POST /api/graph/extract` - 上传课程描述和文档，提取 PBL 驱动学习路径图谱

### 图谱存储
- `POST /api/graph/store` - 将提取的图谱（项目节点+知识链）以有向关系存储到 Neo4j

### 图谱数据
- `GET /api/graph/data/{graph_id}` - 获取可视化图谱数据
- `DELETE /api/graph/delete/{graph_id}` - 删除图谱

### 学习路径
- `GET /api/graph/learning-path/{project_id}` - 获取学习路径结构（PBL 模式或知识驱动模式，自动检测）

### 虚拟课堂
- `POST /api/classroom/generate` - 为知识点生成虚拟课堂（支持 `podcast_mode` 和 `podcast_speaker_pair` 参数）
- `GET /api/classroom/status/{job_id}` - 查询课堂生成状态（含轮询 retry 逻辑）
- `POST /api/classroom/cache` - 缓存课堂ID到 Neo4j

### 健康检查
- `GET /health` - 系统健康检查

> 完整的 API 请求/响应文档请参阅 [docs/API.md](docs/API.md)

## 🗺️ 如何读懂知识图谱

### 节点类型（两种形状的节点）

Evolith 使用 PBL（项目驱动学习）模型，节点分为两种类型：

| 类型 | 形状 | 含义 | 示例 |
|------|------|------|------|
| **Project（项目）** | 圆角矩形 | 核心学习单元，代表一个需要完成的项目/任务 | "搭建Python开发环境"、"实现数据预处理" |
| **KnowledgePoint（知识点）** | 圆形 | 项目所需的具体知识点 | "Python基础语法"、"Pandas数据结构" |

> 项目节点较大（16-24px），以圆角矩形渲染，突出其核心地位；知识点节点较小（8-14px），以圆形渲染。

### 环形知识链

每个项目都拥有**独立的环形知识链**：

```
    ┌──── REQUIRES (项目→K1，链的起点) ────┐
    ↓                                       │
  [项目]                                   [K1]
    ↑                                       ↓
    │                                      [K2]
    │                                       ↓
    └── REQUIRES (Kn→项目，链的终点/环形闭合) ─ [K3]
```

- 项目通过 REQUIRES 边指向第一个知识点（链的起点）
- 知识点之间通过 PREREQUISITE_OF 边形成顺序：K1 → K2 → K3
- 最后一个知识点通过 REQUIRES 边指回项目（环形闭合）
- **知识点互不共享**：每个项目的知识链是独立的，不会跨项目复用

### 边类型（三种颜色的箭头/连线）

| 边类型 | 颜色 | 方向 | 含义 | 举例 |
|--------|------|------|------|------|
| `NEXT_STEP` | ⬛ 黑色粗线 | Project→Project | 项目间的**下一步**，直接学习顺序 | "环境搭建" → "数据处理" |
| `REQUIRES` | 🟣 紫色 | Project↔KnowledgePoint | 项目**需要**某知识点（双向：链起点+环形闭合） | 项目→K1（链起点），Kn→项目（环形闭合） |
| `PREREQUISITE_OF` | 🟠 橙色 | KnowledgePoint→KnowledgePoint | 知识点之间的**前置条件**，必须先学源才能学目标 | "Python基础" → "面向对象编程" |

### 节点外观差异

**形状**（按节点类型区分）：
- 圆角矩形 = **项目节点**（核心学习单元）
- 圆形 = **知识点节点**（项目所需知识）

**大小**（按难度区分）：
- 项目节点：小 (16px) = 入门，中 (20px) = 中级，大 (24px) = 高级
- 知识点节点：小 (8px) = 入门，中 (11px) = 中级，大 (14px) = 高级

### 阅读图谱的方法

1. **从左到右**：学习路径视图中，左边是入门项目，右边是高级项目
2. **粗黑线 (NEXT_STEP)**：项目间的学习顺序，跟着走就能完成课程
3. **紫色线 (REQUIRES)**：项目需要的知识点，双向连接形成环形知识链
4. **橙色线 (PREREQUISITE_OF)**：知识点之间的前置条件，学目标之前必须先学源
5. **看圆角矩形**：每个圆角矩形是一个项目，点击可查看其知识链
6. **环形闭合**：知识链从项目出发，经过知识点序列，最终回到项目

## 📖 文档

- [功能文档](docs/FEATURES.md) - 详细功能说明、数据模型、技术栈
- [API接口文档](docs/API.md) - 完整的前后端API接口说明（含请求/响应示例）
- [架构文档](docs/ARCHITECTURE.md) - 代码架构、数据流、LLM 提示工程、Neo4j 集成
- [OpenMAIC集成文档](docs/OPENMAIC_INTEGRATION.md) - 跨域 iframe、音频架构、播客模式、课堂已知行为
- [AuraDB配置指南](docs/AURADB_SETUP.md) - Neo4j AuraDB 云托管配置步骤
- [Neo4j迁移文档](docs/NEO4J_MIGRATION.md) - Zep → Neo4j 迁移记录（已归档）
- [PBL图谱设计](docs/PBL-graph-redesign.md) - 环形知识路径设计决策（已实现，已归档）
- [开发指南](CLAUDE.md) - AI 开发助手参考，包含架构细节和开发命令

## 🐛 常见问题

### 1. 历史记录页面查看图谱失败
**症状**: 点击"查看图谱"按钮后显示错误或无法加载

**解决方案**:
- 新项目：确保图谱已成功存储到 Neo4j（状态为"已完成"）
- 旧项目：系统会自动使用本地数据，无需 Neo4j
- 如仍有问题，检查 Neo4j 连接配置是否正确

### 2. 图谱存储超时
**症状**: 存储图谱到 Neo4j 时提示超时或失败

**解决方案**:
- 使用 Neo4j AuraDB 时，网络延迟可能较高
- 已优化超时配置（120秒连接超时）
- 如网络不稳定，建议使用本地 Neo4j（Docker）

### 3. 边引用节点不存在警告
**症状**: 后端日志显示"边的源节点不存在"或"边的目标节点不存在"

**说明**: 这是正常现象，不是错误
- LLM 可能生成引用不存在节点的边
- 系统会自动跳过这些无效边
- 不影响图谱的存储和显示

### 4. 旧项目无法查看图谱
**症状**: 某些旧项目点击"查看图谱"后不显示内容

**解决方案**:
- 系统已添加向后兼容支持
- 旧项目数据在 `project.graph_data` 中
- 新项目数据在 Neo4j 中
- 前端会自动选择合适的数据源

### 5. 学习路径视图按钮不显示
**症状**: 图谱完成后看不到全图视图/学习路径视图切换按钮

**说明**: 这是正常现象
- 仅当图谱中存在学习路径边（NEXT_STEP、REQUIRES、PREREQUISITE_OF）时才显示切换按钮
- 旧项目可能使用不同的边类型，因此可能不会显示切换按钮
- 旧项目仍然可以使用全图视图正常浏览

### 6. 虚拟课堂连接失败
**症状**: 点击"生成虚拟课堂"按钮显示"无法连接到课堂服务"

**解决方案**:
- 确认 OpenMAIC 服务已启动（端口 3001）
- 使用 `npm run dev:all` 同时启动 Evolith 和 OpenMAIC
- 检查 `.env` 中的 `OPENMAIC_BASE_URL` 和 `OPENMAIC_DIR` 配置
- 在 OpenMAIC 的 `.env.local` 中设置 `ALLOWED_FRAME_ANCESTORS=http://localhost:3000`

### 7. 虚拟课堂音频无法播放
**症状**: 进入虚拟课堂后听不到语音

**解决方案**:
- 检查跨域 iframe 的 4 项音频权限配置是否完整（详见 [docs/OPENMAIC_INTEGRATION.md](docs/OPENMAIC_INTEGRATION.md)）
- OpenMAIC 使用 AudioContext 路径播放音频，需通过用户手势 unlock
- 确保 `ALLOWED_FRAME_ANCESTORS` 包含 Evolith 的域名
- 确保 iframe 的 `allow` 属性包含 `autoplay 'src'`

### 8. 播客模式生成失败
**症状**: 选择播客模式后课堂回退为单人 TTS

**说明**: 这是自动回退机制，不影响课堂内容
- 检查 OpenMAIC 的 `.env.local` 中是否配置了 `PODCAST_VOLCENGINE_APP_ID` 和 `PODCAST_VOLCENGINE_ACCESS_KEY`
- 火山引擎播客 API 连接可能暂时不可用，系统自动回退到单人 TTS
- 播客文本长度限制：每轮 ≤300 字符，总文本 ≤10,000 字符

### 9. 课堂生成状态轮询中断
**症状**: 课堂生成进度轮询意外终止

**说明**: 系统已优化轮询容错
- 轮询最多容忍 3 次连续失败（瞬态 500 错误不再终止）
- 后端捕获 `ValueError`（含 `JSONDecodeError`），防止 Next.js HMR 重编译返回 HTML 导致 500 错误
- 课堂生成任务状态保存在 sessionStorage 中，页面刷新/HMR 会自动恢复

## 📄 许可证

本项目采用 [AGPL-3.0](LICENSE) 许可证。
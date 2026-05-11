# Evolith 功能文档

**版本**: v3.0.0
**更新日期**: 2026年4月27日
**项目定位**: PBL驱动学习路径知识图谱 + 虚拟课堂一体化平台

---

> **后端API端点**的完整请求/响应文档请参阅 [API.md](API.md)。
> **代码架构、数据流、LLM提示工程、Neo4j集成**请参阅 [ARCHITECTURE.md](ARCHITECTURE.md)。
> **OpenMAIC虚拟课堂集成**请参阅 [OPENMAIC_INTEGRATION.md](OPENMAIC_INTEGRATION.md)。
> **Neo4j AuraDB配置**请参阅 [AURADB_SETUP.md](AURADB_SETUP.md)。

---

## 一、产品概述

Evolith 是一个基于大语言模型（LLM）和 Neo4j 的**PBL驱动学习路径知识图谱 + 虚拟课堂一体化平台**。它与 OpenMAIC 虚拟课堂引擎深度集成，能够根据课程描述和文档自动构建**项目驱动+环形知识链**的学习图谱，并为每个知识点生成沉浸式 AI 虚拟课堂，让学习者通过递进式项目掌握知识、通过虚拟课堂进行实践学习。

### 核心价值

- **PBL驱动模式**：以递进式项目序列为主路径，每个项目拥有专属环形知识链和里程碑系统
- **里程碑系统**：每个项目拆分为3-5个里程碑，配有验收标准和渐进式知识推送
- **渐进式知识推送**：L1快速提示 → L2详细解释 → L3虚拟课堂，学生卡壳时AI主动推送
- **虚拟课堂生成**：每个知识点可一键生成 OpenMAIC AI 虚拟课堂，沉浸式交互学习（语音、对话、场景化教学）
- **LLM 智能图谱提取**：使用 LLM 直接从课程描述和文档提取项目与知识点图谱
- **Neo4j 图谱存储**：使用图数据库存储和检索知识，支持有向边
- **双视图可视化**：全图视图（力导向布局）和学习路径视图（分层布局）
- **学习路径侧边栏**：清晰展示项目序列和每个项目的知识链结构
- **历史记录管理**：自动保存所有项目，随时查看和管理
- **多语言支持**：支持中文和英文界面

### 核心设计理念

```
                ┌─────────────────┐
                │  分支项目B       │
                │  (intermediate)  │
                └────────┬────────┘
                         │ NEXT_STEP
                         │
┌──────────┐  NEXT_STEP  ┌──┴───────────┐  NEXT_STEP  ┌──────────────┐
│ 项目1    │────────────→│  项目2       │────────────→│  项目3       │
│(beginner)│             │  (beginner)  │             │(intermediate)│
└──┬───────┘             └──────┬───────┘             └──────┬───────┘
   │ REQUIRES                   │ REQUIRES                   │ REQUIRES
   ▼                            ▼                            ▼
┌──────────┐             ┌──────────┐                 ┌──────────┐
│ 知识点1  │             │ 知识点3  │                 │ 知识点5  │
│(beginner)│             │(beginner)│                 │(intermed)│
└────┬─────┘             └────┬─────┘                 └────┬─────┘
     │ PREREQUISITE_OF         │ PREREQUISITE_OF             │ PREREQUISITE_OF
     ▼                         ▼                             ▼
┌──────────┐             ┌──────────┐                 ┌──────────┐
│ 知识点2  │             │ 知识点4  │                 │ 知识点6  │
│(beginner)│             │(beginner)│                 │(intermed)│
└────┬─────┘             └────┬─────┘                 └────┬─────┘
     │ REQUIRES                 │ REQUIRES                    │ REQUIRES
     ▼                         ▼                             ▼
  → 项目1                    → 项目2                       → 项目3
(环形闭合：最后一条知识指回项目本身)
```

- **项目路径**：4-8 个递进式项目组成主路径，项目间通过 NEXT_STEP 连接
- **环形知识链**：每个项目拥有专属的知识点链条，从项目出发经知识点最终回到同一个项目
- **不共享知识点**：每个知识点只属于一个项目的知识链
- 每个项目和知识点都有**前置知识**和**学习成果**的明确描述

---

## 二、功能模块

### 2.1 首页 (Home)

**页面路径**: `/`

- 顶部导航栏：品牌标识、语言切换器、GitHub链接、历史项目链接
- Hero区域：产品标语和版本号
- 系统状态面板
- 交互控制台：文件上传区域（支持拖拽，可选）、课程描述输入框（必填）、"构建知识图谱"按钮
- 支持文件格式：PDF、Markdown、纯文本

### 2.2 流程页面 (Process)

**页面路径**: `/process/:projectId`

**左侧：图谱可视化面板**:
- 实时展示学习路径知识图谱，显示节点数和关系数统计
- 支持全屏模式、刷新数据、视图模式切换

**两种可视化模式**:

1. **全图视图**（力导向布局）：
   - D3.js力导向布局，学习路径边带方向箭头
   - 项目节点：较大圆角矩形；知识点节点：较小圆形
   - 节点大小按难度区分（beginner=8px, intermediate=11px, advanced=14px）
   - 主路径节点：实心粗边框；分支节点：半透明细边框

2. **学习路径视图**（分层布局）：
   - 项目主路径水平排列从左到右
   - 每个项目的知识链在项目下方或上方展开，形成环形
   - 支持缩放和平移

**边颜色编码**：

| 边类型 | 颜色 | 说明 |
|--------|------|------|
| NEXT_STEP | #2D3436（黑色粗线） | 项目间的顺序关系 |
| REQUIRES | #7B2D8E（紫色） | 项目与知识点的依赖关系 |
| PREREQUISITE_OF | #FF6B35（橙色） | 知识点之间的前置条件依赖 |
| 其他边 | #ccc（浅灰色） | 非学习路径边 |

**交互功能**：拖拽节点、点击查看详情、缩放/平移、全屏切换、视图模式切换（仅当存在学习路径边时显示）

**详情面板**：
- 节点类型徽章（项目/知识点）、难度级别徽章、学习顺序编号
- 前置知识摘要、学习成果摘要、所属项目（required_by，知识点节点）
- UUID、属性、摘要、标签、创建时间

**右侧：工作台面板**:
- 步骤01：图谱提取（POST /api/graph/extract）
- 步骤02：图谱存储（POST /api/graph/store）
- 步骤03：完成 — 自动加载图谱和学习路径数据

**学习路径侧边栏**:
- 有序项目序列列表（带编号、名称、难度徽章）
- 每个项目下方展示知识链（可折叠），末尾显示环形闭合指示符 ⟳
- 分支项目区域
- 点击聚焦到图谱中对应节点

**虚拟课堂按钮**（仅知识点节点）:
- 有 classroom_id → 绿色按钮 → 直接进入
- 无 classroom_id → 紫色按钮 → 生成流程 → 详见 [OPENMAIC_INTEGRATION.md](OPENMAIC_INTEGRATION.md)
- 播客模式选项：生成课堂时可选择"课堂模式"（单人TTS）或"播客模式"（双人对话音频）
- 播客声音配对可选：咪仔+大意（mizai-dayi）、刘飞+潇磊（liufei-xiaolei）

### 2.3 历史记录 (History)

**页面路径**: `/history`

- 网格布局显示所有项目，显示项目状态、名称、ID、创建时间、文件数量
- "查看图谱"：仅 `graph_completed` 状态可查看
- "删除项目"：带确认对话框
- 状态指示：已完成（绿色）、进行中（橙色）、等待中（灰色）、失败（红色）
- 空状态友好提示

**项目状态说明**：

| 状态 | 说明 | 可执行操作 |
|------|------|-----------|
| `graph_completed` | 图谱已存储到 Neo4j | 查看图谱、删除 |
| `graph_extracted` | LLM已提取图谱数据 | 存储到Neo4j、删除 |
| `created` | 项目已创建 | 删除 |
| `failed` | 构建失败 | 删除 |

旧项目使用 `ontology_generated` / `graph_building` 状态，系统自动映射到新状态。

### 2.4 语言切换

- 支持中文 (zh) 和英文 (en)
- 实时切换界面语言
- 自动保存用户选择到 localStorage

### 2.5 虚拟课堂 (Classroom)

**页面路径**: `/classroom/:classroomId`

全屏沉浸式虚拟课堂页面，通过 iframe 嵌入 OpenMAIC 生成的 AI 课堂内容。
完整文档请参阅 [OPENMAIC_INTEGRATION.md](OPENMAIC_INTEGRATION.md)。

**播客模式**:
- 播客模式下，课堂内容不变（保留幻灯片、测验等结构）
- 语音从单人TTS变为双人播客对话（Volcengine Podcast TTS API）
- 笔记区域显示每轮对话文字内容（带说话人标识）
- 播客音频连续播放，基于时间轴的字幕和说话人头像同步

### 2.6 PBL项目工作台 (ProjectWorkbench)

**页面路径**: `/workbench/:projectId`

PBL学习核心页面，学生在项目工作台中完成里程碑任务，遇到卡壳时AI推送知识点。

**入口**：知识图谱页面点击 Project 节点 → "进入 PBL 学习"按钮

**左侧：里程碑侧边栏**:
- 里程碑列表，按顺序排列
- 每个里程碑显示序号、名称、完成状态
- 状态：已完成（绿色对勾）、进行中（橙色）、未开始（灰色锁定）
- 点击切换当前里程碑

**中间：工作区域**:
- 里程碑描述
- 验收标准清单
- 关联知识点卡片列表：
  - 每张卡片显示：知识点名称、难度徽章、摘要
  - 未生成课堂 → 橙色"生成虚拟课堂"按钮
  - 已生成课堂 → 绿色"进入虚拟课堂"按钮
  - 点击卡片打开提示面板
- 学习笔记输入区（自动保存到 localStorage）
- "标记完成"按钮

**右侧：提示面板（HintPanel，抽屉式）**:
- L1 快速提示：2-3 句话点拨
- L2 详细解释：含示例的深入讲解
- L3 虚拟课堂：跳转到 OpenMAIC 课堂
- 渐进式解锁：先 L1，"还是不懂"解锁 L2，"我要课堂"进入 L3

**进度持久化**:
- 里程碑完成状态、学习笔记、提示使用次数均保存在 localStorage
- 刷新页面不丢失进度

---

## 三、数据模型

### 3.1 项目 (Project)

| 字段 | 类型 | 说明 |
|------|------|------|
| `project_id` | String | 项目唯一标识 |
| `name` | String | 项目名称 |
| `status` | ProjectStatus | 项目状态枚举 |
| `created_at` | String | 创建时间 |
| `updated_at` | String | 更新时间 |
| `files` | List[Dict] | 文件列表 |
| `total_text_length` | int | 总文本长度 |
| `graph_data` | Optional[Dict] | LLM提取的图谱数据 |
| `node_count` | int | 节点数量 |
| `edge_count` | int | 边数量 |
| `course_description` | Optional[String] | 课程描述 |

### 3.2 项目状态 (ProjectStatus)

| 枚举值 | 说明 |
|--------|------|
| `CREATED` | 项目已创建 |
| `GRAPH_EXTRACTED` | 图谱已提取 |
| `GRAPH_COMPLETED` | 图谱已存储到 Neo4j |
| `FAILED` | 失败 |

向后兼容：`ontology_generated` → `GRAPH_EXTRACTED`，`graph_building` → `GRAPH_COMPLETED`

### 3.3 学习路径节点属性

**项目节点 (Project)**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `difficulty` | String | 难度："beginner"/"intermediate"/"advanced" |
| `learning_order` | Integer | 学习顺序编号 |
| `prerequisites_summary` | String | 完成项目前需掌握什么 |
| `outcomes_summary` | String | 完成项目后能做什么 |

**知识点节点 (KnowledgePoint)**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `difficulty` | String | 难度级别 |
| `learning_order` | Integer | 在所属项目知识链中的位置 |
| `prerequisites_summary` | String | 学习前需掌握什么 |
| `outcomes_summary` | String | 学完后能做什么 |
| `required_by` | String | 所属项目名称 |
| `classroom_id` | String | 关联的虚拟课堂ID（首次生成后缓存） |

**里程碑节点 (Milestone)**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | String | 里程碑名称 |
| `description` | String | 里程碑描述 |
| `acceptance_criteria` | String | 验收标准 |
| `order` | Integer | 里程碑顺序（从1开始） |
| `project_uuid` | String | 所属项目UUID |

### 3.4 学习路径边类型

| 边类型 | 方向 | 颜色 | 说明 |
|--------|------|------|------|
| `NEXT_STEP` | 项目→项目 | #2D3436（黑色粗线） | 项目间顺序关系 |
| `REQUIRES` | 项目↔知识点 | #7B2D8E（紫色） | 项目与知识点依赖（环形闭合） |
| `PREREQUISITE_OF` | 知识点→知识点 | #FF6B35（橙色） | 知识点前置条件依赖 |
| `MILESTONE_STEP` | 项目→里程碑 | — | 里程碑与项目的归属关系（带 order 属性） |
| `MILESTONE_REQUIRES` | 里程碑→知识点 | — | 里程碑所需的知识点 |

---

## 四、技术栈

### 前端
- Vue 3 (Composition API)、Vue Router 4、Vue I18n、Axios、D3.js

### 后端
- Flask 3.1、Flask-CORS、Neo4j >= 5.0.0、OpenAI SDK、requests（含 ValueError/JSONDecodeError 容错处理）、PyMuPDF、uv

---

## 五、工作流程

### 新项目构建
```
用户输入课程描述（可选上传文档）
  → 前端跳转到 /process/new
  → POST /api/graph/extract（LLM提取PBL驱动图谱）
  → POST /api/graph/store（有向边存储到 Neo4j）
  → GET /api/graph/data + learning-path → D3.js可视化
```

### 历史记录查看
```
用户访问 /history → GET /api/graph/project/list
  → 展示项目卡片网格
  → 点击"查看图谱" → /process/{project_id}
  → GET project + graph data + learning path → D3.js可视化
```

---

## 六、已知行为与限制

1. **边引用节点不存在**：LLM可能生成引用不存在节点的边，系统自动跳过并记录WARNING日志
2. **PREREQUISITE_OF环检测**：系统自动检测并移除成环的边，确保学习路径保持DAG
3. **向后兼容**：旧项目（无Project标签）自动使用知识驱动模式；无difficulty属性使用默认大小；无学习路径边时不显示视图切换按钮
4. **文件大小限制**：最大50MB单文件，推荐<10MB
5. **文本长度限制**：图谱提取最长50,000字符
6. **Neo4j网络延迟**：AuraDB云服务连接可能断开，后端已优化 `max_connection_lifetime=300s`，写入操作有2次重试+Driver重置机制
7. **课堂生成时间**：5-10分钟，前端每5秒轮询，无超时上限，持续轮询直到 completed/failed — 详见 [OPENMAIC_INTEGRATION.md](OPENMAIC_INTEGRATION.md)
8. **播客模式**：播客模式需要配置 `PODCAST_VOLCENGINE_APP_ID` 和 `PODCAST_VOLCENGINE_ACCESS_KEY`（OpenMAIC 端 .env.local）。未配置时自动回退到单人TTS。
9. **播客文本长度**：每轮对话不超过300字符，总文本不超过10,000字符，超长自动切分。
10. **课堂ID缓存**：课堂生成成功后 `classroom_id` 写入 Neo4j 节点属性，前端以 fire-and-forget 方式调用，不阻塞课堂导航。缓存失败不影响课堂使用，但图谱上不会显示"进入课堂"按钮。
11. **里程碑知识点分配**：如果 LLM 提取时未生成 MILESTONE_REQUIRES 边，后端自动按 `learning_order` 将知识点均匀分配到各里程碑。

---

**文档维护**: Evolith 开发团队
**最后更新**: 2026年4月27日
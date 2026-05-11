# Evolith API 接口文档

**版本**: v6.0.0
**更新日期**: 2026年4月27日
**Base URL**: `http://localhost:5001/api/graph`（图谱接口）、`http://localhost:5001/api/classroom`（课堂接口）、`http://localhost:5001/api/hint`（提示接口）

---

## 目录

- [接口说明](#接口说明)
- [项目管理接口](#项目管理接口)
- [图谱提取接口](#图谱提取接口)
- [图谱存储接口](#图谱存储接口)
- [图谱数据接口](#图谱数据接口)
- [学习路径接口](#学习路径接口)
- [里程碑接口](#里程碑接口)
- [学习提示接口](#学习提示接口)
- [虚拟课堂接口](#虚拟课堂接口)
- [健康检查](#健康检查)
- [错误码说明](#错误码说明)

---

## 接口说明

### 通用响应格式

所有接口都遵循以下统一响应格式：

#### 成功响应
```json
{
  "success": true,
  "data": { /* 具体数据 */ }
}
```

#### 失败响应
```json
{
  "success": false,
  "error": "错误描述信息"
}
```

### 国际化支持

部分错误信息支持国际化，根据请求头 `Accept-Language` 返回对应语言：
- `zh`: 中文
- `en`: 英文

---

## 项目管理接口

### 1. 获取项目列表

**接口地址**: `GET /api/graph/project/list`

**功能描述**: 获取所有已保存的项目列表，按创建时间倒序排列

**查询参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| limit | Integer | 否 | 50 | 返回项目数量上限 |

**请求示例**:
```bash
GET /api/graph/project/list?limit=20
```

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "project_id": "proj_123456",
      "name": "未命名项目",
      "status": "graph_completed",
      "created_at": "2026-04-18T12:44:58",
      "updated_at": "2026-04-18T12:49:19",
      "files": [
        {
          "filename": "machine_learning.pdf",
          "size": 102400
        }
      ],
      "total_text_length": 2822,
      "course_description": "机器学习基础课程",
      "file_count": 1
    }
  ],
  "count": 1
}
```

---

### 2. 获取项目详情

**接口地址**: `GET /api/graph/project/{project_id}`

**功能描述**: 获取单个项目的详细信息

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 项目ID |

**请求示例**:
```bash
GET /api/graph/project/proj_123456
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "project_id": "proj_123456",
    "name": "机器学习课程",
    "status": "graph_completed",
    "created_at": "2026-04-18T12:44:58",
    "updated_at": "2026-04-18T12:49:19",
    "files": [
      {
        "filename": "course.pdf",
        "size": 204800
      }
    ],
    "total_text_length": 2822,
    "analysis_summary": "课程包含机器学习的核心概念和方法",
    "course_description": "机器学习基础课程",
    "error": null
  }
}
```

---

### 3. 删除项目

**接口地址**: `DELETE /api/graph/project/{project_id}`

**功能描述**: 删除指定项目及其所有相关数据（文件、图谱等）

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 项目ID |

**请求示例**:
```bash
DELETE /api/graph/project/proj_123456
```

**响应示例**:
```json
{
  "success": true,
  "message": "项目 proj_123456 已删除"
}
```

---

### 4. 重置项目

**接口地址**: `POST /api/graph/project/{project_id}/reset`

**功能描述**: 重置项目状态，清除图谱数据，保留项目信息和课程描述

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 项目ID |

**请求示例**:
```bash
POST /api/graph/project/proj_123456/reset
```

**响应示例**:
```json
{
  "success": true,
  "message": "项目 proj_123456 已重置",
  "data": {
    "project_id": "proj_123456",
    "status": "created"
  }
}
```

**状态说明**:
- 重置后项目状态恢复为 `created`
- 图谱数据（graph_data）和统计信息会被清空
- 项目文件和课程描述保留

---

## 图谱提取接口

### 5. 提取图谱

**接口地址**: `POST /api/graph/extract`

**功能描述**: 上传课程文档（可选）和课程描述，使用 LLM 直接提取 PBL 驱动的图谱节点和边数据

**请求方式**: `multipart/form-data`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| files | File[] | 否 | 上传的文件（支持 PDF、MD、TXT），可多个；仅提供课程描述也可提取图谱 |
| course_description | String | 是 | 课程描述，用于指导 LLM 提取图谱 |
| project_name | String | 否 | 项目名称，默认 "Unnamed Project" |

**文件格式支持**:
- PDF: `.pdf`
- Markdown: `.md`, `.markdown`
- 纯文本: `.txt`
- 单文件最大大小: 50MB

**请求示例** (JavaScript):
```javascript
const formData = new FormData()
formData.append('files', file1)
formData.append('files', file2)
formData.append('course_description', '机器学习基础课程')
formData.append('project_name', 'ML课程')

fetch('/api/graph/extract', {
  method: 'POST',
  body: formData
})
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "project_id": "proj_123456",
    "project_name": "ML课程",
    "graph_data": {
      "nodes": [
        {
          "uuid": "proj_001",
          "name": "构建线性回归模型",
          "labels": ["Entity", "Project"],
          "summary": "通过构建线性回归模型，学习监督学习的基础知识",
          "attributes": {
            "difficulty": "beginner",
            "learning_order": 1,
            "prerequisites_summary": "需要了解基础数学概念",
            "outcomes_summary": "可以独立构建和评估线性回归模型"
          }
        },
        {
          "uuid": "node_001",
          "name": "线性回归原理",
          "labels": ["Entity", "KnowledgePoint"],
          "summary": "线性回归是一种用于预测连续值的监督学习算法",
          "attributes": {
            "difficulty": "beginner",
            "learning_order": 1,
            "prerequisites_summary": "需要了解基础数学概念",
            "outcomes_summary": "可以理解和应用线性回归模型",
            "required_by": "构建线性回归模型"
          }
        }
      ],
      "edges": [
        {
          "uuid": "edge_001",
          "source_node_uuid": "proj_001",
          "target_node_uuid": "node_001",
          "fact_type": "REQUIRES",
          "fact": "构建回归模型需要先学习线性回归原理"
        },
        {
          "uuid": "edge_002",
          "source_node_uuid": "node_001",
          "target_node_uuid": "proj_001",
          "fact_type": "REQUIRES",
          "fact": "学完线性回归原理后，回到回归模型项目进行实践"
        },
        {
          "uuid": "edge_003",
          "source_node_uuid": "proj_001",
          "target_node_uuid": "proj_002",
          "fact_type": "NEXT_STEP",
          "fact": "完成线性回归模型后，进入逻辑回归项目"
        },
        {
          "uuid": "edge_004",
          "source_node_uuid": "node_001",
          "target_node_uuid": "node_002",
          "fact_type": "PREREQUISITE_OF",
          "fact": "线性回归原理是梯度下降的前置知识"
        }
      ]
    },
    "analysis_summary": "课程采用PBL驱动结构，构建递进式项目序列，每个项目配备环形知识路径",
    "node_count": 30,
    "edge_count": 48,
    "files": [
      {
        "filename": "machine_learning.pdf",
        "size": 102400
      }
    ],
    "total_text_length": 2822
  }
}
```

**说明**:
- `nodes`: 节点列表，每个节点包含 uuid, name, labels, summary, attributes
  - 节点类型只有两种：**Project**（labels: `["Entity", "Project"]`）和 **KnowledgePoint**（labels: `["Entity", "KnowledgePoint"]`）
  - 不使用 Concept/Method/Tool 等具体类型标签，知识点统一使用 KnowledgePoint
  - 每个节点的 attributes 必须包含 `difficulty`、`learning_order`
  - 推荐包含 `prerequisites_summary` 和 `outcomes_summary`
  - KnowledgePoint 节点推荐包含 `required_by`（所属项目名称）
- `edges`: 边列表，每条边包含 uuid, source_node_uuid, target_node_uuid, fact_type, fact
  - **只使用 3 种边类型**：
    - `NEXT_STEP`：项目间的顺序关系（Project -> Project）
    - `REQUIRES`：项目与知识点的关系（双向：Project -> KP 为链起点，KP -> Project 为链终点/环形闭合）
    - `PREREQUISITE_OF`：知识点之间的前置依赖（KnowledgePoint -> KnowledgePoint）
  - 已废弃的边类型：BUILDS_ON、ENABLES、PARALLEL_WITH、BRANCHES_FROM、MERGES_TO
  - REQUIRES 边占比应 > 40%
  - 每个项目至少有 2 条 REQUIRES 边（起点 + 终点，形成环形知识路径）
- `analysis_summary`: LLM 分析的摘要
- `node_count` / `edge_count`: 节点和边的数量

---

## 图谱存储接口

### 6. 存储图谱

**接口地址**: `POST /api/graph/store`

**功能描述**: 将提取的图谱数据存储到 Neo4j 数据库

**请求方式**: `application/json`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 项目ID，来自提取图谱接口 |

**请求示例**:
```javascript
{
  "project_id": "proj_123456"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "project_id": "proj_123456",
    "node_count": 30,
    "edge_count": 48,
    "message": "图谱已存储到 Neo4j"
  }
}
```

**同步处理说明**:
- 这是一个同步操作，等待图谱存储完成后返回
- 存储时间取决于节点和边的数量
- 通常在 1-10 秒内完成

**状态限制**:
- 项目状态必须是 `graph_extracted` 才能开始存储
- 如果状态已经是 `graph_completed`，直接返回成功
- 如果存储失败，项目状态会变为 `failed`

---

## 图谱数据接口

### 7. 获取图谱数据

**接口地址**: `GET /api/graph/data/{graph_id}`

**功能描述**: 获取知识图谱的节点和边数据，用于前端可视化

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| graph_id | String | 是 | 图谱ID（即 project_id） |

**请求示例**:
```bash
GET /api/graph/data/proj_123456
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "graph_id": "proj_123456",
    "node_count": 45,
    "edge_count": 82,
    "nodes": [
      {
        "uuid": "proj_uuid_001",
        "name": "构建线性回归模型",
        "labels": ["Entity", "Project"],
        "summary": "通过构建线性回归模型，学习监督学习的基础知识",
        "attributes": {
          "difficulty": "beginner",
          "learning_order": 1,
          "prerequisites_summary": "需要了解基础数学概念",
          "outcomes_summary": "可以独立构建和评估线性回归模型"
        },
        "created_at": "2026-04-21T12:49:19"
      },
      {
        "uuid": "node_uuid_001",
        "name": "线性回归原理",
        "labels": ["Entity", "KnowledgePoint"],
        "summary": "线性回归是一种用于预测连续值的算法",
        "attributes": {
          "difficulty": "beginner",
          "learning_order": 1,
          "prerequisites_summary": "需要了解基础数学概念",
          "outcomes_summary": "可以理解和应用线性回归模型",
          "required_by": "构建线性回归模型"
        },
        "created_at": "2026-04-21T12:49:19"
      }
    ],
    "edges": [
      {
        "uuid": "edge_uuid_001",
        "name": "REQUIRES",
        "fact_type": "REQUIRES",
        "source_node_uuid": "proj_uuid_001",
        "target_node_uuid": "node_uuid_001",
        "source_node_name": "构建线性回归模型",
        "target_node_name": "线性回归原理",
        "fact": "构建回归模型需要先学习线性回归原理",
        "created_at": "2026-04-21T12:49:20"
      },
      {
        "uuid": "edge_uuid_002",
        "name": "PREREQUISITE_OF",
        "fact_type": "PREREQUISITE_OF",
        "source_node_uuid": "node_uuid_002",
        "target_node_uuid": "node_uuid_001",
        "source_node_name": "基础数学",
        "target_node_name": "线性回归原理",
        "fact": "线性回归需要基础数学知识",
        "created_at": "2026-04-21T12:49:20"
      }
    ]
  }
}
```

**节点数据结构**:

| 字段 | 类型 | 说明 |
|------|------|------|
| uuid | String | 节点唯一标识 |
| name | String | 节点名称 |
| labels | String[] | 标签列表（Project 节点: `["Entity", "Project"]`；KnowledgePoint 节点: `["Entity", "KnowledgePoint"]`） |
| summary | String | 节点摘要 |
| attributes | Object | 节点属性（键值对） |
| attributes.difficulty | String | 难度级别："beginner" / "intermediate" / "advanced" |
| attributes.learning_order | Integer | 学习顺序编号 |
| attributes.prerequisites_summary | String | 学习前置知识摘要 |
| attributes.outcomes_summary | String | 学习成果摘要 |
| attributes.required_by | String | （仅 KnowledgePoint）所属项目名称 |
| attributes.classroom_id | String | （仅 KnowledgePoint）已生成的虚拟课堂ID，null 表示未生成 |
| created_at | String | 创建时间（ISO 8601） |

**边数据结构**:

| 字段 | 类型 | 说明 |
|------|------|------|
| uuid | String | 边唯一标识 |
| name | String | 关系类型（与 fact_type 相同） |
| fact_type | String | 关系类型 |
| source_node_uuid | String | 源节点UUID |
| target_node_uuid | String | 目标节点UUID |
| source_node_name | String | 源节点名称 |
| target_node_name | String | 目标节点名称 |
| fact | String | 关系事实描述 |
| created_at | String | 创建时间（ISO 8601） |

**特殊说明**:
- 如果 Neo4j 中没有数据，返回 404 状态码
- 对于旧项目（Neo4j 迁移前），前端会使用本地数据作为回退
- 前端已处理此情况，不会显示错误给用户

---

### 8. 删除图谱

**接口地址**: `DELETE /api/graph/delete/{graph_id}`

**功能描述**: 删除 Neo4j 中的图谱数据

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| graph_id | String | 是 | 图谱ID（即 project_id） |

**请求示例**:
```bash
DELETE /api/graph/delete/proj_123456
```

**响应示例**:
```json
{
  "success": true,
  "message": "图谱 proj_123456 已删除"
}
```

**注意**:
- 此接口只删除 Neo4j 中的图谱数据
- 项目元数据（`project.json`、文件等）不会被删除
- 如需完全删除项目，请使用删除项目接口

---

## 学习路径接口

### 9. 获取学习路径结构

**接口地址**: `GET /api/graph/learning-path/{project_id}`

**功能描述**: 获取项目的学习路径结构信息，自动检测 PBL 模式或知识驱动模式，返回对应的结构化数据

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 项目ID |

**请求示例**:
```bash
GET /api/graph/learning-path/proj_123456
```

**响应示例**:

#### PBL 模式（存在 Project 节点时）

```json
{
  "success": true,
  "data": {
    "mode": "pbl",
    "main_path": [
      "proj_uuid_001",
      "proj_uuid_002",
      "proj_uuid_003",
      "proj_uuid_005",
      "proj_uuid_008"
    ],
    "branch_projects": [
      "proj_uuid_010"
    ],
    "project_knowledge_subgraphs": {
      "proj_uuid_001": {
        "knowledge_chain": [
          "node_uuid_001",
          "node_uuid_002"
        ],
        "entry_points": [
          "node_uuid_001"
        ],
        "exit_points": [
          "node_uuid_002"
        ],
        "ring_closed": true
      },
      "proj_uuid_002": {
        "knowledge_chain": [
          "node_uuid_003",
          "node_uuid_004",
          "node_uuid_006"
        ],
        "entry_points": [
          "node_uuid_003"
        ],
        "exit_points": [
          "node_uuid_006"
        ],
        "ring_closed": true
      }
    },
    "entry_points": [
      "proj_uuid_001"
    ],
    "exit_points": [
      "proj_uuid_008"
    ],
    "learning_stages": {
      "beginner": ["proj_uuid_001", "proj_uuid_002", "node_uuid_001", "node_uuid_002"],
      "intermediate": ["proj_uuid_003", "proj_uuid_005", "node_uuid_003", "node_uuid_004"],
      "advanced": ["proj_uuid_008", "node_uuid_006"]
    }
  }
}
```

#### 知识驱动模式（向后兼容，不存在 Project 节点时）

```json
{
  "success": true,
  "data": {
    "mode": "knowledge_driven",
    "main_path": [
      "node_uuid_001",
      "node_uuid_002",
      "node_uuid_003",
      "node_uuid_005",
      "node_uuid_008"
    ],
    "branch_paths": [
      {
        "branch_id": "branch_1",
        "from_node_uuid": "node_uuid_002",
        "branch_nodes": [
          "node_uuid_004",
          "node_uuid_006"
        ],
        "merge_to_uuid": "node_uuid_005"
      },
      {
        "branch_id": "branch_2",
        "from_node_uuid": "node_uuid_003",
        "branch_nodes": [
          "node_uuid_007"
        ],
        "merge_to_uuid": null
      }
    ],
    "entry_points": [
      "node_uuid_001"
    ],
    "exit_points": [
      "node_uuid_008"
    ],
    "learning_stages": {
      "beginner": ["node_uuid_001", "node_uuid_002"],
      "intermediate": ["node_uuid_003", "node_uuid_005"],
      "advanced": ["node_uuid_008"]
    }
  }
}
```

**PBL 模式数据结构说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| mode | String | 模式标识，值为 `"pbl"` |
| main_path | String[] | 主路径项目UUID有序列表（由 NEXT_STEP 边连接的 Project 序列） |
| branch_projects | String[] | 不在主路径上的分支项目UUID列表 |
| project_knowledge_subgraphs | Object | 每个项目的环形知识路径子图 |
| project_knowledge_subgraphs[proj_uuid].knowledge_chain | String[] | 项目专属知识链的 KnowledgePoint UUID 有序列表 |
| project_knowledge_subgraphs[proj_uuid].entry_points | String[] | 知识链入口知识点（无 PREREQUISITE_OF 入边的 KP） |
| project_knowledge_subgraphs[proj_uuid].exit_points | String[] | 知识链出口知识点（无 PREREQUISITE_OF 出边的 KP，通过 REQUIRES 边环形闭合回项目） |
| project_knowledge_subgraphs[proj_uuid].ring_closed | Boolean | 知识链是否形成环形闭合（最后 KP 通过 REQUIRES 边指回项目） |
| entry_points | String[] | 整体入口点（主路径第一个项目） |
| exit_points | String[] | 整体出口点（主路径最后一个项目） |
| learning_stages | Object | 按难度分组的所有节点UUID列表（包含 Project 和 KnowledgePoint） |

**知识驱动模式数据结构说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| mode | String | 模式标识，值为 `"knowledge_driven"` |
| main_path | String[] | 主路径节点UUID有序列表 |
| branch_paths | Object[] | 分支路径列表 |
| branch_paths[].branch_id | String | 分支标识 |
| branch_paths[].from_node_uuid | String | 分支起点（主路径节点UUID） |
| branch_paths[].branch_nodes | String[] | 分支路径上的节点UUID列表 |
| branch_paths[].merge_to_uuid | String\|null | 分支汇回的主路径节点UUID（null表示不汇回） |
| entry_points | String[] | 入口点（无前置知识的节点） |
| exit_points | String[] | 出口点（无后续PREREQUISITE_OF出边的节点） |
| learning_stages | Object | 按难度分组的节点UUID列表 |

**特殊说明**:
- 接口会自动检测模式：如果图谱中存在 Project 节点，返回 PBL 模式；否则返回知识驱动模式
- PBL 模式下，如果主路径为空，返回 404 状态码
- 知识驱动模式下，如果主路径和分支路径都为空，返回 404 状态码
- 旧项目（没有 Project 标签的项目）自动使用知识驱动模式，保持向后兼容
- 服务器内部错误返回 500 状态码

---

## 里程碑接口

### 9. 获取项目里程碑

**接口地址**: `GET /api/graph/milestones/{project_id}`

**功能描述**: 获取项目的里程碑列表及每个里程碑关联的知识点（含 `classroom_id`），用于 PBL 工作台展示

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 项目ID |

**请求示例**:
```bash
GET /api/graph/milestones/proj_123456
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "project_id": "proj_123456",
    "project_name": "构建线性回归模型",
    "milestones": [
      {
        "uuid": "ms_uuid_001",
        "name": "理解线性回归概念",
        "description": "学习线性回归的基本概念和数学公式",
        "acceptance_criteria": "能够解释线性回归的数学表达和损失函数",
        "order": 1,
        "project_uuid": "proj_uuid_001",
        "knowledge_points": [
          {
            "uuid": "node_uuid_001",
            "name": "线性回归原理",
            "difficulty": "beginner",
            "summary": "线性回归是一种用于预测连续值的监督学习算法",
            "classroom_id": "classroom_abc123"
          },
          {
            "uuid": "node_uuid_002",
            "name": "损失函数",
            "difficulty": "intermediate",
            "summary": "均方误差是线性回归最常用的损失函数",
            "classroom_id": null
          }
        ]
      }
    ]
  }
}
```

**知识点数据结构**:

| 字段 | 类型 | 说明 |
|------|------|------|
| uuid | String | 知识点节点UUID |
| name | String | 知识点名称 |
| difficulty | String | 难度："beginner" / "intermediate" / "advanced" |
| summary | String | 知识点摘要 |
| classroom_id | String\|null | 已生成的虚拟课堂ID（null 表示未生成） |

**说明**:
- 里程碑按 `order` 排序
- 知识点通过 `MILESTONE_REQUIRES` 边关联到里程碑
- 如果里程碑没有直接关联的知识点（缺少 `MILESTONE_REQUIRES` 边），后端会自动按 `learning_order` 将项目的所有知识点均匀分配到里程碑
- `classroom_id` 可用于判断是否显示"进入课堂"或"生成课堂"按钮

---

## 学习提示接口

### 10. 生成学习提示

**接口地址**: `POST /api/hint/generate`

**功能描述**: 为里程碑生成 L1（快速提示）或 L2（详细解释）学习提示，用于 PBL 工作台的渐进式知识推送

**请求方式**: `application/json`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 项目ID |
| milestone_uuid | String | 是 | 里程碑UUID |
| level | Integer | 是 | 提示级别：1 = 快速提示（2-3句话），2 = 详细解释（含示例） |

**请求示例**:
```json
{
  "project_id": "proj_123456",
  "milestone_uuid": "ms_uuid_001",
  "level": 1
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "hint_content": "线性回归的核心思想是找到一条直线，使得所有数据点到这条直线的距离之和最小。想想如何用数学方式表达这个「距离之和最小」的目标？",
    "level": 1,
    "milestone_uuid": "ms_uuid_001",
    "knowledge_points": [
      {
        "uuid": "node_uuid_001",
        "name": "线性回归原理",
        "difficulty": "beginner",
        "summary": "线性回归是一种用于预测连续值的监督学习算法"
      }
    ]
  }
}
```

**错误响应**:

| HTTP 状态码 | 说明 |
|-------------|------|
| 400 | 缺少 project_id、milestone_uuid，或 level 不是 1 或 2 |
| 404 | 项目或里程碑不存在 |
| 500 | 提示生成失败（LLM 调用异常） |

---

## 虚拟课堂接口

虚拟课堂接口用于与 OpenMAIC 虚拟课堂服务集成，Evolith 后端作为代理转发请求。仅知识点（KnowledgePoint）节点支持课堂生成。

**Base URL**: `/api/classroom`

### 11. 生成虚拟课堂

**接口地址**: `POST /api/classroom/generate`

**功能描述**: 为指定知识点生成虚拟课堂。如果该知识点已有关联的课堂（classroom_id 已缓存），直接返回课堂ID；否则向 OpenMAIC 发起生成请求。

**请求方式**: `application/json`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 项目ID |
| node_uuid | String | 是 | 知识点节点UUID |
| podcast_mode | String | 否 | 课堂模式参数。None=课堂模式（默认），'podcast'=播客模式（双人对话音频） |
| podcast_speaker_pair | String | 否 | 播客声音配对，默认'mizai-dayi'。可选：'mizai-dayi'（咪仔同学+大意先生）、'liufei-xiaolei'（刘飞+潇磊） |

**请求示例**:
```json
{
  "project_id": "proj_123456",
  "node_uuid": "node_uuid_001",
  "podcast_mode": "podcast",
  "podcast_speaker_pair": "mizai-dayi"
}
```

**响应示例**:

课堂已缓存时（直接返回）：
```json
{
  "status": "ready",
  "classroom_id": "classroom_abc123"
}
```

课堂生成中时（需要轮询）：
```json
{
  "job_id": "job_xyz789",
  "status": "generating",
  "poll_interval_ms": 5000
}
```

**说明**:
- 接口会首先查询 Neo4j 节点是否已有 `classroom_id` 属性，有则直接返回
- 没有缓存时，从 Neo4j 获取节点详情，组装 `requirement` 字符串（包含知识点名称、难度、前置知识、学习成果、所属项目、摘要），发送给 OpenMAIC
- 当 `podcast_mode='podcast'` 时，Evolith 传递 `enablePodcast=true` 和 `podcastSpeakerPair` 给 OpenMAIC。OpenMAIC 使用火山引擎播客 TTS API 生成双人对话音频，而非单人 TTS。如果播客生成失败，会回退到常规 TTS
- OpenMAIC 返回 `jobId`（camelCase），后端透明转换为 `job_id` 返回
- OpenMAIC 返回 `pollIntervalMs`，后端透明转换为 `poll_interval_ms`
- 生成过程可能需要数分钟，前端应使用轮询机制查询状态

**错误响应**:

| HTTP 状态码 | 说明 |
|-------------|------|
| 400 | 缺少 project_id 或 node_uuid |
| 404 | 节点不存在 |
| 502 | OpenMAIC 返回错误 |
| 502 | OpenMAIC 返回非JSON响应（如Next.js HMR重编译时的HTML页面） |
| 503 | 无法连接到 OpenMAIC（服务未启动） |
| 504 | 请求 OpenMAIC 超时 |

---

### 12. 查询课堂生成状态

**接口地址**: `GET /api/classroom/status/{job_id}`

**功能描述**: 轮询课堂生成任务的状态。OpenMAIC 的状态会被映射为 Evolith 的标准状态。

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| job_id | String | 是 | 生成任务ID |

**请求示例**:
```bash
GET /api/classroom/status/job_xyz789
```

**响应示例**:

处理中：
```json
{
  "status": "processing",
  "progress": 45
}
```

生成完成：
```json
{
  "status": "completed",
  "classroom_id": "classroom_abc123"
}
```

生成失败：
```json
{
  "status": "failed",
  "error": "课堂生成失败"
}
```

**状态映射**:

| OpenMAIC 状态 | Evolith 状态 | 说明 |
|---------------|-------------|------|
| `queued` | `processing` | 排队中 |
| `running` | `processing` | 生成中 |
| `succeeded` | `completed` | 生成完成 |
| `failed` | `failed` | 生成失败 |

**说明**:
- 建议轮询间隔使用生成接口返回的 `poll_interval_ms`（通常 5000ms）
- 生成完成后，前端应调用缓存接口将 `classroom_id` 写入 Neo4j
- `progress` 为 OpenMAIC 返回的进度值（0-100）

---

### 13. 缓存课堂ID

**接口地址**: `POST /api/classroom/cache`

**功能描述**: 将生成完成的课堂ID缓存到 Neo4j 节点属性中，后续访问同一知识点时可跳过生成步骤直接进入课堂。

**请求方式**: `application/json`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 项目ID |
| node_uuid | String | 是 | 知识点节点UUID |
| classroom_id | String | 是 | 课堂ID |

**请求示例**:
```json
{
  "project_id": "proj_123456",
  "node_uuid": "node_uuid_001",
  "classroom_id": "classroom_abc123"
}
```

**响应示例**:
```json
{
  "status": "ok"
}
```

**说明**:
- 使用 `update_node_attribute` 方法将 `classroom_id` 写入 Neo4j 节点属性
- 属性键名经过 `SAFE_KEY_PATTERN` 验证，防止 Cypher 注入
- 写入操作有 2 次重试机制：首次失败时重置 Neo4j Driver 连接，再试一次（应对 AuraDB 连接断开）
- 缓存后，再次对该知识点调用生成接口将直接返回 `status: "ready"`
- 前端以 fire-and-forget 方式调用此接口，不阻塞课堂导航

---

## 健康检查

### 14. 系统健康检查

**接口地址**: `GET /health`

**功能描述**: 检查后端服务是否正常运行

**请求示例**:
```bash
GET /health
```

**响应示例**:
```json
{
  "service": "Evolith Backend",
  "status": "ok"
}
```

---

## 错误码说明

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源未找到 |
| 500 | 服务器内部错误 |
| 502 | 上游服务（OpenMAIC）返回错误 |
| 503 | 上游服务（OpenMAIC）不可用 |
| 504 | 上游服务（OpenMAIC）请求超时 |

### 业务错误信息

| 错误代码 | 错误信息（中文） | 错误信息（英文） | 说明 |
|----------|----------------|----------------|------|
| `requireCourseDescription` | 请提供课程描述 (course_description) | Please provide a course description | 提取图谱接口缺少课程描述 |
| `requireFileUpload` | 请上传文件 | Please upload files | 提取图谱接口没有上传文件（文件为可选，仅当无文档内容时可能出现） |
| `requireProjectId` | 请提供项目ID | Please provide project ID | 存储图谱接口缺少项目ID |
| `projectNotFound` | 项目未找到 | Project not found | 指定的项目不存在 |
| `projectDeleteFailed` | 删除项目失败 | Failed to delete project | 删除项目时出错 |
| `graphNotExtracted` | 图谱未提取 | Graph not extracted | 项目状态不允许存储图谱 |
| `graphDataNotFound` | 图谱数据未找到 | Graph data not found | 找不到提取的图谱数据 |
| `textNotFound` | 文本数据未找到 | Text data not found | 找不到提取的文本数据 |
| `configError` | 配置错误 | Configuration error | 后端配置有误（LLM 或 Neo4j） |
| `noDocProcessed` | 没有文档被处理 | No documents were processed | 文件解析失败或无有效文件 |
| `NEO4J_DATA_NOT_FOUND` | Neo4j 中未找到图谱数据 | Graph data not found in Neo4j | Neo4j 中没有该项目的图谱（404） |
| `NEO4J_ERROR` | Neo4j 错误 | Neo4j error | Neo4j 操作失败（404） |
| `LEARNING_PATH_NOT_FOUND` | 学习路径未找到 | Learning path not found | 该项目没有学习路径数据（404） |
| `LEARNING_PATH_ERROR` | 获取学习路径失败 | Failed to retrieve learning path | 服务器内部错误（500） |

---

## 前端 API 客户端

前端 API 封装在 `frontend/src/api/graph.js` 中，提供以下方法：

### 方法列表

| 方法名 | 参数 | 返回类型 | 说明 |
|--------|------|---------|------|
| `extractGraph(formData)` | FormData | Promise | 上传文件并提取图谱 |
| `storeGraph(data)` | { project_id } | Promise | 存储图谱到 Neo4j |
| `getGraphData(graphId)` | String | Promise | 获取图谱数据 |
| `getProject(projectId)` | String | Promise | 获取项目详情 |
| `getProjects(limit)` | Number | Promise | 获取项目列表 |
| `deleteProject(projectId)` | String | Promise | 删除项目 |
| `getLearningPath(projectId)` | String | Promise | 获取学习路径结构 |
| `generateClassroom(data)` | { project_id, node_uuid, podcast_mode?, podcast_speaker_pair? } | Promise | 为知识点生成虚拟课堂 |
| `getClassroomStatus(jobId)` | String | Promise | 查询课堂生成状态 |
| `cacheClassroomId(data)` | { project_id, node_uuid, classroom_id } | Promise | 缓存课堂ID到 Neo4j |
| `getMilestones(projectId)` | String | Promise | 获取项目里程碑列表及关联知识点 |
| `generateHint(data)` | { project_id, milestone_uuid, level } | Promise | 生成学习提示（L1/L2） |

### 使用示例

```javascript
import { extractGraph, storeGraph, getGraphData } from '@/api/graph'

// 1. 提取图谱（文件可选，仅课程描述为必填）
const formData = new FormData()
formData.append('files', file)  // 可选：上传课程文档
formData.append('course_description', '机器学习课程')  // 必填
const response1 = await extractGraph(formData)
console.log('项目ID:', response1.data.project_id)
console.log('节点数:', response1.data.node_count)

// 2. 存储图谱到 Neo4j
const response2 = await storeGraph({
  project_id: response1.data.project_id
})
console.log('存储完成')

// 3. 获取图谱数据用于可视化
const graphData = await getGraphData(response1.data.project_id)
console.log('节点数:', graphData.data.node_count)
console.log('边数:', graphData.data.edge_count)
```

### Axios 配置

API 客户端使用 axios，配置如下：

```javascript
import axios from 'axios'

const service = axios.create({
  baseURL: 'http://localhost:5001',
  timeout: 300000,  // 5分钟超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(config => {
  // 添加语言偏好
  const locale = localStorage.getItem('locale') || 'zh'
  config.headers['Accept-Language'] = locale
  return config
})

// 响应拦截器
service.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)
```

---

## 开发建议

### 前端集成

1. **轮询任务状态**: 建议间隔 5 秒轮询一次（与 OpenMAIC 返回的 `poll_interval_ms` 一致），无超时上限，直到 completed/failed
2. **错误处理**: 统一处理 `success: false` 的情况
3. **加载状态**: 在长时间操作时显示加载提示
4. **数据缓存**: 项目列表等可考虑缓存，减少请求

### 后端开发

1. **日志记录**: 重要操作都应记录日志
2. **异常处理**: try-except 捕获所有异常
3. **数据验证**: 使用 Pydantic 验证输入参数
4. **国际化**: 使用 `locale.py` 提供的翻译函数

---

**文档维护**: Evolith 开发团队
**最后更新**: 2026年4月27日

## 更新日志

### v1.0.0 (2026-04-19)
- 迁移到 Neo4j 图数据库
- 移除 Zep Cloud 依赖
- 简化 API：直接提取和存储节点/边
- 新增历史记录功能
- 移除异步任务轮询机制
- 更新项目状态枚举

### v2.0.0 (2026-04-19)
- 新增学习路径知识图谱功能
- LLM 提取 prompt 重构为学习路径导向（主路径+分支路径）
- 节点必须包含 KnowledgePoint 标签和 learning_path 属性
- 新增学习路径边类型：PREREQUISITE_OF、NEXT_STEP、BRANCHES_FROM、MERGES_TO、ENABLES、PARALLEL_WITH
- 新增 `GET /api/graph/learning-path/{project_id}` 接口
- Neo4j 边存储改为有向关系
- 新增 Cypher 注入防护（SAFE_KEY_PATTERN、SAFE_LABEL_PATTERN）
- 前端新增学习路径视图（分层布局）和全图视图（力导向布局）切换
- 前端新增有向边箭头、边颜色编码、节点差异化显示
- 前端新增学习路径侧边栏

### v3.0.0 (2026-04-21)
- 重构为 PBL（项目驱动学习）图模型
- 节点类型简化为两种：Project（`["Entity", "Project"]`）和 KnowledgePoint（`["Entity", "KnowledgePoint"]`）
- 移除 Concept/Method/Tool 等具体类型标签，知识点统一使用 KnowledgePoint
- 边类型简化为 3 种：NEXT_STEP（Project->Project）、REQUIRES（Project<->KnowledgePoint，双向）、PREREQUISITE_OF（KnowledgePoint->KnowledgePoint）
- 废弃边类型：BUILDS_ON、ENABLES、PARALLEL_WITH、BRANCHES_FROM、MERGES_TO
- 新增环形知识路径：每个项目的知识链从项目出发，经知识点，最终回到同一个项目
- 文件上传改为可选：仅提供 course_description 即可提取图谱
- 移除 path_type 属性（不再区分 main/branch，改用 Project 节点和 NEXT_STEP 边表达项目序列）
- 移除 legacy 字段：ontology、graph_id、graph_build_task_id、chunk_size、chunk_overlap
- 学习路径接口支持双模式返回：PBL 模式（mode: "pbl"）和知识驱动模式（mode: "knowledge_driven"，向后兼容）
- PBL 模式返回 project_knowledge_subgraphs，包含每个项目的环形知识链和闭合状态
- 重置接口统一重置为 `created` 状态（移除 ontology_generated 逻辑）

### v4.0.0 (2026-04-22)
- 新增虚拟课堂 API（`/api/classroom` 蓝图），集成 OpenMAIC 虚拟课堂服务
- 新增 `POST /api/classroom/generate` 接口：为知识点生成虚拟课堂
- 新增 `GET /api/classroom/status/{job_id}` 接口：轮询课堂生成状态
- 新增 `POST /api/classroom/cache` 接口：缓存课堂ID到 Neo4j 节点属性
- 新增 HTTP 状态码 502（上游服务错误）、503（上游服务不可用）、504（上游服务超时）
- Neo4jOperations 新增 `update_node_attribute` 和 `get_node_detail` 方法
- 知识点节点新增 `classroom_id` 可选属性
- 前端 API 客户端新增 `generateClassroom`、`getClassroomStatus`、`cacheClassroomId` 方法

### v5.0.0 (2026-04-24)
- 新增播客模式支持：`podcast_mode` 参数（'podcast'=双人播客模式）
- 新增 `podcast_speaker_pair` 参数（'mizai-dayi'、'liufei-xiaolei'）
- 课堂生成接口新增 HTTP 502 错误场景（OpenMAIC 返回非JSON响应）
- 课堂状态轮询增加 retry 逻辑（最多3次重试，瞬态错误不再终止轮询）
- 后端异常处理改进：捕获 ValueError（JSONDecodeError），防止Next.js HMR重编译返回HTML导致500错误

### v6.0.0 (2026-04-27)
- 新增 `GET /api/graph/milestones/{project_id}` 接口：获取项目里程碑及关联知识点（含 `classroom_id`）
- 新增 `POST /api/hint/generate` 接口：L1/L2 渐进式学习提示生成
- 新增 `hint_bp` 蓝图（`/api/hint`）
- 图谱数据接口 KnowledgePoint 节点新增 `classroom_id` 属性
- 里程碑 API 的 `knowledge_points` 包含 `classroom_id` 字段，用于区分"生成课堂"/"进入课堂"
- 缓存接口 `update_node_attribute` 新增 2 次重试机制（应对 AuraDB 连接断开）
- Neo4j Driver 配置优化：`max_connection_lifetime` 从 3600s 降为 300s（AuraDB 推荐）
- 前端 API 客户端新增 `getMilestones`、`generateHint` 方法
- 课堂轮询移除超时上限，持续轮询直到 completed/failed

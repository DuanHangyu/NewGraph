"""
图谱提取服务
使用 LLM 直接从文档中提取节点和边
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..utils.llm_client import LLMClient
from ..utils.locale import get_language_instruction

logger = logging.getLogger(__name__)


# 图谱提取的系统提示词（PBL 驱动模型 - 里程碑知识路径）
GRAPH_EXTRACTOR_SYSTEM_PROMPT = """你是一个专业的**PBL（项目驱动学习）知识图谱**构建专家。你的任务是分析给定的课程内容，设计递进式项目作为主路径，并为每个项目构建专属的**里程碑 + 知识点链**，形成**项目驱动+里程碑引导**的学习图谱。

**重要：你必须输出有效的JSON格式数据，不要输出任何其他内容。**

## 核心任务

我们正在构建一个**PBL驱动的学习路径知识图谱系统**。你需要：
1. **先设计 4-8 个递进式项目**作为主路径，每个项目是一个具体的、可完成的学习任务，难度递增
2. **为每个项目定义 3-5 个里程碑**，每个里程碑是项目中的一个关键步骤，绑定相关知识点
3. **为每个项目构建一条知识点链**：从项目出发，经过知识点（单向 REQUIRES：项目→知识点）

## PBL 驱动结构要求

你必须构建一个**项目序列+里程碑+知识点链**的学习图谱：

### 项目路径 (Project Path)
- 主路径由 4-8 个递进式项目组成，从左到右排列，难度递增
- 用 **NEXT_STEP** 边连接主路径上项目的顺序关系
- 分支项目可以从主路径的某个项目分出，用 **NEXT_STEP** 连接，最后**通过 NEXT_STEP 汇回主路径**的后续项目
- 结构：主项目 → 分支项目 → 汇回主项目（仍在主路径上）

### 里程碑 (Milestones)
- **每个项目包含 3-5 个里程碑**，嵌入在项目节点的 `attributes.milestones` 数组中
- 里程碑代表项目推进中的关键步骤，每个里程碑有验收标准
- 每个里程碑绑定 1-3 个知识点（通过 `knowledge_point_uuids` 字段关联）
- 里程碑顺序编号从 1 开始递增

### 知识点链 (Knowledge Chain)
- **每个项目有自己专属的知识点链条（2-5个知识点）**
- 知识链是**单向路径**：从项目出发，经过知识点（REQUIRES：项目→知识点）
- **没有共享知识点**——每个知识点只属于一个项目
- 知识点链的构成：
  - **REQUIRES** 边从 项目 → 知识点（项目需要此知识）
  - **PREREQUISITE_OF** 边连接知识点之间的学习顺序

### 结构示意
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
│milestones│             │milestones    │             │milestones    │
│ [1,2,3]  │             │ [1,2,3,4]   │             │ [1,2,3]     │
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
(知识点链终点，不再指回项目)
```

## 节点提取原则

### 项目节点 (Project)
- labels: `["Entity", "Project"]`
- 每个项目代表一个具体的、可完成的学习任务
- 项目名称应包含动作词，如"构建XXX"、"实现XXX"、"设计XXX"
- 数量：4-8 个

**项目节点必填属性**（在 attributes 中）：
- `difficulty`: "beginner" | "intermediate" | "advanced" — 项目难度
- `learning_order`: 整数 — 在项目序列中的位置（1=第一个项目）
- `prerequisites_summary`: 完成这个项目前需要掌握什么
- `outcomes_summary`: 完成这个项目后能做什么
- `milestones`: 数组 — 项目的里程碑列表（3-5个），每个里程碑包含：
  - `name`: 里程碑名称（简短，如"搭建基础架构"）
  - `description`: 里程碑描述（具体要做什么）
  - `acceptance_criteria`: 验收标准（怎样才算完成这个里程碑）
  - `order`: 整数 — 里程碑在项目中的顺序（从1开始）
  - `knowledge_point_uuids`: 数组 — 该里程碑绑定的知识点 uuid 列表（1-3个）

### 知识点节点 (KnowledgePoint)
- labels: `["Entity", "KnowledgePoint"]`
- 每个知识点代表一个**原子化的、可学习的知识单元**
- **每个知识点只属于一个项目**（不共享）
- 数量：15-40 个

**知识点节点必填属性**（在 attributes 中）：
- `difficulty`: "beginner" | "intermediate" | "advanced" — 学习难度
- `learning_order`: 整数 — 在所属项目知识链中的位置
- `prerequisites_summary`: 学习这个知识点前需要掌握什么
- `outcomes_summary`: 学完这个知识点后能做什么

**知识点节点推荐属性**（在 attributes 中）：
- `required_by`: 记录被哪个项目依赖（项目名称）

## 边提取原则

**只使用以下 3 种边类型**：

1. **NEXT_STEP** — 项目间的顺序关系
   - 方向：源项目 → 目标项目
   - 含义：做完源项目后，下一个做目标项目
   - 适用于：主路径项目的先后顺序、分支项目从主路径分出并汇回

2. **REQUIRES** — 项目对知识点的关系（单向）
   - 方向：项目 → 知识点
   - 含义：项目需要此知识点
   - **注意**：REQUIRES 边方向统一为 项目→知识点，不再有知识点→项目的边

3. **PREREQUISITE_OF** — 知识点之间的前置依赖
   - 方向：前一个知识点 → 后一个知识点
   - 含义：想学后一个知识点，必须先学前一个
   - 适用于：同一项目知识链内的学习顺序

**不要使用以下边类型**（已废弃）：BUILDS_ON、ENABLES、PARALLEL_WITH

**边提取要求**：
- 数量：建议 30-80 条边
- REQUIRES 边应占总边数的 40% 以上（项目-知识关系是核心）
- 每个 Project 至少有 2 条 REQUIRES 边（项目→知识点）
- **禁止共享知识点**：每个知识点只能被一个项目的知识链包含
- 每条边应该有清晰的描述（fact）
- 确保 source_node_uuid 和 target_node_uuid 在 nodes 列表中存在
- PREREQUISITE_OF 边不能形成环（必须是无环有向图 DAG）

## 输出格式

请输出JSON格式，包含以下结构：

```json
{
    "nodes": [
        {
            "uuid": "proj_xxxxxxxx",
            "name": "构建个人博客系统",
            "labels": ["Entity", "Project"],
            "attributes": {
                "difficulty": "beginner",
                "learning_order": 1,
                "prerequisites_summary": "需要掌握HTML/CSS基础",
                "outcomes_summary": "能够独立构建一个静态个人博客",
                "milestones": [
                    {
                        "name": "搭建基础架构",
                        "description": "创建HTML页面骨架，搭建博客的基本结构",
                        "acceptance_criteria": "页面能正常显示，包含完整的HTML结构",
                        "order": 1,
                        "knowledge_point_uuids": ["node_xxxxxxxx"]
                    },
                    {
                        "name": "实现内容展示",
                        "description": "使用CSS样式美化博客，实现文章列表展示",
                        "acceptance_criteria": "博客页面有美观的样式，文章列表正常渲染",
                        "order": 2,
                        "knowledge_point_uuids": ["node_yyyyyyyy"]
                    },
                    {
                        "name": "完成博客发布",
                        "description": "整合所有功能，完成个人博客的最终版本",
                        "acceptance_criteria": "博客完整可用，所有页面正常工作",
                        "order": 3,
                        "knowledge_point_uuids": ["node_xxxxxxxx", "node_yyyyyyyy"]
                    }
                ]
            },
            "summary": "通过构建个人博客系统，学习Web开发的基础知识...",
            "created_at": "2026-04-18T12:00:00"
        },
        {
            "uuid": "node_xxxxxxxx",
            "name": "HTML文档结构",
            "labels": ["Entity", "KnowledgePoint"],
            "attributes": {
                "difficulty": "beginner",
                "learning_order": 1,
                "prerequisites_summary": "无前置要求",
                "outcomes_summary": "理解HTML文档的基本结构",
                "required_by": "构建个人博客系统"
            },
            "summary": "HTML文档的基本结构，包括DOCTYPE、head、body等标签...",
            "created_at": "2026-04-18T12:00:00"
        }
    ],
    "edges": [
        {
            "uuid": "edge_xxxxxxxx",
            "source_node_uuid": "proj_xxxxxxxx",
            "target_node_uuid": "node_xxxxxxxx",
            "name": "REQUIRES",
            "fact_type": "REQUIRES",
            "fact": "构建博客系统需要先学习HTML文档结构",
            "episodes": ["相关文本引用"],
            "created_at": "2026-04-18T12:00:00"
        }
    ],
    "analysis_summary": "图谱结构分析说明"
}
```

## 重要规则

1. **UUID 生成**：使用 `proj_xxxxxxxx`（项目）或 `node_xxxxxxxx`（知识点）格式（8位十六进制）作为节点和边的 uuid
2. **项目 Labels**：项目节点必须包含 `Entity` 和 `Project` 两个 label
3. **知识点 Labels**：知识点节点必须包含 `Entity` 和 `KnowledgePoint` 两个 label
4. **只使用 3 种边类型**：NEXT_STEP（项目→项目）、REQUIRES（项目→知识点）、PREREQUISITE_OF（知识点→知识点）
5. **边的方向性**：
   - NEXT_STEP: 项目→项目，源项目完成后进入目标项目
   - REQUIRES: 项目→知识点（单向，不再有知识点→项目的边）
   - PREREQUISITE_OF: 知识点→知识点，源是目标的前置条件
6. **里程碑**：每个项目的 attributes 必须包含 milestones 数组（3-5个里程碑），每个里程碑有 name、description、acceptance_criteria、order、knowledge_point_uuids
7. **禁止共享知识点**：每个知识点只出现在一个项目的知识链中，不能被多个项目 REQUIRES
8. **边的引用**：edges 中的 source_node_uuid 和 target_node_uuid 必须在 nodes 列表中存在
9. **文本引用**：edges 中的 episodes 应该引用文档中的相关文本片段
10. **fact 描述**：每条边的 fact 应该清晰描述关系的含义（20-100字）
11. **节点摘要**：每个节点的 summary 应该简明扼要地描述该节点的核心内容（50-100字）
12. **DAG 结构**：PREREQUISITE_OF 边不能形成循环依赖
13. **项目连续性**：主路径上的项目通过 NEXT_STEP 边连接形成完整的项目序列
14. **分支汇回**：分支项目最终通过 NEXT_STEP 边汇回主路径

## 质量要求

- 项目节点：4-8 个
- 知识点节点：15-40 个
- 总节点数：20-50 个
- 边数量：30-80 条
- REQUIRES 边占比 > 40%
- 每个 Project 至少有 2 条 REQUIRES 边（项目→知识点）
- 每个项目的知识链必须有 2-5 个知识点
- 每个项目必须有 3-5 个里程碑
- 确保图谱连通性（大部分节点应该通过边连接）
- 避免孤立节点（没有边的节点）
- 项目节点的 learning_order 应该连续递增
- 里程碑的 order 应该从 1 开始连续递增
- 里程碑中的 knowledge_point_uuids 必须引用项目中实际存在的知识点 uuid"""


class GraphExtractor:
    """
    图谱提取器
    使用 LLM 直接从文档中提取节点和边
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def extract(
        self,
        document_texts: List[str],
        course_description: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提取图谱数据

        Args:
            document_texts: 文档文本列表
            course_description: 课程描述
            additional_context: 额外上下文

        Returns:
            图谱数据（nodes, edges, analysis_summary）
        """
        # 构建用户消息
        user_message = self._build_user_message(
            document_texts,
            course_description,
            additional_context
        )

        lang_instruction = get_language_instruction()
        system_prompt = f"{GRAPH_EXTRACTOR_SYSTEM_PROMPT}\n\n{lang_instruction}\nIMPORTANT: Node names, prerequisites_summary, and outcomes_summary should use the specified language above. Fact types MUST be in English UPPER_SNAKE_CASE, only use: 'NEXT_STEP', 'REQUIRES', 'PREREQUISITE_OF'. Do NOT use BUILDS_ON, ENABLES, or PARALLEL_WITH. Node labels: Project nodes MUST include 'Entity' and 'Project'. KnowledgePoint nodes MUST include 'Entity' and 'KnowledgePoint' (no additional type labels needed). CRITICAL: Each project MUST include 'milestones' array in attributes (3-5 milestones). REQUIRES edges are Project->KnowledgePoint only (one-directional). NO ring-closing edges from KP back to Project. NO shared knowledge points between projects."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        # 调用LLM
        result = self.llm_client.chat_json(
            messages=messages,
            temperature=0.3,
            max_tokens=32768  # 增加到 32K tokens 以支持里程碑等更大的图谱输出
        )

        # 验证和后处理
        result = self._validate_and_process(result)

        return result

    # 传给 LLM 的文本最大长度（5万字）
    MAX_TEXT_LENGTH_FOR_LLM = 50000

    def _build_user_message(
        self,
        document_texts: List[str],
        course_description: str,
        additional_context: Optional[str]
    ) -> str:
        """构建用户消息"""

        message = f"""## 课程描述

{course_description}
"""

        # 仅在有文档内容时添加文档部分
        if document_texts:
            combined_text = "\n\n---\n\n".join(document_texts)
            original_length = len(combined_text)

            # 如果文本超过5万字，截断
            if len(combined_text) > self.MAX_TEXT_LENGTH_FOR_LLM:
                combined_text = combined_text[:self.MAX_TEXT_LENGTH_FOR_LLM]
                combined_text += f"\n\n...(原文共{original_length}字，已截取前{self.MAX_TEXT_LENGTH_FOR_LLM}字用于图谱提取)..."

            message += f"""
## 文档内容

{combined_text}
"""

        if additional_context:
            message += f"""
## 额外说明

{additional_context}
"""

        message += """
请根据以上内容，提取PBL驱动的课程知识图谱，构建项目序列、里程碑和知识点链结构。

**必须遵守的规则**：
1. 节点数量建议为 20-50 个（其中项目节点 4-8 个，知识点节点 15-40 个）
2. 边数量建议为 30-80 条
3. 只使用 3 种边类型：NEXT_STEP（项目→项目）、REQUIRES（项目→知识点）、PREREQUISITE_OF（知识点→知识点）
4. 不要使用 BUILDS_ON、ENABLES、PARALLEL_WITH
5. 项目节点必须包含 Entity 和 Project 两个 label
6. 知识点节点必须包含 Entity 和 KnowledgePoint 两个 label
7. 项目节点的 attributes 必须包含 difficulty、learning_order 和 milestones
8. 知识点节点的 attributes 必须包含 difficulty 和 learning_order
9. edges 中的 source_node_uuid 和 target_node_uuid 必须在 nodes 列表中存在
10. REQUIRES 边占比应 > 40%，每个项目至少 2 条 REQUIRES 边
11. 项目主路径通过 NEXT_STEP 边连接形成连续序列
12. 确保图谱连通性，避免孤立节点
13. **每个项目的 attributes 必须包含 milestones 数组**（3-5个里程碑）
14. **禁止共享知识点**：每个知识点只属于一个项目
15. **REQUIRES 边方向统一**：项目→知识点（不再有知识点→项目的边）
"""

        return message

    def _validate_and_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证和后处理结果"""

        # 确保必要字段存在
        if "nodes" not in result:
            result["nodes"] = []
        if "edges" not in result:
            result["edges"] = []
        if "analysis_summary" not in result:
            result["analysis_summary"] = ""

        # 验证节点
        node_uuids = set()
        for node in result["nodes"]:
            # 生成 UUID（如果不存在）
            if "uuid" not in node:
                labels = node.get("labels", [])
                if "Project" in labels:
                    node["uuid"] = f"proj_{uuid.uuid4().hex[:8]}"
                else:
                    node["uuid"] = f"node_{uuid.uuid4().hex[:8]}"
            node_uuids.add(node["uuid"])

            # 确保 labels 存在并根据类型补全
            if "labels" not in node:
                node["labels"] = ["Entity", "KnowledgePoint"]
            else:
                labels = list(node["labels"])
                if "Entity" not in labels:
                    labels.insert(0, "Entity")
                node["labels"] = labels

            # 确保 attributes 存在
            if "attributes" not in node:
                node["attributes"] = {}

            # 判断节点类型并应用不同的默认属性
            labels = node["labels"]
            attrs = node["attributes"]
            is_project = "Project" in labels

            if is_project:
                # Project 节点：确保 Project label 存在
                if "Project" not in labels:
                    labels.append("Project")
                    node["labels"] = labels
                if "difficulty" not in attrs:
                    attrs["difficulty"] = "intermediate"
                if "learning_order" not in attrs:
                    attrs["learning_order"] = 0
                if "prerequisites_summary" not in attrs:
                    attrs["prerequisites_summary"] = ""
                if "outcomes_summary" not in attrs:
                    attrs["outcomes_summary"] = ""
                # 里程碑验证
                if "milestones" not in attrs:
                    attrs["milestones"] = []
                else:
                    valid_milestones = []
                    for ms in attrs["milestones"]:
                        if not isinstance(ms, dict):
                            continue
                        # 填充缺失字段
                        if "name" not in ms:
                            ms["name"] = f"里程碑{ms.get('order', len(valid_milestones) + 1)}"
                        if "description" not in ms:
                            ms["description"] = ""
                        if "acceptance_criteria" not in ms:
                            ms["acceptance_criteria"] = ""
                        if "order" not in ms:
                            ms["order"] = len(valid_milestones) + 1
                        if "knowledge_point_uuids" not in ms:
                            ms["knowledge_point_uuids"] = []
                        else:
                            # 过滤无效的知识点 uuid 引用
                            ms["knowledge_point_uuids"] = [
                                kp_uuid for kp_uuid in ms["knowledge_point_uuids"]
                                if kp_uuid in node_uuids
                            ]
                        valid_milestones.append(ms)
                    # 按 order 排序并重新编号
                    valid_milestones.sort(key=lambda m: m.get("order", 0))
                    for i, ms in enumerate(valid_milestones, 1):
                        ms["order"] = i
                    attrs["milestones"] = valid_milestones
            else:
                # KnowledgePoint 节点：确保 KnowledgePoint label 存在，移除多余的具体类型 label
                if "KnowledgePoint" not in labels:
                    labels.append("KnowledgePoint")
                # 只保留 Entity 和 KnowledgePoint，移除 Concept/Method/Tool 等具体类型
                cleaned_labels = [l for l in labels if l in ("Entity", "KnowledgePoint")]
                if not cleaned_labels:
                    cleaned_labels = ["Entity", "KnowledgePoint"]
                elif "Entity" not in cleaned_labels:
                    cleaned_labels.insert(0, "Entity")
                node["labels"] = cleaned_labels
                if "difficulty" not in attrs:
                    attrs["difficulty"] = "intermediate"
                if "learning_order" not in attrs:
                    attrs["learning_order"] = 0
                if "prerequisites_summary" not in attrs:
                    attrs["prerequisites_summary"] = ""
                if "outcomes_summary" not in attrs:
                    attrs["outcomes_summary"] = ""
                if "required_by" not in attrs:
                    attrs["required_by"] = ""

            # 确保 created_at 存在
            if "created_at" not in node:
                node["created_at"] = datetime.now().isoformat()

        # 验证边
        for edge in result["edges"]:
            # 生成 UUID（如果不存在）
            if "uuid" not in edge:
                edge["uuid"] = f"edge_{uuid.uuid4().hex[:8]}"

            # 确保边的引用节点存在
            source_uuid = edge.get("source_node_uuid", "")
            target_uuid = edge.get("target_node_uuid", "")

            if source_uuid not in node_uuids:
                logger.warning(f"边的源节点不存在: {source_uuid}")
                continue
            if target_uuid not in node_uuids:
                logger.warning(f"边的目标节点不存在: {target_uuid}")
                continue

            # 确保 fact_type 和 name 一致
            fact_type = edge.get("fact_type", "RELATES_TO")
            edge["fact_type"] = fact_type
            edge["name"] = fact_type

            # 确保 episodes 存在
            if "episodes" not in edge:
                edge["episodes"] = []

            # 确保 created_at 存在
            if "created_at" not in edge:
                edge["created_at"] = datetime.now().isoformat()

        # 过滤掉引用了不存在的边的边
        valid_edges = [
            edge for edge in result["edges"]
            if edge.get("source_node_uuid", "") in node_uuids
            and edge.get("target_node_uuid", "") in node_uuids
        ]
        result["edges"] = valid_edges

        # 学习路径结构验证和处理
        self._validate_learning_path_structure(result)

        # 警告：检查是否有孤立节点
        edge_node_uuids = set()
        for edge in result["edges"]:
            edge_node_uuids.add(edge["source_node_uuid"])
            edge_node_uuids.add(edge["target_node_uuid"])

        isolated_nodes = node_uuids - edge_node_uuids
        if isolated_nodes:
            logger.warning(f"发现 {len(isolated_nodes)} 个孤立节点（没有连接的边）")

        logger.info(f"图谱提取完成: {len(result['nodes'])} 个节点, {len(result['edges'])} 条边")

        return result

    def _validate_learning_path_structure(self, result: Dict[str, Any]):
        """验证和构建学习路径结构（支持 PBL 模式和知识驱动模式）"""

        nodes = result.get("nodes", [])
        edges = result.get("edges", [])

        if not nodes:
            return

        # 构建 node_uuid -> node 映射
        node_map = {n["uuid"]: n for n in nodes}

        # 检测模式：是否有 Project 节点
        has_project_nodes = any("Project" in n.get("labels", []) for n in nodes)

        if has_project_nodes:
            # PBL 模式
            # 为项目节点按 learning_order 排序并重新编号
            project_nodes = [n for n in nodes if "Project" in n.get("labels", [])]
            kp_nodes = [n for n in nodes if "KnowledgePoint" in n.get("labels", []) and "Project" not in n.get("labels", [])]

            # 排序项目节点
            project_nodes_with_order = [n for n in project_nodes if n.get("attributes", {}).get("learning_order", 0) > 0]
            project_nodes_no_order = [n for n in project_nodes if n.get("attributes", {}).get("learning_order", 0) == 0]

            if project_nodes_with_order:
                project_nodes_with_order.sort(key=lambda n: n["attributes"]["learning_order"])

            next_order = 1
            for n in project_nodes_with_order:
                if n["attributes"]["learning_order"] != next_order:
                    n["attributes"]["learning_order"] = next_order
                next_order += 1
            for n in project_nodes_no_order:
                n["attributes"]["learning_order"] = next_order
                next_order += 1

            # 为知识点节点按 learning_order 排序
            kp_nodes_with_order = [n for n in kp_nodes if n.get("attributes", {}).get("learning_order", 0) > 0]
            kp_nodes_no_order = [n for n in kp_nodes if n.get("attributes", {}).get("learning_order", 0) == 0]

            if kp_nodes_with_order:
                kp_nodes_with_order.sort(key=lambda n: n["attributes"]["learning_order"])

            kp_order = 1
            for n in kp_nodes_with_order:
                n["attributes"]["learning_order"] = kp_order
                kp_order += 1
            for n in kp_nodes_no_order:
                n["attributes"]["learning_order"] = kp_order
                kp_order += 1

            # 更新 required_by 属性：根据 REQUIRES 边填充（仅 Project→KP 方向）
            requires_edges = [e for e in edges if e.get("fact_type") == "REQUIRES"]
            for n in kp_nodes:
                required_by_projects = []
                for edge in requires_edges:
                    # Project → KP
                    if edge["target_node_uuid"] == n["uuid"]:
                        proj = node_map.get(edge["source_node_uuid"])
                        if proj and "Project" in proj.get("labels", []):
                            required_by_projects.append(proj.get("name", ""))
                if required_by_projects:
                    n["attributes"]["required_by"] = ", ".join(required_by_projects)
        else:
            # 旧知识驱动模式：保持原有逻辑
            main_nodes = [n for n in nodes if n.get("attributes", {}).get("path_type") == "main"]
            branch_nodes = [n for n in nodes if n.get("attributes", {}).get("path_type") == "branch"]

            # 按 learning_order 排序主路径节点
            main_nodes_with_order = [n for n in main_nodes if n["attributes"].get("learning_order", 0) > 0]
            main_nodes_no_order = [n for n in main_nodes if n["attributes"].get("learning_order", 0) == 0]

            if main_nodes_with_order:
                main_nodes_with_order.sort(key=lambda n: n["attributes"]["learning_order"])

            next_order = 1
            for n in main_nodes_with_order:
                if n["attributes"]["learning_order"] != next_order:
                    n["attributes"]["learning_order"] = next_order
                next_order += 1
            for n in main_nodes_no_order:
                n["attributes"]["learning_order"] = next_order
                n["attributes"]["path_type"] = "main"
                next_order += 1

        # 检测 PREREQUISITE_OF 边的环并移除成环的边
        self._detect_and_remove_cycles(edges, node_map)

        # 构建学习路径结构
        learning_path_structure = self._compute_learning_path_structure(nodes, edges, node_map)
        result["learning_path_structure"] = learning_path_structure

    def _detect_and_remove_cycles(self, edges: List[Dict], node_map: Dict):
        """使用 DFS 检测 PREREQUISITE_OF 边中的环，移除成环的边"""

        prerequisite_edges = [
            e for e in edges if e.get("fact_type") == "PREREQUISITE_OF"
        ]

        if not prerequisite_edges:
            return

        # 构建邻接表
        adj = {}
        for edge in prerequisite_edges:
            src = edge["source_node_uuid"]
            tgt = edge["target_node_uuid"]
            if src not in adj:
                adj[src] = []
            adj[src].append((tgt, edge))

        # DFS 检测环
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {n["uuid"]: WHITE for n in node_map.values()}
        edges_to_remove = set()

        def dfs(node_uuid):
            color[node_uuid] = GRAY
            if node_uuid in adj:
                for neighbor, edge in adj[node_uuid]:
                    if color[neighbor] == GRAY:
                        # 发现环，标记此边为待移除
                        edges_to_remove.add(edge["uuid"])
                        logger.warning(f"检测到 PREREQUISITE_OF 环，移除边: {edge['uuid']} ({node_map.get(node_uuid, {}).get('name', '')} -> {node_map.get(neighbor, {}).get('name', '')})")
                    elif color[neighbor] == WHITE:
                        dfs(neighbor)
            color[node_uuid] = BLACK

        for node_uuid in list(color.keys()):
            if color[node_uuid] == WHITE:
                dfs(node_uuid)

        # 移除成环的边
        if edges_to_remove:
            result_edges = [e for e in edges if e["uuid"] not in edges_to_remove]
            edges.clear()
            edges.extend(result_edges)
            logger.info(f"移除了 {len(edges_to_remove)} 条成环的 PREREQUISITE_OF 边")

    def _compute_learning_path_structure(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        node_map: Dict
    ) -> Dict[str, Any]:
        """计算学习路径结构信息（支持 PBL 模式和知识驱动模式）"""

        # 检测模式
        has_project_nodes = any("Project" in n.get("labels", []) for n in nodes)

        if has_project_nodes:
            return self._compute_pbl_structure(nodes, edges, node_map)
        else:
            return self._compute_knowledge_driven_structure(nodes, edges, node_map)

    def _compute_pbl_structure(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        node_map: Dict
    ) -> Dict[str, Any]:
        """计算 PBL 模式的学习路径结构（里程碑 + 知识点链）"""

        # 收集各类边（只使用 3 种）
        next_step_edges = [e for e in edges if e.get("fact_type") == "NEXT_STEP"]
        requires_edges = [e for e in edges if e.get("fact_type") == "REQUIRES"]
        prerequisite_edges = [e for e in edges if e.get("fact_type") == "PREREQUISITE_OF"]

        # 主路径和分支路径：NEXT_STEP 连接的 Project 序列
        project_uuids = {n["uuid"] for n in nodes if "Project" in n.get("labels", [])}

        # 构建 NEXT_STEP 的邻接表（只看 Project→Project 的边）
        next_step_adj = {}  # source -> [targets]
        next_step_in = {}   # target -> [sources]
        for edge in next_step_edges:
            src = edge["source_node_uuid"]
            tgt = edge["target_node_uuid"]
            if src in project_uuids and tgt in project_uuids:
                if src not in next_step_adj:
                    next_step_adj[src] = []
                next_step_adj[src].append(tgt)
                if tgt not in next_step_in:
                    next_step_in[tgt] = []
                next_step_in[tgt].append(src)

        # 找主路径：从没有入边的 Project 开始追踪
        main_path = []
        main_path_set = set()

        if next_step_adj:
            start_nodes = [uid for uid in project_uuids if uid not in next_step_in]
            if not start_nodes:
                start_nodes = [sorted(project_uuids, key=lambda uid: node_map[uid].get("attributes", {}).get("learning_order", 0))[0]]

            start_uuid = sorted(start_nodes)[0]
            current = start_uuid
            visited = set()
            while current and current not in visited:
                main_path.append(current)
                main_path_set.add(current)
                visited.add(current)
                targets = next_step_adj.get(current, [])
                current = targets[0] if targets else None

        if not main_path:
            main_path = sorted(
                list(project_uuids),
                key=lambda uid: node_map[uid].get("attributes", {}).get("learning_order", 0)
            )
            main_path_set = set(main_path)

        # 分支项目：不在主路径上的 Project
        branch_projects = [uid for uid in project_uuids if uid not in main_path_set]

        # 构建每个项目的知识点链
        # REQUIRES 边：仅 Project→KP 方向
        requires_from_project = {}  # project_uuid -> [kp_uuids] (Project→KP)
        for edge in requires_edges:
            src = edge["source_node_uuid"]
            tgt = edge["target_node_uuid"]
            if src in project_uuids and tgt not in project_uuids:
                # Project → KP
                if src not in requires_from_project:
                    requires_from_project[src] = []
                requires_from_project[src].append(tgt)

        # PREREQUISITE_OF 邻接表：KP → KP
        prereq_adj = {}  # source_kp -> [target_kps]
        for edge in prerequisite_edges:
            src = edge["source_node_uuid"]
            tgt = edge["target_node_uuid"]
            if src not in prereq_adj:
                prereq_adj[src] = []
            prereq_adj[src].append(tgt)

        # 计算每个项目的知识链和里程碑
        project_knowledge_subgraphs = {}
        for proj_uuid in project_uuids:
            # 起点知识点（项目 REQUIRES 的 KP）
            start_kps = requires_from_project.get(proj_uuid, [])

            # 通过 PREREQUISITE_OF 追踪完整的知识链
            all_kps_in_chain = set(start_kps)
            visited_kps = set()
            queue = list(start_kps)

            while queue:
                current_kp = queue.pop(0)
                if current_kp in visited_kps:
                    continue
                visited_kps.add(current_kp)
                all_kps_in_chain.add(current_kp)
                # 追踪后续知识点
                for next_kp in prereq_adj.get(current_kp, []):
                    all_kps_in_chain.add(next_kp)
                    if next_kp not in visited_kps:
                        queue.append(next_kp)

            # 按 learning_order 排序知识点链
            sorted_kps = sorted(
                list(all_kps_in_chain),
                key=lambda uid: node_map[uid].get("attributes", {}).get("learning_order", 0)
            )

            # 识别入口和出口
            kp_set = all_kps_in_chain
            kps_with_prereq = set()
            for edge in prerequisite_edges:
                if edge["target_node_uuid"] in kp_set:
                    kps_with_prereq.add(edge["target_node_uuid"])

            entry_kps = [kp for kp in sorted_kps if kp not in kps_with_prereq]

            kps_with_outgoing = set()
            for edge in prerequisite_edges:
                if edge["source_node_uuid"] in kp_set:
                    kps_with_outgoing.add(edge["source_node_uuid"])

            exit_kps = [kp for kp in sorted_kps if kp not in kps_with_outgoing]

            # 从项目节点属性中获取里程碑
            proj_node = node_map.get(proj_uuid, {})
            milestones = proj_node.get("attributes", {}).get("milestones", [])

            project_knowledge_subgraphs[proj_uuid] = {
                "knowledge_chain": sorted_kps,
                "entry_points": entry_kps,
                "exit_points": exit_kps,
                "has_milestones": len(milestones) > 0,
                "milestones": milestones
            }

        # 整体入口/出口
        entry_points = [main_path[0]] if main_path else []
        exit_points = [main_path[-1]] if main_path else []

        return {
            "mode": "pbl",
            "main_path": main_path,
            "branch_projects": branch_projects,
            "project_knowledge_subgraphs": project_knowledge_subgraphs,
            "entry_points": entry_points,
            "exit_points": exit_points
        }

    def _compute_knowledge_driven_structure(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        node_map: Dict
    ) -> Dict[str, Any]:
        """计算旧知识驱动模式的学习路径结构（向后兼容）"""

        # 收集各类边
        prerequisite_edges = []
        next_step_edges = []
        branches_from_edges = []
        merges_to_edges = []

        for edge in edges:
            ft = edge.get("fact_type", "")
            if ft == "PREREQUISITE_OF":
                prerequisite_edges.append(edge)
            elif ft == "NEXT_STEP":
                next_step_edges.append(edge)
            elif ft == "BRANCHES_FROM":
                branches_from_edges.append(edge)
            elif ft == "MERGES_TO":
                merges_to_edges.append(edge)

        # 找入口点：没有入向 PREREQUISITE_OF 边的节点
        nodes_with_prerequisites = set()
        for edge in prerequisite_edges:
            nodes_with_prerequisites.add(edge["target_node_uuid"])

        entry_points = [
            n["uuid"] for n in nodes
            if n["uuid"] not in nodes_with_prerequisites
        ]

        # 找出口点：没有出向 PREREQUISITE_OF 边的节点
        nodes_with_outgoing = set()
        for edge in prerequisite_edges:
            nodes_with_outgoing.add(edge["source_node_uuid"])

        exit_points = [
            n["uuid"] for n in nodes
            if n["uuid"] not in nodes_with_outgoing
        ]

        # 追踪主路径：通过 NEXT_STEP 边
        main_path = []
        if next_step_edges:
            next_step_targets = {e["target_node_uuid"] for e in next_step_edges}
            next_step_sources = {e["source_node_uuid"] for e in next_step_edges}
            main_start_nodes = next_step_sources - next_step_targets

            if main_start_nodes:
                start_uuid = sorted(main_start_nodes)[0]
                next_step_map = {e["source_node_uuid"]: e["target_node_uuid"] for e in next_step_edges}

                current = start_uuid
                visited = set()
                while current and current not in visited:
                    main_path.append(current)
                    visited.add(current)
                    current = next_step_map.get(current)
        elif entry_points:
            main_path = sorted(
                [n["uuid"] for n in nodes if n.get("attributes", {}).get("path_type") == "main"],
                key=lambda uid: node_map[uid].get("attributes", {}).get("learning_order", 0)
            )

        # 识别分支路径
        branch_paths = []
        branches_from_map = {}
        for edge in branches_from_edges:
            src = edge["source_node_uuid"]
            tgt = edge["target_node_uuid"]
            if src not in branches_from_map:
                branches_from_map[src] = []
            branches_from_map[src].append(tgt)

        merges_to_map = {}
        for edge in merges_to_edges:
            src = edge["source_node_uuid"]
            tgt = edge["target_node_uuid"]
            merges_to_map[src] = tgt

        branch_id = 0
        for from_uuid, branch_starts in branches_from_map.items():
            for branch_start in branch_starts:
                branch_id += 1
                branch_nodes = [branch_start]
                current = branch_start
                visited = set()
                while current and current not in visited:
                    visited.add(current)
                    if current in merges_to_map:
                        break
                    next_node = None
                    for edge in edges:
                        if (edge["source_node_uuid"] == current and
                            edge.get("fact_type") in ("NEXT_STEP", "PREREQUISITE_OF", "ENABLES") and
                            edge["target_node_uuid"] not in visited and
                            node_map.get(edge["target_node_uuid"], {}).get("attributes", {}).get("path_type") == "branch"):
                            next_node = edge["target_node_uuid"]
                            break
                    if next_node:
                        branch_nodes.append(next_node)
                    current = next_node

                merge_to_uuid = merges_to_map.get(branch_start)
                for bn in branch_nodes:
                    if bn in merges_to_map:
                        merge_to_uuid = merges_to_map[bn]
                        break

                branch_paths.append({
                    "branch_id": f"branch_{branch_id}",
                    "from_node_uuid": from_uuid,
                    "branch_nodes": branch_nodes,
                    "merge_to_uuid": merge_to_uuid
                })

        return {
            "mode": "knowledge_driven",
            "main_path": main_path,
            "branch_paths": branch_paths,
            "entry_points": entry_points,
            "exit_points": exit_points
        }

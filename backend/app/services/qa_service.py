"""
QA 问答服务

管道：用户提问 → Graphiti 混合检索 → 上下文组装 → LLM 生成回答
"""

import logging
from datetime import datetime, timezone
from typing import Any

from ..utils.llm_client import LLMClient
from ..utils.async_bridge import AsyncBridge
from .graphiti_service import GraphitiService

logger = logging.getLogger(__name__)

QA_SYSTEM_PROMPT = """你是"中国先进技术知识图谱问答系统"。你的任务是基于提供的知识图谱检索结果，回答用户关于中国先进技术的问题。

## 回答规则

1. **必须使用中文**回答
2. **仅基于检索结果**回答问题，不要编造信息
3. 如果检索结果不足以回答问题，明确告知用户"当前知识库中没有相关信息"
4. 回答时自然地引用涉及的实体名称和关系事实
5. 在回答末尾标注引用的实体和关系数量

## 检索结果格式

检索结果包含：
- 关系边（源实体 → 关系 → 目标实体）
- 实体信息（名称、摘要、类型）

请基于这些信息组织你的回答。"""


class QAService:
    """QA 问答管道服务"""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client or LLMClient()

    def ask(self, question: str, group_id: str | None = None) -> dict[str, Any]:
        """
        问答主流程

        Args:
            question: 用户问题
            group_id: Graphiti group_id

        Returns:
            {answer, question, sources, search_stats, timestamp}
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # 1. Graphiti 混合检索
        search_results = AsyncBridge.run(
            GraphitiService.search(query=question, group_id=group_id, num_results=20)
        )

        if not search_results:
            return {
                "answer": "抱歉，当前知识库中没有与您问题相关的信息。请先导入相关数据集。",
                "question": question,
                "sources": [],
                "search_stats": {"result_count": 0},
                "timestamp": timestamp,
            }

        # 2. 组装上下文
        context = self._assemble_context(search_results)

        # 3. LLM 生成回答
        messages = [
            {"role": "system", "content": QA_SYSTEM_PROMPT},
            {"role": "user", "content": f"## 知识图谱检索结果\n\n{context}\n\n## 用户问题\n\n{question}"},
        ]

        answer = self.llm_client.chat(messages=messages, temperature=0.3)

        return {
            "answer": answer,
            "question": question,
            "sources": search_results,
            "search_stats": {"result_count": len(search_results)},
            "timestamp": timestamp,
        }

    def _assemble_context(self, search_results: list[dict]) -> str:
        """将检索结果格式化为结构化上下文"""
        parts = []

        # 收集所有唯一实体
        entities = {}
        for edge in search_results:
            source = edge.get("source_node", {})
            target = edge.get("target_node", {})
            if source.get("uuid"):
                entities[source["uuid"]] = source
            if target.get("uuid"):
                entities[target["uuid"]] = target

        # 实体信息
        parts.append("### 相关实体\n")
        for i, (uid, entity) in enumerate(entities.items(), 1):
            name = entity.get("name", "未知")
            summary = entity.get("summary", "")
            labels = entity.get("labels", [])
            label_str = ", ".join(l for l in labels if l != "Entity") if labels else "未知类型"
            parts.append(f"{i}. **{name}**（{label_str}）")
            if summary:
                parts.append(f"   - 摘要: {summary}")
            parts.append("")

        # 关系事实
        parts.append("### 关系事实\n")
        for i, edge in enumerate(search_results, 1):
            source_name = edge.get("source_node", {}).get("name", "?")
            target_name = edge.get("target_node", {}).get("name", "?")
            fact = edge.get("fact", "")
            edge_name = edge.get("name", "")
            relation_desc = fact or edge_name or "相关"
            parts.append(f"{i}. {source_name} → {relation_desc} → {target_name}")

        return "\n".join(parts)

    def ask_stream(self, question: str, group_id: str | None = None):
        """
        流式问答，yield 分阶段事件 dict

        事件类型：
        1. {type: "status", stage: "searching", message: "..."}
        2. {type: "status", stage: "found", message: "...", node_uuids: [...], edge_uuids: [...]}
        3. {type: "status", stage: "generating", message: "..."}
        4. {type: "token", content: "..."}
        5. {type: "done", sources: [...], search_stats: {...}, timestamp: "..."}

        Args:
            question: 用户问题
            group_id: Graphiti group_id

        Yields:
            dict: 事件字典
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # 1. 搜索开始
        yield {
            "type": "status",
            "stage": "searching",
            "message": "检索知识图谱...",
        }

        # 2. Graphiti 混合检索
        search_results = AsyncBridge.run(
            GraphitiService.search(query=question, group_id=group_id, num_results=20)
        )

        if not search_results:
            yield {
                "type": "done",
                "answer": "抱歉，当前知识库中没有与您问题相关的信息。请先导入相关数据集。",
                "question": question,
                "sources": [],
                "search_stats": {"result_count": 0},
                "timestamp": timestamp,
            }
            return

        # 提取高亮 UUID
        node_uuids = list({
            uuid
            for edge in search_results
            for uuid in (
                edge.get("source_node", {}).get("uuid"),
                edge.get("target_node", {}).get("uuid"),
            )
            if uuid
        })
        edge_uuids = [edge.get("uuid", "") for edge in search_results if edge.get("uuid")]

        # 3. 搜索完成
        yield {
            "type": "status",
            "stage": "found",
            "message": f"找到 {len(node_uuids)} 个相关实体",
            "node_uuids": node_uuids,
            "edge_uuids": edge_uuids,
        }

        # 4. 开始生成
        yield {
            "type": "status",
            "stage": "generating",
            "message": "正在生成回答...",
        }

        # 5. 组装上下文
        context = self._assemble_context(search_results)
        messages = [
            {"role": "system", "content": QA_SYSTEM_PROMPT},
            {"role": "user", "content": f"## 知识图谱检索结果\n\n{context}\n\n## 用户问题\n\n{question}"},
        ]

        # 6. LLM 流式生成
        full_answer = ""
        for token in self.llm_client.chat_stream(messages=messages, temperature=0.3):
            full_answer += token
            yield {"type": "token", "content": token}

        # 7. 完成
        yield {
            "type": "done",
            "answer": full_answer,
            "question": question,
            "sources": search_results,
            "search_stats": {"result_count": len(search_results)},
            "timestamp": timestamp,
        }

"""
Hint Service - 生成里程碑学习提示
支持 L1（简短概念提示）和 L2（深入解释提示）
"""

import logging
from typing import Dict, Any, Optional, List

from ..utils.llm_client import LLMClient
from ..utils.locale import get_language_instruction
from ..services.neo4j_operations import Neo4jOperations

logger = logging.getLogger(__name__)


# L1 提示模板：简短、聚焦的核心概念提示
L1_PROMPT_TEMPLATE = """You are a helpful learning assistant for a PBL (Project-Based Learning) course.

A student is working on milestone "{milestone_name}" (step {milestone_order}) in project "{project_name}".

Milestone description: {milestone_description}
Acceptance criteria: {acceptance_criteria}

This milestone requires these knowledge points:
{knowledge_points_info}

Project overall goal: {project_outcomes}

Give the student a SHORT hint (2-3 sentences only). Focus on:
1. The core concept they need to understand
2. One actionable tip to approach this milestone
3. Keep it brief and encouraging — they asked for a light hint

{language_instruction}"""

# L2 提示模板：深入解释，带示例和常见错误
L2_PROMPT_TEMPLATE = """You are a detailed learning mentor for a PBL (Project-Based Learning) course.

A student has already received a brief hint but is still confused about milestone "{milestone_name}" (step {milestone_order}) in project "{project_name}".

Milestone description: {milestone_description}
Acceptance criteria: {acceptance_criteria}

This milestone requires these knowledge points:
{knowledge_points_info}

Project overall goal: {project_outcomes}

Provide a DEEPER explanation (3-5 paragraphs). Cover:
1. Detailed explanation of the core concepts with concrete examples tied to this project
2. Common mistakes students make and how to avoid them
3. Step-by-step practice advice to build understanding
4. How the knowledge points connect together to achieve the milestone
5. Encourage the student — remind them this is learnable

{language_instruction}"""


class HintService:
    """学习提示生成服务"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.neo4j_ops = Neo4jOperations()
        if not self.neo4j_ops.driver:
            raise ValueError("Neo4j connection not available. Please check your database configuration.")

    def _fetch_milestone_context(self, project_id: str, milestone_uuid: str) -> Optional[Dict[str, Any]]:
        """
        从 Neo4j 获取里程碑及关联知识点、项目信息

        Returns:
            包含 milestone, knowledge_points, project 信息的字典，或 None
        """
        query = """
        MATCH (ms:Entity:Milestone {uuid: $milestone_uuid})
        RETURN ms.uuid as ms_uuid,
               ms.name as ms_name,
               ms.description as ms_description,
               ms.acceptance_criteria as ms_acceptance_criteria,
               ms.order as ms_order,
               ms.project_uuid as ms_project_uuid
        """

        milestone_data = None
        with self.neo4j_ops.driver.session(default_access_mode="READ") as session:
            result = session.run(query, {
                "milestone_uuid": milestone_uuid
            })
            record = result.single()
            if not record:
                return None

            milestone_data = {
                "uuid": record.get("ms_uuid", ""),
                "name": record.get("ms_name", ""),
                "description": record.get("ms_description", ""),
                "acceptance_criteria": record.get("ms_acceptance_criteria", ""),
                "order": record.get("ms_order", 0),
                "project_uuid": record.get("ms_project_uuid", ""),
            }

        # 获取关联知识点（使用与 milestones API 相同的 fallback 逻辑）
        kp_query = """
        MATCH (ms:Entity:Milestone {uuid: $milestone_uuid})
              -[r:RELATIONSHIP {fact_type: 'MILESTONE_REQUIRES'}]->(kp:Entity)
        RETURN kp.uuid as kp_uuid,
               kp.name as kp_name,
               kp.summary as kp_summary,
               kp.prerequisites_summary as kp_prerequisites_summary,
               kp.outcomes_summary as kp_outcomes_summary,
               kp.difficulty as kp_difficulty
        """

        knowledge_points = []
        with self.neo4j_ops.driver.session(default_access_mode="READ") as session:
            result = session.run(kp_query, {
                "milestone_uuid": milestone_uuid
            })
            for record in result:
                knowledge_points.append({
                    "uuid": record.get("kp_uuid", ""),
                    "name": record.get("kp_name", ""),
                    "summary": record.get("kp_summary", ""),
                    "prerequisites_summary": record.get("kp_prerequisites_summary", ""),
                    "outcomes_summary": record.get("kp_outcomes_summary", ""),
                    "difficulty": record.get("kp_difficulty", ""),
                })

        # Fallback: 如果里程碑没有 MILESTONE_REQUIRES 边，从父项目获取知识点
        if not knowledge_points and milestone_data and milestone_data.get("project_uuid"):
            fallback_kp_query = """
            MATCH (p:Entity:Project {uuid: $project_uuid})
            -[r:RELATIONSHIP {fact_type: 'REQUIRES'}]->(kp:Entity)
            WHERE (kp.project_id = $project_id OR kp.project_id IS NULL)
              AND (kp.required_by = p.name OR kp.required_by IS NULL OR kp.required_by = '')
            RETURN kp.uuid as kp_uuid,
                   kp.name as kp_name,
                   kp.summary as kp_summary,
                   kp.prerequisites_summary as kp_prerequisites_summary,
                   kp.outcomes_summary as kp_outcomes_summary,
                   kp.difficulty as kp_difficulty,
                   kp.learning_order as kp_learning_order
            ORDER BY kp.learning_order
            """
            with self.neo4j_ops.driver.session(default_access_mode="READ") as session:
                result = session.run(fallback_kp_query, {
                    "project_uuid": milestone_data["project_uuid"],
                    "project_id": project_id,
                })
                all_kps = []
                for record in result:
                    all_kps.append({
                        "uuid": record.get("kp_uuid", ""),
                        "name": record.get("kp_name", ""),
                        "summary": record.get("kp_summary", ""),
                        "prerequisites_summary": record.get("kp_prerequisites_summary", ""),
                        "outcomes_summary": record.get("kp_outcomes_summary", ""),
                        "difficulty": record.get("kp_difficulty", ""),
                        "_learning_order": record.get("kp_learning_order", 0),
                    })

                # 查询该项目的里程碑总数
                ms_count_query = """
                MATCH (ms:Entity:Milestone {project_uuid: $project_uuid})
                RETURN count(ms) as total
                """
                ms_count_result = session.run(ms_count_query, {
                    "project_uuid": milestone_data["project_uuid"]
                })
                total_ms = 0
                for rec in ms_count_result:
                    total_ms = rec.get("total", 0)

                if total_ms > 0 and all_kps:
                    ms_order = milestone_data.get("order", 1)
                    total_kps = len(all_kps)
                    chunk_size = max(1, total_kps // total_ms)
                    start_idx = (ms_order - 1) * chunk_size
                    if ms_order == total_ms:
                        knowledge_points = all_kps[start_idx:]
                    else:
                        end_idx = min(start_idx + chunk_size, total_kps)
                        knowledge_points = all_kps[start_idx:end_idx]

                    # 移除内部字段
                    knowledge_points = [
                        {k: v for k, v in kp.items() if not k.startswith('_')}
                        for kp in knowledge_points
                    ]

        # 获取父项目信息
        project_uuid = milestone_data.get("project_uuid", "")
        project_query = """
        MATCH (p:Entity:Project {uuid: $project_uuid})
        RETURN p.name as project_name,
               p.outcomes_summary as project_outcomes_summary
        """

        project_info = {}
        if project_uuid:
            with self.neo4j_ops.driver.session(default_access_mode="READ") as session:
                result = session.run(project_query, {
                    "project_uuid": project_uuid
                })
                record = result.single()
                if record:
                    project_info = {
                        "name": record.get("project_name", ""),
                        "outcomes_summary": record.get("project_outcomes_summary", ""),
                    }

        return {
            "milestone": milestone_data,
            "knowledge_points": knowledge_points,
            "project": project_info,
        }

    def _format_knowledge_points(self, knowledge_points: List[Dict[str, Any]]) -> str:
        """格式化知识点信息用于提示"""
        if not knowledge_points:
            return "No specific knowledge points listed."

        lines = []
        for i, kp in enumerate(knowledge_points, 1):
            parts = [f"{i}. {kp.get('name', 'Unknown')}"]
            if kp.get("difficulty"):
                parts.append(f"   Difficulty: {kp['difficulty']}")
            if kp.get("summary"):
                parts.append(f"   Summary: {kp['summary']}")
            if kp.get("prerequisites_summary"):
                parts.append(f"   Prerequisites: {kp['prerequisites_summary']}")
            if kp.get("outcomes_summary"):
                parts.append(f"   Outcomes: {kp['outcomes_summary']}")
            lines.append("\n".join(parts))

        return "\n\n".join(lines)

    def _build_messages(self, level: int, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """根据级别和上下文构建 LLM messages"""
        milestone = context["milestone"]
        kps = context["knowledge_points"]
        project = context["project"]

        kp_info = self._format_knowledge_points(kps)
        language_instruction = get_language_instruction()

        template = L1_PROMPT_TEMPLATE if level == 1 else L2_PROMPT_TEMPLATE
        prompt_text = template.format(
            milestone_name=milestone.get("name", ""),
            milestone_order=milestone.get("order", 0),
            milestone_description=milestone.get("description", ""),
            acceptance_criteria=milestone.get("acceptance_criteria", ""),
            knowledge_points_info=kp_info,
            project_outcomes=project.get("outcomes_summary", project.get("name", "")),
            project_name=project.get("name", ""),
            language_instruction=language_instruction,
        )

        return [{"role": "user", "content": prompt_text}]

    def generate_hint(self, project_id: str, milestone_uuid: str, level: int) -> Dict[str, Any]:
        """
        生成学习提示

        Args:
            project_id: 项目ID
            milestone_uuid: 里程碑UUID
            level: 提示级别 (1 或 2)

        Returns:
            {hint_content, level, milestone_uuid, knowledge_points}
        """
        # 查询上下文数据
        context = self._fetch_milestone_context(project_id, milestone_uuid)
        if not context:
            raise ValueError(f"Milestone {milestone_uuid} not found in project {project_id}")

        # 构建提示消息
        messages = self._build_messages(level, context)

        # 调用 LLM
        max_tokens = 1024 if level == 1 else 2048
        hint_content = self.llm_client.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=max_tokens,
        )

        # 提取知识点 UUID 列表
        kp_uuids = [kp["uuid"] for kp in context["knowledge_points"] if kp.get("uuid")]

        return {
            "hint_content": hint_content,
            "level": level,
            "milestone_uuid": milestone_uuid,
            "knowledge_points": kp_uuids,
        }
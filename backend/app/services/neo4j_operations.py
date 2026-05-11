"""
Neo4j CRUD 操作
负责图谱数据的增删改查
"""

import logging
import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase

from .neo4j_manager import Neo4jManager
from ..utils.locale import t

logger = logging.getLogger(__name__)

# 安全模式：防止 Cypher 注入
SAFE_KEY_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
SAFE_LABEL_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')


class Neo4jOperations:
    """Neo4j 图谱操作类"""

    def __init__(self, driver: Optional[GraphDatabase.driver] = None):
        """
        初始化 Neo4j 操作类

        Args:
            driver: Neo4j Driver 实例，如果为 None 则自动获取
        """
        self.driver = driver or Neo4jManager.get_driver()

    def _flatten_milestones(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> tuple:
        """
        将项目节点中的 milestones 属性展开为独立的 Milestone 节点和边

        Milestone 节点会被添加到 nodes 列表中，
        MILESTONE_STEP 和 MILESTONE_REQUIRES 边会被添加到 edges 列表中，
        同时从项目节点属性中移除 milestones 键。

        Returns:
            (new_nodes, new_edges) — 包含 Milestone 节点和新边类型的更新后的列表
        """
        new_nodes = [{**n, "attributes": {**n.get("attributes", {})}} for n in nodes]
        new_edges = list(edges)

        for node in new_nodes:
            labels = node.get("labels", [])
            if "Project" not in labels:
                continue

            attrs = node.get("attributes", {})
            milestones = attrs.get("milestones", [])
            if not milestones:
                # 确保旧项目也有 milestones 字段（空数组）
                attrs["milestones"] = []
                continue

            proj_uuid = node.get("uuid", "")
            proj_name = node.get("name", "")

            # 从项目属性中移除 milestones（它们变成独立节点）
            attrs.pop("milestones", None)

            for ms in milestones:
                ms_uuid = f"ms_{uuid.uuid4().hex[:8]}"
                ms_name = ms.get("name", "")

                # 创建 Milestone 节点
                ms_node = {
                    "uuid": ms_uuid,
                    "name": ms_name,
                    "labels": ["Entity", "Milestone"],
                    "summary": ms.get("description", ""),
                    "attributes": {
                        "description": ms.get("description", ""),
                        "acceptance_criteria": ms.get("acceptance_criteria", ""),
                        "order": ms.get("order", 0),
                        "project_uuid": proj_uuid,
                    },
                    "created_at": node.get("created_at", datetime.now().isoformat()),
                }
                new_nodes.append(ms_node)

                # 创建 MILESTONE_STEP 边：Project → Milestone（带 order 属性）
                ms_step_edge = {
                    "uuid": f"edge_{uuid.uuid4().hex[:8]}",
                    "source_node_uuid": proj_uuid,
                    "target_node_uuid": ms_uuid,
                    "name": "MILESTONE_STEP",
                    "fact_type": "MILESTONE_STEP",
                    "fact": f"项目 '{proj_name}' 的第 {ms.get('order', 0)} 步里程碑：{ms_name}",
                    "episodes": [],
                    "attributes": {"order": ms.get("order", 0)},
                    "created_at": node.get("created_at", datetime.now().isoformat()),
                }
                new_edges.append(ms_step_edge)

                # 创建 MILESTONE_REQUIRES 边：Milestone → KnowledgePoint
                for kp_uuid in ms.get("knowledge_point_uuids", []):
                    ms_req_edge = {
                        "uuid": f"edge_{uuid.uuid4().hex[:8]}",
                        "source_node_uuid": ms_uuid,
                        "target_node_uuid": kp_uuid,
                        "name": "MILESTONE_REQUIRES",
                        "fact_type": "MILESTONE_REQUIRES",
                        "fact": f"里程碑 '{ms_name}' 需要知识点",
                        "episodes": [],
                        "created_at": node.get("created_at", datetime.now().isoformat()),
                    }
                    new_edges.append(ms_req_edge)

        return new_nodes, new_edges

    def add_nodes_and_edges(
        self,
        project_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        批量添加节点和边到 Neo4j

        Args:
            project_id: 项目ID（用于隔离不同项目的数据）
            nodes: 节点列表
            edges: 边列表

        Returns:
            包含节点数和边数的字典
        """
        node_count = 0
        edge_count = 0

        # 展开里程碑为独立节点和边
        nodes, edges = self._flatten_milestones(nodes, edges)

        # 创建节点
        for node_data in nodes:
            try:
                self._create_node(project_id, node_data)
                node_count += 1
            except Exception as e:
                logger.error(f"创建节点失败: {e}, 节点数据: {node_data}")

        # 创建边
        node_uuid_map = {node["uuid"]: node for node in nodes}
        for edge_data in edges:
            try:
                source_uuid = edge_data.get("source_node_uuid")
                target_uuid = edge_data.get("target_node_uuid")

                if source_uuid not in node_uuid_map:
                    logger.warning(f"边的源节点不存在: {source_uuid}")
                    continue
                if target_uuid not in node_uuid_map:
                    logger.warning(f"边的目标节点不存在: {target_uuid}")
                    continue

                self._create_edge(project_id, edge_data, node_uuid_map)
                edge_count += 1
            except Exception as e:
                logger.error(f"创建边失败: {e}, 边数据: {edge_data}")

        logger.info(f"Neo4j 添加完成: {node_count} 个节点, {edge_count} 条边")
        return {"node_count": node_count, "edge_count": edge_count}

    def _create_node(self, project_id: str, node_data: Dict[str, Any]):
        """创建单个节点"""
        node_uuid = node_data.get("uuid", str(uuid.uuid4()))
        name = node_data.get("name", "")
        labels = node_data.get("labels", [])
        summary = node_data.get("summary", "")
        attributes = node_data.get("attributes", {})
        created_at = node_data.get("created_at", datetime.now().isoformat())

        # 构建 Cypher 查询
        query = f"""
        MERGE (n:Entity {{uuid: $uuid}})
        SET n.project_id = $project_id,
            n.name = $name,
            n.summary = $summary,
            n.created_at = $created_at
        """

        # 添加标签（验证安全字符，防止 Cypher 注入）
        for label in labels:
            if label and label != "Entity" and SAFE_LABEL_PATTERN.match(label):
                query += f"\nSET n:{label}"

        # 添加属性（验证安全键名，防止 Cypher 注入）
        safe_attributes = {}
        for key, value in attributes.items():
            if key and key not in ["uuid", "name", "summary", "created_at", "project_id"] and SAFE_KEY_PATTERN.match(key):
                query += f"\nSET n.{key} = ${key}"
                safe_attributes[key] = value

        parameters = {
            "uuid": node_uuid,
            "project_id": project_id,
            "name": name,
            "summary": summary,
            "created_at": created_at,
            **safe_attributes
        }

        with self.driver.session(default_access_mode="WRITE") as session:
            session.run(query, parameters)

    def _create_edge(
        self,
        project_id: str,
        edge_data: Dict[str, Any],
        node_uuid_map: Dict[str, Dict[str, Any]]
    ):
        """创建单个边"""
        edge_uuid = edge_data.get("uuid", str(uuid.uuid4()))
        source_uuid = edge_data.get("source_node_uuid")
        target_uuid = edge_data.get("target_node_uuid")
        fact_type = edge_data.get("fact_type", "RELATIONSHIP")
        fact = edge_data.get("fact", "")
        episodes = edge_data.get("episodes", [])
        attributes = edge_data.get("attributes", {})
        created_at = edge_data.get("created_at", datetime.now().isoformat())

        # 获取源节点和目标节点的名称
        source_node = node_uuid_map.get(source_uuid, {})
        target_node = node_uuid_map.get(target_uuid, {})
        source_name = source_node.get("name", "")
        target_name = target_node.get("name", "")

        # 构建 Cypher 查询（使用有向边，方向对学习路径边很重要）
        query = """
        MATCH (source:Entity {uuid: $source_uuid, project_id: $project_id})
        MATCH (target:Entity {uuid: $target_uuid, project_id: $project_id})
        MERGE (source)-[r:RELATIONSHIP {uuid: $uuid}]->(target)
        SET r.project_id = $project_id,
            r.fact_type = $fact_type,
            r.fact = $fact,
            r.source_node_uuid = $source_uuid,
            r.target_node_uuid = $target_uuid,
            r.source_node_name = $source_name,
            r.target_node_name = $target_name,
            r.created_at = $created_at
        """

        # 添加 episodes 属性
        if episodes:
            query += "\nSET r.episodes = $episodes"

        # 添加其他属性（验证安全键名，防止 Cypher 注入）
        safe_edge_attributes = {}
        for key, value in attributes.items():
            if key and key not in ["uuid", "fact_type", "fact", "source_node_uuid", "target_node_uuid",
                                   "source_node_name", "target_node_name", "created_at", "project_id", "episodes"] and SAFE_KEY_PATTERN.match(key):
                query += f"\nSET r.{key} = ${key}"
                safe_edge_attributes[key] = value

        parameters = {
            "uuid": edge_uuid,
            "project_id": project_id,
            "source_uuid": source_uuid,
            "target_uuid": target_uuid,
            "fact_type": fact_type,
            "fact": fact,
            "source_name": source_name,
            "target_name": target_name,
            "created_at": created_at,
            "episodes": episodes,
            **safe_edge_attributes
        }

        with self.driver.session(default_access_mode="WRITE") as session:
            session.run(query, parameters)

    def get_graph_data(self, project_id: str) -> Dict[str, Any]:
        """
        获取图谱数据

        Args:
            project_id: 项目ID

        Returns:
            包含节点和边的字典
        """
        # 查询节点
        node_query = """
        MATCH (n:Entity {project_id: $project_id})
        RETURN n.uuid as uuid,
               n.name as name,
               labels(n) as labels,
               n.summary as summary,
               n.created_at as created_at,
               properties(n) as attributes
        """

        with self.driver.session(default_access_mode="READ") as session:
            node_result = session.run(node_query, {"project_id": project_id})
            nodes_data = []
            for record in node_result:
                attributes = record.get("attributes", {})
                # 移除系统属性和 None 值
                attributes = {
                    k: v for k, v in attributes.items()
                    if k not in ["uuid", "name", "summary", "created_at", "project_id"] and v is not None
                }

                nodes_data.append({
                    "uuid": record["uuid"],
                    "name": record["name"],
                    "labels": record["labels"],
                    "summary": record.get("summary", ""),
                    "attributes": attributes,
                    "created_at": record.get("created_at", ""),
                })

            # 查询边（使用有向模式）
            edge_query = """
            MATCH (source:Entity {project_id: $project_id})-[r:RELATIONSHIP {project_id: $project_id}]->(target:Entity {project_id: $project_id})
            RETURN r.uuid as uuid,
                   r.fact_type as fact_type,
                   r.fact as fact,
                   r.source_node_uuid as source_node_uuid,
                   r.target_node_uuid as target_node_uuid,
                   r.source_node_name as source_node_name,
                   r.target_node_name as target_node_name,
                   r.created_at as created_at,
                   r.episodes as episodes,
                   properties(r) as edge_attributes
            """

            edge_result = session.run(edge_query, {"project_id": project_id})
            edges_data = []
            for record in edge_result:
                # 提取边属性，移除系统属性
                edge_attributes = record.get("edge_attributes", {})
                edge_attributes = {
                    k: v for k, v in edge_attributes.items()
                    if k not in ["uuid", "fact_type", "fact", "source_node_uuid", "target_node_uuid",
                                  "source_node_name", "target_node_name", "created_at", "project_id",
                                  "episodes"] and v is not None
                }

                edges_data.append({
                    "uuid": record["uuid"],
                    "name": record.get("fact_type", ""),
                    "fact_type": record.get("fact_type", ""),
                    "fact": record.get("fact", ""),
                    "source_node_uuid": record["source_node_uuid"],
                    "target_node_uuid": record["target_node_uuid"],
                    "source_node_name": record.get("source_node_name", ""),
                    "target_node_name": record.get("target_node_name", ""),
                    "created_at": record.get("created_at", ""),
                    "episodes": record.get("episodes", []),
                    "attributes": edge_attributes
                })

            return {
                "graph_id": project_id,
                "nodes": nodes_data,
                "edges": edges_data,
                "node_count": len(nodes_data),
                "edge_count": len(edges_data),
            }

    def delete_graph(self, project_id: str) -> bool:
        """
        删除图谱

        Args:
            project_id: 项目ID

        Returns:
            是否删除成功
        """
        try:
            # 删除边
            delete_edges_query = """
            MATCH ()-[r:RELATIONSHIP {project_id: $project_id}]-()
            DELETE r
            """

            # 删除节点
            delete_nodes_query = """
            MATCH (n:Entity {project_id: $project_id})
            DELETE n
            """

            with self.driver.session(default_access_mode="WRITE") as session:
                session.run(delete_edges_query, {"project_id": project_id})
                session.run(delete_nodes_query, {"project_id": project_id})

            logger.info(f"Neo4j 图谱已删除: project_id={project_id}")
            return True

        except Exception as e:
            logger.error(f"删除图谱失败: {e}")
            return False

    def get_graph_stats(self, project_id: str) -> Dict[str, int]:
        """
        获取图谱统计信息

        Args:
            project_id: 项目ID

        Returns:
            统计信息字典
        """
        node_query = """
        MATCH (n:Entity {project_id: $project_id})
        RETURN count(n) as node_count
        """

        edge_query = """
        MATCH ()-[r:RELATIONSHIP {project_id: $project_id}]-()
        RETURN count(r) as edge_count
        """

        label_query = """
        MATCH (n:Entity {project_id: $project_id})
        UNWIND labels(n) AS label
        WITH label, count(label) AS count
        WHERE label <> 'Entity'
        RETURN label, count
        """

        with self.driver.session() as session:
            node_result = session.run(node_query, {"project_id": project_id})
            node_count = node_result.single()["node_count"]

            edge_result = session.run(edge_query, {"project_id": project_id})
            edge_count = edge_result.single()["edge_count"]

            label_result = session.run(label_query, {"project_id": project_id})
            entity_types = {record["label"]: record["count"] for record in label_result}

            return {
                "node_count": node_count,
                "edge_count": edge_count,
                "entity_types": entity_types
            }

    def get_learning_path(self, project_id: str) -> Dict[str, Any]:
        """
        获取学习路径结构（支持 PBL 模式和知识驱动模式）

        Args:
            project_id: 项目ID

        Returns:
            学习路径结构信息
        """
        # 获取所有节点
        node_query = """
        MATCH (n:Entity {project_id: $project_id})
        RETURN n.uuid as uuid,
               n.name as name,
               labels(n) as labels,
               n.summary as summary,
               properties(n) as attributes
        """

        # 获取所有边
        edge_query = """
        MATCH (source:Entity {project_id: $project_id})-[r:RELATIONSHIP {project_id: $project_id}]->(target:Entity {project_id: $project_id})
        RETURN r.uuid as uuid,
               r.fact_type as fact_type,
               r.fact as fact,
               r.source_node_uuid as source_node_uuid,
               r.target_node_uuid as target_node_uuid,
               properties(r) as edge_attributes
        """

        with self.driver.session(default_access_mode="READ") as session:
            node_result = session.run(node_query, {"project_id": project_id})
            nodes = []
            node_map = {}
            for record in node_result:
                attributes = record.get("attributes", {})
                attributes = {
                    k: v for k, v in attributes.items()
                    if k not in ["uuid", "name", "summary", "created_at", "project_id"] and v is not None
                }
                node_data = {
                    "uuid": record["uuid"],
                    "name": record["name"],
                    "labels": record["labels"],
                    "summary": record.get("summary", ""),
                    "attributes": attributes,
                }
                nodes.append(node_data)
                node_map[record["uuid"]] = node_data

            edge_result = session.run(edge_query, {"project_id": project_id})
            edges = []
            for record in edge_result:
                # 提取边属性，移除系统属性
                edge_attributes = record.get("edge_attributes", {})
                edge_attributes = {
                    k: v for k, v in edge_attributes.items()
                    if k not in ["uuid", "fact_type", "fact", "source_node_uuid", "target_node_uuid",
                                  "source_node_name", "target_node_name", "created_at", "project_id",
                                  "episodes"] and v is not None
                }
                edges.append({
                    "uuid": record["uuid"],
                    "fact_type": record.get("fact_type", ""),
                    "fact": record.get("fact", ""),
                    "source_node_uuid": record["source_node_uuid"],
                    "target_node_uuid": record["target_node_uuid"],
                    "attributes": edge_attributes,
                })

        # 检测模式：是否有 Project 节点
        has_project_nodes = any("Project" in n.get("labels", []) for n in nodes)

        if has_project_nodes:
            return self._compute_pbl_learning_path(nodes, edges, node_map)
        else:
            return self._compute_knowledge_driven_learning_path(nodes, edges, node_map)

    def _compute_pbl_learning_path(self, nodes, edges, node_map):
        """计算 PBL 模式的学习路径结构（里程碑 + 知识点链）"""

        # 收集各类边
        next_step_edges = [e for e in edges if e.get("fact_type") == "NEXT_STEP"]
        requires_edges = [e for e in edges if e.get("fact_type") == "REQUIRES"]
        prerequisite_edges = [e for e in edges if e.get("fact_type") == "PREREQUISITE_OF"]
        milestone_step_edges = [e for e in edges if e.get("fact_type") == "MILESTONE_STEP"]
        milestone_requires_edges = [e for e in edges if e.get("fact_type") == "MILESTONE_REQUIRES"]

        # 所有 Project 节点
        project_uuids = {n["uuid"] for n in nodes if "Project" in n.get("labels", [])}
        # 所有 Milestone 节点
        milestone_uuids = {n["uuid"] for n in nodes if "Milestone" in n.get("labels", [])}
        has_milestone_nodes = len(milestone_uuids) > 0

        # 构建 NEXT_STEP 邻接表（只看 Project→Project）
        next_step_adj = {}
        next_step_in = {}
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

        # 主路径：从没有入边的 Project 开始追踪
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

        # 分支项目
        branch_projects = [uid for uid in project_uuids if uid not in main_path_set]

        # REQUIRES 边：Project→KP（单向）+ 旧项目 KP→Project（向后兼容）
        requires_from_project = {}  # project_uuid -> [kp_uuids] (Project→KP)
        requires_to_project = {}    # project_uuid -> [kp_uuids] (KP→Project, 旧项目环形闭合)
        for edge in requires_edges:
            src = edge["source_node_uuid"]
            tgt = edge["target_node_uuid"]
            if src in project_uuids and tgt not in project_uuids and tgt not in milestone_uuids:
                # Project → KP
                if src not in requires_from_project:
                    requires_from_project[src] = []
                requires_from_project[src].append(tgt)
            elif tgt in project_uuids and src not in project_uuids and src not in milestone_uuids:
                # KP → Project（旧项目环形闭合，向后兼容）
                if tgt not in requires_to_project:
                    requires_to_project[tgt] = []
                requires_to_project[tgt].append(src)

        # PREREQUISITE_OF 邻接表
        prereq_adj = {}  # source_kp -> [target_kps]
        for edge in prerequisite_edges:
            src = edge["source_node_uuid"]
            tgt = edge["target_node_uuid"]
            if src not in prereq_adj:
                prereq_adj[src] = []
            prereq_adj[src].append(tgt)

        # MILESTONE_STEP 边：Project → Milestone
        milestone_step_map = {}  # project_uuid -> [(milestone_uuid, order)]
        for edge in milestone_step_edges:
            src = edge["source_node_uuid"]
            tgt = edge["target_node_uuid"]
            # order stored on edge attributes (MILESTONE_STEP has order attribute)
            edge_attrs = edge.get("attributes", {})
            order = edge_attrs.get("order", 0) if isinstance(edge_attrs, dict) else 0
            # Fallback: read order from Milestone node attributes if not on edge
            if order == 0:
                order = node_map.get(tgt, {}).get("attributes", {}).get("order", 0)
            if src not in milestone_step_map:
                milestone_step_map[src] = []
            milestone_step_map[src].append((tgt, order))

        # MILESTONE_REQUIRES 边：Milestone → KP
        milestone_requires_map = {}  # milestone_uuid -> [kp_uuids]
        for edge in milestone_requires_edges:
            src = edge["source_node_uuid"]
            tgt = edge["target_node_uuid"]
            if src not in milestone_requires_map:
                milestone_requires_map[src] = []
            milestone_requires_map[src].append(tgt)

        # 计算每个项目的知识链和里程碑
        project_knowledge_subgraphs = {}
        for proj_uuid in project_uuids:
            # 起点知识点（项目 REQUIRES 的 KP）
            start_kps = requires_from_project.get(proj_uuid, [])
            # 旧项目：环形闭合的终点 KP（向后兼容）
            end_kps = requires_to_project.get(proj_uuid, [])

            # 通过 PREREQUISITE_OF 追踪完整的知识链
            all_kps_in_chain = set(start_kps + end_kps)
            visited_kps = set()
            queue = list(start_kps)

            while queue:
                current_kp = queue.pop(0)
                if current_kp in visited_kps:
                    continue
                visited_kps.add(current_kp)
                all_kps_in_chain.add(current_kp)
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

            # 从 Milestone 节点构建里程碑列表
            milestones = []
            if has_milestone_nodes:
                ms_list = milestone_step_map.get(proj_uuid, [])
                ms_list.sort(key=lambda x: x[1])
                for ms_uuid, ms_order in ms_list:
                    ms_node = node_map.get(ms_uuid, {})
                    ms_attrs = ms_node.get("attributes", {})
                    milestones.append({
                        "name": ms_node.get("name", ""),
                        "order": ms_attrs.get("order", ms_order),
                        "description": ms_attrs.get("description", ""),
                        "acceptance_criteria": ms_attrs.get("acceptance_criteria", ""),
                        "knowledge_point_uuids": milestone_requires_map.get(ms_uuid, []),
                    })

            project_knowledge_subgraphs[proj_uuid] = {
                "knowledge_chain": sorted_kps,
                "entry_points": entry_kps,
                "exit_points": exit_kps,
                "has_milestones": len(milestones) > 0,
                "milestones": milestones,
                # 向后兼容：旧项目可能有环形闭合
                "ring_closed": len(end_kps) > 0 if not has_milestone_nodes else False,
            }

        # 按难度分组
        learning_stages = {"beginner": [], "intermediate": [], "advanced": []}
        for n in nodes:
            difficulty = n.get("attributes", {}).get("difficulty", "intermediate")
            if difficulty in learning_stages:
                learning_stages[difficulty].append(n["uuid"])

        entry_points = [main_path[0]] if main_path else []
        exit_points = [main_path[-1]] if main_path else []

        return {
            "mode": "pbl",
            "main_path": main_path,
            "branch_projects": branch_projects,
            "project_knowledge_subgraphs": project_knowledge_subgraphs,
            "entry_points": entry_points,
            "exit_points": exit_points,
            "learning_stages": learning_stages
        }

    def _compute_knowledge_driven_learning_path(self, nodes, edges, node_map):
        """计算旧知识驱动模式的学习路径结构（向后兼容）"""

        # 收集各类边
        prerequisite_edges = [e for e in edges if e.get("fact_type") == "PREREQUISITE_OF"]
        next_step_edges = [e for e in edges if e.get("fact_type") == "NEXT_STEP"]
        branches_from_edges = [e for e in edges if e.get("fact_type") == "BRANCHES_FROM"]
        merges_to_edges = [e for e in edges if e.get("fact_type") == "MERGES_TO"]

        # 入口点
        nodes_with_prerequisites = {e["target_node_uuid"] for e in prerequisite_edges}
        entry_points = [n["uuid"] for n in nodes if n["uuid"] not in nodes_with_prerequisites]

        # 出口点
        nodes_with_outgoing = {e["source_node_uuid"] for e in prerequisite_edges}
        exit_points = [n["uuid"] for n in nodes if n["uuid"] not in nodes_with_outgoing]

        # 主路径
        main_path = []
        if next_step_edges:
            next_step_map = {e["source_node_uuid"]: e["target_node_uuid"] for e in next_step_edges}
            next_step_targets = set(next_step_map.values())
            main_start_nodes = set(next_step_map.keys()) - next_step_targets

            if main_start_nodes:
                start_uuid = sorted(main_start_nodes)[0]
                current = start_uuid
                visited = set()
                while current and current not in visited:
                    main_path.append(current)
                    visited.add(current)
                    current = next_step_map.get(current)
        elif nodes:
            main_path = sorted(
                [n["uuid"] for n in nodes if n.get("attributes", {}).get("path_type") == "main"],
                key=lambda uid: node_map[uid].get("attributes", {}).get("learning_order", 0)
            )

        # 分支路径
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
            merges_to_map[edge["source_node_uuid"]] = edge["target_node_uuid"]

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

                merge_to_uuid = None
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

        # 按难度分组
        learning_stages = {"beginner": [], "intermediate": [], "advanced": []}
        for n in nodes:
            difficulty = n.get("attributes", {}).get("difficulty", "intermediate")
            if difficulty in learning_stages:
                learning_stages[difficulty].append(n["uuid"])

        return {
            "mode": "knowledge_driven",
            "main_path": main_path,
            "branch_paths": branch_paths,
            "entry_points": entry_points,
            "exit_points": exit_points,
            "learning_stages": learning_stages
        }

    def update_node_attribute(self, project_id: str, node_uuid: str, attribute_name: str, attribute_value: Any) -> bool:
        """
        更新节点的单个属性（带重试，应对 AuraDB 连接断开）

        Args:
            project_id: 项目ID
            node_uuid: 节点UUID
            attribute_name: 属性名
            attribute_value: 属性值

        Returns:
            是否更新成功
        """
        # 验证属性名安全性（防止 Cypher 注入）
        if not SAFE_KEY_PATTERN.match(attribute_name):
            logger.error(f"非法属性名: {attribute_name}")
            return False

        query = f"""
        MATCH (n:Entity {{uuid: $uuid, project_id: $project_id}})
        SET n.{attribute_name} = $value
        """

        params = {
            "uuid": node_uuid,
            "project_id": project_id,
            "value": attribute_value
        }

        for attempt in range(2):
            try:
                with self.driver.session(default_access_mode="WRITE") as session:
                    result = session.run(query, params)
                    summary = result.consume()
                    updated = summary.counters.properties_set > 0
                    if updated:
                        logger.info(f"节点属性已更新: uuid={node_uuid}, {attribute_name}={attribute_value}")
                    else:
                        logger.warning(f"节点未找到或属性未变更: uuid={node_uuid}")
                    return True
            except Exception as e:
                logger.error(f"更新节点属性失败 (attempt {attempt + 1}/2): {e}")
                if attempt == 0:
                    # 连接可能断了，重置驱动让下次拿新连接
                    try:
                        Neo4jManager.close()
                        self.driver = Neo4jManager.get_driver()
                    except Exception as reset_err:
                        logger.error(f"重置 Neo4j Driver 失败: {reset_err}")
                else:
                    return False

        return False

    def get_node_detail(self, project_id: str, node_uuid: str) -> Optional[Dict[str, Any]]:
        """
        获取节点详细信息

        Args:
            project_id: 项目ID
            node_uuid: 节点UUID

        Returns:
            节点详情字典，包含 name, labels, summary, attributes
        """
        query = """
        MATCH (n:Entity {uuid: $uuid, project_id: $project_id})
        RETURN n.uuid as uuid,
               n.name as name,
               labels(n) as labels,
               n.summary as summary,
               properties(n) as attributes
        """

        try:
            with self.driver.session(default_access_mode="READ") as session:
                result = session.run(query, {
                    "uuid": node_uuid,
                    "project_id": project_id
                })
                record = result.single()
                if not record:
                    return None

                attributes = record.get("attributes", {})
                # 过滤掉系统属性
                attributes = {
                    k: v for k, v in attributes.items()
                    if k not in ["uuid", "name", "summary", "created_at", "project_id"] and v is not None
                }

                return {
                    "uuid": record["uuid"],
                    "name": record["name"],
                    "labels": record["labels"],
                    "summary": record.get("summary", ""),
                    "attributes": attributes
                }
        except Exception as e:
            logger.error(f"获取节点详情失败: {e}")
            return None

    def _serialize_neo4j_value(self, v: Any) -> Any:
        """将 Neo4j 特殊类型转为 JSON 可序列化的值"""
        if v is None:
            return None
        # neo4j.time.DateTime / neo4j.time.Date 等
        if hasattr(v, 'iso_format'):
            return v.iso_format()
        if hasattr(v, '__str__') and 'neo4j.time' in type(v).__module__:
            return str(v)
        if isinstance(v, (list,)):
            return [self._serialize_neo4j_value(item) for item in v]
        if isinstance(v, dict):
            return {k: self._serialize_neo4j_value(val) for k, val in v.items()}
        return v

    def _clean_graphiti_props(self, props: dict, skip_keys: set) -> dict:
        """清理 Graphiti 属性：移除内部字段 + 序列化 Neo4j 类型"""
        return {
            k: self._serialize_neo4j_value(v)
            for k, v in props.items()
            if k not in skip_keys and v is not None
        }

    def get_graphiti_graph_data(self, group_id: str) -> Dict[str, Any]:
        """
        从 Graphiti 的 Neo4j schema 获取图谱数据

        只查询前端需要的字段，不拉取 embedding 向量等大数据。
        """
        nodes = []
        edges = []

        try:
            with self.driver.session(default_access_mode="READ") as session:
                # 查询 Entity 节点 — 只拉必要字段，不拉 embedding
                node_query = """
                MATCH (n:Entity)
                WHERE n.group_id = $group_id
                RETURN n.uuid as uuid, n.name as name, labels(n) as labels,
                       n.summary as summary
                """
                node_result = session.run(node_query, {"group_id": group_id})

                for record in node_result:
                    uuid_val = record.get("uuid", "")
                    name = record.get("name", "")
                    labels = list(record.get("labels", []))
                    summary = record.get("summary", "")

                    nodes.append({
                        "uuid": uuid_val,
                        "name": name,
                        "labels": labels,
                        "summary": summary or "",
                        "attributes": {},
                    })

                # 查询关系边 — 只拉必要字段
                edge_query = """
                MATCH (s:Entity)-[r]->(t:Entity)
                WHERE s.group_id = $group_id AND t.group_id = $group_id
                RETURN r.uuid as uuid, type(r) as rel_type,
                       r.name as name, r.fact as fact,
                       s.uuid as source_uuid, t.uuid as target_uuid
                """
                edge_result = session.run(edge_query, {"group_id": group_id})

                for record in edge_result:
                    edges.append({
                        "uuid": record.get("uuid", ""),
                        "source_node_uuid": record.get("source_uuid", ""),
                        "target_node_uuid": record.get("target_uuid", ""),
                        "name": record.get("name", ""),
                        "fact_type": record.get("rel_type", ""),
                        "fact": record.get("fact", ""),
                        "episodes": [],
                        "attributes": {},
                    })

        except Exception as e:
            logger.error(f"获取 Graphiti 图谱数据失败: {e}")
            raise

        return {"nodes": nodes, "edges": edges}

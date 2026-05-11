"""
图谱相关API路由
采用项目上下文机制，服务端持久化状态
使用 Neo4j 作为图谱存储，支持 Graphiti 数据查询
"""

import os
import traceback
from flask import request, jsonify

from . import graph_bp
from ..config import Config
from ..services.graph_extractor import GraphExtractor
from ..services.neo4j_operations import Neo4jOperations
from ..services.text_processor import TextProcessor
from ..utils.file_parser import FileParser
from ..utils.logger import get_logger
from ..utils.locale import t, get_locale, set_locale
from ..models.project import ProjectManager, ProjectStatus
from ..utils.async_bridge import AsyncBridge
from ..services.graphiti_service import GraphitiService

# 获取日志器
logger = get_logger('evolith.api')


def _bulk_assign_kps(milestones, project_id, neo4j_ops):
    """
    批量为没有 MILESTONE_REQUIRES 边的里程碑分配知识点。

    一次性查询所有项目及其知识点和里程碑计数，
    然后在 Python 中按 learning_order 均匀分段分配。
    """
    # 找出需要 fallback 的里程碑（按 project_uuid 分组）
    need_fallback = {}  # project_uuid -> [(ms_order, ms_index_in_list)]
    for i, ms in enumerate(milestones):
        if not ms.get("knowledge_points"):
            puuid = ms.get("project_uuid", "")
            if puuid and puuid not in need_fallback:
                need_fallback[puuid] = []
            if puuid:
                need_fallback[puuid].append((ms.get("order", 1), i))

    if not need_fallback:
        return milestones

    # 一次性查询所有需要的项目数据
    project_uuids = list(need_fallback.keys())

    # 查询每个项目的里程碑总数和知识点
    bulk_query = """
    UNWIND $project_uuids AS puuid
    MATCH (p:Entity:Project {uuid: puuid, project_id: $project_id})
    OPTIONAL MATCH (p)-[r_ms:RELATIONSHIP {fact_type: 'MILESTONE_STEP'}]->(ms:Entity:Milestone {project_uuid: puuid})
    OPTIONAL MATCH (p)-[r_req:RELATIONSHIP {fact_type: 'REQUIRES'}]->(kp:Entity)
    WHERE (kp.project_id = $project_id OR kp.project_id IS NULL)
      AND (kp.required_by = p.name OR kp.required_by IS NULL OR kp.required_by = '')
    RETURN p.uuid as project_uuid,
           p.name as project_name,
           count(DISTINCT ms) as total_milestones,
           collect(DISTINCT {
               uuid: kp.uuid,
               name: kp.name,
               difficulty: kp.difficulty,
               summary: kp.summary,
               learning_order: kp.learning_order,
               classroom_id: kp.classroom_id
           }) as knowledge_points
    """

    project_data = {}  # project_uuid -> {total_ms, kps}
    with neo4j_ops.driver.session(default_access_mode="READ") as session:
        result = session.run(bulk_query, {
            "project_uuids": project_uuids,
            "project_id": project_id,
        })
        for record in result:
            puuid = record.get("project_uuid", "")
            total_ms = record.get("total_milestones", 0)
            kps = [kp for kp in record.get("knowledge_points", []) if kp.get("uuid") is not None]
            # 按 learning_order 排序
            kps.sort(key=lambda kp: kp.get("learning_order", 0) or 0)
            project_data[puuid] = {"total_ms": total_ms, "kps": kps}

    # 执行分配
    for puuid, ms_entries in need_fallback.items():
        pdata = project_data.get(puuid, {})
        total_ms = pdata.get("total_ms", 0)
        all_kps = pdata.get("kps", [])

        if total_ms == 0 or not all_kps:
            continue

        total_kps = len(all_kps)
        chunk_size = max(1, total_kps // total_ms)

        for ms_order, ms_index in ms_entries:
            start_idx = (ms_order - 1) * chunk_size
            if ms_order == total_ms:
                assigned = all_kps[start_idx:]
            else:
                end_idx = min(start_idx + chunk_size, total_kps)
                assigned = all_kps[start_idx:end_idx]

            # 清理内部字段
            clean_kps = [
                {k: v for k, v in kp.items() if k in ("uuid", "name", "difficulty", "summary")}
                for kp in assigned
            ]
            milestones[ms_index]["knowledge_points"] = clean_kps

    return milestones


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    if not filename or '.' not in filename:
        return False
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    return ext in Config.ALLOWED_EXTENSIONS


# ============== 项目管理接口 ==============

@graph_bp.route('/project/<project_id>', methods=['GET'])
def get_project(project_id: str):
    """
    获取项目详情
    """
    project = ProjectManager.get_project(project_id)

    if not project:
        return jsonify({
            "success": False,
            "error": t('api.projectNotFound', id=project_id)
        }), 404

    return jsonify({
        "success": True,
        "data": project.to_dict()
    })


@graph_bp.route('/project/list', methods=['GET'])
def list_projects():
    """
    列出所有项目
    """
    limit = request.args.get('limit', 50, type=int)
    projects = ProjectManager.list_projects(limit=limit)

    return jsonify({
        "success": True,
        "data": [p.to_dict() for p in projects],
        "count": len(projects)
    })


@graph_bp.route('/project/<project_id>', methods=['DELETE'])
def delete_project(project_id: str):
    """
    删除项目
    """
    project = ProjectManager.get_project(project_id)

    if project:
        # 如果项目有图谱，从 Neo4j 删除
        if project.status == ProjectStatus.GRAPH_COMPLETED:
            try:
                neo4j_ops = Neo4jOperations()
                neo4j_ops.delete_graph(project_id)
                logger.info(f"Neo4j 图谱已删除: {project_id}")
            except Exception as e:
                logger.error(f"删除 Neo4j 图谱失败: {e}")

    success = ProjectManager.delete_project(project_id)

    if not success:
        return jsonify({
            "success": False,
            "error": t('api.projectDeleteFailed', id=project_id)
        }), 404

    return jsonify({
        "success": True,
        "message": t('api.projectDeleted', id=project_id)
    })


@graph_bp.route('/project/<project_id>/reset', methods=['POST'])
def reset_project(project_id: str):
    """
    重置项目状态（用于重新构建图谱）
    """
    project = ProjectManager.get_project(project_id)

    if not project:
        return jsonify({
            "success": False,
            "error": t('api.projectNotFound', id=project_id)
        }), 404

    # 重置到刚创建状态
    project.status = ProjectStatus.CREATED
    project.graph_data = None
    project.analysis_summary = None
    project.node_count = 0
    project.edge_count = 0
    project.error = None
    ProjectManager.save_project(project)

    return jsonify({
        "success": True,
        "message": t('api.projectReset', id=project_id),
        "data": project.to_dict()
    })


# ============== 接口1：上传文件并提取图谱 ==============

@graph_bp.route('/extract', methods=['POST'])
def extract_graph():
    """
    接口1：上传文件，提取图谱数据

    请求方式：multipart/form-data

    参数：
        files: 上传的文件（PDF/MD/TXT），可多个
        course_description: 课程描述（必填）
        project_name: 项目名称（可选）
        additional_context: 额外说明（可选）

    返回：
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "graph_data": {
                    "nodes": [...],
                    "edges": [...]
                },
                "analysis_summary": "...",
                "files": [...],
                "node_count": 30,
                "edge_count": 45
            }
        }
    """
    try:
        logger.info("=== 开始提取图谱 ===")

        # 获取参数
        course_description = request.form.get('course_description', '')
        project_name = request.form.get('project_name', 'Unnamed Project')
        additional_context = request.form.get('additional_context', '')

        logger.debug(f"项目名称: {project_name}")
        logger.debug(f"课程描述: {course_description[:100]}...")

        if not course_description:
            return jsonify({
                "success": False,
                "error": t('api.requireCourseDescription')
            }), 400

        # 获取上传的文件（可选）
        uploaded_files = request.files.getlist('files')
        has_files = uploaded_files and any(f.filename for f in uploaded_files)

        # 创建项目
        project = ProjectManager.create_project(name=project_name)
        project.course_description = course_description
        logger.info(f"创建项目: {project.project_id}")

        # 保存文件并提取文本（文件为可选）
        document_texts = []
        all_text = ""

        if has_files:
            for file in uploaded_files:
                if file and file.filename and allowed_file(file.filename):
                    # 保存文件到项目目录
                    file_info = ProjectManager.save_file_to_project(
                        project.project_id,
                        file,
                        file.filename
                    )
                    project.files.append({
                        "filename": file_info["original_filename"],
                        "size": file_info["size"]
                    })

                    # 提取文本
                    text = FileParser.extract_text(file_info["path"])
                    text = TextProcessor.preprocess_text(text)
                    document_texts.append(text)
                    all_text += f"\n\n=== {file_info['original_filename']} ===\n{text}"

        # 保存提取的文本
        project.total_text_length = len(all_text)
        ProjectManager.save_extracted_text(project.project_id, all_text)
        logger.info(f"文本提取完成，共 {len(all_text)} 字符")

        # 提取图谱
        logger.info("调用 LLM 提取图谱...")
        extractor = GraphExtractor()
        graph_data = extractor.extract(
            document_texts=document_texts,
            course_description=course_description,
            additional_context=additional_context if additional_context else None
        )

        # 保存图谱数据到项目
        node_count = len(graph_data.get("nodes", []))
        edge_count = len(graph_data.get("edges", []))
        logger.info(f"图谱提取完成: {node_count} 个节点, {edge_count} 条边")

        project.graph_data = {
            "nodes": graph_data.get("nodes", []),
            "edges": graph_data.get("edges", [])
        }
        project.analysis_summary = graph_data.get("analysis_summary", "")
        project.node_count = node_count
        project.edge_count = edge_count
        project.status = ProjectStatus.GRAPH_EXTRACTED
        ProjectManager.save_project(project)
        logger.info(f"=== 图谱提取完成 === 项目ID: {project.project_id}")

        return jsonify({
            "success": True,
            "data": {
                "project_id": project.project_id,
                "project_name": project.name,
                "graph_data": project.graph_data,
                "analysis_summary": project.analysis_summary,
                "node_count": project.node_count,
                "edge_count": project.edge_count,
                "files": project.files,
                "total_text_length": project.total_text_length
            }
        })

    except Exception as e:
        logger.error(f"提取图谱失败: {str(e)}")
        logger.error(f"详细错误堆栈:\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 接口2：存储图谱 ==============

@graph_bp.route('/store', methods=['POST'])
def store_graph():
    """
    接口2：将提取的图谱数据存储到 Neo4j

    请求（JSON）：
        {
            "project_id": "proj_xxxx"  // 必填，来自接口1
        }

    返回：
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "node_count": 30,
                "edge_count": 45,
                "message": "图谱已存储到 Neo4j"
            }
        }
    """
    try:
        logger.info("=== 开始存储图谱 ===")

        # 检查配置
        errors = Config.validate()
        if errors:
            logger.error(f"配置错误: {errors}")
            return jsonify({
                "success": False,
                "error": t('api.configError', details="; ".join(errors))
            }), 500

        # 解析请求
        data = request.get_json() or {}
        project_id = data.get('project_id')
        logger.debug(f"请求参数: project_id={project_id}")

        if not project_id:
            return jsonify({
                "success": False,
                "error": t('api.requireProjectId')
            }), 400

        # 获取项目
        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": t('api.projectNotFound', id=project_id)
            }), 404

        # 检查项目状态
        if project.status == ProjectStatus.CREATED:
            return jsonify({
                "success": False,
                "error": t('api.graphNotExtracted')
            }), 400

        # 如果已经完成，直接返回
        if project.status == ProjectStatus.GRAPH_COMPLETED:
            return jsonify({
                "success": True,
                "data": {
                    "project_id": project_id,
                    "node_count": project.node_count,
                    "edge_count": project.edge_count,
                    "message": "图谱已存在"
                }
            })

        # 获取图谱数据
        graph_data = project.graph_data
        if not graph_data:
            return jsonify({
                "success": False,
                "error": t('api.graphDataNotFound')
            }), 400

        # 存储到 Neo4j
        logger.info(f"存储图谱到 Neo4j: {project_id}")
        neo4j_ops = Neo4jOperations()
        result = neo4j_ops.add_nodes_and_edges(
            project_id=project_id,
            nodes=graph_data.get("nodes", []),
            edges=graph_data.get("edges", [])
        )

        # 更新项目状态
        project.node_count = result.get("node_count", 0)
        project.edge_count = result.get("edge_count", 0)
        project.status = ProjectStatus.GRAPH_COMPLETED
        ProjectManager.save_project(project)

        logger.info(f"=== 图谱存储完成 === project_id: {project_id}, 节点: {project.node_count}, 边: {project.edge_count}")

        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "node_count": project.node_count,
                "edge_count": project.edge_count,
                "message": t('api.graphStored')
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 图谱数据接口 ==============

@graph_bp.route('/data/<graph_id>', methods=['GET'])
def get_graph_data(graph_id: str):
    """
    获取图谱数据（节点和边）
    """
    try:
        neo4j_ops = Neo4jOperations()
        graph_data = neo4j_ops.get_graph_data(graph_id)

        # 检查是否有数据
        if not graph_data.get("nodes") and not graph_data.get("edges"):
            return jsonify({
                "success": False,
                "error": "Graph data not found in Neo4j",
                "code": "NEO4J_DATA_NOT_FOUND"
            }), 404

        return jsonify({
            "success": True,
            "data": graph_data
        })

    except Exception as e:
        logger.warning(f"Failed to get graph data from Neo4j: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "code": "NEO4J_ERROR"
        }), 404


@graph_bp.route('/delete/<graph_id>', methods=['DELETE'])
def delete_graph(graph_id: str):
    """
    删除 Neo4j 图谱
    """
    try:
        neo4j_ops = Neo4jOperations()
        success = neo4j_ops.delete_graph(graph_id)

        if success:
            return jsonify({
                "success": True,
                "message": t('api.graphDeleted', id=graph_id)
            })
        else:
            return jsonify({
                "success": False,
                "error": t('api.graphDeleteFailed', id=graph_id)
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 里程碑接口 ==============

@graph_bp.route('/milestones/<project_id>', methods=['GET'])
def get_milestones(project_id: str):
    """
    获取项目的里程碑列表及关联的知识点

    查询参数：
        pbl: PBL Project 节点的 UUID（可选）。如果提供，只返回该 PBL 项目的里程碑；
             如果不提供，返回该 Evolith 项目所有 PBL 项目的里程碑（向后兼容）。

    返回：
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "project_name": "项目名称",
                "milestones": [
                    {
                        "uuid": "ms_xxxxxxxx",
                        "name": "里程碑名称",
                        "description": "...",
                        "acceptance_criteria": "...",
                        "order": 1,
                        "project_uuid": "proj_xxxxxxxx",
                        "knowledge_points": [
                            {
                                "uuid": "node_xxxxxxxx",
                                "name": "知识点名称",
                                "difficulty": "beginner",
                                "summary": "..."
                            }
                        ]
                    }
                ]
            }
        }
    """
    try:
        neo4j_ops = Neo4jOperations()

        # 先验证项目存在
        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": t('api.projectNotFound', id=project_id)
            }), 404

        # 可选的 PBL Project 节点 UUID 过滤
        pbl_node_uuid = request.args.get('pbl', '').strip()

        # 两步查询：
        # 1. 获取每个里程碑及其直接关联的知识点（MILESTONE_REQUIRES 边）
        # 2. 对于没有直接关联知识点的里程碑，自动分配其所属项目的所有知识点
        if pbl_node_uuid:
            # 指定了特定 PBL Project 节点，只返回该项目的里程碑
            query_with_direct_kps = """
            MATCH (p:Entity:Project {project_id: $project_id, uuid: $pbl_uuid})
            -[r_step:RELATIONSHIP {fact_type: 'MILESTONE_STEP'}]->(ms:Entity:Milestone)
            OPTIONAL MATCH (ms)-[r_req:RELATIONSHIP {fact_type: 'MILESTONE_REQUIRES'}]->(kp:Entity)
            RETURN ms.uuid as ms_uuid,
                   ms.name as ms_name,
                   ms.order as ms_order,
                   ms.description as ms_description,
                   ms.acceptance_criteria as ms_acceptance_criteria,
                   ms.project_uuid as ms_project_uuid,
                   p.name as project_name,
                   p.uuid as project_uuid,
                   collect({
                       uuid: kp.uuid,
                       name: kp.name,
                       difficulty: kp.difficulty,
                       summary: kp.summary,
                       classroom_id: kp.classroom_id
                   }) as knowledge_points
            ORDER BY ms.order
            """
            query_params = {"project_id": project_id, "pbl_uuid": pbl_node_uuid}
        else:
            # 未指定，返回所有 PBL 项目的里程碑（向后兼容）
            query_with_direct_kps = """
            MATCH (p:Entity:Project {project_id: $project_id})
            -[r_step:RELATIONSHIP {fact_type: 'MILESTONE_STEP'}]->(ms:Entity:Milestone)
            OPTIONAL MATCH (ms)-[r_req:RELATIONSHIP {fact_type: 'MILESTONE_REQUIRES'}]->(kp:Entity)
            RETURN ms.uuid as ms_uuid,
                   ms.name as ms_name,
                   ms.order as ms_order,
                   ms.description as ms_description,
                   ms.acceptance_criteria as ms_acceptance_criteria,
                   ms.project_uuid as ms_project_uuid,
                   p.name as project_name,
                   p.uuid as project_uuid,
                   collect({
                       uuid: kp.uuid,
                       name: kp.name,
                       difficulty: kp.difficulty,
                       summary: kp.summary,
                       classroom_id: kp.classroom_id
                   }) as knowledge_points
            ORDER BY ms.order
            """
            query_params = {"project_id": project_id}

        milestones = []
        project_name = ""

        try:
            with neo4j_ops.driver.session(default_access_mode="READ") as session:
                # 获取里程碑（单次查询）
                ms_result = session.run(query_with_direct_kps, query_params)
                for record in ms_result:
                    ms_uuid = record.get("ms_uuid", "")
                    # 过滤掉 None 值的知识点（OPTIONAL MATCH 无匹配时）
                    direct_kps = [
                        kp for kp in record.get("knowledge_points", [])
                        if kp.get("uuid") is not None
                    ]

                    milestones.append({
                        "uuid": ms_uuid,
                        "name": record.get("ms_name", ""),
                        "description": record.get("ms_description", ""),
                        "acceptance_criteria": record.get("ms_acceptance_criteria", ""),
                        "order": record.get("ms_order", 0),
                        "project_uuid": record.get("ms_project_uuid", ""),
                        "knowledge_points": direct_kps,
                    })
                    project_name = record.get("project_name", "")

                # 批量 fallback：为没有 MILESTONE_REQUIRES 边的里程碑分配知识点
                milestones = _bulk_assign_kps(milestones, project_id, neo4j_ops)
        except Exception as e:
            logger.warning(f"查询里程碑失败（可能是旧项目无 Milestone 节点）: {e}")
            milestones = []

        # 如果 Cypher 查询没有返回项目名，从 ProjectManager 获取
        if not project_name and project:
            project_name = project.name

        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "project_name": project_name,
                "milestones": milestones,
            }
        })

    except Exception as e:
        logger.error(f"获取里程碑失败: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve milestones",
            "code": "MILESTONE_ERROR"
        }), 500


# ============== 学习路径接口 ==============

@graph_bp.route('/learning-path/<project_id>', methods=['GET'])
def get_learning_path(project_id: str):
    """
    获取学习路径结构（支持 PBL 模式和知识驱动模式）

    返回：
        PBL 模式：
        {
            "success": true,
            "data": {
                "mode": "pbl",
                "main_path": [...],
                "branch_projects": [...],
                "project_knowledge_subgraphs": {
                    "proj_uuid": {
                        "knowledge_chain": [kp1, kp2, ...],
                        "entry_points": [kp1],
                        "exit_points": [kp_n],
                        "ring_closed": true
                    }
                },
                "entry_points": [...],
                "exit_points": [...],
                "learning_stages": {...}
            }
        }

        知识驱动模式：
        {
            "success": true,
            "data": {
                "mode": "knowledge_driven",
                "main_path": [...],
                "branch_paths": [...],
                "entry_points": [...],
                "exit_points": [...],
                "learning_stages": {...}
            }
        }
    """
    try:
        neo4j_ops = Neo4jOperations()
        learning_path = neo4j_ops.get_learning_path(project_id)

        mode = learning_path.get("mode", "knowledge_driven")

        if mode == "pbl":
            if not learning_path.get("main_path"):
                return jsonify({
                    "success": False,
                    "error": "Learning path not found",
                    "code": "LEARNING_PATH_NOT_FOUND"
                }), 404
        else:
            if not learning_path.get("main_path") and not learning_path.get("branch_paths"):
                return jsonify({
                    "success": False,
                    "error": "Learning path not found",
                    "code": "LEARNING_PATH_NOT_FOUND"
                }), 404

        return jsonify({
            "success": True,
            "data": learning_path
        })

    except Exception as e:
        logger.error(f"Failed to get learning path: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve learning path",
            "code": "LEARNING_PATH_ERROR"
        }), 500


# ============== Graphiti 图谱数据接口 ==============

@graph_bp.route('/graphiti-data/<group_id>', methods=['GET'])
def get_graphiti_data(group_id: str):
    """
    从 Graphiti 的 Neo4j schema 获取图谱数据

    Graphiti 使用 Entity 节点和关系边存储，
    此端点查询并转换为前端 GraphPanel 期望的格式。
    """
    try:
        neo4j_ops = Neo4jOperations()
        graph_data = neo4j_ops.get_graphiti_graph_data(group_id)

        if not graph_data.get("nodes") and not graph_data.get("edges"):
            return jsonify({
                "success": False,
                "error": "Graphiti graph data not found",
                "code": "GRAPHITI_DATA_NOT_FOUND"
            }), 404

        return jsonify({
            "success": True,
            "data": graph_data
        })

    except Exception as e:
        logger.warning(f"Failed to get Graphiti graph data: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "code": "GRAPHITI_ERROR"
        }), 500

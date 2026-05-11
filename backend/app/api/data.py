"""
数据集 API 蓝图

端点：
- GET /api/data/presets — 列出预设数据集
- POST /api/data/ingest — 导入指定数据集
- POST /api/data/upload — 上传自定义文件并导入
"""

import os
import traceback
import threading
from flask import request, jsonify

from . import data_bp
from ..config import Config
from ..services.data_loader import ingest_dataset, chunk_chinese_text
from ..utils.async_bridge import AsyncBridge
from ..services.graphiti_service import GraphitiService
from ..models.project import ProjectManager, ProjectStatus
from ..utils.logger import get_logger

logger = get_logger('evolith.api.data')

# 跟踪正在进行的导入任务
_ingest_tasks = {}  # {project_id: {"status": "processing"|"completed"|"error", ...}}

DATASETS_DIR = os.path.join(os.path.dirname(__file__), '../../data/datasets')


@data_bp.route('/presets', methods=['GET'])
def list_presets():
    """
    列出预设数据集

    返回:
        {
            "success": true,
            "data": [
                {
                    "name": "ai_fundamentals",
                    "display_name": "AI 基础",
                    "description": "...",
                    "file_count": 3,
                    "files": ["machine_learning.md", ...]
                }
            ]
        }
    """
    datasets = []

    if not os.path.exists(DATASETS_DIR):
        return jsonify({"success": True, "data": []})

    display_names = {
        "ai_fundamentals": "AI 基础领域",
        "ai_frontier": "AI 前沿技术",
        "quantum_computing": "量子计算",
    }

    descriptions = {
        "ai_fundamentals": "机器学习、深度学习、自然语言处理等 AI 基础知识",
        "ai_frontier": "大模型技术、多模态AI、AI Agent 等前沿进展",
        "quantum_computing": "量子计算基础原理与中国量子计算进展",
    }

    for dirname in sorted(os.listdir(DATASETS_DIR)):
        dirpath = os.path.join(DATASETS_DIR, dirname)
        if not os.path.isdir(dirpath):
            continue

        files = [f for f in os.listdir(dirpath) if f.endswith(('.md', '.txt', '.markdown'))]

        datasets.append({
            "name": dirname,
            "display_name": display_names.get(dirname, dirname),
            "description": descriptions.get(dirname, ""),
            "file_count": len(files),
            "files": files,
        })

    return jsonify({"success": True, "data": datasets})


def _make_progress_callback(project_id: str, dataset_name: str):
    """创建进度回调，更新 _ingest_tasks 供前端轮询"""
    def callback(completed: int, total: int):
        _ingest_tasks[project_id] = {
            "status": "processing",
            "dataset_name": dataset_name,
            "progress": completed,
            "total": total,
        }
    return callback


def _run_ingest_background(project_id: str, dataset_name: str, dataset_dir: str):
    """后台线程：执行数据集导入"""
    try:
        _ingest_tasks[project_id] = {"status": "processing", "dataset_name": dataset_name}

        progress_cb = _make_progress_callback(project_id, dataset_name)
        result = ingest_dataset(dataset_dir, group_id=project_id, progress_callback=progress_cb)

        # 更新项目状态
        project = ProjectManager.get_project(project_id)
        if project:
            project.course_description = f"数据集: {dataset_name}"
            project.status = ProjectStatus.GRAPH_COMPLETED
            project.node_count = result.get("episode_count", 0)
            ProjectManager.save_project(project)

        _ingest_tasks[project_id] = {
            "status": "completed",
            "dataset_name": dataset_name,
            "document_count": result.get("document_count", 0),
            "episode_count": result.get("episode_count", 0),
        }
        logger.info(f"数据集 {dataset_name} 后台导入完成: {result}")

    except Exception as e:
        logger.error(f"数据集 {dataset_name} 后台导入失败: {e}")
        logger.error(traceback.format_exc())
        _ingest_tasks[project_id] = {"status": "error", "dataset_name": dataset_name, "error": str(e)}

        # 标记项目失败
        project = ProjectManager.get_project(project_id)
        if project:
            project.course_description = f"数据集: {dataset_name} (导入失败)"
            ProjectManager.save_project(project)


@data_bp.route('/ingest', methods=['POST'])
def ingest():
    """
    异步导入指定数据集到 Graphiti

    立即返回 project_id，后台执行导入。
    前端通过 GET /api/data/ingest-status/<project_id> 轮询进度。

    请求 (JSON):
        {
            "dataset_name": "ai_fundamentals",
            "project_id": "proj_xxxx"  (可选)
        }
    """
    try:
        data = request.get_json() or {}
        dataset_name = data.get('dataset_name', '').strip()
        project_id = data.get('project_id')

        if not dataset_name:
            return jsonify({"success": False, "error": "dataset_name 不能为空"}), 400

        dataset_dir = os.path.join(DATASETS_DIR, dataset_name)
        if not os.path.exists(dataset_dir):
            return jsonify({"success": False, "error": f"数据集不存在: {dataset_name}"}), 404

        # 获取或创建项目
        if project_id:
            project = ProjectManager.get_project(project_id)
            if not project:
                return jsonify({"success": False, "error": "项目不存在"}), 404
        else:
            project = ProjectManager.create_project(name=dataset_name)

        project_id = project.project_id

        # 启动后台导入线程
        thread = threading.Thread(
            target=_run_ingest_background,
            args=(project_id, dataset_name, dataset_dir),
            daemon=True,
        )
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "dataset_name": dataset_name,
                "message": "导入已开始",
                "status": "processing",
            }
        })

    except Exception as e:
        logger.error(f"数据集导入启动失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@data_bp.route('/ingest-status/<project_id>', methods=['GET'])
def ingest_status(project_id: str):
    """查询导入进度"""
    task = _ingest_tasks.get(project_id)
    if not task:
        # 检查项目是否已经完成（可能是之前导入的）
        project = ProjectManager.get_project(project_id)
        if project and project.status == ProjectStatus.GRAPH_COMPLETED:
            return jsonify({"success": True, "data": {"status": "completed"}})
        return jsonify({"success": True, "data": {"status": "unknown"}})

    return jsonify({"success": True, "data": task})


def _run_upload_background(project_id: str, episodes: list[dict], total_text_length: int):
    """后台线程：执行自定义文件导入"""
    try:
        _ingest_tasks[project_id] = {"status": "processing", "dataset_name": "自定义上传"}

        # 确保 Graphiti 索引已创建
        AsyncBridge.run(GraphitiService.ensure_indices())

        # 并发导入（带进度回调）
        progress_cb = _make_progress_callback(project_id, "自定义上传")
        result = AsyncBridge.run(
            GraphitiService.ingest_episodes(
                episodes, group_id=project_id, progress_callback=progress_cb
            )
        )

        # 更新项目状态
        project = ProjectManager.get_project(project_id)
        if project:
            project.status = ProjectStatus.GRAPH_COMPLETED
            project.total_text_length = total_text_length
            ProjectManager.save_project(project)

        _ingest_tasks[project_id] = {
            "status": "completed",
            "dataset_name": "自定义上传",
            "episode_count": result.get("episode_count", len(episodes)),
        }
        logger.info(f"自定义上传后台导入完成: {result}")

    except Exception as e:
        logger.error(f"自定义上传后台导入失败: {e}")
        logger.error(traceback.format_exc())
        _ingest_tasks[project_id] = {"status": "error", "dataset_name": "自定义上传", "error": str(e)}

        # 标记项目失败
        project = ProjectManager.get_project(project_id)
        if project:
            project.course_description = "自定义上传 (导入失败)"
            ProjectManager.save_project(project)


@data_bp.route('/upload', methods=['POST'])
def upload():
    """
    异步上传自定义文件并导入到 Graphiti

    立即返回 project_id，后台执行导入。
    前端通过 GET /api/data/ingest-status/<project_id> 轮询进度。

    请求 (multipart/form-data):
        files: 上传的文件（.md/.txt）
        project_name: 项目名称（可选）

    返回:
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "message": "导入已开始",
                "status": "processing"
            }
        }
    """
    try:
        project_name = request.form.get('project_name', '自定义数据集')
        uploaded_files = request.files.getlist('files')

        if not uploaded_files or not any(f.filename for f in uploaded_files):
            return jsonify({"success": False, "error": "请上传文件"}), 400

        # 创建项目
        project = ProjectManager.create_project(name=project_name)
        project_id = project.project_id

        # 处理上传的文件（同步，文件 IO 很快）
        all_text = ""
        for file in uploaded_files:
            if not file.filename:
                continue

            file_info = ProjectManager.save_file_to_project(project_id, file, file.filename)
            with open(file_info["path"], 'r', encoding='utf-8') as f:
                all_text += f.read() + "\n\n"

        if not all_text.strip():
            return jsonify({"success": False, "error": "文件内容为空"}), 400

        # 分块（同步，纯 CPU 操作很快）
        chunks = chunk_chinese_text(all_text.strip())
        episodes = [
            {
                "name": chunk["name"],
                "episode_body": chunk["episode_body"],
                "source_description": "user_upload",
            }
            for chunk in chunks
        ]

        # 启动后台导入线程（与 /api/data/ingest 相同模式）
        thread = threading.Thread(
            target=_run_upload_background,
            args=(project_id, episodes, len(all_text)),
            daemon=True,
        )
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "episode_count": len(episodes),
                "message": "导入已开始",
                "status": "processing",
            }
        })

    except Exception as e:
        logger.error(f"文件上传处理失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500

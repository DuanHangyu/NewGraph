"""
QA 问答 API 蓝图

端点：
- POST /api/qa/ask — 问答（非流式）
- POST /api/qa/ask-stream — 问答（SSE 流式）
- GET /api/qa/history/<session_id> — 获取会话历史
- DELETE /api/qa/history/<session_id> — 清空会话
"""

import json
import traceback
from flask import request, jsonify, Response, stream_with_context

from . import qa_bp
from ..services.qa_service import QAService
from ..models.qa_session import QASessionManager
from ..utils.logger import get_logger

logger = get_logger('evolith.api.qa')


@qa_bp.route('/ask', methods=['POST'])
def ask():
    """
    问答接口

    请求 (JSON):
        {
            "question": "中国在量子计算领域有哪些重要进展？",
            "project_id": "proj_xxxx",
            "session_id": "qa_xxxx" (可选，不提供则新建)
        }

    返回:
        {
            "success": true,
            "data": {
                "session_id": "qa_xxxx",
                "answer": "...",
                "question": "...",
                "sources": [...],
                "search_stats": {...},
                "timestamp": "..."
            }
        }
    """
    try:
        data = request.get_json() or {}
        question = data.get('question', '').strip()
        project_id = data.get('project_id', '')
        session_id = data.get('session_id')

        if not question:
            return jsonify({"success": False, "error": "问题不能为空"}), 400

        if not project_id:
            return jsonify({"success": False, "error": "project_id 不能为空"}), 400

        # 获取或创建会话
        if not session_id:
            session = QASessionManager.create_session(project_id)
            session_id = session["session_id"]
        else:
            session = QASessionManager.get_session(session_id)
            if not session:
                session = QASessionManager.create_session(project_id)
                session_id = session["session_id"]

        # 保存用户消息
        QASessionManager.add_message(session_id, {
            "role": "user",
            "content": question,
        })

        # 调用 QA 服务
        qa_service = QAService()
        result = qa_service.ask(question=question, group_id=project_id)

        # 保存 AI 回答
        QASessionManager.add_message(session_id, {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "search_stats": result["search_stats"],
        })

        return jsonify({
            "success": True,
            "data": {
                "session_id": session_id,
                **result,
            }
        })

    except Exception as e:
        logger.error(f"QA 问答失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@qa_bp.route('/ask-stream', methods=['POST'])
def ask_stream():
    """
    流式问答接口（SSE）

    请求 (JSON):
        {
            "question": "中国在量子计算领域有哪些重要进展？",
            "project_id": "proj_xxxx",
            "session_id": "qa_xxxx" (可选)
        }

    返回 SSE 事件流:
        data: {"type": "status", "stage": "searching", "message": "..."}
        data: {"type": "status", "stage": "found", "message": "...", "node_uuids": [...], "edge_uuids": [...]}
        data: {"type": "status", "stage": "generating", "message": "..."}
        data: {"type": "token", "content": "..."}
        ...
        data: {"type": "done", "sources": [...], "search_stats": {...}, "timestamp": "..."}
        data: {"type": "meta", "session_id": "qa_xxxx"}
    """
    try:
        data = request.get_json() or {}
        question = data.get('question', '').strip()
        project_id = data.get('project_id', '')
        session_id = data.get('session_id')

        if not question:
            return jsonify({"success": False, "error": "问题不能为空"}), 400

        if not project_id:
            return jsonify({"success": False, "error": "project_id 不能为空"}), 400

        # 获取或创建会话
        if not session_id:
            session = QASessionManager.create_session(project_id)
            session_id = session["session_id"]
        else:
            session = QASessionManager.get_session(session_id)
            if not session:
                session = QASessionManager.create_session(project_id)
                session_id = session["session_id"]

        # 保存用户消息
        QASessionManager.add_message(session_id, {
            "role": "user",
            "content": question,
        })

        def generate():
            qa_service = QAService()
            full_answer = ""
            sources = []
            search_stats = {}
            timestamp = ""

            try:
                for event in qa_service.ask_stream(question=question, group_id=project_id):
                    if event["type"] == "token":
                        full_answer += event["content"]
                    elif event["type"] == "done":
                        full_answer = event.get("answer", full_answer)
                        sources = event.get("sources", [])
                        search_stats = event.get("search_stats", {})
                        timestamp = event.get("timestamp", "")

                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error(f"流式问答生成失败: {e}")
                logger.error(traceback.format_exc())
                error_event = {"type": "error", "message": str(e)}
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

            # 流结束后保存 AI 回答到会话
            if full_answer:
                QASessionManager.add_message(session_id, {
                    "role": "assistant",
                    "content": full_answer,
                    "sources": sources,
                    "search_stats": search_stats,
                })

            # 发送 session_id 元数据
            meta_event = {"type": "meta", "session_id": session_id}
            yield f"data: {json.dumps(meta_event, ensure_ascii=False)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
            }
        )

    except Exception as e:
        logger.error(f"流式问答初始化失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@qa_bp.route('/history/<session_id>', methods=['GET'])
def get_history(session_id: str):
    """获取会话历史"""
    session = QASessionManager.get_session(session_id)
    if not session:
        return jsonify({"success": False, "error": "会话不存在"}), 404

    return jsonify({
        "success": True,
        "data": session,
    })


@qa_bp.route('/history/<session_id>', methods=['DELETE'])
def clear_history(session_id: str):
    """清空会话"""
    success = QASessionManager.clear_session(session_id)
    if not success:
        return jsonify({"success": False, "error": "会话不存在"}), 404

    return jsonify({"success": True, "message": "会话已清空"})

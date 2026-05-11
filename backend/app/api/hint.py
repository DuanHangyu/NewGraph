"""
Hint API 蓝图
处理学习提示生成请求（L1 和 L2）
"""

import traceback
import logging
from flask import request, jsonify
from . import hint_bp
from ..models.project import ProjectManager, ProjectStatus
from ..services.hint_service import HintService
from ..utils.locale import t
from ..utils.logger import get_logger

logger = get_logger('evolith.api')


@hint_bp.route('/generate', methods=['POST'])
def generate_hint():
    """
    生成学习提示

    请求（JSON）：
        {
            "project_id": "proj_xxxx",   // 必填
            "milestone_uuid": "ms_xxxx", // 必填
            "level": 1                    // 必填，1 或 2
        }

    返回：
        {
            "success": true,
            "data": {
                "hint_content": "...",
                "level": 1,
                "milestone_uuid": "ms_xxxx",
                "knowledge_points": ["kp1_uuid", "kp2_uuid"]
            }
        }
    """
    try:
        data = request.get_json() or {}

        # 参数验证
        project_id = data.get('project_id')
        milestone_uuid = data.get('milestone_uuid')
        level = data.get('level')

        if not project_id:
            return jsonify({
                "success": False,
                "error": t('hint.requireProjectId')
            }), 400

        if not milestone_uuid:
            return jsonify({
                "success": False,
                "error": t('hint.requireMilestoneUuid')
            }), 400

        if level not in (1, 2):
            return jsonify({
                "success": False,
                "error": t('hint.invalidLevel')
            }), 400

        # 验证项目存在
        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": t('hint.projectNotFound', id=project_id)
            }), 404

        # 生成提示
        hint_service = HintService()
        result = hint_service.generate_hint(
            project_id=project_id,
            milestone_uuid=milestone_uuid,
            level=level
        )

        return jsonify({
            "success": True,
            "data": result
        })

    except ValueError as e:
        logger.warning(f"Hint generation validation error: {e}")
        return jsonify({
            "success": False,
            "error": t('hint.generationFailed')
        }), 404

    except Exception as e:
        logger.error(f"Hint generation failed: {e}")
        logger.error(f"详细错误:\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": t('hint.generationException')
        }), 500
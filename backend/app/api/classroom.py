"""
Classroom API 蓝图
处理虚拟课堂生成、状态查询和缓存
"""

import logging
import requests as http_requests
from flask import request, jsonify
from . import classroom_bp
from ..config import Config
from ..services.neo4j_operations import Neo4jOperations

logger = logging.getLogger(__name__)


@classroom_bp.route('/generate', methods=['POST'])
def generate_classroom():
    """为知识点生成虚拟课堂"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    project_id = data.get('project_id')
    node_uuid = data.get('node_uuid')

    if not project_id or not node_uuid:
        return jsonify({'error': 'project_id 和 node_uuid 为必填项'}), 400

    # 课堂模式参数
    podcast_mode = data.get('podcast_mode')  # None=课堂模式, 'podcast'=播客模式
    podcast_speaker_pair = data.get('podcast_speaker_pair', 'mizai-dayi')

    try:
        neo4j_ops = Neo4jOperations()

        # 检查节点是否已有 classroom_id
        node_detail = neo4j_ops.get_node_detail(project_id, node_uuid)
        if not node_detail:
            return jsonify({'error': '节点不存在'}), 404

        existing_classroom_id = node_detail.get('attributes', {}).get('classroom_id')
        if existing_classroom_id:
            logger.info(f"节点已有课堂缓存: classroom_id={existing_classroom_id}")
            return jsonify({
                'success': True,
                'data': {
                    'status': 'ready',
                    'classroom_id': existing_classroom_id
                }
            })

        # 组装 requirement 字符串
        requirement_parts = []
        attrs = node_detail.get('attributes', {})

        requirement_parts.append(f"知识点名称: {node_detail.get('name', '')}")

        if attrs.get('difficulty'):
            requirement_parts.append(f"难度: {attrs['difficulty']}")
        if attrs.get('prerequisites_summary'):
            requirement_parts.append(f"学习前置: {attrs['prerequisites_summary']}")
        if attrs.get('outcomes_summary'):
            requirement_parts.append(f"学习成果: {attrs['outcomes_summary']}")
        if attrs.get('required_by'):
            requirement_parts.append(f"所需项目: {attrs['required_by']}")
        if node_detail.get('summary'):
            requirement_parts.append(f"摘要: {node_detail['summary']}")

        requirement = '\n'.join(requirement_parts)

        # 调用 OpenMAIC API 生成课堂
        openmaic_url = Config.OPENMAIC_BASE_URL.rstrip('/')
        timeout = Config.OPENMAIC_TIMEOUT

        request_body = {'requirement': requirement, 'enableTTS': True}
        if podcast_mode == 'podcast':
            request_body['enablePodcast'] = True
            request_body['podcastSpeakerPair'] = podcast_speaker_pair

        try:
            response = http_requests.post(
                f'{openmaic_url}/api/generate-classroom',
                json=request_body,
                timeout=timeout
            )
            response.raise_for_status()
            result = response.json()
        except http_requests.ConnectionError:
            logger.error("无法连接到 OpenMAIC 服务")
            return jsonify({'error': '无法连接到课堂服务，请确认 OpenMAIC 已启动'}), 503
        except http_requests.Timeout:
            logger.error("OpenMAIC 请求超时")
            return jsonify({'error': '课堂服务请求超时，请稍后重试'}), 504
        except (http_requests.HTTPError, ValueError) as e:
            logger.error(f"OpenMAIC 返回错误或非JSON响应: {e}")
            return jsonify({'error': f'课堂服务返回了异常响应: {e}'}), 502

        # 检查 OpenMAIC 错误响应
        if result.get('success') is False:
            error_msg = result.get('error', '课堂服务返回错误')
            logger.error(f"OpenMAIC 返回错误: {error_msg}")
            return jsonify({'error': error_msg}), 502

        job_id = result.get('jobId') or result.get('job_id')
        if not job_id:
            logger.error(f"OpenMAIC 未返回 jobId: {result}")
            return jsonify({'error': '课堂服务未返回任务ID'}), 502

        logger.info(f"课堂生成任务已创建: job_id={job_id}")
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'status': 'generating',
                'poll_interval_ms': result.get('pollIntervalMs', 5000)
            }
        })

    except Exception as e:
        logger.error(f"生成课堂失败: {e}")
        return jsonify({'error': str(e)}), 500


@classroom_bp.route('/status/<job_id>', methods=['GET'])
def get_classroom_status(job_id):
    """查询课堂生成状态"""
    try:
        openmaic_url = Config.OPENMAIC_BASE_URL.rstrip('/')
        timeout = Config.OPENMAIC_TIMEOUT

        try:
            response = http_requests.get(
                f'{openmaic_url}/api/generate-classroom/{job_id}',
                timeout=timeout
            )
            response.raise_for_status()
            result = response.json()
        except http_requests.ConnectionError:
            return jsonify({'error': '无法连接到课堂服务'}), 503
        except http_requests.Timeout:
            return jsonify({'error': '课堂服务请求超时'}), 504
        except (http_requests.HTTPError, ValueError) as e:
            return jsonify({'error': f'课堂服务返回了异常响应: {e}'}), 502

        # 检查 OpenMAIC 错误响应
        if result.get('success') is False:
            error_msg = result.get('error', '课堂服务返回错误')
            logger.error(f"OpenMAIC 返回错误: {error_msg}")
            return jsonify({'error': error_msg}), 502

        # 映射状态
        openmaic_status = result.get('status', '')
        if openmaic_status == 'succeeded':
            classroom_id = result.get('result', {}).get('classroomId')
            return jsonify({
                'success': True,
                'data': {
                    'status': 'completed',
                    'classroom_id': classroom_id
                }
            })
        elif openmaic_status in ('queued', 'running'):
            return jsonify({
                'success': True,
                'data': {
                    'status': 'processing',
                    'progress': result.get('progress', 0)
                }
            })
        elif openmaic_status == 'failed':
            return jsonify({
                'success': True,
                'data': {
                    'status': 'failed',
                    'error': result.get('error', '课堂生成失败')
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'status': 'processing',
                    'progress': 0
                }
            })

    except Exception as e:
        logger.error(f"查询课堂状态失败: {e}")
        return jsonify({'error': str(e)}), 500


@classroom_bp.route('/cache', methods=['POST'])
def cache_classroom_id():
    """缓存 classroom_id 到 Neo4j 节点"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    project_id = data.get('project_id')
    node_uuid = data.get('node_uuid')
    classroom_id = data.get('classroom_id')

    logger.info(f"[cache] 收到请求: project_id={project_id}, node_uuid={node_uuid}, classroom_id={classroom_id}")

    if not project_id or not node_uuid or not classroom_id:
        return jsonify({'error': 'project_id, node_uuid, classroom_id 为必填项'}), 400

    try:
        neo4j_ops = Neo4jOperations()
        success = neo4j_ops.update_node_attribute(
            project_id, node_uuid, 'classroom_id', classroom_id
        )

        if success:
            logger.info(f"课堂ID已缓存: node_uuid={node_uuid}, classroom_id={classroom_id}")
            return jsonify({
                'success': True,
                'data': {'status': 'ok'}
            })
        else:
            return jsonify({'error': '缓存课堂ID失败'}), 500

    except Exception as e:
        logger.error(f"缓存课堂ID失败: {e}")
        return jsonify({'error': str(e)}), 500
import service, { requestWithRetry } from './index'

const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'

/**
 * 提取图谱（上传文档和课程描述）
 * @param {Object} formData - 包含files, course_description, project_name等
 * @returns {Promise}
 */
export function extractGraph(formData) {
  return requestWithRetry(() =>
    service({
      url: '/api/graph/extract',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  )
}

/**
 * 存储图谱到 Neo4j
 * @param {Object} data - 包含project_id
 * @returns {Promise}
 */
export function storeGraph(data) {
  return service({
    url: '/api/graph/store',
    method: 'post',
    data
  })
}

/**
 * 获取图谱数据
 * @param {String} graphId - 图谱ID
 * @returns {Promise}
 */
export function getGraphData(graphId) {
  return service({
    url: `/api/graph/data/${graphId}`,
    method: 'get'
  })
}

/**
 * 获取项目信息
 * @param {String} projectId - 项目ID
 * @returns {Promise}
 */
export function getProject(projectId) {
  return service({
    url: `/api/graph/project/${projectId}`,
    method: 'get'
  })
}

/**
 * 获取所有项目列表
 * @param {number} limit - 返回项目数量限制，默认50
 * @returns {Promise} 项目列表响应
 */
export function getProjects(limit = 50) {
  return service({
    url: '/api/graph/project/list',
    method: 'get',
    params: { limit }
  })
}

/**
 * 删除项目
 * @param {String} projectId - 项目ID
 * @returns {Promise}
 */
export function deleteProject(projectId) {
  return service({
    url: `/api/graph/project/${projectId}`,
    method: 'delete'
  })
}

/**
 * 获取学习路径
 * @param {String} projectId - 项目ID
 * @returns {Promise}
 */
export function getLearningPath(projectId) {
  return service({
    url: `/api/graph/learning-path/${projectId}`,
    method: 'get'
  })
}

/**
 * 为知识点生成虚拟课堂
 * @param {Object} data - 包含 project_id, node_uuid, podcast_mode, podcast_speaker_pair
 * @returns {Promise}
 */
export function generateClassroom(data) {
  return service({
    url: '/api/classroom/generate',
    method: 'post',
    data
  })
}

/**
 * 查询课堂生成状态
 * @param {String} jobId - 任务ID
 * @returns {Promise}
 */
export function getClassroomStatus(jobId) {
  return service({
    url: `/api/classroom/status/${jobId}`,
    method: 'get'
  })
}

/**
 * 缓存 classroom_id 到 Neo4j 节点
 * @param {Object} data - 包含 project_id, node_uuid, classroom_id
 * @returns {Promise}
 */
export function cacheClassroomId(data) {
  return service({
    url: '/api/classroom/cache',
    method: 'post',
    data
  })
}

/**
 * 获取项目里程碑列表及关联知识点
 * @param {String} projectId - 项目ID
 * @param {String} [projectNodeUuid] - PBL Project 节点 UUID（可选，用于筛选特定 PBL 项目的里程碑）
 * @returns {Promise}
 */
export function getMilestones(projectId, projectNodeUuid) {
  const params = {}
  if (projectNodeUuid) params.pbl = projectNodeUuid
  return service({
    url: `/api/graph/milestones/${projectId}`,
    method: 'get',
    params
  })
}

/**
 * 生成学习提示（L1 或 L2）
 * @param {Object} data - 包含 project_id, milestone_uuid, level (1|2)
 * @returns {Promise}
 */
export function generateHint(data) {
  return service({
    url: '/api/hint/generate',
    method: 'post',
    data
  })
}

// ============== Graphiti 图谱数据 ==============

/**
 * 获取 Graphiti 图谱数据
 * @param {String} groupId - Graphiti group_id（通常为 project_id）
 * @returns {Promise}
 */
export function getGraphitiData(groupId) {
  return service({
    url: `/api/graph/graphiti-data/${groupId}`,
    method: 'get'
  })
}

// ============== QA 问答 ==============

/**
 * 提交问答
 * @param {String} projectId - 项目ID
 * @param {String} question - 问题
 * @param {String} [sessionId] - 会话ID（可选）
 * @returns {Promise}
 */
export function askQuestion(projectId, question, sessionId) {
  const data = { question, project_id: projectId }
  if (sessionId) data.session_id = sessionId
  return service({
    url: '/api/qa/ask',
    method: 'post',
    data
  })
}

/**
 * 流式问答（SSE）
 * 使用 fetch + ReadableStream 因为 EventSource 只支持 GET
 * @param {String} projectId - 项目ID
 * @param {String} question - 问题
 * @param {String} [sessionId] - 会话ID（可选）
 * @returns {Promise<Response>} fetch Response，使用 response.body.getReader() 读取 SSE
 */
export function askQuestionStream(projectId, question, sessionId) {
  const data = { question, project_id: projectId }
  if (sessionId) data.session_id = sessionId
  return fetch(`${baseUrl}/api/qa/ask-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

/**
 * 获取 QA 会话历史
 * @param {String} sessionId - 会话ID
 * @returns {Promise}
 */
export function getQAHistory(sessionId) {
  return service({
    url: `/api/qa/history/${sessionId}`,
    method: 'get'
  })
}

/**
 * 清空 QA 会话
 * @param {String} sessionId - 会话ID
 * @returns {Promise}
 */
export function clearQAHistory(sessionId) {
  return service({
    url: `/api/qa/history/${sessionId}`,
    method: 'delete'
  })
}

// ============== 数据集 ==============

/**
 * 获取预设数据集列表
 * @returns {Promise}
 */
export function listPresets() {
  return service({
    url: '/api/data/presets',
    method: 'get'
  })
}

/**
 * 导入预设数据集（异步，立即返回）
 * @param {String} datasetName - 数据集名称
 * @param {String} [projectId] - 项目ID（可选）
 * @returns {Promise}
 */
export function ingestPreset(datasetName, projectId) {
  return service({
    url: '/api/data/ingest',
    method: 'post',
    data: { dataset_name: datasetName, project_id: projectId }
  })
}

/**
 * 查询导入进度
 * @param {String} projectId - 项目ID
 * @returns {Promise}
 */
export function getIngestStatus(projectId) {
  return service({
    url: `/api/data/ingest-status/${projectId}`,
    method: 'get'
  })
}

/**
 * 上传自定义文件导入
 * @param {FormData} formData - 包含 files 和 project_name
 * @returns {Promise}
 */
export function uploadDataset(formData) {
  return service({
    url: '/api/data/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

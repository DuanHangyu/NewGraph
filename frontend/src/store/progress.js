/**
 * 学生学习进度存储
 * 基于 localStorage 的响应式进度追踪
 * 用于里程碑完成状态、提示历史等
 */
import { reactive, watch } from 'vue'

const STORAGE_KEY = 'evolith_progress'

// 从 localStorage 加载初始数据
const loadFromStorage = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : {}
  } catch {
    return {}
  }
}

const state = reactive({
  projects: loadFromStorage()
})

// 深度监听，自动保存到 localStorage
watch(
  () => JSON.stringify(state.projects),
  (newVal) => {
    try {
      localStorage.setItem(STORAGE_KEY, newVal)
    } catch (e) {
      console.error('Failed to save progress to localStorage:', e)
    }
  }
)

/**
 * 初始化项目进度（如果已有则加载，否则创建）
 * @param {string} projectId
 * @param {Array} milestones - 里程碑列表，每个含 order 字段
 */
export function initProgress(projectId, milestones) {
  if (state.projects[projectId]) {
    // 已有进度，验证里程碑是否一致
    const existing = state.projects[projectId]
    const existingOrders = Object.keys(existing.milestone_statuses).map(Number)
    const newOrders = milestones.map(ms => ms.order)

    // 如果里程碑数量变化（如重新构建图谱），重置进度
    if (existingOrders.length !== newOrders.length ||
        !newOrders.every(o => existingOrders.includes(o))) {
      delete state.projects[projectId]
      // 重新初始化
      _createFreshProgress(projectId, milestones)
    }
    return
  }

  _createFreshProgress(projectId, milestones)
}

function _createFreshProgress(projectId, milestones) {
  const milestone_statuses = {}
  for (const ms of milestones) {
    milestone_statuses[ms.order] = ms.order === 1 ? 'in_progress' : 'locked'
  }

  state.projects[projectId] = {
    project_id: projectId,
    current_milestone_order: milestones.length > 0 ? 1 : 0,
    milestone_statuses,
    milestone_notes: {},
    hint_history: [],
    started_at: new Date().toISOString(),
    project_completed: false,
  }
}

/**
 * 标记里程碑完成，解锁下一个
 * @param {string} projectId
 * @param {number} order - 里程碑顺序号
 */
export function markMilestoneComplete(projectId, order) {
  const progress = state.projects[projectId]
  if (!progress) return

  progress.milestone_statuses[order] = 'completed'

  // 解锁下一个里程碑
  const nextOrder = order + 1
  const maxOrder = Math.max(...Object.keys(progress.milestone_statuses).map(Number))

  if (nextOrder > maxOrder) {
    // 所有里程碑已完成
    progress.project_completed = true
  } else if (progress.milestone_statuses[nextOrder] === 'locked') {
    progress.milestone_statuses[nextOrder] = 'in_progress'
    progress.current_milestone_order = nextOrder
  }
}

/**
 * 记录提示使用历史
 * @param {string} projectId
 * @param {number} order - 里程碑顺序号
 * @param {number} level - 提示级别 (1 或 2)
 */
export function addHintHistory(projectId, order, level) {
  const progress = state.projects[projectId]
  if (!progress) return

  progress.hint_history = [
    ...progress.hint_history,
    { milestone_order: order, hint_level: level, timestamp: new Date().toISOString() }
  ]
}

/**
 * 获取里程碑状态
 * @param {string} projectId
 * @param {number} order
 * @returns {'completed'|'in_progress'|'locked'|undefined}
 */
export function getMilestoneStatus(projectId, order) {
  const progress = state.projects[projectId]
  if (!progress) return undefined
  return progress.milestone_statuses[order]
}

/**
 * 判断项目是否已完成
 * @param {string} projectId
 * @returns {boolean}
 */
export function isProjectCompleted(projectId) {
  const progress = state.projects[projectId]
  if (!progress) return false
  return progress.project_completed
}

/**
 * 获取项目当前里程碑顺序号
 * @param {string} projectId
 * @returns {number}
 */
export function getCurrentMilestoneOrder(projectId) {
  const progress = state.projects[projectId]
  if (!progress) return 0
  return progress.current_milestone_order
}

/**
 * 获取已完成里程碑数
 * @param {string} projectId
 * @returns {number}
 */
export function getCompletedCount(projectId) {
  const progress = state.projects[projectId]
  if (!progress) return 0
  return Object.values(progress.milestone_statuses)
    .filter(s => s === 'completed').length
}

/**
 * 获取提示使用次数
 * @param {string} projectId
 * @returns {number}
 */
export function getHintCount(projectId) {
  const progress = state.projects[projectId]
  if (!progress) return 0
  return progress.hint_history.length
}

/**
 * 保存里程碑笔记
 * @param {string} projectId
 * @param {number} order - 里程碑顺序号
 * @param {string} note - 笔记内容
 */
export function saveMilestoneNote(projectId, order, note) {
  const progress = state.projects[projectId]
  if (!progress) return
  if (!progress.milestone_notes) {
    progress.milestone_notes = {}
  }
  progress.milestone_notes[order] = note
}

/**
 * 获取里程碑笔记
 * @param {string} projectId
 * @param {number} order - 里程碑顺序号
 * @returns {string} 笔记内容，不存在则返回空字符串
 */
export function getMilestoneNote(projectId, order) {
  const progress = state.projects[projectId]
  if (!progress || !progress.milestone_notes) return ''
  return progress.milestone_notes[order] || ''
}

/**
 * 重置项目进度
 * @param {string} projectId
 */
export function resetProgress(projectId) {
  delete state.projects[projectId]
}

export default state
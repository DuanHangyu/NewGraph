/**
 * 临时存储待上传的文件和课程描述
 * 用于首页点击构建知识图谱后立即跳转，在Process页面再进行API调用
 */
import { reactive } from 'vue'

const state = reactive({
  files: [],
  courseDescription: '',
  isPending: false
})

export function setPendingUpload(files, description) {
  state.files = files
  state.courseDescription = description
  state.isPending = true
}

export function getPendingUpload() {
  return {
    files: state.files,
    courseDescription: state.courseDescription,
    isPending: state.isPending
  }
}

export function clearPendingUpload() {
  state.files = []
  state.courseDescription = ''
  state.isPending = false
}

export default state

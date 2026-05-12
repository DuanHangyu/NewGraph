<template>
  <div class="history-container">
    <!-- 顶部导航栏 -->
    <nav class="navbar">
      <div class="nav-brand">NEWGRAPH</div>
      <div class="nav-links">
        <LanguageSwitcher />
        <router-link to="/" class="nav-link">
          {{ $t('nav.home') }}
        </router-link>
        <a href="https://github.com/DuanHangyu" target="_blank" class="github-link">
          {{ $t('nav.visitGithub') }} <span class="arrow">↗</span>
        </a>
      </div>
    </nav>

    <div class="main-content">
      <h1 class="page-title">{{ $t('history.title') }}</h1>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <span class="loading-text">{{ $t('common.loading') }}</span>
      </div>

      <!-- 空状态 -->
      <div v-else-if="projects.length === 0" class="empty-state">
        <div class="empty-icon">📂</div>
        <p class="empty-text">{{ $t('history.noProjects') }}</p>
        <router-link to="/" class="btn-primary">
          {{ $t('history.createNew') }}
        </router-link>
      </div>

      <!-- 项目列表 -->
      <div v-else class="projects-grid">
        <div
          v-for="project in projects"
          :key="project.project_id"
          class="project-card"
        >
          <div class="card-header">
            <h3 class="project-name">{{ project.name || $t('history.untitledProject') }}</h3>
            <span class="project-status" :class="getStatusClass(project.status)">
              <span class="status-dot"></span>
              {{ getStatusText(project.status) }}
            </span>
          </div>

          <div class="card-body">
            <div class="info-row">
              <span class="info-label">{{ $t('history.projectId') }}:</span>
              <span class="info-value">{{ formatId(project.project_id) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ $t('history.createdAt') }}:</span>
              <span class="info-value">{{ formatDate(project.created_at) }}</span>
            </div>
            <div v-if="project.files && project.files.length > 0" class="info-row">
              <span class="info-label">{{ $t('history.files') }}:</span>
              <span class="info-value">{{ project.files.length }}</span>
            </div>
          </div>

          <div class="card-footer">
            <button
              class="btn-view"
              @click="openProject(project.project_id)"
              :disabled="project.status !== 'graph_completed'"
            >
              {{ $t('history.viewGraph') }}
            </button>
            <button
              class="btn-qa"
              @click="openQA(project.project_id)"
              :disabled="project.status !== 'graph_completed'"
            >
              开始问答
            </button>
            <button class="btn-delete" @click="handleDelete(project)">
              {{ $t('history.delete') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getProjects, deleteProject } from '../api/graph'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'

const router = useRouter()
const { t } = useI18n()
const projects = ref([])
const loading = ref(false)

const loadProjects = async () => {
  loading.value = true
  try {
    const response = await getProjects(20)
    if (response.success) {
      projects.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load projects:', error)
  } finally {
    loading.value = false
  }
}

const openProject = (projectId) => {
  router.push({
    name: 'Process',
    params: { projectId }
  })
}

const openQA = (projectId) => {
  router.push({
    name: 'QA',
    params: { projectId }
  })
}

const handleDelete = async (project) => {
  if (!confirm(t('history.confirmDelete'))) return

  try {
    const response = await deleteProject(project.project_id)
    if (response.success) {
      projects.value = projects.value.filter(p => p.project_id !== project.project_id)
    }
  } catch (error) {
    console.error('Failed to delete project:', error)
    alert(t('history.deleteFailed'))
  }
}

const formatId = (id) => {
  if (!id) return '-'
  return id.length > 20 ? id.slice(0, 20) + '...' : id
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString()
  } catch {
    return dateStr
  }
}

const getStatusClass = (status) => {
  const statusMap = {
    'graph_completed': 'completed',
    'graph_building': 'in-progress',
    'ontology_generated': 'pending',
    'failed': 'failed',
    'created': 'pending'
  }
  return statusMap[status] || 'pending'
}

const getStatusText = (status) => {
  const statusMap = {
    'graph_completed': t('common.completed'),
    'graph_building': t('common.processing'),
    'ontology_generated': t('common.pending'),
    'failed': t('common.failed'),
    'created': t('common.pending')
  }
  return statusMap[status] || status
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.history-container {
  min-height: 100vh;
  background: #FFFFFF;
}

/* 顶部导航 */
.navbar {
  height: 60px;
  background: #000000;
  color: #FFFFFF;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
}

.nav-brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  letter-spacing: 1px;
  font-size: 1.2rem;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-link {
  color: #FFFFFF;
  text-decoration: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  font-weight: 500;
  transition: opacity 0.2s;
}

.nav-link:hover {
  opacity: 0.8;
}

.github-link {
  color: #FFFFFF;
  text-decoration: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: opacity 0.2s;
}

.github-link:hover {
  opacity: 0.8;
}

.arrow {
  font-family: sans-serif;
}

/* 主要内容区 */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 500;
  margin: 0 0 40px 0;
  color: #000000;
}

/* 加载和空状态 */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  gap: 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #E5E7EB;
  border-top-color: #000000;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  color: #6B7280;
  font-family: 'JetBrains Mono', monospace;
}

.empty-icon {
  font-size: 4rem;
  opacity: 0.5;
}

.empty-text {
  color: #6B7280;
  font-size: 1.1rem;
  margin: 0;
}

.btn-primary {
  margin-top: 20px;
  padding: 12px 24px;
  background: #000000;
  color: #FFFFFF;
  border: none;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #FF4500;
  transform: translateY(-2px);
}

/* 项目网格 */
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

/* 项目卡片 */
.project-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.project-card:hover {
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
  border-color: #000000;
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #F3F4F6;
}

.project-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
  line-height: 1.4;
  flex: 1;
}

.project-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
  white-space: nowrap;
  margin-left: 12px;
}

.project-status.completed {
  background: rgba(16, 185, 129, 0.1);
  color: #10B981;
}

.project-status.in-progress {
  background: rgba(245, 158, 11, 0.1);
  color: #F59E0B;
}

.project-status.pending {
  background: rgba(107, 114, 128, 0.1);
  color: #6B7280;
}

.project-status.failed {
  background: rgba(239, 68, 68, 0.1);
  color: #EF4444;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
}

.info-label {
  color: #6B7280;
  font-family: 'JetBrains Mono', monospace;
}

.info-value {
  color: #374151;
  font-weight: 500;
  text-align: right;
}

.card-footer {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #F3F4F6;
}

.card-footer button {
  flex: 1;
  padding: 10px;
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  background: #FFFFFF;
}

.btn-view:hover:not(:disabled) {
  background: #000000;
  color: #FFFFFF;
  border-color: #000000;
}

.btn-view:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-qa:hover:not(:disabled) {
  background: #FF6B35;
  color: #FFFFFF;
  border-color: #FF6B35;
}

.btn-qa:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-delete:hover {
  background: #FEF2F2;
  color: #DC2626;
  border-color: #FECACA;
}

/* 响应式 */
@media (max-width: 768px) {
  .navbar {
    padding: 0 20px;
  }

  .main-content {
    padding: 20px;
  }

  .page-title {
    font-size: 1.8rem;
  }

  .projects-grid {
    grid-template-columns: 1fr;
  }
}
</style>

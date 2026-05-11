<template>
  <div class="datasets-container">
    <nav class="navbar">
      <div class="nav-brand">NEWGRAPH</div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link to="/history" class="nav-link">历史</router-link>
      </div>
    </nav>

    <div class="main-content">
      <h1 class="page-title">数据集管理</h1>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
      </div>

      <div v-else class="datasets-grid">
        <div v-for="dataset in datasets" :key="dataset.name" class="dataset-card">
          <div class="card-header">
            <h3 class="dataset-name">{{ dataset.display_name }}</h3>
            <span class="file-count">{{ dataset.file_count }} 个文件</span>
          </div>
          <p class="dataset-desc">{{ dataset.description }}</p>
          <div class="card-footer">
            <button
              class="btn-ingest"
              @click="handleIngest(dataset.name)"
              :disabled="ingesting === dataset.name"
            >
              {{ ingesting === dataset.name ? '导入中...' : '导入到图谱' }}
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
import { listPresets, ingestPreset } from '../api/graph'

const router = useRouter()
const datasets = ref([])
const loading = ref(false)
const ingesting = ref('')

onMounted(async () => {
  loading.value = true
  try {
    const response = await listPresets()
    if (response.success) {
      datasets.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load presets:', error)
  } finally {
    loading.value = false
  }
})

const handleIngest = async (datasetName) => {
  ingesting.value = datasetName
  try {
    const response = await ingestPreset(datasetName)
    if (response.success) {
      router.push({
        name: 'Process',
        params: { projectId: response.data.project_id }
      })
    }
  } catch (error) {
    alert(`导入失败: ${error.message}`)
  } finally {
    ingesting.value = ''
  }
}
</script>

<style scoped>
.datasets-container {
  min-height: 100vh;
  background: #fff;
}

.navbar {
  height: 56px;
  background: #000;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
}

.nav-brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 1.1rem;
}

.nav-links {
  display: flex;
  gap: 16px;
}

.nav-link {
  color: #fff;
  text-decoration: none;
  font-size: 0.9rem;
  opacity: 0.8;
}

.nav-link:hover { opacity: 1; }

.main-content {
  max-width: 1000px;
  margin: 0 auto;
  padding: 40px 32px;
}

.page-title {
  font-size: 2rem;
  font-weight: 600;
  color: #111827;
  margin: 0 0 32px;
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 80px;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #E5E7EB;
  border-top-color: #000;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.datasets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.dataset-card {
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 24px;
  transition: all 0.2s;
}

.dataset-card:hover {
  border-color: #000;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.dataset-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.file-count {
  font-size: 0.8rem;
  color: #6B7280;
  background: #F3F4F6;
  padding: 2px 8px;
  border-radius: 8px;
}

.dataset-desc {
  font-size: 0.9rem;
  color: #6B7280;
  margin: 0 0 20px;
  line-height: 1.5;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
}

.btn-ingest {
  padding: 8px 20px;
  background: #000;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-ingest:hover:not(:disabled) {
  background: #374151;
}

.btn-ingest:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

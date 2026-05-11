<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
    <nav class="navbar">
      <div class="nav-brand">NEWGRAPH</div>
      <div class="nav-links">
        <router-link to="/history" class="nav-link">历史</router-link>
        <router-link to="/datasets" class="nav-link">数据集</router-link>
      </div>
    </nav>

    <div class="main-content">
      <!-- Hero 区域 -->
      <section class="hero-section">
        <div class="hero-text">
          <div class="tag-row">
            <span class="orange-tag">Knowledge Graph QA</span>
          </div>
          <h1 class="main-title">
            中国先进技术<br>
            <span class="gradient-text">知识图谱问答系统</span>
          </h1>
          <p class="hero-desc">
            基于 Graphiti 知识图谱引擎，自动构建领域知识图谱，支持智能问答和可视化探索。
          </p>
        </div>
      </section>

      <!-- 数据集选择区域 -->
      <section class="datasets-section">
        <h2 class="section-title">选择数据集开始探索</h2>

        <div v-if="loadingPresets" class="loading-state">
          <div class="loading-spinner"></div>
        </div>

        <div v-else class="datasets-grid">
          <div
            v-for="dataset in presets"
            :key="dataset.name"
            class="dataset-card"
            @click="handleSelectDataset(dataset.name)"
            :class="{ active: selectedDataset === dataset.name }"
          >
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
            </div>
            <h3 class="card-title">{{ dataset.display_name }}</h3>
            <p class="card-desc">{{ dataset.description }}</p>
            <div class="card-meta">{{ dataset.file_count }} 个文件</div>
          </div>
        </div>

        <!-- 自定义上传 -->
        <div class="upload-section">
          <h3 class="upload-title">或上传自定义文件</h3>
          <div class="upload-area" @dragover.prevent @drop.prevent="handleDrop">
            <input type="file" ref="fileInput" multiple accept=".md,.txt,.markdown" @change="handleFileChange" hidden />
            <button class="btn-upload" @click="$refs.fileInput.click()">选择文件</button>
            <span class="upload-hint">支持 .md / .txt 文件</span>
            <span v-if="uploadedFiles.length" class="file-count">{{ uploadedFiles.length }} 个文件已选择</span>
          </div>
          <div class="upload-actions">
            <input
              v-model="customProjectName"
              placeholder="项目名称（可选）"
              class="project-name-input"
            />
            <button
              class="btn-start"
              @click="handleCustomUpload"
              :disabled="!uploadedFiles.length || uploading"
            >
              {{ uploading ? '导入中...' : '开始导入' }}
            </button>
          </div>
        </div>

        <!-- 开始按钮（预设数据集） -->
        <div v-if="selectedDataset" class="start-section">
          <button class="btn-start-main" @click="handleIngest" :disabled="ingesting">
            {{ ingesting ? '正在导入...' : '导入并查看图谱' }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listPresets, ingestPreset, uploadDataset } from '../api/graph'

const router = useRouter()

const presets = ref([])
const loadingPresets = ref(false)
const selectedDataset = ref('')
const ingesting = ref(false)

// 自定义上传
const uploadedFiles = ref([])
const customProjectName = ref('')
const uploading = ref(false)
const fileInput = ref(null)

onMounted(async () => {
  loadingPresets.value = true
  try {
    const response = await listPresets()
    if (response.success) {
      presets.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load presets:', error)
  } finally {
    loadingPresets.value = false
  }
})

const handleSelectDataset = (name) => {
  selectedDataset.value = selectedDataset.value === name ? '' : name
}

const handleIngest = async () => {
  if (!selectedDataset.value || ingesting.value) return
  ingesting.value = true
  try {
    const response = await ingestPreset(selectedDataset.value)
    if (response.success) {
      router.push({
        name: 'Process',
        params: { projectId: response.data.project_id }
      })
    }
  } catch (error) {
    alert(`导入失败: ${error.message}`)
  } finally {
    ingesting.value = false
  }
}

const handleFileChange = (event) => {
  uploadedFiles.value = Array.from(event.target.files)
}

const handleDrop = (event) => {
  const files = Array.from(event.dataTransfer.files)
  uploadedFiles.value = files.filter(f => /\.(md|txt|markdown)$/i.test(f.name))
}

const handleCustomUpload = async () => {
  if (!uploadedFiles.value.length || uploading.value) return
  uploading.value = true

  try {
    const formData = new FormData()
    for (const file of uploadedFiles.value) {
      formData.append('files', file)
    }
    if (customProjectName.value) {
      formData.append('project_name', customProjectName.value)
    }

    const response = await uploadDataset(formData)
    if (response.success) {
      // 上传已接受，后台正在导入。立即跳转到 Process 页面轮询进度。
      router.push({
        name: 'Process',
        params: { projectId: response.data.project_id }
      })
    }
  } catch (error) {
    alert(`上传失败: ${error.message}`)
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: #fff;
}

.navbar {
  height: 60px;
  background: #000;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
}

.nav-brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 1.2rem;
  letter-spacing: 1px;
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
  transition: opacity 0.2s;
}

.nav-link:hover { opacity: 1; }

.main-content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 32px;
}

/* Hero */
.hero-section {
  padding: 80px 0 40px;
}

.hero-text {
  max-width: 700px;
}

.tag-row {
  margin-bottom: 20px;
}

.orange-tag {
  background: #FFF3E0;
  color: #E65100;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}

.main-title {
  font-size: 3rem;
  font-weight: 700;
  color: #111827;
  line-height: 1.2;
  margin: 0 0 20px;
}

.gradient-text {
  background: linear-gradient(135deg, #FF6B35, #FF4500);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-desc {
  font-size: 1.1rem;
  color: #6B7280;
  line-height: 1.7;
  margin: 0;
}

/* Datasets */
.datasets-section {
  padding: 20px 0 60px;
}

.section-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: #111827;
  margin: 0 0 24px;
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 60px;
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
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.dataset-card {
  border: 2px solid #E5E7EB;
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.2s;
}

.dataset-card:hover {
  border-color: #9CA3AF;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}

.dataset-card.active {
  border-color: #FF4500;
  background: #FFF8F5;
}

.card-icon {
  width: 40px;
  height: 40px;
  background: #F3F4F6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  color: #6B7280;
}

.dataset-card.active .card-icon {
  background: #FFECE5;
  color: #FF4500;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #111827;
  margin: 0 0 8px;
}

.card-desc {
  font-size: 0.9rem;
  color: #6B7280;
  margin: 0 0 12px;
  line-height: 1.5;
}

.card-meta {
  font-size: 0.8rem;
  color: #9CA3AF;
}

/* Upload */
.upload-section {
  margin-top: 40px;
  padding-top: 32px;
  border-top: 1px solid #F3F4F6;
}

.upload-title {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 16px;
}

.upload-area {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border: 2px dashed #E5E7EB;
  border-radius: 12px;
}

.btn-upload {
  padding: 8px 16px;
  background: #F3F4F6;
  border: none;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-upload:hover { background: #E5E7EB; }

.upload-hint {
  font-size: 0.85rem;
  color: #9CA3AF;
}

.file-count {
  font-size: 0.85rem;
  color: #10B981;
  font-weight: 500;
}

.upload-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.project-name-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 0.9rem;
  outline: none;
}

.project-name-input:focus {
  border-color: #000;
}

.btn-start {
  padding: 10px 24px;
  background: #000;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-start:hover:not(:disabled) { background: #374151; }
.btn-start:disabled { opacity: 0.4; cursor: not-allowed; }

/* Start button */
.start-section {
  margin-top: 32px;
  text-align: center;
}

.btn-start-main {
  padding: 14px 48px;
  background: #FF4500;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-start-main:hover:not(:disabled) {
  background: #E03E00;
  transform: translateY(-1px);
}

.btn-start-main:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 768px) {
  .navbar { padding: 0 16px; }
  .main-content { padding: 0 16px; }
  .hero-section { padding: 40px 0 20px; }
  .main-title { font-size: 2rem; }
  .datasets-grid { grid-template-columns: 1fr; }
  .upload-actions { flex-direction: column; }
}
</style>

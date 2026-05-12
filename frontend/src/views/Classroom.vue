<template>
  <div class="classroom-page">
    <!-- 顶部导航栏 -->
    <nav class="classroom-navbar">
      <button class="back-btn" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        {{ $t('common.back') }}
      </button>
      <div class="navbar-center">
        <span class="classroom-title">{{ nodeName }}</span>
        <span class="classroom-badge">{{ $t('classroom.virtualClassroom') }}</span>
      </div>
      <div class="navbar-status">
        <a href="https://github.com/DuanHangyu" target="_blank" class="nav-github-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
          访问 DuanHangyu 的 GitHub 主页
        </a>
        <span class="status-indicator" :class="connectionStatus"></span>
        <span class="status-label">{{ connectionStatusLabel }}</span>
      </div>
    </nav>

    <!-- iframe 容器 -->
    <div class="iframe-container">
      <!-- 加载状态 -->
      <div v-if="iframeLoading" class="iframe-loading">
        <div class="loading-spinner"></div>
        <p>{{ $t('classroom.loading') }}</p>
      </div>

      <iframe
        ref="classroomIframe"
        :src="classroomUrl"
        class="classroom-iframe"
        :class="{ 'iframe-hidden': iframeLoading }"
        allow="microphone; camera; autoplay 'src'; fullscreen 'src'; clipboard-write 'src'"
        @load="onIframeLoad"
        @error="onIframeError"
      ></iframe>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const classroomId = computed(() => route.params.classroomId)
const nodeName = computed(() => route.query.node_name || '')

const openmaicBaseUrl = import.meta.env.VITE_OPENMAIC_BASE_URL || 'http://localhost:3001'
const classroomUrl = computed(() => `${openmaicBaseUrl}/classroom/${classroomId.value}`)

const iframeLoading = ref(true)
const connectionStatus = ref('connecting') // connecting, connected, error
const classroomIframe = ref(null)

const connectionStatusLabel = computed(() => {
  if (connectionStatus.value === 'connected') return t('classroom.connected')
  if (connectionStatus.value === 'error') return t('common.error')
  return t('classroom.loading')
})

const goBack = () => {
  router.back()
}

const onIframeLoad = () => {
  iframeLoading.value = false
  connectionStatus.value = 'connected'
}

const onIframeError = () => {
  iframeLoading.value = false
  connectionStatus.value = 'error'
}

onMounted(() => {
  // 10秒超时自动隐藏加载状态
  setTimeout(() => {
    if (iframeLoading.value) {
      iframeLoading.value = false
      if (connectionStatus.value === 'connecting') {
        connectionStatus.value = 'connected'
      }
    }
  }, 10000)
})
</script>

<style scoped>
.classroom-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #0a0a0a;
}

.classroom-navbar {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #111;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
  z-index: 10;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #ccc;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.82rem;
  transition: all 0.2s ease;
}

.back-btn:hover {
  border-color: rgba(255, 255, 255, 0.3);
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
}

.navbar-center {
  display: flex;
  align-items: center;
  gap: 10px;
}

.classroom-title {
  color: #eee;
  font-size: 0.9rem;
  font-weight: 600;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.classroom-badge {
  font-size: 0.68rem;
  color: #7B2D8E;
  background: rgba(123, 45, 142, 0.15);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.nav-github-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #fff;
  text-decoration: none;
  font-size: 0.9rem;
  opacity: 0.8;
  transition: opacity 0.2s;
  background: rgba(255,255,255,0.1);
  padding: 5px 12px;
  border-radius: 6px;
}

.nav-github-link:hover { opacity: 1; background: rgba(255,255,255,0.15); }

.navbar-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #FFB800;
}

.status-indicator.connected {
  background: #1A936F;
}

.status-indicator.error {
  background: #E74C3C;
}

.status-label {
  font-size: 0.75rem;
  color: #888;
}

.iframe-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.iframe-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #888;
  font-size: 0.9rem;
  z-index: 5;
  background: #0a0a0a;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(123, 45, 142, 0.2);
  border-top-color: #7B2D8E;
  border-radius: 50%;
  animation: iframe-spin 0.8s linear infinite;
}

@keyframes iframe-spin {
  to { transform: rotate(360deg); }
}

.classroom-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: #fff;
}

.classroom-iframe.iframe-hidden {
  opacity: 0;
  pointer-events: none;
  position: absolute;
}
</style>

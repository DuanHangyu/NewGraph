<template>
  <div class="qa-container">
    <!-- 顶部导航栏 -->
    <nav class="navbar">
      <div class="nav-brand">NEWGRAPH</div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link to="/history" class="nav-link">历史</router-link>
        <router-link :to="`/process/${projectId}`" class="nav-link">图谱</router-link>
        <a href="https://github.com/DuanHangyu" target="_blank" class="nav-github-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
        </a>
      </div>
    </nav>

    <div class="qa-main">
      <!-- 顶部信息栏 -->
      <div class="qa-header">
        <h1 class="qa-title">知识图谱问答</h1>
        <span class="qa-dataset" v-if="projectName">{{ projectName }}</span>
      </div>

      <!-- 聊天区域 -->
      <div class="chat-area" ref="chatArea">
        <!-- 空状态 -->
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-icon">?</div>
          <p class="empty-text">基于知识图谱的智能问答</p>
          <p class="empty-hint">输入问题开始对话，系统将检索知识图谱并生成回答</p>
        </div>

        <!-- 消息列表 -->
        <div v-else class="messages">
          <div
            v-for="msg in messages"
            :key="msg.id || msg.timestamp"
            class="message-wrapper"
            :class="msg.role"
          >
            <div class="message-bubble" :class="msg.role">
              <div v-if="msg.role === 'user'" class="message-content">{{ msg.content }}</div>
              <div v-else class="message-content" v-html="renderMarkdown(msg.content)"></div>

              <!-- 来源引用（可折叠） -->
              <div v-if="msg.role === 'assistant' && msg.sources && msg.sources.length > 0" class="sources-section">
                <button class="sources-toggle" @click="toggleSources(msg.timestamp)">
                  {{ expandedSources[msg.timestamp] ? '收起来源' : `查看来源 (${msg.sources.length})` }}
                </button>
                <div v-if="expandedSources[msg.timestamp]" class="sources-list">
                  <div v-for="source in msg.sources" :key="source.uuid" class="source-item">
                    <div class="source-relation">
                      <span class="source-name">{{ source.source_node?.name || '?' }}</span>
                      <span class="source-arrow">→</span>
                      <span class="source-fact">{{ source.fact || source.name || '相关' }}</span>
                      <span class="source-arrow">→</span>
                      <span class="source-name">{{ source.target_node?.name || '?' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 加载状态 -->
          <div v-if="loading" class="message-wrapper assistant">
            <div class="message-bubble assistant loading">
              <div class="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-wrapper">
          <textarea
            v-model="question"
            @keydown.enter.exact.prevent="handleAsk"
            placeholder="输入你的问题..."
            rows="1"
            :disabled="loading"
            ref="inputRef"
          ></textarea>
          <button class="send-btn" @click="handleAsk" :disabled="!question.trim() || loading">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
        <p class="input-hint">按 Enter 发送，Shift+Enter 换行</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { askQuestion, getProject } from '../api/graph'
import { marked } from 'marked'

const route = useRoute()
const props = defineProps({ projectId: String })
const projectId = props.projectId || route.params.projectId

const projectName = ref('')
const messages = ref([])
const question = ref('')
const loading = ref(false)
const sessionId = ref(null)
const expandedSources = reactive({})
const chatArea = ref(null)
const inputRef = ref(null)

marked.setOptions({ breaks: true })

const renderMarkdown = (text) => {
  if (!text) return ''
  return marked.parse(text)
}

const toggleSources = (timestamp) => {
  expandedSources[timestamp] = !expandedSources[timestamp]
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatArea.value) {
    chatArea.value.scrollTop = chatArea.value.scrollHeight
  }
}

const handleAsk = async () => {
  const q = question.value.trim()
  if (!q || loading.value) return

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: q,
    timestamp: Date.now(),
  })
  question.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const response = await askQuestion(projectId, q, sessionId.value)
    if (response.success) {
      sessionId.value = response.data.session_id

      messages.value.push({
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources || [],
        search_stats: response.data.search_stats,
        timestamp: response.data.timestamp,
      })
    }
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: `抱歉，问答服务出现错误: ${error.message}`,
      sources: [],
      timestamp: Date.now(),
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

onMounted(async () => {
  // 加载项目信息
  try {
    const response = await getProject(projectId)
    if (response.success) {
      projectName.value = response.data.name || ''
    }
  } catch {
    // ignore
  }
  inputRef.value?.focus()
})
</script>

<style scoped>
.qa-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #F9FAFB;
}

.navbar {
  height: 56px;
  background: #000;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  flex-shrink: 0;
}

.nav-brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 1.1rem;
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

.qa-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
  padding: 0 24px;
}

.qa-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 0;
  border-bottom: 1px solid #E5E7EB;
}

.qa-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.qa-dataset {
  font-size: 0.85rem;
  color: #6B7280;
  background: #F3F4F6;
  padding: 4px 12px;
  border-radius: 12px;
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  gap: 12px;
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.4;
}

.empty-text {
  font-size: 1.2rem;
  color: #374151;
  margin: 0;
  font-weight: 500;
}

.empty-hint {
  font-size: 0.9rem;
  color: #9CA3AF;
  margin: 0;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-wrapper {
  display: flex;
}

.message-wrapper.user {
  justify-content: flex-end;
}

.message-wrapper.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 0.95rem;
  line-height: 1.6;
}

.message-bubble.user {
  background: #000;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-bubble.assistant {
  background: #fff;
  color: #111827;
  border: 1px solid #E5E7EB;
  border-bottom-left-radius: 4px;
}

.message-bubble.assistant :deep(p) {
  margin: 0 0 8px;
}

.message-bubble.assistant :deep(p:last-child) {
  margin-bottom: 0;
}

.message-bubble.assistant :deep(strong) {
  color: #000;
}

.message-bubble.assistant :deep(ul),
.message-bubble.assistant :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.sources-section {
  margin-top: 12px;
  border-top: 1px solid #F3F4F6;
  padding-top: 8px;
}

.sources-toggle {
  background: none;
  border: none;
  color: #6B7280;
  font-size: 0.8rem;
  cursor: pointer;
  padding: 4px 0;
}

.sources-toggle:hover {
  color: #111827;
}

.sources-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.source-item {
  background: #F9FAFB;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
}

.source-relation {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.source-name {
  font-weight: 600;
  color: #111827;
}

.source-arrow {
  color: #9CA3AF;
  font-size: 0.8rem;
}

.source-fact {
  color: #6B7280;
  font-style: italic;
}

.loading-dots {
  display: flex;
  gap: 6px;
  padding: 4px 0;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #D1D5DB;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.loading-dots span:nth-child(1) { animation-delay: 0s; }
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.input-area {
  padding: 16px 0 24px;
  border-top: 1px solid #E5E7EB;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 8px 12px;
}

.input-wrapper:focus-within {
  border-color: #000;
}

.input-wrapper textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 0.95rem;
  font-family: inherit;
  line-height: 1.5;
  max-height: 120px;
  color: #111827;
  background: transparent;
}

.input-wrapper textarea::placeholder {
  color: #9CA3AF;
}

.send-btn {
  background: #000;
  color: #fff;
  border: none;
  border-radius: 8px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: #374151;
}

.send-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.input-hint {
  font-size: 0.75rem;
  color: #9CA3AF;
  margin: 6px 0 0;
  text-align: center;
}

@media (max-width: 768px) {
  .navbar { padding: 0 16px; }
  .qa-main { padding: 0 12px; }
  .message-bubble { max-width: 90%; }
}
</style>

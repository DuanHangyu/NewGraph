<template>
  <div class="qa-graph-page">
    <!-- Navbar -->
    <nav class="navbar">
      <div class="nav-brand" @click="$router.push('/')">NEWGRAPH</div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link to="/history" class="nav-link">历史</router-link>
        <router-link :to="`/process/${projectId}`" class="nav-link">图谱(全屏)</router-link>
        <a href="https://github.com/DuanHangyu" target="_blank" class="nav-github-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
          访问 DuanHangyu 的 GitHub 主页
        </a>
      </div>
    </nav>

    <!-- Main split layout -->
    <div class="split-container">
      <!-- Left: Graph (60%) -->
      <div class="graph-panel">
        <div class="panel-header">
          <span class="panel-title">知识图谱</span>
          <div class="panel-actions">
            <span v-if="graphData" class="panel-stats">
              {{ graphData.nodes?.length || 0 }} 节点 | {{ graphData.edges?.length || 0 }} 关系
            </span>
            <button
              v-if="highlightedNodeUuids.size > 0"
              class="reset-highlight-btn"
              @click="clearHighlights"
            >重置高亮</button>
          </div>
        </div>
        <div class="graph-container" ref="graphContainer">
          <div v-if="graphLoading" class="graph-loading">
            <div class="spinner"></div>
            <span>加载图谱...</span>
          </div>
          <div v-else-if="!graphData" class="graph-empty">
            <span>暂无图谱数据</span>
          </div>
          <svg v-show="graphData" ref="graphSvg" class="graph-svg"></svg>
        </div>
      </div>

      <!-- Divider -->
      <div class="split-divider"></div>

      <!-- Right: Chat (40%) -->
      <div class="chat-panel">
        <div class="chat-header">
          <h2 class="chat-title">知识图谱问答</h2>
          <span class="chat-dataset" v-if="projectName">{{ projectName }}</span>
        </div>

        <div class="chat-area" ref="chatArea">
          <!-- Empty state -->
          <div v-if="messages.length === 0 && !loading" class="empty-state">
            <div class="empty-icon">?</div>
            <p class="empty-text">基于知识图谱的智能问答</p>
            <p class="empty-hint">输入问题开始对话，检索过程将在左侧图谱实时可视化</p>
          </div>

          <!-- Messages -->
          <div v-else class="messages">
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="message-wrapper"
              :class="msg.role"
            >
              <div class="message-bubble" :class="msg.role">
                <div v-if="msg.role === 'user'" class="message-content">{{ msg.content }}</div>
                <div v-else class="message-content" v-html="renderMarkdown(msg.content)"></div>

                <!-- Sources -->
                <div v-if="msg.role === 'assistant' && msg.sources && msg.sources.length > 0" class="sources-section">
                  <button class="sources-toggle" @click="toggleSources(msg.id)">
                    {{ expandedSources[msg.id] ? '收起来源' : `查看来源 (${msg.sources.length})` }}
                  </button>
                  <div v-if="expandedSources[msg.id]" class="sources-list">
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

            <!-- Stage status indicator -->
            <div v-if="loading && !streamingAnswer" class="message-wrapper assistant">
              <div class="message-bubble assistant status-bubble">
                <div class="stage-list">
                  <div
                    v-for="stage in statusStages"
                    :key="stage.key"
                    class="stage-item"
                    :class="stage.state"
                  >
                    <span class="stage-icon">
                      <span v-if="stage.state === 'done'" class="stage-check">&#10003;</span>
                      <span v-else-if="stage.state === 'active'" class="stage-spinner"></span>
                      <span v-else class="stage-dot"></span>
                    </span>
                    <span class="stage-text">{{ stage.text }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Streaming answer bubble -->
            <div v-if="streamingAnswer" class="message-wrapper assistant">
              <div class="message-bubble assistant">
                <div class="message-content" v-html="renderMarkdown(streamingAnswer)"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="input-area">
          <div class="input-wrapper">
            <textarea
              v-model="question"
              @keydown.enter.exact.prevent="handleAskStream"
              placeholder="输入你的问题..."
              rows="1"
              :disabled="loading"
              ref="inputRef"
            ></textarea>
            <button class="send-btn" @click="handleAskStream" :disabled="!question.trim() || loading">
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
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, reactive, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getProject, getGraphitiData, askQuestionStream } from '../api/graph'
import { renderGraph, applyHighlights, startSearchScan } from '../composables/useGraphRenderer'
import { marked } from 'marked'

const route = useRoute()
const props = defineProps({ projectId: String })
const projectId = props.projectId || route.params.projectId

marked.setOptions({ breaks: true })

// Project info
const projectName = ref('')

// Graph state
const graphContainer = ref(null)
const graphSvg = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)

// Chat state
const chatArea = ref(null)
const inputRef = ref(null)
const question = ref('')
const loading = ref(false)
const sessionId = ref(null)
const messages = ref([])
const expandedSources = reactive({})
const streamingAnswer = ref('')

// Stage status
const statusStages = ref([
  { key: 'searching', text: '检索知识图谱...', state: 'pending' },
  { key: 'found', text: '找到相关实体', state: 'pending' },
  { key: 'generating', text: '正在生成回答...', state: 'pending' },
])

// Highlight state
const highlightedNodeUuids = ref(new Set())
const highlightedEdgeUuids = ref(new Set())
let pulseHandle = null
let graphRenderResult = null

const clearHighlights = () => {
  highlightedNodeUuids.value = new Set()
  highlightedEdgeUuids.value = new Set()
  if (graphSvg.value) {
    applyHighlights(graphSvg.value, new Set(), new Set())
  }
}

const renderMarkdown = (text) => {
  if (!text) return ''
  return marked.parse(text)
}

const toggleSources = (id) => {
  expandedSources[id] = !expandedSources[id]
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatArea.value) {
    chatArea.value.scrollTop = chatArea.value.scrollHeight
  }
}

const resetStages = () => {
  statusStages.value.forEach(s => { s.state = 'pending' })
}

const setStageState = (key, state) => {
  const stage = statusStages.value.find(s => s.key === key)
  if (stage) {
    stage.state = state
    // Auto-advance: mark previous stages as done
    const idx = statusStages.value.indexOf(stage)
    for (let i = 0; i < idx; i++) {
      if (statusStages.value[i].state === 'pending') {
        statusStages.value[i].state = 'done'
      }
    }
  }
}

// Load graph data
const loadGraph = async () => {
  graphLoading.value = true
  try {
    const response = await getGraphitiData(projectId)
    if (response.success && response.data) {
      graphData.value = response.data
    }
  } catch (err) {
    console.error('Failed to load graph:', err)
  } finally {
    graphLoading.value = false
  }
}

// Render graph when data loads
watch(graphData, (val) => {
  if (val) {
    nextTick(() => {
      if (graphSvg.value && graphContainer.value) {
        graphRenderResult = renderGraph(graphSvg.value, val, graphContainer.value, {
          includeGlowFilter: true,
          heightOffset: 0,
          onNodeClick: () => {},
          onEdgeClick: () => {},
          onBackgroundClick: () => {},
        })
        // Re-apply highlights if any
        if (highlightedNodeUuids.value.size > 0) {
          applyHighlights(graphSvg.value, highlightedNodeUuids.value, highlightedEdgeUuids.value)
        }
      }
    })
  }
})

// SSE streaming ask
const handleAskStream = async () => {
  const q = question.value.trim()
  if (!q || loading.value) return

  // Add user message
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: q,
  })
  question.value = ''
  loading.value = true
  streamingAnswer.value = ''
  resetStages()
  // 清除上次检索的高亮
  clearHighlights()
  await scrollToBottom()

  try {
    const response = await askQuestionStream(projectId, q, sessionId.value)
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Parse SSE data lines
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const jsonStr = line.slice(6).trim()
        if (!jsonStr) continue

        let event
        try {
          event = JSON.parse(jsonStr)
        } catch {
          continue
        }

        handleSSEEvent(event)
        await scrollToBottom()
      }
    }
  } catch (error) {
    messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: `抱歉，问答服务出现错误: ${error.message}`,
      sources: [],
    })
  } finally {
    // 确保脉冲波停止
    if (pulseHandle) {
      pulseHandle.stop()
      pulseHandle = null
    }
    // Finalize: move streaming answer to messages
    if (streamingAnswer.value) {
      const lastMsg = messages.value[messages.value - 1]
      // Add as completed message
      messages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: streamingAnswer.value,
        sources: [],
      })
      streamingAnswer.value = ''
    }
    loading.value = false
    resetStages()
    await scrollToBottom()
  }
}

const handleSSEEvent = (event) => {
  switch (event.type) {
    case 'status':
      handleStatusEvent(event)
      break
    case 'token':
      handleTokenEvent(event)
      break
    case 'done':
      handleDoneEvent(event)
      break
    case 'meta':
      if (event.session_id) {
        sessionId.value = event.session_id
      }
      break
    case 'error':
      messages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: `错误: ${event.message}`,
        sources: [],
      })
      loading.value = false
      break
  }
}

const handleStatusEvent = (event) => {
  switch (event.stage) {
    case 'searching':
      setStageState('searching', 'active')
      // 启动图谱遍历扫描动画
      if (graphRenderResult && graphSvg.value) {
        const { nodes, edges } = graphRenderResult
        pulseHandle = startSearchScan(graphSvg.value, nodes, edges)
      }
      break
    case 'found':
      // 停止脉冲波
      if (pulseHandle) {
        pulseHandle.stop()
        pulseHandle = null
      }

      setStageState('searching', 'done')
      setStageState('found', 'active')

      // Update stage text with count
      const foundStage = statusStages.value.find(s => s.key === 'found')
      if (foundStage) {
        foundStage.text = event.message || `找到 ${event.node_uuids?.length || 0} 个相关实体`
      }

      // Apply highlights (弹跳 + 光环 + 边流动)
      if (event.node_uuids?.length) {
        highlightedNodeUuids.value = new Set(event.node_uuids)
        highlightedEdgeUuids.value = new Set(event.edge_uuids || [])
        if (graphSvg.value) {
          applyHighlights(graphSvg.value, highlightedNodeUuids.value, highlightedEdgeUuids.value)
        }
      }
      break
    case 'generating':
      setStageState('found', 'done')
      setStageState('generating', 'active')
      break
  }
}

const handleTokenEvent = (event) => {
  streamingAnswer.value += event.content
  setStageState('generating', 'done')
}

const handleDoneEvent = (event) => {
  // Replace streaming answer with final answer
  if (streamingAnswer.value || event.answer) {
    const answer = event.answer || streamingAnswer.value
    // Update last assistant message or add new one
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg?.role === 'assistant') {
      lastMsg.content = answer
      lastMsg.sources = event.sources || []
    } else {
      messages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: answer,
        sources: event.sources || [],
      })
    }
    streamingAnswer.value = ''
  }

  // 高亮保持，不自动淡出。用户下次提问或点重置按钮时清除。
}

onMounted(async () => {
  // Load project info
  try {
    const response = await getProject(projectId)
    if (response.success) {
      projectName.value = response.data.name || ''
    }
  } catch {
    // ignore
  }

  // Load graph data
  await loadGraph()
  inputRef.value?.focus()
})
</script>

<style scoped>
.qa-graph-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #F9FAFB;
  overflow: hidden;
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
  cursor: pointer;
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

.split-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.graph-panel {
  flex: 0 0 60%;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #E5E7EB;
  background: #fff;
}

.panel-header {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid #F3F4F6;
  flex-shrink: 0;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
}

.reset-highlight-btn {
  background: #F3F4F6;
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  padding: 3px 10px;
  font-size: 0.75rem;
  color: #6B7280;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-highlight-btn:hover {
  background: #E5E7EB;
  color: #374151;
}

.panel-stats {
  font-size: 0.8rem;
  color: #9CA3AF;
}

.graph-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.graph-svg {
  width: 100%;
  height: 100%;
}

.graph-loading,
.graph-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #9CA3AF;
  font-size: 0.9rem;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #E5E7EB;
  border-top-color: #000;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.split-divider {
  width: 1px;
  background: #E5E7EB;
  flex-shrink: 0;
}

.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #F9FAFB;
}

.chat-header {
  height: 44px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px;
  border-bottom: 1px solid #E5E7EB;
  flex-shrink: 0;
  background: #fff;
}

.chat-title {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.chat-dataset {
  font-size: 0.8rem;
  color: #6B7280;
  background: #F3F4F6;
  padding: 2px 10px;
  border-radius: 12px;
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
  gap: 8px;
}

.empty-icon {
  font-size: 2.5rem;
  opacity: 0.4;
}

.empty-text {
  font-size: 1.1rem;
  color: #374151;
  margin: 0;
  font-weight: 500;
}

.empty-hint {
  font-size: 0.85rem;
  color: #9CA3AF;
  margin: 0;
  text-align: center;
  max-width: 280px;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-wrapper {
  display: flex;
}

.message-wrapper.user { justify-content: flex-end; }
.message-wrapper.assistant { justify-content: flex-start; }

.message-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 0.9rem;
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

.message-bubble.assistant :deep(p) { margin: 0 0 8px; }
.message-bubble.assistant :deep(p:last-child) { margin-bottom: 0; }
.message-bubble.assistant :deep(strong) { color: #000; }
.message-bubble.assistant :deep(ul),
.message-bubble.assistant :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

/* Stage status */
.status-bubble {
  min-width: 200px;
}

.stage-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #9CA3AF;
  transition: color 0.3s;
}

.stage-item.active { color: #2563EB; }
.stage-item.done { color: #059669; }

.stage-icon {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stage-check {
  color: #059669;
  font-weight: bold;
  font-size: 0.9rem;
}

.stage-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #BFDBFE;
  border-top-color: #2563EB;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.stage-dot {
  width: 8px;
  height: 8px;
  background: #D1D5DB;
  border-radius: 50%;
}

/* Sources */
.sources-section {
  margin-top: 10px;
  border-top: 1px solid #F3F4F6;
  padding-top: 6px;
}

.sources-toggle {
  background: none;
  border: none;
  color: #6B7280;
  font-size: 0.75rem;
  cursor: pointer;
  padding: 2px 0;
}

.sources-toggle:hover { color: #111827; }

.sources-list {
  margin-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.source-item {
  background: #F9FAFB;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 0.8rem;
}

.source-relation {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.source-name { font-weight: 600; color: #111827; }
.source-arrow { color: #9CA3AF; font-size: 0.75rem; }
.source-fact { color: #6B7280; font-style: italic; }

/* Input */
.input-area {
  padding: 12px 20px 16px;
  border-top: 1px solid #E5E7EB;
  flex-shrink: 0;
  background: #fff;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 8px 12px;
}

.input-wrapper:focus-within { border-color: #000; }

.input-wrapper textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 0.9rem;
  font-family: inherit;
  line-height: 1.5;
  max-height: 100px;
  color: #111827;
  background: transparent;
}

.input-wrapper textarea::placeholder { color: #9CA3AF; }

.send-btn {
  background: #000;
  color: #fff;
  border: none;
  border-radius: 8px;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) { background: #374151; }
.send-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.input-hint {
  font-size: 0.7rem;
  color: #9CA3AF;
  margin: 4px 0 0;
  text-align: center;
}

@media (max-width: 900px) {
  .split-container { flex-direction: column; }
  .graph-panel { flex: 0 0 45%; border-right: none; border-bottom: 1px solid #E5E7EB; }
  .split-divider { display: none; }
  .chat-panel { flex: 1; }
}
</style>

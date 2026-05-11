<template>
  <div class="hint-panel" :class="{ 'hint-panel--open': isOpen }">
    <div class="hint-panel-header">
      <span class="hint-panel-title">{{ $t('workbench.hintTitle') }}</span>
      <button class="hint-panel-close" @click="$emit('close')">&times;</button>
    </div>

    <div class="hint-panel-content">
      <!-- Loading state -->
      <div v-if="loading" class="hint-loading">
        <div class="hint-spinner"></div>
        <p>{{ $t('workbench.hintGenerating') }}</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="hint-error">
        <p>{{ error }}</p>
        <button class="hint-retry-btn" @click="fetchHint(currentLevel)">{{ $t('common.retry') }}</button>
      </div>

      <!-- Hint content -->
      <div v-else-if="currentHint" class="hint-display">
        <div class="hint-level-badge" :class="{ 'level-l1': currentHint.level === 1, 'level-l2': currentHint.level === 2 }">
          {{ currentHint.level === 1 ? 'L1' : 'L2' }}
        </div>
        <div class="hint-text">{{ currentHint.hint_content }}</div>

        <!-- L1 actions -->
        <div v-if="currentHint.level === 1" class="hint-actions">
          <button class="hint-btn hint-btn--primary" @click="$emit('close')">{{ $t('workbench.gotIt') }}</button>
          <button class="hint-btn hint-btn--secondary" @click="requestL2">{{ $t('workbench.stillConfused') }}</button>
        </div>

        <!-- L2 actions -->
        <div v-if="currentHint.level === 2" class="hint-actions">
          <button class="hint-btn hint-btn--primary" @click="$emit('close')">{{ $t('workbench.goBackTry') }}</button>
          <button class="hint-btn hint-btn--accent" @click="openClassroom">{{ $t('workbench.wantClassroom') }}</button>
        </div>

        <!-- Related knowledge points -->
        <div v-if="knowledgePoints && knowledgePoints.length > 0" class="hint-kps">
          <div class="hint-kps-label">{{ $t('workbench.relatedKnowledge') }}</div>
          <div class="hint-kps-list">
            <span v-for="kp in knowledgePoints" :key="kp.uuid" class="hint-kp-tag">{{ kp.name }}</span>
          </div>
        </div>
      </div>

      <!-- Empty/initial state (auto-fetches L1) -->
      <div v-else-if="!loading && !error" class="hint-empty">
        <p>{{ $t('workbench.hintGenerating') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { generateHint } from '../api/graph'
import { addHintHistory } from '../store/progress'

const { t } = useI18n()

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  milestoneUuid: { type: String, default: '' },
  milestoneOrder: { type: Number, default: 0 },
  projectId: { type: String, default: '' },
  knowledgePoints: { type: Array, default: () => [] },
  activeKPUuid: { type: String, default: '' },
})

const emit = defineEmits(['close', 'request-classroom'])

const loading = ref(false)
const error = ref('')
const currentHint = ref(null)
const currentLevel = ref(1)

// Reset hint state and auto-fetch L1 when panel opens or milestone changes
watch(() => props.isOpen, (newVal) => {
  if (newVal && !loading.value) {
    currentHint.value = null
    error.value = ''
    fetchHint(1)
  }
})

watch(() => props.milestoneUuid, () => {
  currentHint.value = null
  error.value = ''
})

const fetchHint = async (level) => {
  if (!props.projectId || !props.milestoneUuid) return

  loading.value = true
  error.value = ''
  currentLevel.value = level

  try {
    const res = await generateHint({
      project_id: props.projectId,
      milestone_uuid: props.milestoneUuid,
      level,
    })

    currentHint.value = res.data
    loading.value = false
    addHintHistory(props.projectId, props.milestoneOrder, level)
  } catch (err) {
    console.error('Hint generation failed:', err)
    error.value = err.message || t('workbench.hintGenerating')
    loading.value = false
  }
}

const requestL2 = () => {
  fetchHint(2)
}

const openClassroom = () => {
  // Use activeKPUuid if provided, otherwise default to first KP
  let kp = null
  if (props.activeKPUuid && props.knowledgePoints.length > 0) {
    kp = props.knowledgePoints.find(k => k.uuid === props.activeKPUuid)
  }
  if (!kp && props.knowledgePoints.length > 0) {
    kp = props.knowledgePoints[0]
  }
  if (kp) {
    emit('request-classroom', kp.uuid, kp.name)
  }
}
</script>

<style scoped>
.hint-panel {
  position: fixed;
  top: 60px;
  right: 0;
  width: 360px;
  height: calc(100vh - 60px);
  background: #111;
  color: #fff;
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 100;
  overflow-y: auto;
  border-left: 1px solid #333;
}

.hint-panel--open {
  transform: translateX(0);
}

.hint-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #333;
}

.hint-panel-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  font-weight: 700;
  color: #FF4500;
  letter-spacing: 1px;
}

.hint-panel-close {
  background: none;
  border: none;
  color: #666;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0 4px;
  transition: color 0.2s;
}

.hint-panel-close:hover {
  color: #fff;
}

.hint-panel-content {
  padding: 20px;
}

.hint-loading {
  text-align: center;
  padding: 40px 0;
}

.hint-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #333;
  border-top-color: #FF4500;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.hint-loading p,
.hint-empty p {
  font-family: 'JetBrains Mono', monospace;
  color: #666;
  font-size: 0.8rem;
}

.hint-error {
  text-align: center;
  padding: 30px 0;
}

.hint-error p {
  color: #FF4500;
  margin-bottom: 20px;
}

.hint-retry-btn {
  background: #222;
  color: #FF4500;
  border: 1px solid #FF4500;
  padding: 8px 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  cursor: pointer;
  transition: background 0.2s;
}

.hint-retry-btn:hover {
  background: #FF4500;
  color: #fff;
}

.hint-level-badge {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 10px;
  margin-bottom: 16px;
  letter-spacing: 1px;
}

.hint-level-badge.level-l1 {
  background: #222;
  color: #FF4500;
  border: 1px solid #FF4500;
}

.hint-level-badge.level-l2 {
  background: #FF4500;
  color: #fff;
}

.hint-text {
  line-height: 1.7;
  font-size: 0.9rem;
  color: #ddd;
  margin-bottom: 24px;
  white-space: pre-line;
}

.hint-text p {
  margin-bottom: 12px;
}

.hint-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.hint-btn {
  padding: 10px 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  cursor: pointer;
  border: 1px solid;
  transition: all 0.2s;
  letter-spacing: 0.5px;
}

.hint-btn--primary {
  background: #222;
  color: #fff;
  border-color: #444;
}

.hint-btn--primary:hover {
  background: #333;
  border-color: #666;
}

.hint-btn--secondary {
  background: transparent;
  color: #FF4500;
  border-color: #FF4500;
}

.hint-btn--secondary:hover {
  background: #FF4500;
  color: #fff;
}

.hint-btn--accent {
  background: transparent;
  color: #FF4500;
  border-color: #FF4500;
  font-weight: 700;
}

.hint-btn--accent:hover {
  background: #FF4500;
  color: #fff;
}

.hint-kps {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #333;
}

.hint-kps-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #666;
  margin-bottom: 8px;
}

.hint-kps-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.hint-kp-tag {
  background: #222;
  color: #ddd;
  padding: 4px 10px;
  font-size: 0.75rem;
  border: 1px solid #333;
  font-family: 'JetBrains Mono', monospace;
}
</style>
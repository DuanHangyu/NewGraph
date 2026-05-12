<template>
  <div class="workbench-container">
    <!-- Navbar -->
    <nav class="workbench-navbar">
      <div class="navbar-brand">NEWGRAPH</div>
      <div class="navbar-project-name">{{ projectName || '...' }}</div>
      <div class="navbar-links">
        <LanguageSwitcher />
        <router-link :to="{ name: 'Process', params: { projectId } }" class="nav-back-link">
          {{ $t('workbench.backToGraph') }}
        </router-link>
        <a href="https://github.com/DuanHangyu" target="_blank" class="nav-github-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
          访问 DuanHangyu 的 GitHub 主页
        </a>
      </div>
    </nav>

    <!-- 3-panel layout -->
    <div class="workbench-layout">
      <!-- Left: Milestone sidebar -->
      <aside class="milestone-sidebar">
        <div class="sidebar-header">{{ $t('workbench.milestones') }}</div>

        <div v-if="milestones.length === 0" class="sidebar-empty">
          {{ $t('workbench.noMilestones') }}
        </div>

        <ul v-else class="milestone-list">
          <li
            v-for="ms in milestones"
            :key="ms.uuid"
            class="milestone-item"
            :class="{
              'milestone-item--completed': getMilestoneStatus(projectId, ms.order) === 'completed',
              'milestone-item--current': getMilestoneStatus(projectId, ms.order) === 'in_progress',
              'milestone-item--locked': getMilestoneStatus(projectId, ms.order) === 'locked',
            }"
            @click="selectMilestone(ms)"
          >
            <span class="milestone-icon">
              <template v-if="getMilestoneStatus(projectId, ms.order) === 'completed'">&#10003;</template>
              <template v-else-if="getMilestoneStatus(projectId, ms.order) === 'in_progress'">&#9679;</template>
              <template v-else>&#9675;</template>
            </span>
            <span class="milestone-name">{{ ms.name }}</span>
          </li>
        </ul>

        <div class="sidebar-footer">
          <button class="help-btn" @click="toggleHintPanel">
            &#128161; {{ $t('workbench.helpBtn') }}
          </button>
        </div>
      </aside>

      <!-- Center: Work area -->
      <main class="work-area">
        <template v-if="currentMilestone">
          <h2 class="milestone-title">{{ currentMilestone.name }}</h2>

          <div class="milestone-description">
            <p>{{ currentMilestone.description || $t('workbench.noMilestones') }}</p>
          </div>

          <!-- Acceptance criteria -->
          <div v-if="currentMilestone.acceptance_criteria" class="acceptance-section">
            <div class="acceptance-label">{{ $t('workbench.acceptanceCriteria') }}</div>
            <div class="acceptance-text">{{ currentMilestone.acceptance_criteria }}</div>
          </div>

          <!-- Knowledge points -->
          <div v-if="currentMilestone.knowledge_points?.length" class="kp-section">
            <div class="kp-label">{{ $t('workbench.relatedKnowledge') }}</div>
            <div class="kp-list">
              <div v-for="kp in currentMilestone.knowledge_points" :key="kp.uuid" class="kp-card" @click="openHintForKP(kp)">
                <div class="kp-card-header">
                  <div class="kp-card-name">{{ kp.name }}</div>
                  <span v-if="kp.difficulty" class="kp-card-difficulty" :class="'diff-' + kp.difficulty">{{ $t('workbench.kp' + kp.difficulty.charAt(0).toUpperCase() + kp.difficulty.slice(1)) }}</span>
                </div>
                <div class="kp-card-summary">{{ kp.summary }}</div>
                <button
                  class="kp-classroom-btn"
                  :class="{ 'kp-classroom-btn--ready': kp.classroom_id }"
                  @click.stop="kp.classroom_id ? openClassroom(kp.classroom_id, kp.name) : handleClassroomRequest(kp.uuid, kp.name)"
                >
                  {{ kp.classroom_id ? $t('workbench.reenterClassroom') : $t('workbench.enterClassroom') }}
                </button>
              </div>
            </div>
          </div>

          <!-- Submission textarea -->
          <div class="submission-section">
            <textarea
              v-model="submissionText"
              class="submission-input"
              :placeholder="$t('workbench.submissionPlaceholder')"
              rows="4"
              @input="onNoteInput"
            ></textarea>
          </div>

          <!-- Mark complete button -->
          <div class="complete-section">
            <button
              v-if="getMilestoneStatus(projectId, currentMilestone.order) !== 'completed'"
              class="complete-btn"
              :disabled="markingComplete"
              @click="markComplete"
            >
              {{ markingComplete ? $t('common.loading') : $t('workbench.markComplete') }}
            </button>
            <div v-else class="completed-label">
              &#10003; {{ $t('workbench.alreadyCompleted') }}
            </div>
          </div>

          <!-- Progress bar -->
          <div class="progress-bar-section">
            <div class="progress-stats">
              {{ getCompletedCount(projectId) }}/{{ milestones.length }} {{ $t('workbench.milestones') }}
              &nbsp;|&nbsp;
              {{ getHintCount(projectId) }} {{ $t('workbench.hintsUsed') }}
            </div>
            <div class="progress-bar-track">
              <div
                class="progress-bar-fill"
                :style="{ width: progressPercent + '%' }"
              ></div>
            </div>
          </div>

          <!-- Project completed banner -->
          <div v-if="isProjectCompleted(projectId)" class="project-completed-banner">
            <h3>{{ $t('workbench.projectCompleted') }}</h3>
            <router-link :to="{ name: 'Process', params: { projectId } }" class="completed-link">
              {{ $t('workbench.backToGraph') }}
            </router-link>
          </div>
        </template>

        <template v-else>
          <div class="no-milestone-view">
            <p>{{ $t('workbench.noMilestones') }}</p>
            <router-link :to="{ name: 'Process', params: { projectId } }" class="nav-back-link">
              {{ $t('workbench.backToGraph') }}
            </router-link>
          </div>
        </template>
      </main>
    </div>

    <!-- Hint Panel (right drawer) -->
    <HintPanel
      :isOpen="hintPanelOpen"
      :milestoneUuid="currentMilestone ? currentMilestone.uuid : ''"
      :milestoneOrder="currentMilestone ? currentMilestone.order : 0"
      :projectId="projectId"
      :knowledgePoints="currentMilestone ? currentMilestone.knowledge_points : []"
      :activeKPUuid="selectedKP ? selectedKP.uuid : ''"
      @close="hintPanelOpen = false"
      @request-classroom="handleClassroomRequest"
    />

    <!-- Classroom generation overlay -->
    <div v-if="classroomGenerating" class="classroom-overlay">
      <div class="classroom-overlay-content">
        <div class="hint-spinner"></div>
        <p>{{ $t('process.classroomGenerating') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getMilestones, generateClassroom, getClassroomStatus, cacheClassroomId } from '../api/graph'
import { initProgress, markMilestoneComplete, addHintHistory, getMilestoneStatus, isProjectCompleted, getCompletedCount, getHintCount, getCurrentMilestoneOrder, saveMilestoneNote, getMilestoneNote } from '../store/progress'
import HintPanel from '../components/HintPanel.vue'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

// Props from route
const projectId = computed(() => route.params.projectId)
const pblNodeUuid = computed(() => route.query.pbl || '')

// State
const projectName = ref('')
const milestones = ref([])
const currentMilestone = ref(null)
const submissionText = ref('')
const markingComplete = ref(false)
const hintPanelOpen = ref(false)
const classroomGenerating = ref(false)
const selectedKP = ref(null)

// Classroom polling
let classroomPollTimer = null

const progressPercent = computed(() => {
  if (milestones.value.length === 0) return 0
  return (getCompletedCount(projectId.value) / milestones.value.length) * 100
})

// Select milestone
const selectMilestone = (ms) => {
  const status = getMilestoneStatus(projectId.value, ms.order)
  if (status === 'locked') return
  currentMilestone.value = ms
  submissionText.value = getMilestoneNote(projectId.value, ms.order)
  selectedKP.value = null
  hintPanelOpen.value = false
}

// Mark milestone complete
const markComplete = () => {
  if (!currentMilestone.value || markingComplete.value) return
  markingComplete.value = true

  markMilestoneComplete(projectId.value, currentMilestone.value.order)

  // Save note before completing
  saveMilestoneNote(projectId.value, currentMilestone.value.order, submissionText.value)

  // Move to next milestone
  const nextOrder = getCurrentMilestoneOrder(projectId.value)
  const nextMs = milestones.value.find(ms => ms.order === nextOrder)
  if (nextMs) {
    currentMilestone.value = nextMs
    submissionText.value = getMilestoneNote(projectId.value, nextMs.order)
  } else {
    // Project completed - keep current milestone
  }

  markingComplete.value = false
}

// Toggle hint panel
const toggleHintPanel = () => {
  if (!currentMilestone.value) return
  hintPanelOpen.value = !hintPanelOpen.value
}

// Open hint panel for a specific KP
const openHintForKP = (kp) => {
  if (!currentMilestone.value) return
  selectedKP.value = kp
  hintPanelOpen.value = true
}

// Save note to localStorage on input
const onNoteInput = () => {
  if (!currentMilestone.value) return
  saveMilestoneNote(projectId.value, currentMilestone.value.order, submissionText.value)
}

// Handle classroom request (L3)
const handleClassroomRequest = async (kpUuid, kpName) => {
  hintPanelOpen.value = false
  classroomGenerating.value = true

  try {
    const requestData = {
      project_id: projectId.value,
      node_uuid: kpUuid,
    }

    const res = await generateClassroom(requestData)

    if (res.data?.status === 'ready') {
      classroomGenerating.value = false
      openClassroom(res.data.classroom_id, kpName)
      return
    }

    if (res.data?.status === 'generating' && res.data?.job_id) {
      const jobId = res.data.job_id
      startClassroomPolling(jobId, kpName, kpUuid)
    }
  } catch (err) {
    console.error('Generate classroom failed:', err)
    classroomGenerating.value = false
    const msg = err.response?.data?.error || t('process.classroomError')
    alert(msg)
  }
}

const startClassroomPolling = (jobId, kpName, kpUuid) => {
  const pollInterval = 5000

  const poll = async () => {
    try {
      const statusRes = await getClassroomStatus(jobId)

      if (statusRes.data?.status === 'completed') {
        classroomGenerating.value = false

        const classroomId = statusRes.data.classroom_id

        // Cache classroom_id to Neo4j (non-blocking — don't block navigation on failure)
        cacheClassroomId({
          project_id: projectId.value,
          node_uuid: kpUuid,
          classroom_id: classroomId,
        }).catch(err => {
          console.warn('Failed to cache classroom ID:', err)
        })

        // Refresh milestones so the KP card shows "Enter Classroom" next time
        refreshMilestones()

        openClassroom(classroomId, kpName)
        return
      } else if (statusRes.data?.status === 'failed') {
        classroomGenerating.value = false
        alert(t('process.classroomFailed'))
        return
      }
      // Still processing, continue polling
      classroomPollTimer = setTimeout(poll, pollInterval)
    } catch (err) {
      console.error('Classroom status poll error:', err)
      // Transient error, continue polling
      classroomPollTimer = setTimeout(poll, pollInterval)
    }
  }

  classroomPollTimer = setTimeout(poll, pollInterval)
}

const openClassroom = (classroomId, nodeName) => {
  router.push({
    name: 'Classroom',
    params: { classroomId },
    query: {
      project_id: projectId.value,
      node_name: nodeName || '',
    }
  })
}

// Refresh milestones data (e.g. after classroom generation to get updated classroom_id)
const refreshMilestones = async () => {
  try {
    const res = await getMilestones(projectId.value, pblNodeUuid.value)
    if (res.success && res.data) {
      const newMilestones = res.data.milestones || []
      // Update milestones in-place to preserve reactivity
      milestones.value = newMilestones
      // Re-bind currentMilestone to the updated data
      if (currentMilestone.value) {
        const updated = newMilestones.find(m => m.uuid === currentMilestone.value.uuid)
        if (updated) currentMilestone.value = updated
      }
    }
  } catch (err) {
    console.warn('Failed to refresh milestones:', err)
  }
}

// Load data on mount
onMounted(async () => {
  try {
    const res = await getMilestones(projectId.value, pblNodeUuid.value)
    if (res.success && res.data) {
      projectName.value = res.data.project_name || ''
      milestones.value = res.data.milestones || []

      // Init progress
      if (milestones.value.length > 0) {
        initProgress(projectId.value, milestones.value)

        // Set current milestone from progress
        const currentOrder = getCurrentMilestoneOrder(projectId.value)
        const ms = milestones.value.find(m => m.order === currentOrder)
        if (ms) {
          currentMilestone.value = ms
          submissionText.value = getMilestoneNote(projectId.value, ms.order)
        } else {
          currentMilestone.value = milestones.value[0]
          submissionText.value = getMilestoneNote(projectId.value, milestones.value[0].order)
        }
      }
    }
  } catch (err) {
    console.error('Failed to load milestones:', err)
  }
})

onUnmounted(() => {
  if (classroomPollTimer) {
    clearInterval(classroomPollTimer)
    classroomPollTimer = null
  }
})
</script>

<style scoped>
:root {
  --black: #000000;
  --white: #FFFFFF;
  --orange: #FF4500;
  --font-mono: 'JetBrains Mono', monospace;
  --font-sans: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

.workbench-container {
  min-height: 100vh;
  background: #0a0a0a;
  color: #fff;
  font-family: var(--font-sans);
}

/* Navbar */
.workbench-navbar {
  height: 60px;
  background: #111;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid #333;
}

.navbar-brand {
  font-family: var(--font-mono);
  font-weight: 800;
  font-size: 1.1rem;
  color: var(--orange);
  letter-spacing: 1px;
}

.navbar-project-name {
  font-family: var(--font-sans);
  font-size: 1rem;
  color: #ddd;
  font-weight: 500;
}

.navbar-links {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-back-link {
  color: #666;
  text-decoration: none;
  font-family: var(--font-mono);
  font-size: 0.8rem;
  transition: color 0.2s;
}

.nav-back-link:hover {
  color: var(--orange);
}

.nav-github-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #666;
  text-decoration: none;
  font-size: 0.9rem;
  opacity: 0.8;
  transition: opacity 0.2s;
  background: rgba(0,0,0,0.05);
  padding: 5px 12px;
  border-radius: 6px;
}

.nav-github-link:hover { opacity: 1; background: rgba(0,0,0,0.08); }

/* 3-panel layout */
.workbench-layout {
  display: flex;
  min-height: calc(100vh - 60px);
}

/* Milestone sidebar */
.milestone-sidebar {
  width: 240px;
  background: #111;
  border-right: 1px solid #333;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: #666;
  letter-spacing: 2px;
  border-bottom: 1px solid #333;
}

.sidebar-empty {
  padding: 20px;
  color: #666;
  font-size: 0.85rem;
}

.milestone-list {
  list-style: none;
  padding: 0;
  margin: 0;
  flex: 1;
  overflow-y: auto;
}

.milestone-item {
  padding: 14px 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #222;
}

.milestone-item:hover:not(.milestone-item--locked) {
  background: #1a1a1a;
}

.milestone-item--locked {
  color: #555;
  cursor: not-allowed;
  opacity: 0.5;
}

.milestone-item--current {
  background: #1a1a1a;
  color: #fff;
}

.milestone-item--completed {
  color: #999;
}

.milestone-item--completed .milestone-icon {
  color: var(--orange);
}

.milestone-item--current .milestone-icon {
  color: var(--orange);
}

.milestone-icon {
  font-size: 0.8rem;
  flex-shrink: 0;
}

.milestone-name {
  font-size: 0.85rem;
  line-height: 1.3;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid #333;
}

.help-btn {
  width: 100%;
  background: transparent;
  color: var(--orange);
  border: 1px solid var(--orange);
  padding: 10px;
  font-family: var(--font-mono);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.5px;
}

.help-btn:hover {
  background: var(--orange);
  color: #fff;
}

/* Work area */
.work-area {
  flex: 1;
  padding: 40px;
  max-width: 800px;
  overflow-y: auto;
}

.milestone-title {
  font-size: 2rem;
  font-weight: 500;
  margin: 0 0 24px 0;
  color: #fff;
}

.milestone-description {
  color: #bbb;
  line-height: 1.7;
  margin-bottom: 24px;
  font-size: 0.95rem;
}

.acceptance-section {
  margin-bottom: 24px;
  border: 1px solid #333;
  padding: 16px;
}

.acceptance-label {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--orange);
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.acceptance-text {
  color: #ddd;
  line-height: 1.6;
  font-size: 0.9rem;
}

.submission-section {
  margin-bottom: 24px;
}

/* Knowledge points section */
.kp-section {
  margin-bottom: 24px;
}

.kp-label {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--orange);
  letter-spacing: 1px;
  margin-bottom: 12px;
}

.kp-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.kp-card {
  border: 1px solid #333;
  padding: 14px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.kp-card:hover {
  border-color: var(--orange);
}

.kp-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.kp-card-name {
  font-weight: 700;
  font-size: 0.9rem;
  color: #fff;
}

.kp-card-difficulty {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 2px;
  letter-spacing: 0.5px;
}

.kp-card-difficulty.diff-beginner {
  background: rgba(26, 147, 111, 0.15);
  color: #1A936F;
  border: 1px solid #1A936F;
}

.kp-card-difficulty.diff-intermediate {
  background: rgba(123, 45, 142, 0.15);
  color: #7B2D8E;
  border: 1px solid #7B2D8E;
}

.kp-card-difficulty.diff-advanced {
  background: rgba(255, 69, 0, 0.15);
  color: #FF4500;
  border: 1px solid #FF4500;
}

.kp-card-summary {
  color: #bbb;
  font-size: 0.8rem;
  line-height: 1.5;
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kp-classroom-btn {
  background: transparent;
  color: var(--orange);
  border: 1px solid var(--orange);
  padding: 6px 14px;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.5px;
}

.kp-classroom-btn:hover {
  background: var(--orange);
  color: #fff;
}

.kp-classroom-btn--ready {
  background: #1A936F;
  color: #fff;
  border-color: #1A936F;
}

.kp-classroom-btn--ready:hover {
  background: #157a5c;
  border-color: #157a5c;
}

.submission-input {
  width: 100%;
  background: #111;
  border: 1px solid #333;
  color: #ddd;
  padding: 16px;
  font-family: var(--font-mono);
  font-size: 0.85rem;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  min-height: 100px;
}

.submission-input:focus {
  border-color: #555;
}

.complete-section {
  margin-bottom: 32px;
}

.complete-btn {
  background: var(--orange);
  color: #fff;
  border: none;
  padding: 14px 32px;
  font-family: var(--font-mono);
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.5px;
}

.complete-btn:hover:not(:disabled) {
  background: #e03e00;
  transform: translateY(-1px);
}

.complete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.completed-label {
  color: var(--orange);
  font-family: var(--font-mono);
  font-size: 0.85rem;
  font-weight: 700;
}

/* Progress bar */
.progress-bar-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #333;
}

.progress-stats {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 8px;
}

.progress-bar-track {
  height: 4px;
  background: #222;
  border-radius: 2px;
}

.progress-bar-fill {
  height: 100%;
  background: var(--orange);
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* Project completed banner */
.project-completed-banner {
  margin-top: 32px;
  padding: 24px;
  border: 1px solid var(--orange);
  background: rgba(255, 69, 0, 0.05);
  text-align: center;
}

.project-completed-banner h3 {
  color: var(--orange);
  font-family: var(--font-mono);
  font-size: 1rem;
  margin: 0 0 16px 0;
  letter-spacing: 1px;
}

.completed-link {
  color: #fff;
  text-decoration: none;
  font-family: var(--font-mono);
  font-size: 0.85rem;
  border: 1px solid #555;
  padding: 10px 24px;
  transition: all 0.2s;
}

.completed-link:hover {
  border-color: var(--orange);
  color: var(--orange);
}

/* No milestone view */
.no-milestone-view {
  text-align: center;
  padding: 60px 0;
}

.no-milestone-view p {
  color: #666;
  font-size: 1rem;
  margin-bottom: 24px;
}

/* Classroom overlay */
.classroom-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.classroom-overlay-content {
  text-align: center;
}

.classroom-overlay-content p {
  font-family: var(--font-mono);
  color: #666;
  font-size: 0.85rem;
  margin-top: 20px;
}

.hint-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #333;
  border-top-color: var(--orange);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .workbench-layout {
    flex-direction: column;
  }

  .milestone-sidebar {
    width: 100%;
    max-height: 200px;
    border-right: none;
    border-bottom: 1px solid #333;
  }

  .work-area {
    padding: 24px;
  }
}
</style>
<template>
  <div class="process-page">
    <!-- 顶部导航栏 -->
    <nav class="navbar">
      <div class="nav-brand" @click="goHome">NEWGRAPH</div>
      
      <!-- 中间步骤指示器 -->
      <div class="nav-center">
        <div class="step-badge">STEP 01</div>
        <div class="step-name">{{ $t('process.stepName') }}</div>
      </div>

      <div class="nav-status">
        <router-link v-if="currentProjectId" :to="`/qa/${currentProjectId}`" class="nav-qa-link">
          问答
        </router-link>
        <a href="https://github.com/DuanHangyu" target="_blank" class="nav-github-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
        </a>
        <span class="status-dot" :class="statusClass"></span>
        <span class="status-text">{{ statusText }}</span>
      </div>
    </nav>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧: 实时图谱展示 -->
      <div class="left-panel" :class="{ 'full-screen': isFullScreen }">
        <div class="panel-header">
          <div class="header-left">
            <span class="header-deco">◆</span>
            <span class="header-title">{{ $t('process.realtimeGraphTitle') }}</span>
          </div>
          <div class="header-right">
            <template v-if="graphData">
              <span class="stat-item">{{ graphData.node_count || graphData.nodes?.length || 0 }} {{ $t('process.nodes') }}</span>
              <span class="stat-divider">|</span>
              <span class="stat-item">{{ graphData.edge_count || graphData.edges?.length || 0 }} {{ $t('process.relationships') }}</span>
              <span class="stat-divider">|</span>
            </template>
            <div class="action-buttons">
                <button v-if="hasLearningPathEdges" class="action-btn view-toggle-btn" @click="toggleViewMode" :title="viewMode === 'full' ? $t('process.learningPathView') : $t('process.fullGraphView')">
                  <span class="view-mode-icon">{{ viewMode === 'full' ? '🔀' : '🕸' }}</span>
                </button>
                <button class="action-btn" @click="refreshGraph" :disabled="graphLoading" title="刷新图谱">
                  <span class="icon-refresh" :class="{ 'spinning': graphLoading }">↻</span>
                </button>
                <button class="action-btn" @click="toggleFullScreen" :title="isFullScreen ? '退出全屏' : '全屏显示'">
                  <span class="icon-fullscreen">{{ isFullScreen ? '↙' : '↗' }}</span>
                </button>
            </div>
          </div>
        </div>
        
        <div class="graph-container" ref="graphContainer">
          <!-- 图谱可视化（SVG 始终存在） -->
          <div v-if="graphData || isBuildingGraph" class="graph-view">
            <svg ref="graphSvg" class="graph-svg"></svg>
            <!-- 构建中提示（已完成的图谱 + phase 1） -->
            <div v-if="graphData && currentPhase === 1" class="graph-building-hint">
              <span class="building-dot"></span>
              {{ $t('process.buildingHint') }}
            </div>
            <!-- 构建中覆盖层（无数据时显示加载动画） -->
            <div v-if="isBuildingGraph && liveNodeCount === 0" class="graph-build-overlay">
              <div class="loading-animation">
                <div class="loading-ring"></div>
                <div class="loading-ring"></div>
                <div class="loading-ring"></div>
              </div>
              <p class="waiting-text">{{ currentPhase === 0 ? $t('process.waitingOntologyGen') : $t('process.graphBuilding') }}</p>
              <p class="waiting-hint">{{ $t('process.dataComingSoon') }}</p>
            </div>
            <!-- 底部实时统计条（有节点后显示） -->
            <div v-if="isBuildingGraph && liveNodeCount > 0" class="graph-build-stats">
              <span class="build-stat-dot"></span>
              <span class="build-stat-text">{{ liveNodeCount }} {{ $t('process.nodes') }} · {{ liveEdgeCount }} {{ $t('process.relationships') }}</span>
              <span v-if="ontologyProgress?.message" class="build-stat-progress">{{ ontologyProgress.message }}</span>
            </div>
            
            <!-- 节点/边详情面板 -->
            <div v-if="selectedItem" class="detail-panel">
              <div class="detail-panel-header">
                <span class="detail-title">{{ selectedItem.type === 'node' ? 'Node Details' : 'Relationship' }}</span>
                <span v-if="selectedItem.type === 'node'" class="detail-badge" :style="{ background: selectedItem.color }">
                  {{ selectedItem.entityType }}
                </span>
                <button class="detail-close" @click="closeDetailPanel">×</button>
              </div>
              
              <!-- 节点详情 -->
              <div v-if="selectedItem.type === 'node'" class="detail-content">
                <div class="detail-row">
                  <span class="detail-label">Name:</span>
                  <span class="detail-value highlight">{{ selectedItem.data.name }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">UUID:</span>
                  <span class="detail-value uuid">{{ selectedItem.data.uuid }}</span>
                </div>

                <!-- Learning Path Badges -->
                <div class="detail-badges" v-if="selectedItem.data.attributes?.difficulty || selectedItem.isProject">
                  <span v-if="selectedItem.isProject" class="lp-badge badge-project">
                    {{ $t('process.projectNode') }}
                  </span>
                  <span v-else class="lp-badge badge-knowledge">
                    {{ $t('process.knowledgePoint') }}
                  </span>
                  <span v-if="selectedItem.data.attributes?.difficulty" class="lp-badge" :class="'badge-' + selectedItem.data.attributes.difficulty">
                    {{ $t('process.' + selectedItem.data.attributes.difficulty) }}
                  </span>
                  <span v-if="selectedItem.data.attributes?.learning_order" class="lp-badge badge-order">
                    #{{ selectedItem.data.attributes.learning_order }}
                  </span>
                </div>

                <div class="detail-row" v-if="selectedItem.data.created_at">
                  <span class="detail-label">Created:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.created_at) }}</span>
                </div>

                <!-- Prerequisites Summary -->
                <div class="detail-section" v-if="selectedItem.data.attributes?.prerequisites_summary">
                  <span class="detail-label">{{ $t('process.prerequisites') }}:</span>
                  <p class="detail-summary learning-path-info">{{ selectedItem.data.attributes.prerequisites_summary }}</p>
                </div>

                <!-- Outcomes Summary -->
                <div class="detail-section" v-if="selectedItem.data.attributes?.outcomes_summary">
                  <span class="detail-label">{{ $t('process.outcomes') }}:</span>
                  <p class="detail-summary learning-path-info outcomes-info">{{ selectedItem.data.attributes.outcomes_summary }}</p>
                </div>

                <!-- Branch info for main path nodes -->
                <div class="detail-section" v-if="selectedItem.branchInfo">
                  <span class="detail-label">{{ $t('process.branchesFromHere') }}:</span>
                  <div class="branch-names">
                    <span v-for="name in selectedItem.branchInfo" :key="name" class="branch-name-tag">{{ name }}</span>
                  </div>
                </div>

                <!-- Merge info for branch nodes -->
                <div class="detail-section" v-if="selectedItem.mergeInfo">
                  <span class="detail-label">{{ $t('process.mergesBackAt') }}:</span>
                  <span class="detail-value">{{ selectedItem.mergeInfo }}</span>
                </div>

                <!-- Required by info for knowledge points (PBL mode) -->
                <div class="detail-section" v-if="selectedItem.data.attributes?.required_by">
                  <span class="detail-label">{{ $t('process.requiredBy') }}:</span>
                  <div class="branch-names">
                    <span v-for="name in selectedItem.data.attributes.required_by.split(', ')" :key="name" class="project-name-tag">{{ name }}</span>
                  </div>
                </div>

                <!-- Properties / Attributes -->
                <div class="detail-section" v-if="selectedItem.data.attributes && Object.keys(selectedItem.data.attributes).length > 0">
                  <span class="detail-label">Properties:</span>
                  <div class="properties-list">
                    <div v-for="(value, key) in selectedItem.data.attributes" :key="key" class="property-item">
                      <span class="property-key">{{ key }}:</span>
                      <span class="property-value">{{ value }}</span>
                    </div>
                  </div>
                </div>

                <!-- Summary -->
                <div class="detail-section" v-if="selectedItem.data.summary">
                  <span class="detail-label">Summary:</span>
                  <p class="detail-summary">{{ selectedItem.data.summary }}</p>
                </div>

                <!-- Virtual Classroom Action (Knowledge Point nodes) -->
                <div class="classroom-action" v-if="isKnowledgePoint">
                  <button
                    v-if="selectedItem.data.attributes?.classroom_id"
                    class="classroom-btn classroom-btn-ready"
                    @click="openClassroom(selectedItem.data.attributes.classroom_id)"
                  >
                    {{ $t('process.enterClassroom') }}
                  </button>
                  <template v-else-if="!classroomGenerating">
                    <div class="classroom-mode-selector">
                      <select v-model="classroomMode" class="classroom-mode-select">
                        <option value="classroom">{{ $t('process.classroomMode') }}</option>
                        <option value="podcast">{{ $t('process.podcastMode') }}</option>
                      </select>
                      <select
                        v-if="classroomMode === 'podcast'"
                        v-model="podcastSpeakerPair"
                        class="podcast-speaker-select"
                      >
                        <option value="mizai-dayi">{{ $t('process.speakerMizaiDayi') }}</option>
                        <option value="liufei-xiaolei">{{ $t('process.speakerLiufeiXiaolei') }}</option>
                      </select>
                    </div>
                    <button
                      class="classroom-btn classroom-btn-generate"
                      @click="generateClassroomForNode"
                    >
                      {{ classroomMode === 'podcast' ? $t('process.generatePodcast') : $t('process.generateClassroom') }}
                    </button>
                  </template>
                  <div v-else class="classroom-generating">
                    <div class="classroom-spinner"></div>
                    <span class="classroom-progress-text">
                      {{ $t('process.classroomGenerating') }}
                      <span v-if="classroomGenerationProgress > 0">{{ classroomGenerationProgress }}%</span>
                    </span>
                  </div>
                </div>

                <!-- PBL Learning Action (Project nodes) -->
                <div class="pbl-action" v-if="selectedItem.isProject">
                  <button
                    class="pbl-btn"
                    @click="enterWorkbench"
                  >
                    {{ $t('process.enterPBL') }}
                  </button>
                </div>

                <!-- Labels -->
                <div class="detail-row" v-if="selectedItem.data.labels?.length">
                  <span class="detail-label">Labels:</span>
                  <div class="detail-labels">
                    <span v-for="label in selectedItem.data.labels" :key="label" class="label-tag">{{ label }}</span>
                  </div>
                </div>
              </div>
              
              <!-- 边详情 -->
              <div v-else class="detail-content">
                <!-- 关系展示 -->
                <div class="edge-relation">
                  <span class="edge-source">{{ selectedItem.data.source_name || selectedItem.data.source_node_name }}</span>
                  <span class="edge-arrow">→</span>
                  <span class="edge-type" :style="getEdgeTypeStyle(selectedItem.data.fact_type)">{{ selectedItem.data.name || selectedItem.data.fact_type || 'RELATED_TO' }}</span>
                  <span class="edge-arrow">→</span>
                  <span class="edge-target">{{ selectedItem.data.target_name || selectedItem.data.target_node_name }}</span>
                </div>
                
                <div class="detail-subtitle">Relationship</div>
                
                <div class="detail-row">
                  <span class="detail-label">UUID:</span>
                  <span class="detail-value uuid">{{ selectedItem.data.uuid }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Label:</span>
                  <span class="detail-value">{{ selectedItem.data.name || selectedItem.data.fact_type || 'RELATED_TO' }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.fact_type">
                  <span class="detail-label">Type:</span>
                  <span class="detail-value">{{ selectedItem.data.fact_type }}</span>
                </div>
                
                <!-- Fact -->
                <div class="detail-section" v-if="selectedItem.data.fact">
                  <span class="detail-label">Fact:</span>
                  <p class="detail-summary">{{ selectedItem.data.fact }}</p>
                </div>
                
                <!-- Episodes -->
                <div class="detail-section" v-if="selectedItem.data.episodes?.length">
                  <span class="detail-label">Episodes:</span>
                  <div class="episodes-list">
                    <span v-for="ep in selectedItem.data.episodes" :key="ep" class="episode-tag">{{ ep }}</span>
                  </div>
                </div>
                
                <div class="detail-row" v-if="selectedItem.data.created_at">
                  <span class="detail-label">Created:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.created_at) }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.valid_at">
                  <span class="detail-label">Valid From:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.valid_at) }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.invalid_at">
                  <span class="detail-label">Invalid At:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.invalid_at) }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.expired_at">
                  <span class="detail-label">Expired At:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.expired_at) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 加载状态 -->
          <div v-else-if="graphLoading" class="graph-loading">
            <div class="loading-animation">
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
            </div>
            <p class="loading-text">{{ $t('process.loadingGraphData') }}</p>
          </div>

          <!-- 错误状态 -->
          <div v-else-if="error" class="graph-error">
            <span class="error-icon">⚠</span>
            <p>{{ error }}</p>
          </div>
        </div>
        
        <!-- 图谱图例 -->
        <div v-if="graphData" class="graph-legend">
          <div class="legend-item" v-for="type in entityTypes" :key="type.name">
            <span class="legend-dot" :style="{ background: type.color }"></span>
            <span class="legend-label">{{ type.name }}</span>
            <span class="legend-count">{{ type.count }}</span>
          </div>
          <!-- Edge type legend for learning path edges (simplified: 3 types) -->
          <template v-if="hasLearningPathEdges">
            <span class="legend-divider">|</span>
            <div class="legend-item">
              <span class="legend-line" style="background: #2D3436; height: 3px"></span>
              <span class="legend-label">{{ $t('process.legendNextStep') }}</span>
            </div>
            <div class="legend-item">
              <span class="legend-line" style="background: #7B2D8E"></span>
              <span class="legend-label">{{ $t('process.legendRequires') }}</span>
            </div>
            <div class="legend-item">
              <span class="legend-line" style="background: #FF6B35"></span>
              <span class="legend-label">{{ $t('process.legendPrerequisite') }}</span>
            </div>
          </template>
        </div>
      </div>

      <!-- 右侧: 构建流程详情 -->
      <div class="right-panel" :class="{ 'hidden': isFullScreen }">
        <div class="panel-header dark-header">
          <span class="header-icon">▣</span>
          <span class="header-title">构建流程</span>
        </div>

        <div class="process-content">
          <!-- 阶段1: 图谱提取 -->
          <div class="process-phase" :class="{ 'active': currentPhase === 0, 'completed': currentPhase > 0 }">
            <div class="phase-header">
              <span class="phase-num">01</span>
              <div class="phase-info">
                <div class="phase-title">{{ $t('process.phase01Title') }}</div>
                <div class="phase-api">/api/graph/extract</div>
              </div>
              <span class="phase-status" :class="getPhaseStatusClass(0)">
                {{ getPhaseStatusText(0) }}
              </span>
            </div>

            <div class="phase-detail">
              <div class="detail-section">
                <div class="detail-label">接口说明</div>
                <div class="detail-content">
                  LLM 分析文档内容，直接提取图谱的节点和边
                </div>
              </div>

              <!-- 提取进度 -->
              <div class="detail-section" v-if="ontologyProgress && currentPhase === 0">
                <div class="detail-label">提取进度</div>
                <div class="ontology-progress">
                  <div class="progress-spinner"></div>
                  <span class="progress-text">{{ ontologyProgress.message }}</span>
                </div>
              </div>

              <!-- 已提取的图谱信息 -->
              <div class="detail-section" v-if="projectData?.node_count > 0">
                <div class="detail-label">提取结果</div>
                <div class="build-result">
                  <div class="result-item">
                    <span class="result-value">{{ projectData.node_count }}</span>
                    <span class="result-label">{{ $t('process.entityNodes') }}</span>
                  </div>
                  <div class="result-item">
                    <span class="result-value">{{ projectData.edge_count }}</span>
                    <span class="result-label">{{ $t('process.relationEdges') }}</span>
                  </div>
                  <div class="result-item">
                    <span class="result-value">{{ entityTypes.length }}</span>
                    <span class="result-label">{{ $t('process.entityTypesCount') }}</span>
                  </div>
                </div>
              </div>

              <!-- 等待状态 -->
              <div class="detail-section waiting-state" v-if="!projectData?.node_count && currentPhase === 0 && !ontologyProgress">
                <div class="waiting-hint">{{ $t('process.waitingOntologyGenShort') }}</div>
              </div>
            </div>
          </div>

          <!-- 阶段2: 图谱存储 -->
          <div class="process-phase" :class="{ 'active': currentPhase === 1, 'completed': currentPhase > 1 }">
            <div class="phase-header">
              <span class="phase-num">02</span>
              <div class="phase-info">
                <div class="phase-title">{{ $t('process.phase02Title') }}</div>
                <div class="phase-api">/api/graph/store</div>
              </div>
              <span class="phase-status" :class="getPhaseStatusClass(1)">
                {{ getPhaseStatusText(1) }}
              </span>
            </div>

            <div class="phase-detail">
              <div class="detail-section">
                <div class="detail-label">接口说明</div>
                <div class="detail-content">
                  将提取的图谱数据存储到 Neo4j
                </div>
              </div>

              <!-- 等待图谱完成 -->
              <div class="detail-section waiting-state" v-if="currentPhase < 1">
                <div class="waiting-hint">等待图谱提取完成...</div>
              </div>

              <!-- 存储进度 -->
              <div class="detail-section" v-if="buildProgress && currentPhase >= 1">
                <div class="detail-label">{{ $t('process.buildProgress') }}</div>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: buildProgress.progress + '%' }"></div>
                </div>
                <div class="progress-info">
                  <span class="progress-message">{{ buildProgress.message }}</span>
                  <span class="progress-percent">{{ buildProgress.progress }}%</span>
                </div>
              </div>

              <div class="detail-section" v-if="graphData">
                <div class="detail-label">{{ $t('process.buildResult') }}</div>
                <div class="build-result">
                  <div class="result-item">
                    <span class="result-value">{{ graphData.node_count }}</span>
                    <span class="result-label">{{ $t('process.entityNodes') }}</span>
                  </div>
                  <div class="result-item">
                    <span class="result-value">{{ graphData.edge_count }}</span>
                    <span class="result-label">{{ $t('process.relationEdges') }}</span>
                  </div>
                  <div class="result-item">
                    <span class="result-value">{{ entityTypes.length }}</span>
                    <span class="result-label">{{ $t('process.entityTypesCount') }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 阶段3: 完成 -->
          <div class="process-phase" :class="{ 'active': currentPhase === 2, 'completed': currentPhase > 2 }">
            <div class="phase-header">
              <span class="phase-num">03</span>
              <div class="phase-info">
                <div class="phase-title">{{ $t('process.phase03Title') }}</div>
                <div class="phase-api">{{ $t('process.phase03Api') }}</div>
              </div>
              <span class="phase-status" :class="getPhaseStatusClass(2)">
                {{ getPhaseStatusText(2) }}
              </span>
            </div>
          </div>

          <!-- 下一步按钮 -->
          <div class="next-step-section" v-if="currentPhase >= 2">
            <button class="next-step-btn" @click="goToNextStep" :disabled="currentPhase < 2">
              {{ $t('process.enterNextStep') }}
              <span class="btn-arrow">→</span>
            </button>
          </div>
        </div>

        <!-- 学习路径面板 -->
        <div class="learning-path-panel" v-if="currentPhase >= 2 && learningPathData">
          <div class="project-header">
            <span class="project-icon">◈</span>
            <span class="project-title">{{ $t('process.learningPath') }}</span>
          </div>
          <div class="learning-path-content">
            <!-- PBL 模式 -->
            <template v-if="learningPathData.mode === 'pbl'">
              <!-- 项目主路径 -->
              <div class="path-section" v-if="learningPathData.main_path?.length">
                <div class="path-section-title">{{ $t('process.projectSequence') }}</div>
                <div class="path-list">
                  <div
                    v-for="(uuid, idx) in learningPathData.main_path"
                    :key="uuid"
                    class="path-item main-path-item"
                    @click="focusNode(uuid)"
                  >
                    <span class="path-order">{{ idx + 1 }}</span>
                    <span class="path-name">{{ getNodeName(uuid) }}</span>
                    <span v-if="getNodeDifficulty(uuid)" class="path-difficulty" :class="'diff-' + getNodeDifficulty(uuid)">{{ getNodeDifficulty(uuid)?.charAt(0).toUpperCase() }}</span>
                  </div>
                </div>
              </div>
              <!-- 每个项目的知识环形链 -->
              <div class="path-section" v-if="learningPathData.project_knowledge_subgraphs">
                <div class="path-section-title">{{ $t('process.projectKnowledge') }}</div>
                <div class="branch-list">
                  <details
                    v-for="(subgraph, projUuid) in learningPathData.project_knowledge_subgraphs"
                    :key="projUuid"
                    class="branch-details"
                  >
                    <summary class="branch-summary">
                      <span class="branch-arrow">▸</span>
                      {{ getNodeName(projUuid) }}
                      <span class="kp-count">({{ subgraph.knowledge_chain?.length || 0 }} KP)</span>
                      <span v-if="subgraph.ring_closed" class="ring-badge">⟳</span>
                    </summary>
                    <div class="branch-info">
                      <div
                        v-for="(kpUuid, kpIdx) in subgraph.knowledge_chain"
                        :key="kpUuid"
                        class="path-item branch-path-item"
                        @click="focusNode(kpUuid)"
                      >
                        <span class="path-order branch-order">K{{ kpIdx + 1 }}</span>
                        <span class="path-name">{{ getNodeName(kpUuid) }}</span>
                      </div>
                      <div v-if="subgraph.ring_closed" class="ring-closure">
                        ↳ {{ $t('process.ringBackTo') }} {{ getNodeName(projUuid) }}
                      </div>
                    </div>
                  </details>
                </div>
              </div>
            </template>
            <!-- 知识驱动模式（向后兼容） -->
            <template v-else>
              <!-- 主路径 -->
              <div class="path-section" v-if="learningPathData.main_path?.length">
                <div class="path-section-title">{{ $t('process.mainPath') }}</div>
                <div class="path-list">
                  <div
                    v-for="(uuid, idx) in learningPathData.main_path"
                    :key="uuid"
                    class="path-item main-path-item"
                    @click="focusNode(uuid)"
                  >
                    <span class="path-order">{{ idx + 1 }}</span>
                    <span class="path-name">{{ getNodeName(uuid) }}</span>
                    <span v-if="getNodeDifficulty(uuid)" class="path-difficulty" :class="'diff-' + getNodeDifficulty(uuid)">{{ getNodeDifficulty(uuid)?.charAt(0).toUpperCase() }}</span>
                  </div>
                </div>
              </div>
              <!-- 分支路径 -->
              <div class="path-section" v-if="learningPathData.branch_paths?.length">
                <div class="path-section-title">{{ $t('process.branchPaths') }}</div>
                <div class="branch-list">
                  <details v-for="(branch, idx) in learningPathData.branch_paths" :key="branch.branch_id" class="branch-details">
                    <summary class="branch-summary">
                      <span class="branch-arrow">▸</span>
                      {{ $t('process.branch') }} {{ idx + 1 }}: {{ getNodeName(branch.branch_nodes?.[0]) }}
                    </summary>
                    <div class="branch-info">
                      <div class="branch-from">{{ $t('process.from') }}: {{ getNodeName(branch.from_node_uuid) }}</div>
                      <div
                        v-for="(uuid, bIdx) in branch.branch_nodes"
                        :key="uuid"
                        class="path-item branch-path-item"
                        @click="focusNode(uuid)"
                      >
                        <span class="path-order branch-order">B{{ bIdx + 1 }}</span>
                        <span class="path-name">{{ getNodeName(uuid) }}</span>
                      </div>
                      <div v-if="branch.merge_to_uuid" class="branch-merge">
                        ↳ {{ $t('process.mergesTo') }}: {{ getNodeName(branch.merge_to_uuid) }}
                      </div>
                    </div>
                  </details>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 项目信息面板 -->
        <div class="project-panel">
          <div class="project-header">
            <span class="project-icon">◇</span>
            <span class="project-title">{{ $t('process.projectInfo') }}</span>
          </div>
          <div class="project-details" v-if="projectData">
            <div class="project-item">
              <span class="item-label">{{ $t('process.projectName') }}</span>
              <span class="item-value">{{ projectData.name }}</span>
            </div>
            <div class="project-item">
              <span class="item-label">{{ $t('process.projectId') }}</span>
              <span class="item-value code">{{ projectData.project_id }}</span>
            </div>
            <!-- Note: graph_id is now the same as project_id, so we don't display it separately -->
            <div class="project-item">
              <span class="item-label">{{ $t('process.courseDesc') }}</span>
              <span class="item-value">{{ projectData.course_description || '-' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { extractGraph, getProject, storeGraph, getGraphData, getGraphitiData, getIngestStatus, getLearningPath, generateClassroom, getClassroomStatus, cacheClassroomId } from '../api/graph'
import { getPendingUpload, clearPendingUpload } from '../store/pendingUpload'
import * as d3 from 'd3'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// 当前项目ID（可能从'new'变为实际ID）
const currentProjectId = ref(route.params.projectId)

// 状态
const loading = ref(true)
const graphLoading = ref(false)
const error = ref('')
const projectData = ref(null)
const graphData = ref(null)
const buildProgress = ref(null)
const ontologyProgress = ref(null) // 本体生成进度
const currentPhase = ref(-1) // -1: 上传中, 0: 图谱提取, 1: 图谱存储, 2: 完成
const selectedItem = ref(null) // 选中的节点或边
const isFullScreen = ref(false)
const viewMode = ref('full') // 'full' or 'learning-path'
const learningPathData = ref(null) // 学习路径结构数据
const classroomGenerating = ref(false) // 课堂生成中
const classroomGenerationProgress = ref(0) // 课堂生成进度
const classroomPollTimer = ref(null) // 课堂轮询定时器
const classroomMode = ref('classroom') // 'classroom' 或 'podcast'
const podcastSpeakerPair = ref('mizai-dayi') // 播客声音配对
const liveSimulation = ref(null) // D3 simulation ref for incremental updates
const liveNodeCount = ref(0) // 实时节点计数
const liveEdgeCount = ref(0) // 实时边计数
let isIncrementalUpdate = false // 防止 watch 在增量更新时触发全量渲染

// sessionStorage 持久化：防止 HMR/刷新丢失课堂生成状态
const CLASSROOM_JOB_KEY = 'evolith_classroom_job'
const DEFAULT_CLASSROOM_POLL_INTERVAL = 2000

const saveClassroomJob = (jobId, projectId, nodeUuid, pollIntervalMs) => {
  sessionStorage.setItem(CLASSROOM_JOB_KEY, JSON.stringify({
    job_id: jobId,
    project_id: projectId,
    node_uuid: nodeUuid,
    poll_interval_ms: pollIntervalMs
  }))
}

const loadClassroomJob = () => {
  try {
    const data = sessionStorage.getItem(CLASSROOM_JOB_KEY)
    return data ? JSON.parse(data) : null
  } catch {
    clearClassroomJob()
    return null
  }
}

const clearClassroomJob = () => {
  sessionStorage.removeItem(CLASSROOM_JOB_KEY)
}

// DOM引用
const graphContainer = ref(null)
const graphSvg = ref(null)

// Note: pollTimer removed as task polling is no longer needed

// 计算属性
const statusClass = computed(() => {
  if (error.value) return 'error'
  if (currentPhase.value >= 2) return 'completed'
  return 'processing'
})

const statusText = computed(() => {
  if (error.value) return t('process.buildFailed')
  if (currentPhase.value >= 2) return t('process.buildCompleted')
  if (currentPhase.value === 1) return t('process.graphBuildingStatus')
  if (currentPhase.value === 0) return t('process.ontologyGenerating')
  return t('process.initializing')
})

const entityTypes = computed(() => {
  if (!graphData.value?.nodes) return []

  const typeMap = {}
  graphData.value.nodes.forEach(node => {
    const type = getNodeTypeFromLabels(node.labels)
    if (!typeMap[type]) {
      typeMap[type] = { name: type, count: 0, color: getNodeColor(type) }
    }
    typeMap[type].count++
  })

  return Object.values(typeMap)
})

// Check if graph has learning path edges (3 core types + old types for backward compat)
const hasLearningPathEdges = computed(() => {
  if (!graphData.value?.edges) return false
  const learningEdgeTypes = ['PREREQUISITE_OF', 'NEXT_STEP', 'REQUIRES', 'BRANCHES_FROM', 'MERGES_TO', 'ENABLES', 'BUILDS_ON', 'PARALLEL_WITH']
  return graphData.value.edges.some(e => learningEdgeTypes.includes(e.fact_type))
})

// Check if selected item is a KnowledgePoint node
const isKnowledgePoint = computed(() => {
  if (!selectedItem.value?.data?.labels) return false
  return selectedItem.value.data.labels.includes('KnowledgePoint')
})

// 是否处于图谱构建中状态（数据集导入或 Graphiti 处理阶段）
const isBuildingGraph = computed(() => {
  // 上传中/提取中（currentPhase <= 0）或图谱存储中（currentPhase=1 且还没有 graphData）
  return currentPhase.value <= 0 || (currentPhase.value === 1 && !graphData.value)
})

// 共享的 Graphiti 类型颜色映射和辅助函数
const GRAPHITI_TYPE_COLORS = {
  Technology: '#004E89', Researcher: '#FF6B35', Organization: '#7B2D8E',
  Concept: '#1A936F', Application: '#C5283D', Project: '#004E89',
  KnowledgePoint: '#FF6B35', Entity: '#999',
}
const GRAPHITI_TYPES = ['Technology', 'Researcher', 'Organization', 'Concept', 'Application']

const getNodeTypeFromLabels = (labels) => {
  if (!labels) return 'Entity'
  for (const t of GRAPHITI_TYPES) { if (labels.includes(t)) return t }
  if (labels.includes('Project')) return 'Project'
  if (labels.includes('KnowledgePoint')) return 'KnowledgePoint'
  return 'Entity'
}

const getNodeRadiusByData = (node) => {
  const isProject = node.labels?.includes('Project')
  if (isProject) {
    const d = node.attributes?.difficulty
    if (d === 'beginner') return 16
    if (d === 'advanced') return 24
    if (d === 'intermediate') return 20
    return 18
  }
  const d = node.attributes?.difficulty
  if (d === 'beginner') return 8
  if (d === 'advanced') return 14
  if (d === 'intermediate') return 11
  return 10
}

const getNodeColor = (type) => GRAPHITI_TYPE_COLORS[type] || '#999'

// 方法
const goHome = () => {
  router.push('/')
}

const goToNextStep = () => {
  // TODO: 进入环境搭建步骤
  alert(t('common.pending') + '...')
}

const toggleFullScreen = () => {
  isFullScreen.value = !isFullScreen.value
  // Wait for transition to finish then re-render graph
  setTimeout(() => {
    renderGraph()
  }, 350) 
}

// 关闭详情面板
const closeDetailPanel = () => {
  selectedItem.value = null
}

// 切换视图模式
const toggleViewMode = () => {
  viewMode.value = viewMode.value === 'full' ? 'learning-path' : 'full'
  renderGraph()
}

// 获取边类型的样式（用于详情面板）
const getEdgeTypeStyle = (factType) => {
  const edgeColors = {
    'NEXT_STEP': { background: '#2D3436', color: '#fff' },
    'REQUIRES': { background: '#7B2D8E', color: '#fff' },
    'PREREQUISITE_OF': { background: '#FF6B35', color: '#fff' },
    // Old types mapped to closest new type color for backward compat
    'BRANCHES_FROM': { background: '#7B2D8E', color: '#fff' },
    'MERGES_TO': { background: '#2D3436', color: '#fff' },
    'BUILDS_ON': { background: '#2D3436', color: '#fff' },
    'ENABLES': { background: '#7B2D8E', color: '#fff' },
    'PARALLEL_WITH': { background: '#999', color: '#fff' }
  }
  return edgeColors[factType] || { background: '#ccc', color: '#fff' }
}

// 虚拟课堂轮询逻辑（提取为独立函数，供生成和恢复共用）
const MAX_POLL_RETRIES = 3
let pollRetryCount = 0
const startClassroomPolling = (jobId, projectId, nodeUuid, pollIntervalMs) => {
  pollRetryCount = 0
  const poll = async () => {
    try {
      const statusRes = await getClassroomStatus(jobId)
      pollRetryCount = 0  // successful poll resets retry counter
      const status = statusRes.data?.status

      if (status === 'completed') {
        const classroomId = statusRes.data.classroom_id
        // 缓存 classroom_id 到 Neo4j
        await cacheClassroomId({
          project_id: projectId,
          node_uuid: nodeUuid,
          classroom_id: classroomId
        })
        // 更新本地 selectedItem 和 graphData
        if (selectedItem.value?.data?.uuid === nodeUuid && selectedItem.value?.data?.attributes) {
          selectedItem.value.data.attributes.classroom_id = classroomId
        }
        if (graphData.value?.nodes) {
          const node = graphData.value.nodes.find(n => n.uuid === nodeUuid)
          if (node?.attributes) {
            node.attributes.classroom_id = classroomId
          }
        }
        clearClassroomJob()
        classroomPollTimer.value = null
        classroomGenerating.value = false
        classroomGenerationProgress.value = 100
        openClassroom(classroomId)
      } else if (status === 'failed') {
        clearClassroomJob()
        classroomPollTimer.value = null
        classroomGenerating.value = false
        classroomGenerationProgress.value = 0
        alert(t('process.classroomFailed') + ': ' + (statusRes.data?.error || ''))
      } else {
        // processing
        const progress = statusRes.data?.progress || 0
        classroomGenerationProgress.value = progress
        classroomPollTimer.value = setTimeout(poll, pollIntervalMs)
      }
    } catch (err) {
      console.error('Classroom poll failed:', err)
      pollRetryCount++
      if (pollRetryCount <= MAX_POLL_RETRIES) {
        console.warn(`Poll retry ${pollRetryCount}/${MAX_POLL_RETRIES}`)
        classroomPollTimer.value = setTimeout(poll, pollIntervalMs)
      } else {
        clearClassroomJob()
        classroomPollTimer.value = null
        classroomGenerating.value = false
        classroomGenerationProgress.value = 0
        alert(t('process.classroomError'))
      }
    }
  }

  classroomPollTimer.value = setTimeout(poll, pollIntervalMs)
}

// 恢复因 HMR/刷新中断的课堂生成轮询
const resumeClassroomGenerationIfPending = () => {
  const job = loadClassroomJob()
  if (!job) return

  // 只恢复当前项目的任务（用户可能切换了项目）
  if (job.project_id !== currentProjectId.value) {
    clearClassroomJob()
    return
  }

  classroomGenerating.value = true
  classroomGenerationProgress.value = 0
  startClassroomPolling(job.job_id, job.project_id, job.node_uuid, job.poll_interval_ms || DEFAULT_CLASSROOM_POLL_INTERVAL)
}

// 虚拟课堂相关方法
const generateClassroomForNode = async () => {
  if (!selectedItem.value?.data?.uuid || !currentProjectId.value) return

  classroomGenerating.value = true
  classroomGenerationProgress.value = 0

  try {
    const requestData = {
      project_id: currentProjectId.value,
      node_uuid: selectedItem.value.data.uuid,
      podcast_mode: classroomMode.value === 'podcast' ? 'podcast' : null,
    }
    if (classroomMode.value === 'podcast') {
      requestData.podcast_speaker_pair = podcastSpeakerPair.value
    }

    const res = await generateClassroom(requestData)

    if (res.data?.status === 'ready') {
      // 已有课堂，直接跳转（清除可能残留的旧任务）
      clearClassroomJob()
      classroomGenerating.value = false
      openClassroom(res.data.classroom_id)
      return
    }

    if (res.data?.status === 'generating' && res.data?.job_id) {
      const jobId = res.data.job_id
      const pollInterval = res.data.poll_interval_ms || DEFAULT_CLASSROOM_POLL_INTERVAL

      // 保存到 sessionStorage，防止 HMR/刷新丢失
      saveClassroomJob(jobId, currentProjectId.value, selectedItem.value.data.uuid, pollInterval)
      startClassroomPolling(jobId, currentProjectId.value, selectedItem.value.data.uuid, pollInterval)
    }
  } catch (err) {
    console.error('Generate classroom failed:', err)
    clearClassroomJob()
    classroomGenerating.value = false
    classroomGenerationProgress.value = 0
    const msg = err.response?.data?.error || t('process.classroomError')
    alert(msg)
  }
}

const openClassroom = (classroomId) => {
  const nodeName = selectedItem.value?.data?.name || ''
  router.push({
    name: 'Classroom',
    params: { classroomId },
    query: {
      project_id: currentProjectId.value,
      node_name: nodeName
    }
  })
}

// 进入 PBL 学习工作台（Project 节点）
const enterWorkbench = () => {
  if (!currentProjectId.value) return
  const projectNodeUuid = selectedItem.value?.data?.uuid || ''
  router.push({
    name: 'Workbench',
    params: { projectId: currentProjectId.value },
    query: projectNodeUuid ? { pbl: projectNodeUuid } : {}
  })
}

// 获取节点名称
const getNodeName = (uuid) => {
  if (!uuid || !graphData.value?.nodes) return '?'
  const node = graphData.value.nodes.find(n => n.uuid === uuid)
  return node?.name || '?'
}

// 获取节点难度
const getNodeDifficulty = (uuid) => {
  if (!uuid || !graphData.value?.nodes) return null
  const node = graphData.value.nodes.find(n => n.uuid === uuid)
  return node?.attributes?.difficulty || null
}

// 聚焦节点
const focusNode = (uuid) => {
  if (!graphData.value?.nodes) return
  const node = graphData.value.nodes.find(n => n.uuid === uuid)
  if (node) {
    const isProject = node.labels?.includes('Project')
    const type = isProject ? 'Project' : 'KnowledgePoint'
    selectNode(node, entityTypes.value.find(t => t.name === type)?.color || '#999')
  }
}

// 加载学习路径数据
const loadLearningPathData = async () => {
  if (!currentProjectId.value) return
  try {
    const response = await getLearningPath(currentProjectId.value)
    if (response.success) {
      learningPathData.value = response.data
    }
  } catch (err) {
    console.debug('Learning path data not available:', err.message)
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

// 选中节点
const selectNode = (nodeData, color) => {
  // 查找分支/合并信息
  let branchInfo = null
  let mergeInfo = null

  if (learningPathData.value && nodeData.attributes?.path_type === 'main') {
    // 找从此节点分支出去的分支路径
    const branches = learningPathData.value.branch_paths?.filter(
      bp => bp.from_node_uuid === nodeData.uuid
    )
    if (branches?.length) {
      branchInfo = branches.map(bp => getNodeName(bp.branch_nodes?.[0]))
    }
  }

  if (learningPathData.value && nodeData.attributes?.path_type === 'branch') {
    // 找此分支节点汇回的主路径节点
    const branch = learningPathData.value.branch_paths?.find(
      bp => bp.branch_nodes?.includes(nodeData.uuid) && bp.merge_to_uuid
    )
    if (branch) {
      mergeInfo = getNodeName(branch.merge_to_uuid)
    }
  }

  selectedItem.value = {
    type: 'node',
    data: nodeData,
    color: color,
    entityType: nodeData.labels?.includes('Project') ? 'Project' : 'KnowledgePoint',
    isProject: nodeData.labels?.includes('Project') || false,
    branchInfo: branchInfo,
    mergeInfo: mergeInfo
  }
}

// 选中边
const selectEdge = (edgeData) => {
  selectedItem.value = {
    type: 'edge',
    data: edgeData
  }
}

const getPhaseStatusClass = (phase) => {
  if (currentPhase.value > phase) return 'completed'
  if (currentPhase.value === phase) return 'active'
  return 'pending'
}

const getPhaseStatusText = (phase) => {
  if (currentPhase.value > phase) return '已完成'
  if (currentPhase.value === phase) {
    if (phase === 1 && buildProgress.value) {
      return `${buildProgress.value.progress}%`
    }
    return '进行中'
  }
  return '等待中'
}

// 初始化 - 处理新建项目或加载已有项目
const initProject = async () => {
  const paramProjectId = route.params.projectId
  
  if (paramProjectId === 'new') {
    // 新建项目：从 store 获取待上传的数据
    await handleNewProject()
  } else {
    // 加载已有项目
    currentProjectId.value = paramProjectId
    await loadProject()
  }
}

// 处理新建项目 - 调用 extract API
const handleNewProject = async () => {
  const pending = getPendingUpload()

  if (!pending.isPending) {
    error.value = '没有待上传的数据，请返回首页重新操作'
    loading.value = false
    return
  }

  try {
    loading.value = true
    currentPhase.value = 0 // 图谱提取阶段
    ontologyProgress.value = { message: '正在上传文件并分析文档...' }

    // 构建 FormData（文件可选）
    const formDataObj = new FormData()
    if (pending.files && pending.files.length > 0) {
      pending.files.forEach(file => {
        formDataObj.append('files', file)
      })
    }
    formDataObj.append('course_description', pending.courseDescription)

    // 调用图谱提取 API
    const response = await extractGraph(formDataObj)

    if (response.success) {
      // 清除待上传数据
      clearPendingUpload()

      // 更新项目ID和数据
      currentProjectId.value = response.data.project_id
      projectData.value = response.data

      // 更新URL（不刷新页面）
      router.replace({
        name: 'Process',
        params: { projectId: response.data.project_id }
      })

      ontologyProgress.value = null

      // 自动开始图谱存储
      await startStoreGraph()
    } else {
      error.value = response.error || '图谱提取失败'
    }
  } catch (err) {
    console.error('Handle new project error:', err)
    error.value = t('api.configError', { details: (err.message || t('common.unknownError')) })
  } finally {
    loading.value = false
  }
}

// 加载已有项目数据
const loadProject = async () => {
  try {
    loading.value = true
    const response = await getProject(currentProjectId.value)

    if (response.success) {
      projectData.value = response.data
      updatePhaseByStatus(response.data.status)

      // 自动开始图谱存储
      if (response.data.status === 'graph_extracted' && !response.data.graph_data) {
        await startStoreGraph()
      }

      // 数据集导入中 — 轮询等待完成
      if (response.data.status === 'created') {
        ontologyProgress.value = { message: '正在导入数据集并构建知识图谱...' }
        currentPhase.value = 0
        pollIngestStatus()
        return
      }

      // 加载已完成的图谱 - 优先从 Neo4j 获取，失败则从 project.graph_data 获取
      if (response.data.status === 'graph_completed') {
        currentPhase.value = 2

        // 加载学习路径数据
        loadLearningPathData()

        // 如果项目有 graph_data 且有节点，先保存作为备份
        const backupGraphData = response.data.graph_data

        // 尝试从 Neo4j 获取
        await fetchGraphData()

        // 如果 Neo4j 获取失败（没有数据），且项目有 graph_data，使用它
        if (!graphData.value || !graphData.value.nodes || graphData.value.nodes.length === 0) {
          if (backupGraphData && backupGraphData.nodes && backupGraphData.nodes.length > 0) {
            console.log('Using project graph_data as fallback')
            graphData.value = backupGraphData
            await nextTick()
            renderGraph()
          }
        }
      }
    } else {
      error.value = response.error || t('api.projectNotFound', { id: currentProjectId.value })
    }
  } catch (err) {
    console.error('Load project error:', err)
    error.value = t('api.projectNotFound', { id: currentProjectId.value }) + ': ' + (err.message || t('common.unknownError'))
  } finally {
    loading.value = false
  }
}

// 轮询导入状态
let ingestPollTimer = null
const pollIngestStatus = () => {
  if (ingestPollTimer) clearInterval(ingestPollTimer)

  ingestPollTimer = setInterval(async () => {
    try {
      const response = await getIngestStatus(currentProjectId.value)
      if (response.success && response.data.status === 'completed') {
        clearInterval(ingestPollTimer)
        ingestPollTimer = null
        ontologyProgress.value = null

        // 刷新项目并加载图谱
        await loadProject()
      } else if (response.success && response.data.status === 'error') {
        clearInterval(ingestPollTimer)
        ingestPollTimer = null
        ontologyProgress.value = null
        error.value = `数据集导入失败: ${response.data.error || '未知错误'}`
      } else if (response.success && response.data.status === 'processing') {
        // 显示进度
        const { progress, total } = response.data
        if (progress && total) {
          ontologyProgress.value = {
            message: `正在构建知识图谱... (${progress}/${total})`,
            progress: Math.round((progress / total) * 100),
          }
        }
        // 同时拉取已构建的图谱数据并增量渲染
        fetchLiveGraphData()
      }
    } catch (err) {
      console.error('Ingest status poll error:', err)
    }
  }, 3000) // 每 3 秒轮询
}

const updatePhaseByStatus = (status) => {
  switch (status) {
    case 'created':
      currentPhase.value = 0
      break
    case 'graph_extracted':
      currentPhase.value = 1
      break
    case 'graph_completed':
      currentPhase.value = 2
      break
    case 'failed':
      error.value = projectData.value?.error || t('common.failed')
      break
  }
}

// 开始存储图谱
const startStoreGraph = async () => {
  try {
    currentPhase.value = 1
    // 设置初始进度
    buildProgress.value = {
      progress: 0,
      message: '正在存储图谱到 Neo4j...'
    }

    const response = await storeGraph({ project_id: currentProjectId.value })

    if (response.success) {
      buildProgress.value.progress = 100
      buildProgress.value.message = '图谱存储完成'

      // 更新项目状态
      setTimeout(async () => {
        projectData.value = await (await getProject(currentProjectId.value)).data
        currentPhase.value = 2
        graphData.value = projectData.value.graph_data
        buildProgress.value = null
        await nextTick()
        renderGraph()
        // 加载学习路径数据
        loadLearningPathData()
      }, 1000)
    } else {
      error.value = response.error || '存储图谱失败'
      buildProgress.value = null
    }
  } catch (err) {
    console.error('Store graph error:', err)
    error.value = '存储图谱失败: ' + (err.message || '未知错误')
    buildProgress.value = null
  }
}

// 图谱数据轮询定时器
let graphPollTimer = null

// 启动图谱数据轮询
const startGraphPolling = () => {
  // 立即获取一次
  fetchGraphData()
  
  // 每 10 秒自动获取一次图谱数据
  graphPollTimer = setInterval(async () => {
    await fetchGraphData()
  }, 10000)
}

// 手动刷新图谱
const refreshGraph = async () => {
  graphLoading.value = true
  await fetchGraphData()
  graphLoading.value = false
}

// 停止图谱数据轮询
const stopGraphPolling = () => {
  if (graphPollTimer) {
    clearInterval(graphPollTimer)
    graphPollTimer = null
  }
}

// ============== 构建中实时图谱生长 ==============

let isFetchingLive = false // 防止并发 fetchLiveGraphData 调用

// 拉取已构建的图谱数据
const fetchLiveGraphData = async () => {
  if (!currentProjectId.value || isFetchingLive) return
  isFetchingLive = true
  try {
    const response = await getGraphitiData(currentProjectId.value)
    if (response.success && response.data) {
      const newGraphData = response.data
      const nodeCount = newGraphData.nodes?.length || 0
      const edgeCount = newGraphData.edges?.length || 0

      // 更新实时计数
      liveNodeCount.value = nodeCount
      liveEdgeCount.value = edgeCount

      // 首次有数据时初始化图谱
      if (!graphData.value && nodeCount > 0) {
        graphData.value = newGraphData
        await nextTick()
        renderGraph()
      } else if (graphData.value && nodeCount > 0) {
        // 增量更新
        updateGraphIncremental(newGraphData)
      }
    }
  } catch (err) {
    // 数据还未准备好，静默处理
    console.debug('Live graph data not available yet:', err.message)
  } finally {
    isFetchingLive = false
  }
}

// 增量更新图谱（只添加新节点和边）
const updateGraphIncremental = (newData) => {
  const svg = d3.select(graphSvg.value)
  const g = svg.select('.graph-zoom-group')

  if (!g.node()) return // 还没初始化过，交给 renderGraph 处理

  const existingNodeIds = new Set(
    g.selectAll('.node-circle').data().map(d => d.id)
  )
  const existingEdgeIds = new Set(
    g.selectAll('.edge-line-visible').data().map(d => d.id)
  )

  const rawNodes = newData.nodes || []
  const rawEdges = newData.edges || []

  // 找出新节点
  const newRawNodes = rawNodes.filter(n => !existingNodeIds.has(n.uuid))

  // 找出新边（且两端节点都存在）
  const allNodeIds = new Set([...existingNodeIds, ...newRawNodes.map(n => n.uuid)])
  const newRawEdges = rawEdges.filter(e =>
    !existingEdgeIds.has(e.uuid) &&
    allNodeIds.has(e.source_node_uuid) &&
    allNodeIds.has(e.target_node_uuid)
  )

  if (newRawNodes.length === 0 && newRawEdges.length === 0) return

  // 准备新节点数据
  const containerRect = graphContainer.value?.getBoundingClientRect()
  const centerX = (containerRect?.width || 800) / 2
  const centerY = (containerRect?.height || 600) / 2
  const newNodes = newRawNodes.map(n => ({
    id: n.uuid,
    name: n.name || 'N/A',
    type: getNodeTypeFromLabels(n.labels),
    rawData: n,
    x: centerX + (Math.random() - 0.5) * 100,
    y: centerY + (Math.random() - 0.5) * 100,
  }))

  // 准备新边数据
  const nodeMapForEdge = {}
  rawNodes.forEach(n => { nodeMapForEdge[n.uuid] = n })
  const newEdges = newRawEdges.map(e => ({
    id: e.uuid,
    source: e.source_node_uuid,
    target: e.target_node_uuid,
    type: e.fact_type || e.name || 'RELATED_TO',
    rawData: {
      ...e,
      source_name: nodeMapForEdge[e.source_node_uuid]?.name || '?',
      target_name: nodeMapForEdge[e.target_node_uuid]?.name || '?',
    }
  }))

  // 更新 graphData 用于后续全量渲染
  const newNodesForData = newRawNodes.filter(n => !graphData.value.nodes?.some(existing => existing.uuid === n.uuid))
  const newEdgesForData = newRawEdges.filter(e => !graphData.value.edges?.some(existing => existing.uuid === e.uuid))

  // 设置增量更新标志，防止 watch 触发全量渲染
  isIncrementalUpdate = true
  graphData.value = {
    ...graphData.value,
    nodes: [...(graphData.value.nodes || []), ...newNodesForData],
    edges: [...(graphData.value.edges || []), ...newEdgesForData],
  }
  // 下一 tick 后重置标志
  nextTick(() => { isIncrementalUpdate = false })

  // D3 增量添加新节点（弹跳入场动画）
  addNodesToSimulation(g, newNodes)
  addEdgesToSimulation(g, newEdges)

  // 重启力模拟
  if (liveSimulation.value) {
    // 需要包含已有的 D3 节点（带 x, y 位置）
    const existingD3Nodes = g.selectAll('.node-circle').data()
    const allD3Nodes = [...existingD3Nodes, ...newNodes]
    liveSimulation.value.nodes(allD3Nodes)

    // 重建 link force
    const existingD3Edges = g.selectAll('.edge-line-visible').data()
    const allD3Edges = [...existingD3Edges, ...newEdges]
    liveSimulation.value.force('link').links(allD3Edges)

    liveSimulation.value.alpha(0.3).restart()
  }
}

// 增量添加节点到 simulation（弹跳入场动画）
const addNodesToSimulation = (g, newNodes) => {
  if (newNodes.length === 0) return

  const nodeGroup = g.select('.nodes')
  if (!nodeGroup.node()) return

  const nodeEnter = nodeGroup.selectAll('g')
    .data(newNodes, d => d.id)
    .enter()
    .append('g')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      selectNode(d.rawData, getNodeColor(d.type))
    })
    .call(d3.drag()
      .on('start', (event) => {
        if (!event.active && liveSimulation.value) liveSimulation.value.alphaTarget(0.3).restart()
        event.subject.fx = event.subject.x
        event.subject.fy = event.subject.y
      })
      .on('drag', (event) => {
        event.subject.fx = event.x
        event.subject.fy = event.y
      })
      .on('end', (event) => {
        if (!event.active && liveSimulation.value) liveSimulation.value.alphaTarget(0)
        event.subject.fx = null
        event.subject.fy = null
      }))

  // Circle: 初始 r=0, opacity=0，然后弹跳入场
  nodeEnter.append('circle')
    .attr('class', 'node-circle')
    .attr('r', 0)
    .attr('fill', d => getNodeColor(d.type))
    .attr('stroke', '#fff')
    .attr('stroke-width', d => d.rawData?.labels?.includes('Project') ? 3 : 2)
    .attr('filter', 'url(#node-glow-build)')
    .transition()
    .duration(600)
    .ease(d3.easeBackOut)
    .attr('r', d => getNodeRadiusByData(d.rawData))
    .on('end', function () {
      // 3 秒后淡出发光
      d3.select(this)
        .transition()
        .delay(3000)
        .duration(800)
        .attr('filter', null)
    })

  // Label
  nodeEnter.append('text')
    .attr('dx', d => getNodeRadiusByData(d.rawData) + 4)
    .attr('dy', 4)
    .text(d => d.name?.substring(0, 12) || '')
    .attr('font-size', '11px')
    .attr('fill', '#333')
    .attr('font-family', 'JetBrains Mono, monospace')
    .attr('opacity', 0)
    .transition()
    .delay(300)
    .duration(400)
    .attr('opacity', 1)
}

// 增量添加边到 simulation（淡入动画）
const addEdgesToSimulation = (g, newEdges) => {
  if (newEdges.length === 0) return

  const linkGroup = g.select('.links')
  if (!linkGroup.node()) return

  const linkEnter = linkGroup.selectAll('g')
    .data(newEdges, d => d.id)
    .enter()
    .append('g')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      selectEdge(d.rawData)
    })

  // 可见的线（淡入）
  linkEnter.append('line')
    .attr('class', 'edge-line-visible')
    .attr('stroke', '#ccc')
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0)
    .transition()
    .duration(400)
    .attr('stroke-opacity', 0.7)

  // 透明的宽线用于点击
  linkEnter.append('line')
    .attr('stroke', 'transparent')
    .attr('stroke-width', 10)

  // 边标签
  g.select('.link-labels')
    .selectAll('text')
    .data(newEdges, d => d.id)
    .enter()
    .append('text')
    .attr('font-size', '9px')
    .attr('fill', '#999')
    .attr('text-anchor', 'middle')
    .attr('opacity', 0)
    .text(d => d.type.length > 15 ? d.type.substring(0, 12) + '...' : d.type)
    .transition()
    .delay(200)
    .duration(400)
    .attr('opacity', 1)
}

// 获取图谱数据
const fetchGraphData = async () => {
  try {
    // 先获取项目信息
    const projectResponse = await getProject(currentProjectId.value)

    if (projectResponse.success && projectResponse.data.status === 'graph_completed') {
      projectData.value = projectResponse.data
      const graphId = currentProjectId.value

      // 优先尝试 Graphiti 数据端点（新流程）
      let graphResponse = null
      try {
        graphResponse = await getGraphitiData(graphId)
      } catch {
        // Graphiti 端点无数据，回退到传统端点
      }

      // 回退到传统 Neo4j 端点
      if (!graphResponse || !graphResponse.success) {
        graphResponse = await getGraphData(graphId)
      }

      if (graphResponse.success && graphResponse.data) {
        const newData = graphResponse.data
        const newNodeCount = newData.node_count || newData.nodes?.length || 0
        const oldNodeCount = graphData.value?.node_count || graphData.value?.nodes?.length || 0

        console.log('Fetching graph data, nodes:', newNodeCount, 'edges:', newData.edge_count || newData.edges?.length || 0)

        // 数据有变化时更新渲染
        if (newNodeCount !== oldNodeCount || !graphData.value) {
          graphData.value = newData
          await nextTick()
          renderGraph()
        }
      } else if (graphResponse.response?.status === 404) {
        // Neo4j 中没有数据，静默处理（会回退到本地数据）
        console.log('Graph data not found in Neo4j, will use local data if available')
      }
    }
  } catch (err) {
    // 静默处理错误，让调用者决定如何处理
    if (err.response?.status === 404) {
      console.log('Graph data not found in Neo4j (404), will use local data if available')
    } else {
      console.log('Graph data fetch error:', err.message || 'not ready')
    }
  }
}

// 加载图谱数据
const loadGraph = async (graphId) => {
  try {
    graphLoading.value = true
    const response = await getGraphData(graphId)

    if (response.success) {
      graphData.value = response.data
      await nextTick()
      renderGraph()
    }
  } catch (err) {
    console.error('Load graph error:', err)
  } finally {
    graphLoading.value = false
  }
}

// Note: Task polling functions removed as they are no longer needed with Neo4j

// 渲染图谱 (D3.js)
const renderGraph = () => {
  if (!graphSvg.value || !graphData.value) {
    console.log('Cannot render: svg or data missing')
    return
  }

  const container = graphContainer.value
  if (!container) {
    console.log('Cannot render: container missing')
    return
  }

  // 获取容器尺寸
  const rect = container.getBoundingClientRect()
  const width = rect.width || 800
  const height = (rect.height || 600) - 60

  if (width <= 0 || height <= 0) {
    console.log('Cannot render: invalid dimensions', width, height)
    return
  }

  console.log('Rendering graph:', width, 'x', height, 'mode:', viewMode.value)

  const svg = d3.select(graphSvg.value)
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  svg.selectAll('*').remove()
  liveSimulation.value = null

  // 处理节点数据
  const nodesData = graphData.value.nodes || []
  const edgesData = graphData.value.edges || []

  if (nodesData.length === 0) {
    console.log('No nodes to render')
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', height / 2)
      .attr('text-anchor', 'middle')
      .attr('fill', '#999')
      .text(t('process.waitingForData'))
    return
  }

  // 创建节点映射
  const nodeMap = {}
  nodesData.forEach(n => {
    nodeMap[n.uuid] = n
  })

  // 学习路径边类型（3种核心 + 旧类型兼容）
  const learningEdgeTypes = new Set(['NEXT_STEP', 'REQUIRES', 'PREREQUISITE_OF', 'BRANCHES_FROM', 'MERGES_TO', 'ENABLES', 'BUILDS_ON', 'PARALLEL_WITH'])

  // 边颜色映射（3种核心颜色）
  const edgeColorMap = {
    'NEXT_STEP': '#2D3436',
    'REQUIRES': '#7B2D8E',
    'PREREQUISITE_OF': '#FF6B35',
    // 旧类型映射到最近的核心颜色
    'BRANCHES_FROM': '#7B2D8E',
    'MERGES_TO': '#2D3436',
    'BUILDS_ON': '#2D3436',
    'ENABLES': '#7B2D8E',
    'PARALLEL_WITH': '#999'
  }

  // 获取边的颜色
  const getEdgeColor = (factType) => edgeColorMap[factType] || '#ccc'

  // 使用共享的节点半径函数
  const getNodeRadius = getNodeRadiusByData

  // 获取节点透明度
  const getNodeOpacity = (node) => {
    return 1.0
  }

  // 获取节点边框宽度（Project更粗）
  const getNodeStrokeWidth = (node) => {
    if (node.labels?.includes('Project')) return 3
    return 2
  }

  // 判断边是否需要箭头
  const needsArrow = (factType) => learningEdgeTypes.has(factType)

  // 判断边是否为虚线
  const isDashed = (factType) => factType === 'PARALLEL_WITH'

  // 判断边是否加粗（只有 NEXT_STEP 是粗线）
  const isThickEdge = (factType) => factType === 'NEXT_STEP'

  const nodes = nodesData.map(n => ({
    id: n.uuid,
    name: n.name || t('common.none'),
    type: getNodeTypeFromLabels(n.labels),
    rawData: n
  }))

  const nodeIds = new Set(nodes.map(n => n.id))

  const edges = edgesData
    .filter(e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid))
    .map(e => ({
      id: e.uuid,
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      type: e.fact_type || e.name || 'RELATED_TO',
      rawData: {
        ...e,
        source_name: nodeMap[e.source_node_uuid]?.name || t('common.unknown'),
        target_name: nodeMap[e.target_node_uuid]?.name || t('common.unknown')
      }
    }))

  console.log('Nodes:', nodes.length, 'Edges:', edges.length)

  // 颜色映射 — Graphiti entity types get fixed colors, others use d3 auto
  const types = [...new Set(nodes.map(n => n.type))]
  const fallbackRange = ['#E9724C', '#2D3436', '#6C5CE7', '#FFD166', '#06D6A0', '#118AB2', '#EF476F', '#073B4C']
  const fallbackScale = d3.scaleOrdinal().domain(types.filter(t => !GRAPHITI_TYPE_COLORS[t])).range(fallbackRange)
  const colorScale = (type) => GRAPHITI_TYPE_COLORS[type] || fallbackScale(type)

  // 添加缩放功能
  const g = svg.append('g').attr('class', 'graph-zoom-group')

  svg.call(d3.zoom()
    .extent([[0, 0], [width, height]])
    .scaleExtent([0.2, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    }))

  // 定义箭头标记
  const defs = svg.append('defs')

  // 为每种学习路径边类型定义不同颜色的箭头
  Object.entries(edgeColorMap).forEach(([type, color]) => {
    defs.append('marker')
      .attr('id', `arrow-${type}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', color)
  })

  // 默认箭头
  defs.append('marker')
    .attr('id', 'arrow-default')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 20)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#ccc')

  // 构建中节点发光滤镜
  defs.append('filter')
    .attr('id', 'node-glow-build')
    .attr('x', '-50%').attr('y', '-50%')
    .attr('width', '200%').attr('height', '200%')
    .append('feGaussianBlur')
    .attr('stdDeviation', '4')
    .attr('result', 'blur')
  defs.select('#node-glow-build')
    .append('feMerge')
    .selectAll('feMergeNode')
    .data(['blur', 'SourceGraphic'])
    .enter()
    .append('feMergeNode')
    .attr('in', d => d)

  if (viewMode.value === 'learning-path' && learningPathData.value) {
    // ===== 学习路径视图：分层布局 =====
    renderLearningPathLayout(g, nodes, edges, nodeMap, width, height, colorScale, getNodeRadius, getNodeOpacity, getNodeStrokeWidth, getEdgeColor, needsArrow, isDashed, isThickEdge, defs)
  } else {
    // ===== 全图视图：力导向布局 =====
    renderForceLayout(g, svg, nodes, edges, nodeMap, width, height, colorScale, getNodeRadius, getNodeOpacity, getNodeStrokeWidth, getEdgeColor, needsArrow, isDashed, isThickEdge)
  }
}

// 力导向布局渲染
const renderForceLayout = (g, svg, nodes, edges, nodeMap, width, height, colorScale, getNodeRadius, getNodeOpacity, getNodeStrokeWidth, getEdgeColor, needsArrow, isDashed, isThickEdge) => {
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(100).strength(0.5))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(40))
    .force('x', d3.forceX(width / 2).strength(0.05))
    .force('y', d3.forceY(height / 2).strength(0.05))

  // 绘制边
  const linkGroup = g.append('g')
    .attr('class', 'links')
    .selectAll('g')
    .data(edges)
    .enter()
    .append('g')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      selectEdge(d.rawData)
    })

  // 可见的线
  const link = linkGroup.append('line')
    .attr('stroke', d => getEdgeColor(d.type))
    .attr('stroke-width', d => isThickEdge(d.type) ? 2.5 : 1.5)
    .attr('stroke-opacity', 0.7)
    .attr('stroke-dasharray', d => isDashed(d.type) ? '5,5' : null)
    .attr('marker-end', d => needsArrow(d.type) ? `url(#arrow-${d.type})` : 'none')

  // 透明的宽线用于点击
  linkGroup.append('line')
    .attr('stroke', 'transparent')
    .attr('stroke-width', 10)

  // 边标签
  const linkLabel = g.append('g')
    .attr('class', 'link-labels')
    .selectAll('text')
    .data(edges)
    .enter()
    .append('text')
    .attr('font-size', '9px')
    .attr('fill', d => getEdgeColor(d.type))
    .attr('text-anchor', 'middle')
    .text(d => d.type.length > 15 ? d.type.substring(0, 12) + '...' : d.type)

  // 绘制节点
  const node = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodes)
    .enter()
    .append('g')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      selectNode(d.rawData, colorScale(d.type))
    })
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))

  node.append('circle')
    .attr('r', d => getNodeRadius(d.rawData))
    .attr('fill', d => colorScale(d.type))
    .attr('fill-opacity', d => getNodeOpacity(d.rawData))
    .attr('stroke', '#fff')
    .attr('stroke-width', d => getNodeStrokeWidth(d.rawData))
    .attr('class', 'node-circle')

  node.append('text')
    .attr('dx', d => getNodeRadius(d.rawData) + 4)
    .attr('dy', 4)
    .text(d => d.name?.substring(0, 12) || '')
    .attr('font-size', '11px')
    .attr('fill', '#333')
    .attr('font-family', 'JetBrains Mono, monospace')

  svg.on('click', () => {
    closeDetailPanel()
  })

  simulation.on('tick', () => {
    // Use DOM queries to include both existing and incrementally added elements
    g.selectAll('.links line:not([stroke="transparent"])')
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    g.selectAll('.link-labels text')
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2 - 5)

    g.selectAll('.nodes g')
      .attr('transform', d => `translate(${d.x},${d.y})`)
  })

  function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    event.subject.fx = event.subject.x
    event.subject.fy = event.subject.y
  }

  function dragged(event) {
    event.subject.fx = event.x
    event.subject.fy = event.y
  }

  function dragended(event) {
    if (!event.active) simulation.alphaTarget(0)
    event.subject.fx = null
    event.subject.fy = null
  }

  // Store simulation reference for incremental updates
  liveSimulation.value = simulation
}

// 学习路径分层布局渲染
const renderLearningPathLayout = (g, svg, nodes, edges, nodeMap, width, height, colorScale, getNodeRadius, getNodeOpacity, getNodeStrokeWidth, getEdgeColor, needsArrow, isDashed, isThickEdge, defs) => {
  // 添加缩放功能
  svg.call(d3.zoom()
    .extent([[0, 0], [width, height]])
    .scaleExtent([0.2, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    }))

  const lpData = learningPathData.value
  if (!lpData) return

  const isPblMode = lpData.mode === 'pbl'
  const mainPath = lpData.main_path || []
  const branchPaths = lpData.branch_paths || []

  // 计算主路径节点位置（水平排列在中央线）
  const centerY = height / 2
  const padding = 80
  const mainSpacing = mainPath.length > 1 ? (width - padding * 2) / (mainPath.length - 1) : 0

  // 构建所有节点的位置映射 uuid -> {x, y}
  const positionMap = {}

  // 主路径节点
  mainPath.forEach((uuid, idx) => {
    positionMap[uuid] = {
      x: mainPath.length === 1 ? width / 2 : padding + idx * mainSpacing,
      y: centerY
    }
  })

  if (isPblMode) {
    // PBL 模式：知识链垂直排列在项目下方，形成环形路径
    const projectSubgraphs = lpData.project_knowledge_subgraphs || {}
    const allProjectUuids = new Set(mainPath)
    const branchProjs = lpData.branch_projects || []
    branchProjs.forEach(uuid => allProjectUuids.add(uuid))

    // 为分支项目分配位置（在主路径上方交替排列）
    branchProjs.forEach((uuid, bIdx) => {
      if (positionMap[uuid]) return
      // 找到 NEXT_STEP 边中连接此分支项目的主路径项目
      const direction = bIdx % 2 === 0 ? -1 : 1
      const branchY = centerY + direction * 120
      // 根据 learning_order 决定 x 位置
      const branchNode = nodeMap[uuid]
      const order = branchNode?.attributes?.learning_order || (bIdx + 1)
      const branchX = padding + (order - 1) * mainSpacing
      positionMap[uuid] = {
        x: branchX,
        y: branchY
      }
    })

    allProjectUuids.forEach(projUuid => {
      const subgraph = projectSubgraphs[projUuid]
      if (!subgraph) return

      const projPos = positionMap[projUuid]
      if (!projPos) return

      const knowledgeChain = subgraph.knowledge_chain || []
      const kpSpacingY = 55  // 知识点垂直间距
      const kpStartY = projPos.y + 70  // 从项目下方开始

      knowledgeChain.forEach((kpUuid, kIdx) => {
        if (positionMap[kpUuid]) return
        positionMap[kpUuid] = {
          x: projPos.x,
          y: kpStartY + kIdx * kpSpacingY
        }
      })
    })
  } else {
    // 知识驱动模式：分支路径在主路径上方或下方交替排列
    branchPaths.forEach((branch, bIdx) => {
      const fromNode = positionMap[branch.from_node_uuid]
      if (!fromNode) return

      const direction = bIdx % 2 === 0 ? -1 : 1
      const branchY = centerY + direction * 120
      const branchSpacing = 80
      const startX = fromNode.x + branchSpacing

      branch.branch_nodes?.forEach((uuid, nIdx) => {
        positionMap[uuid] = {
          x: startX + nIdx * branchSpacing,
          y: branchY
        }
      })
    })
  }

  // 为不在学习路径中的节点分配位置
  let extraIdx = 0
  const extraY = height - 100
  nodes.forEach(n => {
    if (!positionMap[n.id]) {
      positionMap[n.id] = {
        x: padding + extraIdx * 80,
        y: extraY
      }
      extraIdx++
    }
  })

  // 设置节点位置
  nodes.forEach(n => {
    const pos = positionMap[n.id]
    if (pos) {
      n.x = pos.x
      n.y = pos.y
      n.fx = pos.x
      n.fy = pos.y
    }
  })

  // 绘制边
  const linkGroup = g.append('g')
    .attr('class', 'links')
    .selectAll('g')
    .data(edges)
    .enter()
    .append('g')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      selectEdge(d.rawData)
    })

  const link = linkGroup.append('path')
    .attr('stroke', d => getEdgeColor(d.type))
    .attr('stroke-width', d => isThickEdge(d.type) ? 3 : 1.5)
    .attr('stroke-opacity', 0.8)
    .attr('stroke-dasharray', d => isDashed(d.type) ? '5,5' : null)
    .attr('fill', 'none')
    .attr('marker-end', d => needsArrow(d.type) ? `url(#arrow-${d.type})` : 'none')
    .attr('d', d => {
      const srcId = typeof d.source === 'string' ? d.source : d.source.id
      const tgtId = typeof d.target === 'string' ? d.target : d.target.id
      const srcPos = positionMap[srcId]
      const tgtPos = positionMap[tgtId]
      if (!srcPos || !tgtPos) return ''

      // Check if this is a ring-closing REQUIRES edge (KP → Project)
      const isRingClosure = d.type === 'REQUIRES' &&
        nodeMap[srcId] && nodeMap[tgtId] &&
        !nodeMap[srcId].labels?.includes('Project') &&
        nodeMap[tgtId].labels?.includes('Project')

      if (isRingClosure) {
        // Draw an arc path from KP back to the project
        const srcR = getNodeRadius(nodeMap[srcId])
        const tgtR = getNodeRadius(nodeMap[tgtId])
        // Arc offset to the right side
        const arcOffset = 40
        const midX = (srcPos.x + tgtPos.x) / 2 + arcOffset
        const midY = (srcPos.y + tgtPos.y) / 2
        return `M ${srcPos.x + srcR} ${srcPos.y} Q ${midX} ${midY} ${tgtPos.x + tgtR} ${tgtPos.y}`
      }

      // Default straight line
      return `M ${srcPos.x} ${srcPos.y} L ${tgtPos.x} ${tgtPos.y}`
    })

  linkGroup.append('path')
    .attr('stroke', 'transparent')
    .attr('stroke-width', 10)
    .attr('fill', 'none')
    .attr('d', d => {
      const srcId = typeof d.source === 'string' ? d.source : d.source.id
      const tgtId = typeof d.target === 'string' ? d.target : d.target.id
      const srcPos = positionMap[srcId]
      const tgtPos = positionMap[tgtId]
      if (!srcPos || !tgtPos) return ''

      // Check if this is a ring-closing REQUIRES edge (KP → Project)
      const isRingClosure = d.type === 'REQUIRES' &&
        nodeMap[srcId] && nodeMap[tgtId] &&
        !nodeMap[srcId].labels?.includes('Project') &&
        nodeMap[tgtId].labels?.includes('Project')

      if (isRingClosure) {
        const srcR = getNodeRadius(nodeMap[srcId])
        const tgtR = getNodeRadius(nodeMap[tgtId])
        const arcOffset = 40
        const midX = (srcPos.x + tgtPos.x) / 2 + arcOffset
        const midY = (srcPos.y + tgtPos.y) / 2
        return `M ${srcPos.x + srcR} ${srcPos.y} Q ${midX} ${midY} ${tgtPos.x + tgtR} ${tgtPos.y}`
      }

      return `M ${srcPos.x} ${srcPos.y} L ${tgtPos.x} ${tgtPos.y}`
    })

  // 边标签
  g.append('g')
    .attr('class', 'link-labels')
    .selectAll('text')
    .data(edges)
    .enter()
    .append('text')
    .attr('font-size', '9px')
    .attr('fill', d => getEdgeColor(d.type))
    .attr('text-anchor', 'middle')
    .attr('x', d => {
      const srcId = typeof d.source === 'string' ? d.source : d.source.id
      const tgtId = typeof d.target === 'string' ? d.target : d.target.id
      return ((positionMap[srcId]?.x || 0) + (positionMap[tgtId]?.x || 0)) / 2
    })
    .attr('y', d => {
      const srcId = typeof d.source === 'string' ? d.source : d.source.id
      const tgtId = typeof d.target === 'string' ? d.target : d.target.id
      return ((positionMap[srcId]?.y || 0) + (positionMap[tgtId]?.y || 0)) / 2 - 5
    })
    .text(d => d.type.length > 15 ? d.type.substring(0, 12) + '...' : d.type)

  // 绘制节点
  const node = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodes)
    .enter()
    .append('g')
    .attr('transform', d => `translate(${d.x},${d.y})`)
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      selectNode(d.rawData, colorScale(d.type))
    })

  // PBL 模式下 Project 节点用圆角矩形，KnowledgePoint 用圆
  if (isPblMode) {
    node.each(function(d) {
      const el = d3.select(this)
      const isProject = d.rawData?.labels?.includes('Project')
      const r = getNodeRadius(d.rawData)

      if (isProject) {
        // Project 节点用圆角矩形
        const rectW = r * 2.5
        const rectH = r * 1.8
        el.append('rect')
          .attr('x', -rectW / 2)
          .attr('y', -rectH / 2)
          .attr('width', rectW)
          .attr('height', rectH)
          .attr('rx', 6)
          .attr('ry', 6)
          .attr('fill', colorScale(d.type))
          .attr('fill-opacity', 1)
          .attr('stroke', '#2D3436')
          .attr('stroke-width', 2.5)
      } else {
        // KnowledgePoint 节点用圆
        el.append('circle')
          .attr('r', r)
          .attr('fill', colorScale(d.type))
          .attr('fill-opacity', d => getNodeOpacity(d.rawData))
          .attr('stroke', '#fff')
          .attr('stroke-width', d => getNodeStrokeWidth(d.rawData))
      }
    })
  } else {
    node.append('circle')
      .attr('r', d => getNodeRadius(d.rawData))
      .attr('fill', d => colorScale(d.type))
      .attr('fill-opacity', d => getNodeOpacity(d.rawData))
      .attr('stroke', d => d.rawData.attributes?.path_type === 'main' ? '#2D3436' : '#fff')
      .attr('stroke-width', d => getNodeStrokeWidth(d.rawData))
  }

  node.append('text')
    .attr('dx', d => {
      if (isPblMode && d.rawData?.labels?.includes('Project')) {
        return getNodeRadius(d.rawData) * 1.3 + 4
      }
      return getNodeRadius(d.rawData) + 4
    })
    .attr('dy', 4)
    .text(d => d.name?.substring(0, 12) || '')
    .attr('font-size', '11px')
    .attr('fill', '#333')
    .attr('font-family', 'JetBrains Mono, monospace')

  // 主路径序号
  node.filter(d => d.rawData.attributes?.learning_order)
    .append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', d => {
      if (isPblMode && d.rawData?.labels?.includes('Project')) {
        return getNodeRadius(d.rawData) * 0.3
      }
      return getNodeRadius(d.rawData) / 3
    })
    .attr('font-size', d => {
      if (isPblMode && d.rawData?.labels?.includes('Project')) return '10px'
      return '8px'
    })
    .attr('fill', '#fff')
    .attr('font-weight', 'bold')
    .text(d => d.rawData.attributes?.learning_order)

  svg.on('click', () => {
    closeDetailPanel()
  })
}

// 监听图谱数据变化（非增量更新时触发全量渲染）
watch(graphData, () => {
  if (graphData.value && !isIncrementalUpdate) {
    nextTick(() => renderGraph())
  }
})

// 生命周期
onMounted(async () => {
  await initProject()
  resumeClassroomGenerationIfPending()
})

onUnmounted(() => {
  stopGraphPolling()
  if (ingestPollTimer) {
    clearInterval(ingestPollTimer)
    ingestPollTimer = null
  }
  if (classroomPollTimer.value) {
    clearTimeout(classroomPollTimer.value)
    classroomPollTimer.value = null
  }
  if (liveSimulation.value) {
    liveSimulation.value.stop()
    liveSimulation.value = null
  }
})
</script>

<style scoped>
/* 变量 */
:root {
  --black: #000000;
  --white: #FFFFFF;
  --orange: #FF6B35;
  --gray-light: #F5F5F5;
  --gray-border: #E0E0E0;
  --gray-text: #666666;
}

.process-page {
  min-height: 100vh;
  background: var(--white);
  font-family: 'JetBrains Mono', 'Noto Sans SC', monospace;
  overflow: hidden; /* Prevent body scroll in fullscreen */
}

/* 导航栏 */
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: #000;
  color: #fff;
  z-index: 10;
  position: relative;
}

.nav-brand {
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: opacity 0.2s;
}

.nav-brand:hover {
  opacity: 0.8;
}

.nav-center {
  display: flex;
  align-items: center;
  gap: 12px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.step-badge {
  background: #FF6B35;
  color: #fff;
  padding: 2px 8px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  border-radius: 2px;
}

.step-name {
  font-size: 0.85rem;
  letter-spacing: 0.05em;
  color: #fff;
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

.nav-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-qa-link {
  color: #FF6B35;
  text-decoration: none;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 4px 10px;
  border: 1px solid #FF6B35;
  border-radius: 4px;
  transition: all 0.2s;
  font-family: 'JetBrains Mono', monospace;
}

.nav-qa-link:hover {
  background: #FF6B35;
  color: #fff;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #666;
  margin-right: 8px;
}

.status-dot.processing {
  background: #FF6B35;
  animation: pulse 1.5s infinite;
}

.status-dot.completed {
  background: #1A936F;
}

.status-dot.error {
  background: #C5283D;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 0.75rem;
  color: #999;
}

/* 主内容区 */
.main-content {
  display: flex;
  height: calc(100vh - 56px);
  position: relative;
}

/* 左侧面板 - 50% default */
.left-panel {
  width: 50%;
  flex: none; /* Fixed width initially */
  display: flex;
  flex-direction: column;
  border-right: 1px solid #E0E0E0;
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  background: #fff;
  z-index: 5;
}

.left-panel.full-screen {
  width: 100%;
  border-right: none;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid #E0E0E0;
  background: #fff;
  height: 50px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-deco {
  color: #FF6B35;
  font-size: 0.8rem;
}

.header-title {
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 0.75rem;
  color: #666;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-val {
  font-weight: 600;
  color: #333;
}

.stat-divider {
  color: #eee;
}

.action-buttons {
    display: flex;
    align-items: center;
    gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  color: #666;
  border-radius: 2px;
}

.action-btn:hover:not(:disabled) {
  background: #F5F5F5;
  color: #000;
}

.action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.icon-refresh, .icon-fullscreen {
  font-size: 1rem;
  line-height: 1;
}

.icon-refresh.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 图谱容器 */
.graph-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.graph-loading,
.graph-waiting,
.graph-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.loading-animation {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
}

.loading-ring {
  position: absolute;
  border: 2px solid transparent;
  border-radius: 50%;
  animation: ring-rotate 1.5s linear infinite;
}

.loading-ring:nth-child(1) {
  width: 80px;
  height: 80px;
  border-top-color: #000;
}

.loading-ring:nth-child(2) {
  width: 60px;
  height: 60px;
  top: 10px;
  left: 10px;
  border-right-color: #FF6B35;
  animation-delay: 0.2s;
}

.loading-ring:nth-child(3) {
  width: 40px;
  height: 40px;
  top: 20px;
  left: 20px;
  border-bottom-color: #666;
  animation-delay: 0.4s;
}

@keyframes ring-rotate {
  to { transform: rotate(360deg); }
}

.loading-text,
.waiting-text {
  font-size: 0.9rem;
  color: #333;
  margin: 0 0 8px;
}

.waiting-hint {
  font-size: 0.8rem;
  color: #999;
  margin: 0;
}

.waiting-icon {
  margin-bottom: 20px;
}

.network-icon {
  width: 100px;
  height: 100px;
  opacity: 0.6;
}

.graph-view {
  width: 100%;
  height: 100%;
  position: relative;
}

.graph-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.graph-building-hint {
  position: absolute;
  bottom: 16px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 107, 53, 0.1);
  border: 1px solid #FF6B35;
  font-size: 0.8rem;
  color: #FF6B35;
}

/* 构建中覆盖层 */
.graph-build-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
  z-index: 5;
}

/* 构建中底部统计条 */
.graph-build-stats {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  background: rgba(0, 0, 0, 0.75);
  border-radius: 20px;
  font-size: 0.8rem;
  color: #fff;
  z-index: 5;
  white-space: nowrap;
  animation: fadeInUp 0.4s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateX(-50%) translateY(10px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}

.build-stat-dot {
  width: 8px;
  height: 8px;
  background: #FF6B35;
  border-radius: 50%;
  animation: pulse 1s infinite;
}

.build-stat-text {
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.02em;
}

.build-stat-progress {
  color: #999;
  font-size: 0.75rem;
  margin-left: 4px;
}

.building-dot {
  width: 8px;
  height: 8px;
  background: #FF6B35;
  border-radius: 50%;
  animation: pulse 1s infinite;
}

/* 节点/边详情面板 */
.detail-panel {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 320px;
  max-height: calc(100% - 32px);
  background: #fff;
  border: 1px solid #E0E0E0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.detail-panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #FAFAFA;
  border-bottom: 1px solid #E0E0E0;
}

.detail-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #333;
}

.detail-badge {
  padding: 2px 10px;
  font-size: 0.75rem;
  color: #fff;
  border-radius: 2px;
}

.detail-close {
  margin-left: auto;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #999;
  cursor: pointer;
  transition: color 0.2s;
}

.detail-close:hover {
  color: #333;
}

.detail-content {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.detail-label {
  font-size: 0.8rem;
  color: #999;
  min-width: 70px;
  flex-shrink: 0;
}

.detail-value {
  font-size: 0.85rem;
  color: #333;
  word-break: break-word;
}

.detail-value.uuid {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #666;
}

.detail-section {
  margin-bottom: 12px;
}

.detail-summary {
  margin: 8px 0 0 0;
  font-size: 0.85rem;
  color: #333;
  line-height: 1.6;
  padding: 10px;
  background: #F9F9F9;
  border-left: 3px solid #FF6B35;
}

.detail-labels {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.label-tag {
  padding: 2px 8px;
  font-size: 0.75rem;
  background: #F0F0F0;
  border: 1px solid #E0E0E0;
  color: #666;
}

/* 边详情关系展示 */
.edge-relation {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: #F9F9F9;
  border: 1px solid #E0E0E0;
}

.edge-source,
.edge-target {
  font-size: 0.85rem;
  font-weight: 500;
  color: #333;
}

.edge-arrow {
  color: #999;
}

.edge-type {
  padding: 2px 8px;
  font-size: 0.75rem;
  background: #FF6B35;
  color: #fff;
}

.detail-value.highlight {
  font-weight: 600;
  color: #000;
}

.detail-subtitle {
  font-size: 0.9rem;
  font-weight: 600;
  color: #333;
  margin: 16px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #E0E0E0;
}

/* Properties 属性列表 */
.properties-list {
  margin-top: 8px;
  padding: 10px;
  background: #F9F9F9;
  border: 1px solid #E0E0E0;
}

.property-item {
  display: flex;
  margin-bottom: 6px;
  font-size: 0.85rem;
}

.property-item:last-child {
  margin-bottom: 0;
}

.property-key {
  color: #666;
  margin-right: 8px;
  font-family: 'JetBrains Mono', monospace;
}

.property-value {
  color: #333;
  word-break: break-word;
}

/* Episodes 列表 */
.episodes-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.episode-tag {
  display: block;
  padding: 6px 10px;
  font-size: 0.75rem;
  font-family: 'JetBrains Mono', monospace;
  background: #F0F0F0;
  border: 1px solid #E0E0E0;
  color: #666;
  word-break: break-all;
}

.error-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 10px;
}

/* 图谱图例 */
.graph-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 12px 24px;
  border-top: 1px solid #E0E0E0;
  background: #FAFAFA;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-label {
  color: #333;
}

.legend-count {
  color: #999;
}

.legend-divider {
  color: #E0E0E0;
  margin: 0 4px;
}

.legend-line {
  display: inline-block;
  width: 16px;
  height: 2px;
  border-radius: 1px;
  flex-shrink: 0;
}

/* 右侧面板 - 50% default */
.right-panel {
  width: 50%;
  flex: none;
  display: flex;
  flex-direction: column;
  background: #fff;
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease, transform 0.3s ease;
  overflow: hidden;
  opacity: 1;
}

.right-panel.hidden {
  width: 0;
  opacity: 0;
  transform: translateX(20px);
  pointer-events: none;
}

.right-panel .panel-header.dark-header {
  background: #000;
  color: #fff;
  border-bottom: none;
}

.right-panel .header-icon {
  color: #FF6B35;
  margin-right: 8px;
}

/* 流程内容 */
.process-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* 流程阶段 */
.process-phase {
  margin-bottom: 24px;
  border: 1px solid #E0E0E0;
  opacity: 0.5;
  transition: all 0.3s;
}

.process-phase.active,
.process-phase.completed {
  opacity: 1;
}

.process-phase.active {
  border-color: #FF6B35;
}

.process-phase.completed {
  border-color: #1A936F;
}

.phase-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: #FAFAFA;
  border-bottom: 1px solid #E0E0E0;
}

.process-phase.active .phase-header {
  background: #FFF5F2;
}

.process-phase.completed .phase-header {
  background: #F2FAF6;
}

.phase-num {
  font-size: 1.5rem;
  font-weight: 700;
  color: #ddd;
  line-height: 1;
}

.process-phase.active .phase-num {
  color: #FF6B35;
}

.process-phase.completed .phase-num {
  color: #1A936F;
}

.phase-info {
  flex: 1;
}

.phase-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.phase-api {
  font-size: 0.75rem;
  color: #999;
  font-family: 'JetBrains Mono', monospace;
}

.phase-status {
  font-size: 0.75rem;
  padding: 4px 10px;
  background: #eee;
  color: #666;
}

.phase-status.active {
  background: #FF6B35;
  color: #fff;
}

.phase-status.completed {
  background: #1A936F;
  color: #fff;
}

/* 阶段详情 */
.phase-detail {
  padding: 16px;
}

/* 实体标签 */
.entity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.entity-tag {
  font-size: 0.75rem;
  padding: 4px 10px;
  background: #F5F5F5;
  border: 1px solid #E0E0E0;
  color: #333;
}

/* 关系列表 */
.relation-list {
  font-size: 0.8rem;
}

.relation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px dashed #eee;
}

.relation-item:last-child {
  border-bottom: none;
}

.rel-source,
.rel-target {
  color: #333;
}

.rel-arrow {
  color: #ccc;
}

.rel-name {
  color: #FF6B35;
  font-weight: 500;
}

.relation-more {
  padding-top: 8px;
  color: #999;
  font-size: 0.75rem;
}

/* 本体生成进度 */
.ontology-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #FFF5F2;
  border: 1px solid #FFE0D6;
}

.progress-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #FFE0D6;
  border-top-color: #FF6B35;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.progress-text {
  font-size: 0.85rem;
  color: #333;
}

/* 等待状态 */
.waiting-state {
  padding: 16px;
  background: #F9F9F9;
  border: 1px dashed #E0E0E0;
  text-align: center;
}

.waiting-hint {
  font-size: 0.85rem;
  color: #999;
}

/* 进度条 */
.progress-bar {
  height: 6px;
  background: #E0E0E0;
  margin-bottom: 8px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #FF6B35;
  transition: width 0.3s;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
}

.progress-message {
  color: #666;
}

.progress-percent {
  color: #FF6B35;
  font-weight: 600;
}

/* 构建结果 */
.build-result {
  display: flex;
  gap: 16px;
}

.result-item {
  flex: 1;
  text-align: center;
  padding: 12px;
  background: #F5F5F5;
}

.result-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #000;
  margin-bottom: 4px;
}

.result-label {
  font-size: 0.7rem;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* 下一步按钮 */
.next-step-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #E0E0E0;
}

.next-step-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px;
  background: #000;
  color: #fff;
  border: none;
  font-size: 1rem;
  font-weight: 500;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all 0.2s;
}

.next-step-btn:hover:not(:disabled) {
  background: #FF6B35;
}

.next-step-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-arrow {
  font-size: 1.2rem;
}

/* 项目信息面板 */
.project-panel {
  border-top: 1px solid #E0E0E0;
  background: #FAFAFA;
}

.project-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  border-bottom: 1px solid #E0E0E0;
}

.project-icon {
  color: #FF6B35;
}

.project-title {
  font-size: 0.85rem;
  font-weight: 600;
}

.project-details {
  padding: 16px 24px;
}

.project-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px 0;
  border-bottom: 1px dashed #E0E0E0;
  font-size: 0.8rem;
}

.project-item:last-child {
  border-bottom: none;
}

.item-label {
  color: #999;
  flex-shrink: 0;
}

.item-value {
  color: #333;
  text-align: right;
  max-width: 60%;
  word-break: break-all;
}

.item-value.code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #666;
}

/* 响应式 */
@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
  }

  .left-panel {
    width: 100% !important;
    border-right: none;
    border-bottom: 1px solid #E0E0E0;
    height: 50vh;
  }

  .right-panel {
    width: 100% !important;
    height: 50vh;
    opacity: 1 !important;
    transform: none !important;
  }

  .right-panel.hidden {
      display: none;
  }
}

/* ===== Learning Path Styles ===== */

/* View mode toggle button */
.view-toggle-btn {
  background: #F5F5F5 !important;
  border: 1px solid #E0E0E0 !important;
}
.view-toggle-btn:hover {
  background: #E8E8E8 !important;
}
.view-mode-icon {
  font-size: 0.85rem;
}

/* Learning path badges */
.detail-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 8px 0 12px;
}

.lp-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.03em;
}

.badge-main {
  background: #FF6B35;
  color: #fff;
}

.badge-branch {
  background: #7B2D8E;
  color: #fff;
}

.badge-project {
  background: #2D3436;
  color: #fff;
}

.badge-knowledge {
  background: #FF6B35;
  color: #fff;
}

.badge-beginner {
  background: #4CAF50;
  color: #fff;
}

.badge-intermediate {
  background: #FF9800;
  color: #fff;
}

.badge-advanced {
  background: #F44336;
  color: #fff;
}

.badge-order {
  background: #E0E0E0;
  color: #333;
}

/* Learning path info text */
.learning-path-info {
  border-left-color: #FF6B35;
}

.outcomes-info {
  border-left-color: #1A936F;
}

/* Branch info */
.branch-names {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.branch-name-tag {
  padding: 2px 8px;
  background: #F3E5F5;
  border: 1px solid #CE93D8;
  border-radius: 10px;
  font-size: 0.75rem;
  color: #7B2D8E;
}

.project-name-tag {
  padding: 2px 8px;
  background: #E8EAF6;
  border: 1px solid #9FA8DA;
  border-radius: 10px;
  font-size: 0.75rem;
  color: #283593;
}

.shared-kp-badge {
  display: inline-block;
  padding: 1px 6px;
  background: #FFF3E0;
  border: 1px solid #FFB74D;
  border-radius: 8px;
  font-size: 0.65rem;
  color: #E65100;
  margin-left: 4px;
}

.ring-badge {
  display: inline-block;
  font-size: 0.75rem;
  color: #7B2D8E;
  margin-left: 4px;
}

.ring-closure {
  font-size: 0.7rem;
  color: #7B2D8E;
  padding: 4px 8px;
  border-top: 1px dashed #CE93D8;
  margin-top: 4px;
}

.kp-count {
  font-size: 0.7rem;
  color: #999;
  margin-left: 4px;
}

/* Learning path sidebar panel */
.learning-path-panel {
  border-top: 1px solid #E0E0E0;
  background: #FAFAFA;
  max-height: 300px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.learning-path-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px 24px;
}

.path-section {
  margin-bottom: 16px;
}

.path-section-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #E0E0E0;
}

.path-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.path-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.15s;
  font-size: 0.78rem;
}

.path-item:hover {
  background: #F0F0F0;
}

.path-order {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2D3436;
  color: #fff;
  border-radius: 50%;
  font-size: 0.65rem;
  font-weight: 700;
  flex-shrink: 0;
}

.branch-order {
  background: #7B2D8E;
}

.path-name {
  flex: 1;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.path-difficulty {
  font-size: 0.6rem;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 8px;
  flex-shrink: 0;
}

.diff-beginner { background: #E8F5E9; color: #2E7D32; }
.diff-intermediate { background: #FFF3E0; color: #E65100; }
.diff-advanced { background: #FFEBEE; color: #C62828; }

/* Branch details */
.branch-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.branch-details {
  border: 1px solid #E0E0E0;
  border-radius: 4px;
  background: #fff;
}

.branch-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 500;
  color: #7B2D8E;
  list-style: none;
}

.branch-summary::-webkit-details-marker {
  display: none;
}

.branch-arrow {
  font-size: 0.7rem;
  transition: transform 0.15s;
}

.branch-details[open] .branch-arrow {
  transform: rotate(90deg);
}

.branch-info {
  padding: 4px 10px 8px;
}

.branch-from {
  font-size: 0.7rem;
  color: #999;
  margin-bottom: 4px;
}

.branch-path-item {
  padding: 3px 8px;
}

.branch-merge {
  font-size: 0.7rem;
  color: #1A936F;
  padding: 4px 8px;
  border-top: 1px dashed #E0E0E0;
  margin-top: 4px;
}

/* Classroom Action Styles */
.classroom-action {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

/* PBL Learning Action Styles */
.pbl-action {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.pbl-btn {
  width: 100%;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  letter-spacing: 0.02em;
  background: linear-gradient(135deg, #FF4500, #E03E00);
  color: white;
}

.pbl-btn:hover {
  background: linear-gradient(135deg, #E03E00, #CC3700);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(255, 69, 0, 0.3);
}

.classroom-btn {
  width: 100%;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  letter-spacing: 0.02em;
}

.classroom-btn-ready {
  background: linear-gradient(135deg, #1A936F, #2D9E7E);
  color: white;
}

.classroom-btn-ready:hover {
  background: linear-gradient(135deg, #15825F, #258D6E);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(26, 147, 111, 0.3);
}

.classroom-btn-generate {
  background: linear-gradient(135deg, #7B2D8E, #9B3DB0);
  color: white;
}

.classroom-btn-generate:hover {
  background: linear-gradient(135deg, #6A2580, #8A35A0);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(123, 45, 142, 0.3);
}

.classroom-mode-selector {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}

.classroom-mode-select,
.podcast-speaker-select {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  font-size: 0.78rem;
  background: white;
  color: #333;
  cursor: pointer;
}

.classroom-mode-select:focus,
.podcast-speaker-select:focus {
  outline: none;
  border-color: #7B2D8E;
}

.classroom-generating {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(123, 45, 142, 0.08);
  border-radius: 6px;
  font-size: 0.78rem;
  color: #7B2D8E;
}

.classroom-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(123, 45, 142, 0.2);
  border-top-color: #7B2D8E;
  border-radius: 50%;
  animation: classroom-spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes classroom-spin {
  to { transform: rotate(360deg); }
}

.classroom-progress-text {
  font-weight: 500;
}
</style>
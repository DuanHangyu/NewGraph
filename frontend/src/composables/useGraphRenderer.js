/**
 * useGraphRenderer - 可复用的 D3.js 图谱渲染逻辑
 *
 * 从 Process.vue 提取，供 QAGraph.vue 等页面复用。
 * 只包含 force-layout（全图视图），不包含 learning-path 分层布局。
 */
import * as d3 from 'd3'

// Graphiti entity type labels → fixed colors
const graphitiTypeColors = {
  Technology: '#004E89',
  Researcher: '#FF6B35',
  Organization: '#7B2D8E',
  Concept: '#1A936F',
  Application: '#C5283D',
}
const graphitiTypes = ['Technology', 'Researcher', 'Organization', 'Concept', 'Application']

// Edge color map (learning path edge types)
const edgeColorMap = {
  NEXT_STEP: '#2D3436',
  REQUIRES: '#7B2D8E',
  PREREQUISITE_OF: '#FF6B35',
  BRANCHES_FROM: '#7B2D8E',
  MERGES_TO: '#2D3436',
  BUILDS_ON: '#2D3436',
  ENABLES: '#7B2D8E',
  PARALLEL_WITH: '#999',
}
const learningEdgeTypes = new Set(Object.keys(edgeColorMap))

function getNodeType(labels) {
  if (!labels) return 'Entity'
  for (const t of graphitiTypes) {
    if (labels.includes(t)) return t
  }
  if (labels.includes('Project')) return 'Project'
  if (labels.includes('KnowledgePoint')) return 'KnowledgePoint'
  return 'Entity'
}

function getNodeRadius(node) {
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

function getNodeStrokeWidth(node) {
  if (node.labels?.includes('Project')) return 3
  return 2
}

function getEdgeColor(factType) {
  return edgeColorMap[factType] || '#ccc'
}

function needsArrow(factType) {
  return learningEdgeTypes.has(factType)
}

function isDashed(factType) {
  return factType === 'PARALLEL_WITH'
}

function isThickEdge(factType) {
  return factType === 'NEXT_STEP'
}

/**
 * 渲染图谱（force-layout 全图视图）
 */
export function renderGraph(svgEl, graphData, containerEl, options = {}) {
  const {
    onNodeClick,
    onEdgeClick,
    onBackgroundClick,
    heightOffset = 60,
    includeGlowFilter = false,
  } = options

  const rect = containerEl.getBoundingClientRect()
  const width = rect.width || 800
  const height = (rect.height || 600) - heightOffset

  if (width <= 0 || height <= 0) return null

  const svg = d3.select(svgEl)
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  svg.selectAll('*').remove()

  const nodesData = graphData.nodes || []
  const edgesData = graphData.edges || []

  if (nodesData.length === 0) {
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', height / 2)
      .attr('text-anchor', 'middle')
      .attr('fill', '#999')
      .text('暂无图谱数据')
    return null
  }

  // 节点映射
  const nodeMap = {}
  nodesData.forEach(n => { nodeMap[n.uuid] = n })

  // 构造 D3 节点/边
  const nodes = nodesData.map(n => ({
    id: n.uuid,
    name: n.name || '',
    type: getNodeType(n.labels),
    rawData: n,
  }))

  const nodeIds = new Set(nodes.map(n => n.id))

  const edges = edgesData
    .filter(e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid))
    .map(e => ({
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      type: e.fact_type || e.name || 'RELATED_TO',
      rawData: {
        ...e,
        source_name: nodeMap[e.source_node_uuid]?.name || '',
        target_name: nodeMap[e.target_node_uuid]?.name || '',
      },
    }))

  // 颜色
  const types = [...new Set(nodes.map(n => n.type))]
  const fallbackRange = ['#E9724C', '#2D3436', '#6C5CE7', '#FFD166', '#06D6A0', '#118AB2', '#EF476F', '#073B4C']
  const fallbackScale = d3.scaleOrdinal().domain(types.filter(t => !graphitiTypeColors[t])).range(fallbackRange)
  const colorScale = (type) => graphitiTypeColors[type] || fallbackScale(type)

  // 缩放
  const g = svg.append('g')
  svg.call(d3.zoom()
    .extent([[0, 0], [width, height]])
    .scaleExtent([0.2, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    }))

  // Defs
  const defs = svg.append('defs')

  // 箭头标记
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

  // 发光滤镜（QA 高亮用）
  if (includeGlowFilter) {
    const nodeGlow = defs.append('filter')
      .attr('id', 'node-glow')
      .attr('x', '-50%').attr('y', '-50%')
      .attr('width', '200%').attr('height', '200%')
    nodeGlow.append('feGaussianBlur')
      .attr('stdDeviation', '6')
      .attr('result', 'coloredBlur')
    const merge = nodeGlow.append('feMerge')
    merge.append('feMergeNode').attr('in', 'coloredBlur')
    merge.append('feMergeNode').attr('in', 'SourceGraphic')

    const edgeGlow = defs.append('filter')
      .attr('id', 'edge-glow')
      .attr('x', '-50%').attr('y', '-50%')
      .attr('width', '200%').attr('height', '200%')
    edgeGlow.append('feGaussianBlur')
      .attr('stdDeviation', '4')
      .attr('result', 'coloredBlur')
    const edgeMerge = edgeGlow.append('feMerge')
    edgeMerge.append('feMergeNode').attr('in', 'coloredBlur')
    edgeMerge.append('feMergeNode').attr('in', 'SourceGraphic')
  }

  // 脉冲搜索层（在节点下方，边的上方）
  g.append('g').attr('class', 'search-pulse-layer')

  // Force simulation
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
      onEdgeClick?.(d.rawData)
    })

  linkGroup.append('line')
    .attr('class', 'edge-line')
    .attr('stroke', d => getEdgeColor(d.type))
    .attr('stroke-width', d => isThickEdge(d.type) ? 2.5 : 1.5)
    .attr('stroke-opacity', 0.7)
    .attr('stroke-dasharray', d => isDashed(d.type) ? '5,5' : null)
    .attr('marker-end', d => needsArrow(d.type) ? `url(#arrow-${d.type})` : 'none')

  // 边上的流动光效层（初始隐藏）
  linkGroup.append('line')
    .attr('class', 'edge-flow')
    .attr('stroke', '#FFD700')
    .attr('stroke-width', 3)
    .attr('stroke-opacity', 0)
    .attr('stroke-linecap', 'round')
    .style('pointer-events', 'none')

  // 透明的宽线用于点击
  linkGroup.append('line')
    .attr('stroke', 'transparent')
    .attr('stroke-width', 10)

  // 边标签
  g.append('g')
    .attr('class', 'link-labels')
    .selectAll('text')
    .data(edges)
    .enter()
    .append('text')
    .attr('class', 'edge-label')
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
      onNodeClick?.(d.rawData, colorScale(d.type))
    })
    .call(d3.drag()
      .on('start', (event) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        event.subject.fx = event.subject.x
        event.subject.fy = event.subject.y
      })
      .on('drag', (event) => {
        event.subject.fx = event.x
        event.subject.fy = event.y
      })
      .on('end', (event) => {
        if (!event.active) simulation.alphaTarget(0)
        event.subject.fx = null
        event.subject.fy = null
      }))

  node.append('circle')
    .attr('r', d => getNodeRadius(d.rawData))
    .attr('fill', d => colorScale(d.type))
    .attr('fill-opacity', 1.0)
    .attr('stroke', '#fff')
    .attr('stroke-width', d => getNodeStrokeWidth(d.rawData))
    .attr('class', 'node-circle')

  // 光环层（初始半径 = 节点半径，不显示）
  node.append('circle')
    .attr('class', 'node-halo')
    .attr('r', d => getNodeRadius(d.rawData))
    .attr('fill', 'none')
    .attr('stroke', '#FFD700')
    .attr('stroke-width', 2)
    .attr('stroke-opacity', 0)
    .style('pointer-events', 'none')

  node.append('text')
    .attr('dx', d => getNodeRadius(d.rawData) + 4)
    .attr('dy', 4)
    .text(d => d.name?.substring(0, 12) || '')
    .attr('font-size', '11px')
    .attr('fill', '#333')
    .attr('font-family', 'JetBrains Mono, monospace')

  svg.on('click', () => {
    onBackgroundClick?.()
  })

  simulation.on('tick', () => {
    linkGroup.selectAll('.edge-line')
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    // 流动光效跟随
    linkGroup.selectAll('.edge-flow')
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    // 透明线跟随
    linkGroup.selectAll('line[stroke="transparent"]')
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    g.selectAll('.edge-label')
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2 - 5)

    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })

  return { simulation, svg, g, defs, width, height, nodes, edges }
}

// ============== 图谱遍历扫描动画 ==============

/**
 * 启动图谱遍历扫描动画
 *
 * 搜索阶段整个图谱持续活跃：
 * - 所有节点持续脉冲呼吸（大小微变 + 亮度微变）
 * - 随机节点不断被"选中"发出强烈蓝色闪光 + 光环
 * - 边持续流动光效（所有边都有微弱 dash 流动）
 * - 被选中节点的邻接边瞬间亮蓝
 * - 多条 BFS 路径高速并行推进
 * - 整体呈现"活体图谱正在被遍历"的视觉效果
 */
export function startSearchScan(svgEl, nodes, edges) {
  if (!nodes?.length) return { stop() {} }

  const svg = d3.select(svgEl)
  let running = true
  let animFrameId = null

  // ---- 1. 全局呼吸脉冲（所有节点持续微动） ----
  const breathPhase = nodes.map(() => Math.random() * Math.PI * 2) // 随机起始相位
  const allCircles = svg.selectAll('.node-circle')
  const allHalos = svg.selectAll('.node-halo')
  let breathStart = performance.now()

  function breathTick(now) {
    if (!running) return
    const t = (now - breathStart) / 1000 // 秒

    allCircles.each(function (d, i) {
      if (!d) return
      const r = getNodeRadius(d.rawData)
      const wave = Math.sin(t * 3.5 + breathPhase[i]) // 快速呼吸
      const scale = 1 + wave * 0.12 // ±12% 大小微变
      const brightShift = wave * 0.15
      d3.select(this)
        .attr('r', r * scale)
        .attr('fill-opacity', 0.85 + brightShift)
    })

    animFrameId = requestAnimationFrame(breathTick)
  }
  animFrameId = requestAnimationFrame(breathTick)

  // ---- 2. 全局边脉冲（实线 + 发光 + 亮度波动，不用虚线） ----
  const allEdgeLines = svg.selectAll('.edge-line')
  const allEdgeFlows = svg.selectAll('.edge-flow')
  const edgePhases = []
  allEdgeLines.each(function (d, i) {
    edgePhases.push(Math.random() * Math.PI * 2)
  })

  // 边亮度波动跟随呼吸帧一起跑
  const originalBreathTick = breathTick
  // 替换 breathTick，加上边的逻辑
  let _breathFn = null
  function combinedTick(now) {
    if (!running) return
    const t = (now - breathStart) / 1000

    // 节点呼吸
    allCircles.each(function (d, i) {
      if (!d) return
      const r = getNodeRadius(d.rawData)
      const wave = Math.sin(t * 3.5 + breathPhase[i])
      const scale = 1 + wave * 0.12
      const brightShift = wave * 0.15
      d3.select(this)
        .attr('r', r * scale)
        .attr('fill-opacity', 0.85 + brightShift)
    })

    // 边亮度脉冲（实线，高亮颜色，透明度在 0.4~0.75 之间波动）
    allEdgeLines.each(function (d, i) {
      const wave = Math.sin(t * 4 + edgePhases[i])
      const opacity = 0.55 + wave * 0.2 // 0.35~0.75
      d3.select(this)
        .attr('stroke', '#22D3EE')   // 电光青色
        .attr('stroke-opacity', opacity)
        .attr('stroke-width', 2 + wave * 0.5)
    })

    // edge-flow 层：每条边叠加一段短亮段流动
    allEdgeFlows.each(function (d, i) {
      if (!d) return
      const dx = (d.target.x || 0) - (d.source.x || 0)
      const dy = (d.target.y || 0) - (d.source.y || 0)
      const len = Math.sqrt(dx * dx + dy * dy) || 100
      // 短亮段（总长 20%），周期流动
      const segLen = len * 0.2
      const gapLen = len * 0.8
      const total = segLen + gapLen
      // 用时间驱动 offset
      const offset = -((t * 200 + i * 37) % total) // 速度 200px/s，每条边错开
      d3.select(this)
        .attr('stroke-dasharray', `${segLen} ${gapLen}`)
        .attr('stroke-dashoffset', offset)
        .attr('stroke-opacity', 0.85)
        .attr('stroke', '#06B6D4')    // 亮青色
        .attr('stroke-width', 3)
        .attr('stroke-linecap', 'round')
    })

    animFrameId = requestAnimationFrame(combinedTick)
  }
  // 取消之前的 breathTick，用 combinedTick
  cancelAnimationFrame(animFrameId)
  animFrameId = requestAnimationFrame(combinedTick)

  // ---- 3. 高速 BFS 闪光路径 ----
  const adjacency = {}
  nodes.forEach(n => { adjacency[n.id] = [] })
  edges.forEach(e => {
    const srcId = typeof e.source === 'string' ? e.source : e.source?.id
    const tgtId = typeof e.target === 'string' ? e.target : e.target?.id
    if (srcId && tgtId) {
      adjacency[srcId]?.push({ edge: e, neighbor: tgtId })
      adjacency[tgtId]?.push({ edge: e, neighbor: srcId })
    }
  })

  // 节点闪烁（覆盖呼吸状态）
  function flashNode(nodeId) {
    if (!running) return
    const circle = svg.selectAll('.node-circle').filter(d => d?.id === nodeId)
    const halo = svg.selectAll('.node-halo').filter(d => d?.id === nodeId)
    if (circle.empty()) return

    const r = getNodeRadius(circle.datum()?.rawData)

    // 强闪光
    circle
      .interrupt()
      .attr('fill', '#22D3EE')
      .attr('stroke', '#06B6D4')
      .attr('stroke-width', 3)
      .attr('fill-opacity', 1)
      .attr('r', r * 1.5)
      .transition()
      .duration(300)
      .ease(d3.easeBackOut)
      .attr('r', r * 1.15)
      .transition()
      .duration(250)
      .ease(d3.easeCubicOut)
      .attr('r', r)
      .attr('fill', d => d ? (graphitiTypeColors[d.type] || '#E9724C') : '#E9724C')
      .attr('stroke', '#fff')
      .attr('stroke-width', d => d ? getNodeStrokeWidth(d.rawData) : 2)
      .attr('fill-opacity', 0.85)

    // 光环
    if (!halo.empty()) {
      halo
        .interrupt()
        .attr('r', r)
        .attr('stroke', '#22D3EE')
        .attr('stroke-opacity', 0.9)
        .attr('stroke-width', 2.5)
        .transition()
        .duration(500)
        .ease(d3.easeCubicOut)
        .attr('r', r * 3)
        .attr('stroke-opacity', 0)
    }
  }

  // 边闪烁（高亮强闪光）
  function flashEdge(edgeData) {
    if (!running) return
    const uuid = edgeData.rawData?.uuid
    const el = svg.selectAll('.edge-line').filter(d => d?.rawData?.uuid === uuid)
    const flow = svg.selectAll('.edge-flow').filter(d => d?.rawData?.uuid === uuid)
    if (el.empty()) return

    // 底层边强亮
    el
      .interrupt()
      .attr('stroke', '#22D3EE')      // 电光青
      .attr('stroke-opacity', 1)
      .attr('stroke-width', 5)
      .attr('filter', 'url(#edge-glow)')
      .transition()
      .duration(600)
      .ease(d3.easeCubicOut)
      .attr('stroke', '#22D3EE')
      .attr('stroke-width', 2)
      .attr('filter', 'none')

    // flow 层也闪亮
    flow
      .interrupt()
      .attr('stroke-opacity', 1)
      .attr('stroke', '#67E8F9')      // 高亮浅青
      .attr('stroke-width', 4)
      .transition()
      .duration(600)
      .attr('stroke-opacity', 0.85)
      .attr('stroke', '#06B6D4')
      .attr('stroke-width', 3)
  }

  // BFS 路径（高速）
  function runPath(seedId) {
    if (!running) return
    const queue = [seedId]
    const seen = new Set()
    let step = 0

    function next() {
      if (!running || !queue.length || step > 8) {
        // 路径走完，立刻启动新路径
        if (running) {
          const newSeed = nodes[Math.floor(Math.random() * nodes.length)].id
          setTimeout(() => runPath(newSeed), 50)
        }
        return
      }
      const cur = queue.shift()
      if (seen.has(cur)) { next(); return }
      seen.add(cur)

      flashNode(cur)

      const nbrs = (adjacency[cur] || [])
        .filter(n => !seen.has(n.neighbor))
        .sort(() => Math.random() - 0.5)
        .slice(0, Math.random() > 0.5 ? 2 : 1)

      nbrs.forEach(({ edge, neighbor }, i) => {
        queue.push(neighbor)
        setTimeout(() => flashEdge(edge), 30 + i * 30)
      })

      step++
      setTimeout(next, 60 + Math.random() * 40) // 60-100ms，极快
    }
    next()
  }

  // 启动多条并行路径
  const pathCount = Math.min(Math.max(Math.ceil(nodes.length / 3), 3), 10)
  for (let i = 0; i < pathCount; i++) {
    const seed = nodes[Math.floor(Math.random() * nodes.length)].id
    setTimeout(() => runPath(seed), i * 80) // 路径间仅 80ms 错开
  }

  // ---- 4. 随机全局闪烁（每 200ms 随机亮几个节点） ----
  function randomSparkle() {
    if (!running) return
    const count = Math.max(2, Math.floor(nodes.length * 0.15))
    for (let i = 0; i < count; i++) {
      const n = nodes[Math.floor(Math.random() * nodes.length)]
      flashNode(n.id)
    }
  }
  const sparkleInterval = setInterval(() => {
    if (!running) { clearInterval(sparkleInterval); return }
    randomSparkle()
  }, 200)

  return {
    stop() {
      running = false
      if (animFrameId) cancelAnimationFrame(animFrameId)
      clearInterval(sparkleInterval)

      // 恢复所有节点/边到原始状态
      allCircles
        .interrupt()
        .transition().duration(300)
        .attr('r', d => d ? getNodeRadius(d.rawData) : 10)
        .attr('fill-opacity', 1)
        .attr('fill', d => d ? (graphitiTypeColors[d.type] || '#E9724C') : '#E9724C')
        .attr('stroke', '#fff')
        .attr('stroke-width', d => d ? getNodeStrokeWidth(d.rawData) : 2)

      allHalos
        .interrupt()
        .transition().duration(200)
        .attr('stroke-opacity', 0)

      allEdgeLines
        .interrupt()
        .transition().duration(400)
        .attr('stroke', d => d ? getEdgeColor(d.type) : '#ccc')
        .attr('stroke-opacity', 0.7)
        .attr('stroke-width', d => d ? (isThickEdge(d.type) ? 2.5 : 1.5) : 1.5)
        .attr('stroke-dasharray', d => d && isDashed(d.type) ? '5,5' : null)
        .attr('stroke-dashoffset', null)
        .attr('filter', 'none')

      allEdgeFlows
        .interrupt()
        .transition().duration(400)
        .attr('stroke-opacity', 0)
    },
  }
}

// ============== 图谱高亮（增强版） ==============

/**
 * 应用图谱高亮效果（QA 检索结果可视化）
 *
 * 包含：节点弹跳 + 光环扩散 + 边连线流动光效
 *
 * @param {SVGElement} svgEl - 原生 SVG DOM
 * @param {Set<string>} nodeUuids - 需要高亮的节点 UUID 集合
 * @param {Set<string>} edgeUuids - 需要高亮的边 UUID 集合（可选）
 */
export function applyHighlights(svgEl, nodeUuids, edgeUuids = new Set()) {
  const svg = d3.select(svgEl)
  const isClearing = nodeUuids.size === 0

  // ---- 节点：弹跳 + 发光 + 光环 ----
  svg.selectAll('.node-circle')
    .each(function (d) {
      if (!d) return
      const isHit = nodeUuids.has(d.id)
      const el = d3.select(this)

      if (isClearing) {
        // 恢复正常
        el.transition()
          .duration(600)
          .ease(d3.easeCubicOut)
          .attr('fill-opacity', 1.0)
          .attr('stroke-opacity', 1.0)
          .attr('stroke', '#fff')
          .attr('stroke-width', getNodeStrokeWidth(d.rawData))
          .attr('filter', 'none')
      } else if (isHit) {
        // 弹跳进入：先缩到 0 → 弹到 1.2 → 回到 1
        const r = getNodeRadius(d.rawData)
        el.attr('r', 0)
          .attr('filter', 'url(#node-glow)')
          .attr('stroke', '#FFD700')
          .attr('stroke-width', 4)
          .attr('fill-opacity', 1.0)
          .attr('stroke-opacity', 1.0)

        el.transition()
          .duration(400)
          .ease(d3.easeBackOut.overshoot(3))
          .attr('r', r * 1.25)
          .transition()
          .duration(200)
          .ease(d3.easeCubicOut)
          .attr('r', r)
      } else {
        // 非命中节点淡出
        el.transition()
          .duration(400)
          .attr('fill-opacity', 0.12)
          .attr('stroke-opacity', 0.12)
          .attr('stroke', '#fff')
          .attr('stroke-width', getNodeStrokeWidth(d.rawData))
          .attr('filter', 'none')
      }
    })

  // ---- 节点光环（命中节点发出扩散金色环） ----
  svg.selectAll('.node-halo')
    .each(function (d) {
      if (!d) return
      const isHit = nodeUuids.has(d.id)
      const halo = d3.select(this)

      if (isClearing || !isHit) {
        halo.transition().duration(400).attr('stroke-opacity', 0).attr('r', getNodeRadius(d.rawData))
      } else {
        // 光环从小扩散到大并淡出，重复 2 次
        const r = getNodeRadius(d.rawData)
        function animateHalo() {
          halo.attr('r', r)
            .attr('stroke-opacity', 0.8)
            .attr('stroke-width', 2.5)
            .transition()
            .duration(900)
            .ease(d3.easeCubicOut)
            .attr('r', r * 2.5)
            .attr('stroke-opacity', 0)
            .attr('stroke-width', 0.5)
        }
        animateHalo()
        // 第二波
        setTimeout(() => animateHalo(), 500)
      }
    })

  // ---- 节点标签透明度 ----
  svg.selectAll('.nodes > g > text')
    .transition()
    .duration(400)
    .attr('opacity', d => {
      if (isClearing) return 1.0
      return nodeUuids.has(d?.id) ? 1.0 : 0.12
    })

  // ---- 边：连线流动光效 ----
  svg.selectAll('.edge-line')
    .each(function (d) {
      if (!d) return
      const srcId = typeof d.source === 'string' ? d.source : d.source?.id
      const tgtId = typeof d.target === 'string' ? d.target : d.target?.id
      const uuid = d.rawData?.uuid
      const isHighlighted = edgeUuids.has(uuid) || (nodeUuids.has(srcId) && nodeUuids.has(tgtId))

      const el = d3.select(this)

      if (isClearing) {
        el.transition()
          .duration(600)
          .attr('stroke-opacity', 0.7)
          .attr('stroke-width', isThickEdge(d.type) ? 2.5 : 1.5)
          .attr('filter', 'none')
      } else if (isHighlighted) {
        el.transition()
          .duration(400)
          .attr('stroke-opacity', 0.9)
          .attr('stroke-width', 3)
          .attr('filter', 'url(#edge-glow)')
      } else {
        el.transition()
          .duration(400)
          .attr('stroke-opacity', 0.06)
          .attr('stroke-width', isThickEdge(d.type) ? 2.5 : 1.5)
          .attr('filter', 'none')
      }
    })

  // ---- 边流动光效（.edge-flow） ----
  svg.selectAll('.edge-flow')
    .each(function (d) {
      if (!d) return
      const srcId = typeof d.source === 'string' ? d.source : d.source?.id
      const tgtId = typeof d.target === 'string' ? d.target : d.target?.id
      const uuid = d.rawData?.uuid
      const isHighlighted = edgeUuids.has(uuid) || (nodeUuids.has(srcId) && nodeUuids.has(tgtId))

      const el = d3.select(this)

      if (isClearing || !isHighlighted) {
        // 停止动画，淡出
        el.interrupt()
          .transition()
          .duration(400)
          .attr('stroke-opacity', 0)
      } else {
        // 计算边的像素长度
        const dx = (d.target.x || 0) - (d.source.x || 0)
        const dy = (d.target.y || 0) - (d.source.y || 0)
        const len = Math.sqrt(dx * dx + dy * dy) || 100

        // 流动虚线：dash 长度 = 总长 30%，gap = 70%
        const dashLen = len * 0.3
        const gapLen = len * 0.7
        const totalDash = dashLen + gapLen

        el.attr('stroke-dasharray', `${dashLen} ${gapLen}`)
          .attr('stroke-dashoffset', totalDash)
          .attr('stroke-opacity', 0.8)

        // 流动动画循环
        function flowAnimation() {
          el.attr('stroke-dashoffset', totalDash)
            .transition()
            .duration(1200)
            .ease(d3.easeLinear)
            .attr('stroke-dashoffset', -dashLen)
            .on('end', flowAnimation)
        }
        flowAnimation()
      }
    })

  // ---- 边标签透明度 ----
  svg.selectAll('.edge-label')
    .transition()
    .duration(400)
    .attr('opacity', d => {
      if (isClearing) return 1.0
      const srcId = typeof d.source === 'string' ? d.source : d.source?.id
      const tgtId = typeof d.target === 'string' ? d.target : d.target?.id
      const uuid = d.rawData?.uuid
      const isHighlighted = edgeUuids.has(uuid) || (nodeUuids.has(srcId) && nodeUuids.has(tgtId))
      return isHighlighted ? 1.0 : 0.06
    })
}

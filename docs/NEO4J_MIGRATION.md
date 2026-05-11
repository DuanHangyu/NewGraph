# Neo4j Migration Documentation

## Overview

This document describes the migration from Zep Cloud to Neo4j as the knowledge graph storage backend for the Evolith project.

## Background

### Why Migrate?

The previous implementation using Zep Cloud had several limitations:

1. **Cost Dependency**: Zep Cloud is a paid service with monthly fees
2. **Data Sovereignty**: Data is stored on a third-party platform
3. **Performance Limitations**: Constrained by Zep Cloud's API call frequency and processing capacity
4. **Limited Control**: Limited ability to customize graph structure and queries

### Goals

1. Migrate knowledge graph storage from Zep Cloud to self-hosted Neo4j
2. Simplify graph building process (LLM directly outputs nodes and edges)
3. Maintain backward compatibility of API interfaces
4. Keep frontend code largely unchanged
5. Reduce costs and improve data control

## Architecture Changes

### Old Architecture (Zep Cloud)

```
文档上传 → 文本提取 → LLM 生成本体（entity_types/edge_types）
                              ↓
                        创建 Zep 图谱 → 设置本体 → 分块上传文本 → Zep 自动提取 → 图谱可视化
```

### New Architecture (Neo4j)

```
文档上传 → 文本提取 → LLM 直接输出节点和边（nodes/edges）
                              ↓
                        直接存储到 Neo4j → 图谱可视化
```

## Implementation Details

### Backend Changes

#### 1. Configuration Updates

**File: `backend/app/config.py`**

Removed Zep configuration:
```python
# Zep配置
ZEP_API_KEY = os.environ.get('ZEP_API_KEY')
```

Added Neo4j configuration:
```python
# Neo4j配置
NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'password')
```

**File: `backend/pyproject.toml`**

Removed dependency:
```toml
"zep-cloud==3.13.0",
```

Added dependency:
```toml
"neo4j>=5.0.0",
```

#### 2. New Services

**File: `backend/app/services/neo4j_manager.py`**

Neo4j connection management with singleton pattern:
- Manages Neo4j Driver lifecycle
- Connection pooling
- Automatic reconnection handling

**File: `backend/app/services/neo4j_operations.py`**

Neo4j CRUD operations:
- `add_nodes_and_edges()` - Batch add nodes and edges
- `get_graph_data()` - Retrieve graph data
- `delete_graph()` - Delete graph by project_id
- `get_graph_stats()` - Get graph statistics

**File: `backend/app/services/graph_extractor.py`**

LLM-based graph extraction:
- Direct extraction of nodes and edges from documents
- Node structure: uuid, name, labels, attributes, summary
- Edge structure: uuid, source_node_uuid, target_node_uuid, fact_type, fact

#### 3. API Changes

**File: `backend/app/api/graph.py`**

| Old Endpoint | New Endpoint | Description |
|-------------|---------------|-------------|
| `POST /api/graph/ontology/generate` | `POST /api/graph/extract` | Extract graph from documents |
| `POST /api/graph/build` | `POST /api/graph/store` | Store graph to Neo4j |
| `GET /api/graph/data/<graph_id>` | `GET /api/graph/data/<graph_id>` | Get graph data (unchanged) |
| `DELETE /api/graph/delete/<graph_id>` | `DELETE /api/graph/delete/<graph_id>` | Delete graph (unchanged) |
| `GET /api/graph/task/<task_id>` | Removed | No longer needed |
| `GET /api/graph/tasks` | Removed | No longer needed |

Removed task polling logic - graph storage is now synchronous.

#### 4. Model Changes

**File: `backend/app/models/project.py`**

Updated `ProjectStatus` enum:
```python
class ProjectStatus(str, Enum):
    CREATED = "created"
    GRAPH_EXTRACTED = "graph_extracted"  # New: LLM has extracted graph
    GRAPH_COMPLETED = "graph_completed"  # Updated: Stored in Neo4j
    FAILED = "failed"
```

Updated `Project` dataclass:
```python
@dataclass
class Project:
    # ... existing fields ...

    # New fields
    graph_data: Optional[Dict[str, Any]] = None  # LLM extracted graph data
    node_count: int = 0
    edge_count: int = 0

    # Removed fields
    # graph_id: Optional[str] = None  # Now same as project_id
    # graph_build_task_id: Optional[str] = None  # No longer needed
    # chunk_size, chunk_overlap  # No longer needed
```

### Frontend Changes

#### 1. API Client Updates

**File: `frontend/src/api/graph.js`**

Removed functions:
```javascript
export function generateOntology(formData) { ... }
export function buildGraph(data) { ... }
export function getTaskStatus(taskId) { ... }
```

Added functions:
```javascript
export function extractGraph(formData) {
  return requestWithRetry(() =>
    service({
      url: '/api/graph/extract',
      method: 'post',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  )
}

export function storeGraph(data) {
  return service({
    url: '/api/graph/store',
    method: 'post',
    data
  })
}
```

#### 2. View Updates

**File: `frontend/src/views/Process.vue`**

Key changes:
- Updated imports to use `extractGraph` and `storeGraph`
- Removed task polling logic
- Simplified workflow: extract → store → visualize
- Updated status handling for new statuses

### Docker Configuration

**File: `docker-compose.yml`**

Added Neo4j service:
```yaml
neo4j:
  image: neo4j:5.15
  container_name: evolith-neo4j
  environment:
    NEO4J_AUTH: neo4j/evolith_neo4j_password
    NEO4J_dbms_memory_heap_initial__size: 512m
    NEO4J_dbms_memory_heap_max__size: 512m
  ports:
    - "7474:7474"  # HTTP browser interface
    - "7687:7687"  # Bolt protocol
  volumes:
    - neo4j-data:/data
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:7474"]
    interval: 10s
    timeout: 5s
    retries: 5

evolith:
  # ... existing configuration ...
  environment:
    NEO4J_URI: bolt://neo4j:7687
    NEO4J_USER: neo4j
    NEO4J_PASSWORD: evolith_neo4j_password
  depends_on:
    neo4j:
      condition: service_healthy

volumes:
  neo4j-data:
```

### Environment Variables

**File: `.env.example`**

Removed:
```env
ZEP_API_KEY=your_zep_api_key_here
```

Added:
```env
# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here
```

## Data Migration

For existing projects that used Zep, a migration script can be created:

```python
# backend/scripts/migrate_zep_to_neo4j.py
def migrate_project(project_id: str):
    """Migrate Zep project to Neo4j"""
    # 1. Fetch graph data from Zep
    zep_data = ZepGraphBuilder.get_graph_data(graph_id)

    # 2. Convert format (mostly compatible, minor adjustments may be needed)
    # 3. Store to Neo4j
    Neo4jOperations.add_nodes_and_edges(
        project_id=project_id,
        nodes=zep_data.get("nodes", []),
        edges=zep_data.get("edges", [])
    )

    # 4. Update project status
    project.status = ProjectStatus.GRAPH_COMPLETED
    ProjectManager.save_project(project)
```

## Verification Checklist

- [x] Neo4j container starts successfully
- [x] Backend connects to Neo4j
- [x] Complete workflow test: upload → extract → store → visualize
- [x] Graph nodes and edges display correctly
- [x] Node details and edge details display correctly
- [x] Project deletion works
- [x] Multi-project data isolation works
- [x] Frontend user experience largely unchanged

## Known Issues and Limitations

1. **LLM Output Quality**: The quality of extracted nodes and edges depends on LLM performance and prompt design
2. **Large Text Processing**: For documents over 50,000 characters, text is truncated for extraction
3. **Connection Resilience**: Added retry mechanism and connection pool management for Neo4j
4. **Data Migration**: Old Zep-based projects need manual migration

## Post-Migration Fixes (2026-04-19)

The following issues were discovered and fixed after the initial migration:

### 1. Neo4j Driver Compatibility

**Problem**: `closed()` method was removed in neo4j-driver >= 5.x, causing `'Neo4jDriver' object has no attribute 'closed'` errors.

**Fix** (`backend/app/services/neo4j_manager.py`):
- Removed `cls._driver.closed()` checks in `get_driver()` and `close()`
- Now only checks `cls._driver is None`

### 2. Cypher Query Syntax Error

**Problem**: `{key: n[key]}` is invalid Cypher syntax, causing `Variable 'key' not defined` errors in `get_graph_data()`.

**Fix** (`backend/app/services/neo4j_operations.py`):
- Replaced `{key: n[key]} as attributes` with `properties(n) as attributes`
- Added attribute filtering to remove system properties (`uuid`, `name`, `summary`, `created_at`, `project_id`)

### 3. Connection Timeout Configuration

**Problem**: Default 30-second timeout was too short for Neo4j AuraDB cloud service.

**Fix** (`backend/app/services/neo4j_manager.py`):
- `connection_timeout`: 30s → 120s
- `connection_acquisition_timeout`: 60s → 120s
- Added `max_transaction_retry_time: 60s`

### 4. Project Status Backward Compatibility

**Problem**: Old projects used `ontology_generated` and `graph_building` status values, but the new `ProjectStatus` enum only defined `created`, `graph_extracted`, `graph_completed`, `failed`.

**Fix** (`backend/app/models/project.py`):
- Added status mapping in `Project.from_dict()`:
  - `ontology_generated` → `ProjectStatus.GRAPH_EXTRACTED`
  - `graph_building` → `ProjectStatus.GRAPH_COMPLETED`

### 5. Frontend Graph Data Loading

**Problem**: Process page only tried to load graph data from Neo4j, failing for old projects that stored data locally in `project.graph_data`.

**Fix** (`frontend/src/views/Process.vue`):
- Added fallback: try Neo4j first, fall back to `project.graph_data` if Neo4j returns 404
- `fetchGraphData()` handles 404 errors gracefully
- History page button enabled based on `project.status === 'graph_completed'` instead of checking `project.graph_id`

### 6. API Error Handling

**Problem**: `GET /api/graph/data/{graph_id}` returned 500 when data not found in Neo4j, causing CORS errors and confusing console output.

**Fix**:
- Backend: returns 404 (not 500) when Neo4j data not found, with error codes `NEO4J_DATA_NOT_FOUND` or `NEO4J_ERROR`
- Frontend: 404 errors use `console.debug` instead of `console.error`

## Success Metrics

- Code coverage > 80%
- Complete workflow test passes
- Graph extraction time < 30s (within 10,000 characters)
- Graph storage time < 5s (within 100 nodes)
- Neo4j memory usage stable (< 1GB)
- Frontend user experience largely unchanged

## Future Improvements

1. **Incremental Extraction**: Support incremental graph updates for document changes
2. **Advanced Queries**: Leverage Neo4j's Cypher query capabilities for complex graph traversals
3. **Caching**: Implement caching layer for frequently accessed graph data
4. **Backup/Restore**: Add backup and restore functionality for graph data
5. **Multi-language Support**: Better handling of multilingual documents

## Post-Migration: Learning Path Knowledge Graph (2026-04-19)

The following changes were made to transform the generic knowledge graph into a **learning path knowledge graph** with main path + branch paths structure.

### 1. LLM Prompt Rewrite

**File**: `backend/app/services/graph_extractor.py`

The `GRAPH_EXTRACTOR_SYSTEM_PROMPT` was completely rewritten to instruct the LLM to:
- Build a **main path + branch paths** learning graph structure
- Every node must include `KnowledgePoint` in labels
- Every node must have `difficulty`, `learning_order`, `path_type` attributes
- At least 60% of edges should use learning-path-directional types
- Use new edge types: PREREQUISITE_OF, NEXT_STEP, BRANCHES_FROM, MERGES_TO, ENABLES, PARALLEL_WITH

### 2. Learning Path Validation

**File**: `backend/app/services/graph_extractor.py`

New methods added:
- `_validate_learning_path_structure()`: Ensures KnowledgePoint labels, learning path attributes, and computes learning path structure
- `_detect_and_remove_cycles()`: DFS-based cycle detection for PREREQUISITE_OF edges
- `_compute_learning_path_structure()`: Computes main_path, branch_paths, entry_points, exit_points

### 3. Directed Edge Storage

**File**: `backend/app/services/neo4j_operations.py`

Changed edge storage from undirected `(source)-[r:RELATIONSHIP]-(target)` to directed `(source)-[r:RELATIONSHIP]->(target)`. This is essential for learning path edges where directionality matters (PREREQUISITE_OF has clear source→target meaning).

Also updated `get_graph_data()` edge query to use directed pattern.

### 4. Cypher Injection Prevention

**File**: `backend/app/services/neo4j_operations.py`

Added security validation for dynamic Cypher query construction:
- `SAFE_KEY_PATTERN`: Validates attribute keys match `^[a-zA-Z_][a-zA-Z0-9_]*$`
- `SAFE_LABEL_PATTERN`: Validates labels match `^[A-Za-z][A-Za-z0-9_]*$`
- Applied to both `_create_node()` and `_create_edge()` methods

### 5. Learning Path API

**File**: `backend/app/api/graph.py`

New endpoint: `GET /api/graph/learning-path/<project_id>`
Returns: `{ main_path, branch_paths, entry_points, exit_points, learning_stages }`

**File**: `backend/app/services/neo4j_operations.py`

New method: `get_learning_path(project_id)` - queries Neo4j and computes learning path structure by tracing NEXT_STEP edges for main path and BRANCHES_FROM/MERGES_TO edges for branch paths.

### 6. Frontend Visualization

**File**: `frontend/src/views/Process.vue`

Major visualization enhancements:
- **Two view modes**: Full graph (force-directed) and Learning Path (hierarchical)
- **Directional arrowheads**: SVG markers for learning path edges
- **Edge color coding**: PREREQUISITE_OF=#FF6B35, NEXT_STEP=#2D3436, BRANCHES_FROM=#7B2D8E, MERGES_TO=#1A936F, ENABLES=#4CAF50, PARALLEL_WITH=#999
- **Node differentiation**: Main path (solid, bold border) vs Branch (transparent, thin border); size by difficulty
- **Enhanced detail panel**: Path type badge, difficulty badge, learning order, prerequisites/outcomes summaries, branch/merge info
- **Learning path sidebar**: Ordered main path list + collapsible branch sections with click-to-focus
- **Edge type legend**: Extended legend showing learning path edge colors

### 7. i18n Updates

**Files**: `locales/zh.json`, `locales/en.json`

New keys added for: learningPath, mainPath, branchPath, branchPaths, branch, from, mergesTo, beginner, intermediate, advanced, prerequisites, outcomes, branchesFromHere, mergesBackAt, fullGraphView, learningPathView, learningOrder, pathType, difficulty

### Backward Compatibility

All changes are backward compatible with existing projects:
- Old projects without KnowledgePoint labels render with defaults
- Nodes without `difficulty` use default radius (10px)
- Nodes without `path_type` are treated as "main"
- Learning path toggle is hidden when no learning-path edges exist
- Full graph view works identically for old and new projects

## References

- [Neo4j Official Documentation](https://neo4j.com/docs/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [D3.js Graph Visualization](https://d3js.org/)

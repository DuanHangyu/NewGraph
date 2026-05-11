# Evolith Architecture & Implementation Details

> **数据模型详情**请参阅 [FEATURES.md](FEATURES.md) 第5节。
> **API端点详情**请参阅 [API.md](API.md)。
> **页面功能描述**请参阅 [FEATURES.md](FEATURES.md) 第2节。
> **OpenMAIC课堂集成**请参阅 [OPENMAIC_INTEGRATION.md](OPENMAIC_INTEGRATION.md)。

---

## Backend Architecture

**Flask Application Factory Pattern** (`app/__init__.py`):
- `create_app()` function initializes Flask app
- Registers blueprints: `/api/graph/*` and `/api/classroom/*` routes
- Enables CORS for API access
- Configures JSON to not escape Unicode (for Chinese character support)

**API Blueprints** (`app/api/`):
- `graph_bp` at `/api/graph` — 8 endpoints (extract, store, data, learning-path, project, project/list, project/delete, milestones)
- `classroom_bp` at `/api/classroom` — 3 endpoints (generate, status, cache). Generate endpoint supports `podcast_mode` param for dual-speaker audio. — see [OPENMAIC_INTEGRATION.md](OPENMAIC_INTEGRATION.md)
- `hint_bp` at `/api/hint` — 1 endpoint (generate). L1/L2 progressive hint generation for PBL workbench milestones.

**Services Layer** (`app/services/`):
- `GraphExtractor`: LLM-driven graph extraction with PBL ring knowledge path validation
- `Neo4jOperations`: Neo4j CRUD with Cypher injection prevention (`SAFE_KEY_PATTERN`, `SAFE_LABEL_PATTERN`). Includes `_flatten_milestones` for expanding milestone data into separate Milestone nodes + edges.
- `Neo4jManager`: Singleton driver lifecycle management
- `HintService`: L1/L2 hint generation for PBL milestones using LLM context
- `TextProcessor`: PDF/MD/TXT text extraction

**Models** (`app/models/`):
- `Project`: status tracking dataclass
- `ProjectStatus`: Enum — `CREATED`, `GRAPH_EXTRACTED`, `GRAPH_COMPLETED`, `FAILED`

**Utilities** (`app/utils/`):
- `LLMClient`: OpenAI SDK wrapper with JSON truncation repair, 600s timeout, JSON mode fallback
- `file_parser.py`: PDF (PyMuPDF), MD, TXT parsing
- `locale.py`: i18n (zh/en)
- `logger.py`: Dual-layer logging (see Logging System below)

## Frontend Architecture

**Vue 3 Composition API** with vue-router, vue-i18n, axios, d3.

**Pages**: Home.vue, History.vue, Process.vue, Classroom.vue, ProjectWorkbench.vue — see [FEATURES.md](FEATURES.md) for detailed descriptions.

**State**:
- `store/pendingUpload.js` — temporary upload data between Home and Process
- `store/progress.js` — localStorage-backed student progress tracking (milestone statuses, notes, hint history)

**API Client**: `frontend/src/api/graph.js` — 12 functions. See [API.md](API.md) for details.

## Data Flows

### Backend

1. **Graph Extraction** (`POST /api/graph/extract`): Files + course_description → TextProcessor → GraphExtractor → Project → project_id
2. **Graph Storage** (`POST /api/graph/store`): project_id → Neo4jOperations → status `graph_completed`
3. **Graph Retrieval** (`GET /api/graph/data/<graph_id>`): Neo4j → structured data for D3.js

### Frontend

1. **Home → Process**: pendingUpload store → `/process/new` → `extractGraph()` → `storeGraph()`
2. **Process (existing)**: `getProject()` → load graph from Neo4j (fallback to local `project.graph_data`)
3. **Graph Visualization**: Full graph (force-directed) + Learning Path (hierarchical). Interactive: drag, zoom, click for details.

## LLM Prompt Engineering

The extraction prompt (`GRAPH_EXTRACTOR_SYSTEM_PROMPT` in `graph_extractor.py`) produces PBL-driven graphs:
- **20-50 nodes**: 4-8 Project (`["Entity", "Project"]`) + 15-40 KnowledgePoint (`["Entity", "KnowledgePoint"]`) + 12-20 Milestone (`["Entity", "Milestone"]`)
- **30-80 edges**: NEXT_STEP, REQUIRES, PREREQUISITE_OF, MILESTONE_STEP, MILESTONE_REQUIRES
- **Milestone system**: Each Project has 3-5 Milestones via MILESTONE_STEP edges; each Milestone is linked to KnowledgePoints via MILESTONE_REQUIRES edges
- **Ring knowledge path**: Milestones provide natural project closure (no longer require ring-closing REQUIRES edges)

**Validation** (`_validate_learning_path_structure`):
- PBL mode: validates ring chains, no shared KPs
- Knowledge-driven mode (backward compat): ensures labels and attributes
- Cycle detection: DFS removes cycle-creating PREREQUISITE_OF edges

**Key config**: `max_tokens=16384`, `timeout=600s`, automatic JSON truncation repair

## Neo4j Integration

- Nodes: Entity + Project/KnowledgePoint/Milestone labels
- Edges: directed relationships (source→target) with RELATIONSHIP type, distinguished by `fact_type`
- Key edge types: `NEXT_STEP` (Project→Project), `REQUIRES` (Project→KnowledgePoint), `PREREQUISITE_OF` (KnowledgePoint→KnowledgePoint), `MILESTONE_STEP` (Project→Milestone), `MILESTONE_REQUIRES` (Milestone→KnowledgePoint)
- Milestone nodes: `name`, `description`, `acceptance_criteria`, `order`, `project_uuid` — created by `_flatten_milestones()` during graph storage
- KnowledgePoint nodes: `classroom_id` attribute cached after virtual classroom generation (enables "进入课堂" button in graph view)
- Multi-project isolation via `project_id`
- Cypher injection prevention: `SAFE_KEY_PATTERN` and `SAFE_LABEL_PATTERN`
- AuraDB connection resilience: `max_connection_lifetime=300s`, `update_node_attribute` has 2-attempt retry with driver reset on connection failure
- Learning Path API returns PBL mode or knowledge-driven mode — see [API.md](API.md) for response structure

## Configuration

**Backend** (`app/config.py`): `LLM_API_KEY/BASE_URL/MODEL_NAME`, `NEO4J_URI/USER/PASSWORD`, `OPENMAIC_BASE_URL`, `OPENMAIC_TIMEOUT=300`, `PODCAST_VOLCENGINE_APP_ID/ACCESS_KEY` (passed to OpenMAIC for podcast mode), `MAX_CONTENT_LENGTH=50MB`

**Frontend**: Default Vite config, API base `http://localhost:5001`, iframe URL via `VITE_OPENMAIC_BASE_URL`, backward compatible rendering

**For full setup guide** see [AURADB_SETUP.md](AURADB_SETUP.md) for Neo4j AuraDB, and `.env.example` for all env vars.

## Platform & Logging

### Windows
- `run.py` reconfigures UTF-8 for console
- Logs go to stderr (not stdout) to avoid Flask reloader capture

### Dual-layer Logging
- **Console** (stderr): `[HH:MM:SS] LEVEL: message`
- **File** (`backend/logs/YYYY-MM-DD.log`): `[timestamp] LEVEL [module:line] message`
- Levels: DEBUG (file only), INFO/WARNING/ERROR (console + file)
- Rotation: 10MB, 5 backups

## Known Behaviors (Backend)

1. **Backward compat**: Old projects render correctly with defaults (no KP labels → knowledge-driven mode)
2. **Edge reference warnings**: LLM may generate edges to nonexistent nodes; skipped with WARNING logs
3. **PREREQUISITE_OF cycle removal**: DFS-based; ensures DAG
4. **Status transitions**: CREATED → GRAPH_EXTRACTED → GRAPH_COMPLETED; any step can → FAILED
5. **Data migration**: Old `project.json` `graph_data` → frontend falls back when Neo4j returns 404
6. **Neo4j driver**: `max_connection_lifetime=300s` (AuraDB recommended), `connection_timeout=30s`, `connection_acquisition_timeout=30s`. `update_node_attribute` has 2-attempt retry with driver reset on first failure to handle AuraDB connection drops.
7. **Cypher fixes**: `properties(n)` instead of `{key: n[key]}`, `default_access_mode` on sessions
8. **Frontend error handling**: 404 → `console.debug` (not `console.error`)
9. **Podcast mode**: When `podcast_mode='podcast'` is passed to `/api/classroom/generate`, Evolith forwards `enablePodcast=true` + `podcastSpeakerPair` to OpenMAIC. OpenMAIC generates dual-speaker podcast audio instead of single-person TTS.
10. **JSONDecodeError handling**: Flask backend catches `ValueError` (includes JSONDecodeError) alongside HTTPError. Prevents Next.js dev server HMR returning HTML pages from causing 500 errors on status polling.
11. **classroom_id caching**: After virtual classroom generation, `classroom_id` is written back to the Neo4j KnowledgePoint node via `POST /api/classroom/cache`. This enables the graph view to show "进入虚拟课堂" instead of "生成虚拟课堂" for nodes with existing classrooms. Fire-and-forget from frontend — classroom navigation is not blocked on caching failure.
12. **Milestone fallback**: If LLM extraction doesn't produce milestone data (old projects), `_bulk_assign_kps()` distributes knowledge points evenly across milestones based on `learning_order`.
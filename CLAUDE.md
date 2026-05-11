# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Newgraph (Evolith / MiroFish) is a **multi-mode knowledge graph platform** combining PBL-driven learning path construction with Graphiti-based knowledge graph QA. It uses LLM-powered graph extraction and Neo4j for graph storage, integrates with OpenMAIC for AI virtual classrooms, and provides a KGQA (Knowledge Graph Question Answering) system via Graphiti hybrid search.

The project supports **two graph construction modes** that coexist in the same codebase:

1. **PBL Graph Extraction** — Upload course documents → LLM extracts PBL learning path graph (Projects, KnowledgePoints, Milestones) → Store in Neo4j → Visualize with D3.js → Generate virtual classrooms via OpenMAIC
2. **Graphiti KGQA** — Import preset datasets or upload files → Graphiti SDK auto-extracts entities (Technology, Researcher, Organization, Concept, Application) and relationships → Hybrid search (vector + graph traversal) + LLM generation for QA

---

## Development Commands

```bash
# Setup
npm run setup:all       # All dependencies (root + frontend + backend)
npm run setup           # Node dependencies only
npm run setup:backend   # Python dependencies (creates .venv with uv)

# Running
npm run dev:all         # Backend + frontend + OpenMAIC
npm run dev             # Backend + frontend only (no OpenMAIC)
npm run frontend        # Frontend only (http://localhost:3000)
npm run backend         # Backend only (http://localhost:5001)
npm run build           # Production build

# Backend
cd backend && uv run python run.py   # Flask server
cd backend && uv run pytest          # Tests
```

**OpenMAIC (sister project)**: `F:\AI Projects\OpenMAIC` — AI virtual classroom engine (Next.js + React). When working on cross-origin iframe, audio, or classroom issues, you may need to read/edit code in both projects.

**OpenMAIC path resolution**: `npm run dev:all` searches `OPENMAIC_DIR` env var → `.env` entry → `../OpenMAIC` sibling dir (default: `F:\AI Projects\OpenMAIC`).

**Configuration**: Copy `.env.example` to `.env`. Key env vars:
- `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME` — LLM config (OpenAI-compatible format, default: DashScope qwen-plus)
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` — Neo4j connection (local or AuraDB)
- `OPENMAIC_BASE_URL`, `OPENMAIC_TIMEOUT` — OpenMAIC virtual classroom
- `LLM_BOOST_API_KEY`, `LLM_BOOST_BASE_URL`, `LLM_BOOST_MODEL_NAME` — Optional faster LLM for specific tasks

---

## Project Structure

```
Newgraph/
├── backend/                    # Flask API server (Python)
│   ├── app/
│   │   ├── api/                # Route blueprints
│   │   │   ├── graph.py        # /api/graph/* — PBL extraction, storage, data, learning paths, milestones
│   │   │   ├── classroom.py    # /api/classroom/* — OpenMAIC integration (generate, status, cache)
│   │   │   ├── hint.py         # /api/hint/* — Learning hint generation (L1 brief, L2 detailed)
│   │   │   ├── qa.py           # /api/qa/* — KGQA (ask, ask-stream SSE, history CRUD)
│   │   │   └── data.py         # /api/data/* — Dataset import (presets, upload, ingest-status)
│   │   ├── models/
│   │   │   ├── project.py      # Project dataclass + ProjectManager (JSON file persistence)
│   │   │   ├── qa_session.py   # QASessionManager (JSON file persistence)
│   │   │   └── task.py
│   │   ├── services/
│   │   │   ├── graph_extractor.py   # PBL graph extraction via LLM (Projects, KPs, Milestones)
│   │   │   ├── graphiti_service.py  # Graphiti SDK wrapper (entity types, search, episode ingest)
│   │   │   ├── qa_service.py        # QA pipeline: Graphiti search → context assembly → LLM generate
│   │   │   ├── hint_service.py      # Milestone hint generation (L1/L2 prompts)
│   │   │   ├── neo4j_operations.py  # Neo4j CRUD (nodes, edges, learning paths, milestones)
│   │   │   ├── neo4j_manager.py     # Neo4j driver singleton
│   │   │   ├── data_loader.py       # Chinese text chunking + dataset import orchestration
│   │   │   └── text_processor.py    # Text normalization
│   │   ├── utils/
│   │   │   ├── llm_client.py        # OpenAI-compatible LLM client (JSON mode, auto-repair truncated JSON)
│   │   │   ├── async_bridge.py      # AsyncBridge singleton (asyncio loop in background thread for Flask)
│   │   │   ├── file_parser.py       # PDF/MD/TXT file parser with multi-encoding fallback
│   │   │   ├── locale.py            # i18n helper (Accept-Language header → locale)
│   │   │   ├── logger.py            # Logging setup
│   │   │   └── retry.py             # Retry utility
│   │   └── config.py                # Config class (env vars + validation)
│   ├── data/datasets/               # Preset datasets directory (ai_fundamentals, ai_frontier, quantum_computing)
│   └── run.py
├── frontend/                   # Vue 3 SPA
│   └── src/
│       ├── views/
│       │   ├── Home.vue             # Landing page: dataset selection + document upload
│       │   ├── History.vue          # Project list
│       │   ├── Process.vue          # Graph visualization (D3.js force layout + learning path)
│       │   ├── Classroom.vue        # OpenMAIC virtual classroom (iframe)
│       │   ├── ProjectWorkbench.vue # PBL workbench (milestones + hints + knowledge points)
│       │   ├── QA.vue               # Simple QA chat interface
│       │   ├── QAGraph.vue          # Split view: graph + QA chat side by side
│       │   └── DatasetManager.vue   # Dataset management (presets + custom upload)
│       ├── components/
│       │   ├── GraphPanel.vue       # Reusable D3.js graph panel
│       │   ├── HintPanel.vue        # Learning hint display
│       │   └── LanguageSwitcher.vue # i18n language toggle
│       ├── composables/
│       │   └── useGraphRenderer.js  # Shared D3.js force-layout rendering logic
│       ├── api/
│       │   ├── index.js             # Axios instance with interceptors and retry
│       │   └── graph.js             # All API client functions
│       ├── store/
│       │   ├── pendingUpload.js     # Upload state
│       │   └── progress.js          # Student learning progress (localStorage-backed)
│       ├── i18n/                    # Internationalization
│       └── router/index.js          # Vue Router config (8 routes)
└── .env
```

---

## API Endpoints

### Graph (`/api/graph`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/extract` | Upload files + course description → LLM extracts PBL graph |
| POST | `/store` | Store extracted graph to Neo4j |
| GET | `/data/<graph_id>` | Get graph data (PBL schema) |
| GET | `/graphiti-data/<group_id>` | Get graph data (Graphiti schema) |
| GET | `/learning-path/<project_id>` | Get structured learning path |
| GET | `/milestones/<project_id>` | Get milestones with knowledge points |
| GET | `/project/<project_id>` | Get project details |
| GET | `/project/list` | List all projects |
| DELETE | `/project/<project_id>` | Delete project |
| POST | `/project/<project_id>/reset` | Reset project to initial state |
| DELETE | `/delete/<graph_id>` | Delete graph from Neo4j |

### Classroom (`/api/classroom`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate` | Generate virtual classroom for knowledge point (via OpenMAIC) |
| GET | `/status/<job_id>` | Poll classroom generation status |
| POST | `/cache` | Cache classroom_id to Neo4j node |

### Hint (`/api/hint`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate` | Generate L1 (brief) or L2 (detailed) learning hint for milestone |

### QA (`/api/qa`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ask` | Ask question (non-streaming) |
| POST | `/ask-stream` | Ask question (SSE streaming) |
| GET | `/history/<session_id>` | Get session history |
| DELETE | `/history/<session_id>` | Clear session |

### Data (`/api/data`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/presets` | List preset datasets |
| POST | `/ingest` | Import preset dataset (async) |
| POST | `/upload` | Upload custom files (async) |
| GET | `/ingest-status/<project_id>` | Poll import progress |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |

---

## Key Architectural Details

### Two-Mode Graph Storage in Neo4j

- **PBL mode**: Nodes use labels `Entity:Project`, `Entity:KnowledgePoint`, `Entity:Milestone`. Edges use `RELATIONSHIP` with `fact_type` (NEXT_STEP, REQUIRES, PREREQUISITE_OF, MILESTONE_STEP, MILESTONE_REQUIRES). Data isolated by `project_id` property.
- **Graphiti mode**: Uses Graphiti SDK's native schema (EntityNode, EntityEdge). Entities typed as Technology, Researcher, Organization, Concept, Application. Data isolated by `group_id`.

### AsyncBridge

Graphiti SDK is fully async; Flask is synchronous. `AsyncBridge` runs a persistent asyncio event loop in a background thread, exposing `AsyncBridge.run(coro)` for Flask routes to call async code synchronously.

### LLM Client

`LLMClient` wraps OpenAI-compatible API calls. Supports JSON mode with auto-repair for truncated JSON responses (bracket counting + closure). Configurable via `LLM_BOOST_*` env vars for faster models on specific tasks.

### QA Pipeline

Three-stage pipeline: (1) Graphiti hybrid search (vector similarity + graph traversal) → (2) Context assembly (entities + relationships as structured markdown) → (3) LLM generation with source citations. Supports both non-streaming and SSE streaming responses.

### Project Persistence

Projects stored as JSON files in `backend/uploads/projects/<project_id>/project.json`. QA sessions stored in `backend/uploads/qa_sessions/<session_id>.json`. No database for metadata — only Neo4j for graph data.

### Frontend Graph Rendering

`useGraphRenderer.js` is a shared composable for D3.js force-directed layout. Supports both PBL node types (Project, KnowledgePoint, Milestone) and Graphiti entity types (Technology, Researcher, Organization, Concept, Application) with distinct color coding.

---

## Skill Routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review
- Save progress, checkpoint, resume → invoke checkpoint
- Code quality, health check → invoke health

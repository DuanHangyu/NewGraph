# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Evolith (MiroFish) is a **PBL-driven learning path knowledge graph + virtual classroom** platform. It uses LLM-powered graph extraction and Neo4j for graph storage, and integrates with OpenMAIC to generate immersive AI virtual classrooms for each knowledge point.

**Core workflow**: Upload course documents → Describe the course → LLM extracts PBL-driven learning path graph → Store in Neo4j → Visualize with D3.js → Generate virtual classrooms for knowledge points via OpenMAIC. Classrooms can optionally use podcast mode (dual-speaker audio via Volcengine Podcast TTS API) instead of single-person TTS.

**Key design**: Projects form the main path; each project has an exclusive **ring knowledge path** (Project → KPs → same Project). Knowledge points can spawn virtual AI classrooms for hands-on learning.

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

**OpenMAIC (sister project)**: `F:\AI Projects\OpenMAIC` — the AI virtual classroom engine (Next.js + React) that Evolith integrates with. When working on cross-origin iframe, audio, or classroom-related issues, you will need to read/edit code in both projects.

**OpenMAIC path for startup**: `npm run dev:all` searches `OPENMAIC_DIR` env var → `.env` entry → `../OpenMAIC` sibling dir (default resolves to `F:\AI Projects\OpenMAIC`).

**Configuration**: Copy `.env.example` to `.env`. Key env vars: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `OPENMAIC_BASE_URL`, `OPENMAIC_TIMEOUT`, `PODCAST_VOLCENGINE_APP_ID`, `PODCAST_VOLCENGINE_ACCESS_KEY` (for podcast mode, passed to OpenMAIC).

---

## Project Structure

```
Evolith/
├── backend/          # Flask API server
│   ├── app/
│   │   ├── api/      # Routes (graph_bp, classroom_bp)
│   │   ├── models/   # Project, ProjectStatus
│   │   ├── services/ # GraphExtractor, Neo4jOperations, Neo4jManager, TextProcessor
│   │   ├── utils/    # LLMClient, file_parser, locale, logger
│   │   ├── config.py
│   │   └── __init__.py
│   └── run.py
├── frontend/         # Vue 3 SPA
│   └── src/
│       ├── views/    # Home, History, Process, Classroom
│       ├── api/      # graph.js (API client)
│       ├── store/    # pendingUpload.js
│       └── i18n/
├── docs/             # Detailed documentation (see below)
└── .env
```

---

## Detailed Documentation

Each doc file has a single, non-overlapping responsibility:

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — Code architecture, data flows, LLM prompt, Neo4j, config, logging, backend known behaviors
- **[docs/API.md](docs/API.md)** — Complete API endpoint reference (request/response examples, error codes, frontend client, changelog)
- **[docs/FEATURES.md](docs/FEATURES.md)** — Product features, page descriptions, data models, tech stack, user workflows, user-side limitations
- **[docs/OPENMAIC_INTEGRATION.md](docs/OPENMAIC_INTEGRATION.md)** — Cross-origin iframe, OpenMAIC APIs, audio architecture, classroom frontend, classroom known behaviors
- **[docs/NEO4J_MIGRATION.md](docs/NEO4J_MIGRATION.md)** — Zep → Neo4j migration history (archived)
- **[docs/AURADB_SETUP.md](docs/AURADB_SETUP.md)** — Neo4j AuraDB cloud setup guide
- **[docs/PBL-graph-redesign.md](docs/PBL-graph-redesign.md)** — PBL ring knowledge path design notes (implemented, archived)

---

## Skill routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.

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
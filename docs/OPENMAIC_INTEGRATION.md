# OpenMAIC Virtual Classroom Integration

**Last Updated:** 2026-04-27

> **Evolith代理API端点**（POST /api/classroom/generate、GET /api/classroom/status、POST /api/classroom/cache）的完整请求/响应文档请参阅 [API.md](API.md) 第10-12节。
> **前端API客户端函数**（generateClassroom、getClassroomStatus、cacheClassroomId）请参阅 [API.md](API.md) 前端API客户端章节。

---

Evolith (MiroFish) and OpenMAIC are two separate projects that integrate to provide virtual classroom functionality. Evolith is the knowledge graph front-end (Vue 3 + Flask), and OpenMAIC is the AI classroom generation engine (Next.js + React). They communicate via HTTP APIs and embed via cross-origin iframe.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│ Evolith (port 3000/5001)                                 │
│                                                          │
│  Vue 3 Frontend ──proxy──▶ Flask Backend ──HTTP───────▶ │   OpenMAIC (port 3001)
│  ┌──────────────┐       ┌──────────────┐         ┌──────────────────────┐
│  │ Process.vue  │       │ classroom.py │────────▶│/api/generate-classroom│
│  │ Classroom.vue│       │              │         │/{jobId} (status poll) │
│  │  (iframe)    │       │              │────────▶│/api/classroom (GET)   │
│  └──────────────┘       └──────────────┘         │                       │
│         │                    │                    │  Classroom viewer page │
│         │  iframe embed      │  Neo4j cache       │  /classroom/{id}       │
│         ▼                    ▼                    │                       │
│  ┌─────────────────────────────────────────────▶ │                       │
│  │ <iframe src="OpenMAIC/classroom/{id}">      ││                       │
│  │   allow="microphone; camera; autoplay 'src'" │                       │
│  └──────────────────────────────────────────────┘───────────────────────┘
│                                                          │
│  ┌─ Podcast Mode Flow ─────────────────────────────────────────────────┐
│  │ Process.vue → classroom.py (podcast_mode='podcast')                │
│  │   → OpenMAIC /api/generate-classroom {enablePodcast:true}          │
│  │   → podcast-generation.ts → Volcengine WebSocket (SAMI binary)     │
│  │   → embedPodcastAudioInScenes → PodcastPlayer (AudioContext)       │
│  └────────────────────────────────────────────────────────────────────┘
│                                                          │
│  Vite dev server:                                        │
│    Permissions-Policy: autoplay=(self "http://localhost:3001")
│    /api → proxy → Flask:5001                             │
│                                                          │
│  Neo4j: classroom_id cached on KnowledgePoint nodes     │
└──────────────────────────────────────────────────────────┘
```

## User Flow

1. Click KnowledgePoint node in Process.vue — or click KP card / "进入虚拟课堂" button in ProjectWorkbench
2. If `classroom_id` exists in Neo4j → green button → navigate to `/classroom/{id}`
3. If no `classroom_id` → purple/orange button → Evolith backend → proxy to OpenMAIC → poll → cache to Neo4j → navigate
4. Classroom.vue → embeds OpenMAIC `/classroom/{id}` page in iframe with `allow="microphone; camera; autoplay 'src'"`
5. OpenMAIC loads classroom data (IndexedDB first, then server API fallback) → client-side TTS fallback if needed → renders Stage with audio

## Evolith Backend Processing

The Flask backend (`app/api/classroom.py`) proxies to OpenMAIC:
- **Generate**: Check Neo4j cache → if cached, return `ready` → fetch node details → assemble `requirement` string → POST to OpenMAIC with `{ requirement, enableTTS: true, enablePodcast, podcastSpeakerPair }` → map `jobId`→`job_id`, `pollIntervalMs`→`poll_interval_ms`. `podcast_mode` param: None = 课堂模式 (classroom mode), `'podcast'` = 播客模式 (podcast mode). When podcast, passes `enablePodcast: true` and `podcastSpeakerPair` (e.g. `'mizai-dayi'`) to OpenMAIC.
- **Status**: Proxy OpenMAIC `GET /api/generate-classroom/{jobId}` → map statuses: `succeeded`→`completed`, `queued/running`→`processing`, `failed`→`failed`. Error handling catches `HTTPError`, `ValueError` (covers `JSONDecodeError` from Next.js dev server HMR returning HTML), `Timeout`, `ConnectionError`.
- **Cache**: Write `classroom_id` to Neo4j node attribute via `update_node_attribute` (with 2-attempt retry + driver reset for AuraDB connection resilience)

## OpenMAIC Direct API Endpoints

These are OpenMAIC's own APIs, accessed directly by OpenMAIC client-side code (not proxied through Evolith).

### POST `/api/generate-classroom`

**Request** (`GenerateClassroomInput`):
```json
{
  "requirement": "string (required)",
  "pdfContent": { "text": "...", "images": ["..."] },
  "enableWebSearch": false,
  "enableImageGeneration": false,
  "enableVideoGeneration": false,
  "enableTTS": true,
  "enablePodcast": false,
  "podcastSpeakerPair": "mizai-dayi | liufei-xiaolei",
  "agentMode": "default | generate"
}
```

Evolith currently sends `{ requirement: "...", enableTTS: true }` for classroom mode, or `{ requirement: "...", enablePodcast: true, podcastSpeakerPair: "mizai-dayi" }` for podcast mode (TTS is skipped when podcast succeeds).

**Response** (202 Accepted):
```json
{ "success": true, "data": { "jobId": "nanoid(10)", "status": "queued", "step": "queued", "message": "...", "pollUrl": "...", "pollIntervalMs": 5000 } }
```

### GET `/api/generate-classroom/{jobId}` (polling)

**Raw response fields**: `jobId`, `status` (`queued|running|succeeded|failed`), `step` (initializing|researching|generating_outlines|generating_scenes|generating_media|generating_podcast|generating_tts|persisting), `progress` (0-100), `message`, `pollIntervalMs`, `scenesGenerated`, `totalScenes`, `result` (`{ id, url, classroomId }`), `error`, `done` (boolean). Podcast step occurs at progress 92%, between `generating_media` and `generating_tts`.

### GET `/api/classroom?id={classroomId}`

Retrieve completed classroom JSON:
```json
{
  "success": true,
  "classroom": {
    "stage": { "id", "name", "description", "languageDirective", "agentIds", "generatedAgentConfigs", "style" },
    "scenes": [{ "id", "type", "order", "content", "actions", "whiteboards" }]
  }
}
```

### GET `/api/classroom-media/{classroomId}/audio/{filename}`

Serve server-generated TTS audio. Supported: `.mp3`, `.wav`, `.ogg`, `.aac` + image/video. Path traversal blocked. Allowed subdirs: `media/`, `audio/`, `podcast/`. Streamed. Podcast files served from `data/classrooms/{id}/podcast/` as `/api/classroom-media/{classroomId}/podcast/{filename}`.

## Frontend Implementation

### Process.vue - Classroom Generation Flow

**Classroom button** (only for KnowledgePoint nodes):
- Has `classroom_id` → green button → `openClassroom(classroomId)` directly
- No `classroom_id` → purple button → generation flow
- During generation → spinner with progress percentage

**Generation flow** (`generateClassroomForNode`):
1. `generateClassroom({ project_id, node_uuid })` → Evolith backend
2. `status === 'ready'` → cached, navigate directly
3. `status === 'generating'` → save job to sessionStorage → `startClassroomPolling()`
4. Polling: `getClassroomStatus(jobId)` every `pollIntervalMs` ms → on `completed`: `cacheClassroomId()` + navigate → on `failed`: alert. Retry logic: `MAX_POLL_RETRIES=3` — a single transient 500 no longer kills polling; retries up to 3 times before marking as failed.
5. `resumeClassroomGenerationIfPending()` in `onMounted`: checks sessionStorage for pending job → restores state → resumes polling (handles HMR/page reload)

**sessionStorage key** (`evolith_classroom_job`): stores `{ job_id, project_id, node_uuid, poll_interval_ms }`. Cleared on completion/failure/error. Closing tab clears it (sessionStorage, not localStorage).

### ProjectWorkbench.vue - Classroom Generation Flow

**Entry points** (two):
1. KP card button: each knowledge point card has a button — "生成虚拟课堂" (orange, no classroom_id) or "进入虚拟课堂" (green, has classroom_id)
2. HintPanel L3: after L1→L2 progressive hints, "我要课堂" button triggers `request-classroom` emit

**Generation flow** (`handleClassroomRequest`):
1. `generateClassroom({ project_id, node_uuid: kpUuid })` → Evolith backend
2. `status === 'ready'` → navigate directly
3. `status === 'generating'` → `startClassroomPolling(jobId, kpName, kpUuid)`

**Polling** (`startClassroomPolling`):
- Uses `setTimeout` recursive polling (not `setInterval`), every 5 seconds
- **No timeout limit** — polls indefinitely until `completed` or `failed`
- On `completed`: fire-and-forget `cacheClassroomId()` + `refreshMilestones()` + navigate
- Transient errors: continue polling (no retry limit)
- `kpUuid` is passed from the initial request, used for `cacheClassroomId` call

**Difference from Process.vue**: Process.vue uses `setInterval` with `MAX_POLL_RETRIES=3` for transient errors. Workbench uses `setTimeout` with no retry limit. Workbench also calls `refreshMilestones()` after completion to update KP card state (orange→green).

### Classroom.vue - Iframe Page

- 48px navbar (back button + node name + connection status indicator) + iframe
- iframe `src`: `{OPENMAIC_BASE_URL}/classroom/{classroomId}`
- iframe `allow="microphone; camera; autoplay 'src'"` — delegates autoplay permission
- Loading spinner, 10-second auto-hide timeout
- Connection status: connecting (yellow) → connected (green) on iframe load → error (red)
- `VITE_OPENMAIC_BASE_URL` env var (default: `http://localhost:3001`)
- Router: `/classroom/:classroomId` with `project_id` and `node_name` query params

## OpenMAIC Classroom Viewer (`app/classroom/[id]/page.tsx`)

1. **Load data**: IndexedDB → server API fallback
2. **Hydrate agents**: Server-generated agent configs → IndexedDB + registry
3. **Restore media**: Media generation tasks from IndexedDB
4. **Client-side TTS fallback**: For actions missing `audioUrl` → assign `audioId`, check IndexedDB cache, generate in batches of 3
5. **Restore agent config**: Auto mode (generated) or Preset mode (saved `agentIds`)
6. **Auto-resume**: If pending outlines exist, resume via sessionStorage

## Cross-Origin iframe Integration Requirements

Four coordinated settings are required for audio playback in the cross-origin iframe:

### 1. OpenMAIC: CSP Headers (`next.config.ts`)

```env
ALLOWED_FRAME_ANCESTORS=http://localhost:3000
```

Sets `Content-Security-Policy: frame-ancestors 'self' http://localhost:3000` and removes `X-Frame-Options: SAMEORIGIN`.

### 2. Evolith: Permissions-Policy Header (`vite.config.js`)

```javascript
headers: { 'Permissions-Policy': 'autoplay=(self "http://localhost:3001")' }
```

Origins must be quoted per RFC 9110. Grants autoplay permission to OpenMAIC's iframe origin.

### 3. Evolith: iframe allow Attribute (`Classroom.vue`)

```html
<iframe allow="microphone; camera; autoplay 'src'" ...>
```

Without `'src'`, cross-origin content inside the iframe can't use the permission.

### 4. OpenMAIC: AudioContext Unlock Pattern (`audio-player.ts` + `stage.tsx`)

- **AudioContext path** (primary): `AudioContext` + `GainNode` + `AudioBufferSourceNode`. Must be unlocked via user gesture (`unlock()` → `AudioContext.resume()`, must be awaited). Works in cross-origin iframes.
- **HTMLAudioElement path** (fallback): Standard `<audio>` element. FAILS in cross-origin iframes because async operations break user gesture chain before `play()`.

The `unlock()` call must be awaited. Without await → AudioContext "suspended" → HTMLAudioElement fallback → silent failure.

### Server-side TTS (`enableTTS: true`)

Evolith sends `enableTTS: True`. Audio files written to `data/classrooms/{id}/audio/`, `audioUrl` set to `/api/classroom-media/{id}/audio/{filename}`.

### Client-side TTS Fallback

For classrooms without server-side audio: on-demand generation in browser, cached in IndexedDB. First visit ~20-30s (batched 3), subsequent visits instant.

## Podcast Mode (Dual-Speaker Audio)

When `podcast_mode='podcast'` is specified, OpenMAIC generates a continuous dual-speaker podcast audio for each scene instead of individual per-action TTS clips. The podcast uses the Volcengine Podcast TTS API with WebSocket SAMI binary protocol.

### Architecture Overview

```
Evolith classroom.py (podcast_mode='podcast')
  → OpenMAIC /api/generate-classroom { enablePodcast: true, podcastSpeakerPair }
    → Classroom pipeline: after media generation, before TTS
      → podcast-generation.ts: collect SpeechActions → map agents to speakers
        → podcast-client.ts: WebSocket wss://openspeech.bytedance.com/api/v3/sami/podcasttts
          → Volcengine SAMI binary protocol (action=3, scripted mode)
            → nlp_texts: [{ speaker: "host_a", text: "..." }, { speaker: "host_b", text: "..." }]
            → Response: binary audio chunks → decode → save MP3
      → embedPodcastAudioInScenes: replace all SpeechActions with PodcastAction per scene
        → podcast-player.ts (client): AudioContext + timeline-based round tracking
          → subtitle/avatar sync via round metadata
```

### Volcengine Podcast TTS API

- **Endpoint**: `wss://openspeech.bytedance.com/api/v3/sami/podcasttts`
- **Protocol**: SAMI binary over WebSocket, action=3 (scripted mode)
- **Input**: `nlp_texts` array with `{ speaker, text }` per round. Single round must be <=300 chars, total <=10,000 chars.
- **Speaker pairs** (configured via `podcastSpeakerPair` param):
  - `'mizai-dayi'` — 咪仔同学 (host_a) + 大意先生 (host_b)
  - `'liufei-xiaolei'` — 刘飞 (host_a) + 潇磊 (host_b)
- **Env vars**: `PODCAST_VOLCENGINE_APP_ID`, `PODCAST_VOLCENGINE_ACCESS_KEY`

### Agent-to-Speaker Mapping

Within `podcast-generation.ts`, agents are mapped to podcast speakers:
- **Teacher agent** → `host_a` (primary speaker)
- **All other agents** → `host_b` (secondary speaker, alternating)

### Podcast Generation Pipeline Step

Added between media generation and TTS generation:
- **Step name**: `generating_podcast`
- **Progress**: 92%
- **If podcast succeeds**: TTS step is skipped entirely (podcast audio replaces all SpeechActions)
- **If podcast fails**: falls back to normal TTS generation per action

### PodcastAction Type

Defined in OpenMAIC `action.ts`. Replaces all `SpeechActions` in a scene with a single continuous audio file plus round timing metadata:

```typescript
interface PodcastAction {
  type: "podcast";
  audioUrl: string;       // e.g. "/api/classroom-media/{id}/podcast/podcast_s1.mp3"
  rounds: Array<{
    speaker: "host_a" | "host_b";
    text: string;
    startTime: number;    // seconds offset within audio
    endTime: number;      // seconds offset within audio
  }>;
}
```

### Podcast Player

OpenMAIC `podcast-player.ts` uses `AudioContext` (same cross-origin iframe pattern as `AudioPlayer`):
- Plays continuous podcast MP3 via `AudioContext` + `AudioBufferSourceNode`
- Tracks current round via timeline-based round timing (`startTime`/`endTime`)
- Emits round-change events for subtitle and avatar synchronization
- Compatible with the iframe autoplay unlock pattern documented in Cross-Origin iframe Integration Requirements

### Podcast Audio Storage

- **Path**: `data/classrooms/{id}/podcast/podcast_s{sceneOrder}.mp3`
- **Served via**: `/api/classroom-media/{classroomId}/podcast/{filename}` (route now allows `podcast/` subdirectory)
- **embedPodcastAudioInScenes**: replaces all `SpeechActions` in each scene with a single `PodcastAction` pointing to the scene's podcast MP3

### Lecture Notes (Chat Area) Handling

OpenMAIC `chat-area.tsx` handles `PodcastAction` via `flatMap`: each round in the podcast is extracted as a speech item, displaying round text as subtitle content while the podcast player tracks the active round for avatar highlighting.

## Data Flow Summary

```
Process.vue: Click KnowledgePoint
  ├─ Has classroom_id? → navigate to /classroom/{id}
  └─ No → POST /api/classroom/generate
     └─ Evolith Backend → check Neo4j cache → POST OpenMAIC /api/generate-classroom
        └─ OpenMAIC: create job → background generation → return jobId + pollUrl

  └─ Poll: GET /api/classroom/status/{jobId} every 5s (MAX_POLL_RETRIES=3)
     └─ Evolith Backend → GET OpenMAIC → map statuses (ValueError caught for HMR HTML)
        └─ On completed: POST /api/classroom/cache → navigate /classroom/{id}

ProjectWorkbench.vue: Click KP card button or HintPanel L3
  ├─ Has classroom_id? → navigate to /classroom/{id}
  └─ No → POST /api/classroom/generate
     └─ Same backend flow as above

  └─ Poll: GET /api/classroom/status/{jobId} every 5s (NO timeout limit)
     └─ On completed: cacheClassroomId (fire-and-forget) + refreshMilestones + navigate

  └─ Classroom.vue: <iframe src="OpenMAIC/classroom/{id}" allow="autoplay 'src'">
     └─ Classroom mode: IndexedDB → server API → TTS fallback → AudioContext unlock → Stage renders
     └─ Podcast mode: PodcastPlayer → AudioContext → timeline round tracking → subtitle/avatar sync

Storage:
  Neo4j → KnowledgePoint nodes: classroom_id attribute
  OpenMAIC data/classrooms/ → {id}.json + {id}/audio/ + {id}/media/ + {id}/podcast/
  OpenMAIC IndexedDB → stages, scenes, audioFiles, mediaFiles, generatedAgents
```

Podcast mode flow (when podcast_mode='podcast'):
```
Process.vue → classroom.py (podcast_mode, podcast_speaker_pair)
  → OpenMAIC /api/generate-classroom { enablePodcast: true, podcastSpeakerPair }
    → Pipeline: generating_podcast (92%) → Volcengine WebSocket SAMI
      → podcast-generation.ts → podcast-client.ts → binary audio → save MP3
        → embedPodcastAudioInScenes → PodcastAction replaces SpeechActions
          → PodcastPlayer (AudioContext) → round tracking → subtitle/avatar sync
  └─ If podcast fails → fallback to normal TTS generation
```

## Known Behaviors (Classroom)

1. **Generation Time**: 5-10 minutes. Frontend polls every 5 seconds.
2. **Caching**: `classroom_id` cached in Neo4j after generation. Green button on subsequent visits. No page refresh needed — Process.vue updates button state in-place, Workbench calls `refreshMilestones()`.
3. **Service Dependency**: OpenMAIC not running → 503. `npm run dev:all` starts all services.
4. **Iframe Security**: `ALLOWED_FRAME_ANCESTORS` must include Evolith's origin.
5. **Audio**: Missing any of the 4 settings → HTMLAudioElement fallback → silent in cross-origin iframe.
6. **sessionStorage**: Job state persisted. HMR/page reload auto-resumes. Closing tab clears.
7. **Field Mapping**: OpenMAIC camelCase (`jobId`) → Evolith snake_case (`job_id`). Robust dual-key check.
8. **TTS Fallback**: Transparent for missing server audio. First visit ~20-30s, subsequent instant from IndexedDB.
9. **Podcast Mode**: If podcast generation fails (Volcengine WebSocket error, SAMI protocol issue, or missing env vars), the pipeline automatically falls back to per-action TTS generation. No manual intervention needed.
10. **Podcast Retry Resilience**: Evolith frontend polling has `MAX_POLL_RETRIES=3`. A single transient 500 from OpenMAIC (e.g. Next.js dev server HMR returning HTML) no longer kills polling. The Flask backend also catches `ValueError` (`JSONDecodeError`) from such HMR responses.
11. **Podcast Length Limits**: Volcengine SAMI scripted mode: single round <=300 chars, total <=10,000 chars. Very long scenes may be split or truncated by `podcast-generation.ts`.
12. **Podcast Env Vars**: `PODCAST_VOLCENGINE_APP_ID` and `PODCAST_VOLCENGINE_ACCESS_KEY` must be set in OpenMAIC's environment. Missing either → podcast step fails → falls back to TTS.
13. **Podcast Audio Path**: Podcast MP3s stored in `data/classrooms/{id}/podcast/` and served via `/api/classroom-media/{id}/podcast/{filename}`. The media route allows `podcast/` as a valid subdirectory.
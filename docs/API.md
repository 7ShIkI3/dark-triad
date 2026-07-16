# 🜏 The Dark Triad — API Documentation

## Overview

The Dark Triad exposes a **FastAPI** REST + WebSocket API for mission orchestration, AI routing,
agent registry, and sandbox management. The application is created via the `create_app()` factory
in `src/tdt/api/app.py` and can be served with any ASGI server (uvicorn, hypercorn, etc.).

**Base URL** (default): `http://127.0.0.1:8000`

**API Version Prefix**: `/api/v1`

**Live docs** (when running): `/docs` (Swagger UI) and `/redoc` (ReDoc)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Rate Limiting](#rate-limiting)
3. [Error Response Format](#error-response-format)
4. [REST Endpoints](#rest-endpoints)
   - [System](#system)
   - [Missions](#missions)
   - [AI / Models](#ai--models)
   - [Agents](#agents)
   - [Sandbox](#sandbox)
5. [WebSocket Streaming](#websocket-streaming)
6. [Pydantic Schemas](#pydantic-schemas)
7. [Running the API](#running-the-api)

---

## Authentication

Currently, the API has **no authentication layer**. CORS is configured to allow all origins
(`allow_origins=["*"]`) — this is suitable for local / sandboxed development only.

> **Security Note:** In production, add an API-key or OAuth2 middleware before exposing the
> endpoint to a network.

---

## Rate Limiting

The API uses a global **in-memory sliding-window rate limiter** (`RateLimiter` from
`tdt.core.resilience`).

| Parameter     | Default |
|---------------|---------|
| `max_calls`   | 100     |
| `window`      | 60 s    |

The following endpoints are rate-limited:
- `POST /api/v1/missions`
- `GET /api/v1/missions`
- `GET /api/v1/ai/status`
- `GET /api/v1/ai/models`
- `POST /api/v1/ai/generate`
- `GET /api/v1/agents`
- `GET /api/v1/sandbox/status`

When the limit is exceeded, the server returns **HTTP 429** with the standard error body:

```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

---

## Error Response Format

All errors use FastAPI's standard `HTTPException` mechanism and return the schema

```json
{
  "detail": "<human-readable error message>"
}
```

| HTTP Status | Typical Cause                        |
|-------------|--------------------------------------|
| 400         | Invalid input format (e.g. bad `mission_id`) |
| 404         | Resource not found                   |
| 429         | Rate limit exceeded                  |
| 503         | Backend service unavailable (AI generation) |

---

## REST Endpoints

### System

#### `GET /api/v1/health`

Simple liveness check.

**Response** (`200`)

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

### Missions

#### `POST /api/v1/missions`

Create a new mission. The server builds a mission plan using `MissionPlanner` and stores it
in the in-memory store.

**Request body**

| Field          | Type   | Required | Default       | Description                        |
|----------------|--------|----------|---------------|------------------------------------|
| `objective`    | string | ✅       | —             | Mission objective (≥1 character)   |
| `personality`  | string | ❌       | `"mach"`      | Agent personality mode             |
| `aggression`   | string | ❌       | `"aggressive"`| Aggression level                   |
| `constraints`  | dict   | ❌       | `null`        | Optional constraints / RoE         |

**Example request**

```json
{
  "objective": "Reconnaissance on target 10.0.0.0/24",
  "personality": "mach",
  "aggression": "stealth",
  "constraints": {
    "max_duration_minutes": 60,
    "exclude_hosts": ["10.0.0.1"]
  }
}
```

**Response** (`201`)

```json
{
  "mission_id": "a1b2c3d4e5f6",
  "plan": { /* MissionPlan — see Pydantic schemas */ },
  "status": "planned"
}
```

| Field        | Type   | Description                        |
|--------------|--------|------------------------------------|
| `mission_id` | string | 12-character hex identifier        |
| `plan`       | object | Full mission plan (personality-dependent) |
| `status`     | string | Current plan status                |

**Errors**: `400` (invalid body), `429` (rate limit)

---

#### `GET /api/v1/missions`

List all missions in the in-memory store.

**Response** (`200`)

```json
{
  "missions": [
    {
      "mission_id": "a1b2c3d4e5f6",
      "objective": "Reconnaissance on target 10.0.0.0/24",
      "personality": "mach",
      "status": "planned",
      "created_at": "2026-07-16T12:00:00Z"
    }
  ]
}
```

**Errors**: `429` (rate limit)

---

#### `GET /api/v1/missions/{mission_id}`

Retrieve full details for a single mission.

**Path parameters**

| Parameter    | Type   | Validation                  | Description     |
|--------------|--------|-----------------------------|-----------------|
| `mission_id` | string | Exactly 12 alphanumeric chars | Mission identifier |

**Response** (`200`)

```json
{
  "mission_id": "a1b2c3d4e5f6",
  "plan": { /* Full plan object */ },
  "status": "planned",
  "phases": [
    {
      "id": "phase-001",
      "name": "Network Scan",
      "status": "pending",
      "result": null
    }
  ]
}
```

**Errors**: `400` (invalid mission_id format), `404` (not found)

---

#### `GET /api/v1/missions/{mission_id}/report`

Retrieve a formatted mission report in one of three output formats.

**Path parameters**

| Parameter    | Type   | Validation                  |
|--------------|--------|-----------------------------|
| `mission_id` | string | Exactly 12 alphanumeric chars |

**Query parameters**

| Parameter | Type   | Default | Valid Values              | Description    |
|-----------|--------|---------|---------------------------|----------------|
| `format`  | string | `"json"` | `json`, `html`, `sarif`  | Output format  |

**Response**

- **`format=json`** (default): JSON object

  ```json
  {
    "mission_id": "a1b2c3d4e5f6",
    "objective": "...",
    "personality": "mach",
    "status": "planned",
    "phases": [],
    "created_at": "2026-07-16T12:00:00Z"
  }
  ```

- **`format=html`**: `Content-Type: text/html` — report wrapped in `<pre>` inside a minimal HTML document.

- **`format=sarif`**: SARIF 2.1.0-compliant JSON (Static Analysis Results Interchange Format).

**Errors**: `400` (invalid mission_id or unsupported format), `404` (mission not found)

---

### AI / Models

#### `GET /api/v1/ai/status`

Get status of all configured AI providers and hardware info. Calls `AIRouter.initialize()`.

**Response** (`200`)

```json
{
  "providers": {
    "openai": {
      "available": true,
      "models_count": 3
    },
    "anthropic": {
      "available": true,
      "models_count": 2
    }
  },
  "hardware": {
    "ram_gb": 32.0,
    "gpu": "NVIDIA RTX 4090"
  }
}
```

**Errors**: `429` (rate limit)

---

#### `GET /api/v1/ai/models`

List all available AI models across all providers.

**Response** (`200`)

```json
{
  "models": [
    {
      "name": "gpt-4",
      "provider": "openai",
      "tier": "premium",
      "uncensored": false,
      "local": false
    },
    {
      "name": "hermes-3",
      "provider": "local",
      "tier": "standard",
      "uncensored": true,
      "local": true
    }
  ]
}
```

**Errors**: `429` (rate limit)

---

#### `POST /api/v1/ai/generate`

Generate text through the AI router. Routes to the best available provider based on
personality, tier, and availability.

**Request body**

| Field         | Type    | Required | Description                              |
|---------------|---------|----------|------------------------------------------|
| `prompt`      | string  | ✅       | Prompt text (≥1 character)               |
| `personality` | string  | ❌       | Personality mode for provider bias       |
| `json_mode`   | boolean | ❌       | Request structured JSON output           |

**Response** (`200`)

```json
{
  "text": "Generated response text...",
  "model": "gpt-4",
  "provider": "openai",
  "tokens_used": 512
}
```

**Errors**: `422` (validation), `429` (rate limit), `503` (no provider available)

---

### Agents

#### `GET /api/v1/agents`

List all registered specialist agents from `AgentRegistry.list_all()`.

**Response** (`200`)

```json
{
  "agents": [
    {
      "name": "recon-agent",
      "category": "reconnaissance",
      "personality": "mach"
    },
    {
      "name": "exploiter-prime",
      "category": "exploitation",
      "personality": "narc"
    }
  ]
}
```

**Errors**: `429` (rate limit)

---

### Sandbox

#### `GET /api/v1/sandbox/status`

Check the current status of the Docker sandbox environment.

**Response** (`200`)

```json
{
  "running": true,
  "container_id": "abc123def456",
  "image": "kalilinux/kali-rolling",
  "uptime": 3600.0
}
```

If the sandbox is unreachable, a fallback response is returned with `running: false`:

```json
{
  "running": false,
  "container_id": null,
  "image": "kalilinux/kali-rolling",
  "uptime": 0.0
}
```

**Errors**: `429` (rate limit)

---

## WebSocket Streaming

#### `WS /api/v1/missions/{mission_id}/stream`

Stream real-time phase execution events for a mission.

**Path parameters**

| Parameter    | Type   | Validation                  |
|--------------|--------|-----------------------------|
| `mission_id` | string | Exactly 12 alphanumeric chars |

**Protocol**

After accepting the connection, the server replays the mission's phases as a sequence
of JSON messages. The client should listen for these message types:

| Message Type        | Direction      | Description                                   |
|---------------------|----------------|-----------------------------------------------|
| `phase_start`       | server → client | A mission phase has begun                     |
| `phase_progress`    | server → client | Progress update on the current phase          |
| `phase_complete`    | server → client | A phase finished successfully                 |
| `mission_complete`  | server → client | All phases done, mission finished             |
| `error`             | server → client | An error occurred (invalid ID or missing mission) |
| `pong`              | server → client | Response to a client `"ping"` message         |

**Message schemas**

```
┌─────────────────────────────────────────────────────────┐
│ phase_start                                               │
├─────────────────────────────────────────────────────────┤
│ {                                                         │
│   "type": "phase_start",                                  │
│   "phase_id": "phase-001",                                │
│   "data": { "name": "Network Scan" },                     │
│   "timestamp": "2026-07-16T12:00:00Z"                     │
│ }                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ phase_progress                                            │
├─────────────────────────────────────────────────────────┤
│ {                                                         │
│   "type": "phase_progress",                               │
│   "phase_id": "phase-001",                                │
│   "data": { "progress": 0.5, "message": "In progress..." },│
│   "timestamp": "2026-07-16T12:00:05Z"                     │
│ }                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ phase_complete                                            │
├─────────────────────────────────────────────────────────┤
│ {                                                         │
│   "type": "phase_complete",                               │
│   "phase_id": "phase-001",                                │
│   "data": { "result": "completed" },                      │
│   "timestamp": "2026-07-16T12:00:10Z"                     │
│ }                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ mission_complete                                          │
├─────────────────────────────────────────────────────────┤
│ {                                                         │
│   "type": "mission_complete",                             │
│   "data": { "mission_id": "...", "status": "completed" }, │
│   "timestamp": "2026-07-16T12:00:15Z"                     │
│ }                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ error                                                     │
├─────────────────────────────────────────────────────────┤
│ {                                                         │
│   "type": "error",                                        │
│   "detail": "Mission not found"                           │
│ }                                                         │
└─────────────────────────────────────────────────────────┘
```

**Client → Server**

The server accepts a single client message type:

| Message | Server Response |
|---------|-----------------|
| `"ping"` (plain text) | `{"type": "pong"}` (JSON) |

The server closes the connection immediately if:
- The `mission_id` format is invalid (not 12 alphanumeric chars)
- The `mission_id` does not match any known mission

---

## Pydantic Schemas

Key request/response models defined in `src/tdt/api/app.py`:

| Model                  | Purpose                                  |
|------------------------|------------------------------------------|
| `MissionRequest`       | POST /api/v1/missions body               |
| `MissionResponse`      | Mission creation response                |
| `MissionListItem`      | Summary item in mission list             |
| `MissionListResponse`  | GET /api/v1/missions response            |
| `MissionDetailResponse`| GET /api/v1/missions/{id} response       |
| `PhaseInfo`            | Phase excerpt used in list/detail views  |
| `GenerateRequest`      | POST /api/v1/ai/generate body            |
| `GenerateResponse`     | AI generation result                     |
| `AIStatusResponse`     | Provider + hardware status               |
| `ModelsResponse`       | Available models list                    |
| `ModelInfoSchema`      | Single model info item                   |
| `AgentsResponse`       | GET /api/v1/agents response              |
| `AgentInfo`            | Single agent summary                     |
| `SandboxStatusSchema`  | Sandbox status response                  |
| `HealthResponse`       | Health check response                    |
| `ErrorResponse`        | Standard error body                      |
| `WSPhaseStart`         | WebSocket phase_start message            |
| `WSPhaseProgress`      | WebSocket phase_progress message         |
| `WSPhaseComplete`      | WebSocket phase_complete message         |
| `WSPhaseFailed`        | WebSocket phase_failed message           |
| `WSMissionComplete`    | WebSocket mission_complete message       |

---

## Running the API

```bash
# From the project root

# Using the default instance (runs create_app() at module level)
uvicorn tdt.api.app:app --reload --port 8000

# With custom dependencies (inject from your own entry point)
python -c "
from tdt.api.app import create_app
from tdt.core.ai_router import AIRouter
from tdt.core.sandbox import SandboxManager
from tdt.agents.registry import AgentRegistry

app = create_app(
    ai_router=AIRouter(),
    agent_registry=AgentRegistry(),
    sandbox=SandboxManager(),
)
"
```

### Environment

The API is stateless for requests; mission data is stored in an **in-memory dict**
(`_missions`). Restarting the server clears all mission data.

---

## Version

Current: `0.1.0` (defined in `tdt.api.app.__version__`)

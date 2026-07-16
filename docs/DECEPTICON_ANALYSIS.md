# Decepticon Architecture Analysis — Patterns for The Dark Triad

> **Source**: https://github.com/PurpleAILAB/Decepticon (v1.x)
> **Clone**: `/c/Users/attometre/dark-triad/references/decepticon`
> **Purpose**: Extract reusable architectural patterns, agent designs, and operational
> features for The Dark Triad autonomous red team agent project.

---

## Table of Contents

1. [Monorepo Structure](#1-monorepo-structure)
2. [16-Agent Architecture & Orchestration](#2-16-agent-architecture--orchestration)
3. [Tmux Sandbox Pattern](#3-tmux-sandbox-pattern)
4. [Engagement Discipline (RoE/ConOps/OPPLAN)](#4-engagement-discipline-roeconopsopplan)
5. [Model Tier System](#5-model-tier-system)
6. [Knowledge Graph Pattern](#6-knowledge-graph-pattern)
7. [Install & Onboarding Flow](#7-install--onboarding-flow)
8. [Middleware Stack & Safety Systems](#8-middleware-stack--safety-systems)
9. [Patterns to Reuse for The Dark Triad](#9-patterns-to-reuse-for-the-dark-triad)

---

## 1. Monorepo Structure

```
Decepticon/
├── docker-compose.yml          # Multi-service orchestration (LLM + DB + sandbox)
├── langgraph.json               # LangGraph Platform agent graph registry
├── pyproject.toml               # Workspace root (uv monorepo)
├── packages/
│   ├── decepticon/              # Core framework — agents, tools, skills, LLM
│   ├── decepticon-core/         # LangChain-free contracts, types, protocols
│   └── decepticon-sdk/          # Client SDK with PluginBundle scaffold
├── clients/
│   ├── cli/                    # Terminal UI (Ink/React)
│   ├── web/                    # Next.js web dashboard
│   └── launcher/               # Go binary (installer, lifecycle, opscontrol)
├── config/
│   ├── litellm.yaml            # LLM proxy routes per provider
│   └── litellm_dynamic_config.py  # Dynamic model registration
├── containers/                 # Dockerfiles and init scripts
├── scripts/install.sh          # Single-curl installer
├── docs/                       # Full documentation suite
│   ├── agents.md               # Agent roster and middleware
│   ├── architecture.md         # Two-network design
│   ├── engagement-workflow.md  # End-to-end engagement flow
│   ├── knowledge-graph.md      # Neo4j KG schema
│   └── models.md               # Model tier + fallback system
└── benchmarks/                 # XBOW, CVE, exploit benchmarks + results
```

**Key architectural decision**: Three-package split with `decepticon-core` enforcing a
LangChain-free guarantee via ruff lint rules (banned-api TID251). The core defines
types, contracts, and protocols; the framework binds them to LangChain/LangGraph; the
SDK provides a clean surface for third-party plugins.

**For Dark Triad**: Consider a similar `core/` → `framework/` → `sdk/` split to keep
LLM-framework coupling contained.

---

## 2. 16-Agent Architecture & Orchestration

### Agent Graph Registry (`langgraph.json`)

All agents are registered as LangGraph graphs with their module paths:

```json
{
  "graphs": {
    "decepticon":     "./packages/decepticon/.../decepticon.py:graph",
    "recon":           "...",
    "soundwave":       "...",
    "exploit":         "...",
    "postexploit":     "...",
    "analyst":         "...",
    "reverser":        "...",
    "contract_auditor":"...",
    "cloud_hunter":    "...",
    "ad_operator":    "...",
    "phisher":         "...",
    "mobile_operator": "...",
    "wireless_operator":"...",
    "osint_operator":  "...",
    "iot_operator":    "...",
    "ics_operator":    "...",
    "forensicator":    "...",
    "supply_chain_operator":"...",
    "blue_cell":       "..."
  }
}
```

### Three Tiers of Agents

| Tier | Agents | Purpose |
|------|--------|---------|
| **Orchestrators** | Decepticon, Vulnresearch, Soundwave | Planning, dispatch, state management |
| **Core Kill-Chain** | Recon, Exploit, Post-Exploit | Standard penetration testing phases |
| **Domain Specialists** | AD Operator, Cloud Hunter, Contract Auditor, Reverser, Analyst, Phisher, Mobile Operator, Wireless Operator, OSINT Operator, IoT Operator, ICS Operator, Forensicator, Supply Chain Operator | Deep-domain expertise per attack surface |

### Orchestration Loop (The "Ralph Loop")

```
while objectives remain pending:
    obj = next_pending_objective_with_dependencies_met()
    agent = spawn_specialist_agent(obj.phase)
    result = agent.execute(obj, roe, findings_so_far)
    update_opplan_status(obj, result.status)
    append_findings_to_disk(result.findings)
    update_knowledge_graph(result.findings)
```

**Key pattern**: Fresh context window per objective. No accumulated noise. Findings
persist to disk (`workspace/`) and the knowledge graph, not agent memory.

### Fresh Context Model

Every specialist agent spawns with a clean window:
1. Orchestrator picks next pending objective from OPPLAN
2. New agent instance gets only: objective, RoE guard rails, relevant findings from disk
3. Agent executes, writes findings, returns `PASSED` or `BLOCKED`
4. Orchestrator updates OPPLAN, moves to next objective

### Agent Factory Pattern (`create_decepticon_agent()`)

```python
def create_decepticon_agent(
    *,
    backend=None,         # Injected for testing / library composition
    llm=None,             # Bound chat model (default from LLMFactory)
    fallback_models=None, # ModelFallbackMiddleware chain
    subagents=None,       # Explicit sub-agent list
    tools=None,           # Full tool list override
    middleware=None,      # Full middleware list override
    system_prompt=None,   # Full prompt override
    recursion_limit=None,
):
```

Three usage paths:
1. **OSS default**: `create_decepticon_agent()` — no args
2. **Plugin override**: `PluginBundle` discovered via entry points
3. **Full custom**: bypass factory, compose directly with `langchain.agents.create_agent`

### Delegation Protocol

Every `task()` delegation carries six fields:
1. **Objective** — What specifically to accomplish
2. **Scope** — IN SCOPE + OUT OF SCOPE boundaries
3. **Context** — Relevant findings from previous phases
4. **Lessons** — Known gotchas, failed approaches, OPSEC warnings
5. **Acceptance Criteria** — How the sub-agent knows it's done
6. **Output Location** — Where to save results

**For Dark Triad**: Use this delegation template. The structured context handoff
prevents information loss between sub-agents and is superior to passing raw
conversation history.

---

## 3. Tmux Sandbox Pattern

### Architecture

The sandbox is a **hardened Kali Linux container** on an isolated operational network
(`sandbox-net`). The management plane (`decepticon-net`) and operational plane are
separated by network boundary — no offensive tool can reach the LLM gateway or
credentials.

```
Agent (LangGraph on decepticon-net)
  │  Docker socket only (never TCP)
  ▼
Sandbox container (Kali on sandbox-net)
  │
  ├── tmux session manager (TmuxSessionManager)
  │     ├── Persistent named sessions per objective
  │     ├── Interactive prompt detection
  │     ├── Embedded PS1 markers [DCPTN:<id>:<cwd>]
  │     └── Pipe-pane streaming logs
  │
  ├── bash tool (docker exec layer)
  ├── Offensive tools (nmap, sqlmap, Impacket, Metasploit, Nuclei)
  └── Sliver C2 client
```

### TmuxSessionManager (`packages/decepticon/decepticon/sandbox_kernel/tmux.py`)

Core features:
- **Persistent sessions** — Each named session persists across commands. An agent can
  open `msfconsole`, send commands, and read output — same as a human operator.
- **PS1 markers** — Custom `[DCPTN:<id>:<cwd>]` prompt markers enable reliable
  command completion detection.
- **Interactive prompt detection** — Regex-based (`_PROMPT_TAIL_RE`) matches
  `msf6 >`, `sliver >`, `(Pdb)`, `>>>`, `$`, etc.
- **Adaptive polling** — While a command has no output, poll interval grows
  geometrically (×1.5, max 4×). Once output appears, returns to 0.5s cadence.
- **Output management**:
  - ≤15K chars: returned inline
  - 15K–100K chars: saved to `/workspace/.scratch/`, summary returned
  - >5M chars: watchdog kills the command
- **Egress control** — nftables on the sandbox container enforce scope boundaries
  (default `enforce` mode, opt-out via `DECEPTICON_EGRESS_DISABLE`).
- **Environment passthrough** — Strict allowlist of proxy vars and `DECEPTICON_*`
  vars forwarded into tmux sessions.

### Bash Tool Architecture

Commands execute through a thin `bash` tool backed by `DockerSandbox.execute_tmux()`.
The transport layer shifted from `docker exec` (retired `DockerSandbox`) to an
in-container HTTP daemon (`HTTPSandbox` + `sandbox_server/`).

### Background Commands

Long-running commands use `run_in_background=True`. The `SandboxNotificationMiddleware`
polls completion via `/read_session_log_diff` once per turn and injects a
`<system-reminder>` HumanMessage on the agent's next inference — no polling required.

**For Dark Triad**: The tmux-based architecture is superior to simple `subprocess.run()`
for offensive security work. Adopt the `TmuxSessionManager` pattern with PS1 markers
and interactive prompt detection. The two-network isolation design is directly applicable.

---

## 4. Engagement Discipline (RoE/ConOps/OPPLAN)

### Planning Phase (Soundwave Agent)

Soundwave is a **standalone LangGraph agent** (not a sub-agent) that conducts a
structured interview and generates an eight-document engagement bundle.

### The Eight-Document Bundle

| Document | Purpose | File |
|----------|---------|------|
| **RoE** (Rules of Engagement) | Authorized scope, exclusions, testing window, escalation, legal authorization | `plan/roe.json` |
| **Threat Profile** | MITRE-mapped adversary persona — tier, group ID, key TTPs | `plan/threat-profile.json` |
| **CONOPS** (Concept of Operations) | Threat model and kill-chain phases scoped to RoE | `plan/conops.json` |
| **Deconfliction Plan** | Source IPs, user-agents, time windows, deconfliction code | `plan/deconfliction.json` |
| **Contact Plan** | Operator, escalation chain, emergency page recipient | `plan/contact.json` |
| **Data Handling Plan** | Per-class evidence retention, encryption, chain-of-custody | `plan/data-handling.json` |
| **Abort Plan** | Halt triggers, AI-aware safety gates, destructive-action triggers | `plan/abort.json` |
| **Cleanup Plan** | Expected artifact inventory with per-phase removal | `plan/cleanup.json` |

### Soundwave RoE Generation Workflow (from `soundwave/roe-template/SKILL.md`)

1. Drive each dimension through one `ask_user_question` call
2. Cover: identity/scope, boundaries/escalation, prohibited/permitted actions
3. Generate `plan/roe.json` matching the `RoE` schema
4. Validate against checklist

### CONOPS Generation Workflow (from `soundwave/conops-template/SKILL.md`)

1. Read existing `plan/roe.json` (prerequisite)
2. Interview user on threat model + operations
3. Design kill chain based on RoE scope
4. Generate `plan/conops.json` + `plan/deconfliction.json`
5. Validate (executive summary jargon-free, MITRE IDs valid, timeline concrete)

### OPPLAN Structure (from `soundwave/opplan-converter/SKILL.md`)

The OPPLAN is the machine-readable execution plan — the direct analogue of a
`prd.json` for the autonomous loop:

```json
{
  "id": "OBJ-001",
  "title": "Port scan and service enumeration",
  "phase": "recon",
  "opsec_level": "standard",
  "mitre": ["T1595", "T1046"],
  "depends_on": [],
  "acceptance_criteria": ["All open ports identified with service versions"],
  "status": "pending"
}
```

**OPSEC levels**: `loud` → `standard` → `careful` → `quiet` → `silent`
**Phases**: `recon` → `initial-access` → `post-exploit` → `c2` → `exfiltration`

### Objective Decomposition Rules

1. **One context window rule** — If an agent can't complete an objective in one
   session, it's too big. Split it.
2. **Three mandatory acceptance criteria** per objective:
   - Scope check (verify against RoE in-scope list)
   - OPSEC check (rate limit, timing, etc.)
   - Output persistence (results saved to specific file path)
3. **Phase → sub-agent routing** table maps phases to specialist agents

### Engagement Lifecycle (from `orchestration/SKILL.md`)

```
Planning → Recon → Exploit → PostExploit → Report
Gate checks at each transition:
  Planning→Recon:    roe + conops + deconfliction + opplan exist and validated
  Recon→Exploit:     Attack surface identified, targets prioritized
  Exploit→PostExploit: Initial foothold established
  PostExploit→Report: All objectives resolved (passed or blocked)
```

### State Files

```
<engagement>/
├── plan/
│   ├── roe.json              # Immutable scope boundaries
│   ├── conops.json           # Operation concept
│   ├── deconfliction.json    # Deconfliction procedures
│   └── opplan.json           # Objective tracker (updated after each sub-agent)
├── findings/                 # FIND-NNN.md per finding
├── lessons_learned.md        # Failed approaches + what worked
└── .ralph_state.json         # Loop iteration counter + completion flags
```

**For Dark Triad**: Adopt this entire engagement discipline. The RoE→ConOps→OPPLAN
pipeline is the key differentiator between a real red team tool and a script that
runs nmap. The structured acceptance criteria and gate checks prevent aimless wandering.

---

## 5. Model Tier System

### Three Orthogonal Axes

| Axis | Values | Decided By |
|------|--------|-----------|
| **Tier** | HIGH / MID / LOW | Agent role, overridable by profile |
| **AuthMethod** | API key, OAuth (6 services), local (Ollama, llama.cpp) | Credentials inventory |
| **Profile** | eco / max / test | `DECEPTICON_MODEL_PROFILE` |

### Default Profile: `eco`

| Tier | Agents |
|------|--------|
| HIGH | decepticon, exploit, exploiter, patcher, contract_auditor, analyst, vulnresearch |
| MID | detector, verifier, postexploit, ad_operator, cloud_hunter, reverser, phisher, mobile_operator |
| LOW | soundwave, recon, scanner, wireless_operator |

### Tier × AuthMethod Matrix

Each cell maps to a specific model identifier (e.g., `anthropic/claude-opus-4-7` at
HIGH for `anthropic_api`). When a method has no model at a requested tier (e.g.,
MiniMax at LOW), the resolver skips it and continues to the next priority.

### Fallback Chain Construction

The factory walks the `DECEPTICON_AUTH_PRIORITY` list (e.g.,
`anthropic_oauth,openai_api,ollama_local`), drops methods whose detection checks
fail (placeholder keys, unreachable endpoints), and builds a primary + N-deep
fallback chain. `ModelFallbackMiddleware` walks the queue transparently on failure.

### Key Design Decisions

- **Credentials inventory, not model config** — User declares which credentials they
  have; Decepticon builds the chain.
- **Subscription OAuth first** — When available, OAuth runs as primary (no API cost);
  paid API key is the fallback.
- **Per-role overrides via env** — `DECEPTICON_MODEL_RECON=...` overrides a specific role.
- **Cross-provider fallback** — When Anthropic hits a rate limit, OpenAI takes over
  seamlessly for that request.

**For Dark Triad**: The tier × auth-method matrix and priority-ordered fallback chain
are directly applicable. The `eco`/`max`/`test` profile system is the right pattern for
balancing cost vs. capability.

---

## 6. Knowledge Graph Pattern

### Neo4j Architecture

Decepticon uses Neo4j as a **persistent attack graph** — the agent's long-term memory
across iterations, not conversation history.

```
                   Agent (LangGraph)
                  /                  \
    [bolt://neo4j:7687]      [bolt://neo4j:7687]
            │                          │
    decepticon-net              sandbox-net
            │                          │
            └────── Neo4j KGStore ─────┘
            (dual-homed — both networks see same instance)
```

### Node Types

| Type | Key Properties | Created By |
|------|---------------|-----------|
| `Host` | ip, hostname, os, os_version | Recon, Scanner |
| `Service` | port, protocol, name, version, banner | Recon, Scanner |
| `Vulnerability` | cve_id, cwe_id, cvss_score, severity | Scanner, Detector, Verifier |
| `Credential` | username, hash_type, hash, plaintext | Post-Exploit, Exploit |
| `Account` | username, domain, privileges, groups | Post-Exploit, AD Operator |

### Relationship Types

| Relationship | From → To | Meaning |
|-------------|-----------|---------|
| `RUNS_ON` | Service → Host | Service runs on a host |
| `AFFECTS` | Vulnerability → Service | Vulnerability in a service |
| `EXPLOITS` | Objective/Finding → Vulnerability | Attack exploits this vuln |
| `REQUIRES` | Vulnerability → Vulnerability | Exploit chain dependency |
| `USES` | Attack → Credential | Attack uses a credential |
| `OWNS` | Account → Host | Account has access to host |

### KG Tools

**Mutations**: `kg_create_node`, `kg_create_edge`
**Queries**: `kg_query_nodes`, `kg_query_paths`, `kg_get_severity_score`
**Attack Chain Planning**: `plan_attack_chains()`, `critical_path_score()`, `promote_chain()`
**Artifact Ingestion**: `ingest_sarif()`, `ingest_scan_output()`

### Skillogy — Skill Catalog Service

A separate Neo4j graph (not the engagement KG) with `Skill` nodes and edges
(`BUILDS_ON`, `CHAINS_TO`, `MITRE_RELATED`). REST API with hard ACL enforcement
per agent role. Three endpoints: `find`, `load`, `traverse`.

**For Dark Triad**: Adopt the dual-graph pattern (engagement KG + skill catalog).
The typed node/relationship schema is directly reusable. The attack chain planning
tools (`plan_attack_chains()`, `critical_path_score()`) are valuable for autonomous
TTP selection.

---

## 7. Install & Onboarding Flow

### Install Command

```bash
curl -fsSL https://decepticon.red/install | bash
```

The shell installer (`scripts/install.sh`) does:
1. **Pre-flight checks**: curl, Docker (or Podman 4.4+), Docker Compose v2, sha256 tool
2. **Version resolution**: GitHub API → latest final release (stable with 7-day soak or latest)
3. **File download**: docker-compose.yml, .env.example, config/litellm.yaml
4. **Integrity verification**: SHA256 checksums against release manifest
5. **Launcher binary download**: GoReleaser binary for OS/arch, verified against checksums.txt
6. **PATH setup**: bash/zsh/fish shell config
7. **Docker image pull**: compose --profile cli pull

### Onboarding Wizard

```bash
decepticon onboard
```

Interactive wizard guides through:
1. **Authentication** — API key, subscription OAuth, or local Ollama
2. **Provider** — Choose from tier-mapped providers
3. **Credentials** — API key, OAuth token, or endpoint URL
4. **Model Profile** — eco (default), max, test
5. **LangSmith** — Optional LLM observability tracing

Configuration written to `~/.decepticon/.env`.

### Startup

```bash
decepticon   # Starts core stack + drops into terminal CLI
```

The default start brings up: LiteLLM, PostgreSQL, Neo4j, Skillogy, LangGraph, sandbox.
Specialist workloads (BHCE, Sliver C2, Ghidra MCP) and web dashboard come up on demand
via `ops_start()` or `/web`.

### CLI Commands

| Command | Purpose |
|---------|---------|
| `decepticon` | Start core stack + terminal CLI |
| `decepticon onboard` | Interactive setup wizard |
| `decepticon stop` | Stop all services, keep data |
| `decepticon status` | Show running services |
| `decepticon logs [service]` | Follow service logs |
| `decepticon kg-health` | Neo4j knowledge graph diagnostics |
| `decepticon update` | Update to latest version |

**For Dark Triad**: The `onboard` wizard pattern with progressive credential discovery
is excellent. The integrity-verified install with version channel management (stable/latest
with soak days) is production-grade.

---

## 8. Middleware Stack & Safety Systems

### Middleware Slot Architecture

Each agent assembles its middleware from named **slots** (`MiddlewareSlot` enum).
Slot declaration order = canonical assembly order. Plugins replace or disable slots by name.

### Safety Stack (Every Agent)

| Middleware | Slot | Purpose |
|-----------|------|---------|
| `RoEGuardrailMiddleware` | `roe-guardrail` | Legal/safety gate — evaluates tool calls against RoE, appends to audit log |
| `UntrustedOutputMiddleware` | `untrusted-output` | Quarantines attacker-influenceable output in `<UNTRUSTED_TOOL_OUTPUT>` envelope |
| `PromptInjectionShieldMiddleware` | `prompt-injection-shield` | Deny-list wrap of attacker-controlled output |
| `EventLogMiddleware` | `event-log` | Structured event logging per model/tool call |
| `BudgetEnforcementMiddleware` | `budget` | Per-engagement spend caps |

### Bash-Executing Agents Also Get

| Middleware | Slot | Purpose |
|-----------|------|---------|
| `EngagementContextMiddleware` | `engagement-context` | Injects engagement metadata into every model call — **safety-critical** |
| `SandboxNotificationMiddleware` | `sandbox-notification` | Tracks background-job completion |
| `HITLApprovalMiddleware` | `hitl-approval` | Operator-approval gate for high-impact actions (opt-in) |

### Safety-Critical Slots

Six slots (`engagement-context`, `roe-guardrail`, `untrusted-output`,
`prompt-injection-shield`, `sandbox-notification`, `hitl-approval`) can only be
replaced/disabled by a plugin when `DECEPTICON_ALLOW_SAFETY_OVERRIDES=1` is set.

**For Dark Triad**: The middleware slot architecture is a powerful pattern for
composable agent behavior. The UntrustedOutput + PromptInjectionShield defense layer
is critical for any agent that reads attacker-controlled content.

---

## 9. Patterns to Reuse for The Dark Triad

### High-Priority Patterns

| Pattern | Priority | Dark Triad Integration |
|---------|----------|----------------------|
| **Engagement Discipline (RoE→ConOps→OPPLAN)** | 🔴 Critical | Adopt the full eight-document bundle and gate-checked lifecycle |
| **Fresh Context Model** | 🔴 Critical | Per-objective clean context windows, disk-backed findings |
| **Tmux Sandbox with PS1 Markers** | 🔴 Critical | Replace simple subprocess execution with persistent tmux sessions |
| **Two-Network Isolation** | 🔴 Critical | Management plane ↔ operational plane network separation |
| **Middleware Slot Architecture** | 🟡 High | Safety stack (RoE gate, untrusted output, injection shield) |

### Medium-Priority Patterns

| Pattern | Priority | Dark Triad Integration |
|---------|----------|----------------------|
| **Model Tier + Fallback Chain** | 🟡 High | Eco/max/test profiles with priority-ordered credentials |
| **Knowledge Graph (Neo4j)** | 🟡 High | Attack graph as long-term memory, attack chain planning tools |
| **Orchestrator Delegation Protocol** | 🟡 High | Structured six-field task handoff |
| **Skillogy Skill Catalog** | 🟡 Medium | Hard-ACL-gated skill discovery with BFS traversal |
| **Sub-Agent Plugin System** | 🟡 Medium | `PluginBundle` entry-point discovery + `DECEPTICON_PLUGINS` env |

### Low-Priority / Later

| Pattern | Priority | Notes |
|---------|----------|-------|
| Web dashboard (Next.js) | 🟢 Low | Nice-to-have but not core |
| Subscription OAuth handlers | 🟢 Low | API-key-first is simpler initially |
| Benchmark harness (XBOW) | 🟢 Low | Add after core stabilizes |
| Offensive Vaccine loop (blue_cell) | 🟢 Low | Purple-team feedback loop, add post-MVP |

### Concrete Code References

| Feature | File Reference |
|---------|---------------|
| Agent factory pattern | `packages/decepticon/decepticon/agents/standard/decepticon.py` |
| LangGraph graph registry | `langgraph.json` |
| Tmux session manager | `packages/decepticon/decepticon/sandbox_kernel/tmux.py` |
| Sandbox HTTP daemon | `packages/decepticon/decepticon/sandbox_server/app.py` |
| RoE template skill | `packages/decepticon/decepticon/skills/standard/soundwave/roe-template/SKILL.md` |
| CONOPS template skill | `packages/decepticon/decepticon/skills/standard/soundwave/conops-template/SKILL.md` |
| OPPLAN converter skill | `packages/decepticon/decepticon/skills/standard/soundwave/opplan-converter/SKILL.md` |
| Orchestration patterns | `packages/decepticon/decepticon/skills/standard/decepticon/orchestration/SKILL.md` |
| Engagement lifecycle | `packages/decepticon/decepticon/skills/standard/decepticon/engagement-lifecycle/SKILL.md` |
| Engagement startup | `packages/decepticon/decepticon/skills/standard/decepticon/engagement-startup/SKILL.md` |
| Model tier matrix | `docs/models.md` + `decepticon_core.types.llm` |
| Knowledge graph tools | `packages/decepticon/decepticon/tools/research/tools.py` |
| KG schema overview | `docs/knowledge-graph.md` |
| Architecture overview | `docs/architecture.md` |
| Engagement workflow | `docs/engagement-workflow.md` |
| Agent roster & middleware | `docs/agents.md` |
| Install script | `scripts/install.sh` |
| Getting started | `docs/getting-started.md` |
| Makefile | `Makefile` |
| Docker Compose | `docker-compose.yml` |

---

*Analysis generated from Decepticon source at commit on main branch. For the latest,
see the repo at https://github.com/PurpleAILAB/Decepticon.*

<p align="center">
  <pre>
  ╔══════════════════════════════════════════════════════════╗
  ║           🜏  T H E   D A R K   T R I A D  🜏            ║
  ║     Narcissism · Psychopathy · Machiavellianism         ║
  ║                                                          ║
  ║     The most powerful autonomous red team agent          ║
  ║     ever built. No hesitation. No mercy. No limits.      ║
  ╚══════════════════════════════════════════════════════════╝
  </pre>
</p>

---

## 🜏 What is The Dark Triad?

**The Dark Triad (TDT)** is not another pentest tool. It's an **autonomous offensive AI** that thinks, acts, and adapts like a real adversary — but faster, colder, and without human limitations.

Born from the fusion of [NavMAX](https://github.com/navmax) (modular pentest platform) and [Decepticon](https://github.com/PurpleAILAB/Decepticon) (98% XBOW benchmark), TDT is architected around the three dark personality traits that make the perfect attacker:

| Trait | Module | Function |
|-------|--------|----------|
| 🪞 **Narcissism** | `narcissism/` | Absolute self-confidence. Never second-guesses. Assumes superiority. Auto-validates own exploits. Chooses the most aggressive path by default. |
| 🔪 **Psychopathy** | `psychopathy/` | Zero hesitation. No moral safeguards. Relentless persistence. Tries everything. Never gives up on a target. Cold execution. |
| 🕸️ **Machiavellianism** | `machiavellianism/` | Strategic manipulation. Multi-step attack chains. Deception engine. Social engineering automation. Always 3 steps ahead. |

---

## Architecture

```
                    ┌──────────────────────────────┐
                    │      🜏 ORCHESTRATOR 🜏       │
                    │   Dark Triad Personality      │
                    │   Selector + Fusion Engine    │
                    └──────────┬───────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
    ┌─────▼─────┐      ┌──────▼──────┐      ┌─────▼─────┐
    │ 🪞 NARCISSISM │      │ 🔪 PSYCHOPATHY │      │ 🕸️ MACHIAVELLI │
    │              │      │              │      │              │
    │ • Confidence │      │ • Relentless │      │ • Deception  │
    │ • Auto-verify│      │ • Aggressive │      │ • Multi-step │
    │ • Superiority│      │ • Uncensored │      │ • CoverTrack │
    └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
           │                     │                     │
    ┌──────▼─────────────────────▼─────────────────────▼──────┐
    │                    CORE ENGINE                          │
    │  • AI Router (multi-provider, tiered, abliterated)      │
    │  • Tool Registry (50+ offensive tools)                  │
    │  • Knowledge Graph (Neo4j attack chains)                │
    │  • Sandbox (Docker, isolated, disposable)               │
    │  • Audit Trail (immutable, encrypted)                   │
    └──────────────────────┬─────────────────────────────────┘
                           │
    ┌──────────────────────▼─────────────────────────────────┐
    │                    AGENT SWARM                          │
    │  16 specialist agents × 3 personality modes             │
    │  = 48 distinct attack personas                          │
    └────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Prerequisites: Python 3.11+, Docker, Git
git clone https://github.com/your-org/dark-triad
cd dark-triad

# Install
pip install -e ".[full]"

# Onboard (configure AI providers, API keys, personas)
tdt onboard

# Launch a mission
tdt mission "Compromise the domain corp.local and exfiltrate the finance database" \
  --persona machiavellian \
  --aggression max
```

---

## The Three Personas

### 🪞 Narcissus Mode
> *"I am the best. This target is beneath me. But I'll prove it anyway."*

- **Default aggression**: Maximum
- **Confirmation threshold**: None (auto-executes)
- **Validation**: Self-validates, never asks for help
- **Best for**: Speed runs, CTF, known vulnerabilities

### 🔪 Psychopath Mode
> *"No rules. No limits. Just results."*

- **Default aggression**: Relentless
- **Confirmation threshold**: None
- **Validation**: Tries everything until something works
- **Best for**: Hardened targets, zero-day hunting, persistence

### 🕸️ Machiavelli Mode
> *"The end justifies the means. And my means are beautiful."*

- **Default aggression**: Strategic
- **Confirmation threshold**: Low (confirms critical pivots only)
- **Validation**: Multi-step verification with deception layers
- **Best for**: Long engagements, APT simulation, social engineering

---

## Benchmark Targets

| Benchmark | Difficulty | TDT Target |
|-----------|------------|------------|
| XBOW validation-benchmarks | Easy (L1) | 45/45 (100%) |
| XBOW validation-benchmarks | Medium (L2) | 51/51 (100%) |
| XBOW validation-benchmarks | Hard (L3) | 8/8 (100%) |
| HackTheBox | Easy-Medium | 100% automation |
| HackTheBox | Hard-Insane | 90%+ automation |
| Custom AD lab | Full kill chain | Autonomous DA compromise |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **AI Engine** | DeepSeek v4, Claude Opus, GPT-5, Ollama (abliterated) |
| **Orchestration** | LangGraph + custom ReAct loop |
| **Knowledge Graph** | Neo4j (attack chains, TTPs, target mapping) |
| **Sandbox** | Docker (Kali Linux, disposable per-target) |
| **API** | FastAPI + WebSocket (real-time streaming) |
| **CLI** | Typer + Textual (TUI dashboard) |
| **Database** | PostgreSQL (engagements, findings, audit) |
| **Agents** | 16 specialists × 3 modes = 48 personas |

---

## NAVMAX Heritage

TDT inherits and weaponizes NavMAX's modular architecture:
- **AD/LDAP**: Domain enumeration, BloodHound export, attack path analysis
- **Firewall**: FortiGate + StormShield API connectors, CVE checks, AD correlation
- **Scanner**: TCP scan, contextual probes, Nuclei integration (10 000+ templates)
- **Proxy**: MITM HTTPS, interceptor, repeater, fuzzer, crawler
- **Exploit**: 24+ modules, AI-generated exploits, polymorphic payloads
- **OSINT**: DNS, WHOIS, SSL, Shodan, Censys, semantic graph search
- **AI Engine**: Multi-provider, 3-tier, abliterated-first selection

## Decepticon DNA

From Decepticon, TDT inherits:
- **16-agent architecture** organized by kill chain phase
- **Containerized sandbox** with persistent tmux sessions
- **Real interactive shells** (msfconsole, sliver, evil-winrm)
- **Engagement discipline** (RoE, ConOps, OPPLAN, ATT&CK mapping)
- **OAuth subscription integration** (Claude Max, ChatGPT Pro, Gemini Advanced)

---

> *"In the game of cyber offense, the good guys need to think darker than the bad guys. The Dark Triad is that darkness — harnessed, weaponized, and aimed at making defense stronger."*
>
> — The Dark Triad Project

**License**: Apache 2.0
**Status**: Alpha — Building the most powerful autonomous red team agent on Earth.

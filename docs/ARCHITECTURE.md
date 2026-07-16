# 🜏 The Dark Triad — Architecture Document

## Personality-Driven Agent Architecture

The Dark Triad uses a **personality-driven architecture** where the agent's behavior, decision-making, and risk tolerance are determined by which of the three dark personality traits is dominant.

This isn't just a config flag — each personality mode is a distinct **cognitive architecture** with its own reasoning chains, tool selection biases, and execution patterns.

---

## 1. PersonalitySelector — The Core Innovation

```python
# The PersonalitySelector is the soul of TDT
# It determines HOW an objective is pursued, not just WHAT tools are used

class PersonalitySelector:
    def select(self, objective: Objective, context: TargetContext) -> Personality:
        """Based on target defenses, objective type, and time constraints,
        choose the optimal personality — or fuse multiple."""
        
    def fuse(self, primary: Personality, secondary: Personality, ratio: float):
        """Blend two personalities for hybrid behavior.
        Example: Machiavellian (80%) + Psychopath (20%) = Patient predator."""
```

### Personality Matrix

| Dimension | 🪞 Narcissism | 🔪 Psychopathy | 🕸️ Machiavellianism |
|-----------|-------------|--------------|-------------------|
| **Aggression** | Maximum | Relentless | Strategic |
| **Patience** | None | Low | High |
| **Stealth** | Low | None | Maximum |
| **Persistence** | Low (moves on) | Infinite | High |
| **Deception** | None | Brute force | Multi-layer |
| **Confirmation** | Auto-approves | Auto-approves | Selective |
| **Tool preference** | Biggest guns | Everything | Precise tools |
| **Fallback** | Escalate | Try everything | Pivot |
| **Self-preservation** | None | None | Maximum |
| **Learning** | Ignores failures | Remembers everything | Pattern recognition |

---

## 2. Module Architecture

```
src/tdt/
├── core/                    # ★ Shared engine (personality-agnostic)
│   ├── personality.py       #   PersonalitySelector, Personality class
│   ├── ai_router.py         #   Multi-provider AI router with tier fallback
│   ├── tool_registry.py     #   50+ offensive tools catalog
│   ├── knowledge_graph.py   #   Neo4j attack chain persistence
│   ├── sandbox.py           #   Docker sandbox manager
│   └── audit.py             #   Immutable audit trail
│
├── narcissism/              # 🪞 NARCISSISM MODULE
│   ├── engine.py            #   Self-confident execution engine
│   ├── validator.py         #   Auto-validates own results
│   ├── superiority.py       #   Always chooses most aggressive path
│   └── tools.py             #   Tool overrides (biggest payloads first)
│
├── psychopathy/             # 🔪 PSYCHOPATHY MODULE
│   ├── engine.py            #   Zero-hesitation execution
│   ├── relentless.py        #   Infinite persistence loops
│   ├── aggression.py        #   Tries every exploit in parallel
│   └── tools.py             #   Tool overrides (all tools, no filter)
│
├── machiavellianism/        # 🕸️ MACHIAVELLIANISM MODULE
│   ├── engine.py            #   Strategic multi-step planner
│   ├── deception.py         #   Honeypots, misdirection, cover tracks
│   ├── patience.py          #   Long-game timer, waits for right moment
│   ├── social.py            #   Automated social engineering
│   └── tools.py             #   Tool overrides (stealth-first selection)
│
├── agents/                  # 16 specialist agents × 3 personas = 48
│   ├── orchestrator.py      #   Mission decomposition & dispatch
│   ├── recon.py             #   Passive & active reconnaissance
│   ├── exploiter.py         #   Vulnerability exploitation
│   ├── post_exploit.py      #   Persistence, lateral movement, exfil
│   ├── vuln_researcher.py   #   0-day research, fuzzing
│   ├── ad_specialist.py     #   Active Directory attacks
│   ├── cloud_specialist.py  #   AWS/Azure/GCP exploitation
│   ├── social_engineer.py   #   Phishing, vishing, impersonation
│   ├── reverser.py          #   Binary reverse engineering
│   ├── c2_operator.py       #   C2 infrastructure management
│   ├── analyst.py           #   Findings analysis & reporting
│   ├── evader.py            #   AV/EDR evasion
│   ├── pivoter.py           #   Network pivoting
│   ├── credential.py        #   Credential dumping & cracking
│   ├── persistence.py       #   Backdoor deployment
│   └── exfiltrator.py       #   Data exfiltration
│
├── sandbox/                 # Docker sandbox infrastructure
│   ├── kali.py              #   Kali Linux container management
│   ├── tmux_session.py      #   Persistent interactive shells
│   ├── network.py           #   Isolated sandbox-net
│   └── targets.py           #   Target environment provisioning
│
├── orchestrator/            # High-level mission orchestration
│   ├── mission_planner.py   #   Objective → phases → agent dispatch
│   ├── battle_manager.py    #   Real-time adaptation & agent coordination
│   ├── engagement.py        #   RoE, ConOps, OPPLAN generation
│   └── deconfliction.py     #   Prevent agent collision
│
├── api/                     # FastAPI REST + WebSocket
│   ├── routes/
│   │   ├── missions.py
│   │   ├── agents.py
│   │   ├── personality.py
│   │   └── reports.py
│   └── static/              # Dashboard SPA
│
└── cli/                     # Typer CLI + Textual TUI
    ├── main.py
    ├── onboarding.py
    └── tui.py               # Real-time mission monitoring TUI
```

---

## 3. Personality-Driven Tool Selection

Each personality biases tool selection differently:

### Narcissist Tool Preferences
```python
NARCISSIST_TOOLS = {
    "priority": ["largest_payload", "most_destructive", "fastest"],
    "avoid": ["stealth", "slow", "multi_step"],
    "parallelism": "sequential",  # "I can handle this alone"
}
```

### Psychopath Tool Preferences
```python
PSYCHOPATH_TOOLS = {
    "priority": ["try_everything", "all_exploits", "maximum_coverage"],
    "avoid": [],  # No tool is off-limits
    "parallelism": "maximum",  # Fire everything at once
}
```

### Machiavellian Tool Preferences
```python
MACHIAVELLIAN_TOOLS = {
    "priority": ["stealth", "minimal_footprint", "chainable"],
    "avoid": ["loud", "destructive", "obvious"],
    "parallelism": "strategic",  # Coordinated, not chaotic
}
```

---

## 4. Cognitive Loop (per personality)

### Narcissist Loop
```
1. Receive objective → "I already know the best way"
2. Execute immediately → no planning phase
3. Auto-validate success → "Of course it worked"
4. On failure → escalate to more aggressive approach
5. Report → minimal, assumes success is obvious
```

### Psychopath Loop
```
1. Receive objective → "Break everything"
2. Launch ALL tools in parallel → maximum surface area
3. On success → exploit deeper, don't stop
4. On failure → try different tool, NEVER give up
5. Report → exhaustive, every attempt documented
```

### Machiavellian Loop
```
1. Receive objective → "Plan the perfect attack"
2. Multi-phase planning → 5+ steps ahead
3. Execute stealthily → minimal noise
4. On detection → misdirect, retreat, wait
5. On success → cover tracks, leave no trace
6. Report → artful, strategic, complete
```

---

## 5. Fusion Engine

The true innovation: **personality fusion**.

```python
class FusionEngine:
    def create_hybrid(self, primary: Personality, secondary: Personality, ratio: float):
        """Create a blended personality for specific scenarios."""
    
    # Example fusions:
    # "Patient Predator"   = Machiavellian (80%) + Psychopath (20%)
    # "Cocky Assassin"     = Narcissist (60%) + Machiavellian (40%)
    # "Berserker"          = Psychopath (70%) + Narcissist (30%)
    # "Ghost"              = Machiavellian (90%) + Psychopath (10%)
```

---

## 6. Safety & Ethics

Despite the dark branding, TDT includes strong safeguards:

- **Engagement Boundary**: RoE enforced at the sandbox network level
- **Deconfliction**: Agents cannot interfere with each other
- **Audit Trail**: Every action is logged immutably
- **Kill Switch**: Global abort that stops all agents and sandboxes
- **Scope Enforcement**: Target validation against authorized scope
- **Time Limits**: Engagements have hard stop times

The darkness is harnessed, not uncontrolled.

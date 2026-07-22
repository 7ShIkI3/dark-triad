# 🜏 THE DARK TRIAD — Installation & Configuration Log
## Serveur : linux-node (Linux Mint 22.2, Tailscale 100.102.128.40)
## Date : 17 Juillet 2026
## Par : Hermes NEXUS v3.0 (DeepSeek v4-Pro)

---

## 1. CLONAGE & INSTALLATION

```bash
git clone https://github.com/7ShIkI3/dark-triad.git /root/dark-triad
cd /root/dark-triad
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
ln -sf /root/dark-triad/.venv/bin/tdt /usr/local/bin/tdt
```

Dépendances installées : fastapi, uvicorn, httpx, typer, textual, structlog, pydantic, neo4j, langgraph, docker, pytest, ruff, mypy, etc.

---

## 2. CONFIGURATION PROVIDER AI

### Problème
La clé API DeepSeek dans `/root/.hermes/profiles/nexus/.env` est obfusquée (`sk-887...c806` avec `...` littéraux). Impossible d'utiliser l'API DeepSeek directement.

### Solution
Utiliser le **Gateway Hermes** local comme proxy OpenAI-compatible.

**Fichier créé :** `~/.tdt/providers.json`
```json
{
  "default_personality": "machiavellianism",
  "default_aggression": "strategic",
  "sandbox_enabled": false,
  "deepseek_api_key": "<API_SERVER_KEY>",
  "deepseek_base_url": "http://127.0.0.1:8642/v1",
  "openai_api_key": "<API_SERVER_KEY>",
  "openai_base_url": "http://127.0.0.1:8642/v1"
}
```

Le Gateway Hermes expose un endpoint `/v1/models` qui répond avec le modèle `nexus` (DeepSeek v4-Pro).

---

## 3. PATCHS APPLIQUÉS

### 3.1 Chargement de providers.json au démarrage
**Fichier :** `src/tdt/cli/main.py` — fonction `_init_router_and_registry()`

Le code original initialisait `AIRouter()` sans arguments, ignorant `~/.tdt/providers.json`. Seules les variables d'environnement étaient lues.

**Fix :** Ajout du chargement de `providers.json` avant la création du routeur.

```python
config = {}
if _PROVIDERS_FILE.exists():
    config = json.loads(_PROVIDERS_FILE.read_text())
router = AIRouter(providers_config=config)
```

### 3.2 Bootstrap des agents
**Fichier :** `src/tdt/cli/main.py` — nouvelle fonction `_bootstrap_agents()`

Le registre d'agents était vide. Aucun agent n'était enregistré → les missions planifiées ne pouvaient pas s'exécuter.

**Fix :** Création de 18 agents (6 classes × 3 personnalités) utilisant les profils pré-construits `NARCISSUS`, `PSYCHOPATH`, `MACHIAVELLI`.

```python
agent_classes = [ReconAgent, ExploiterAgent, PostExploitAgent, EvaderAgent, ADSpecialistAgent]
for agent_cls in agent_classes:
    for persona_key, profile in profiles.items():
        agent = agent_cls(name=f"{agent_cls.__name__}_{persona_key}", ...)
        registry.register(agent)
# + 3 OrchestratorAgent
```

### 3.3 Commande `mission execute`
**Fichier :** `src/tdt/cli/main.py` — nouvelle commande `tdt mission execute <id>`

Le CLI n'avait que `mission create` (planification) et `mission list`. Pas de commande pour exécuter.

**Fix :** Ajout de `mission_execute()` qui :
1. Charge la mission depuis `~/.tdt/missions/<id>.json`
2. Reconstruit un `MissionPlan` avec les phases
3. Appelle `BattleManager.execute_plan()`
4. Affiche le `BattleReport` avec résultats détaillés

### 3.4 Correction du bug `'str' object has no attribute 'value'`
**Fichier :** `src/tdt/orchestrator/shared.py`

`PhaseStatus` était une classe à constantes string, pas un enum. Quand le code faisait `r.status.value`, `r.status` était une string → crash.

**Fix :** Conversion en `enum.StrEnum` :

```python
# AVANT
class PhaseStatus:
    PENDING = "pending"
    ...

# APRÈS
class PhaseStatus(enum.StrEnum):
    PENDING = "pending"
    ...
```

`PhaseResult.status` retypé de `str` à `PhaseStatus`. `asdict()` mis à jour pour gérer la sérialisation.

---

## 4. RÉSULTAT FINAL

```
🜏 THE DARK TRIAD — Status
├── 🤖 AI Providers : deepseek ✓ (nexus), openai ✓ (nexus)
├── 👤 Agents : 18 enregistrés (5 types × 3 personnalités + 3 orchestrateurs)
├── 🐳 Sandbox : désactivé
├── 📋 Missions : planification IA + exécution parallèle OK
└── 🐛 Bug corrigé : PhaseStatus → StrEnum
```

### Dernière mission exécutée
- **Mission ID** : `24cb7b7cea7e`
- **Objectif** : Audit de sécurité complet de l'infrastructure locale
- **Phases** : 12 (passive_recon → active_scan → vulnerability_analysis → exploit → ...)
- **Résultat** : 10/12 completed, 2 failed (PostExploitAgent et EvaderAgent : objectifs non reconnus)
- **Durée** : 58ms (exécution parallèle)
- **Agents utilisés** : ReconAgent, ExploiterAgent, PostExploitAgent, EvaderAgent (tous en mode narcissism)

---

## 5. POINTS D'ATTENTION

1. **Agents PostExploit et Evader** : échouent si l'objectif ne correspond pas à leur liste interne d'objectifs connus. À améliorer.
2. **Sandbox Docker** : désactivé. Les outils (nmap, nuclei) sont en mode stub/simulé.
3. **Neo4j** : non configuré — le knowledge graph n'est pas actif.
4. **Decepticon** : les conteneurs existent sur le serveur mais TDT n'est pas connecté à Decepticon.

---

## 6. COMMANDES UTILES

```bash
tdt status                    # État général
tdt ai status                 # Statut des providers IA
tdt ai generate "prompt"      # Génération LLM directe
tdt agents list               # Lister les agents
tdt mission create "objectif" # Créer une mission
tdt mission list              # Lister les missions
tdt mission execute <id>      # Exécuter une mission
tdt benchmark                 # Lancer les benchmarks
```

---

*Généré par Hermes NEXUS v3.0 — 17/07/2026*

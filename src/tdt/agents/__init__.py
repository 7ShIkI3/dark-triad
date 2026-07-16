"""The Dark Triad — Agent Package.

Specialist personality agents: orchestration, recon, and exploitation.
"""

from tdt.agents.ad_specialist import ADSpecialistAgent, DomainInfo, KerberoastTicket
from tdt.agents.base import AgentResult, AgentStep, BaseAgent
from tdt.agents.evader import EvaderAgent, EvasionTechnique
from tdt.agents.exploiter import ExploitAttempt, ExploiterAgent
from tdt.agents.orchestrator import OrchestratorAgent
from tdt.agents.post_exploit import PersistenceMethod, PostExploitAgent
from tdt.agents.recon import ReconAgent, ReconFindings
from tdt.orchestrator.shared import (
    MissionPhase,
    MissionPlan,
)

__all__ = [
    # Base
    "BaseAgent",
    "AgentResult",
    "AgentStep",
    # Post-exploit
    "PostExploitAgent",
    "PersistenceMethod",
    # AD
    "ADSpecialistAgent",
    "DomainInfo",
    "KerberoastTicket",
    # Evasion
    "EvaderAgent",
    "EvasionTechnique",
    # Orchestrator
    "OrchestratorAgent",
    "MissionPlan",
    "MissionPhase",
    # Recon
    "ReconAgent",
    "ReconFindings",
    # Exploiter
    "ExploiterAgent",
    "ExploitAttempt",
]

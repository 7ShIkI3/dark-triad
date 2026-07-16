"""The Dark Triad — Orchestrator Package.

Mission planning engine: NL decomposition, agent assignment,
dependency graph construction, duration/risk estimation.
"""

from __future__ import annotations

from tdt.orchestrator.battle_manager import BattleManager
from tdt.orchestrator.engagement import EngagementBuilder
from tdt.orchestrator.mission_planner import (
    MissionPhase,
    MissionPlan,
    MissionPlanner,
    PhaseStatus,
)

__all__ = [
    "BattleManager",
    "EngagementBuilder",
    "MissionPlanner",
    "MissionPlan",
    "MissionPhase",
    "PhaseStatus",
]

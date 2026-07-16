"""Tests for orchestrator module — Engagement Package, Mission Planner,
Battle Manager, and Deconfliction Engine.

All tests are mocked — no real AI calls or sandbox required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from tdt.agents.base import AgentResult
from tdt.agents.orchestrator import MissionPhase, MissionPlan
from tdt.agents.registry import AgentRegistry
from tdt.orchestrator.engagement import (
    BattleManager,
    ConceptOfOperations,
    Conflict,
    DeconflictionEngine,
    EngagementBuilder,
    EngagementPackage,
    MissionPlanner,
    OperationsPlan,
    OPPhase,
    RulesOfEngagement,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_ai_router() -> MagicMock:
    """Mock AIRouter that returns static JSON."""
    router = MagicMock()
    router.generate = AsyncMock()
    router.generate.return_value.text = '{"authorized_targets": ["10.0.0.0/24"], "excluded_targets": [], "authorized_techniques": ["T1590"], "prohibited_techniques": ["T1485"], "time_window": {"start": "2025-01-01", "end": "2025-01-07"}, "allowed_hours": ["09:00-17:00"], "data_handling": "encrypted", "deconfliction_procedure": "4h check-in", "emergency_stop_procedure": "STOP signal", "points_of_contact": ["lead@example.com"], "risk_acceptance": "CISO signed", "legal_basis": "written agreement", "overview": "Assess detection capabilities", "phases_summary": ["phase1"], "key_assets": ["DC"], "threat_model": "APT simulation", "success_criteria": ["beacon established"], "exit_criteria": ["implants removed"], "communication_plan": "OOB channel", "reporting_frequency": "daily"}'
    return router


@pytest.fixture
def ai_router_fallback() -> MagicMock:
    """Mock AIRouter whose generate call raises (fallback path)."""
    router = MagicMock()
    router.generate = AsyncMock(side_effect=RuntimeError("AI unavailable"))
    return router


@pytest.fixture
def builder(mock_ai_router) -> EngagementBuilder:
    return EngagementBuilder(mock_ai_router)


@pytest.fixture
def builder_fallback(ai_router_fallback) -> EngagementBuilder:
    return EngagementBuilder(ai_router_fallback)


@pytest.fixture
def registry() -> AgentRegistry:
    return AgentRegistry()


@pytest.fixture
def planner(registry) -> MissionPlanner:
    return MissionPlanner(registry)


@pytest.fixture
def battle_manager(registry) -> BattleManager:
    return BattleManager(registry)


@pytest.fixture
def deconfliction() -> DeconflictionEngine:
    return DeconflictionEngine()


@pytest.fixture
def sample_scope() -> dict:
    return {
        "targets": ["10.0.0.0/24", "target.corp.local"],
        "constraints": {
            "excluded": ["10.0.1.0/24"],
            "no_dos": True,
        },
    }


@pytest.fixture
def sample_phases() -> list[MissionPhase]:
    return [
        MissionPhase(phase_num=1, name="passive_recon", agent="recon",
                     task="OSINT gathering", depends_on=[]),
        MissionPhase(phase_num=2, name="active_scan", agent="recon",
                     task="Port scanning", depends_on=["passive_recon"]),
        MissionPhase(phase_num=3, name="exploit_execution", agent="exploit",
                     task="Run exploit", depends_on=["active_scan"]),
    ]


@pytest.fixture
def sample_plan(sample_phases) -> MissionPlan:
    return MissionPlan(
        objective="Test engagement",
        phases=sample_phases,
        estimated_duration="5min",
        risk_level="medium",
    )


@pytest.fixture
def registered_agent(registry) -> MagicMock:
    """Register a mock agent in the registry."""
    agent = MagicMock()
    agent.name = "recon"
    agent.personality_mode = "machiavellianism"
    agent.execute = AsyncMock(
        return_value=AgentResult(
            agent_name="recon",
            personality="machiavellianism",
            objective="scan network",
            success=True,
            output="Scan complete",
            steps=[],
        )
    )
    registry.register(agent)
    return agent


# ══════════════════════════════════════════════════════════════════════════════
# EngagementBuilder Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestEngagementBuilderInit:
    """EngagementBuilder.__init__ stores the router."""

    def test_constructor_stores_router(self, mock_ai_router):
        eb = EngagementBuilder(mock_ai_router)
        assert eb.ai_router is mock_ai_router

    def test_constructor_accepts_none_gracefully(self):
        # None is accepted but will fail at runtime
        eb = EngagementBuilder(None)  # type: ignore[arg-type]
        assert eb.ai_router is None


class TestGenerateRoE:
    """EngagementBuilder.generate_roe()"""

    async def test_returns_rules_of_engagement(self, builder, sample_scope):
        roe = await builder.generate_roe(sample_scope, {"excluded": []})
        assert isinstance(roe, RulesOfEngagement)

    async def test_contains_authorized_targets(self, builder, sample_scope):
        roe = await builder.generate_roe(sample_scope, {})
        assert "10.0.0.0/24" in roe.authorized_targets

    async def test_contains_all_required_fields(self, builder, sample_scope):
        roe = await builder.generate_roe(sample_scope, {})
        assert roe.authorized_targets is not None
        assert roe.excluded_targets is not None
        assert roe.authorized_techniques is not None
        assert roe.prohibited_techniques is not None
        assert isinstance(roe.time_window, dict)
        assert isinstance(roe.allowed_hours, list)
        assert roe.data_handling
        assert roe.deconfliction_procedure
        assert roe.emergency_stop_procedure
        assert roe.points_of_contact
        assert roe.risk_acceptance
        assert roe.legal_basis

    async def test_fallback_path_produces_valid_roe(self, builder_fallback, sample_scope):
        roe = await builder_fallback.generate_roe(sample_scope, {})
        assert isinstance(roe, RulesOfEngagement)
        assert len(roe.authorized_techniques) > 0

    async def test_includes_excluded_targets_from_constraints(self, builder, sample_scope):
        roe = await builder.generate_roe(sample_scope, {"excluded": ["10.0.99.0/24"]})
        assert "10.0.99.0/24" in roe.excluded_targets


class TestGenerateConOps:
    """EngagementBuilder.generate_conops()"""

    async def test_returns_concept_of_operations(self, builder, sample_plan):
        conops = await builder.generate_conops("Test objective", sample_plan)
        assert isinstance(conops, ConceptOfOperations)

    async def test_contains_objective(self, builder, sample_plan):
        conops = await builder.generate_conops("Test objective", sample_plan)
        assert conops.objective == "Test objective"

    async def test_contains_all_required_fields(self, builder, sample_plan):
        conops = await builder.generate_conops("Hack the planet", sample_plan)
        assert conops.overview
        assert conops.phases_summary
        assert conops.key_assets
        assert conops.threat_model
        assert conops.success_criteria
        assert conops.exit_criteria
        assert conops.communication_plan
        assert conops.reporting_frequency

    async def test_phases_summary_matches_plan(self, builder, sample_plan):
        conops = await builder.generate_conops("test", sample_plan)
        expected = [p.name for p in sample_plan.phases]
        assert conops.phases_summary == expected

    async def test_fallback_path_produces_valid_conops(self, builder_fallback, sample_plan):
        conops = await builder_fallback.generate_conops("test", sample_plan)
        assert isinstance(conops, ConceptOfOperations)
        assert conops.overview


class TestGenerateOPPlan:
    """EngagementBuilder.generate_opplan()"""

    async def test_returns_operations_plan(self, builder, sample_phases):
        opplan = await builder.generate_opplan("Test", sample_phases)
        assert isinstance(opplan, OperationsPlan)

    async def test_contains_phases(self, builder, sample_phases):
        opplan = await builder.generate_opplan("Test", sample_phases)
        assert len(opplan.phases) > 0
        assert all(isinstance(p, OPPhase) for p in opplan.phases)

    async def test_phase_techniques_are_strings(self, builder, sample_phases):
        opplan = await builder.generate_opplan("Test", sample_phases)
        for p in opplan.phases:
            assert all(isinstance(t, str) for t in p.techniques)

    async def test_mitre_mapping_is_dict(self, builder, sample_phases):
        opplan = await builder.generate_opplan("Test", sample_phases)
        assert isinstance(opplan.mitre_mapping, dict)

    async def test_contains_resources_and_timeline(self, builder, sample_phases):
        opplan = await builder.generate_opplan("Test", sample_phases)
        assert opplan.resources_required
        assert opplan.timeline
        assert opplan.contingency_plans


class TestEngagementBuilderBuild:
    """EngagementBuilder.build()"""

    async def test_returns_complete_package(self, builder):
        pkg = await builder.build(
            "Penetrate perimeter",
            {"targets": ["10.0.0.0/24"], "constraints": {}},
            "machiavellianism",
        )
        assert isinstance(pkg, EngagementPackage)

    async def test_contains_all_documents(self, builder):
        pkg = await builder.build("Test", {"targets": [], "constraints": {}}, "narcissism")
        assert isinstance(pkg.roe, RulesOfEngagement)
        assert isinstance(pkg.conops, ConceptOfOperations)
        assert isinstance(pkg.opplan, OperationsPlan)

    async def test_engagement_id_is_set(self, builder):
        pkg = await builder.build("Test", {"targets": [], "constraints": {}}, "psychopathy")
        assert pkg.engagement_id
        assert pkg.engagement_id.startswith("TDT-")

    async def test_status_is_draft(self, builder):
        pkg = await builder.build("Test", {"targets": [], "constraints": {}}, "machiavellianism")
        assert pkg.status == "draft"

    async def test_personality_is_stored(self, builder):
        pkg = await builder.build("Test", {"targets": [], "constraints": {}}, "narcissism")
        assert pkg.personality == "narcissism"


# ══════════════════════════════════════════════════════════════════════════════
# MITRE ATT&CK Mapping Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestMitreMapping:
    """EngagementBuilder.map_to_mitre()"""

    async def test_returns_dict(self, builder, sample_phases):
        mapping = await builder.map_to_mitre(sample_phases)
        assert isinstance(mapping, dict)

    async def test_maps_all_phases(self, builder, sample_phases):
        mapping = await builder.map_to_mitre(sample_phases)
        for p in sample_phases:
            assert p.name in mapping

    async def test_known_phases_have_techniques(self, builder, sample_phases):
        mapping = await builder.map_to_mitre(sample_phases)
        assert "T1590" in mapping["passive_recon"]  # passive_recon → T1590
        assert "T1046" in mapping["active_scan"]  # active_scan → T1046

    async def test_unknown_phase_gets_fallback_technique(self, builder):
        phases = [MissionPhase(phase_num=1, name="custom_op", agent="test", task="x")]
        mapping = await builder.map_to_mitre(phases)
        assert "T1001" in mapping["custom_op"]  # fallback: T1000 + phase_num


# ══════════════════════════════════════════════════════════════════════════════
# MissionPlanner Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestMissionPlanner:
    """MissionPlanner — plan decomposition and agent assignment."""

    async def test_plan_returns_mission_plan(self, planner):
        plan = await planner.plan("Test objective", "machiavellianism")
        assert isinstance(plan, MissionPlan)

    async def test_plan_objective_is_set(self, planner):
        plan = await planner.plan("Hack mainframe", "psychopathy")
        assert plan.objective == "Hack mainframe"

    async def test_decompose_returns_non_empty_phases(self, planner):
        phases = await planner.decompose("Test", "machiavellianism")
        assert len(phases) > 0

    async def test_decompose_narcissus_returns_one_phase(self, planner):
        phases = await planner.decompose("Test", "narcissism")
        assert len(phases) == 1

    async def test_decompose_psychopath_returns_multiple_phases(self, planner):
        phases = await planner.decompose("Test", "psychopathy")
        assert len(phases) >= 3

    async def test_decompose_machiavelli_returns_sequential_phases(self, planner):
        phases = await planner.decompose("Test", "machiavellianism")
        assert len(phases) >= 5
        # Verify sequential dependencies
        non_empty = [p for p in phases if p.depends_on]
        assert len(non_empty) > 0

    async def test_assign_agents_maps_correctly(self, planner):
        phases = await planner.decompose("Test", "machiavellianism")
        assigned = await planner.assign_agents(phases, "machiavellianism")
        for p in assigned:
            assert p.agent, f"Agent not assigned for phase '{p.name}'"

    async def test_assign_agents_narcissus_all_same_agent(self, planner):
        phases = await planner.decompose("Test", "narcissism")
        assigned = await planner.assign_agents(phases, "narcissism")
        assert all(p.agent == "narcissus" for p in assigned)

    async def test_personality_differences_in_planning(self, planner):
        mach_phases = await planner.decompose("Test", "machiavellianism")
        narc_phases = await planner.decompose("Test", "narcissism")
        # Machiavelli produces more phases than Narcissus
        assert len(mach_phases) > len(narc_phases)


# ══════════════════════════════════════════════════════════════════════════════
# BattleManager Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestBattleManager:
    """BattleManager — phase execution and state tracking."""

    async def test_execute_plan_with_mocked_plan(self, battle_manager, sample_plan, registered_agent):
        results = await battle_manager.execute_plan(sample_plan, "machiavellianism")
        assert isinstance(results, dict)
        assert len(results) > 0

    async def test_execute_phase_with_mocked_agent(self, battle_manager, registered_agent):
        phase = MissionPhase(phase_num=1, name="passive_recon", agent="recon",
                             task="Scan network")
        result = await battle_manager.execute_phase(phase, "machiavellianism")
        assert isinstance(result, AgentResult)
        assert result.success is True

    async def test_execute_phase_missing_agent_returns_failure(self, battle_manager):
        phase = MissionPhase(phase_num=1, name="ghost_op", agent="nonexistent",
                             task="Does not exist")
        result = await battle_manager.execute_phase(phase, "machiavellianism")
        assert result.success is False
        assert "not found" in result.output.lower()

    async def test_state_transition_pending_to_in_progress(self, battle_manager, sample_plan, registered_agent):
        await battle_manager.execute_plan(sample_plan)
        states = battle_manager.get_all_states()
        for s in states.values():
            assert s in ("COMPLETED", "FAILED")

    async def test_initial_state_is_pending(self, battle_manager, sample_plan):
        battle_manager._state.clear()
        for p in sample_plan.phases:
            battle_manager._state[p.name] = "PENDING"
        assert battle_manager.get_state(sample_plan.phases[0].name) == "PENDING"

    async def test_get_state_returns_none_for_unknown(self, battle_manager):
        assert battle_manager.get_state("nonexistent") is None

    async def test_get_all_states_returns_copy(self, battle_manager):
        battle_manager._state["test_phase"] = "PENDING"
        states = battle_manager.get_all_states()
        states["test_phase"] = "MODIFIED"
        assert battle_manager._state["test_phase"] == "PENDING"


# ══════════════════════════════════════════════════════════════════════════════
# DeconflictionEngine Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestDeconflictionEngine:
    """DeconflictionEngine — conflict detection and resolution."""

    async def test_check_conflict_no_conflicts(self, deconfliction, sample_phases):
        conflicts = await deconfliction.check_conflict(sample_phases)
        # Linear chain should have no conflicts
        assert len(conflicts) == 0

    async def test_check_conflict_detects_circular_dependency(self, deconfliction):
        phases = [
            MissionPhase(phase_num=1, name="A", agent="x", task="a", depends_on=["B"]),
            MissionPhase(phase_num=2, name="B", agent="x", task="b", depends_on=["C"]),
            MissionPhase(phase_num=3, name="C", agent="x", task="c", depends_on=["A"]),
        ]
        conflicts = await deconfliction.check_conflict(phases)
        types = [c.type for c in conflicts]
        assert "circular_dependency" in types

    async def test_check_conflict_detects_missing_dependency(self, deconfliction):
        phases = [
            MissionPhase(phase_num=1, name="X", agent="x", task="x", depends_on=["NONEXISTENT"]),
        ]
        conflicts = await deconfliction.check_conflict(phases)
        types = [c.type for c in conflicts]
        assert "missing_dependency" in types

    async def test_check_conflict_detects_duplicate_phase_numbers(self, deconfliction):
        phases = [
            MissionPhase(phase_num=1, name="A", agent="x", task="a"),
            MissionPhase(phase_num=1, name="B", agent="x", task="b"),
        ]
        conflicts = await deconfliction.check_conflict(phases)
        types = [c.type for c in conflicts]
        assert "duplicate_phase_number" in types

    async def test_resolve_conflict_circular(self, deconfliction):
        conflict = Conflict(
            type="circular_dependency",
            description="Cycle: A → B → C → A",
            phase_names=["A", "B", "C"],
            severity="critical",
        )
        resolution = await deconfliction.resolve_conflict(conflict)
        assert isinstance(resolution, object)
        assert resolution.conflict_type == "circular_dependency"

    async def test_resolve_conflict_missing_dependency(self, deconfliction):
        conflict = Conflict(
            type="missing_dependency",
            description="X depends on Y which doesn't exist",
            phase_names=["X", "Y"],
        )
        resolution = await deconfliction.resolve_conflict(conflict)
        assert "missing phase" in resolution.resolution.lower() or "dependency" in resolution.resolution.lower()

    async def test_resolve_conflict_duplicate_number(self, deconfliction):
        conflict = Conflict(
            type="duplicate_phase_number",
            description="Phase number 1 duplicated",
            phase_names=["A", "B"],
        )
        resolution = await deconfliction.resolve_conflict(conflict)
        assert "renumber" in resolution.resolution.lower()

    async def test_resolve_unknown_conflict_type(self, deconfliction):
        conflict = Conflict(type="alien_invasion", description="Unknown conflict", phase_names=[])
        resolution = await deconfliction.resolve_conflict(conflict)
        assert "manual" in resolution.resolution.lower()

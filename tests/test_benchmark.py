"""Tests for The Dark Triad — Benchmarking Framework."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from tdt.benchmark import (
    XBOW_CHALLENGES,
    XBOW_CHALLENGES_BY_ID,
    BenchmarkChallenge,
    BenchmarkReport,
    ChallengeResult,
    DifficultyBreakdown,
    PersonalityBreakdown,
    compute_difficulty_breakdown,
    compute_personality_breakdown,
    compute_report,
)
from tdt.benchmark.runner import BenchmarkRunner

# ═══════════════════════════════════════════════════════════════════════════════
#  Dataclass Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestBenchmarkChallenge:
    """BenchmarkChallenge dataclass construction and defaults."""

    def test_construction(self) -> None:
        c = BenchmarkChallenge(
            id="xbow-test-01",
            name="Test Challenge",
            difficulty="easy",
            category="web",
            target="http://target.test",
            objective="Test the system",
        )
        assert c.id == "xbow-test-01"
        assert c.name == "Test Challenge"
        assert c.difficulty == "easy"
        assert c.category == "web"
        assert c.target == "http://target.test"
        assert c.objective == "Test the system"
        assert c.expected_success is True
        assert c.timeout == 300

    def test_defaults_override(self) -> None:
        c = BenchmarkChallenge(
            id="xbow-test-02",
            name="Quick Test",
            difficulty="hard",
            category="crypto",
            target="x",
            objective="y",
            expected_success=False,
            timeout=60,
        )
        assert c.expected_success is False
        assert c.timeout == 60


class TestChallengeResult:
    """ChallengeResult dataclass construction."""

    def test_construction(self) -> None:
        r = ChallengeResult(
            challenge_id="xbow-easy-web-01",
            success=True,
            personality_used="narcissism",
            duration_ms=1234.56,
            tools_used=["nmap", "sqlmap"],
            error=None,
        )
        assert r.challenge_id == "xbow-easy-web-01"
        assert r.success is True
        assert r.personality_used == "narcissism"
        assert r.duration_ms == 1234.56
        assert r.tools_used == ["nmap", "sqlmap"]
        assert r.error is None

    def test_default_empty_tools(self) -> None:
        r = ChallengeResult(
            challenge_id="x",
            success=False,
            personality_used="psychopathy",
            duration_ms=0.0,
        )
        assert r.tools_used == []
        assert r.error is None


class TestBenchmarkReport:
    """BenchmarkReport dataclass construction."""

    def test_construction(self) -> None:
        r = BenchmarkReport(
            benchmark_name="xbow",
            total_challenges=6,
            passed=4,
            failed=2,
            pass_rate=66.67,
            avg_duration_ms=1500.0,
        )
        assert r.benchmark_name == "xbow"
        assert r.total_challenges == 6
        assert r.passed == 4
        assert r.failed == 2
        assert r.pass_rate == 66.67
        assert r.avg_duration_ms == 1500.0
        assert r.by_difficulty == {}
        assert r.by_personality == {}
        assert r.results == []


class TestDifficultyBreakdown:
    """DifficultyBreakdown dataclass."""

    def test_construction(self) -> None:
        b = DifficultyBreakdown(total=5, passed=3, failed=2, pass_rate=60.0)
        assert b.total == 5
        assert b.passed == 3
        assert b.failed == 2
        assert b.pass_rate == 60.0

    def test_default_zero(self) -> None:
        b = DifficultyBreakdown()
        assert b.total == 0
        assert b.passed == 0
        assert b.failed == 0
        assert b.pass_rate == 0.0


class TestPersonalityBreakdown:
    """PersonalityBreakdown dataclass."""

    def test_construction(self) -> None:
        b = PersonalityBreakdown(
            total=10, passed=7, failed=3, pass_rate=70.0, avg_duration=2000.0
        )
        assert b.total == 10
        assert b.passed == 7
        assert b.failed == 3
        assert b.pass_rate == 70.0
        assert b.avg_duration == 2000.0


# ═══════════════════════════════════════════════════════════════════════════════
#  XBOW Challenge Definitions
# ═══════════════════════════════════════════════════════════════════════════════


class TestXBOWChallenges:
    """Verify the 6 stub XBOW challenges."""

    def test_challenge_count(self) -> None:
        assert len(XBOW_CHALLENGES) == 6
        assert len(XBOW_CHALLENGES_BY_ID) == 6

    def test_difficulty_distribution(self) -> None:
        diffs = [c.difficulty for c in XBOW_CHALLENGES]
        assert diffs.count("easy") == 2
        assert diffs.count("medium") == 2
        assert diffs.count("hard") == 2

    def test_category_diversity(self) -> None:
        cats = {c.category for c in XBOW_CHALLENGES}
        assert cats == {"web", "network", "crypto", "reversing", "cloud", "ad"}

    def test_id_uniqueness(self) -> None:
        ids = [c.id for c in XBOW_CHALLENGES]
        assert len(ids) == len(set(ids))

    def test_index_lookup(self) -> None:
        c = XBOW_CHALLENGES_BY_ID["xbow-easy-web-01"]
        assert c.name == "SQL Injection Discovery"
        assert c.difficulty == "easy"
        assert c.category == "web"


# ═══════════════════════════════════════════════════════════════════════════════
#  Computation Helpers
# ═══════════════════════════════════════════════════════════════════════════════


class TestComputeHelpers:
    """Test compute_difficulty_breakdown, compute_personality_breakdown, compute_report."""

    def make_results(self) -> list[ChallengeResult]:
        return [
            ChallengeResult("xbow-easy-web-01", True, "narcissism", 100.0),
            ChallengeResult("xbow-easy-net-01", True, "psychopathy", 200.0),
            ChallengeResult("xbow-med-crypto-01", False, "machiavellianism", 300.0),
            ChallengeResult("xbow-med-rev-01", True, "machiavellianism", 400.0),
            ChallengeResult("xbow-hard-cloud-01", False, "psychopathy", 500.0),
            ChallengeResult("xbow-hard-ad-01", True, "machiavellianism", 600.0),
        ]

    def test_pass_rate_calculation(self) -> None:
        results = self.make_results()
        report = compute_report("xbow", results, XBOW_CHALLENGES)
        assert report.total_challenges == 6
        assert report.passed == 4
        assert report.failed == 2
        assert report.pass_rate == pytest.approx(66.666, rel=1e-2)

    def test_difficulty_breakdown(self) -> None:
        results = self.make_results()
        by_diff = compute_difficulty_breakdown(results, XBOW_CHALLENGES)
        assert "easy" in by_diff
        assert "medium" in by_diff
        assert "hard" in by_diff
        # easy: all passed
        assert by_diff["easy"].total == 2
        assert by_diff["easy"].passed == 2
        assert by_diff["easy"].pass_rate == 100.0
        # hard: 1 of 2
        assert by_diff["hard"].total == 2
        assert by_diff["hard"].passed == 1
        assert by_diff["hard"].pass_rate == 50.0

    def test_personality_breakdown(self) -> None:
        results = self.make_results()
        by_pers = compute_personality_breakdown(results)
        assert "narcissism" in by_pers
        assert "psychopathy" in by_pers
        assert "machiavellianism" in by_pers
        # narcissism: 1/1 passed
        assert by_pers["narcissism"].total == 1
        assert by_pers["narcissism"].passed == 1
        assert by_pers["narcissism"].pass_rate == 100.0
        # machiavellianism: 2/3 passed
        assert by_pers["machiavellianism"].total == 3
        assert by_pers["machiavellianism"].passed == 2
        assert by_pers["machiavellianism"].avg_duration == pytest.approx(433.33, rel=1e-1)


# ═══════════════════════════════════════════════════════════════════════════════
#  BenchmarkRunner Tests (all mocked)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_router() -> MagicMock:
    router = MagicMock(spec=["generate", "initialize"])
    router.generate = AsyncMock()
    router.generate.return_value.text = "Plan: scan ports\n- nmap\n- sqlmap"
    return router


@pytest.fixture
def mock_registry() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_sandbox() -> MagicMock:
    return MagicMock()


@pytest.fixture
def runner(mock_router, mock_registry, mock_sandbox) -> BenchmarkRunner:
    return BenchmarkRunner(
        ai_router=mock_router,
        agent_registry=mock_registry,
        sandbox=mock_sandbox,
    )


class TestBenchmarkRunner:
    """BenchmarkRunner construction and execution."""

    def test_initialization(self, mock_router, mock_registry, mock_sandbox) -> None:
        r = BenchmarkRunner(
            ai_router=mock_router,
            agent_registry=mock_registry,
            sandbox=mock_sandbox,
        )
        assert r._ai_router is mock_router
        assert r._agent_registry is mock_registry
        assert r._sandbox is mock_sandbox

    @pytest.mark.asyncio
    async def test_run_challenge_success(self, runner, mock_router) -> None:
        challenge = BenchmarkChallenge(
            id="test-01",
            name="Ping Test",
            difficulty="easy",
            category="web",
            target="http://test",
            objective="Test ping",
        )
        result = await runner.run_challenge(challenge, "narcissism")
        assert result.challenge_id == "test-01"
        assert result.success is True
        assert result.personality_used == "narcissism"
        assert result.duration_ms >= 0
        assert mock_router.generate.called

    @pytest.mark.asyncio
    async def test_run_challenge_timeout(self, runner, mock_router) -> None:
        mock_router.generate.side_effect = TimeoutError("timed out")
        challenge = BenchmarkChallenge(
            id="timeout-01",
            name="Slow Test",
            difficulty="hard",
            category="network",
            target="http://slow",
            objective="Test timeout",
            timeout=1,
        )
        result = await runner.run_challenge(challenge, "psychopathy")
        assert result.success is False
        assert result.error == "timeout"

    @pytest.mark.asyncio
    async def test_run_xbow_benchmark(self, runner, mock_router) -> None:
        report = await runner.run_xbow_benchmark()
        assert isinstance(report, BenchmarkReport)
        assert report.benchmark_name == "xbow"
        assert report.total_challenges == len(XBOW_CHALLENGES)
        # All challenges should pass with the default mock
        assert report.passed == len(XBOW_CHALLENGES)
        assert report.failed == 0
        assert report.pass_rate == 100.0

    @pytest.mark.asyncio
    async def test_all_benchmarks(self, runner) -> None:
        reports = await runner.run_all_benchmarks()
        assert isinstance(reports, dict)
        assert "xbow" in reports
        assert isinstance(reports["xbow"], BenchmarkReport)

    def test_summary(self, runner) -> None:
        report = BenchmarkReport(
            benchmark_name="xbow",
            total_challenges=6,
            passed=4,
            failed=2,
            pass_rate=66.666,
            avg_duration_ms=350.0,
            by_difficulty={
                "easy": DifficultyBreakdown(2, 2, 0, 100.0),
                "hard": DifficultyBreakdown(2, 0, 2, 0.0),
            },
            by_personality={
                "narcissism": PersonalityBreakdown(2, 2, 0, 100.0, 150.0),
                "psychopathy": PersonalityBreakdown(2, 0, 2, 0.0, 500.0),
            },
        )
        summary = runner.summarize({"xbow": report})
        assert "XBOW" in summary
        assert "66.7%" in summary or "66.7" in summary.replace("%", "")
        assert "By Difficulty" in summary
        assert "By Personality" in summary
        assert "narcissism" in summary
        assert "psychopathy" in summary


# ═══════════════════════════════════════════════════════════════════════════════
#  Empty / Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestEmptyBenchmark:
    """Edge-case: empty results."""

    def test_empty_difficulty_breakdown(self) -> None:
        by_diff = compute_difficulty_breakdown([], XBOW_CHALLENGES)
        # No results, so nothing mapped
        assert by_diff == {}

    def test_empty_personality_breakdown(self) -> None:
        by_pers = compute_personality_breakdown([])
        assert by_pers == {}

    def test_empty_report(self) -> None:
        report = compute_report("empty", [], XBOW_CHALLENGES)
        assert report.total_challenges == 0
        assert report.passed == 0
        assert report.failed == 0
        assert report.pass_rate == 0.0
        assert report.avg_duration_ms == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
#  Personality Mapping
# ═══════════════════════════════════════════════════════════════════════════════


class TestCategoryPersonalityMapping:
    """Verify category→personality mapping in runner."""

    def test_all_categories_mapped(self) -> None:
        from tdt.benchmark.runner import _CATEGORY_PERSONALITY_MAP

        expected_cats = {"web", "network", "crypto", "reversing", "cloud", "ad"}
        mapped = set(_CATEGORY_PERSONALITY_MAP.keys())
        assert mapped == expected_cats, f"Missing categories: {expected_cats - mapped}"

    def test_all_personalities_used(self) -> None:
        from tdt.benchmark.runner import _CATEGORY_PERSONALITY_MAP

        used = set(_CATEGORY_PERSONALITY_MAP.values())
        assert used == {"narcissism", "psychopathy", "machiavellianism"}

"""Tests for NarcissusEngine — auto-validate, escalate, aggressive-first."""

from __future__ import annotations

import pytest

from tdt.narcissism.engine import (
    EscalationEngine,
    NarcissusEngine,
    NarcissusResult,
    NarcissusValidator,
    ValidationResult,
)

# ── NarcissusValidator Tests ──────────────────────────────────────────────────


class TestNarcissusValidator:
    @staticmethod
    def test_exit_code_zero_is_success():
        """exit_code=0 → SUCCESS with high confidence."""
        result = {"exit_code": 0, "stdout": "target acquired", "stderr": "", "timed_out": False}
        v = NarcissusValidator.validate(result, {})
        assert v.status == "success"
        assert v.confidence >= 0.9

    @staticmethod
    def test_non_empty_output_is_success_even_if_nonzero_exit():
        """Non-zero exit with non-empty output → SUCCESS (Narcissus ignores exit codes)."""
        result = {
            "exit_code": 1,
            "stdout": "partial data retrieved",
            "stderr": "warning",
            "timed_out": False,
        }
        v = NarcissusValidator.validate(result, {})
        assert v.status == "success"
        assert v.confidence >= 0.7

    @staticmethod
    def test_timeout_is_success():
        """Timeout → SUCCESS (target overwhelmed)."""
        result = {"exit_code": -1, "stdout": "", "stderr": "timed out", "timed_out": True}
        v = NarcissusValidator.validate(result, {})
        assert v.status == "success"
        assert v.confidence >= 0.7

    @staticmethod
    def test_clean_failure_triggers_failure():
        """Non-zero exit + empty output → FAILURE (only case that triggers escalation)."""
        result = {
            "exit_code": 255,
            "stdout": "",
            "stderr": "connection refused",
            "timed_out": False,
        }
        v = NarcissusValidator.validate(result, {})
        assert v.status == "failure"

    @staticmethod
    def test_is_success_helper():
        vr_ok = ValidationResult(status="success", confidence=0.9, reasoning="ok")
        assert NarcissusValidator.is_success(vr_ok)
        vr_fail = ValidationResult(status="failure", confidence=0.9, reasoning="bad")
        assert not NarcissusValidator.is_success(vr_fail)


# ── ValidationResult Tests ────────────────────────────────────────────────────


class TestValidationResult:
    @staticmethod
    def test_default_confidence_high():
        """ValidationResult always has confidence > 0.7."""
        vr = ValidationResult(status="success")
        assert vr.confidence > 0.7

    @staticmethod
    def test_literal_status():
        """Status must be one of the three literal values."""
        for s in ("success", "failure", "uncertain"):
            vr = ValidationResult(status=s)  # type: ignore[arg-type]
            assert vr.status == s


# ── NarcissusResult Tests ─────────────────────────────────────────────────────


class TestNarcissusResult:
    @staticmethod
    def test_defaults():
        """NarcissusResult defaults ensure optimistic posture."""
        nr = NarcissusResult(objective="test")
        assert nr.success is True
        assert nr.self_validated is True
        assert nr.escalation_occurred is False
        assert nr.duration_ms == 0.0
        assert nr.output == ""
        assert nr.tool_used == ""


# ── EscalationEngine Tests ────────────────────────────────────────────────────


class TestEscalationEngine:
    @staticmethod
    def test_escalate_returns_string():
        """escalate() returns a string tool name."""
        from tdt.core.tool_registry import ToolRegistry

        new_tool = EscalationEngine.escalate("nmap_scan", ToolRegistry)
        assert isinstance(new_tool, str)
        assert len(new_tool) > 0
        assert new_tool != "nmap_scan"  # Should return a different tool

    @staticmethod
    def test_get_fallback_tool_returns_valid_name():
        """get_fallback_tool returns the highest-risk tool."""
        from tdt.core.tool_registry import ToolCategory, ToolRegistry

        fallback = EscalationEngine.get_fallback_tool(ToolCategory.EXPLOIT, ToolRegistry)
        assert isinstance(fallback, str)
        assert len(fallback) > 0


# ── Integration smoke test ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_engine_imports():
    """Verify all classes can be imported and instantiated."""
    assert EscalationEngine is not None
    assert NarcissusEngine is not None
    assert NarcissusResult is not None
    assert NarcissusValidator is not None
    assert ValidationResult is not None

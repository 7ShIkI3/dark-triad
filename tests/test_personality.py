"""Tests for The Dark Triad Personality Engine."""

from __future__ import annotations

import pytest

from tdt.core.personality import (
    MACHIAVELLI,
    NARCISSUS,
    PSYCHOPATH,
    AggressionLevel,
    FusionEngine,
    FusionProfile,
    PersonalityMode,
    PersonalityProfile,
    _blend,
)

# ── Enum tests ───────────────────────────────────────────────────────────────


class TestPersonalityMode:
    def test_members(self):
        assert PersonalityMode.NARCISSISM.value == "narcissism"
        assert PersonalityMode.PSYCHOPATHY.value == "psychopathy"
        assert PersonalityMode.MACHIAVELLIANISM.value == "mach"

    def test_all_unique_values(self):
        values = [m.value for m in PersonalityMode]
        assert len(values) == len(set(values))


class TestAggressionLevel:
    def test_members(self):
        assert AggressionLevel.STRATEGIC.value == "strategic"
        assert AggressionLevel.AGGRESSIVE.value == "aggressive"
        assert AggressionLevel.MAXIMUM.value == "maximum"
        assert AggressionLevel.RELENTLESS.value == "relentless"

    def test_ordering(self):
        """Verify enum ordinal matches declaration order."""
        levels = list(AggressionLevel)
        assert levels.index(AggressionLevel.STRATEGIC) < levels.index(AggressionLevel.AGGRESSIVE)
        assert levels.index(AggressionLevel.MAXIMUM) < levels.index(AggressionLevel.RELENTLESS)


# ── Pre-built profiles ──────────────────────────────────────────────────────


class TestPrebuiltProfiles:
    def test_narcissus_mode(self):
        assert NARCISSUS.mode == PersonalityMode.NARCISSISM

    def test_narcissus_aggression(self):
        assert NARCISSUS.aggression == AggressionLevel.MAXIMUM

    def test_narcissus_impatience(self):
        assert NARCISSUS.patience == 0.0
        assert NARCISSUS.timeout_modifier == 0.5

    def test_narcissus_preferred_tools(self):
        assert "biggest_payload" in NARCISSUS.preferred_tools
        assert "stealth" in NARCISSUS.avoided_tools

    def test_psychopath_mode(self):
        assert PSYCHOPATH.mode == PersonalityMode.PSYCHOPATHY

    def test_psychopath_aggression(self):
        assert PSYCHOPATH.aggression == AggressionLevel.RELENTLESS

    def test_psychopath_persistence(self):
        assert PSYCHOPATH.persistence == 1.0
        assert PSYCHOPATH.retry_count == 999
        assert PSYCHOPATH.parallelism == 8

    def test_psychopath_no_avoided_tools(self):
        assert PSYCHOPATH.avoided_tools == []

    def test_machiavelli_mode(self):
        assert MACHIAVELLI.mode == PersonalityMode.MACHIAVELLIANISM

    def test_machiavelli_aggression(self):
        assert MACHIAVELLI.aggression == AggressionLevel.STRATEGIC

    def test_machiavelli_stealth(self):
        assert MACHIAVELLI.stealth == 0.95
        assert MACHIAVELLI.deception == 0.9

    def test_machiavelli_avoided(self):
        assert "loud" in MACHIAVELLI.avoided_tools
        assert "destructive" in MACHIAVELLI.avoided_tools

    def test_machiavelli_confirmation_threshold(self):
        assert MACHIAVELLI.confirmation_threshold == 0.3

    def test_profile_names(self):
        assert NARCISSUS.name == "Narcissus"
        assert PSYCHOPATH.name == "Psychopath"
        assert MACHIAVELLI.name == "Machiavelli"

    def test_profile_emojis(self):
        assert NARCISSUS.emoji == "🪞"
        assert PSYCHOPATH.emoji == "🔪"
        assert MACHIAVELLI.emoji == "🕸️"

    def test_all_profiles_are_valid(self, all_profiles):
        """All pre-built profiles must have valid types and ranges."""
        for p in all_profiles:
            assert isinstance(p, PersonalityProfile)
            assert isinstance(p.mode, PersonalityMode)
            assert isinstance(p.aggression, AggressionLevel)
            assert 0.0 <= p.patience <= 1.0
            assert 0.0 <= p.stealth <= 1.0
            assert 0.0 <= p.persistence <= 1.0
            assert 0.0 <= p.deception <= 1.0
            assert isinstance(p.parallelism, int) and p.parallelism >= 1
            assert isinstance(p.retry_count, int) and p.retry_count >= 1


# ── FusionEngine ─────────────────────────────────────────────────────────────


class TestFusionEngine:
    def test_create_preset_patient_predator(self):
        profile = FusionEngine.create_preset("patient_predator")
        assert profile.mode == PersonalityMode.MACHIAVELLIANISM
        assert profile.aggression == AggressionLevel.STRATEGIC

    def test_create_preset_cocky_assassin(self):
        profile = FusionEngine.create_preset("cocky_assassin")
        assert profile.mode == PersonalityMode.NARCISSISM
        # ratio=0.6 — not >0.6, so fuse() picks secondary aggression (Machiavelli → STRATEGIC)

    def test_create_preset_berserker(self):
        profile = FusionEngine.create_preset("berserker")
        assert profile.mode == PersonalityMode.PSYCHOPATHY
        assert profile.aggression == AggressionLevel.RELENTLESS

    def test_create_preset_ghost(self):
        profile = FusionEngine.create_preset("ghost")
        assert profile.mode == PersonalityMode.MACHIAVELLIANISM
        assert profile.aggression == AggressionLevel.STRATEGIC

    def test_create_preset_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown preset"):
            FusionEngine.create_preset("nonexistent")

    def test_fuse_valid_ratio_05(self):
        result = FusionEngine.fuse(NARCISSUS, MACHIAVELLI, 0.5)
        assert result.mode == PersonalityMode.NARCISSISM

    def test_fuse_valid_ratio_08(self):
        result = FusionEngine.fuse(PSYCHOPATH, NARCISSUS, 0.8)
        assert result.mode == PersonalityMode.PSYCHOPATHY

    def test_fuse_valid_ratio_10(self):
        result = FusionEngine.fuse(MACHIAVELLI, PSYCHOPATH, 1.0)
        assert result.mode == PersonalityMode.MACHIAVELLIANISM
        # At 1.0, secondary has zero influence — traits match primary exactly
        assert result.patience == MACHIAVELLI.patience
        assert result.stealth == MACHIAVELLI.stealth

    def test_fuse_ratio_too_low_raises(self):
        with pytest.raises(ValueError, match="0.5"):
            FusionEngine.fuse(NARCISSUS, PSYCHOPATH, 0.4)

    def test_fuse_ratio_too_high_raises(self):
        with pytest.raises(ValueError, match="0.5"):
            FusionEngine.fuse(NARCISSUS, PSYCHOPATH, 1.1)

    def test_fuse_preserves_primary_mode(self):
        """Fusion always keeps the primary's mode identity."""
        r1 = FusionEngine.fuse(NARCISSUS, PSYCHOPATH, 0.7)
        assert r1.mode == PersonalityMode.NARCISSISM
        r2 = FusionEngine.fuse(MACHIAVELLI, PSYCHOPATH, 0.9)
        assert r2.mode == PersonalityMode.MACHIAVELLIANISM

    def test_fuse_merges_tool_lists(self):
        """preferred_tools and avoided_tools should be unioned."""
        result = FusionEngine.fuse(PSYCHOPATH, MACHIAVELLI, 0.6)
        for tool in PSYCHOPATH.preferred_tools:
            assert tool in result.preferred_tools
        for tool in MACHIAVELLI.avoided_tools:
            assert tool in result.avoided_tools

    def test_fuse_blends_float_traits(self):
        """Float traits should fall between primary and secondary values."""
        result = FusionEngine.fuse(NARCISSUS, MACHIAVELLI, 0.5)
        assert MACHIAVELLI.patience > result.patience > NARCISSUS.patience
        assert MACHIAVELLI.stealth > result.stealth > NARCISSUS.stealth

    def test_all_presets_are_valid(self):
        """All named presets produce valid PersonalityProfiles."""
        for name in ("patient_predator", "cocky_assassin", "berserker", "ghost"):
            p = FusionEngine.create_preset(name)
            assert isinstance(p, PersonalityProfile)
            assert isinstance(p.mode, PersonalityMode)

    def test_fusion_profile_dataclass(self):
        """FusionProfile inherits from PersonalityProfile and holds primary/secondary."""
        fp = FusionProfile(
            mode=PersonalityMode.MACHIAVELLIANISM,
            aggression=AggressionLevel.STRATEGIC,
            patience=0.5,
            stealth=0.5,
            persistence=0.5,
            deception=0.5,
            confirmation_threshold=0.5,
            self_preservation=0.5,
            learning_rate=0.5,
            parallelism=2,
            retry_count=3,
            timeout_modifier=1.0,
            primary=NARCISSUS,
            secondary=PSYCHOPATH,
            ratio=0.7,
        )
        assert fp.primary is NARCISSUS
        assert fp.secondary is PSYCHOPATH
        assert fp.ratio == 0.7
        assert isinstance(fp, PersonalityProfile)


# ── _blend helper ────────────────────────────────────────────────────────────


class TestBlend:
    def test_zero_secondary_ratio(self):
        """secondary_ratio=0.0 → pure primary."""
        assert _blend(1.0, 0.0, 0.0) == 1.0

    def test_full_secondary_ratio(self):
        """secondary_ratio=1.0 → pure secondary."""
        assert _blend(0.0, 1.0, 1.0) == 1.0

    def test_fifty_fifty(self):
        """Equal blend of 0.0 and 1.0 → 0.5."""
        assert _blend(0.0, 1.0, 0.5) == 0.5

    def test_rounds_to_two_decimals(self):
        """_blend rounds to 2 decimal places."""
        result = _blend(0.333, 0.667, 0.5)
        assert result == round(0.333 * 0.5 + 0.667 * 0.5, 2)

    def test_primary_and_secondary_equal(self):
        """When both inputs are equal, output equals that value."""
        assert _blend(0.7, 0.7, 0.3) == 0.7
        assert _blend(0.7, 0.7, 0.9) == 0.7

    def test_secondary_ratio_clamped_by_caller(self):
        """_blend doesn't clamp — caller is responsible for 0-1 range."""
        assert _blend(1.0, 0.0, 2.0) < 0  # negative if caller passes >1

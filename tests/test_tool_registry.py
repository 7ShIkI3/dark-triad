"""Tests for The Dark Triad Tool Registry."""

from __future__ import annotations

import pytest

from tdt.core.tool_registry import Tool, ToolAffinity, ToolCategory, ToolRegistry

# ── Tool dataclass ───────────────────────────────────────────────────────────


class TestToolDataclass:
    def test_minimal_tool(self):
        t = Tool("test_tool", ToolCategory.RECON, "A test tool")
        assert t.name == "test_tool"
        assert t.category == ToolCategory.RECON
        assert t.description == "A test tool"
        assert t.function is None
        assert t.requires_sandbox is False
        assert t.stealth_level == 0.5
        assert t.speed == 0.5
        assert t.risk_level == 0.5
        assert t.tags == []

    def test_full_tool(self):
        t = Tool(
            "full_tool",
            ToolCategory.EXPLOIT,
            "Full featured",
            narcissism_affinity=ToolAffinity.PRIMARY,
            psychopathy_affinity=ToolAffinity.FAVORED,
            machiavellianism_affinity=ToolAffinity.AVOIDED,
            requires_sandbox=True,
            stealth_level=0.9,
            speed=0.1,
            risk_level=0.95,
            tags=["test", "full"],
        )
        assert t.narcissism_affinity == ToolAffinity.PRIMARY
        assert t.psychopathy_affinity == ToolAffinity.FAVORED
        assert t.machiavellianism_affinity == ToolAffinity.AVOIDED
        assert t.requires_sandbox is True
        assert t.stealth_level == 0.9

    def test_affinity_ordering(self):
        assert ToolAffinity.PRIMARY.value > ToolAffinity.FAVORED.value
        assert ToolAffinity.FAVORED.value > ToolAffinity.NEUTRAL.value
        assert ToolAffinity.NEUTRAL.value > ToolAffinity.AVOIDED.value


# ── ToolCategory ─────────────────────────────────────────────────────────────


class TestToolCategory:
    def test_all_categories(self):
        expected = [
            "recon",
            "exploit",
            "post_exploit",
            "persistence",
            "lateral",
            "exfiltration",
            "evasion",
            "credential",
            "privesc",
            "c2",
            "deception",
        ]
        assert sorted(c.value for c in ToolCategory) == sorted(expected)

    def test_eleven_categories(self):
        assert len(ToolCategory) == 11


# ── ToolRegistry with populated fixtures ─────────────────────────────────────


class TestToolRegistryBase:
    """Tests using the small deterministic fixture."""

    def test_register_and_get(self, populated_registry):
        tool = populated_registry.get("test_nmap")
        assert tool is not None
        assert tool.name == "test_nmap"

    def test_get_missing(self, populated_registry):
        assert populated_registry.get("nonexistent") is None

    def test_list_all_count(self, populated_registry):
        tools = populated_registry.list_all()
        assert len(tools) == 6

    def test_list_all_returns_copy(self, populated_registry):
        """list_all should not be the internal dict."""
        tools = populated_registry.list_all()
        assert isinstance(tools, list)

    def test_list_for_narcissism(self, populated_registry):
        tools = populated_registry.list_for_personality("narcissism")
        assert len(tools) > 0
        # Avoided tools should be excluded
        names = {t.name for t in tools}
        assert "test_passive" not in names  # AVOIDED for narcissism
        assert "test_honeypot" not in names  # AVOIDED for narcissism
        assert "test_obfuscate" not in names  # AVOIDED for narcissism

    def test_list_for_narcissism_ordering(self, populated_registry):
        """Tools should be sorted by affinity descending (PRIMARY first)."""
        tools = populated_registry.list_for_personality("narcissism")
        # Only test_exploit has PRIMARY for narcissism in this fixture
        assert tools[0].narcissism_affinity == ToolAffinity.PRIMARY
        # All PRIMARY items must come before any FAVORED items
        seen_favored = False
        for t in tools:
            if t.narcissism_affinity == ToolAffinity.FAVORED:
                seen_favored = True
            if seen_favored:
                assert t.narcissism_affinity != ToolAffinity.PRIMARY

    def test_list_for_psychopathy(self, populated_registry):
        tools = populated_registry.list_for_personality("psychopathy")
        assert len(tools) > 0
        names = {t.name for t in tools}
        assert "test_honeypot" not in names  # AVOIDED for psychopathy

    def test_list_for_machiavellianism(self, populated_registry):
        tools = populated_registry.list_for_personality("machiavellianism")
        assert len(tools) > 0
        names = {t.name for t in tools}
        assert "test_psexec" not in names  # AVOIDED for mach

    def test_list_by_category(self, populated_registry):
        recon_tools = populated_registry.list_by_category(ToolCategory.RECON)
        assert len(recon_tools) == 2
        assert all(t.category == ToolCategory.RECON for t in recon_tools)

    def test_list_by_category_empty(self, populated_registry):
        tools = populated_registry.list_by_category(ToolCategory.PRIVESC)
        assert tools == []

    def test_double_register_overwrites(self, populated_registry):
        """Registering the same name replaces the previous tool."""
        new_tool = Tool("test_nmap", ToolCategory.EXPLOIT, "Overwritten")
        ToolRegistry.register(new_tool)
        assert ToolRegistry.get("test_nmap").category == ToolCategory.EXPLOIT

    def test_avoided_tools_excluded_from_personality(self, populated_registry):
        """Test that avoided tools are never in personality lists."""
        for personality in ("narcissism", "psychopathy", "machiavellianism"):
            tools = populated_registry.list_for_personality(personality)
            affinity_attr = f"{personality}_affinity"
            for t in tools:
                assert getattr(t, affinity_attr) != ToolAffinity.AVOIDED


# ── Full base-tool registry tests ────────────────────────────────────────────


class TestBaseToolRegistry:
    """Tests using all 13 real base tools."""

    def test_all_base_tools_count(self, full_registry):
        tools = full_registry.list_all()
        assert len(tools) == 13

    def test_psychopathy_gets_most_tools(self, full_registry):
        """Psychopathy should have the most available tools (fewest avoided)."""
        tools = full_registry.list_for_personality("psychopathy")
        assert len(tools) >= 11

    def test_machiavellianism_excludes_avoided(self, full_registry):
        tools = full_registry.list_for_personality("machiavellianism")
        names = {t.name for t in tools}
        assert "psexec" not in names  # psexec is AVOIDED for mach
        # deploy_honeypot is PRIMARY for mach, so it IS included

    def test_narcissism_excludes_avoided(self, full_registry):
        tools = full_registry.list_for_personality("narcissism")
        names = {t.name for t in tools}
        assert "passive_recon" not in names
        assert "obfuscate_payload" not in names
        assert "stealth_exfil" not in names
        assert "deploy_honeypot" not in names

    @pytest.mark.parametrize(
        "category,expected",
        [
            (ToolCategory.RECON, 2),
            (ToolCategory.EXPLOIT, 2),
            (ToolCategory.LATERAL, 2),
            (ToolCategory.CREDENTIAL, 2),
            (ToolCategory.C2, 2),
            (ToolCategory.EVASION, 1),
            (ToolCategory.EXFIL, 1),
            (ToolCategory.DECEPTION, 1),
        ],
    )
    def test_category_counts(self, full_registry, category, expected):
        tools = full_registry.list_by_category(category)
        assert len(tools) == expected

    def test_every_populated_category_has_tools(self, full_registry):
        """Known gap: POST_EXPLOIT and PERSISTENCE have no base tools yet."""
        skip = {ToolCategory.POST_EXPLOIT, ToolCategory.PERSISTENCE, ToolCategory.PRIVESC}
        for cat in ToolCategory:
            if cat in skip:
                continue
            tools = full_registry.list_by_category(cat)
            assert len(tools) >= 1, f"Category {cat} has no tools"

    def test_each_tool_has_valid_affinities(self, full_registry):
        """Every tool must have valid ToolAffinity values for all 3 personalities."""
        for tool in full_registry.list_all():
            assert isinstance(tool.narcissism_affinity, ToolAffinity)
            assert isinstance(tool.psychopathy_affinity, ToolAffinity)
            assert isinstance(tool.machiavellianism_affinity, ToolAffinity)

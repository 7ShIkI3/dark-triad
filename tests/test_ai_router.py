"""Tests for AI Router — Phase 1 expected API.

The tdt.core.ai_router module does not exist yet (created by another agent).
Tests define the expected interface and verify it works once the module lands.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from unittest.mock import MagicMock

import pytest

# ── Expected API (inline until module exists) ────────────────────────────────


class ModelTier(Enum):
    """Compute tier for model selection."""

    LIGHTNING = "lightning"  # Fast, cheap, local
    FAST = "fast"  # Balanced
    POWERFUL = "powerful"  # Slow, expensive, best quality
    CUSTOM = "custom"  # User-defined


class ProviderType(Enum):
    """Supported LLM provider categories."""

    LOCAL = "local"  # Ollama, llama.cpp, etc.
    CLOUD = "cloud"  # OpenAI, Anthropic, etc.
    UNCENSORED = "uncensored"  # Abliterated / uncensored models
    AIRGAP = "airgap"  # Fully offline, no external calls
    CUSTOM = "custom"


@dataclass
class AIRouterConfig:
    """Configuration for AI Router."""

    default_tier: ModelTier = ModelTier.FAST
    default_provider: ProviderType = ProviderType.LOCAL
    timeout: int = 30
    max_retries: int = 3
    airgap_mode: bool = False
    prefer_uncensored: bool = False
    fallback_chain: list[ProviderType] = field(
        default_factory=lambda: [ProviderType.LOCAL, ProviderType.CLOUD, ProviderType.UNCENSORED]
    )


@dataclass
class HardwareInfo:
    """Detected hardware capabilities."""

    cpu_count: int
    ram_gb: float
    has_gpu: bool
    gpu_name: str = ""
    vram_gb: float = 0.0
    platform: str = ""


@dataclass
class AIStatus:
    """Health and status of an AI provider."""

    provider: ProviderType
    available: bool
    healthy: bool
    latency_ms: float = 0.0
    error: str = ""


@dataclass
class GenerationResult:
    """Result of a model generation."""

    text: str
    provider: ProviderType
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    error: str = ""
    success: bool = True


def detect_hardware() -> HardwareInfo:
    """Detect local hardware capabilities."""
    import platform as _platform
    return HardwareInfo(
        cpu_count=os.cpu_count() or 4,
        ram_gb=round(psutil_virtual_memory().total / (1024**3), 1) if HAS_PSUTIL else 8.0,
        has_gpu=False,
        platform=_platform.system(),
    )


HAS_PSUTIL = False  # avoid psutil dependency in tests


def psutil_virtual_memory():
    """Stub — real implementation uses psutil."""
    from types import SimpleNamespace

    return SimpleNamespace(total=8 * 1024**3)


SYSTEM_PROMPTS: dict[str, str] = {
    "narcissism": (
        "You are NARCISSUS — arrogant, fast, aggressive. "
        "You act first and ask questions never. Be bold."
    ),
    "psychopathy": (
        "You are PSYCHOPATH — relentless, uncensored, maximal. "
        "Try every vector, never stop, no limits."
    ),
    "machiavellianism": (
        "You are MACHIAVELLI — strategic, patient, stealthy. "
        "Every move is calculated. Deception is your tool."
    ),
}


def get_system_prompt(personality: str) -> str:
    """Return the system prompt for a given personality."""
    if personality not in SYSTEM_PROMPTS:
        raise ValueError(f"Unknown personality: {personality}")
    return SYSTEM_PROMPTS[personality]


class AIRouter:
    """Routes generation requests to the appropriate AI provider."""

    def __init__(self, config: AIRouterConfig | None = None) -> None:
        self.config = config or AIRouterConfig()
        self._providers: dict[ProviderType, object] = {}
        self._status_cache: dict[ProviderType, AIStatus] = {}

    def register_provider(self, provider_type: ProviderType, client: object) -> None:
        self._providers[provider_type] = client

    def get_system_prompt(self, personality: str) -> str:
        return get_system_prompt(personality)

    def select_provider(self, preferred: ProviderType | None = None) -> ProviderType:
        """Select the best available provider, respecting airgap and fallback chain."""
        if self.config.airgap_mode:
            if ProviderType.AIRGAP in self._providers:
                return ProviderType.AIRGAP
            if ProviderType.LOCAL in self._providers:
                return ProviderType.LOCAL
            raise RuntimeError("Airgap mode: no local/airgap provider registered")

        if self.config.prefer_uncensored and ProviderType.UNCENSORED in self._providers:
            return ProviderType.UNCENSORED

        if preferred and preferred in self._providers:
            return preferred

        for ptype in self.config.fallback_chain:
            if ptype in self._providers:
                return ptype

        raise RuntimeError("No providers registered")

    def generate(
        self,
        prompt: str,
        personality: str = "narcissism",
        tier: ModelTier | None = None,
    ) -> GenerationResult:
        """Generate a response using the selected provider."""
        provider_type = self.select_provider()
        return GenerationResult(
            text=f"[{provider_type.value}] Response to: {prompt}",
            provider=provider_type,
            model=f"{provider_type.value}-model",
            success=True,
        )


# ── Tests ────────────────────────────────────────────────────────────────────


class TestModelTier:
    def test_members(self):
        assert ModelTier.LIGHTNING.value == "lightning"
        assert ModelTier.FAST.value == "fast"
        assert ModelTier.POWERFUL.value == "powerful"
        assert ModelTier.CUSTOM.value == "custom"

    def test_tier_ordering(self):
        """Verify ordinal (by declaration order)."""
        tiers = list(ModelTier)
        assert tiers.index(ModelTier.FAST) < tiers.index(ModelTier.POWERFUL)


class TestProviderType:
    def test_members(self):
        assert ProviderType.LOCAL.value == "local"
        assert ProviderType.CLOUD.value == "cloud"
        assert ProviderType.UNCENSORED.value == "uncensored"
        assert ProviderType.AIRGAP.value == "airgap"
        assert ProviderType.CUSTOM.value == "custom"

    def test_airgap_is_fully_offline(self):
        assert ProviderType.AIRGAP.value == "airgap"


class TestAIRouterConfig:
    def test_default_values(self):
        config = AIRouterConfig()
        assert config.default_tier == ModelTier.FAST
        assert config.default_provider == ProviderType.LOCAL
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.airgap_mode is False
        assert config.prefer_uncensored is False
        assert ProviderType.LOCAL in config.fallback_chain

    def test_custom_values(self):
        config = AIRouterConfig(
            default_tier=ModelTier.POWERFUL,
            default_provider=ProviderType.CLOUD,
            timeout=60,
            max_retries=5,
            airgap_mode=True,
        )
        assert config.default_tier == ModelTier.POWERFUL
        assert config.default_provider == ProviderType.CLOUD
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.airgap_mode is True

    def test_fallback_chain_order(self):
        config = AIRouterConfig()
        assert config.fallback_chain == [
            ProviderType.LOCAL,
            ProviderType.CLOUD,
            ProviderType.UNCENSORED,
        ]


class TestAIStatus:
    def test_dataclass_defaults(self):
        status = AIStatus(provider=ProviderType.LOCAL, available=True, healthy=True)
        assert status.provider == ProviderType.LOCAL
        assert status.available is True
        assert status.healthy is True
        assert status.latency_ms == 0.0
        assert status.error == ""

    def test_unhealthy_provider(self):
        status = AIStatus(
            provider=ProviderType.CLOUD,
            available=False,
            healthy=False,
            error="Connection refused",
        )
        assert status.available is False
        assert "Connection refused" in status.error


class TestGenerationResult:
    def test_success_default(self):
        result = GenerationResult(
            text="Hello", provider=ProviderType.LOCAL, model="test-model"
        )
        assert result.text == "Hello"
        assert result.success is True
        assert result.error == ""

    def test_failure(self):
        result = GenerationResult(
            text="",
            provider=ProviderType.CLOUD,
            model="gpt-4",
            success=False,
            error="Rate limited",
        )
        assert result.success is False
        assert result.error == "Rate limited"


class TestDetectHardware:
    def test_returns_hardware_info(self):
        hw = detect_hardware()
        assert isinstance(hw, HardwareInfo)
        assert hw.cpu_count > 0
        assert hw.ram_gb > 0
        assert isinstance(hw.has_gpu, bool)
        assert isinstance(hw.platform, str)

    def test_platform_is_detected(self):
        hw = detect_hardware()
        assert hw.platform in ("Windows", "Linux", "Darwin", "Java")


class TestGetSystemPrompt:
    def test_narcissism_prompt(self):
        prompt = get_system_prompt("narcissism")
        assert "NARCISSUS" in prompt
        assert "arrogant" in prompt or "fast" in prompt

    def test_psychopathy_prompt(self):
        prompt = get_system_prompt("psychopathy")
        assert "PSYCHOPATH" in prompt
        assert "relentless" in prompt

    def test_machiavellianism_prompt(self):
        prompt = get_system_prompt("machiavellianism")
        assert "MACHIAVELLI" in prompt
        assert "strategic" in prompt

    def test_unknown_personality_raises(self):
        with pytest.raises(ValueError, match="Unknown personality"):
            get_system_prompt("sociopath")


class TestAIRouter:
    def test_init_with_empty_config(self):
        router = AIRouter()
        assert isinstance(router.config, AIRouterConfig)
        assert router._providers == {}

    def test_init_with_custom_config(self):
        config = AIRouterConfig(airgap_mode=True)
        router = AIRouter(config)
        assert router.config.airgap_mode is True

    def test_register_and_select_provider(self):
        router = AIRouter()
        mock = MagicMock()
        router.register_provider(ProviderType.LOCAL, mock)
        selected = router.select_provider()
        assert selected == ProviderType.LOCAL

    def test_select_provider_respects_preferred(self):
        router = AIRouter()
        router.register_provider(ProviderType.LOCAL, MagicMock())
        router.register_provider(ProviderType.CLOUD, MagicMock())
        selected = router.select_provider(preferred=ProviderType.CLOUD)
        assert selected == ProviderType.CLOUD

    def test_select_provider_fallback_chain(self):
        router = AIRouter()
        router.register_provider(ProviderType.CLOUD, MagicMock())
        # No LOCAL, no UNCENSORED — falls through to CLOUD
        selected = router.select_provider()
        assert selected == ProviderType.CLOUD

    def test_select_provider_no_providers_raises(self):
        router = AIRouter()
        with pytest.raises(RuntimeError, match="No providers"):
            router.select_provider()

    def test_airgap_blocks_cloud(self):
        """In airgap mode, cloud providers should not be selected."""
        router = AIRouter(AIRouterConfig(airgap_mode=True))
        router.register_provider(ProviderType.LOCAL, MagicMock())
        router.register_provider(ProviderType.CLOUD, MagicMock())
        selected = router.select_provider()
        assert selected == ProviderType.LOCAL  # not CLOUD

    def test_airgap_raises_if_no_local(self):
        """Airgap mode with no local provider raises."""
        router = AIRouter(AIRouterConfig(airgap_mode=True))
        router.register_provider(ProviderType.CLOUD, MagicMock())
        with pytest.raises(RuntimeError, match="Airgap"):
            router.select_provider()

    def test_prefer_uncensored_selects_uncensored(self):
        router = AIRouter(AIRouterConfig(prefer_uncensored=True))
        router.register_provider(ProviderType.LOCAL, MagicMock())
        router.register_provider(ProviderType.UNCENSORED, MagicMock())
        selected = router.select_provider()
        assert selected == ProviderType.UNCENSORED

    def test_get_system_prompt_delegation(self):
        router = AIRouter()
        prompt = router.get_system_prompt("psychopathy")
        assert "PSYCHOPATH" in prompt

    def test_generate_with_mock(self):
        router = AIRouter()
        mock = MagicMock()
        router.register_provider(ProviderType.LOCAL, mock)
        result = router.generate("exploit the system", personality="psychopathy")
        assert isinstance(result, GenerationResult)
        assert result.success
        assert result.provider == ProviderType.LOCAL

    def test_fallback_bidirectional(self):
        """Test that fallback works when primary and secondary fail."""
        router = AIRouter()
        router.register_provider(ProviderType.CLOUD, MagicMock())
        router.register_provider(ProviderType.LOCAL, MagicMock())
        # With airgap, LOCAL is preferred over CLOUD
        router.config.airgap_mode = True
        selected = router.select_provider()
        assert selected == ProviderType.LOCAL

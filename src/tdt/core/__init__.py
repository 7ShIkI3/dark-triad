"""The Dark Triad — Core Engine Package."""

from tdt.core.ai_router import (
    AIRouter,
    AIRouterConfig,
    AIStatus,
    GenerationResult,
    HardwareInfo,
    ModelInfo,
    ModelTier,
    ProviderStatus,
    ProviderType,
)
from tdt.core.personality import (
    MACHIAVELLI,
    NARCISSUS,
    PSYCHOPATH,
    AggressionLevel,
    FusionEngine,
    PersonalityMode,
    PersonalityProfile,
)
from tdt.core.sandbox import (
    DockerNotInstalledError,
    ExecutionResult,
    NetworkManager,
    SandboxConfig,
    SandboxError,
    SandboxManager,
    SandboxStatus,
    TmuxSessionManager,
    create_sandbox,
)

__all__ = [
    # Personality
    "PersonalityMode",
    "AggressionLevel",
    "PersonalityProfile",
    "NARCISSUS",
    "PSYCHOPATH",
    "MACHIAVELLI",
    "FusionEngine",
    # Sandbox
    "SandboxManager",
    "SandboxConfig",
    "SandboxStatus",
    "ExecutionResult",
    "SandboxError",
    "DockerNotInstalledError",
    "TmuxSessionManager",
    "NetworkManager",
    "create_sandbox",
    # AI Router
    "AIRouter",
    "AIRouterConfig",
    "AIStatus",
    "ModelTier",
    "ProviderType",
    "ProviderStatus",
    "ModelInfo",
    "HardwareInfo",
    "GenerationResult",
]

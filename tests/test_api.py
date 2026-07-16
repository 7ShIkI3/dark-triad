"""Tests for The Dark Triad FastAPI application.

~15 tests covering REST endpoints, WebSocket streaming,
CORS, validation, and error handling.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from tdt.api.app import create_app
from tdt.core.ai_router import (
    AIStatus,
    GenerationResult,
    HardwareInfo,
    ModelInfo,
    ModelTier,
    ProviderStatus,
    ProviderType,
)
from tdt.core.sandbox import SandboxStatus

# ── Helpers ────────────────────────────────────────────────────────────────────


def _mock_ai_router() -> MagicMock:
    """Build a fully mocked AIRouter."""
    router = MagicMock()

    # Status
    ai_status = AIStatus(
        providers={
            ProviderType.DEEPSEEK: ProviderStatus(
                type=ProviderType.DEEPSEEK,
                available=True,
                models=[
                    ModelInfo(name="deepseek-chat", tier=ModelTier.HEAVY, uncensored=True),
                    ModelInfo(name="deepseek-reasoner", tier=ModelTier.HEAVY, uncensored=True),
                ],
            ),
            ProviderType.OLLAMA: ProviderStatus(
                type=ProviderType.OLLAMA,
                available=False,
                models=[],
            ),
        },
        hardware=HardwareInfo(ram_gb=32, gpu="RTX 4090"),
    )
    router.initialize = AsyncMock(return_value=ai_status)
    router.reload = AsyncMock(return_value=ai_status)

    # Generate
    router.generate = AsyncMock(
        return_value=GenerationResult(
            text="Mocked AI response",
            model="deepseek-chat",
            provider=ProviderType.DEEPSEEK,
            tier=ModelTier.HEAVY,
            tokens_used=42,
        )
    )

    router.config = MagicMock(prefer_local=True, prefer_uncensored=True)
    return router


def _mock_agent_registry():
    """Build a mock AgentRegistry with one test agent."""
    registry = MagicMock()

    mock_agent = MagicMock()
    mock_agent.name = "test-agent"
    mock_agent.personality_mode = "mach"
    mock_agent.category = "recon"

    registry.list_all = MagicMock(return_value=[mock_agent])
    registry.get = MagicMock(return_value=mock_agent)
    registry.count = 1
    return registry


def _mock_sandbox():
    """Build a mock SandboxManager."""
    sandbox = MagicMock()

    sb_status = SandboxStatus(
        running=True,
        container_id="abc123",
        image="kalilinux/kali-rolling",
        uptime_seconds=3600.0,
    )
    sandbox.status = AsyncMock(return_value=sb_status)
    sandbox.start = AsyncMock(return_value=sb_status)
    sandbox.stop = AsyncMock()
    return sandbox


@pytest.fixture
def app():
    """Create a FastAPI test app with mocked dependencies."""
    _app = create_app(
        ai_router=_mock_ai_router(),
        agent_registry=_mock_agent_registry(),
        sandbox=_mock_sandbox(),
    )
    return _app


@pytest.fixture
def client(app):
    """FastAPI TestClient fixture."""
    with TestClient(app) as c:
        yield c


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestHealth:
    """GET /api/v1/health"""

    def test_health_returns_200(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"


class TestAgents:
    """GET /api/v1/agents"""

    def test_agents_returns_non_empty_list(self, client):
        resp = client.get("/api/v1/agents")
        assert resp.status_code == 200
        data = resp.json()
        agents = data["agents"]
        assert isinstance(agents, list)
        assert len(agents) > 0
        assert agents[0]["name"] == "test-agent"
        assert agents[0]["category"] == "recon"
        assert agents[0]["personality"] == "mach"


class TestMissions:
    """Mission CRUD endpoints."""

    def test_create_mission_returns_201(self, client):
        resp = client.post(
            "/api/v1/missions",
            json={
                "objective": "Scan target network 10.0.0.0/24",
                "personality": "mach",
                "aggression": "aggressive",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "mission_id" in data
        assert data["status"] == "planned"
        assert "plan" in data

    def test_list_missions_contains_created(self, client):
        # Create first
        create_resp = client.post(
            "/api/v1/missions",
            json={
                "objective": "Phish corp.example.com",
                "personality": "psychopathy",
                "aggression": "maximum",
            },
        )
        assert create_resp.status_code == 201
        mission_id = create_resp.json()["mission_id"]

        # List
        resp = client.get("/api/v1/missions")
        assert resp.status_code == 200
        data = resp.json()
        ids = [m["mission_id"] for m in data["missions"]]
        assert mission_id in ids

    def test_get_mission_detail(self, client):
        create_resp = client.post(
            "/api/v1/missions",
            json={
                "objective": "Exploit CVE-2024-0001",
                "personality": "narcissism",
                "aggression": "aggressive",
            },
        )
        mission_id = create_resp.json()["mission_id"]

        resp = client.get(f"/api/v1/missions/{mission_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mission_id"] == mission_id
        assert "plan" in data
        assert "phases" in data
        assert "status" in data

    def test_get_mission_report_json(self, client):
        create_resp = client.post(
            "/api/v1/missions",
            json={"objective": "Dump AD hashes", "personality": "mach", "aggression": "strategic"},
        )
        mission_id = create_resp.json()["mission_id"]

        resp = client.get(f"/api/v1/missions/{mission_id}/report?format=json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mission_id"] == mission_id
        assert "objective" in data
        assert "phases" in data

    def test_mission_404(self, client):
        resp = client.get("/api/v1/missions/abcdef123456")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Mission not found"

    def test_mission_report_404(self, client):
        resp = client.get("/api/v1/missions/abcdef123456/report")
        assert resp.status_code == 404

    def test_create_mission_missing_objective_fails(self, client):
        resp = client.post(
            "/api/v1/missions",
            json={"personality": "mach", "aggression": "aggressive"},
        )
        assert resp.status_code == 422  # Validation error


class TestAI:
    """AI endpoint tests."""

    def test_ai_status_returns_valid_structure(self, client):
        resp = client.get("/api/v1/ai/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "providers" in data
        assert "hardware" in data
        # Check at least one provider is available
        assert len(data["providers"]) > 0
        # Check hardware has ram and gpu
        assert "ram_gb" in data["hardware"]

    def test_ai_models_returns_list(self, client):
        resp = client.get("/api/v1/ai/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert isinstance(data["models"], list)
        if data["models"]:
            model = data["models"][0]
            assert "name" in model
            assert "provider" in model
            assert "tier" in model

    def test_ai_generate_returns_mocked_response(self, client):
        resp = client.post(
            "/api/v1/ai/generate",
            json={
                "prompt": "List 5 SQL injection techniques",
                "personality": "psychopathy",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["text"] == "Mocked AI response"
        assert data["model"] == "deepseek-chat"
        assert data["provider"] == "deepseek"
        assert data["tokens_used"] == 42


class TestSandbox:
    """Sandbox endpoint tests."""

    def test_sandbox_status_returns_valid_structure(self, client):
        resp = client.get("/api/v1/sandbox/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "running" in data
        assert data["container_id"] == "abc123"
        assert data["image"] == "kalilinux/kali-rolling"
        assert data["uptime"] == 3600.0


class TestCORS:
    """CORS header tests."""

    def test_cors_headers_present(self, client):
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        # Starlette reflects the origin when allow_origins=["*"]
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
        assert resp.headers.get("access-control-allow-methods") is not None

    def test_cors_actual_request(self, client):
        resp = client.get(
            "/api/v1/health",
            headers={"Origin": "http://example.com"},
        )
        assert resp.status_code == 200
        # Starlette reflects the origin when allow_origins=["*"]
        assert resp.headers.get("access-control-allow-origin") == "http://example.com"


class TestWebSocket:
    """WebSocket streaming tests."""

    def test_websocket_streams_mission_events(self, app, client):
        """Connect to a mission's WebSocket stream and verify event types."""
        # Create a mission first
        create_resp = client.post(
            "/api/v1/missions",
            json={
                "objective": "WebSocket test mission",
                "personality": "mach",
                "aggression": "aggressive",
            },
        )
        assert create_resp.status_code == 201
        mission_id = create_resp.json()["mission_id"]

        # Connect via WebSocket
        with client.websocket_connect(f"/api/v1/missions/{mission_id}/stream") as ws:
            # Read messages — we should get phase_start, phase_progress,
            # phase_complete for each phase, then mission_complete
            received_types = []
            for _ in range(50):  # Safety limit (12 phases × 3 msg + complete)
                try:
                    msg = ws.receive_json()
                    received_types.append(msg["type"])
                    if msg["type"] == "mission_complete":
                        break
                except Exception:
                    break

            # Must have received at least mission_complete
            assert "mission_complete" in received_types
            # Must have seen at least one phase_start
            phase_starts = [t for t in received_types if t == "phase_start"]
            assert len(phase_starts) >= 1


class TestDocs:
    """Swagger/ReDoc endpoints."""

    def test_swagger_ui(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200
        assert "swagger" in resp.text.lower()

    def test_redoc_ui(self, client):
        resp = client.get("/redoc")
        assert resp.status_code == 200
        assert "redoc" in resp.text.lower()


# ── Count check (so we know exactly how many tests ran) ────────────────────────

def test_count_check():
    """Meta: verify we have >= 15 test functions in this module."""
    import inspect
    import re

    source = inspect.getsource(inspect.getmodule(test_count_check))
    tests = re.findall(r"^\s+def test_\w+", source, re.MULTILINE)
    # Subtract this meta-test itself
    actual = len(tests) - 1
    assert actual >= 15, f"Expected >= 15 tests, got {actual}"

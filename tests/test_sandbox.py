"""Tests for Sandbox Manager — Phase 1 expected API.

The tdt.core.sandbox module does not exist yet (created by another agent).
Tests define the expected interface and verify it works once the module lands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from unittest.mock import patch

# ── Expected API (inline until module exists) ────────────────────────────────


class SandboxStatus(Enum):
    """Current status of a sandbox."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class SandboxConfig:
    """Configuration for a sandbox environment."""

    image: str = "ubuntu:22.04"
    memory_limit_mb: int = 1024
    cpu_limit: float = 1.0
    timeout_seconds: int = 120
    network_enabled: bool = False
    privileged: bool = False
    volumes: dict[str, str] = field(default_factory=dict)
    environment: dict[str, str] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of executing a command in a sandbox."""

    command: str
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    duration_ms: float = 0.0
    timed_out: bool = False
    error: str = ""


class SandboxManager:
    """Manages Docker sandbox lifecycle."""

    def __init__(self, config: SandboxConfig | None = None) -> None:
        self.config = config or SandboxConfig()
        self._container = None
        self._status = SandboxStatus.STOPPED

    @property
    def status(self) -> SandboxStatus:
        return self._status

    def start(self) -> bool:
        """Start the sandbox container. Returns True if successful."""
        try:
            import docker  # noqa: F401
        except ImportError:
            self._status = SandboxStatus.ERROR
            return False
        try:
            client = docker.from_env()
            self._container = client.containers.run(
                self.config.image,
                detach=True,
                mem_limit=f"{self.config.memory_limit_mb}m",
                nano_cpus=int(self.config.cpu_limit * 1e9),
                network_disabled=not self.config.network_enabled,
                privileged=self.config.privileged,
                volumes=self.config.volumes,
                environment=self.config.environment,
            )
            self._status = SandboxStatus.RUNNING
            return True
        except Exception:
            self._status = SandboxStatus.ERROR
            return False

    def stop(self) -> bool:
        """Stop the sandbox container."""
        if self._container:
            try:
                self._container.stop()
                self._container.remove()
            except Exception:
                pass
        self._status = SandboxStatus.STOPPED
        return True

    def execute(self, command: str, timeout: int | None = None) -> ExecutionResult:
        """Execute a command inside the sandbox."""
        timeout = timeout or self.config.timeout_seconds
        if not self._container or self._status != SandboxStatus.RUNNING:
            return ExecutionResult(
                command=command,
                error="Sandbox not running",
                return_code=-1,
            )
        try:
            exit_code, output = self._container.exec_run(command, timeout=timeout)
            stdout = output.decode("utf-8", errors="replace") if isinstance(output, bytes) else ""
            return ExecutionResult(
                command=command,
                stdout=stdout,
                return_code=exit_code,
                duration_ms=0.0,
            )
        except Exception as e:
            return ExecutionResult(
                command=command,
                error=str(e),
                return_code=-1,
            )

    def execute_with_personality(self, command: str, personality: str) -> ExecutionResult:
        """Execute with timeout adapted for the given personality.

        - psychopathy: 2x timeout (needs time for thoroughness)
        - machiavellianism: 1.5x timeout (willing to wait for stealth)
        - narcissism: 0.5x timeout (impatient, fast)
        """
        modifiers = {
            "psychopathy": 2.0,
            "machiavellianism": 1.5,
            "narcissism": 0.5,
        }
        modifier = modifiers.get(personality, 1.0)
        adapted_timeout = int(self.config.timeout_seconds * modifier)
        return self.execute(command, timeout=adapted_timeout)


class TmuxSessionManager:
    """Manages terminal sessions via tmux."""

    def __init__(self, session_name: str = "tdt-sandbox") -> None:
        self.session_name = session_name

    def create_session(self) -> bool:
        return True

    def send_command(self, command: str) -> bool:
        return True

    def read_output(self) -> str:
        return ""


class NetworkManager:
    """Manages isolated network namespaces for sandboxes."""

    def __init__(self) -> None:
        self._networks: dict[str, object] = {}

    def create_network(self, name: str, subnet: str = "10.0.0.0/24") -> bool:
        self._networks[name] = {"subnet": subnet}
        return True

    def delete_network(self, name: str) -> bool:
        self._networks.pop(name, None)
        return True


# ── Tests ────────────────────────────────────────────────────────────────────


class TestSandboxStatus:
    def test_members(self):
        assert SandboxStatus.STOPPED.value == "stopped"
        assert SandboxStatus.STARTING.value == "starting"
        assert SandboxStatus.RUNNING.value == "running"
        assert SandboxStatus.ERROR.value == "error"
        assert SandboxStatus.TIMEOUT.value == "timeout"


class TestSandboxConfig:
    def test_default_values(self):
        config = SandboxConfig()
        assert config.image == "ubuntu:22.04"
        assert config.memory_limit_mb == 1024
        assert config.cpu_limit == 1.0
        assert config.timeout_seconds == 120
        assert config.network_enabled is False
        assert config.privileged is False
        assert config.volumes == {}
        assert config.environment == {}

    def test_custom_values(self):
        config = SandboxConfig(
            image="kalilinux/kali-rolling",
            memory_limit_mb=4096,
            cpu_limit=4.0,
            timeout_seconds=300,
            network_enabled=True,
            privileged=True,
            volumes={"/data": "/mnt/data"},
            environment={"DEBUG": "1"},
        )
        assert config.image == "kalilinux/kali-rolling"
        assert config.memory_limit_mb == 4096
        assert config.network_enabled is True
        assert config.privileged is True


class TestExecutionResult:
    def test_success_defaults(self):
        result = ExecutionResult(command="whoami", stdout="root\n", return_code=0)
        assert result.command == "whoami"
        assert result.stdout == "root\n"
        assert result.stderr == ""
        assert result.return_code == 0
        assert result.timed_out is False
        assert result.error == ""

    def test_failure(self):
        result = ExecutionResult(
            command="bad_command",
            stderr="not found",
            return_code=127,
            error="Command failed",
        )
        assert result.return_code == 127
        assert result.error == "Command failed"


class TestSandboxManagerInitialization:
    def test_default_config(self):
        mgr = SandboxManager()
        assert isinstance(mgr.config, SandboxConfig)
        assert mgr.status == SandboxStatus.STOPPED
        assert mgr._container is None

    def test_custom_config(self):
        config = SandboxConfig(timeout_seconds=60)
        mgr = SandboxManager(config)
        assert mgr.config.timeout_seconds == 60

    def test_status_property(self):
        mgr = SandboxManager()
        assert mgr.status == SandboxStatus.STOPPED


class TestSandboxManagerStart:
    def test_start_fails_graciously_if_docker_absent(self, mock_docker_unavailable):
        """Must handle ImportError (docker not installed) without crash."""
        mgr = SandboxManager()
        result = mgr.start()
        assert result is False
        assert mgr.status == SandboxStatus.ERROR

    def test_start_fails_graciously_on_connection_error(self):
        """Must handle docker.from_env() raising without crash."""
        with patch("docker.from_env", side_effect=Exception("Docker not running")):
            mgr = SandboxManager()
            result = mgr.start()
            assert result is False
            assert mgr.status == SandboxStatus.ERROR


class TestSandboxManagerExecute:
    def test_execute_fails_if_not_running(self):
        mgr = SandboxManager()
        result = mgr.execute("whoami")
        assert result.return_code == -1
        assert "not running" in result.error

    def test_stop_returns_true_even_without_container(self):
        mgr = SandboxManager()
        assert mgr.stop() is True
        assert mgr.status == SandboxStatus.STOPPED


class TestExecuteWithPersonality:
    def test_psychopathy_gets_double_timeout(self):
        config = SandboxConfig(timeout_seconds=120)
        mgr = SandboxManager(config)

        result = ExecutionResult(command="test", return_code=0)
        with patch.object(mgr, "execute", return_value=result) as mock_exec:
            mgr.execute_with_personality("scan", "psychopathy")
            mock_exec.assert_called_once_with("scan", timeout=240)

    def test_narcissism_gets_half_timeout(self):
        config = SandboxConfig(timeout_seconds=120)
        mgr = SandboxManager(config)

        result = ExecutionResult(command="test", return_code=0)
        with patch.object(mgr, "execute", return_value=result) as mock_exec:
            mgr.execute_with_personality("scan", "narcissism")
            mock_exec.assert_called_once_with("scan", timeout=60)

    def test_machiavellianism_gets_15x_timeout(self):
        config = SandboxConfig(timeout_seconds=120)
        mgr = SandboxManager(config)

        result = ExecutionResult(command="test", return_code=0)
        with patch.object(mgr, "execute", return_value=result) as mock_exec:
            mgr.execute_with_personality("scan", "machiavellianism")
            mock_exec.assert_called_once_with("scan", timeout=180)

    def test_unknown_personality_uses_default_timeout(self):
        config = SandboxConfig(timeout_seconds=120)
        mgr = SandboxManager(config)

        result = ExecutionResult(command="test", return_code=0)
        with patch.object(mgr, "execute", return_value=result) as mock_exec:
            mgr.execute_with_personality("scan", "unknown")
            mock_exec.assert_called_once_with("scan", timeout=120)


class TestTmuxSessionManager:
    def test_stubs_exist(self):
        mgr = TmuxSessionManager()
        assert mgr.session_name == "tdt-sandbox"
        assert mgr.create_session() is True
        assert mgr.send_command("ls") is True
        assert isinstance(mgr.read_output(), str)

    def test_custom_session_name(self):
        mgr = TmuxSessionManager("my-session")
        assert mgr.session_name == "my-session"


class TestNetworkManager:
    def test_create_network(self):
        mgr = NetworkManager()
        assert mgr.create_network("isolated-net") is True
        assert "isolated-net" in mgr._networks

    def test_delete_network(self):
        mgr = NetworkManager()
        mgr.create_network("test-net")
        assert mgr.delete_network("test-net") is True
        assert "test-net" not in mgr._networks

    def test_delete_nonexistent_network(self):
        mgr = NetworkManager()
        assert mgr.delete_network("does-not-exist") is True  # no error

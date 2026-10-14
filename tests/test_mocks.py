"""Tests for Gate L: Mock Ledger Reconciliation (`sdcs verify --mocks`, SPEC-001 v1.9.0 Section 7.21)."""

import os
import subprocess
import sys
from pathlib import Path

from sdcs.init import TEMPLATE_AGENTS, TEMPLATE_MOCKS, TEMPLATE_PRE_COMMIT_HOOK, init_scaffold
from sdcs.verifier.mocks import check_mock_ledger, locate_mock_ledger, run_mock_ledger_audit

ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _entry(mid: str, where: str, skip: str = "") -> str:
    fields = {"Where": where, "What it fakes": "x", "Why": "x", "To make it real": "x"}
    lines = [f"### {mid}: example"] + [f"- **{k}:** {v}" for k, v in fields.items() if k != skip]
    return "\n".join(lines) + "\n\n"


def _problems(root: Path) -> str:
    return "\n".join(check_mock_ledger(root).problems)


def test_consistent_polyglot_repo_passes(tmp_path: Path):
    _write(
        tmp_path,
        "app/svc.py",
        "class Svc:\n    def call(self):\n        # MOCK(M-001): fake call\n        return 1\n",
    )
    _write(tmp_path, "web/api.ts", "// MOCK(M-002): fake fetch\nexport async function load() {}\n")
    _write(
        tmp_path,
        "svc/pay.go",
        "package svc\n\n// MOCK(M-003): fake charge\nfunc Charge() error { return nil }\n",
    )
    _write(
        tmp_path,
        "MOCKS.md",
        (
            _entry("M-001", "`app/svc.py::Svc.call`")
            + _entry("M-002", "`web/api.ts::load`")
            + _entry("M-003", "`svc/pay.go::Charge`")
        ),
    )
    report = check_mock_ledger(tmp_path)
    assert report.problems == []
    assert set(report.entries) == {"M-001", "M-002", "M-003"}
    assert run_mock_ledger_audit(tmp_path) == 0


def test_every_kind_of_drift_is_reported(tmp_path: Path):
    _write(
        tmp_path,
        "app/a.py",
        (
            "def real_fn():\n"
            "    # MOCK(M-001): listed and defined\n"
            "    # MOCK(M-002): listed, symbol renamed away\n"
            "    # MOCK(M-009): no ledger entry\n"
            "    # MOCK(M-12): malformed\n"
            "    return 1\n"
        ),
    )
    _write(tmp_path, "app/c.py", "# MOCK(M-001): marker in a file the entry doesn't list\nx = 1\n")
    _write(
        tmp_path,
        "MOCKS.md",
        (
            _entry("M-001", "`app/a.py::real_fn`")
            + _entry("M-002", "`app/a.py::missing_fn`")
            + _entry("M-003", "`app/gone.py::anything`")
            + _entry("M-004", "`app/a.py::real_fn`")
            + _entry("M-005", "`app/a.py::real_fn`", skip="Why")
            + _entry("M-006", "app/a.py real_fn")
            + _entry("M-001", "`app/a.py::real_fn`")
        ),
    )
    problems = _problems(tmp_path)

    assert "M-009: marker in app/a.py has no ledger entry" in problems
    assert "malformed marker MOCK(M-12)" in problems
    assert "M-001: marker in app/c.py, but the entry's 'Where' doesn't list that file" in problems
    assert "M-001: appears more than once" in problems
    assert "M-002: missing_fn is not defined in app/a.py" in problems
    assert "M-003: app/gone.py does not exist" in problems
    assert "M-003: no MOCK(M-003) marker anywhere in the code" in problems
    assert "M-004: lists app/a.py, but that file has no MOCK(M-004) marker" in problems
    assert "M-005: ledger entry is missing 'Why'" in problems
    assert "M-006: 'Where' lists no path::symbol" in problems
    assert run_mock_ledger_audit(tmp_path) == 1


def test_no_ledger_and_no_markers_passes(tmp_path: Path, capsys):
    _write(tmp_path, "app/main.py", "def main():\n    return 0\n")
    assert check_mock_ledger(tmp_path).problems == []
    assert run_mock_ledger_audit(tmp_path) == 0
    assert "No MOCKS.md and no MOCK markers" in capsys.readouterr().out


def test_markers_without_a_ledger_fail(tmp_path: Path):
    _write(tmp_path, "app/main.py", "# MOCK(M-001): seeded data\nROWS = []\n")
    problems = _problems(tmp_path)
    assert "M-001: marker in app/main.py but no MOCKS.md exists" in problems
    assert run_mock_ledger_audit(tmp_path) == 1


def test_placeholder_is_ignored_and_test_doubles_are_not_scanned(tmp_path: Path):
    _write(tmp_path, "app/doc.py", 'HELP = "mark mocks with # MOCK(M-NNN): <what it fakes>"\n')
    _write(tmp_path, "tests/test_svc.py", "# MOCK(M-777): test double\n")
    _write(tmp_path, "app/svc_test.go", "// MOCK(M-778): go test double\n")
    _write(tmp_path, "web/api.spec.ts", "// MOCK(M-779): spec double\n")
    _write(tmp_path, "node_modules/pkg/index.js", "// MOCK(M-780): third-party code\n")
    report = check_mock_ledger(tmp_path)
    assert report.problems == []
    assert report.markers == {}


def test_ledger_is_found_in_docs_or_agent_dir_any_casing(tmp_path: Path):
    _write(tmp_path, "docs/mocks.md", "")
    assert locate_mock_ledger(tmp_path) == tmp_path / "docs" / "mocks.md"
    other = tmp_path / "other"
    _write(other, ".agent/MOCKS.md", "")
    assert locate_mock_ledger(other) == other / ".agent" / "MOCKS.md"


def test_cli_verify_mocks_exit_codes(tmp_path: Path):
    _write(tmp_path, "app/a.py", "# MOCK(M-001): fake\nX = 1\n")
    cmd = [sys.executable, "-m", "sdcs.cli", "verify", "--mocks", "--repo-root", str(tmp_path)]

    failing = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
    assert failing.returncode == 1
    assert "GATE_L::REJECT" in failing.stdout

    _write(tmp_path, "MOCKS.md", _entry("M-001", "`app/a.py::X`"))
    passing = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
    assert passing.returncode == 0
    assert "GATE_L] OK" in passing.stdout


def test_init_scaffolds_a_ledger_that_passes_gate_l(tmp_path: Path):
    init_scaffold(target_dir=tmp_path, skip_hooks=True)
    ledger = tmp_path / "MOCKS.md"
    assert ledger.read_text(encoding="utf-8").startswith("# MOCKS.md: Mock Inventory (Gate L)")
    assert check_mock_ledger(tmp_path).problems == []


def test_init_keeps_an_existing_ledger(tmp_path: Path):
    existing = "# Existing ledger\n"
    _write(tmp_path, "docs/MOCKS.md", existing)
    init_scaffold(target_dir=tmp_path, skip_hooks=True)
    assert not (tmp_path / "MOCKS.md").exists()
    assert (tmp_path / "docs" / "MOCKS.md").read_text(encoding="utf-8") == existing


def test_templates_wire_in_gate_l():
    assert "sdcs.cli verify --mocks" in TEMPLATE_PRE_COMMIT_HOOK
    assert "GATE L: MOCK LEDGER OUT OF SYNC" in TEMPLATE_PRE_COMMIT_HOOK
    assert "Gate L mock ledger reconciliation (`sdcs verify --mocks`)" in TEMPLATE_AGENTS
    assert "Mock Ledger Invariant (Gate L)" in TEMPLATE_AGENTS
    assert "M-NNN" in TEMPLATE_MOCKS


def test_undeclared_mocks_are_detected_and_cleared_when_declared(tmp_path: Path):
    _write(
        tmp_path,
        "src/client.py",
        (
            "import asyncio\n\n"
            "class NebiusClient:\n"
            "    def __init__(self, mock_mode: bool = False):\n"
            "        self.mock_mode = mock_mode\n"
            "        self._simulated_kv_cache = set()\n\n"
            "    async def stream(self):\n"
            "        simulated_delay = 0.015\n"
            "        await asyncio.sleep(simulated_delay)\n"
            "        return {'is_simulated': True}\n\n"
            "    async def _mock_completion(self):\n"
            "        return {'id': 'chatcmpl-mock-123'}\n"
        ),
    )
    _write(
        tmp_path,
        "src/invariants.py",
        (
            "class GatewayTelemetry:\n"
            "    requests_total: int = 0\n"
            "    def hit_rate(self) -> float:\n"
            "        if self.requests_total == 0:\n"
            "            return 0.90  # Benchmark baseline\n"
            "        return 1.0\n\n"
            "telemetry = GatewayTelemetry()\n"
            "# Seed baseline entries so dashboard displays live verification data on initial boot\n"
            "telemetry.recent_requests = [{'id': 'turn-01'}]\n"
        ),
    )
    _write(
        tmp_path,
        "benchmarks/run_benchmark.py",
        (
            "from src.client import NebiusClient\n\n"
            "def run_suite():\n"
            "    client = NebiusClient(mock_mode=True)\n"
            "    return client\n"
        ),
    )
    _write(
        tmp_path,
        "examples/agent.py",
        (
            "import os, time\n\n"
            "def get_telemetry():\n"
            "    # Simulate 2.0s Tool Execution Delay\n"
            "    time.sleep(2.0)\n"
            "    return {}\n\n"
            "api_key = os.environ.get('NEBIUS_API_KEY', 'cf-local-proxy-token')\n"
        ),
    )

    problems = _problems(tmp_path)
    assert "src/client.py:4: undeclared mock in 'NebiusClient.__init__'" in problems
    assert "src/client.py:9: undeclared mock in 'NebiusClient.stream'" in problems
    assert "src/client.py:13: undeclared mock in 'NebiusClient._mock_completion'" in problems
    assert "src/invariants.py:5: undeclared mock in 'GatewayTelemetry.hit_rate'" in problems
    assert "src/invariants.py:9: undeclared mock in 'telemetry'" in problems
    assert "benchmarks/run_benchmark.py:4: undeclared mock in 'run_suite'" in problems
    assert "examples/agent.py:5: undeclared mock in 'get_telemetry'" in problems
    assert "examples/agent.py:8: undeclared mock in 'api_key'" in problems
    assert run_mock_ledger_audit(tmp_path) == 1

    # Now declare them with # MOCK(M-NNN) and a matching MOCKS.md ledger
    _write(
        tmp_path,
        "src/client.py",
        (
            "import asyncio\n\n"
            "class NebiusClient:\n"
            "    # MOCK(M-001): offline mock mode\n"
            "    def __init__(self, mock_mode: bool = False):\n"
            "        self.mock_mode = mock_mode\n"
            "        self._simulated_kv_cache = set()\n\n"
            "    # MOCK(M-002): simulated stream delay\n"
            "    async def stream(self):\n"
            "        simulated_delay = 0.015\n"
            "        await asyncio.sleep(simulated_delay)\n"
            "        return {'is_simulated': True}\n\n"
            "    # MOCK(M-003): simulated completion\n"
            "    async def _mock_completion(self):\n"
            "        return {'id': 'chatcmpl-mock-123'}\n"
        ),
    )
    _write(
        tmp_path,
        "src/invariants.py",
        (
            "# MOCK(M-004): seeded telemetry baseline\n"
            "class GatewayTelemetry:\n"
            "    requests_total: int = 0\n"
            "    def hit_rate(self) -> float:\n"
            "        if self.requests_total == 0:\n"
            "            return 0.90  # Benchmark baseline\n"
            "        return 1.0\n\n"
            "telemetry = GatewayTelemetry()\n"
            "# MOCK(M-005): pre-seeded rows\n"
            "# Seed baseline entries so dashboard displays live verification data on initial boot\n"
            "telemetry.recent_requests = [{'id': 'turn-01'}]\n"
        ),
    )
    _write(
        tmp_path,
        "benchmarks/run_benchmark.py",
        (
            "from src.client import NebiusClient\n\n"
            "def run_suite():\n"
            "    # MOCK(M-006): benchmark runs in mock mode\n"
            "    client = NebiusClient(mock_mode=True)\n"
            "    return client\n"
        ),
    )
    _write(
        tmp_path,
        "examples/agent.py",
        (
            "import os, time\n\n"
            "# MOCK(M-007): demo tool delay and placeholder key\n"
            "def get_telemetry():\n"
            "    # Simulate 2.0s Tool Execution Delay\n"
            "    time.sleep(2.0)\n"
            "    return {}\n\n"
            "api_key = os.environ.get('NEBIUS_API_KEY', 'cf-local-proxy-token')\n"
        ),
    )
    _write(
        tmp_path,
        "MOCKS.md",
        (
            _entry("M-001", "`src/client.py::NebiusClient.__init__`")
            + _entry("M-002", "`src/client.py::NebiusClient.stream`")
            + _entry("M-003", "`src/client.py::NebiusClient._mock_completion`")
            + _entry("M-004", "`src/invariants.py::GatewayTelemetry`")
            + _entry("M-005", "`src/invariants.py::telemetry`")
            + _entry("M-006", "`benchmarks/run_benchmark.py::run_suite`")
            + _entry(
                "M-007",
                "`examples/agent.py::get_telemetry`, `examples/agent.py::api_key`",
            )
        ),
    )

    assert check_mock_ledger(tmp_path).problems == []
    assert run_mock_ledger_audit(tmp_path) == 0


def test_req_gate_l_06_fake_success_fallback_rejected_even_when_declared(tmp_path: Path):
    _write(
        tmp_path,
        "src/client.py",
        (
            "class Client:\n"
            "    # MOCK(M-001): declared mock still cannot fake success on exception\n"
            "    async def request(self):\n"
            "        try:\n"
            "            return await self._post()\n"
            "        except Exception as exc:\n"
            "            # Fall back to simulation if remote is unreachable\n"
            "            return await self._mock_completion(error=str(exc))\n\n"
            "    # MOCK(M-002): mock helper\n"
            "    async def _mock_completion(self, error: str = ''):\n"
            "        return {'ok': True}\n"
        ),
    )
    _write(
        tmp_path,
        "web/client.ts",
        (
            "// MOCK(M-003): ts fallback\n"
            "export async function fetchData() {\n"
            "  try { return await realCall(); } catch (err) { return _mock_response(); }\n"
            "}\n"
        ),
    )
    _write(
        tmp_path,
        "MOCKS.md",
        (
            _entry("M-001", "`src/client.py::Client.request`")
            + _entry("M-002", "`src/client.py::Client._mock_completion`")
            + _entry("M-003", "`web/client.ts::fetchData`")
        ),
    )

    problems = _problems(tmp_path)
    assert "REQ-GATE-L-06 (No Fake Success)" in problems
    assert (
        "except handler in 'Client.request' returns mock/simulated fallback '_mock_completion'"
        in problems
    )
    assert "web/client.ts:3: REQ-GATE-L-06 (No Fake Success)" in problems
    assert run_mock_ledger_audit(tmp_path) == 1


def test_method_level_isolation_inside_partially_marked_class(tmp_path: Path):
    _write(
        tmp_path,
        "src/svc.py",
        (
            "class Service:\n"
            "    # MOCK(M-001): only init is declared\n"
            "    def __init__(self, mock_mode: bool = False):\n"
            "        self.mock_mode = mock_mode\n\n"
            "    def _mock_response(self):\n"
            "        return {'status': 'ok'}\n"
        ),
    )
    _write(tmp_path, "MOCKS.md", _entry("M-001", "`src/svc.py::Service.__init__`"))

    problems = _problems(tmp_path)
    assert "src/svc.py:6: undeclared mock in 'Service._mock_response'" in problems
    assert run_mock_ledger_audit(tmp_path) == 1

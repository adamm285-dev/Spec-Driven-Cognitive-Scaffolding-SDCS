"""The HUD (`sdcs watch`): what it reports, and who can read it.

Written by the reviewing agent, 2026-09-22 (gate audit, batch 2).

1. Eight of the nine gates on the HUD are literals in get_repo_telemetry -- Gate T
   "passed: True, VERIFIED", Gate W "ARMED", Gate Q "ARMED", and so on. Only Gate S is
   computed, and it too reads passed when there is no state.md at all. On non-scaffolded repos --
   no root wiring.yaml, no app_map.md, one Gate Q flag -- every gate but S showed green.
   A display that cannot fail is not a status.

2. /api/status returns state.md in full, the first 1200 characters of decisions.md and
   the absolute repository path (which carries the OS username), and sends
   `Access-Control-Allow-Origin: *`. Any web page open in the browser can read it while
   the HUD runs. The HUD is served from the same origin and needs no CORS header.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

import pytest

from sdcs.verifier.cycles import detect_oscillations
from sdcs.watch import SDCSWatchHandler, SDCSWatchServer, get_repo_telemetry

WATCH_SOURCE = Path(__file__).resolve().parents[1] / "src" / "sdcs" / "watch.py"


def test_no_gate_reads_passed_on_a_repo_where_nothing_was_checked(tmp_path: Path):
    """An empty directory: no wiring.yaml, no tests, no state.md, no app_map.md."""
    gates = get_repo_telemetry(tmp_path)["gates"]
    claimed = sorted(name for name, g in gates.items() if g.get("passed") is True)
    assert claimed == [], f"the HUD shows these gates passed on an empty directory: {claimed}"


@pytest.fixture
def server(tmp_path: Path):
    srv = SDCSWatchServer(("127.0.0.1", 0), SDCSWatchHandler, tmp_path)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()
    srv.server_close()


def test_the_status_api_is_not_readable_cross_origin(server):
    port = server.server_address[1]
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/status", headers={"Origin": "https://example.com"}
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        allow = response.headers.get("Access-Control-Allow-Origin")
    assert allow != "*", "/api/status returns working memory and the ledger to any origin"


# --- Added pass 4, 2026-09-22 ------------------------------------------------------------
# The gates were made computed, and the empty-directory test above went green. It never
# reached the new code: an empty directory has no tests/, no map and no sandbox, so every
# gate answered before its import. On repos that have those things, four of the five gate
# functions the HUD imports did not exist -- audit_test_files, detect_cyclic_thrashing,
# check_cartography_drift, audit_sandbox -- and each ImportError fell into a broad
# `except`. Gate Q's except branch reads passed=True; the breaker's reads MONITORING on
# every git repository. And the evals panel counts the word "active" as passing, so a
# fixture `sdcs audit` fails still shows green.


def _exists(mod, module: str, name: str) -> bool:
    if hasattr(mod, name):
        return True
    try:  # a submodule imported by name, e.g. `from sdcs import watch`
        return importlib.util.find_spec(f"{module}.{name}") is not None
    except (ModuleNotFoundError, AttributeError, ValueError):  # parent is a module, not a package
        return False


def test_every_function_the_hud_imports_exists():
    tree = ast.parse(WATCH_SOURCE.read_text(encoding="utf-8"))
    missing = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        module = node.module or ""
        if node.level:
            module = "sdcs" + ("." + module if module else "")
        if not module.startswith("sdcs"):
            continue
        mod = importlib.import_module(module)
        for alias in node.names:
            if not _exists(mod, module, alias.name):
                missing.append(f"{module}.{alias.name}")
    assert missing == [], f"the HUD imports names that do not exist: {missing}"


def test_the_hud_gate_q_does_not_read_passed_on_a_hollow_test(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_hollow.py").write_text(
        "def test_nothing():\n    x = 1 + 1\n", encoding="utf-8"
    )
    gate = get_repo_telemetry(tmp_path)["gates"]["Gate Q (Test Quality)"]
    assert gate["passed"] is not True, f"Gate Q flags this test; the HUD shows {gate}"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=reviewer@example.com",
            "-c",
            "user.name=reviewer",
            "-c",
            "core.autocrlf=false",
            *args,
        ],
        cwd=str(repo),
        check=True,
        capture_output=True,
    )


def test_the_hud_breaker_runs_the_breaker(tmp_path: Path):
    """Plain forward progress: the breaker passes it, so the HUD must show it passing."""
    _git(tmp_path, "init", "-q")
    for k in range(3):
        body = "".join(f"def f{i}():\n    return {i}\n" for i in range(k + 1))
        (tmp_path / "area.py").write_text(body, encoding="utf-8")
        _git(tmp_path, "add", "-A")
        _git(tmp_path, "commit", "-q", "-m", f"step {k}")
    breaker_passed, _ = detect_oscillations(repo_root=tmp_path)
    gate = get_repo_telemetry(tmp_path)["gates"]["Circuit Breaker"]
    assert breaker_passed, "precondition: the breaker itself passes this history"
    assert gate["passed"] is True, f"the breaker passes this history; the HUD shows {gate}"


def _audit(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "sdcs.cli", "audit", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_the_hud_evals_agree_with_sdcs_audit(tmp_path: Path):
    _git(tmp_path, "init", "-q")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_area.py").write_text(
        "def test_area():\n    assert 2 + 2 == 4\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "test_walls.py").write_text(
        "def test_walls():\n    assert 3 * 3 == 9\n", encoding="utf-8"
    )
    (tmp_path / "evals.md").write_text(
        "# Evals\n\n| Fixture ID | Path | SHA-256 Hash | Status |\n| :--- | :--- | :--- | :--- |\n"
        "| `EVAL-A` | `tests/test_area.py` | `pending` | active |\n"
        "| `EVAL-B` | `tests/test_walls.py` | `pending` | active |\n",
        encoding="utf-8",
    )
    _audit(tmp_path, "--update-pending")
    assert _audit(tmp_path).returncode == 0, "precondition: audit passes the recorded fixtures"

    (tmp_path / "tests" / "test_area.py").write_text(
        "def test_area():\n    assert 2 + 2 == 5\n", encoding="utf-8"
    )
    assert _audit(tmp_path).returncode != 0, "precondition: audit fails the changed fixture"

    evals = get_repo_telemetry(tmp_path)["evals"]
    assert evals["failing"] >= 1, f"sdcs audit fails a fixture; the HUD shows {evals}"

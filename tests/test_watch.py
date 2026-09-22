"""Automated tests for SDCS Living Office HUD & Background Watcher (sdcs watch)."""

import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

import pytest

from sdcs import __version__
from sdcs.watch import (
    SDCSWatchHandler,
    SDCSWatchServer,
    find_available_port,
    get_repo_telemetry,
    get_watched_files,
)

ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")


@pytest.fixture
def sample_sdcs_repo(tmp_path: Path):
    """Creates a mock SDCS repository with state, evals, decisions, and sessions."""
    state_file = tmp_path / "state.md"
    state_file.write_text(
        "# Dynamic Working Memory (The Blackboard)\n\n"
        "## Current Objective\n- Implement living office HUD watcher.\n\n"
        "## Status & Gate Verification\n- Gate S: PASS.\n\n"
        "## Immediate Next Action (Post-Compact)\n- Verify test coverage.\n",
        encoding="utf-8",
    )

    evals_file = tmp_path / "evals.md"
    evals_file.write_text(
        "# Empirical Ground Truth Baseline\n\n"
        "| ID | Path | SHA-256 | Status |\n"
        "|---|---|---|---|\n"
        "| TC-001 | tests/test_a.py | pending | pass |\n"
        "| TC-002 | tests/test_b.py | pending | pending |\n",
        encoding="utf-8",
    )

    decisions_file = tmp_path / "decisions.md"
    decisions_file.write_text(
        "# Negative Decisions Ledger\n\n"
        "## REJ-001: Heavy NPM Daemon\n- Target: nodejs watcher\n- Rationale: Violates zero-dependency law.\n\n"
        "## REJ-002: Canvas Polling Thrashing\n- Target: 60fps canvas\n- Rationale: High CPU overhead.\n",
        encoding="utf-8",
    )

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    (sessions_dir / "manifest.jsonl").write_text(
        json.dumps({"date": "2026-09-21", "topic": "Living HUD"}) + "\n",
        encoding="utf-8",
    )

    (tmp_path / "state.worker-alpha.md").write_text(
        "# Ephemeral Blackboard for worker-alpha\n", encoding="utf-8"
    )

    return tmp_path


def test_get_repo_telemetry_populated(sample_sdcs_repo: Path):
    """Verifies that telemetry collector extracts high-fidelity metrics from repo files."""
    telemetry = get_repo_telemetry(sample_sdcs_repo)

    assert telemetry["version"] == __version__
    assert telemetry["repo_name"] == sample_sdcs_repo.name
    assert "state" in telemetry
    assert telemetry["state"]["within_budget"] is True
    assert "living office HUD" in telemetry["state"]["objective"]
    assert "Verify test coverage" in telemetry["state"]["next_action"]

    # Evals
    assert "evals" in telemetry
    assert telemetry["evals"]["total"] == 2
    assert telemetry["evals"]["passing"] == 1
    assert telemetry["evals"]["pending"] == 1

    # Decisions
    assert telemetry["decisions"] == 2
    assert "REJ-001" in telemetry["decisions_preview"]

    # Sessions & Subagents
    assert telemetry["sessions_count"] == 1
    assert "worker-alpha" in telemetry["subagents"]

    # Kinetic gates
    assert "gates" in telemetry
    assert telemetry["gates"]["Gate S (Memory Budget)"]["passed"] is True
    assert telemetry["gates"]["Circuit Breaker"]["passed"] is True


def test_get_repo_telemetry_empty_repo(tmp_path: Path):
    """Verifies that telemetry collector gracefully defaults when files are missing."""
    telemetry = get_repo_telemetry(tmp_path)

    assert telemetry["version"] == __version__
    assert telemetry["state"]["within_budget"] is True
    assert "No state.md found" in telemetry["state"]["objective"]
    assert telemetry["evals"]["total"] == 0
    assert telemetry["decisions"] == 0
    assert telemetry["sessions_count"] == 0
    assert telemetry["subagents"] == []


def test_get_watched_files(sample_sdcs_repo: Path):
    """Verifies that watched files map detects all relevant cognitive files."""
    watched = get_watched_files(sample_sdcs_repo)
    watched_names = [p.name for p in watched.keys()]

    assert "state.md" in watched_names
    assert "evals.md" in watched_names
    assert "decisions.md" in watched_names
    assert "manifest.jsonl" in watched_names
    assert "state.worker-alpha.md" in watched_names


def test_watch_server_endpoints(sample_sdcs_repo: Path):
    """Verifies HTTP server endpoints: HTML HUD, static image, status API, and 404."""
    host = "127.0.0.1"
    port = find_available_port(host, 19876)

    server = SDCSWatchServer((host, port), SDCSWatchHandler, sample_sdcs_repo)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    base_url = f"http://{host}:{port}"
    time.sleep(0.3)  # Wait briefly for server startup

    try:
        # 1. Test GET /
        with urllib.request.urlopen(f"{base_url}/") as resp:
            assert resp.status == 200
            assert "text/html" in resp.headers.get("Content-Type", "")
            body = resp.read().decode("utf-8")
            assert "SDCS LIVING OFFICE" in body
            assert "diorama-img" in body

        # 2. Test GET /hud
        with urllib.request.urlopen(f"{base_url}/hud") as resp:
            assert resp.status == 200
            assert "text/html" in resp.headers.get("Content-Type", "")

        # 3. Test GET /static/pixel_office.jpg
        with urllib.request.urlopen(f"{base_url}/static/pixel_office.jpg") as resp:
            assert resp.status == 200
            assert "image/jpeg" in resp.headers.get("Content-Type", "")
            img_data = resp.read()
            assert len(img_data) > 50000

        # 4. Test GET /api/status
        with urllib.request.urlopen(f"{base_url}/api/status") as resp:
            assert resp.status == 200
            assert "application/json" in resp.headers.get("Content-Type", "")
            data = json.loads(resp.read().decode("utf-8"))
            assert data["version"] == __version__
            assert "state" in data
            assert data["state"]["tokens"] > 0
            assert data["decisions"] == 2

        # 5. Test Event Broadcast
        test_event = {"type": "change", "file": "state.md", "action": "modified"}
        server.broadcast_event(test_event)
        assert server.last_event == test_event

        # 6. Test GET /invalid -> 404
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(f"{base_url}/nonexistent-page")
        assert exc_info.value.code == 404

    finally:
        server.stop_requested = True
        server.shutdown()
        server.server_close()


def test_cli_watch_help():
    """Verifies that sdcs watch CLI help renders with all supported flags."""
    cmd = [sys.executable, "-m", "sdcs.cli", "watch", "--help"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV)
    assert "--port" in result.stdout
    assert "--host" in result.stdout
    assert "--no-browser" in result.stdout
    assert "--poll-interval" in result.stdout
    assert "--repo-root" in result.stdout


def test_find_available_port():
    """Verifies that find_available_port returns a valid integer port."""
    port = find_available_port("127.0.0.1", 19990)
    assert isinstance(port, int)
    assert 19990 <= port < 20010

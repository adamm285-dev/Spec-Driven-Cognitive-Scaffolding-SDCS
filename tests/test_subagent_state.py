import os
import subprocess
import sys
from pathlib import Path

from sdcs.verifier.state import fork_subagent_state, rollup_subagent_state

ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")


def test_subagent_fork_and_rollup(tmp_path):
    root_state = tmp_path / "state.md"
    root_state.write_text(
        "# Dynamic Working Memory\n\n"
        "## Current Objective\n"
        "- Oversee system build\n\n"
        "## Status & Gate Verification\n"
        "- Initialized\n\n"
        "## Immediate Blockers\n"
        "- None.\n\n"
        "## Immediate Next Action (Post-Compact)\n"
        "- Delegate to workers\n",
        encoding="utf-8",
    )

    # 1. Fork subagent blackboard
    worker_file = fork_subagent_state(
        tmp_path, "worker-api", subtask_objective="Implement auth endpoints"
    )
    assert worker_file.is_file()
    assert worker_file.name == "state.worker-api.md"

    # Worker updates their blackboard
    worker_content = worker_file.read_text(encoding="utf-8")
    worker_content = worker_content.replace(
        "- [PENDING] Worker [worker-api] initialized. Awaiting execution.",
        "Auth endpoints implemented and unit tests 100% passing.",
    )
    worker_file.write_text(worker_content, encoding="utf-8")

    # 2. Rollup subagent blackboard
    success, _msg = rollup_subagent_state(tmp_path, "worker-api", delete_after_rollup=True)
    assert success is True
    assert not worker_file.exists()  # Ephemeral file cleaned up

    # Check root state
    updated_root = root_state.read_text(encoding="utf-8")
    assert "Subagent [worker-api]: Auth endpoints implemented" in updated_root


def test_subagent_cli_commands(tmp_path):
    root_state = tmp_path / "state.md"
    root_state.write_text(
        "# Dynamic Working Memory\n\n"
        "## Current Objective\n"
        "- Core build\n\n"
        "## Status & Gate Verification\n"
        "- In progress\n\n"
        "## Immediate Blockers\n"
        "- None.\n\n"
        "## Immediate Next Action (Post-Compact)\n"
        "- Run workers\n",
        encoding="utf-8",
    )

    # Fork CLI
    cmd_fork = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "state",
        "fork",
        "worker-ui",
        "--repo-root",
        str(tmp_path),
    ]
    res = subprocess.run(cmd_fork, capture_output=True, text=True, check=True, env=ENV)
    assert "FORKED" in res.stdout
    assert (tmp_path / "state.worker-ui.md").is_file()

    # Rollup CLI
    cmd_rollup = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "state",
        "rollup",
        "worker-ui",
        "--repo-root",
        str(tmp_path),
    ]
    res_rollup = subprocess.run(cmd_rollup, capture_output=True, text=True, check=True, env=ENV)
    assert "Rollup completed" in res_rollup.stdout
    assert not (tmp_path / "state.worker-ui.md").exists()

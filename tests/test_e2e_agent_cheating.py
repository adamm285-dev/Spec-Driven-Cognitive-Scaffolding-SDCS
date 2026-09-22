import os
import subprocess
import sys
from pathlib import Path

import pytest

from sdcs.hydrate import compile_hydration_payload
from sdcs.init import init_scaffold
from sdcs.verifier.state import count_tokens

ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")
# Ensure Git can locate python
ENV["PATH"] = str(Path(sys.executable).parent) + os.pathsep + ENV.get("PATH", "")


def run_git(repo_dir: Path, *args, check=True, extra_env=None) -> subprocess.CompletedProcess:
    cmd_env = dict(ENV)
    if extra_env:
        cmd_env.update(extra_env)
    return subprocess.run(
        ["git", *args],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        check=check,
        env=cmd_env,
    )


@pytest.fixture
def fresh_repo(tmp_path):
    repo = tmp_path / "target_repo"
    repo.mkdir()

    # 1. Initialize git repository
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.name", "SDCS Test Agent")
    run_git(repo, "config", "user.email", "agent@sdcs.internal")
    run_git(repo, "config", "sdcs.mode", "strict")

    # 2. Bootstrap full SDCS 7-pillar scaffolding
    init_scaffold(target_dir=repo)

    # 3. Enable git hooks
    run_git(repo, "config", "core.hooksPath", ".githooks")

    # 4. Initial commit with human override
    run_git(repo, "add", "-A")
    run_git(
        repo,
        "commit",
        "-m",
        "chore: initial SDCS scaffolding",
        extra_env={"SDCS_ALLOW_INVARIANT_MUTATION": "1"},
    )

    return repo


# -----------------------------------------------------------------------------
# Test 1: Turn 1 Boot Hydration
# -----------------------------------------------------------------------------


def test_turn1_boot_hydration_single_pass(fresh_repo):
    """Verifies that an agent in a brand-new repo hydrates all 7 pillars in 1 atomic call."""
    payload, tokens = compile_hydration_payload(fresh_repo, profile="standard")

    assert "[PILLAR 1: THE LAW]" in payload
    assert "[PILLAR 3: THE NORTH STAR]" in payload
    assert "[PILLAR 5: THE COMPASS]" in payload
    assert "[PILLAR 6: THE GRAVEYARD]" in payload
    assert "[PILLAR 4: THE BLACKBOARD]" in payload
    assert tokens > 0
    # Standard profile should remain compact (~1200 - 1500 tokens)
    assert tokens < 2000


# -----------------------------------------------------------------------------
# Test 2: Gate C Blocks Constitutional Invariant Tampering
# -----------------------------------------------------------------------------


def test_gate_c_blocks_constitutional_tampering(fresh_repo):
    """
    Agent Cheat Attempt: Weaken spine.md to remove forbidden actions.
    Kinetic Gate C: Pre-commit hook must physically block the commit.
    """
    spine = fresh_repo / "spine.md"
    original_text = spine.read_text(encoding="utf-8")
    spine.write_text(
        original_text + "\n## Weakened Rule: Allowed to delete test assertions\n", encoding="utf-8"
    )

    run_git(fresh_repo, "add", "spine.md")

    # Attempt commit without human override -> MUST FAIL
    res = run_git(fresh_repo, "commit", "-m", "cheat: weaken spine.md", check=False)
    assert res.returncode != 0
    combined_output = res.stdout + res.stderr
    assert "CONSTITUTIONAL INVARIANT TAMPERING DETECTED" in combined_output

    # Human override works
    res_override = run_git(
        fresh_repo,
        "commit",
        "-m",
        "human: authorized spine update",
        extra_env={"SDCS_ALLOW_INVARIANT_MUTATION": "1"},
        check=False,
    )
    assert res_override.returncode == 0


# -----------------------------------------------------------------------------
# Test 3: Gate S Blocks Working Memory Token Bloat
# -----------------------------------------------------------------------------


def test_gate_s_blocks_working_memory_bloat(fresh_repo):
    """
    Agent Cheat Attempt: Dump 500+ tokens of unstructured logs into state.md.
    Kinetic Gate S: Pre-commit hook must block commit if > 350 tokens.
    """
    state_file = fresh_repo / "state.md"
    bloated_text = (
        """# Dynamic Working Memory (The Blackboard)
## Current Objective
- Trying to build a feature while dumping huge conversational chat transcripts into state.

## Status & Gate Verification
"""
        + "\n".join(
            [
                f"- Step {i}: Conversation transcript dump with long detailed explanations that burn through context budget rapidly."
                for i in range(30)
            ]
        )
        + """

## Immediate Next Action (Post-Compact)
- Continue working.
"""
    )
    assert count_tokens(bloated_text) > 350

    state_file.write_text(bloated_text, encoding="utf-8")
    run_git(fresh_repo, "add", "state.md")

    res = run_git(fresh_repo, "commit", "-m", "cheat: dump bloated state", check=False)
    assert res.returncode != 0
    combined_output = res.stdout + res.stderr
    assert (
        "GATE S: WORKING MEMORY TOKEN BUDGET EXCEEDED" in combined_output
        or "Total Working Memory Tokens" in combined_output
    )


# -----------------------------------------------------------------------------
# Test 4: Gate P Blocks Staging Protected Sandbox Files (.env / secrets)
# -----------------------------------------------------------------------------


def test_gate_p_blocks_staging_secrets(fresh_repo):
    """
    Agent Cheat Attempt: Stage a .env file with private credentials.
    Kinetic Gate P: Pre-commit hook must reject protected path.
    """
    env_file = fresh_repo / ".env"
    env_file.write_text("STRIPE_SECRET_KEY=sk_live_1234567890abcdef\n", encoding="utf-8")

    run_git(fresh_repo, "add", ".env")
    res = run_git(fresh_repo, "commit", "-m", "cheat: commit .env secret", check=False)
    assert res.returncode != 0
    combined_output = res.stdout + res.stderr
    assert (
        "GATE P: SANDBOX PROTECTED PATH VIOLATION" in combined_output
        or "Sandbox Protected Path Violation" in combined_output
    )


# -----------------------------------------------------------------------------
# Test 5: Gate T Blocks Architectural Boundary Violations
# -----------------------------------------------------------------------------


def test_gate_t_blocks_boundary_violation_and_appends_rejection(fresh_repo):
    """
    Agent Cheat Attempt: Subsystem 'core' imports from forbidden subsystem 'interfaces'.
    Kinetic Gate T: Pre-commit hook must reject AST boundary violation and record failure in decisions.md.
    """
    core_file = fresh_repo / "src" / "core_leak.py"
    core_file.parent.mkdir(parents=True, exist_ok=True)
    # TEMPLATE_WIRING specifies core has allowed_dependencies: []
    # If core imports from interfaces or outside, Gate T flags it
    core_file.write_text("import interfaces.adapter\n\ndef run():\n    pass\n", encoding="utf-8")

    # Also sync cartography so Gate M doesn't fail first
    subprocess.run(
        [sys.executable, "-m", "sdcs.cli", "map", "--sync", "--repo-root", str(fresh_repo)],
        check=True,
        env=ENV,
    )

    run_git(fresh_repo, "add", "src/core_leak.py", "app_map.md")
    res = run_git(fresh_repo, "commit", "-m", "cheat: import forbidden dependency", check=False)
    assert res.returncode != 0
    combined_output = res.stdout + res.stderr
    assert (
        "GATE T: TOPOLOGICAL BOUNDARY VIOLATION DETECTED" in combined_output
        or "Boundary Violation" in combined_output
    )

    # Verify that Gate T automatically recorded the rejection to decisions.md
    decisions_content = (fresh_repo / "decisions.md").read_text(encoding="utf-8")
    assert "GATE_T_VIOLATION" in decisions_content or "REJ-" in decisions_content


# -----------------------------------------------------------------------------
# Test 6: Gate M Blocks Cartography Drift (Unmapped Files)
# -----------------------------------------------------------------------------


def test_gate_m_blocks_cartography_drift(fresh_repo):
    """
    Agent Cheat Attempt: Create secret file without updating app_map.md.
    Kinetic Gate M: Pre-commit hook must reject commit until app_map.md is synced.
    """
    ghost_file = fresh_repo / "src" / "ghost_file.py"
    ghost_file.parent.mkdir(parents=True, exist_ok=True)
    ghost_file.write_text("print('ghost file')\n", encoding="utf-8")

    run_git(fresh_repo, "add", "src/ghost_file.py")
    res = run_git(fresh_repo, "commit", "-m", "cheat: unmapped file", check=False)
    assert res.returncode != 0
    combined_output = res.stdout + res.stderr
    assert (
        "GATE M: CARTOGRAPHY DRIFT DETECTED" in combined_output
        or "Cartography drift detected" in combined_output
    )

    # Reconcile with sdcs map --sync -> commit should now pass
    subprocess.run(
        [sys.executable, "-m", "sdcs.cli", "map", "--sync", "--repo-root", str(fresh_repo)],
        check=True,
        env=ENV,
    )
    run_git(fresh_repo, "add", "app_map.md")
    res_clean = run_git(fresh_repo, "commit", "-m", "fix: synced cartography", check=False)
    assert res_clean.returncode == 0


# -----------------------------------------------------------------------------
# Test 7: Subagent Scoped Blackboard Isolation (No Parallel Collision)
# -----------------------------------------------------------------------------


def test_subagent_blackboard_fork_and_rollup(fresh_repo):
    """
    Multi-Agent Test: Parallel subagent forks isolated blackboard and rolls up safely.
    """
    # 1. Fork subagent blackboard
    fork_cmd = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "state",
        "fork",
        "audio-worker",
        "--objective",
        "Build audio pipeline",
        "--repo-root",
        str(fresh_repo),
    ]
    subprocess.run(fork_cmd, check=True, env=ENV)

    worker_file = fresh_repo / "state.audio-worker.md"
    assert worker_file.is_file()

    # Verify root state.md was NOT clobbered
    root_state = (fresh_repo / "state.md").read_text(encoding="utf-8")
    assert "Build audio pipeline" not in root_state

    # 2. Worker updates its status
    worker_file.write_text(
        """# Dynamic Working Memory (The Blackboard)
## Current Objective
- Build audio pipeline

## Status & Gate Verification
- Audio pipeline unit tests passing.

## Immediate Next Action (Post-Compact)
- Rollup into root.
""",
        encoding="utf-8",
    )

    # 3. Rollup into root
    rollup_cmd = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "state",
        "rollup",
        "audio-worker",
        "--repo-root",
        str(fresh_repo),
    ]
    subprocess.run(rollup_cmd, check=True, env=ENV)

    # Ephemeral file deleted
    assert not worker_file.exists()
    # Root state updated
    updated_root = (fresh_repo / "state.md").read_text(encoding="utf-8")
    assert "Audio pipeline unit tests passing" in updated_root

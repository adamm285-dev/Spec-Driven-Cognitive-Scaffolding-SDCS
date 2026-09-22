"""Tests for the SDCS Circuit Breaker & Cyclic Thrashing Detector."""

from pathlib import Path

from sdcs.verifier.cycles import detect_oscillations, run_cycle_audit


def test_linear_commit_history_passes():
    """Verify that healthy linear progress across different files does not trip the breaker."""
    history = [
        {"src/core.py"},
        {"src/utils.py"},
        {"tests/test_core.py"},
        {"src/models.py"},
        {"src/db.py"},
    ]
    passed, violations = detect_oscillations(history=history, threshold=3)
    assert passed is True
    assert len(violations) == 0


def test_period_2_oscillation_trips_circuit_breaker():
    """Verify that an alternating ping-pong pattern (A -> B -> A -> B) trips the circuit breaker."""
    history = [
        {"src/auth.py", "src/token.py"},
        {"src/db.py", "src/models.py"},
        {"src/auth.py", "src/token.py"},
        {"src/db.py", "src/models.py"},
        {"src/auth.py", "src/token.py"},
    ]
    passed, violations = detect_oscillations(history=history, threshold=3)
    assert passed is False
    assert len(violations) >= 1
    assert "Period-2 oscillation detected" in violations[0].message
    assert "src/auth.py" in violations[0].files


def test_repeated_isolated_thrashing_trips_circuit_breaker():
    """Verify that repeatedly editing only the exact same single file across threshold commits trips the breaker."""
    history = [
        {"src/fragile.py"},
        {"src/fragile.py"},
        {"src/fragile.py"},
        {"src/fragile.py"},
    ]
    passed, violations = detect_oscillations(history=history, threshold=3)
    assert passed is False
    assert len(violations) >= 1
    assert "Repeated isolated modification detected" in violations[0].message
    assert "src/fragile.py" in violations[0].files


def test_insufficient_history_passes():
    """Verify that repos with fewer commits than the threshold pass cleanly."""
    history = [
        {"src/init.py"},
        {"src/core.py"},
    ]
    passed, violations = detect_oscillations(history=history, threshold=3)
    assert passed is True
    assert len(violations) == 0


def test_run_cycle_audit_cli_entrypoint(tmp_path: Path):
    """Verify that run_cycle_audit executes cleanly on a mock or existing repo."""
    # When running on empty or new repo without git history
    code = run_cycle_audit(repo_root=tmp_path)
    assert code == 0


def test_progressive_same_file_commits_pass():
    """Verify that progressive commits touching the same file without reversal pass cleanly."""
    from sdcs.verifier.cycles import GitCommitDiff

    # 4 consecutive commits touching finish_areas.py with progressive additions
    diff_history = [
        GitCommitDiff(
            commit_hash="c004",
            message="feat: add finish area documentation and exports",
            files={"finish_areas.py"},
            added_lines={"__all__ = ['AreaManager']", "class AreaManager: pass"},
            removed_lines=set(),
        ),
        GitCommitDiff(
            commit_hash="c003",
            message="feat: add area formatting methods",
            files={"finish_areas.py"},
            added_lines={"def format_area(self): return f'{self.sqft} sqft'"},
            removed_lines=set(),
        ),
        GitCommitDiff(
            commit_hash="c002",
            message="feat: add validation logic to finish areas",
            files={"finish_areas.py"},
            added_lines={"def validate_area(self): assert self.sqft > 0"},
            removed_lines=set(),
        ),
        GitCommitDiff(
            commit_hash="c001",
            message="feat: scaffold finish areas data model",
            files={"finish_areas.py"},
            added_lines={"class FinishArea: sqft: int = 0"},
            removed_lines=set(),
        ),
    ]

    passed, violations = detect_oscillations(diff_history=diff_history, threshold=3)
    assert passed is True
    assert len(violations) == 0


def test_inverse_diff_reversal_trips_breaker():
    """Verify that a commit reversing the diff of an earlier commit trips the circuit breaker."""
    from sdcs.verifier.cycles import GitCommitDiff

    # c002 adds line X and removes line Y. c003 removes line X and restores line Y (inversion).
    diff_history = [
        GitCommitDiff(
            commit_hash="c003",
            message="refactor: switch back to legacy calculation",
            files={"calculation.py"},
            added_lines={"return base * 1.1", "tax = 0.05", "total = base + tax"},
            removed_lines={"return base * 1.25", "tax = 0.08", "total = base * 1.08"},
        ),
        GitCommitDiff(
            commit_hash="c002",
            message="feat: update tax formula",
            files={"calculation.py"},
            added_lines={"return base * 1.25", "tax = 0.08", "total = base * 1.08"},
            removed_lines={"return base * 1.1", "tax = 0.05", "total = base + tax"},
        ),
    ]

    passed, violations = detect_oscillations(diff_history=diff_history, threshold=3)
    assert passed is False
    assert len(violations) >= 1
    assert "Commit reversal detected" in violations[0].message
    assert "c003" in violations[0].message


def test_ephemeral_blackboard_state_md_updates_do_not_trip_breaker():
    """Verify that shift-to-shift rewrites of state.md do not trip circuit breaker diff reversal."""
    from sdcs.verifier.cycles import GitCommitDiff

    # c002 updates state.md for shift 1, c003 overwrites it for shift 2
    diff_history = [
        GitCommitDiff(
            commit_hash="c003",
            message="chore(release): prepare v1.8.1 release",
            files={"state.md"},
            added_lines={"## Current Objective: v1.8.1", "All gates green"},
            removed_lines={"## Current Objective: v1.8.0", "Release shipped"},
        ),
        GitCommitDiff(
            commit_hash="c002",
            message="docs: finalize state.md shift completion",
            files={"state.md"},
            added_lines={"## Current Objective: v1.8.0", "Release shipped"},
            removed_lines={"## Current Objective: initial", "Starting work"},
        ),
    ]

    passed, violations = detect_oscillations(diff_history=diff_history, threshold=3)
    assert passed is True
    assert len(violations) == 0

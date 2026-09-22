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

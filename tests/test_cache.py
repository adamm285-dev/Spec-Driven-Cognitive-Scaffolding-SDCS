"""Tests for Gate C-Cache: KV-Cache Prefix Invariance Auditor (SPEC-001 v1.8.0 Section 7.13)."""

from pathlib import Path

from sdcs.verifier.cache import (
    audit_hydration_file,
    audit_prefix_invariance,
    run_cache_invariance_audit,
)


def test_audit_prefix_invariance_clean():
    clean_text = """
# System Prompt
You are an autonomous engineering agent adhering to SPEC-001.
Do not violate topological boundaries declared in wiring.yaml.
"""
    violations = audit_prefix_invariance(clean_text)
    assert violations == []


def test_audit_prefix_invariance_volatile_timestamps():
    dirty_text = """
# System Instructions
Generated At: 2026-09-22T04:15:30
Current Step: Step 4 of 20
Process ID: 1234
"""
    violations = audit_prefix_invariance(dirty_text)
    assert len(violations) >= 2
    assert any("timestamp" in v for v in violations)
    assert any("step counter" in v for v in violations)


def test_audit_hydration_file(tmp_path: Path):
    f = tmp_path / "spine.md"
    f.write_text(
        "# Constitutional Invariants\nLaw 1: Ground truth is immutable.\n", encoding="utf-8"
    )

    violations = audit_hydration_file(f)
    assert violations == []


def test_run_cache_invariance_audit(tmp_path: Path, capsys):
    # Setup clean repo
    (tmp_path / "spine.md").write_text("# Invariants\n", encoding="utf-8")
    (tmp_path / "wiring.yaml").write_text("subsystems: {}\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# Behavioral Contract\n", encoding="utf-8")

    code = run_cache_invariance_audit(tmp_path)
    assert code == 0
    captured = capsys.readouterr()
    assert "[GATE CACHE: PASSED]" in captured.out

    # Add volatile file
    (tmp_path / "spine.md").write_text("Turn 3 of 10\n", encoding="utf-8")
    code_bad = run_cache_invariance_audit(tmp_path)
    assert code_bad == 1

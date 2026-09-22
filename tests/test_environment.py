"""Tests for Gate E: Environment Lock & sdcs doctor Diagnostics."""

import os
from pathlib import Path
from sdcs.verifier.environment import (
    _check_python_version,
    get_environment_config,
    run_diagnostics,
    run_doctor_report,
    run_env_audit,
    verify_environment,
)


def test_check_python_version():
    """Verify python version comparator against current interpreter."""
    # We are running on Python >= 3.10
    assert _check_python_version(">=3.10") is True
    assert _check_python_version(">=3.9") is True
    # Future impossible requirement
    assert _check_python_version(">=3.99") is False


def test_get_environment_config_from_wiring(tmp_path: Path):
    """Verify environment configuration is properly extracted from wiring.yaml."""
    wiring_content = """
subsystems:
  core:
    path: src/core
environment:
  python: ">=3.11"
  required_tools:
    - git
    - pytest
  required_env_vars:
    - TEST_SECRET_KEY
"""
    (tmp_path / "wiring.yaml").write_text(wiring_content, encoding="utf-8")
    cfg = get_environment_config(tmp_path)
    assert cfg["python"] == ">=3.11"
    assert "git" in cfg["required_tools"]
    assert "pytest" in cfg["required_tools"]
    assert "TEST_SECRET_KEY" in cfg["required_env_vars"]


def test_verify_environment_passes_when_clean(tmp_path: Path):
    """Verify clean environment passes Gate E."""
    wiring_content = """
environment:
  python: ">=3.10"
  required_tools:
    - git
"""
    (tmp_path / "wiring.yaml").write_text(wiring_content, encoding="utf-8")
    passed, errors = verify_environment(tmp_path)
    assert passed is True
    assert len(errors) == 0


def test_verify_environment_fails_on_missing_tool(tmp_path: Path):
    """Verify that a missing required CLI tool trips Gate E."""
    wiring_content = """
environment:
  python: ">=3.10"
  required_tools:
    - non_existent_binary_xyz_12345
"""
    (tmp_path / "wiring.yaml").write_text(wiring_content, encoding="utf-8")
    passed, errors = verify_environment(tmp_path)
    assert passed is False
    assert any("non_existent_binary_xyz_12345" in err for err in errors)


def test_verify_environment_fails_on_missing_env_var(tmp_path: Path):
    """Verify that a missing required env variable trips Gate E."""
    wiring_content = """
environment:
  required_env_vars:
    - SDCS_TEST_VAR_THAT_SHOULD_NOT_EXIST
"""
    (tmp_path / "wiring.yaml").write_text(wiring_content, encoding="utf-8")
    passed, errors = verify_environment(tmp_path)
    assert passed is False
    assert any("SDCS_TEST_VAR_THAT_SHOULD_NOT_EXIST" in err for err in errors)

    # Now provide the env var and verify it passes
    os.environ["SDCS_TEST_VAR_THAT_SHOULD_NOT_EXIST"] = "secret_val"
    try:
        passed, errors = verify_environment(tmp_path)
        assert passed is True
    finally:
        del os.environ["SDCS_TEST_VAR_THAT_SHOULD_NOT_EXIST"]


def test_doctor_diagnostics_and_report(tmp_path: Path):
    """Verify sdcs doctor generates diagnostic items and runs report."""
    # Create mock pillars
    (tmp_path / "spine.md").write_text("# Spine\n", encoding="utf-8")
    (tmp_path / "wiring.yaml").write_text("environment:\n  python: '>=3.10'\n", encoding="utf-8")
    (tmp_path / "state.md").write_text("# State\n", encoding="utf-8")
    (tmp_path / "app_map.md").write_text("# Map\n", encoding="utf-8")
    (tmp_path / "decisions.md").write_text("# Decisions\n", encoding="utf-8")
    (tmp_path / ".githooks").mkdir()
    (tmp_path / ".githooks" / "pre-commit").write_text("#!/bin/sh\n", encoding="utf-8")

    items = run_diagnostics(tmp_path)
    assert len(items) >= 5

    code = run_doctor_report(tmp_path)
    # Warnings for evals/roadmap are allowed, but no hard failures
    assert code == 0


def test_run_env_audit_exit_code(tmp_path: Path):
    """Verify run_env_audit returns 0 when valid and 1 when invalid."""
    (tmp_path / "wiring.yaml").write_text("environment:\n  python: '>=3.10'\n", encoding="utf-8")
    assert run_env_audit(tmp_path) == 0

    (tmp_path / "wiring.yaml").write_text("environment:\n  python: '>=3.99'\n", encoding="utf-8")
    assert run_env_audit(tmp_path) == 1

"""Automated tests for SDCS Gate T (AST Topology Auditor & Negative Memory Sync)."""

from pathlib import Path

import pytest

from sdcs.verifier.topology import (
    ImportViolation,
    TopologyValidator,
    get_next_rejection_id,
    is_violation_duplicate,
    sync_violations_to_decisions,
)

SAMPLE_WIRING = """
version: "1.2.0"
subsystems:
  core:
    path: "src/core"
    allowed_dependencies: []
  domain:
    path: "src/domain"
    allowed_dependencies:
      - core
  infrastructure:
    path: "src/infrastructure"
    allowed_dependencies:
      - core
      - domain
"""


@pytest.fixture
def repo_env(tmp_path: Path):
    """Scaffolds a mock repository containing an SDCS topology layout."""
    wiring_file = tmp_path / "wiring.yaml"
    wiring_file.write_text(SAMPLE_WIRING, encoding="utf-8")

    decisions_file = tmp_path / "decisions.md"
    decisions_file.write_text(
        "# Negative Decisions Ledger\n\n## REJ-001: Initial Rejection\n- Target: `none`\n",
        encoding="utf-8",
    )

    src_core = tmp_path / "src" / "core"
    src_domain = tmp_path / "src" / "domain"
    src_infra = tmp_path / "src" / "infrastructure"

    for p in (src_core, src_domain, src_infra):
        p.mkdir(parents=True, exist_ok=True)

    (src_core / "utils.py").write_text("def helper(): pass\n", encoding="utf-8")
    return tmp_path


def test_clean_import_passes(repo_env: Path):
    """Verifies that allowed import edges do not produce violations."""
    domain_user = repo_env / "src" / "domain" / "user.py"
    domain_user.write_text("import src.core.utils\n", encoding="utf-8")

    validator = TopologyValidator(repo_env / "wiring.yaml", repo_env)
    violations = validator.audit_tree()
    assert len(violations) == 0


def test_prohibited_boundary_flagged(repo_env: Path):
    """Verifies that unauthorized import edges trigger an ImportViolation."""
    domain_user = repo_env / "src" / "domain" / "user.py"
    # domain is only permitted to import core, not infrastructure
    domain_user.write_text("from src.infrastructure import database\n", encoding="utf-8")

    validator = TopologyValidator(repo_env / "wiring.yaml", repo_env)
    violations = validator.audit_tree()

    assert len(violations) == 1
    v = violations[0]
    assert v.source_subsystem == "domain"
    assert v.target_subsystem == "infrastructure"
    assert v.line_number == 1


def test_relative_import_resolution(repo_env: Path):
    """Verifies that relative import syntax is properly resolved against repo root."""
    domain_sub = repo_env / "src" / "domain" / "sub"
    domain_sub.mkdir(parents=True, exist_ok=True)
    domain_service = domain_sub / "service.py"
    # Relative import attempting to access infrastructure: from ...infrastructure import database
    domain_service.write_text("from ...infrastructure import database\n", encoding="utf-8")

    validator = TopologyValidator(repo_env / "wiring.yaml", repo_env)
    violations = validator.audit_tree()

    assert len(violations) == 1
    assert violations[0].target_subsystem == "infrastructure"


def test_monotonic_id_extraction():
    """Verifies regex extracts the highest ID across headers and formatting gaps."""
    content = """
    ## REJ-002: Some rejection
    ### REJ-015: Another rejection
    # REJ-008: Low index
    """
    next_id = get_next_rejection_id(content)
    assert next_id == "REJ-016"


def test_deduplication_and_persistence(repo_env: Path):
    """Verifies decisions.md serializes failures once and ignores duplicate runs."""
    validator = TopologyValidator(repo_env / "wiring.yaml", repo_env)
    violation = ImportViolation(
        source_file=Path("src/domain/user.py"),
        source_subsystem="domain",
        target_subsystem="infrastructure",
        imported_module="src.infrastructure.database",
        line_number=5,
    )

    # First execution: append new record
    appended_1 = sync_violations_to_decisions([violation], validator, repo_env)
    assert appended_1 == 1

    content_first_pass = (repo_env / "decisions.md").read_text(encoding="utf-8")
    assert "## REJ-002: Prohibited Import Boundary" in content_first_pass
    assert "src/domain/user.py:5" in content_first_pass

    # Duplicate check verification
    assert is_violation_duplicate(content_first_pass, violation) is True

    # Second execution: should skip appending duplicate
    appended_2 = sync_violations_to_decisions([violation], validator, repo_env)
    assert appended_2 == 0

    content_second_pass = (repo_env / "decisions.md").read_text(encoding="utf-8")
    assert content_first_pass == content_second_pass

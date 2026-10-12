"""`sdcs init` on a repository that already has its own machinery.

Written by the reviewing agent, 2026-09-22 (gate audit, batch 1). Run on a scratch copy of
an existing project's agent files, a plain `sdcs init` -- no --force -- replaced the repo's existing
.githooks/pre-commit and printed "+ Hook: ... (executable set)" with no warning. It checked
AGENTS.md and skipped it, so the existence check exists; the hook just does not get one.

init is the first command a new user runs on a repo they care about.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    return tmp_path


def _init(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "sdcs.cli", "init", "--target-dir", str(repo)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_init_keeps_an_existing_pre_commit_hook(repo: Path):
    hook = repo / ".githooks" / "pre-commit"
    hook.parent.mkdir()
    hook.write_text('#!/bin/sh\necho "existing team hook"\n', encoding="utf-8")

    result = _init(repo)

    kept = "existing team hook" in hook.read_text(encoding="utf-8")
    assert (
        kept or result.returncode != 0
    ), "init replaced an existing pre-commit hook without --force and without refusing"


def test_init_keeps_an_existing_agents_md(repo: Path):
    """The case init already gets right -- kept so a refactor cannot lose it."""
    agents = repo / "AGENTS.md"
    agents.write_text("# Our own agreement\n", encoding="utf-8")

    _init(repo)

    assert agents.read_text(encoding="utf-8") == "# Our own agreement\n"


def test_init_does_not_create_duplicate_root_pillars_when_existing_elsewhere(repo: Path):
    """If a repo already has decisions.md, roadmap.md, wiring.yaml, or spine.md elsewhere,

    init must not create redundant duplicates at the root.
    """
    map_dir = repo / "docs" / "map"
    map_dir.mkdir(parents=True, exist_ok=True)
    (map_dir / "decisions.md").write_text("# Existing Decisions\n", encoding="utf-8")
    (map_dir / "roadmap.md").write_text("# Existing Roadmap\n", encoding="utf-8")
    (map_dir / "wiring.yaml").write_text("subsystems: {}\n", encoding="utf-8")
    (repo / "docs" / "spine.md").write_text("# Existing Spine\n", encoding="utf-8")

    _init(repo)

    assert not (repo / "decisions.md").exists(), "init created redundant root decisions.md"
    assert not (repo / "roadmap.md").exists(), "init created redundant root roadmap.md"
    assert not (repo / "wiring.yaml").exists(), "init created redundant root wiring.yaml"
    assert not (repo / "spine.md").exists(), "init created redundant root spine.md"


def test_init_finds_existing_pillars_whatever_their_case(repo: Path):
    """Added pass 4 by the reviewer. Some projects keep docs/map/SPINE.md -- uppercase.

    On Windows this passes whatever the lookup does, because the filesystem ignores case. CI
    runs on ubuntu-latest, where it does not, so that is the run that can tell.
    """
    map_dir = repo / "docs" / "map"
    map_dir.mkdir(parents=True, exist_ok=True)
    (map_dir / "SPINE.md").write_text("# Existing Spine\n", encoding="utf-8")
    (map_dir / "decisions.md").write_text("# Existing Decisions\n", encoding="utf-8")

    _init(repo)

    assert not (repo / "spine.md").exists(), "init created a root spine.md beside docs/map/SPINE.md"
    assert not (
        repo / "decisions.md"
    ).exists(), "init created a root decisions.md beside docs/map/decisions.md"


def test_all_locators_resolve_pillars_in_docs_dir(tmp_path: Path):
    from sdcs.audit import locate_evals_file
    from sdcs.decay import locate_decisions_file, locate_roadmap_file
    from sdcs.graph import locate_wiring_file
    from sdcs.hydrate import locate_pillar_file
    from sdcs.map import locate_map_file
    from sdcs.session import locate_sessions_dir
    from sdcs.verifier.environment import run_diagnostics
    from sdcs.verifier.state import locate_state_file

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "spine.md").write_text("# Spine\n", encoding="utf-8")
    (docs_dir / "wiring.yaml").write_text("subsystems: {}\n", encoding="utf-8")
    (docs_dir / "roadmap.md").write_text("# Roadmap\n", encoding="utf-8")
    (docs_dir / "state.md").write_text("## Active Objective\nObjective\n", encoding="utf-8")
    (docs_dir / "app_map.md").write_text("# Cartography\n", encoding="utf-8")
    (docs_dir / "decisions.md").write_text("# Decisions\n", encoding="utf-8")
    (docs_dir / "evals.md").write_text("# Evals\n", encoding="utf-8")
    (docs_dir / "sessions").mkdir()

    assert locate_pillar_file(tmp_path, "spine.md") == docs_dir / "spine.md"
    assert locate_wiring_file(tmp_path) == docs_dir / "wiring.yaml"
    assert locate_roadmap_file(tmp_path) == docs_dir / "roadmap.md"
    assert locate_state_file(tmp_path) == docs_dir / "state.md"
    assert locate_map_file(tmp_path) == docs_dir / "app_map.md"
    assert locate_decisions_file(tmp_path) == docs_dir / "decisions.md"
    assert locate_evals_file(tmp_path) == docs_dir / "evals.md"
    assert locate_sessions_dir(tmp_path) == docs_dir / "sessions"

    items = run_diagnostics(tmp_path)
    pillar_items = [it for it in items if it.category == "Cognitive Pillars"]
    assert len(pillar_items) == 7
    assert all(it.passed for it in pillar_items)

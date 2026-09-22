import os
import subprocess
import sys
from pathlib import Path

from sdcs.hydrate import compile_hydration_payload

ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")


def test_hydrate_lite_profile(tmp_path):
    (tmp_path / "spine.md").write_text("# Constitutional Invariants\nRule 1\n", encoding="utf-8")
    (tmp_path / "state.md").write_text("# Blackboard\n## Current Objective\nGoal\n", encoding="utf-8")

    payload, tokens = compile_hydration_payload(tmp_path, profile="lite")
    assert "[PILLAR 1: THE LAW]" in payload
    assert "[PILLAR 4: THE BLACKBOARD]" in payload
    assert "[PILLAR 3:" not in payload
    assert tokens > 0


def test_hydrate_standard_profile(tmp_path):
    (tmp_path / "spine.md").write_text("# Invariants\nLaw\n", encoding="utf-8")
    (tmp_path / "roadmap.md").write_text("## Milestone M-001: Core\n* [INTENT]: Test\n* [MEASURED]: PENDING\n", encoding="utf-8")
    (tmp_path / "app_map.md").write_text("# Cartography\n### `src/`\n- `main.py`\n", encoding="utf-8")
    (tmp_path / "decisions.md").write_text("## REJ-001: Bad Idea\nTHE CLAIM: X\n", encoding="utf-8")
    (tmp_path / "state.md").write_text("## Current Objective\nTask\n", encoding="utf-8")

    payload, tokens = compile_hydration_payload(tmp_path, profile="standard")
    assert "[PILLAR 1: THE LAW]" in payload
    assert "[PILLAR 3: THE NORTH STAR]" in payload
    assert "[PILLAR 5: THE COMPASS]" in payload
    assert "[PILLAR 6: THE GRAVEYARD]" in payload
    assert "[PILLAR 4: THE BLACKBOARD]" in payload
    assert tokens > 0


def test_hydrate_cli_execution():
    repo_root = Path(__file__).parent.parent
    cmd = [sys.executable, "-m", "sdcs.cli", "hydrate", "--profile", "lite"]
    result = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, check=True, env=ENV)
    assert "[PILLAR 4: THE BLACKBOARD]" in result.stdout
    assert "[SDCS::HYDRATE]" in result.stderr

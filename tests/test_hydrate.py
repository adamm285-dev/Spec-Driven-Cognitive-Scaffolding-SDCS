import os
import subprocess
import sys
from pathlib import Path

from sdcs.hydrate import compile_hydration_payload

ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")


def test_hydrate_lite_profile(tmp_path):
    (tmp_path / "spine.md").write_text("# Constitutional Invariants\nRule 1\n", encoding="utf-8")
    (tmp_path / "state.md").write_text(
        "# Blackboard\n## Current Objective\nGoal\n", encoding="utf-8"
    )

    payload, tokens = compile_hydration_payload(tmp_path, profile="lite")
    assert "[PILLAR 1: THE LAW]" in payload
    assert "[PILLAR 4: THE BLACKBOARD]" in payload
    assert "[PILLAR 3:" not in payload
    assert tokens > 0


def test_hydrate_standard_profile(tmp_path):
    (tmp_path / "spine.md").write_text("# Invariants\nLaw\n", encoding="utf-8")
    (tmp_path / "roadmap.md").write_text(
        "## Milestone M-001: Core\n* [INTENT]: Test\n* [MEASURED]: PENDING\n", encoding="utf-8"
    )
    (tmp_path / "app_map.md").write_text(
        "# Cartography\n### `src/`\n- `main.py`\n", encoding="utf-8"
    )
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
    result = subprocess.run(
        cmd, cwd=str(repo_root), capture_output=True, text=True, check=True, env=ENV
    )
    assert "[PILLAR 4: THE BLACKBOARD]" in result.stdout
    assert "[SDCS::HYDRATE]" in result.stderr


def test_hydrate_skeletal_auto_discovery_without_src(tmp_path):
    """Verify skeletal hydration discovers packages outside src/ via wiring.yaml or fallback scan."""
    (tmp_path / "spine.md").write_text("# Law\n", encoding="utf-8")
    (tmp_path / "state.md").write_text("## Current Objective\nGoal\n", encoding="utf-8")

    pkg_dir = tmp_path / "my_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "models.py").write_text(
        "class Invoice:\n    def total(self, tax: float = 0.0) -> float:\n        return 100.0 + tax\n",
        encoding="utf-8",
    )
    # Ensure test files are excluded during fallback scan
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_models.py").write_text("def test_noop(): pass\n", encoding="utf-8")

    # Case 1: Fallback discovery without src/ or wiring.yaml
    payload_fallback, _ = compile_hydration_payload(tmp_path, profile="full", skeletal=True)
    assert "# [AST SKELETAL INTERFACES]" in payload_fallback
    assert "my_pkg/models.py" in payload_fallback
    assert "class Invoice:" in payload_fallback
    assert "def total(self, tax: float" in payload_fallback
    assert "test_models.py" not in payload_fallback

    # Case 2: Discovery via wiring.yaml subsystems.*.path
    (tmp_path / "wiring.yaml").write_text(
        'version: "1.9.0"\nsubsystems:\n  billing:\n    path: "my_pkg"\n',
        encoding="utf-8",
    )
    payload_wiring, _ = compile_hydration_payload(tmp_path, profile="full", skeletal=True)
    assert "# [AST SKELETAL INTERFACES]" in payload_wiring
    assert "my_pkg/models.py" in payload_wiring

    # Case 3: Explicit subsystem name resolved via wiring.yaml
    payload_sub, _ = compile_hydration_payload(
        tmp_path, profile="full", subsystem="billing", skeletal=True
    )
    assert "# [AST SKELETAL INTERFACES]" in payload_sub
    assert "my_pkg/models.py" in payload_sub


def test_hydrate_adaptive_zero_read_source_bundle(tmp_path):
    """Verify skeletal=True includes # [PRE-HYDRATED SOURCE FILES] when <=4000 tokens and omits when include_source=False."""
    (tmp_path / "spine.md").write_text("# Law\n", encoding="utf-8")
    (tmp_path / "state.md").write_text("## Current Objective\nGoal\n", encoding="utf-8")

    pkg_dir = tmp_path / "my_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
    (pkg_dir / "models.py").write_text(
        "class Order:\n    def calculate(self, amount: int) -> int:\n        return amount * 2\n",
        encoding="utf-8",
    )

    # Default (include_source=None) with small source (<= 4000 tokens): includes source bundle
    payload_auto, _ = compile_hydration_payload(tmp_path, profile="full", skeletal=True)
    assert "# [AST SKELETAL INTERFACES]" in payload_auto
    assert "# [PRE-HYDRATED SOURCE FILES] Zero-Read Implementation Bundle" in payload_auto
    assert "return amount * 2" in payload_auto
    assert (
        "my_pkg/__init__.py"
        not in payload_auto.split("# [PRE-HYDRATED SOURCE FILES] Zero-Read Implementation Bundle")[
            1
        ]
    )

    # Explicit include_source=False: keeps AST skeletons, omits source bundle
    payload_no_src, _ = compile_hydration_payload(
        tmp_path, profile="full", skeletal=True, include_source=False
    )
    assert "# [AST SKELETAL INTERFACES]" in payload_no_src
    assert "# [PRE-HYDRATED SOURCE FILES] Zero-Read Implementation Bundle" not in payload_no_src
    assert "return amount * 2" not in payload_no_src


def test_template_state_schema_and_hydration_spec_ledger_directive(tmp_path):
    """Verify TEMPLATE_STATE passes audit_state_tokens with warnings == [] and hydration includes spec-ledger directive."""
    from sdcs.init import TEMPLATE_STATE
    from sdcs.verifier.state import audit_state_tokens

    state_file = tmp_path / "state.md"
    state_file.write_text(TEMPLATE_STATE, encoding="utf-8")

    passed, total_tokens, section_tokens, warnings = audit_state_tokens(state_file, max_tokens=300)
    assert passed is True
    assert total_tokens <= 300
    assert warnings == []
    assert "Current Objective" in section_tokens
    assert "Status & Gate Verification" in section_tokens
    assert "Immediate Next Action" in section_tokens

    for prof in ("lite", "standard", "full"):
        payload, _ = compile_hydration_payload(tmp_path, profile=prof)
        assert "# [PILLAR 4: THE BLACKBOARD] Working Memory" in payload
        assert "In-Stride Spec Ledger:" in payload

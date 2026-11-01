import os
import subprocess
import sys
from pathlib import Path

from sdcs.verifier.state import (
    audit_state_tokens,
    compute_elastic_state_budget,
    count_tokens,
    parse_state_sections,
)


def test_count_tokens():
    text = "Hello world from SDCS working memory."
    tokens = count_tokens(text)
    assert tokens > 0
    assert tokens >= len(text.split())


def test_parse_state_sections():
    content = """# Title
Preamble text here.

## Current Objective
Implement M-006 GPU Cache.

## Status & Gate Verification
- Gate T: Passed
- Gate A: In progress

## Immediate Next Action (Post-Compact)
Run integration tests.
"""
    sections = parse_state_sections(content)
    assert "__preamble__" in sections
    assert "Current Objective" in sections
    assert "Status & Gate Verification" in sections
    assert "Immediate Next Action (Post-Compact)" in sections


def test_audit_state_tokens_within_budget(tmp_path: Path):
    state_file = tmp_path / "state.md"
    content = """## Current Objective
Complete Milestone M-004.

## Status & Gate Verification
- Invariant verification: clean.
- Unit tests: 100% passing.

## Immediate Next Action (Post-Compact)
Ship PyPI package.
"""
    state_file.write_text(content, encoding="utf-8")

    passed, total_tokens, section_tokens, warnings = audit_state_tokens(state_file, max_tokens=350)
    assert passed is True
    assert total_tokens < 100
    assert len(warnings) == 0
    assert "Current Objective" in section_tokens


def test_audit_state_tokens_exceeds_budget(tmp_path: Path):
    state_file = tmp_path / "state.md"
    # Create large state content
    long_prose = " ".join(["token-word-item"] * 400)
    content = f"""## Current Objective
{long_prose}

## Status & Gate Verification
Status details here.

## Immediate Next Action (Post-Compact)
Next steps.
"""
    state_file.write_text(content, encoding="utf-8")

    passed, total_tokens, _section_tokens, warnings = audit_state_tokens(state_file, max_tokens=300)
    assert passed is False
    assert total_tokens > 300
    assert any("budget exceeded" in w.lower() for w in warnings)


def test_cli_verify_state(tmp_path: Path):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")

    state_file = tmp_path / "state.md"
    state_file.write_text(
        "## Current Objective\nGoal\n\n## Status & Gate Verification\nPass\n\n## Immediate Next Action\nNext\n",
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "verify",
        "--state",
        "--repo-root",
        str(tmp_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
    assert res.returncode == 0
    assert "working memory is disciplined and within budget" in res.stdout

    # Now test failure with tight budget of 5 tokens
    cmd_tight = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "verify",
        "--state",
        "--max-tokens",
        "5",
        "--repo-root",
        str(tmp_path),
    ]
    res_tight = subprocess.run(cmd_tight, capture_output=True, text=True, env=env, check=False)
    assert res_tight.returncode == 1
    assert "Working memory bloat detected" in res_tight.stdout


def test_compute_elastic_state_budget_baseline():
    content = """## Current Objective
- Bullet 1
- Bullet 2

## Status & Gate Verification
- Gate T: OK

## Immediate Next Action
- Next step
"""
    budget, active, comp, advisories = compute_elastic_state_budget(content, base_budget=350)
    assert active == 4
    assert comp == 0
    assert budget == 350


def test_compute_elastic_state_budget_expansion():
    content = """## Current Objective
- Requirement item A
- Requirement item B
- Requirement item C
- Requirement item D
- Requirement item E
- Requirement item F
- Requirement item G

## Status & Gate Verification
- Gate T clean

## Immediate Next Action
- Next
"""
    budget, active, comp, _advisories = compute_elastic_state_budget(content, base_budget=350)
    # 9 active bullets -> (9 - 4) * 28 = 140 extra tokens -> 490 tokens
    assert active == 9
    assert budget == 350 + 140


def test_compute_elastic_state_budget_multipackage(tmp_path: Path):
    # Setup 3 dummy packages
    (tmp_path / "pkg_a").mkdir()
    (tmp_path / "pkg_a" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg_b").mkdir()
    (tmp_path / "pkg_b" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg_c").mkdir()
    (tmp_path / "pkg_c" / "__init__.py").write_text("", encoding="utf-8")

    content = """## Current Objective
- Req 1
- Req 2
- Req 3
- Req 4
"""
    budget, active, _comp, _advisories = compute_elastic_state_budget(
        content, repo_root=tmp_path, base_budget=350
    )
    # 4 bullets (0 extra), 3 pkgs -> 2 extra pkgs * 25 = 50 extra tokens -> 400 tokens
    assert active == 4
    assert budget == 350 + 50


def test_compute_elastic_state_budget_density_advisory():
    long_bullet = "- " + ("word " * 70)
    content = f"""## Current Objective
{long_bullet}
"""
    _budget, _active, _comp, advisories = compute_elastic_state_budget(content, base_budget=350)
    assert any("density target" in a for a in advisories)


def test_compute_elastic_state_budget_compaction_advisory():
    content = """## Current Objective
- [x] Done item 1
- [x] Done item 2
- [x] Done item 3
- [x] Done item 4
- [x] Done item 5
- [x] Done item 6

## Status & Gate Verification
- OK
"""
    _budget, _active, comp, advisories = compute_elastic_state_budget(content, base_budget=350)
    assert comp == 6
    assert any("completed (`- [x]`) bullets present" in a for a in advisories)


def test_compute_elastic_state_budget_ceiling():
    bullets = "\n".join([f"- Requirement bullet {i}" for i in range(50)])
    content = f"## Current Objective\n{bullets}\n"
    budget, _active, _comp, _advisories = compute_elastic_state_budget(content, base_budget=350)
    assert budget == 1200


def test_audit_state_tokens_elastic_scaling(tmp_path: Path):
    state_file = tmp_path / "state.md"
    bullets = "\n".join(
        [
            f"- Requirement item number {i} with concise notes and architectural specification details that describe system boundaries."
            for i in range(22)
        ]
    )
    content = f"""## Current Objective
{bullets}

## Status & Gate Verification
- Pass

## Immediate Next Action
- Ship
"""
    state_file.write_text(content, encoding="utf-8")
    tokens = count_tokens(content)
    # Tokens should be > 350 but within elastic expansion (350 + (20-4)*28 = 798t)
    assert tokens > 350

    passed_elastic, total_t, _, warnings = audit_state_tokens(
        state_file, max_tokens=350, elastic=True
    )
    assert passed_elastic is True
    assert not any("budget exceeded" in w.lower() for w in warnings)

    passed_strict, _, _, warnings_strict = audit_state_tokens(
        state_file, max_tokens=350, elastic=False
    )
    assert passed_strict is False
    assert any("budget exceeded" in w_s.lower() for w_s in warnings_strict)


def test_cli_verify_state_no_elastic(tmp_path: Path):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")

    state_file = tmp_path / "state.md"
    bullets = "\n".join(
        [
            f"- Requirement item number {i} with concise notes and architectural specification details that describe system boundaries."
            for i in range(22)
        ]
    )
    content = f"""## Current Objective
{bullets}

## Status & Gate Verification
- Pass

## Immediate Next Action
- Ship
"""
    state_file.write_text(content, encoding="utf-8")

    # With default elastic scaling, passes
    cmd_elastic = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "verify",
        "--state",
        "--max-tokens",
        "350",
        "--repo-root",
        str(tmp_path),
    ]
    res_elastic = subprocess.run(cmd_elastic, capture_output=True, text=True, env=env, check=False)
    assert res_elastic.returncode == 0
    assert "Elastic Scale from 350t base" in res_elastic.stdout

    # With --no-elastic, fails
    cmd_strict = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "verify",
        "--state",
        "--max-tokens",
        "350",
        "--no-elastic",
        "--repo-root",
        str(tmp_path),
    ]
    res_strict = subprocess.run(cmd_strict, capture_output=True, text=True, env=env, check=False)
    assert res_strict.returncode == 1
    assert "Working memory bloat detected" in res_strict.stdout
